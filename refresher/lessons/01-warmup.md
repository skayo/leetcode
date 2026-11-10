---
part: Python
---

# Warm-up

## How this works

Each step shows a short example as if someone typed it into the Python REPL, with the real output under each line.
Then the `>>>` prompt is yours.
Use the example's variables, change them, or try something else.

Press **Enter** on an empty line to go to the next step.
Type `:?` at any time to see every command, like `:b` to go back and `:m` for the menu.

```python
greeting = 'hello'
greeting.upper()
len(greeting)
```

## A first example

Here's quicksort in Python.
Functions and list comprehensions get their own steps later, so don't worry about every piece yet.

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
quicksort([3, 6, 8, 10, 1, 2, 1])
```

Try `quicksort` on a list of your own, or on a string like `'refresher'`.

## Which Python is this?

`sys.version` tells you which Python is running.
The refresher needs Python 3.10 or newer.
Python 2 reached its end of life in 2020, so any advice written for Python 2 is out of date.

```python
import sys
sys.version
sys.version_info >= (3, 10)
```

From a shell, `python3 --version` prints the version too.
