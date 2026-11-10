---
part: NumPy
requires: numpy
---

# Saving and loading arrays

```python setup
import numpy as np
```

## Loading a CSV

`np.loadtxt` reads a text file of numbers into an array.
This example writes a small CSV file first, so there's something to read.

```python
with open('data.csv', 'w') as f:
    print('4,8,15', file=f)
    print('16,23,42', file=f)
data = np.loadtxt('data.csv', delimiter=',')
data
```

`print(..., file=f)` writes a line to the file instead of the screen.

## NumPy's own format

`np.save` writes an array to a binary `.npy` file, and `np.load` reads it back with the same values, shape, and dtype.

```python
saved = np.array([1, 2, 3])
np.save('data.npy', saved)
np.load('data.npy')
```

## Several arrays in one file

`np.savez` stores several named arrays in one `.npz` file.

```python
np.savez('arrays.npz', first=np.arange(3), second=np.eye(2))
loaded = np.load('arrays.npz')
loaded['first']
loaded['second']
```
