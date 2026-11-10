"""Tests for the refresher: the lessons, the REPL runner, and the tutor driven by scripted input.

Run them from the folder above this one:

    python3 -m unittest refresher.test_refresher
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Callable

os.environ.setdefault("MPLBACKEND", "Agg")  # so plt.show() never opens a window here

from refresher.course import Block, LessonError, Step, load_course, parse_lesson  # noqa: E402
from refresher.runner import Runner, TimeLimitExceeded, split_entries, time_limit  # noqa: E402
from refresher.terminal import Term, strip_ansi  # noqa: E402
from refresher.tutor import Progress, Tutor, run_check, same_answer, solution_file_text  # noqa: E402

LESSONS = Path(__file__).resolve().parent / "lessons"
COURSE = load_course(LESSONS)
DICTIONARIES = next(section for section in COURSE if section.id == "dictionaries")


def missing_packages(section) -> list[str]:
    return [name for name in section.requires if importlib.util.find_spec(name) is None]


def run_statements(runner: Runner, source: str, ns: dict) -> tuple[list[bool], str]:
    """Run each REPL entry of `source` like the tutor does. Returns each entry's result and all output."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        results = [runner.run(entry.source, ns) for entry in split_entries(source) if entry.source is not None]
    return results, out.getvalue()


def solution_of(section_id: str, slug: str) -> tuple:
    section = next(s for s in COURSE if s.id == section_id)
    step = next(s for s in section.steps if s.slug == slug)
    return section, step


