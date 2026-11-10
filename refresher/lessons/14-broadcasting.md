---
part: NumPy
requires: numpy
---

# Broadcasting

```python setup
import numpy as np
```

## With a loop

Say you want to add the vector `v` to each row of the matrix `x`.
A loop works:

```python
x = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
v = np.array([1, 0, 1])
y = np.empty_like(x)
for i in range(4):
    y[i, :] = x[i, :] + v
y
```

When `x` is large, a Python loop like this one is slow.

## With stacked copies

Another way is to stack copies of `v` into a matrix the same shape as `x`, then add the two.

```python
x = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
v = np.array([1, 0, 1])
vv = np.tile(v, (4, 1))
vv
x + vv
```

## With broadcasting

NumPy can add `v` to each row without making any copies.
`x` has shape (4, 3) and `v` has shape (3,), and `x + v` works as if `v` were stacked four times.

```python
x = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
v = np.array([1, 0, 1])
x + v
```

## The rules

To broadcast two arrays, NumPy lines up their shapes from the right:

- A missing dimension counts as size 1.
- Two sizes fit when they're equal, or when one of them is 1.
- A dimension of size 1 stretches to match the other array.

```python predict
np.zeros((4, 3)).shape
(np.zeros((4, 3)) + np.zeros(3)).shape
(np.zeros((4, 1)) + np.zeros(3)).shape
```

When two sizes don't fit, NumPy raises an error:

```python error
np.zeros((4, 3)) + np.zeros(4)
```

## Putting it to work

These lines compute an outer product, add `v` to each row of `x`, add `w` to each column of `x`, and scale `x` by a number.

```python
v = np.array([1, 2, 3])
w = np.array([4, 5])
v.reshape(3, 1) * w
x = np.array([[1, 2, 3], [4, 5, 6]])
x + v
x + w.reshape(2, 1)
x * 2
```

A plain number broadcasts against an array of any shape.

## Your turn: center columns

Write `center_columns(data)`.
It returns `data` with each column's mean subtracted from that column, so each column of the result averages to 0.
Use broadcasting instead of a loop.

```python listing
center_columns(np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 9.0]]))
# array([[-2., -3.],
#        [ 0., -1.],
#        [ 2.,  4.]])
```

```starter
def center_columns(data):
    ...
```

```check
got = center_columns(np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 9.0]]))
assert np.shape(got) == (3, 2), f"the result has shape {np.shape(got)}, not (3, 2)"
assert np.allclose(got, [[-2, -3], [0, -1], [2, 4]]), f"the result is {np.asarray(got).tolist()}, and it should be [[-2, -3], [0, -1], [2, 4]]"
got = center_columns(np.array([[4.0], [6.0]]))
assert np.allclose(got, [[-1], [1]]), f"center_columns of [[4], [6]] is {np.asarray(got).tolist()}, and it should be [[-1], [1]]"
```

```hint
`data.mean(axis=0)` gives one mean per column, with shape (2,).
Shapes (3, 2) and (2,) broadcast together.
```

```solution
def center_columns(data):
    return data - data.mean(axis=0)
```
