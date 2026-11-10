---
part: NumPy
requires: numpy
---

# Array indexing

```python setup
import numpy as np
```

## Slicing

NumPy arrays slice like lists, with one slice per dimension.

```python
a = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
a
a[:2, 1:3]
```

`a[:2, 1:3]` takes the first two rows, and columns 1 and 2 of those rows.

## Slices are views

A list slice is a copy, but an array slice is a view of the same data.
Changing the slice changes the original array.

```python predict
a = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
b = a[:2, 1:3]
print(a[0, 1])
b[0, 0] = 77
print(a[0, 1])
```

`b[0, 0]` and `a[0, 1]` are the same element in memory.
Call `.copy()` when you need an independent array.

## Integers drop a dimension

An integer index removes its dimension from the result.
A slice keeps the dimension, even when it covers a single row.

```python
a = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])
a[1, :].shape
a[1:2, :].shape
a[1, :]
a[1:2, :]
a[:, 1]
a[:, 1:2]
```

## Indexing with arrays of integers

Give a list of row indexes and a list of column indexes, and NumPy pairs them up to pick elements.

```python
a = np.array([[1, 2], [3, 4], [5, 6]])
a[[0, 1, 2], [0, 1, 0]]
np.array([a[0, 0], a[1, 1], a[2, 0]])
a[[0, 0], [1, 1]]
```

The first two lines pick the same three elements.
The last line shows that you can pick one element more than once.

## One element from each row

Pair `np.arange` with an array of column indexes to pick, or change, one element in each row.

```python
a = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
cols = np.array([0, 2, 0, 1])
a[np.arange(4), cols]
a[np.arange(4), cols] += 10
a
```

## Boolean indexing

Comparing an array gives an array of booleans with the same shape.
Indexing with that array keeps the elements where it's `True`.

```python
a = np.array([[1, 2], [3, 4], [5, 6]])
a > 2
a[a > 2]
```

## Your turn: clean up

Write two functions, each with boolean indexing.
`positives(x)` returns the positive numbers in `x`, and leaves `x` as it was.
`zero_negatives(x)` changes `x` in place, setting each negative number to 0.

```python listing
x = np.array([3, -1, 4, -1, 5, -9])
positives(x)        # array([3, 4, 5])
zero_negatives(x)
x                   # array([3, 0, 4, 0, 5, 0])
```

```starter
def positives(x):
    ...


def zero_negatives(x):
    ...
```

```check
x = np.array([3, -1, 4, -1, 5, -9])
got = positives(x)
assert got is not None and list(got) == [3, 4, 5], f"positives returned {got}, and it should be [3 4 5]"
assert list(x) == [3, -1, 4, -1, 5, -9], f"positives changed x to {x}, and it should leave x alone"
zero_negatives(x)
assert list(x) == [3, 0, 4, 0, 5, 0], f"after zero_negatives, x is {x}, and it should be [3 0 4 0 5 0]"
```

```hint
`x[x > 0]` keeps the positive numbers.
Assignment works with a boolean index too: `x[x < 0] = ...`.
```

```solution
def positives(x):
    return x[x > 0]


def zero_negatives(x):
    x[x < 0] = 0
```
