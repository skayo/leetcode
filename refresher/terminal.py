"""Terminal output and line input for the refresher.

Everything that deals with escape codes, wrapping, or line editing lives here,
so the tutor itself only passes plain strings around.
"""

from __future__ import annotations

import builtins
import importlib
import io
import keyword
import os
import re
import select
import shutil
import sys
import tokenize
from typing import Callable, Iterator

MAX_WIDTH = 88

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_SGR = {
    "bold": "1",
    "dim": "2",
    "italic": "3",
    "underline": "4",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
}
# Code colors follow the default theme of Python's own REPL (3.14 and later), so the
# examples match what you see as you type. Comments are dimmed instead of red,
# because in the examples they are explanations, not errors.
_CODE_STYLES = {
    "keyword": ("bold", "blue"),
    "builtin": ("cyan",),
    "string": ("green",),
    "number": ("yellow",),
    "comment": ("dim", "italic"),
    "definition": ("bold",),
}
_PROMPT_STYLE = ("bold", "magenta")
_BUILTIN_NAMES = frozenset(dir(builtins))
_LAYOUT_TOKENS = frozenset(
    {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT}
)
_INLINE_RE = re.compile(
    r"`([^`]+)`"  # `code`
    r"|\*\*(.+?)\*\*"  # **bold**
    r"|\*(?!\s)(.+?)(?<!\s)\*"  # *italic*
    r"|\[([^\]]+)\]\(([^)\s]+)\)"  # [text](url)
)
_LIST_ITEM_RE = re.compile(r"^(?:[-*]|\d+\.)\s+")

Segment = tuple[str, tuple[str, ...]]


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def color_enabled(stream=None) -> bool:
    """Decide on color the same way Python 3.13 and later do for the REPL."""
    env = os.environ
    if env.get("PYTHON_COLORS") == "0":
        return False
    if env.get("PYTHON_COLORS") == "1":
        return True
    if env.get("NO_COLOR"):
        return False
    if env.get("FORCE_COLOR"):
        return True
    if env.get("TERM") == "dumb":
        return False
    try:
        return (stream or sys.stdout).isatty()
    except (AttributeError, ValueError):
        return False


