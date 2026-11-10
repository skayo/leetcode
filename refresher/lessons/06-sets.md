---
part: Python
---

# Sets

## Membership

A set is an unordered collection with no duplicates.
Checking whether an item is `in` a set takes constant time on average, however big the set is.

```python
animals = {'cat', 'dog'}
'cat' in animals
'fish' in animals
```

## Add and remove

Adding an item that's already in the set changes nothing.

```python
animals = {'cat', 'dog'}
animals.add('fish')
len(animals)
animals.add('cat')
len(animals)
animals.remove('cat')
animals
```

`set([1, 2, 2, 3])` drops the duplicates from a list.
`{}` makes an empty dictionary, so write an empty set as `set()`.

## No fixed order

You can loop over a set like a list, but the order isn't fixed.
For strings, the order can change each time Python starts.

```python
animals = {'cat', 'dog', 'fish'}
for i, animal in enumerate(animals):
    print(f'#{i + 1}: {animal}')
```

## Set comprehensions

A set comprehension uses braces, like a dictionary comprehension without the colon.

```python
from math import sqrt
{int(sqrt(x)) for x in range(30)}
```

## Set operations

`|` is union, `&` is intersection, and `-` is difference.

```python predict
a = {1, 2, 3}
b = {2, 3, 4}
a | b
a & b
a - b
```

`a - b` keeps the items of `a` that aren't in `b`.

## Your turn: contains duplicate

Write `has_duplicates(nums)`.
It returns `True` when some number appears more than once in `nums`, and `False` otherwise.
Use a set.
This is LeetCode problem 217.

```python listing
has_duplicates([4, 1, 7, 1, 9])   # True, since 1 appears twice
has_duplicates([1, 2, 3])         # False
```

```starter
def has_duplicates(nums):
    ...
```

```check
assert has_duplicates([4, 1, 7, 1, 9]), "has_duplicates([4, 1, 7, 1, 9]) should be True, since 1 appears twice"
assert not has_duplicates([1, 2, 3]), "has_duplicates([1, 2, 3]) should be False"
assert not has_duplicates([]), "has_duplicates([]) should be False"
```

```hint
A set keeps one copy of each number, so compare `len(set(nums))` with `len(nums)`.
```

```solution
def has_duplicates(nums):
    return len(set(nums)) < len(nums)
```

## Recap

```python listing
s = {1, 2}             # make a set; set() makes an empty one
s.add(3)               # add
s.remove(1)            # remove; KeyError if it's missing
2 in s                 # membership in constant time
set(xs)                # drop duplicates
a | b, a & b, a - b    # union, intersection, difference
```
