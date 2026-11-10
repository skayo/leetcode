"""The tutor: shows each step, runs what you type, runs your solution files, and saves progress."""

from __future__ import annotations

import builtins
import contextlib
import importlib
import importlib.util
import io
import json
import linecache
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

from .course import Block, Section, Step
from .runner import Runner, Tee, TimeLimitExceeded, split_entries, time_limit
from .terminal import LineReader, Term

CHECK_SECONDS = 2  # for a challenge's checks
RUN_SECONDS = 5  # for the top level of a solution file
HELP = [
    ("Enter", "next step; on a challenge (★), run your file until it passes"),
    (":n", "next step, skipping a challenge"),
    (":b", "back one step"),
    (":r", "show this step again, rerunning its example"),
    (":h", "a hint, on a challenge"),
    (":s", "the solution, on a challenge"),
    (":e", "edit this step's file in your editor here, then run it"),
    (":m", "menu of sections, to jump anywhere"),
    (":q", "save and quit (Ctrl-D works too)"),
]
COMMANDS = {
    "n": "skip",
    "next": "skip",
    "skip": "skip",
    "b": "back",
    "back": "back",
    "r": "rerun",
    "rerun": "rerun",
    "h": "hint",
    "hint": "hint",
    "s": "solution",
    "solution": "solution",
    "e": "edit",
    "edit": "edit",
    "m": "menu",
    "menu": "menu",
    "q": "quit",
    "quit": "quit",
    "exit": "quit",
    "?": "help",
    "help": "help",
}
QUIT_WORDS = {"exit", "quit", "exit()", "quit()"}
BREW_NAMES = {"matplotlib": "python-matplotlib"}


class Quit(Exception):
    """Leaves the tutor from anywhere in the loop."""


class Progress:
    """Where you are and which challenges you've solved, saved as JSON after every change."""

    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        if not isinstance(data, dict) or not isinstance(data.get("sections"), dict):
            return {"position": None, "sections": {}}
        return data

    def save(self) -> None:
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)

    def _section(self, section_id: str) -> dict:
        record = self.data["sections"].setdefault(section_id, {})
        record.setdefault("step", 0)
        record.setdefault("done", False)
        record.setdefault("solved", [])
        return record

    @property
    def position(self) -> tuple[str, int] | None:
        position = self.data.get("position")
        if isinstance(position, list) and len(position) == 2 and isinstance(position[1], int):
            return position[0], position[1]
        return None

    def move_to(self, section_id: str, step: int) -> None:
        self.data["position"] = [section_id, step]
        self._section(section_id)["step"] = step
        self.save()

    def visited(self, section_id: str) -> bool:
        return section_id in self.data["sections"]

    def step_in(self, section_id: str) -> int:
        step = self.data["sections"].get(section_id, {}).get("step", 0)
        return step if isinstance(step, int) else 0

    def is_done(self, section_id: str) -> bool:
        return bool(self.data["sections"].get(section_id, {}).get("done"))

    def mark_done(self, section_id: str) -> None:
        self._section(section_id)["done"] = True
        self.save()

    def is_solved(self, section_id: str, slug: str) -> bool:
        return slug in self.data["sections"].get(section_id, {}).get("solved", [])

    def mark_solved(self, section_id: str, slug: str) -> None:
        solved = self._section(section_id)["solved"]
        if slug not in solved:
            solved.append(slug)
            self.save()


@dataclass
class Visit:
    """What has happened on the current step since it was last shown."""

    solved: bool = False
    hints: int = 0
    stamp: tuple[int, int, int] | None = None  # the solution file when it last ran


@dataclass
class Verdict:
    passed: bool
    message: str = ""
    error: BaseException | None = None  # raised inside your code, so worth a traceback


