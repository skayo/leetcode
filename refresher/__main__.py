"""Start the refresher: `python3 refresher` from the folder above this one.

Name a section to jump straight to it, by number or by name: `python3 refresher 6`
or `python3 refresher sets`.
"""

import sys

if sys.version_info < (3, 10):
    sys.exit("The refresher needs Python 3.10 or newer.")

import argparse
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
if __package__ in (None, ""):  # run as `python3 refresher` rather than `python3 -m refresher`
    sys.path.insert(0, str(HERE.parent))

from refresher.course import LessonError, load_course  # noqa: E402
from refresher.tutor import Progress, Tutor  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 refresher",
        description="An interactive Python and NumPy refresher for the terminal.",
    )
    parser.add_argument("section", nargs="?", help="a section number or name to jump to, like 5 or dict")
    args = parser.parse_args(argv)

    try:
        sections = load_course(HERE / "lessons")
    except LessonError as error:
        print(f"A lesson file has a problem: {error}", file=sys.stderr)
        return 1

    sandbox = HERE / "sandbox"
    sandbox.mkdir(exist_ok=True)
    tutor = Tutor(
        sections,
        Progress(HERE / ".progress.json"),
        sandbox=sandbox,
        solutions=HERE / "solutions",
        launch_dir=Path.cwd(),
    )

    start = None
    if args.section is not None:
        start = tutor.find_section(args.section)
        if start is None:
            names = ", ".join(f"{number} {section.id}" for number, section in enumerate(sections, 1))
            print(f"No section matches {args.section!r}. The sections are: {names}.", file=sys.stderr)
            return 2

    # Your code runs in the sandbox, so files it writes stay out of the rest of the repo.
    os.chdir(sandbox)
    return tutor.run(start)


if __name__ == "__main__":
    sys.exit(main())