class Term:
    """Formats and prints everything the tutor shows.

    Methods that print write to whatever `sys.stdout` is at the time, so tests can
    capture them with `contextlib.redirect_stdout`.
    """

    def __init__(self, color: bool | None = None, width: int | None = None):
        self.color = color_enabled() if color is None else color
        self._width = width

    @property
    def width(self) -> int:
        if self._width:
            return self._width
        return max(40, min(shutil.get_terminal_size().columns, MAX_WIDTH))

    def paint(self, text: str, *styles: str) -> str:
        if not (self.color and styles and text):
            return text
        codes = ";".join(_SGR[style] for style in styles)
        return f"\x1b[{codes}m{text}\x1b[0m"

    # Prompts and code

    @property
    def ps1(self) -> str:
        return self.paint(">>> ", *_PROMPT_STYLE)

    @property
    def ps2(self) -> str:
        return self.paint("... ", *_PROMPT_STYLE)

    def highlight(self, code: str) -> str:
        """Color Python source. Stripping the colors always gives back `code` exactly."""
        if not (self.color and code):
            return code
        try:
            return self._highlight(code)
        except Exception:  # the tokenizer rejects some fragments; show them plain
            return code

    def _highlight(self, code: str) -> str:
        starts = [0]
        for line in code.splitlines(keepends=True):
            starts.append(starts[-1] + len(line))

        def offset(position: tuple[int, int]) -> int:
            row, col = position
            return starts[min(row, len(starts)) - 1] + col

        out: list[str] = []
        last = 0
        previous = ""
        previous_type = None
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.ENDMARKER:
                break
            start, end = offset(token.start), offset(token.end)
            if start < last or end <= start:
                continue
            gap = code[last:start]
            # Inside an f-string, the tokenizer skips the second brace of {{ and }}.
            if gap and previous_type is not None and _is_string_part(previous_type):
                gap = self._paint_lines(gap, _CODE_STYLES["string"])
            out.append(gap)
            piece = code[start:end]
            style = _token_style(token, previous)
            out.append(self._paint_lines(piece, style) if style else piece)
            last = end
            if token.type not in _LAYOUT_TOKENS:
                previous = token.string
                previous_type = token.type
        out.append(code[last:])
        return "".join(out)

    def _paint_lines(self, text: str, style: tuple[str, ...]) -> str:
        # Paint line by line so a prompt added in front of a line is never colored.
        return "\n".join(self.paint(part, *style) for part in text.split("\n"))

    def code_lines(self, code: str) -> list[str]:
        return self.highlight(code.rstrip("\n")).split("\n")

    # Prose

    def prose(self, text: str, *, base: tuple[str, ...] = (), indent: int = 2) -> None:
        for line in self.prose_lines(text, base=base, indent=indent):
            print(line)

    def prose_lines(
        self, text: str, *, base: tuple[str, ...] = (), indent: int = 2
    ) -> list[str]:
        """Wrap a little Markdown (paragraphs, lists, `code`, **bold**, *italic*, links)."""
        width = max(20, self.width - indent)
        pad = " " * indent
        out: list[str] = []
        for number, paragraph in enumerate(_paragraphs(text)):
            if number:
                out.append("")
            if isinstance(paragraph, str):
                out.extend(pad + line for line in self._wrap(paragraph, width, base))
                continue
            for marker, item in paragraph:
                hang = " " * len(marker)
                for i, line in enumerate(self._wrap(item, width - len(marker), base)):
                    lead = self.paint(marker, "dim") if i == 0 else hang
                    out.append(pad + lead + line)
        return out

    def _wrap(self, text: str, width: int, base: tuple[str, ...]) -> list[str]:
        words: list[list[Segment]] = []
        current: list[Segment] = []
        for piece, styles, atomic in _inline(text):
            styles = base + styles
            if atomic:  # inline code stays on one line when it can
                current.append((piece, styles))
                continue
            for part in re.split(r"(\s+)", piece):
                if not part:
                    continue
                if part.isspace():
                    if current:
                        words.append(current)
                        current = []
                else:
                    current.append((part, styles))
        if current:
            words.append(current)
        words = [part for word in words for part in _split_long_word(word, width)]

        lines: list[list[Segment]] = []
        line: list[Segment] = []
        used = 0
        for word in words:
            size = sum(len(piece) for piece, _ in word)
            if line and used + 1 + size > width:
                lines.append(line)
                line, used = [], 0
            if line:
                line.append((" ", base))
                used += 1
            line.extend(word)
            used += size
        if line:
            lines.append(line)
        return ["".join(self.paint(piece, *styles) for piece, styles in line) for line in lines]

    # Messages

    def note(self, text: str) -> None:
        self.prose(text, base=("dim",))

    def warn(self, text: str) -> None:
        self.prose(text, base=("yellow",))

    def success(self, text: str) -> None:
        self.prose("✓ " + text, base=("green",))

    def failure(self, text: str) -> None:
        self.prose("✗ " + text, base=("yellow",))

    @staticmethod
    def erase_line() -> str:
        """What clears a waiting prompt off its line, so output can replace it."""
        return "\r\x1b[K" if _is_terminal(sys.stdout) else "\n"

    # Rules

    def rule(self, title: str, right: str = "", *, star: bool = False) -> str:
        """A step header: `── title ─────── right ──`."""
        mark = "★ " if star else ""
        tail = f" {right} ──" if right else " ──"
        room = self.width - 3 - len(mark) - len(tail) - 3
        if len(title) > room:
            title = title[: max(1, room - 1)] + "…"
        fill = self.width - 3 - len(mark) - len(title) - 1 - len(tail)
        return (
            self.paint("── ", "dim")
            + self.paint(mark, "yellow")
            + self.paint(title, "bold")
            + " "
            + self.paint("─" * max(2, fill) + tail, "dim")
        )

    def card(self, title: str, right: str = "") -> list[str]:
        """A section banner, heavier than a step header."""
        bar = self.paint("━" * self.width, "dim")
        gap = max(2, self.width - 1 - len(title) - len(right))
        middle = " " + self.paint(title, "bold") + " " * gap + self.paint(right, "dim")
        return [bar, middle, bar]


def _split_long_word(word: list[Segment], width: int) -> list[list[Segment]]:
    """Break a word wider than a line at the spaces inside its code."""
    if sum(len(piece) for piece, _ in word) <= width:
        return [word]
    words: list[list[Segment]] = []
    current: list[Segment] = []
    for piece, styles in word:
        for index, part in enumerate(piece.split(" ")):
            if index and current:
                words.append(current)
                current = []
            if part:
                current.append((part, styles))
    if current:
        words.append(current)
    return words


def _is_string_part(token_type: int) -> bool:
    name = tokenize.tok_name.get(token_type, "")
    return name.endswith("_MIDDLE") and name.startswith(("FSTRING", "TSTRING"))


def _token_style(token: tokenize.TokenInfo, previous: str) -> tuple[str, ...] | None:
    kind = token.type
    if kind == tokenize.COMMENT:
        return _CODE_STYLES["comment"]
    if kind == tokenize.NUMBER:
        return _CODE_STYLES["number"]
    name = tokenize.tok_name.get(kind, "")
    if kind == tokenize.STRING or name.startswith(("FSTRING", "TSTRING")):
        return _CODE_STYLES["string"]
    if kind == tokenize.NAME:
        if keyword.iskeyword(token.string):
            return _CODE_STYLES["keyword"]
        if previous in ("def", "class"):
            return _CODE_STYLES["definition"]
        if token.string in _BUILTIN_NAMES and previous != ".":
            return _CODE_STYLES["builtin"]
    return None


def _paragraphs(text: str) -> Iterator[str | list[list[str]]]:
    """Yield each paragraph as one string, or a list as [marker, text] items."""
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if not _LIST_ITEM_RE.match(lines[0]):
            yield " ".join(lines)
            continue
        items: list[list[str]] = []
        for line in lines:
            match = _LIST_ITEM_RE.match(line)
            if match:
                marker = match.group(0).strip()
                marker = "• " if marker in ("-", "*") else marker + " "
                items.append([marker, line[match.end() :]])
            else:
                items[-1][1] += " " + line
        yield items