class Tutor:
    def __init__(
        self,
        sections: list[Section],
        progress: Progress,
        *,
        sandbox: Path,
        solutions: Path,
        launch_dir: Path | None = None,
        term: Term | None = None,
        reader=None,
    ):
        self.sections = sections
        self.progress = progress
        self.sandbox = sandbox
        self.solutions = solutions
        self.launch_dir = launch_dir or Path.cwd()
        self.term = term or Term()
        self.runner = Runner(color=self.term.color)
        # One dict for the whole session: the line editor's tab completion holds on to
        # it, so it gets cleared and refilled between sections, never replaced.
        self.ns: dict = {}
        self.reader = reader or LineReader(self.ns, self.runner.is_incomplete)
        self.index = 0  # which section
        self.step_index = 0
        self.blocked = False  # the section needs a package that isn't installed
        self.visit = Visit()
        self.entered = False
        self.tips_left = 2

    # Running the session

    def run(self, start: int | None = None) -> int:
        """Run until you quit. `start` is a section index to open instead of the saved place."""
        try:
            self._banner()
            try:
                self._open(start)
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt")
            while True:
                self._turn()
        except (Quit, EOFError):
            self._goodbye()
        return 0

    def _open(self, start: int | None) -> None:
        if start is not None:
            self._enter(start, self._resume_step(self.sections[start]))
            return
        saved = self._saved_position()
        if saved is not None:
            self._enter(*saved)
            return
        print()
        self.term.prose("Pick a section to start with. `:m` jumps to any other section later.")
        self._print_menu()
        index = self._pick_section(default=0)
        self._enter(0 if index is None else index, 0)

    def _turn(self) -> None:
        try:
            if self._on_challenge():
                text = self._read_while_watching()
            else:
                text = self.reader.statement(self.term.ps1, self.term.ps2)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
            return
        try:
            self._handle(text)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")

    def _read_while_watching(self) -> str:
        """On a challenge, read input while running your file whenever you save it."""
        first = self.reader.watch(self.term.ps1, self._poll_solution)
        if not first.strip() or first.lstrip().startswith(":"):
            return first
        lines = [first]
        while self.runner.is_incomplete("\n".join(lines)):
            lines.append(self.reader.watch(self.term.ps2, self._poll_solution))
        return "\n".join(lines)

    def _handle(self, text: str) -> None:
        stripped = text.strip()
        if not stripped:
            self.next()
        elif stripped.startswith(":"):
            self.command(stripped[1:])
        elif stripped in QUIT_WORDS:
            raise Quit
        else:
            self._execute(text)

    def command(self, text: str) -> None:
        name = text.strip().split()[0].lower() if text.strip() else "?"
        action = COMMANDS.get(name)
        if action is None:
            self.term.warn(f"There's no :{name} command. Type :? to see them all.")
            return
        getattr(self, action)()

    # Moving around

    def section(self) -> Section:
        return self.sections[self.index]

    def step(self) -> Step:
        return self.section().steps[self.step_index]

    def _on_challenge(self) -> bool:
        return self.entered and not self.blocked and self.step().is_challenge

    def find_section(self, text: str) -> int | None:
        """Find a section by number (from 1), id, or the start of its title."""
        text = text.strip().lower()
        if text.isdigit():
            number = int(text)
            return number - 1 if 1 <= number <= len(self.sections) else None
        for match in (str.startswith, str.__contains__):
            for index, section in enumerate(self.sections):
                if match(section.id, text) or match(section.title.lower(), text):
                    return index
        return None

    def _saved_position(self) -> tuple[int, int] | None:
        position = self.progress.position
        if position is None:
            return None
        section_id, step = position
        for index, section in enumerate(self.sections):
            if section.id == section_id:
                return index, min(max(step, 0), len(section.steps) - 1)
        return None

    def _resume_step(self, section: Section) -> int:
        if self.progress.is_done(section.id):
            return 0
        return min(self.progress.step_in(section.id), len(section.steps) - 1)

    def next(self) -> None:
        """Enter on an empty line: run an unsolved challenge's file, or move on."""
        if self._on_challenge() and not self.visit.solved:
            self._run_solution()
            return
        self.skip()

    def skip(self) -> None:
        if not self.entered:
            self.menu()
        elif self.blocked or self.step_index + 1 >= len(self.section().steps):
            self._leave_section()
        else:
            self.step_index += 1
            self._show_step()

    def back(self) -> None:
        if self.step_index > 0 and not self.blocked:
            self.step_index -= 1
            self._show_step()
        elif self.index > 0:
            previous = self.sections[self.index - 1]
            self._enter(self.index - 1, len(previous.steps) - 1)
        else:
            self.term.note("This is the very first step.")

    def rerun(self) -> None:
        if self.blocked:
            importlib.invalidate_caches()  # notice a package installed since the section opened
            self._enter(self.index, self.step_index)
        else:
            self._show_step()

    def quit(self) -> None:
        raise Quit

    def _leave_section(self) -> None:
        section = self.section()
        if not self.blocked:
            self.progress.mark_done(section.id)
            message = f"{section.title} done"
            total = len(section.challenges)
            if total:
                message += f" · {self._solved_count(section)} of {total} challenges solved"
            print()
            self.term.success(message)
        if self.index + 1 < len(self.sections):
            self._enter(self.index + 1, self._resume_step(self.sections[self.index + 1]))
        else:
            self.term.note("That's the end of the refresher. :m opens the menu if you want to revisit a section.")

    def _enter(self, index: int, step_index: int) -> None:
        self.index = index
        section = self.section()
        self.step_index = min(max(step_index, 0), len(section.steps) - 1)
        self.entered = True
        self.ns.clear()
        self.ns.update({"__name__": "__main__", "__builtins__": builtins})
        print()
        for line in self.term.card(f"{index + 1}  {section.title}", section.part):
            print(line)
        missing = [name for name in section.requires if importlib.util.find_spec(name) is None]
        self.blocked = bool(missing)
        if missing:
            self.progress.move_to(section.id, self.step_index)
            self._show_missing(missing)
            return
        if section.setup:
            setup = "; ".join(line for line in section.setup.splitlines() if line.strip())
            self.term.note(f"Loaded for you: {setup}")
            ok, output = self.runner.run_quietly(section.setup, self.ns)
            if not ok:
                print(output, end="")
        self._show_step()

    def _show_missing(self, missing: list[str]) -> None:
        names = " and ".join(missing)
        verb, pronoun = ("isn't", "it") if len(missing) == 1 else ("aren't", "them")
        print()
        self.term.prose(
            f"This section needs {names}, which {verb} installed for this Python "
            f"({sys.version.split()[0]}). Install {pronoun} from another shell:"
        )
        print()
        print("      " + self.term.paint(install_command(missing), "bold"))
        print()
        self.term.note("Then type :r to try again. Enter skips to the next section, and :m opens the menu.")
        print()

    # Showing a step

    def _show_step(self) -> None:
        section, step = self.section(), self.step()
        self.visit = Visit()
        self.progress.move_to(section.id, self.step_index)
        print()
        print(self.term.rule(step.title, f"{self.step_index + 1}/{len(section.steps)}", star=step.is_challenge))
        for block in step.shown_blocks:
            print()
            self._show_block(block)
        print()
        if step.is_challenge:
            self._show_challenge(section, step)
        elif self.tips_left > 0:
            self.tips_left -= 1
            self.term.note("Your turn: try things at the prompt. Enter on an empty line moves on.")
            print()

    def _show_challenge(self, section: Section, step: Step) -> None:
        path = self.solution_path(step)
        template = solution_file_text(section, step)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(template, encoding="utf-8")
        self.term.prose(f"Your file: `{self._show_path(path)}`")
        self.term.note(
            f"Open it in {editor_name()} in another pane. Each time you save it, it runs here. "
            "Or type :e to edit it in this pane."
        )
        self.term.prose("Enter runs it now · :h hint · :s solution · :n skip", base=("yellow",))
        print()
        self.visit.stamp = file_stamp(path)
        if path.read_text(encoding="utf-8") != template:  # you've worked on it before
            self._run_solution(entering=True)
            print()

    def _show_block(self, block: Block) -> None:
        if block.kind == "text":
            self.term.prose(block.text)
        elif "listing" in block.flags:
            self._listing(block.text)
        elif "script" in block.flags:
            self._listing(block.text)
            self.runner.run(block.text, self.ns, echo=False)
        else:
            self._transcript(block)

    def _listing(self, code: str) -> None:
        bar = self.term.paint("│ ", "dim")
        for line in self.term.code_lines(code):
            print("  " + bar + line)

    def _transcript(self, block: Block) -> None:
        entries = split_entries(block.text)
        last = max((i for i, entry in enumerate(entries) if entry.source is not None), default=-1)
        for index, entry in enumerate(entries):
            for comment in entry.comments:
                print(self.term.ps1 + self.term.highlight(comment))
            if entry.source is None:
                continue
            lines = self.term.code_lines(entry.source)
            print(self.term.ps1 + lines[0])
            for line in lines[1:]:
                print(self.term.ps2 + line)
            if entry.compound:
                print(self.term.ps2)
            if "predict" in block.flags and index == last:
                self._predict(entry.source)
            else:
                self.runner.run(entry.source, self.ns)

    def _predict(self, source: str) -> None:
        question = self.term.paint("  ? ", "yellow", "bold") + "What will this show? "
        try:
            guess = self.reader.line(question + self.term.paint("(Enter to see) ", "dim")).strip()
        except KeyboardInterrupt:  # Ctrl-C here means "just show me"
            print()
            guess = ""
        tee = Tee(sys.stdout)
        with contextlib.redirect_stdout(tee):
            self.runner.run(source, self.ns)
        if not guess or guess.startswith(":"):
            return
        if same_answer(guess, tee.getvalue()):
            self.term.success("Right.")
        else:
            self.term.warn("Not quite. The real answer is above.")

    # Your code and your solution files

    def _execute(self, text: str) -> None:
        try:
            self.runner.run(text, self.ns)
        except SystemExit:
            raise Quit from None

    def solution_path(self, step: Step) -> Path:
        return self.solutions / self.section().path.stem / step.file_name

    def _show_path(self, path: Path) -> str:
        relative = os.path.relpath(path, self.launch_dir)
        if not relative.startswith(".."):
            return relative
        home = str(Path.home())
        return "~" + str(path)[len(home) :] if str(path).startswith(home + os.sep) else str(path)

    def _poll_solution(self) -> bool:
        """Run the solution file if it changed since it last ran. True if anything printed."""
        if not self._on_challenge():
            return False
        path = self.solution_path(self.step())
        stamp = file_stamp(path)
        if stamp is None or stamp == self.visit.stamp:
            return False
        for _ in range(10):  # an editor can take more than one write to save a file
            time.sleep(0.05)
            settled = file_stamp(path)
            if settled == stamp:
                break
            stamp = settled
        sys.stdout.write(self.term.erase_line())
        self._run_solution()
        return True

    def _run_solution(self, *, entering: bool = False) -> None:
        """Run your file the way `python3` would, minus its own checks, then run the step's check."""
        step = self.step()
        path = self.solution_path(step)
        self.visit.stamp = file_stamp(path)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as error:
            self.term.failure(f"Can't read {self._show_path(path)}: {error.strerror}")
            return
        self.term.note(f"ran {path.name} at {time.strftime('%H:%M:%S')}")
        module = {"__name__": "solution", "__file__": str(path), "__builtins__": builtins}
        try:
            with time_limit(RUN_SECONDS):
                ran = self.runner.run(source, module, echo=False, filename=str(path))
        except TimeLimitExceeded:
            self.term.failure(f"Your file ran for over {RUN_SECONDS} seconds, so it was stopped. Is there an infinite loop?")
            return
        except SystemExit:
            self.term.failure("Your file called exit(), so the checks didn't run.")
            return
        if not ran:
            self.term.failure("Your file raised an error, so the checks didn't run.")
            return
        # Your functions are now yours to call at the prompt, too.
        self.ns.update({name: value for name, value in module.items() if not name.startswith("__")})
        verdict = run_check(step, module)
        if verdict.passed:
            self._celebrate(step, entering=entering)
            return
        if verdict.error is not None:
            self.runner.show_error(verdict.error)
        self.term.failure(f"Not yet: {verdict.message}")

    def _celebrate(self, step: Step, *, entering: bool) -> None:
        self.visit.solved = True
        self.progress.mark_solved(self.section().id, step.slug)
        if entering:
            self.term.success("Your file already passes. Enter moves on.")
            return
        self.term.success("Solved!")
        if step.solved_note:
            self.term.prose(step.solved_note)
        self.term.note("Press Enter for the next step.")

    def _solved_count(self, section: Section) -> int:
        return sum(self.progress.is_solved(section.id, step.slug) for step in section.challenges)

    def hint(self) -> None:
        step = self._challenge_or_note("Hints")
        if step is None:
            return
        hints = step.hints
        if self.visit.hints >= len(hints):
            self.term.note("That's every hint. :s shows the solution." if hints else "No hints for this one. :s shows the solution.")
            return
        self.visit.hints += 1
        label = f"Hint {self.visit.hints} of {len(hints)}." if len(hints) > 1 else "Hint."
        self.term.prose(f"**{label}** {hints[self.visit.hints - 1]}")

    def solution(self) -> None:
        step = self._challenge_or_note("Solutions")
        if step is None or step.solution is None:
            return
        self.term.note("One solution:")
        self._listing(step.solution)
        self.term.note("Put it in your file and save to run it.")

    def _challenge_or_note(self, what: str) -> Step | None:
        if not self._on_challenge():
            self.term.note(f"{what} come with challenges, the steps marked ★.")
            return None
        return self.step()

    def edit(self) -> None:
        """Edit the step's file in your editor, in this pane: the solution file on a challenge."""
        if not self.entered or self.blocked:
            return
        editor = find_editor()
        if editor is None:
            self.term.warn("No editor found. Set $EDITOR, for example to nvim, and try again.")
            return
        section, step = self.section(), self.step()
        if step.is_challenge:
            path = self.solution_path(step)
            fresh = solution_file_text(section, step)
        else:
            path = self.sandbox / section.id / f"{step.slug}.py"
            fresh = scratch_file_text(section, step)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(fresh, encoding="utf-8")
        try:
            result = subprocess.run([*shlex.split(editor), str(path)])
        except OSError as error:
            self.term.warn(f"Couldn't start {editor}: {error}")
            return
        if result.returncode != 0:
            self.term.warn(f"{editor_name()} exited with an error, so nothing ran.")
            return
        if step.is_challenge:
            self._run_solution()
            return
        self.term.note(f"Running {self._show_path(path)}")
        try:
            self.runner.run(path.read_text(encoding="utf-8"), self.ns, filename=str(path))
        except SystemExit:
            raise Quit from None

    # Menu, help, and messages

    def menu(self) -> None:
        self._print_menu()
        index = self._pick_section(default=None if self.entered else 0)
        if index is None:
            self.term.note(f"Staying on {self.section().title}.")
            return
        self._enter(index, self._resume_step(self.sections[index]))

    def _pick_section(self, default: int | None) -> int | None:
        hint = f"Enter for {default + 1}" if default is not None else "Enter to stay"
        while True:
            choice = self.reader.line(self.term.paint(f"  Section number or name ({hint}): ", "dim")).strip()
            if not choice:
                return default
            if choice.startswith(":"):
                if COMMANDS.get(choice[1:].strip().lower()) == "quit":
                    raise Quit
                self.term.warn("Type a section number or name, or press Enter.")
                continue
            index = self.find_section(choice)
            if index is not None:
                return index
            self.term.warn(f"No section matches {choice!r}.")

    def _print_menu(self) -> None:
        part = None
        title_width = max(len(section.title) for section in self.sections) + 2
        for index, section in enumerate(self.sections):
            if section.part != part:
                part = section.part
                print()
                print("  " + self.term.paint(part or "Sections", "bold"))
            here = self.entered and index == self.index
            marker = self.term.paint("▸", "magenta") if here else " "
            title = section.title.ljust(title_width)
            print(f"  {marker} {index + 1:>2}  {self.term.paint(title, 'bold') if here else title}{self._status(section)}")
        print()

    def _status(self, section: Section) -> str:
        missing = [name for name in section.requires if importlib.util.find_spec(name) is None]
        if missing:
            return self.term.paint(f"needs {' and '.join(missing)}", "dim")
        parts = []
        if self.progress.is_done(section.id):
            parts.append(self.term.paint("✓", "green"))
        elif self.progress.visited(section.id):
            step = min(self.progress.step_in(section.id), len(section.steps) - 1)
            parts.append(self.term.paint(f"step {step + 1} of {len(section.steps)}", "dim"))
        total = len(section.challenges)
        if total and self.progress.visited(section.id):
            solved = self._solved_count(section)
            parts.append(self.term.paint(f"★ {solved}/{total}", "yellow" if solved == total else "dim"))
        return "  ".join(parts)

    def help(self) -> None:
        print()
        for key, meaning in HELP:
            print("  " + self.term.paint(key.ljust(7), "bold") + meaning)
        print()
        self.term.note(
            "Anything else you type runs as Python. Your progress saves as you go, "
            "so running the refresher again picks up where you left off."
        )
        print()

    def _banner(self) -> None:
        print(self.term.paint("Python Refresher", "bold"))
        self.term.prose(
            "Type Python at the >>> prompt. Enter on an empty line moves on, and :? lists the commands.",
            base=("dim",),
            indent=0,
        )

    def _goodbye(self) -> None:
        print()
        if not self.entered:
            self.term.note("Bye.")
            return
        section = self.section()
        if self.blocked:
            where = section.title
        else:
            where = f"{section.title}, step {self.step_index + 1} of {len(section.steps)}"
        self.term.note(f"Saved. Next time you'll pick up at {where}.")


