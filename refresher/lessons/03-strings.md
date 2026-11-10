---
part: Python
---

# Strings

## Making strings

Single and double quotes make the same kind of string.
`+` joins strings, and `len` counts characters.

```python
hello = 'hello'
world = "world"
len(hello)
hello + ' ' + world
print(hello, world)
```

The REPL shows a string's value with quotes around it.
`print` shows the text alone.

## f-strings

Put an `f` before the opening quote, and Python fills in the value of anything inside `{}`.
A format spec after a colon controls how a value looks.

```python
name = 'Ada'
year = 1815
f'{name} was born in {year}'
f'{name} would be {2026 - year}'
pi = 3.14159
f'{pi:.2f}'
```

Older code uses `'{} was born in {}'.format(name, year)`, which gives the same result.

## String methods

Each string method returns a new string.
Strings can't be changed in place, so the original stays the same.

```python
s = 'hello'
s.capitalize()
s.upper()
s.rjust(7)
s.center(7)
s.replace('l', '(ell)')
'  world '.strip()
s
```

Run `help(str)` to see every method, and press `q` to leave the help page.

## Split and join

`split` breaks a string into a list.
`join` puts a list of strings back together, with the string you call it on as the separator.

```python predict
'a,b,c'.split(',')
'the quick brown fox'.split()
'-'.join(['a', 'b', 'c'])
'-'.join('xyz')
```

`join` takes any sequence of strings, and a string is a sequence of one-character strings.

## Your turn: price line

Write `price_line(item, price)`, which returns a line like `'coffee costs $3.50'`.
Use an f-string, and always show the price with two decimals.

```python listing
price_line('coffee', 3.5)   # 'coffee costs $3.50'
price_line('tea', 2)        # 'tea costs $2.00'
```

```starter
def price_line(item, price):
    ...
```

```check
for item, price, want in [('coffee', 3.5, 'coffee costs $3.50'), ('tea', 2, 'tea costs $2.00'), ('cake', 4.256, 'cake costs $4.26')]:
    got = price_line(item, price)
    assert got == want, f"price_line({item!r}, {price!r}) returned {got!r}, and the answer is {want!r}"
```

```hint
`f'{price:.2f}'` formats a number with exactly two decimals.
```

```solution
def price_line(item, price):
    return f'{item} costs ${price:.2f}'
```

## Recap

```python listing
s = 'hello'
len(s)                     # 5
f'{s} has {len(s)} chars'  # an f-string
f'{3.14159:.2f}'           # '3.14'
s.upper(), s.strip()       # methods return new strings
'a,b'.split(',')           # ['a', 'b']
', '.join(['a', 'b'])      # 'a, b'
```
