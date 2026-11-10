"""Loads the lessons: one Markdown file per section, split into steps by `##` headings.

A lesson file looks like this:

    ---
    part: NumPy
    requires: numpy
    ---

    # Section title

    ```python setup
    import numpy as np
    ```

    ## Step title

    Prose, with `inline code`, **bold**, *italic*, and lists that start with "- ".

    ```python
    a = np.array([1, 2, 3])
    a * 2
    ```

Front matter is optional. `part` groups sections in the menu, and `requires` lists
packages the section can't run without.

A `python setup` block runs out of sight whenever the section starts. Other `python`
blocks run as a REPL transcript when their step is shown. These flags change that:

- `predict`: before running the last statement, ask what it will show.
- `error`: the block is meant to raise, to show an error message.
- `listing`: show the code without running it.
- `script`: show the code as a listing, then run it all at once.

A step with a `check` block is a challenge, which you solve in a file of your own. The
tutor writes that file from the step: its prose and listings as comments, the `starter`
code to fill in, and the check under `if __name__ == "__main__":`, so `python3` can run
it. The file is named after the step, so "Your turn: two sum" is `two_sum.py`. Each
time you save the file, the tutor runs it and then the check, which passes when it
raises nothing; an assert's message says what's still wrong. A challenge needs a
`starter`, a `check`, and a `solution` that replaces the starter. It can also have
`hint` blocks, shown one at a time, and a `solved` note, shown once it passes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PYTHON_FLAGS = frozenset({"setup", "predict", "error", "listing", "script"})
CHALLENGE_KINDS = frozenset({"check", "hint", "solution", "solved", "starter"})
PROSE_KINDS = frozenset({"hint", "solved"})  # Markdown, like the text between blocks
FRONT_MATTER_KEYS = frozenset({"part", "requires"})
SHOWN_KINDS = frozenset({"text", "python"})


class LessonError(ValueError):
    """A lesson file doesn't follow the format above."""


@dataclass(frozen=True)
class Block:
    kind: str  # "text", "python", or one of CHALLENGE_KINDS
    text: str
    flags: frozenset[str] = frozenset()
    line: int = 0

    @property
    def runs(self) -> bool:
        return self.kind == "python" and "listing" not in self.flags


@dataclass
class Step:
    title: str
    slug: str
    line: int
    blocks: list[Block] = field(default_factory=list)

    def _text_of(self, kind: str) -> str | None:
        return next((b.text for b in self.blocks if b.kind == kind), None)

    @property
    def shown_blocks(self) -> list[Block]:
        return [b for b in self.blocks if b.kind in SHOWN_KINDS]

    @property
    def check(self) -> str | None:
        return self._text_of("check")

    @property
    def is_challenge(self) -> bool:
        return self.check is not None

    @property
    def hints(self) -> list[str]:
        return [b.text for b in self.blocks if b.kind == "hint"]

    @property
    def solution(self) -> str | None:
        return self._text_of("solution")

    @property
    def solved_note(self) -> str | None:
        return self._text_of("solved")

    @property
    def starter(self) -> str | None:
        return self._text_of("starter")

    @property
    def file_name(self) -> str:
        """Where a challenge is solved: "Your turn: two sum" is two_sum.py."""
        return re.sub(r"^your-turn-", "", self.slug).replace("-", "_") + ".py"


@dataclass
class Section:
    id: str
    title: str
    part: str
    requires: tuple[str, ...]
    setup: str | None
    steps: list[Step]
    path: Path

    @property
    def challenges(self) -> list[Step]:
        return [step for step in self.steps if step.is_challenge]


def load_course(directory: Path) -> list[Section]:
    """Parse every lesson in `directory`, in file name order."""
    sections = [parse_lesson(path) for path in sorted(directory.glob("*.md"))]
    if not sections:
        raise LessonError(f"no lessons found in {directory}")
    seen: set[str] = set()
    for section in sections:
        if section.id in seen:
            raise LessonError(f"{section.path.name}: another lesson already uses the id {section.id!r}")
        seen.add(section.id)
    return sections