def run_check(step: Step, namespace: dict) -> Verdict:
    """Run a challenge's check against the names your file defined."""
    env = dict(namespace)
    filename = f"<check {step.slug}>"
    source = str(step.check or "")
    lines = source.splitlines(keepends=True)
    linecache.cache[filename] = (len(source), None, lines, filename)  # so tracebacks show the check's lines
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink), time_limit(CHECK_SECONDS):
            exec(compile(source, filename, "exec"), env)
    except AssertionError as error:
        return Verdict(False, str(error) or "a check failed")
    except TimeLimitExceeded:
        return Verdict(False, f"your code ran for over {CHECK_SECONDS} seconds. Is there an infinite loop?")
    except Exception as error:
        if not _raised_in(error, filename):
            return Verdict(False, f"your code raised {type(error).__name__}: {error}", error)
        if isinstance(error, NameError) and getattr(error, "name", None):
            return Verdict(False, f"{error.name} isn't defined")
        return Verdict(False, f"{type(error).__name__}: {error}")
    return Verdict(True)


def _raised_in(error: BaseException, filename: str) -> bool:
    """True when the innermost frame of the traceback is in `filename`."""
    trace = error.__traceback__
    while trace is not None and trace.tb_next is not None:
        trace = trace.tb_next
    return trace is not None and trace.tb_frame.f_code.co_filename == filename