class InTempDir(unittest.TestCase):
    """Runs each test in its own empty folder, since lessons write files."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()


class LessonTests(InTempDir):
    def test_examples_run_and_every_challenge_can_be_solved(self):
        runner = Runner()
        for section in COURSE:
            with self.subTest(section=section.id):
                if missing_packages(section):
                    self.skipTest(f"{section.id} needs {', '.join(missing_packages(section))}")
                for step in section.steps:
                    # A fresh namespace per step, as when you resume in a new session.
                    self._run_step(runner, section, step, self._fresh(runner, section))

    def _fresh(self, runner: Runner, section) -> dict:
        ns = {"__name__": "__main__"}
        if section.setup:
            ok, output = runner.run_quietly(section.setup, ns)
            self.assertTrue(ok, output)
        return ns

    def _run_step(self, runner: Runner, section, step: Step, ns: dict) -> None:
        where = f"{section.path.name}, step {step.title!r}"
        for block in step.shown_blocks:
            if not block.runs:
                continue
            if "script" in block.flags:
                ok, output = runner.run_quietly(block.text, ns)
                self.assertTrue(ok, f"{where}: {output}")
                continue
            sources = [entry.source for entry in split_entries(block.text) if entry.source is not None]
            if "predict" in block.flags:
                results, output = run_statements(runner, "\n".join(sources[:-1]), ns)
                self.assertTrue(all(results), f"{where}: {output}")
                results, output = run_statements(runner, sources[-1], ns)
                self.assertTrue(all(results), f"{where}: {output}")
                self.assertEqual(len(output.strip().splitlines()), 1, f"{where}: predict needs one line, got {output!r}")
                continue
            results, output = run_statements(runner, block.text, ns)
            if "error" in block.flags:
                self.assertFalse(all(results), f"{where}: an error block ran cleanly")
                self.assertIn("Traceback", output, where)
            else:
                self.assertTrue(all(results), f"{where}: {output}")
        if step.is_challenge:
            starter = self._fresh(runner, section)
            ok, output = runner.run_quietly(step.starter or "", starter)
            self.assertTrue(ok, f"{where}: the starter doesn't run: {output}")
            self.assertFalse(run_check(step, starter).passed, f"{where}: the starter already passes")
            solved = self._fresh(runner, section)
            ok, output = runner.run_quietly(step.solution or "", solved)
            self.assertTrue(ok, f"{where}: the solution doesn't run: {output}")
            verdict = run_check(step, solved)
            self.assertTrue(verdict.passed, f"{where}: the solution fails its check: {verdict.message}")

    def test_solution_files_run_on_their_own(self):
        for section in COURSE:
            for step in section.challenges:
                with self.subTest(section=section.id, step=step.title):
                    if missing_packages(section):
                        self.skipTest(f"{section.id} needs {', '.join(missing_packages(section))}")
                    path = self.tmp / step.file_name
                    path.write_text(solution_file_text(section, step), encoding="utf-8")
                    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0, "the starter file passes its checks")
                    path.write_text(solution_file_text(section, step, body=step.solution), encoding="utf-8")
                    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("All checks pass.", result.stdout)

    def test_challenges_have_hints_and_every_assert_explains_itself(self):
        for section in COURSE:
            for step in section.challenges:
                with self.subTest(section=section.id, step=step.title):
                    self.assertTrue(step.hints, "a challenge needs at least one hint")
                    for node in ast.walk(ast.parse(step.check or "")):
                        if isinstance(node, ast.Assert):
                            self.assertIsNotNone(node.msg, f"line {node.lineno} of the check has no message")

    def test_lessons_never_use_dashes_as_punctuation(self):
        for path in sorted(LESSONS.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for dash in ("\u2014", "\u2013", " -- "):
                self.assertNotIn(dash, text, path.name)

    def test_highlighting_never_changes_the_code(self):
        term = Term(color=True)
        for section in COURSE:
            for step in section.steps:
                for block in step.blocks:
                    if block.kind in ("python", "starter", "solution", "check"):
                        self.assertEqual(strip_ansi(term.highlight(block.text)), block.text)

    def test_prose_fits_the_width(self):
        for width in (40, 60, 88):
            term = Term(color=True, width=width)
            for section in COURSE:
                for step in section.steps:
                    for block in step.blocks:
                        if block.kind not in ("text", "hint", "solved"):
                            continue
                        for line in term.prose_lines(block.text):
                            plain = strip_ansi(line)
                            # Only a single unbreakable piece of code may run past the edge.
                            if len(plain) > width:
                                self.assertNotIn(" ", plain.strip(), f"{section.id}: {plain!r}")


class ParserTests(unittest.TestCase):
    def parse(self, text: str):
        return parse_lesson(Path("99-example.md"), text)

    def test_reads_front_matter_setup_steps_and_blocks(self):
        section = self.parse(
            "---\npart: NumPy\nrequires: numpy, scipy\n---\n\n# Title\n\n"
            "```python setup\nimport numpy as np\n```\n\n"
            "## One\n\nSome *prose*.\n\n```python predict\n1 + 1\n```\n\nMore prose.\n\n"
            "## Your turn: two words\n\nDo it.\n\n```starter\nx = 0\n```\n\n"
            "```check\nassert x == 1, 'x'\n```\n\n```hint\nTry harder.\n```\n\n```solution\nx = 1\n```\n"
        )
        self.assertEqual(section.id, "example")
        self.assertEqual(section.part, "NumPy")
        self.assertEqual(section.requires, ("numpy", "scipy"))
        self.assertEqual(section.setup, "import numpy as np\n")
        one, two = section.steps
        self.assertEqual([b.kind for b in one.blocks], ["text", "python", "text"])
        self.assertEqual(one.blocks[1].flags, {"predict"})
        self.assertTrue(two.is_challenge)
        self.assertEqual(two.slug, "your-turn-two-words")
        self.assertEqual(two.file_name, "two_words.py")
        self.assertEqual(two.hints, ["Try harder."])
        self.assertEqual(two.solution, "x = 1\n")
        self.assertEqual([b.kind for b in two.shown_blocks], ["text"])

    def test_rejects_mistakes(self):
        bad = {
            "text before the first": "# T\n\nLoose text.\n\n## S\n\nx\n",
            "unknown python flag": "# T\n\n## S\n\n```python fancy\n1\n```\n",
            "without a check": "# T\n\n## S\n\nx\n\n```hint\nh\n```\n",
            "needs a starter": "# T\n\n## S\n\nx\n\n```check\nassert 1, 'm'\n```\n",
            "needs a solution": "# T\n\n## S\n\nx\n\n```starter\nx = 0\n```\n\n```check\nassert 1, 'm'\n```\n",
            "never closed": "# T\n\n## S\n\n```python\n1\n",
            "share the title": "# T\n\n## S\n\nx\n\n## S\n\ny\n",
        }
        for message, text in bad.items():
            with self.subTest(message), self.assertRaisesRegex(LessonError, message):
                self.parse(text)


class RunnerTests(unittest.TestCase):
    def run_code(self, source: str, ns: dict | None = None) -> tuple[bool, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            ok = Runner().run(source, {} if ns is None else ns)
        return ok, out.getvalue()

    def test_echoes_only_the_last_expression_like_the_repl(self):
        self.assertEqual(self.run_code("1 + 1\n'two'"), (True, "'two'\n"))

    def test_none_is_not_echoed(self):
        self.assertEqual(self.run_code("None"), (True, ""))

    def test_errors_show_a_traceback_of_your_code_only(self):
        ok, output = self.run_code("x = 1\n1 / 0")
        self.assertFalse(ok)
        self.assertIn("ZeroDivisionError", output)
        self.assertIn("1 / 0", output)  # the source line, from linecache
        self.assertNotIn("runner.py", output)

    def test_syntax_errors_are_reported(self):
        ok, output = self.run_code("d[")
        self.assertFalse(ok)
        self.assertIn("SyntaxError", output)

    def test_exit_and_time_limits_pass_through(self):
        with self.assertRaises(SystemExit):
            Runner().run("exit()", {"exit": exit})
        with self.assertRaises(TimeLimitExceeded), time_limit(0.2):
            Runner().run("while True:\n    pass\n", {})

    def test_knows_when_a_statement_needs_more_lines(self):
        runner = Runner()
        self.assertTrue(runner.is_incomplete("for x in range(3):"))
        self.assertTrue(runner.is_incomplete("for x in range(3):\n    print(x)"))
        self.assertFalse(runner.is_incomplete("for x in range(3):\n    print(x)\n"))
        self.assertTrue(runner.is_incomplete("d = {"))
        self.assertFalse(runner.is_incomplete("x = 1"))
        self.assertFalse(runner.is_incomplete(":b"))
        self.assertFalse(runner.is_incomplete("x = = 1"))

    def test_splits_a_block_into_repl_entries(self):
        entries = split_entries("# a comment\nx = 1; y = 2\nfor i in range(2):\n    print(i)\n# trailing\n")
        self.assertEqual([e.comments for e in entries], [["# a comment"], [], ["# trailing"]])
        self.assertEqual([e.source for e in entries], ["x = 1; y = 2", "for i in range(2):\n    print(i)", None])
        self.assertEqual([e.compound for e in entries], [False, True, False])

    def test_decorators_stay_with_their_function(self):
        entries = split_entries("@dataclass\nclass P:\n    x: int\nP(1)\n")
        self.assertEqual(entries[0].source, "@dataclass\nclass P:\n    x: int")


class CheckTests(unittest.TestCase):
    def step(self, check: str) -> Step:
        return Step("Your turn", "your-turn", 1, blocks=[Block("check", check)])

    def test_reports_the_assert_message(self):
        verdict = run_check(self.step("assert x == 2, 'x should be 2'"), {"x": 1})
        self.assertEqual((verdict.passed, verdict.message), (False, "x should be 2"))

    def test_names_what_isnt_defined(self):
        self.assertEqual(run_check(self.step("assert counts == {}, 'm'"), {}).message, "counts isn't defined")

    def test_keeps_errors_inside_your_code_for_a_traceback(self):
        ns = {}
        exec("def f():\n    return missing_name\n", ns)
        verdict = run_check(self.step("assert f() == 1, 'm'"), ns)
        self.assertFalse(verdict.passed)
        self.assertIn("your code raised NameError", verdict.message)
        self.assertIsInstance(verdict.error, NameError)

    def test_stops_an_infinite_loop(self):
        ns = {}
        exec("def spin():\n    while True:\n        try:\n            pass\n        except Exception:\n            pass\n", ns)
        verdict = run_check(self.step("spin()"), ns)
        self.assertFalse(verdict.passed)
        self.assertIn("infinite loop", verdict.message)

    def test_cannot_change_your_variables(self):
        ns = {"x": 1}
        run_check(self.step("x = 99\nassert False, 'm'"), ns)
        self.assertEqual(ns["x"], 1)

    def test_predictions_ignore_spacing_quotes_and_wrappers(self):
        self.assertTrue(same_answer("[2,3]", "[2, 3]\n"))
        self.assertTrue(same_answer("x-y-z", "'x-y-z'\n"))
        self.assertTrue(same_answer('"a"', "'a'\n"))
        self.assertTrue(same_answer("false", "False\n"))
        self.assertTrue(same_answer("[3, 7]", "array([3, 7])\n"))
        self.assertTrue(same_answer("10", "np.int64(10)\n"))
        self.assertFalse(same_answer("[2, 4]", "[2, 3]\n"))
        self.assertFalse(same_answer("", "[2, 3]\n"))


class FakeReader:
    """Feeds the tutor scripted input, then Ctrl-D.

    A callable in the input stands for something you do outside the tutor, like saving a
    file in your editor. It runs while the tutor watches, and then the tutor polls.
    """

    def __init__(self, inputs: list[str | Callable[[], object]]):
        self.inputs = list(inputs)

    def statement(self, _ps1: str = "", _ps2: str = "") -> str:
        return self._next()

    def line(self, _prompt: str) -> str:
        return self._next()

    def watch(self, _prompt: str, poll: Callable[[], bool]) -> str:
        while self.inputs and callable(self.inputs[0]):
            action = self.inputs.pop(0)
            if callable(action):
                action()
            poll()
        return self._next()

    def _next(self) -> str:
        if not self.inputs:
            raise EOFError
        item = self.inputs.pop(0)
        assert isinstance(item, str), f"expected typed input, got {item!r}"
        return item


class TutorTests(InTempDir):
    def drive(self, inputs: list, *, at: tuple[str, str] | None = None, sections=None) -> tuple[str, Tutor]:
        """Run the tutor on scripted input, optionally starting at (section id, step slug)."""
        sections = sections or COURSE
        progress = Progress(self.tmp / "progress.json")
        if at is not None:
            section = next(s for s in sections if s.id == at[0])
            step = next(i for i, s in enumerate(section.steps) if s.slug == at[1])
            progress.move_to(section.id, step)
        sandbox = self.tmp / "sandbox"
        sandbox.mkdir(exist_ok=True)
        tutor = Tutor(
            sections,
            progress,
            sandbox=sandbox,
            solutions=self.tmp / "solutions",
            launch_dir=self.tmp,
            term=Term(color=False, width=80),
            reader=FakeReader(inputs),
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            tutor.run()
        return out.getvalue(), tutor

    def solution_file(self, slug: str) -> Path:
        return self.tmp / "solutions" / "05-dictionaries" / f"{slug.removeprefix('your-turn-').replace('-', '_')}.py"

    def save(self, slug: str, body: str) -> Callable[[], None]:
        """Stands for writing `body` into a challenge's file and saving it in your editor."""
        section, step = solution_of("dictionaries", slug)

        def write() -> None:
            self.solution_file(slug).write_text(solution_file_text(section, step, body=body), encoding="utf-8")

        return write

    def test_runs_your_code_moves_between_steps_and_saves_the_position(self):
        output, _ = self.drive(["d", "", ":b", ":q"], at=("dictionaries", "add-change-and-remove"))
        self.assertIn(">>> d['fish'] = 'wet'", output)  # the example, as a transcript
        self.assertIn("{'cat': 'fluffy', 'fish': 'wet'}", output)  # what typing d echoed
        self.assertIn("KeyError: 'monkey'", output)  # the next step's error example
        self.assertEqual(output.count("── Add, change, and remove"), 2)  # shown again after :b
        self.assertIn("Saved. Next time you'll pick up at Dictionaries, step 2 of 11.", output)
        self.assertEqual(Progress(self.tmp / "progress.json").position, ("dictionaries", 1))

    def test_a_prediction_gets_a_verdict(self):
        output, _ = self.drive(["False", ":q"], at=("dictionaries", "look-things-up"))
        self.assertIn("✓ Right.", output)
        output, _ = self.drive(["True", ":q"], at=("dictionaries", "look-things-up"))
        self.assertIn("Not quite.", output)

    def test_a_challenge_writes_your_file_and_runs_it_when_you_save(self):
        _, step = solution_of("dictionaries", "your-turn-restock")
        inputs = ["", ":h", self.save("your-turn-restock", step.solution or ""), ""]
        output, tutor = self.drive(inputs, at=("dictionaries", "your-turn-restock"))
        self.assertIn("Your file: solutions/05-dictionaries/restock.py", output)
        self.assertIn("✗ Not yet: after restock, stock['apples'] is 3", output)  # Enter ran the starter
        self.assertIn("Hint. stock['apples'] -= 1 changes a value in place", output)
        self.assertIn("ran restock.py at", output)
        self.assertIn("✓ Solved!", output)
        self.assertIn("── Loop over the keys", output)  # Enter, once solved, moves on
        self.assertTrue(tutor.progress.is_solved("dictionaries", "your-turn-restock"))
        self.assertTrue(self.solution_file("restock").read_text().startswith("# Restock\n# Python refresher, Dictionaries"))

    def test_an_error_in_your_file_shows_its_traceback(self):
        broken = "def restock(stock):\n    stock['bananas'] -= 1\n"
        output, tutor = self.drive([self.save("your-turn-restock", broken)], at=("dictionaries", "your-turn-restock"))
        self.assertIn("KeyError: 'bananas'", output)
        self.assertIn("stock['bananas'] -= 1", output)  # the line from your file
        self.assertIn("✗ Not yet: your code raised KeyError", output)
        self.assertNotIn("tutor.py", output)
        self.assertFalse(tutor.progress.is_solved("dictionaries", "your-turn-restock"))

    def test_a_file_that_doesnt_compile_says_so(self):
        output, _ = self.drive([self.save("your-turn-restock", "def restock(stock):\n    stock[\n")], at=("dictionaries", "your-turn-restock"))
        self.assertIn("SyntaxError", output)
        self.assertIn("✗ Your file raised an error, so the checks didn't run.", output)

    def test_your_functions_are_yours_to_call_once_your_file_runs(self):
        _, step = solution_of("dictionaries", "your-turn-two-sum")
        inputs = [self.save("your-turn-two-sum", step.solution or ""), "two_sum([3, 3], 6)"]
        output, _ = self.drive(inputs, at=("dictionaries", "your-turn-two-sum"))
        self.assertIn("✓ Solved!", output)
        self.assertIn("[0, 1]", output)

    def test_a_file_that_already_passes_is_recognized(self):
        _, step = solution_of("dictionaries", "your-turn-count-letters")
        self.solution_file("count-letters").parent.mkdir(parents=True)
        self.save("your-turn-count-letters", step.solution or "")()
        output, tutor = self.drive([], at=("dictionaries", "your-turn-count-letters"))
        self.assertIn("✓ Your file already passes. Enter moves on.", output)
        self.assertTrue(tutor.progress.is_solved("dictionaries", "your-turn-count-letters"))

    def test_n_skips_a_challenge(self):
        output, tutor = self.drive([":n"], at=("dictionaries", "your-turn-restock"))
        self.assertIn("── Loop over the keys", output)
        self.assertFalse(tutor.progress.is_solved("dictionaries", "your-turn-restock"))

    def test_the_solution_command(self):
        output, _ = self.drive([":s"], at=("dictionaries", "your-turn-count-letters"))
        self.assertIn("One solution:", output)
        self.assertIn("counts[ch] = counts.get(ch, 0) + 1", output)
        self.assertIn("Put it in your file and save to run it.", output)

    def test_finishing_a_section_opens_the_next(self):
        output, tutor = self.drive([""], at=("dictionaries", "recap"))
        self.assertIn("✓ Dictionaries done · 0 of 3 challenges solved", output)
        self.assertIn("6  Sets", output)
        self.assertTrue(tutor.progress.is_done("dictionaries"))

    def test_the_menu_jumps_to_a_section_by_name(self):
        output, tutor = self.drive([":m", "tup", ":q"], at=("dictionaries", "recap"))
        self.assertIn("▸  5  Dictionaries", output)
        self.assertEqual(tutor.section().id, "tuples")

    def test_first_run_asks_where_to_start(self):
        output, tutor = self.drive(["5", "", ":q"])
        self.assertIn("Pick a section to start with.", output)
        self.assertEqual(tutor.section().id, "dictionaries")

    def test_unknown_commands_and_exit(self):
        output, _ = self.drive([":x", "exit()"], at=("dictionaries", "recap"))
        self.assertIn("There's no :x command", output)
        self.assertIn("Saved.", output)

    def test_a_missing_package_blocks_only_its_section(self):
        blocked = parse_lesson(
            Path("98-blocked.md"),
            "---\nrequires: no_such_package_here\n---\n\n# Blocked\n\n## Step\n\nText.\n",
        )
        output, _ = self.drive([":m", "2", ""], sections=[COURSE[0], blocked])
        self.assertIn("This section needs no_such_package_here, which isn't installed", output)
        self.assertIn("install no_such_package_here", output)
        self.assertIn("That's the end of the refresher.", output)

    def test_the_editor_command_opens_your_file_and_runs_it(self):
        editor = self.tmp / "fake-editor"
        editor.write_text(
            "#!/bin/sh\ncat >> \"$1\" <<'EOF'\n\n\n"
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, x in enumerate(nums):\n"
            "        if target - x in seen:\n"
            "            return [seen[target - x], i]\n"
            "        seen[x] = i\n"
            "EOF\n"
        )
        editor.chmod(editor.stat().st_mode | stat.S_IXUSR)
        with unittest.mock.patch.dict(os.environ, {"VISUAL": str(editor)}):
            output, _ = self.drive([":e"], at=("dictionaries", "your-turn-two-sum"))
        self.assertIn("ran two_sum.py at", output)
        self.assertIn("✓ Solved!", output)


class ProgressTests(InTempDir):
    def test_a_damaged_file_starts_fresh(self):
        path = self.tmp / "progress.json"
        path.write_text("{not json")
        self.assertIsNone(Progress(path).position)

    def test_survives_a_restart(self):
        path = self.tmp / "progress.json"
        progress = Progress(path)
        progress.move_to("sets", 2)
        progress.mark_solved("sets", "your-turn-contains-duplicate")
        progress.mark_done("lists")
        again = Progress(path)
        self.assertEqual(again.position, ("sets", 2))
        self.assertTrue(again.is_solved("sets", "your-turn-contains-duplicate"))
        self.assertTrue(again.is_done("lists"))


if __name__ == "__main__":
    unittest.main()