def _inline(text: str) -> Iterator[tuple[str, tuple[str, ...], bool]]:
    """Split prose into (text, styles, unbreakable) pieces."""
    position = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > position:
            yield text[position : match.start()], (), False
        code, bold, italic, link, url = match.groups()
        if code is not None:
            yield code, ("cyan",), True
        elif bold is not None:
            yield bold, ("bold",), False
        elif italic is not None:
            yield italic, ("italic",), False
        else:
            yield link, ("underline",), False
            yield " ", (), False
            yield f"({url})", ("dim",), True
        position = match.end()
    if position < len(text):
        yield text[position:], (), False


def strip_final_indent(text: str) -> str:
    """Drop the indentation left on a block's last, empty line, as Python's REPL does."""
    short = text.rstrip(" \t")
    if short and text[len(short) - 1] == "\n":
        return short
    return text


class LineReader:
    """Reads statements and single lines from the person at the keyboard.

    In a terminal on Python 3.13 or later, it uses the line editor from Python's own
    REPL, which highlights code as you type, indents blocks for you, and lets you
    edit several lines at once. Anywhere else it falls back to `input()`.
    """

    def __init__(self, namespace: dict, is_incomplete: Callable[[str], bool]):
        self.is_incomplete = is_incomplete
        self._typed = ""  # what watch() has read but not yet returned
        self._multiline: Callable[..., str] | None = None
        if _can_use_python_repl():
            try:
                # _pyrepl is private, so any failure here means "use input()".
                from _pyrepl import readline as pyrepl
                from _pyrepl.simple_interact import check

                if not check():
                    # Tab completion looks names up in `namespace`, which the tutor
                    # clears and refills but never replaces.
                    pyrepl._setup(namespace)
                    self._multiline = pyrepl.multiline_input
            except Exception:
                self._multiline = None
        if self._multiline is None:
            _enable_basic_line_editing()

    @property
    def fancy(self) -> bool:
        return self._multiline is not None

    def statement(self, ps1: str = ">>> ", ps2: str = "... ") -> str:
        """Read one statement, which may span lines. Commands and blank lines come back as typed."""
        sys.stdout.flush()
        if self._multiline is not None:
            try:
                return strip_final_indent(self._multiline(self.is_incomplete, ps1, ps2))
            except EOFError:
                raise
            except KeyboardInterrupt:
                _redraw_interrupted_input()
                raise
            except Exception:
                # The private API changed in this Python. Use input() from now on.
                self._multiline = None
                _enable_basic_line_editing()
        first = input(strip_ansi(ps1))
        if not first.strip() or first.lstrip().startswith(":"):
            return first
        lines = [first]
        while self.is_incomplete("\n".join(lines)):
            lines.append(input(strip_ansi(ps2)))
        return "\n".join(lines)

    def line(self, prompt: str) -> str:
        sys.stdout.flush()
        if self._multiline is None:
            prompt = strip_ansi(prompt)  # editline miscounts the width of colored prompts
        return input(prompt)

    def watch(self, prompt: str, poll: Callable[[], bool], interval: float = 0.25) -> str:
        """Read one line, calling `poll` every `interval` seconds while you haven't typed one.

        `poll` returns True when it printed something, and the prompt is shown again
        below it. This uses the terminal's own line editing, since the REPL's editor
        can't share the screen with output that arrives while you type. Away from a
        terminal it reads a plain line and never polls.
        """
        if not _is_terminal(sys.stdin):
            return input(strip_ansi(prompt))
        sys.stdout.write(prompt)
        sys.stdout.flush()
        while "\n" not in self._typed:
            ready, _, _ = select.select([sys.stdin], [], [], interval)
            if ready:
                chunk = os.read(sys.stdin.fileno(), 4096)
                if not chunk:  # Ctrl-D
                    if not self._typed:
                        raise EOFError
                    self._typed += "\n"
                self._typed += chunk.decode("utf-8", errors="replace")
            elif poll():
                sys.stdout.write(prompt)
                sys.stdout.flush()
        line, self._typed = self._typed.split("\n", 1)
        return line


def _is_terminal(stream) -> bool:
    try:
        return stream.isatty()
    except (AttributeError, ValueError):
        return False


def _redraw_interrupted_input() -> None:
    """After Ctrl-C, leave what was typed on screen, as Python's REPL does."""
    try:
        from _pyrepl.readline import _get_reader

        reader = _get_reader()
        reader.cmpltn_reset()
        if reader.input_trans is reader.isearch_trans:
            reader.do_cmd(("isearch-end", [""]))
        reader.pos = len(reader.get_unicode())
        reader.invalidate_full()
        reader.refresh()
    except Exception:  # private API; the redraw is cosmetic
        pass


def _can_use_python_repl() -> bool:
    if os.environ.get("PYTHON_BASIC_REPL") or sys.version_info < (3, 13):
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def _enable_basic_line_editing() -> None:
    try:
        importlib.import_module("readline")  # importing it gives input() arrow keys and history
    except ImportError:
        pass
