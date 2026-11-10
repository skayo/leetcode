---
part: NumPy
requires: numpy
---

# NumPy arrays

```python setup
import numpy as np
```

## Your first array

NumPy is the core library for numerical computing in Python.
Its array is a grid of values that all have the same type.
An array's `shape` is a tuple with its size along each dimension.

```python
a = np.array([1, 2, 3])
type(a)
a.shape
print(a[0], a[1], a[2])
a[0] = 5
a
```

The REPL shows one number from an array as `np.int64(5)`, and `print` shows it as `5`.

## Two dimensions

Nested lists make an array with more dimensions.
Index it with one number per dimension, separated by commas.

```python
b = np.array([[1, 2, 3], [4, 5, 6]])
b
b.shape
print(b[0, 0], b[0, 1], b[1, 0])
```

## Ready-made arrays

NumPy has functions that build common arrays.

```python
np.zeros((2, 2))
np.ones((1, 2))
np.full((2, 2), 7)
np.eye(2)
np.arange(0, 10, 2)
np.random.random((2, 2))
```

`np.arange` works like `range` and returns an array.
`np.random.random` gives different numbers each time you run it.

## Your turn: grid

Write `grid(rows, cols)`.
It returns an array of zeros with that many rows and columns, except for its bottom right element, which is 1.

```python listing
grid(2, 3)   # array([[0., 0., 0.],
             #        [0., 0., 1.]])
```

```starter
def grid(rows, cols):
    ...
```

```check
got = grid(3, 4)
assert isinstance(got, np.ndarray), f"grid(3, 4) returned a {type(got).__name__}, not a NumPy array"
assert got.shape == (3, 4), f"grid(3, 4) has shape {got.shape}, not (3, 4)"
assert got[2, 3] == 1, "the bottom right element of grid(3, 4) should be 1"
assert got.sum() == 1, "every other element of grid(3, 4) should be 0"
got = grid(1, 1)
assert got.tolist() == [[1]], f"grid(1, 1) returned {got.tolist()}, and it should be [[1.0]]"
```

```hint
`np.zeros((rows, cols))` makes the array.
Negative indexes work here too, so `g[-1, -1]` is the bottom right corner.
```

```solution
def grid(rows, cols):
    g = np.zeros((rows, cols))
    g[-1, -1] = 1
    return g
```