def solution_file_text(section: Section, step: Step, body: str | None = None) -> str:
    """The file a challenge is solved in: the problem as comments, your code, then the checks.

    `body` replaces the starter code, which the tests use to put the solution in.
    """
    title = re.sub(r"^your turn:\s*", "", step.title, flags=re.IGNORECASE)
    lines = [f"# {title[:1].upper()}{title[1:]}", f"# Python refresher, {section.title}", "#"]
    for block in step.shown_blocks:
        if block.kind == "text":
            lines += _comment_lines(block.text)
        else:
            lines += ["#     " + line if line.strip() else "#" for line in block.text.rstrip("\n").split("\n")]
        lines.append("#")
    lines.append("# Save the file and the refresher runs it, or run it yourself with python3.")
    parts = ["\n".join(lines) + "\n"]
    if section.setup:
        parts.append("\n" + section.setup)
    parts.append("\n\n" + ((step.starter or "") if body is None else body))
    parts.append('\n\nif __name__ == "__main__":\n    # Checks. Running this file runs them.\n')
    parts.append(textwrap.indent(step.check or "", "    "))
    parts.append('    print("All checks pass.")\n')
    return "".join(parts)


def scratch_file_text(section: Section, step: Step) -> str:
    return (
        f"# {section.title}: {step.title}\n"
        "# Save and quit to run this file in the refresher (in vim or nvim, type :wq).\n"
        "# Variables from the lesson, and anything you made at the prompt, are available.\n\n"
    )


