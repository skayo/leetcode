---
part: Python
---

# Files

## Writing a file

`open(path, 'w')` opens a file for writing, and the file closes when the `with` block ends.
The refresher runs your code in its `sandbox` folder, so files you write go there.

```python
with open('example.txt', 'w') as f:
    f.write('This is the first line.\n')
    f.write('And here is another one.\n')
```

`write` returns the number of characters it wrote, and the REPL prints each return value.

## Reading it back

Looping over a file gives you one line at a time, with its newline still on the end.
`end=''` stops `print` from adding a second newline.

```python
with open('example.txt') as f:
    for line in f:
        print(line, end='')
```

## Reading it all at once

`Path.read_text` from `pathlib` reads a whole file in one call.

```python
from pathlib import Path
text = Path('example.txt').read_text()
text
text.splitlines()
```

## Your turn: lines

Write two functions.
`write_lines(path, lines)` writes each string in `lines` to the file at `path`, one per line.
`count_lines(path)` returns the number of lines in the file at `path`.

```python listing
write_lines('notes.txt', ['one', 'two', 'three'])
count_lines('notes.txt')   # 3
```

```starter
def write_lines(path, lines):
    ...


def count_lines(path):
    ...
```

```check
import os
import tempfile
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, 'notes.txt')
    write_lines(path, ['one', 'two', 'three'])
    assert os.path.exists(path), "write_lines didn't create the file"
    with open(path) as f:
        text = f.read()
    assert text.splitlines() == ['one', 'two', 'three'], f"after write_lines, the file holds {text!r}"
    got = count_lines(path)
    assert got == 3, f"count_lines returned {got!r} for a file with 3 lines"
    write_lines(path, [])
    got = count_lines(path)
    assert got == 0, f"count_lines returned {got!r} for an empty file"
```

```hint
Open the file with `with open(path, 'w') as f:`, and call `f.write(line + '\n')` once per line.
```

```hint
`len(f.readlines())` counts the lines of a file you opened for reading.
```

```solution
def write_lines(path, lines):
    with open(path, 'w') as f:
        for line in lines:
            f.write(line + '\n')


def count_lines(path):
    with open(path) as f:
        return len(f.readlines())
```
