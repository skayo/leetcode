---
part: Python
---

# Tuples

## Making a tuple

A tuple is an ordered sequence that can't change after you make it.
Use one for a fixed group of values, like a point or a pair.

```python
t = (5, 6)
type(t)
t[0]
len(t)
```

## Unpacking

Assigning a tuple to several names unpacks it, one value per name.
Unpacking also swaps two variables without a temporary one.

```python predict
point = (3, 4)
x, y = point
x
a, b = 1, 2
a, b = b, a
a, b
```

`for k, v in d.items()` unpacks too, since each item is a `(key, value)` tuple.

## Tuples as keys

A tuple can't change, so it can be a dictionary key or a set member.

```python
d = {(x, x + 1): x for x in range(10)}
d[(5, 6)]
d[(1, 2)]
visited = {(0, 0), (0, 1)}
(0, 1) in visited
```

Grid problems often store coordinates this way.

## Tuples can't change

Assigning to an item of a tuple raises a `TypeError`.
A list can change, so a list can't be a dictionary key.

```python error
t = (5, 6)
t[0] = 1
{[1, 2]: 'pair'}
```

## Your turn: count points

Write `count_points(points)`.
It takes a list of `(x, y)` tuples and returns a dictionary that maps each point to the number of times it appears.

```python listing
count_points([(0, 0), (1, 2), (0, 0)])   # {(0, 0): 2, (1, 2): 1}
```

```starter
def count_points(points):
    ...
```

```check
for points, want in [([(0, 0), (1, 2), (0, 0), (3, 1), (1, 2), (0, 0)], {(0, 0): 3, (1, 2): 2, (3, 1): 1}), ([], {})]:
    got = count_points(points)
    assert got == want, f"count_points({points!r}) returned {got!r}, and the answer is {want!r}"
```

```hint
It's the counting loop from the dictionaries section: `seen[p] = seen.get(p, 0) + 1`.
```

```solution
def count_points(points):
    seen = {}
    for p in points:
        seen[p] = seen.get(p, 0) + 1
    return seen
```