def parse_lesson(path: Path, text: str | None = None) -> Section:
    if text is None:
        text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    def fail(line: int, message: str) -> LessonError:
        return LessonError(f"{path.name}:{line}: {message}")

    meta, first_line = _front_matter(lines, path)
    title: str | None = None
    setup: str | None = None
    steps: list[Step] = []
    prose: list[str] = []
    prose_start = 0
    fence: tuple[str, frozenset[str], int, list[str]] | None = None

    def flush_prose() -> None:
        nonlocal prose_start
        if any(line.strip() for line in prose):
            if not steps:
                raise fail(prose_start, "text before the first ## step heading")
            steps[-1].blocks.append(Block("text", "\n".join(prose).strip(), line=prose_start))
        prose.clear()

    for number, line in enumerate(lines[first_line:], start=first_line + 1):
        if fence is not None:
            if line.strip() == "```":
                kind, flags, start, body = fence
                content = "\n".join(body).strip()
                if kind not in PROSE_KINDS:
                    content = "\n".join(body).strip("\n") + "\n"
                if "setup" in flags:
                    if steps:
                        raise fail(start, "a python setup block must come before the first step")
                    if setup is not None:
                        raise fail(start, "only one python setup block per lesson")
                    setup = content
                else:
                    steps[-1].blocks.append(Block(kind, content, flags, start))
                fence = None
            else:
                fence[3].append(line)
            continue
        if line.startswith("```"):
            flush_prose()
            words = line[3:].split()
            kind = words[0] if words else ""
            flags = frozenset(words[1:])
            if kind == "python":
                unknown = flags - PYTHON_FLAGS
                if unknown:
                    raise fail(number, f"unknown python flag(s): {', '.join(sorted(unknown))}")
                if len(flags & {"setup", "listing", "script", "predict"}) > 1:
                    raise fail(number, f"these flags don't combine: {' '.join(sorted(flags))}")
            elif kind in CHALLENGE_KINDS:
                if flags:
                    raise fail(number, f"{kind} blocks take no flags")
            else:
                raise fail(number, f"unknown block type {kind!r}")
            if not steps and "setup" not in flags:
                raise fail(number, "code before the first ## step heading")
            fence = (kind, flags, number, [])
            continue
        if line.startswith("# "):
            if title is not None:
                raise fail(number, "a lesson has one # title")
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            flush_prose()
            step_title = line[3:].strip()
            steps.append(Step(step_title, _slug(step_title), number))
            continue
        if not prose:
            prose_start = number
        prose.append(line)

    if fence is not None:
        raise fail(fence[2], "this code block is never closed")
    flush_prose()

    if title is None:
        raise fail(1, "missing the # title")
    if not steps:
        raise fail(1, "no ## steps")
    _check_steps(steps, fail)
    requires = tuple(meta.get("requires", "").replace(",", " ").split())
    return Section(
        id=re.sub(r"^\d+[-_]", "", path.stem),
        title=title,
        part=meta.get("part", ""),
        requires=requires,
        setup=setup,
        steps=steps,
        path=path,
    )


def _front_matter(lines: list[str], path: Path) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            return meta, index + 1
        key, colon, value = line.partition(":")
        key = key.strip()
        if not colon or key not in FRONT_MATTER_KEYS:
            raise LessonError(f"{path.name}:{index + 1}: front matter takes {', '.join(sorted(FRONT_MATTER_KEYS))}")
        meta[key] = value.strip()
    raise LessonError(f"{path.name}: the front matter is never closed with ---")


def _check_steps(steps: list[Step], fail) -> None:
    slugs: set[str] = set()
    for step in steps:
        if step.slug in slugs:
            raise fail(step.line, f"two steps share the title {step.title!r}")
        slugs.add(step.slug)
        if not step.shown_blocks:
            raise fail(step.line, "this step shows nothing")
        kinds = [block.kind for block in step.blocks]
        if kinds.count("check") > 1 or kinds.count("solution") > 1 or kinds.count("starter") > 1:
            raise fail(step.line, "a step has at most one check, solution, and starter")
        extras = CHALLENGE_KINDS & set(kinds)
        if extras and "check" not in kinds:
            raise fail(step.line, f"{', '.join(sorted(extras))} without a check block")
        for needed in ("starter", "solution"):
            if "check" in kinds and needed not in kinds:
                raise fail(step.line, f"a challenge needs a {needed} block")


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
