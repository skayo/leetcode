"""Runs code the way the Python REPL does.

Statements run one after another, the value of the last expression is echoed, and an
error prints a traceback that starts in your code rather than in the tutor's.
"""

from __future__ import annotations

import ast
import codeop
import contextlib
import io
import linecache
import os
import signal
import sys
import threading
import traceback
from dataclasses import dataclass

from .terminal import strip_final_indent

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_COMPOUND = (
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.If,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Match,
) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())


class TimeLimitExceeded(BaseException):
    """Code ran past its time limit. A BaseException, so `except Exception` in your code can't catch it."""


@contextlib.contextmanager
def time_limit(seconds: float):
    """Raise TimeLimitExceeded in the main thread if the block runs longer than `seconds`."""
    if not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        yield
        return

    def interrupt(_signum, _frame):
        raise TimeLimitExceeded

    previous = signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@dataclass
class Entry:
    """One thing typed at the REPL: comment lines, then a statement, if any."""

    comments: list[str]
    source: str | None
    compound: bool = False  # a block, which the REPL ends with an empty "..." line


def split_entries(source: str) -> list[Entry]:
    """Split a code block into the statements someone would type at the REPL."""
    lines = source.rstrip("\n").split("\n")
    spans: list[list] = []  # [first line, end line, compound]
    for statement in ast.parse(source).body:
        decorators = getattr(statement, "decorator_list", [])
        start = min([statement.lineno] + [d.lineno for d in decorators]) - 1
        end = statement.end_lineno or statement.lineno
        compound = isinstance(statement, _COMPOUND)
        if spans and start < spans[-1][1]:  # shares a line with the one before, like a; b
            spans[-1][1] = max(spans[-1][1], end)
            spans[-1][2] = spans[-1][2] or compound
        else:
            spans.append([start, end, compound])
    entries = []
    cursor = 0
    for start, end, compound in spans:
        comments = [line for line in lines[cursor:start] if line.strip()]
        entries.append(Entry(comments, "\n".join(lines[start:end]), compound))
        cursor = end
    trailing = [line for line in lines[cursor:] if line.strip()]
    if trailing:
        entries.append(Entry(trailing, None))
    return entries


class Runner:
    def __init__(self, color: bool = False):
        self.color = color
        self._count = 0
        self._compiler = codeop.CommandCompiler()

    def is_incomplete(self, text: str) -> bool:
        """True when `text` is the start of a statement that needs more lines.

        This mirrors how Python's REPL decides whether Enter runs the code or starts
        a new line. Tutor commands, which start with a colon, are always complete.
        """
        if text.lstrip().startswith(":"):
            return False
        source = strip_final_indent(text)
        try:
            code = self._compiler(source, "<input>", "single")
        except (SyntaxError, ValueError, OverflowError):
            lines = source.splitlines(keepends=True)
            if len(lines) <= 1:
                return False
            last = lines[-1]
            unfinished = last.startswith((" ", "\t")) or last.strip() != ""
            return unfinished and not last.endswith("\n")
        return code is None

    def run(
        self,
        source: str,
        namespace: dict,
        *,
        echo: bool = True,
        filename: str | None = None,
    ) -> bool:
        """Run `source` in `namespace`, and return False if it didn't compile or raised.

        With `echo`, the last statement's value is printed, as at the REPL. Pass a
        `filename` for code that lives in a real file, so tracebacks show its lines.
        """
        if filename is None:
            self._count += 1
            filename = f"<python-input-{self._count}>"
            linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)
        try:
            tree = ast.parse(source, filename, "exec")
        except (SyntaxError, ValueError, OverflowError) as error:
            self.show_error(error)
            return False
        for index, statement in enumerate(tree.body):
            single = echo and index == len(tree.body) - 1
            try:
                if single:
                    code = compile(ast.Interactive([statement]), filename, "single")
                else:
                    code = compile(ast.Module([statement], []), filename, "exec")
            except (SyntaxError, ValueError, OverflowError) as error:
                self.show_error(error)
                return False
            try:
                exec(code, namespace)
            except (SystemExit, TimeLimitExceeded):
                raise
            except BaseException as error:  # KeyboardInterrupt included, as at the REPL
                self.show_error(error)
                return False
        return True

    def run_quietly(self, source: str, namespace: dict) -> tuple[bool, str]:
        """Run `source` without showing anything, and return (ok, everything it printed)."""
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            ok = self.run(source, namespace, echo=False)
        return ok, sink.getvalue()

    def show_error(self, error: BaseException) -> None:
        """Print a traceback the way the REPL does, leaving out the tutor's own frames."""
        trace = error.__traceback__
        while trace is not None and _is_ours(trace.tb_frame.f_code.co_filename):
            trace = trace.tb_next
        error.__traceback__ = trace
        # Like the REPL, keep the error around for `import pdb; pdb.pm()`.
        sys.last_exc = error
        sys.last_type, sys.last_value, sys.last_traceback = type(error), error, trace
        try:
            lines = traceback.format_exception(  # pyright: ignore[reportCallIssue]
                type(error), error, trace, colorize=self.color
            )
        except TypeError:  # Python before 3.13 has no colorize
            lines = traceback.format_exception(type(error), error, trace)
        sys.stdout.flush()
        sys.stderr.write("".join(lines))
        sys.stderr.flush()


def _is_ours(filename: str) -> bool:
    """True for the tutor's own source files, whose frames tracebacks leave out."""
    if filename.startswith("<"):
        return False
    return os.path.dirname(os.path.abspath(filename)) == _PACKAGE_DIR


class Tee(io.TextIOBase):
    """Passes writes through to `stream` and keeps a copy."""

    def __init__(self, stream):
        self._stream = stream
        self._copy = io.StringIO()

    def write(self, text: str) -> int:
        self._stream.write(text)
        self._copy.write(text)
        return len(text)

    def flush(self) -> None:
        self._stream.flush()

    def isatty(self) -> bool:
        return self._stream.isatty()

    def getvalue(self) -> str:
        return self._copy.getvalue()
