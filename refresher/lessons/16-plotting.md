---
part: Matplotlib
requires: numpy matplotlib
---

# Plotting

```python setup
import numpy as np
import matplotlib.pyplot as plt
```

## A sine curve

`plt.plot(x, y)` draws a line through the points, and `plt.show()` opens the plot in a window.
Close the window to get your prompt back.

```python script
x = np.arange(0, 3 * np.pi, 0.1)
y = np.sin(x)
plt.plot(x, y)
plt.show()
```

## Labels and a legend

Call `plot` once per line, and add the labels before you call `show`.

```python script
x = np.arange(0, 3 * np.pi, 0.1)
plt.plot(x, np.sin(x))
plt.plot(x, np.cos(x))
plt.xlabel('x axis label')
plt.ylabel('y axis label')
plt.title('Sine and Cosine')
plt.legend(['Sine', 'Cosine'])
plt.show()
```

At the prompt, each of these calls prints what it returns, like `Text(0.5, 1.0, 'Sine and Cosine')`.
You can ignore those lines.

## Subplots

`plt.subplot(rows, columns, n)` splits the figure into a grid and makes plot number `n` the active one.

```python script
x = np.arange(0, 3 * np.pi, 0.1)
plt.subplot(2, 1, 1)
plt.plot(x, np.sin(x))
plt.title('Sine')
plt.subplot(2, 1, 2)
plt.plot(x, np.cos(x))
plt.title('Cosine')
plt.show()
```

To save a figure as an image instead, call `plt.savefig('plot.png')` before `plt.show()`.
The file goes in the sandbox folder.

## Where to go next

SciPy builds on NumPy with functions for science and engineering.
scikit-learn adds machine learning on top of NumPy, SciPy, and Matplotlib.

That's the end of the refresher.
It's adapted from Herman Kamper's Python and NumPy practical for Stellenbosch University, which built on earlier versions by the Deep Learning Indaba, by Volodymyr Kuleshov and Isaac Caswell, and by Justin Johnson for Stanford's CS231n course.