def _comment_lines(markdown: str) -> list[str]:
    """Turn lesson prose into wrapped comment lines."""
    out: list[str] = []
    for number, paragraph in enumerate(re.split(r"\n\s*\n", markdown.strip())):
        if number:
            out.append("#")
        lines = [line.strip() for line in paragraph.replace("**", "").splitlines() if line.strip()]
        if lines and lines[0].startswith("- "):
            items: list[str] = []
            for line in lines:
                if line.startswith("- "):
                    items.append(line[2:])
                else:
                    items[-1] += " " + line
            for item in items:
                out += _wrap_comment(item, "# - ", "#   ")
        else:
            out += _wrap_comment(" ".join(lines), "# ", "# ")
    return out


def _wrap_comment(text: str, first: str, rest: str) -> list[str]:
    return textwrap.wrap(
        text,
        width=79,
        initial_indent=first,
        subsequent_indent=rest,
        break_long_words=False,
        break_on_hyphens=False,
    )


def file_stamp(path: Path) -> tuple[int, int, int] | None:
    """What changes when a file is saved. Neovim saves by writing a new file, so the inode counts."""
    try:
        info = path.stat()
    except OSError:
        return None
    return (info.st_ino, info.st_mtime_ns, info.st_size)


def same_answer(guess: str, actual: str) -> bool:
    """Compare a prediction with real output, ignoring spaces, quote style, and case."""

    def normalize(text: str) -> str:
        text = text.strip()
        wrapped = re.fullmatch(r"(?:np\.\w+|array)\((.*)\)", text, re.DOTALL)
        if wrapped:
            text = wrapped.group(1)
        return re.sub(r"\s+", "", text).replace('"', "'").lower()

    guess, actual = normalize(guess), normalize(actual)
    return bool(guess) and (guess == actual or guess.strip("'") == actual.strip("'"))


def find_editor() -> str | None:
    """The editor command: $VISUAL, then $EDITOR, then the first of nvim, vim, vi, nano."""
    for variable in ("VISUAL", "EDITOR"):
        value = os.environ.get(variable, "").strip()
        if value:
            return value
    return next((name for name in ("nvim", "vim", "vi", "nano") if shutil.which(name)), None)


def editor_name() -> str:
    editor = find_editor()
    if not editor:
        return "your editor"
    words = shlex.split(editor)
    return Path(words[0]).name if words else "your editor"


def install_command(packages: list[str]) -> str:
    """The command that installs `packages` for the Python running the tutor."""
    homebrew = sys.prefix == sys.base_prefix and "/Cellar/python@" in os.path.realpath(sys.executable)
    if homebrew:
        return "brew install " + " ".join(BREW_NAMES.get(name, name) for name in packages)
    return "python3 -m pip install " + " ".join(packages)
