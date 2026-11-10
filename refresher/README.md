# Python refresher

An interactive Python, NumPy, and Matplotlib tutorial for the terminal.
Each step shows a short example as a REPL session with its real output, then hands you a live Python prompt with the example's variables loaded.
Steps marked ★ are challenges, which you solve in your editor.

The lessons are adapted from Herman Kamper's Python and NumPy practical for Stellenbosch University, which is based on Justin Johnson's tutorial for Stanford's CS231n.

## Run it

From the repository root:

```sh
python3 refresher
```

It opens where you left off.
To jump to a section, name it or give its number, as in `python3 refresher sets` or `python3 refresher 6`.
Type `:?` inside the tutor to list its commands.

It needs Python 3.10 or newer.
On Python 3.13 and newer, the prompt uses the line editor from Python's own REPL, which highlights code, indents blocks, and edits several lines at once.

## Challenges

When you reach a challenge, the tutor writes a file for it under `solutions/`, such as `solutions/05-dictionaries/two_sum.py`.
The file holds the problem as comments, starter code to fill in, and the checks.
Open it in your editor in another pane, and each time you save it, the tutor runs it and its checks and shows the result.
Once it passes, the functions you wrote can be called at the tutor's prompt.

Each solution file also runs on its own, so `python3 solutions/05-dictionaries/two_sum.py` runs its checks without the tutor.
The tutor never overwrites a solution file once it exists.

## Files it writes

Your solutions go in `solutions/`, which git tracks like the rest of the repository.
Code from the prompt runs in `sandbox/`, so files that lessons create go there, along with any scratch file you open with `:e` on a step that isn't a challenge.
`.progress.json` holds your place and the challenges you've solved, and deleting it starts you over.
Git ignores `sandbox/` and `.progress.json`.

## Lessons and tests

Each section is a Markdown file in `lessons/`, and sections run in file name order.
The lesson format is described at the top of `course.py`.

To run the tests from the repository root:

```sh
python3 -m unittest refresher.test_refresher
```

The tests run every lesson example, check that each challenge's starter fails and its solution passes, run every solution file on its own, and drive the tutor with scripted input.
