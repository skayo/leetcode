---
part: Python
---

# Dictionaries

## Look things up

A dictionary maps keys to values, like a `Map` in Java or an object in JavaScript.
Put a key in square brackets to get its value, and use `in` to ask whether a key is there.

```python predict
d = {'cat': 'cute', 'dog': 'furry'}
d['cat']
'cat' in d
'cute' in d
```

`in` checks the keys, never the values.

## Add, change, and remove

Assigning to a key adds it, or replaces its value if the key is already there.
`del` removes a key.

```python
d = {'cat': 'cute', 'dog': 'furry'}
d['fish'] = 'wet'
d['cat'] = 'fluffy'
del d['dog']
d
len(d)
```

## Missing keys

Looking up a key that isn't in the dictionary raises a `KeyError`:

```python error
d = {'cat': 'cute', 'dog': 'furry'}
d['monkey']
```

Check with `in` first, or use `get`, which comes next.

## Reading with a default

`get` returns a default value instead of raising.
Without a default it returns `None`, and the REPL prints nothing for `None`.

```python
d = {'cat': 'cute', 'dog': 'furry'}
d.get('monkey', 'N/A')
d.get('cat', 'N/A')
d.get('monkey')
print(d.get('monkey'))
```

## Your turn: restock

Write `restock(stock)`, which changes the dictionary it's given in place.
It sells one apple by taking 1 off `stock['apples']`, adds `'kiwis'` with a count of 5, and removes `'pears'`.
It doesn't need to return anything.

```python listing
stock = {'apples': 3, 'pears': 0, 'plums': 7}
restock(stock)
stock   # {'apples': 2, 'plums': 7, 'kiwis': 5}
```

```starter
def restock(stock):
    ...
```

```check
stock = {'apples': 3, 'pears': 0, 'plums': 7}
restock(stock)
assert stock.get('apples') == 2, f"after restock, stock['apples'] is {stock.get('apples')!r}, and it should be 2"
assert stock.get('kiwis') == 5, f"after restock, stock['kiwis'] is {stock.get('kiwis')!r}, and it should be 5"
assert 'pears' not in stock, "after restock, 'pears' is still a key in stock"
assert stock == {'apples': 2, 'plums': 7, 'kiwis': 5}, f"after restock, stock is {stock!r}"
```

```hint
`stock['apples'] -= 1` changes a value in place, and `del stock['pears']` removes a key.
```

```solution
def restock(stock):
    stock['apples'] -= 1
    stock['kiwis'] = 5
    del stock['pears']
```

## Loop over the keys

Looping over a dictionary gives you its keys.
Since Python 3.7, a dictionary keeps its keys in the order you added them.

```python
legs = {'person': 2, 'cat': 4, 'spider': 8}
for animal in legs:
    print(f'A {animal} has {legs[animal]} legs')
```

## Keys and values together

`items()` gives you each key and its value as a pair, so you don't have to look each value up.
`keys()` and `values()` give you one side.

```python
legs = {'person': 2, 'cat': 4, 'spider': 8}
for animal, n in legs.items():
    print(f'A {animal} has {n} legs')
list(legs.keys())
list(legs.values())
sum(legs.values())
```

## Dictionary comprehensions

A dictionary comprehension works like a list comprehension, with `key: value` at the front.

```python
nums = [0, 1, 2, 3, 4]
{x: x ** 2 for x in nums if x % 2 == 0}
legs = {'person': 2, 'cat': 4, 'spider': 8}
{n: animal for animal, n in legs.items()}
```

The second comprehension swaps each key with its value.

## Your turn: count letters

Write `count_letters(word)`, which returns a dictionary that maps each letter in `word` to the number of times it appears.

```python listing
count_letters('mississippi')   # {'m': 1, 'i': 4, 's': 4, 'p': 2}
count_letters('')              # {}
```

```starter
def count_letters(word):
    ...
```

```check
for word, want in [('mississippi', {'m': 1, 'i': 4, 's': 4, 'p': 2}), ('aaa', {'a': 3}), ('', {})]:
    got = count_letters(word)
    assert got == want, f"count_letters({word!r}) returned {got!r}, and the answer is {want!r}"
```

```hint
Start with `counts = {}`, then loop over `word` one letter at a time.
```

```hint
`counts[ch] = counts.get(ch, 0) + 1` adds one to a letter's count, starting from 0 the first time the letter appears.
```

```solution
def count_letters(word):
    counts = {}
    for ch in word:
        counts[ch] = counts.get(ch, 0) + 1
    return counts
```

```solved
Counting things with a dictionary comes up in many LeetCode problems.
The standard library has a class for it: `from collections import Counter`, then `Counter(word)`.
```

## Your turn: two sum

Write `two_sum(nums, target)`.
It returns the indexes of the two numbers in `nums` that add up to `target`.
Use a dictionary to remember the index of each number you've seen, so you loop over `nums` only once.
This is LeetCode problem 1.

```python listing
two_sum([2, 7, 11, 15], 9)   # [0, 1], because 2 + 7 is 9
two_sum([3, 2, 4], 6)        # [1, 2]
```

```starter
def two_sum(nums, target):
    seen = {}  # maps each number to the index where you saw it
    for i, x in enumerate(nums):
        ...
```

```check
for nums, target, want in [([2, 7, 11, 15], 9, [0, 1]), ([3, 2, 4], 6, [1, 2]), ([3, 3], 6, [0, 1])]:
    got = two_sum(nums, target)
    assert got is not None, f"two_sum({nums}, {target}) returned None"
    assert sorted(got) == want, f"two_sum({nums}, {target}) returned {got!r}, and the answer is {want}"
```

```hint
For each number `x`, the partner you need is `target - x`.
Check whether you've already seen the partner.
```

```hint
If `target - x` is in `seen`, return `[seen[target - x], i]`.
If it isn't, store `seen[x] = i` and keep going.
```

```solution
def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
```

```solved
The loop runs once, and each dictionary lookup takes constant time, so this is O(n).
Checking every pair of numbers would be O(n²).
```

## Recap

```python listing
d = {'a': 1, 'b': 2}       # make a dictionary
d['a']                     # read a value; KeyError if the key is missing
d.get('z', 0)              # read with a default
d['c'] = 3                 # add or update
del d['a']                 # remove
'a' in d                   # is the key there?
for k, v in d.items():     # keys and values together
    ...
{k: v for k, v in pairs}   # a dictionary comprehension
```

Run `help(dict)` to see every method.
