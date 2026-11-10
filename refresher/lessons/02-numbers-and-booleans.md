---
part: Python
---

# Numbers and booleans

## Integers

`**` is exponentiation.
Python integers never overflow: they grow as large as the value needs.

```python
x = 3
type(x)
x + 1
x - 1
x * 2
x ** 2
2 ** 100
```

## Division

`/` always gives a float.
`//` is floor division, and `%` is the remainder.

```python predict
7 / 2
7 // 2
7 % 2
-7 // 2
```

`//` rounds down, so `-7 // 2` is `-4`.
C and Java round toward zero and give `-3`, so code ported from them can be off by one for negative numbers.

## Updating a variable

Python has no `x++` or `x--`.
Use augmented assignment instead.

```python
x = 3
x += 1
x
x *= 2
x
```

## Floats

Floats are 64-bit binary floating point numbers, so decimal fractions like 0.1 are stored approximately.

```python
y = 2.5
type(y)
y + 1, y * 2, y ** 2
0.1 + 0.2
round(0.1 + 0.2, 2)
```

## Booleans

Python spells the logic operators as words: `and`, `or`, and `not`.

```python
t, f = True, False
type(t)
t and f
t or f
not t
t != f
```

On two booleans, `!=` works as XOR.

## Your turn: split seconds

Write `split_seconds(total)`.
It takes a number of seconds and returns a tuple `(minutes, seconds)`, where `total == 60 * minutes + seconds`.
Compute both with `//` and `%`.

```python listing
split_seconds(754)   # (12, 34)
split_seconds(60)    # (1, 0)
```

```starter
def split_seconds(total):
    ...
```

```check
for total, want in [(754, (12, 34)), (60, (1, 0)), (59, (0, 59)), (0, (0, 0))]:
    got = split_seconds(total)
    assert got == want, f"split_seconds({total}) returned {got!r}, and the answer is {want}"
```

```hint
`total // 60` is the number of whole minutes, and `total % 60` is what's left over.
`return a, b` returns the tuple `(a, b)`.
```

```solution
def split_seconds(total):
    return total // 60, total % 60
```

```solved
`divmod(total, 60)` computes both at once and returns the same tuple.
```
