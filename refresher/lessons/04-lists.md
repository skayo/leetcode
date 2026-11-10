---
part: Python
---

# Lists

## Making a list

A list is Python's resizable array.
Indexes start at 0, and negative indexes count back from the end.

```python
xs = [3, 1, 2]
xs[0]
xs[2]
xs[-1]
len(xs)
```

## Changing a list

A list can hold values of different types.
`append` adds an item to the end, and `pop` removes the last item and returns it.

```python
xs = [3, 1, 2]
xs[2] = 'foo'
xs
xs.append('bar')
xs
last = xs.pop()
last
xs
```

## Slicing

`nums[start:stop]` makes a new list from index `start` up to, but not including, `stop`.
Leave out `start` to begin at the front, or `stop` to go to the end.

```python
nums = list(range(5))
nums
nums[2:4]
nums[2:]
nums[:2]
nums[:]
nums[:-1]
nums[2:4] = [8, 9]
nums
```

`range(5)` produces the numbers 0 to 4 one at a time, and `list()` collects them into a list.
Assigning to a slice replaces that part of the list.

## Slices with a step

A third number in a slice is the step.
A negative step walks backwards.

```python predict
nums = [0, 1, 2, 3, 4, 5]
nums[::2]
nums[1::2]
nums[::-1]
```

Strings slice the same way, so `'hello'[::-1]` reverses a string.

## Looping

`for` gives you each item in turn.
When you also need the index, use `enumerate`.

```python
animals = ['cat', 'dog', 'monkey']
for animal in animals:
    print(animal)
for i, animal in enumerate(animals):
    print(f'#{i + 1}: {animal}')
```

`enumerate(animals, start=1)` counts from 1 instead of 0.

## List comprehensions

A list comprehension builds a new list from another one in a single expression.
These two do the same thing:

```python
nums = [0, 1, 2, 3, 4]
squares = []
for x in nums:
    squares.append(x ** 2)
squares
[x ** 2 for x in nums]
```

Add an `if` at the end to keep only some items:

```python
[x ** 2 for x in nums if x % 2 == 0]
```

## Your turn: long words

Write `long_words(words)`, which returns the words that have more than 3 letters, in their original order.
Use a list comprehension.

```python listing
long_words(['the', 'quick', 'brown', 'fox'])   # ['quick', 'brown']
```

```starter
def long_words(words):
    ...
```

```check
for words, want in [(['the', 'quick', 'brown', 'fox', 'jumps'], ['quick', 'brown', 'jumps']), (['a', 'abcd'], ['abcd']), ([], [])]:
    got = long_words(words)
    assert got == want, f"long_words({words!r}) returned {got!r}, and the answer is {want!r}"
```

```hint
Follow the shape `[x for x in nums if ...]`, with `len(w) > 3` as the condition.
```

```solution
def long_words(words):
    return [w for w in words if len(w) > 3]
```

## Your turn: middle

Write `middle(nums)`, which returns every item except the first and the last, using one slice.
It shouldn't change the list it's given.

```python listing
middle([10, 20, 30, 40, 50])   # [20, 30, 40]
middle([1, 2])                 # []
```

```starter
def middle(nums):
    ...
```

```check
nums = [10, 20, 30, 40, 50]
got = middle(nums)
assert got == [20, 30, 40], f"middle([10, 20, 30, 40, 50]) returned {got!r}, and the answer is [20, 30, 40]"
assert nums == [10, 20, 30, 40, 50], f"middle changed the list it was given to {nums!r}, and a slice makes a copy, so it doesn't need to"
got = middle([1, 2])
assert got == [], f"middle([1, 2]) returned {got!r}, and the answer is []"
```

```hint
A negative stop counts from the end, so a stop of `-1` means "up to, but not including, the last item".
```

```solution
def middle(nums):
    return nums[1:-1]
```

## Recap

```python listing
xs = [3, 1, 2]
xs[0], xs[-1]                 # first and last items
xs.append(4)                  # add to the end
xs.pop()                      # remove from the end
xs[1:3], xs[::-1]             # a slice, and a reversed copy
for i, x in enumerate(xs):    # index and item together
    ...
[x * 2 for x in xs if x > 1]  # a list comprehension
```
