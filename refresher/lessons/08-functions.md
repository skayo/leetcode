---
part: Python
---

# Functions

## Defining a function

`def` defines a function, and `return` sends a value back to the caller.

```python
def sign(x):
    if x > 0:
        return 'positive'
    elif x < 0:
        return 'negative'
    else:
        return 'zero'
for x in [-1, 0, 1]:
    print(sign(x))
```

At the prompt, press Enter on an empty line to finish a block like a `def` or a `for`.

## Default and keyword arguments

A parameter with a default value is optional.
Callers can pass an argument by name, as in `loud=True`.

```python
def hello(name, loud=False):
    if loud:
        print(f'HELLO, {name.upper()}!')
    else:
        print(f'Hello, {name}!')
hello('Bob')
hello('Fred', loud=True)
```

## Returning several values

Return a tuple, and unpack it where you call the function.

```python
def min_max(nums):
    return min(nums), max(nums)
lo, hi = min_max([3, 1, 4, 1, 5])
lo
hi
```

## Passing functions around

A function is a value, so you can pass it to another function.
`sorted` takes a `key` function and sorts by what it returns.
`lambda` writes a one-expression function inline.

```python
words = ['banana', 'kiwi', 'apple']
sorted(words)
sorted(words, key=len)
sorted(words, key=lambda w: w[-1])
```

The last call sorts the words by their final letter.

## Your turn: FizzBuzz

Write `fizzbuzz(n)`.
It returns `'FizzBuzz'` when `n` is divisible by 15, `'Fizz'` when it's divisible by 3, and `'Buzz'` when it's divisible by 5.
Otherwise it returns `n` as a string.

```python listing
fizzbuzz(9)    # 'Fizz'
fizzbuzz(30)   # 'FizzBuzz'
fizzbuzz(22)   # '22'
```

```starter
def fizzbuzz(n):
    ...
```

```check
for n, want in [(1, '1'), (3, 'Fizz'), (5, 'Buzz'), (9, 'Fizz'), (10, 'Buzz'), (15, 'FizzBuzz'), (22, '22'), (30, 'FizzBuzz')]:
    got = fizzbuzz(n)
    assert got == want, f"fizzbuzz({n}) returned {got!r}, and the answer is {want!r}"
```

```hint
Check 15 first.
If you check 3 first, 15 returns `'Fizz'` and never reaches the 15 case.
```

```hint
`n % 3 == 0` is true when `n` is divisible by 3, and `str(n)` turns a number into a string.
```

```solution
def fizzbuzz(n):
    if n % 15 == 0:
        return 'FizzBuzz'
    if n % 3 == 0:
        return 'Fizz'
    if n % 5 == 0:
        return 'Buzz'
    return str(n)
```

## Your turn: ranking

Write `ranking(scores)`.
It takes a dictionary that maps names to scores, and returns the names from the highest score to the lowest.

```python listing
ranking({'ann': 31, 'bob': 27, 'cy': 35})   # ['cy', 'ann', 'bob']
```

```starter
def ranking(scores):
    ...
```

```check
for scores, want in [({'ann': 31, 'bob': 27, 'cy': 35}, ['cy', 'ann', 'bob']), ({'solo': 1}, ['solo']), ({}, [])]:
    got = ranking(scores)
    assert got == want, f"ranking({scores!r}) returned {got!r}, and the answer is {want!r}"
```

```hint
`sorted(scores)` sorts the keys.
Pass `key=scores.get` to sort them by score, and `reverse=True` to put the highest first.
```

```solution
def ranking(scores):
    return sorted(scores, key=scores.get, reverse=True)
```

## Recap

```python listing
def f(a, b=2):                # b is optional
    return a + b, a * b       # several values come back as a tuple
total, product = f(3)         # unpack them
f(3, b=10)                    # a keyword argument
sorted(xs, key=len)           # pass a function
sorted(xs, key=lambda x: -x)  # or write one inline
```
