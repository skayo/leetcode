---
part: NumPy
requires: numpy
---

# Array math

```python setup
import numpy as np
```

## Data types

Every array has one data type, its `dtype`.
NumPy picks one from your data, or you can choose it.

```python
np.array([1, 2]).dtype
np.array([1.0, 2.0]).dtype
np.array([1, 2], dtype=np.float64)
```

## Element by element

Arithmetic operators work element by element.
Each one also has a function form, like `np.add(x, y)` for `x + y`.

```python
x = np.array([[1, 2], [3, 4]], dtype=np.float64)
y = np.array([[5, 6], [7, 8]], dtype=np.float64)
x + y
x - y
x * y
x / y
np.sqrt(x)
```

## Matrix products

`*` multiplies element by element.
For a matrix product, use `@`, or the older `np.dot`.

```python
x = np.array([[1, 2], [3, 4]])
y = np.array([[5, 6], [7, 8]])
v = np.array([9, 10])
w = np.array([11, 12])
v @ w
x @ v
x @ y
np.dot(x, y)
```

`v @ w` is the dot product of two vectors, so it's a single number.

## Sums along an axis

`sum` adds up every element, or adds along one axis.
`axis=0` adds down the columns, and `axis=1` adds across the rows.

```python predict
x = np.array([[1, 2], [3, 4]])
x.sum()
x.sum(axis=0)
x.sum(axis=1)
```

`mean`, `max`, and `min` take an `axis` the same way.

## Transposing

`.T` swaps rows and columns.

```python
x = np.array([[1, 2], [3, 4]])
x.T
v = np.array([[1, 2, 3]])
v.T
np.array([1, 2, 3]).T
```

A 1-D array has one dimension, so `.T` leaves it as it is.

## Your turn: row averages

Write `row_averages(scores)`.
Each row of `scores` holds one student's scores, and it returns each student's average.

```python listing
row_averages(np.array([[90, 80], [70, 100], [60, 60]]))   # array([85., 85., 60.])
```

```starter
def row_averages(scores):
    ...
```

```check
got = row_averages(np.array([[90, 80], [70, 100], [60, 60]]))
assert np.shape(got) == (3,), f"the result has shape {np.shape(got)}, and it should have one value per row, shape (3,)"
assert np.allclose(got, [85, 85, 60]), f"the result is {got}, and it should be [85. 85. 60.]"
got = row_averages(np.array([[1, 2, 3, 4]]))
assert np.allclose(got, [2.5]), f"row_averages of [[1, 2, 3, 4]] is {got}, and it should be [2.5]"
```

```hint
`mean` takes an `axis` like `sum` does.
Which axis runs across a row?
```

```solution
def row_averages(scores):
    return scores.mean(axis=1)
```
