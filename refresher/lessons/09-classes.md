---
part: Python
---

# Classes

## Defining a class

Methods are functions defined inside the class.
`__init__` runs when you make an instance, and `self` is that instance.

```python
class Greeter:
    def __init__(self, name):
        self.name = name
    def greet(self, loud=False):
        if loud:
            print(f'HELLO, {self.name.upper()}!')
        else:
            print(f'Hello, {self.name}')
g = Greeter('Fred')
g.greet()
g.greet(loud=True)
g.name
```

## A readable repr

By default, the REPL shows an object as something like `<__main__.Point object at 0x104f3a0d0>`.
Define `__repr__` to choose what it shows.

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f'Point({self.x}, {self.y})'
p = Point(1, 2)
p
p.x
```

## Dataclasses

`@dataclass` writes `__init__`, `__repr__`, and `==` for you, from the fields you list.

```python
from dataclasses import dataclass
@dataclass
class Point:
    x: int
    y: int
Point(1, 2)
Point(1, 2) == Point(1, 2)
```

## Your turn: stack

Write a `Stack` class that keeps its items in a list.
It needs `push(x)`, `pop()`, which removes and returns the newest item, and `is_empty()`.

```python listing
s = Stack()
s.push(1)
s.push(2)
s.pop()        # 2
s.is_empty()   # False
```

```starter
class Stack:
    def __init__(self):
        self.items = []

    def push(self, x):
        ...

    def pop(self):
        ...

    def is_empty(self):
        ...
```

```check
s = Stack()
assert s.is_empty(), "a new Stack should be empty"
s.push(1)
s.push(2)
assert not s.is_empty(), "after two pushes, is_empty() should return False"
assert s.pop() == 2, "pop() should return the newest item"
assert s.pop() == 1, "the second pop() should return the first item pushed"
assert s.is_empty(), "after popping everything, is_empty() should return True"
```

```hint
A list already works as a stack: `append` adds to the end, and `pop()` removes from the end.
```

```hint
`not self.items` is `True` exactly when the list is empty.
```

```solution
class Stack:
    def __init__(self):
        self.items = []

    def push(self, x):
        self.items.append(x)

    def pop(self):
        return self.items.pop()

    def is_empty(self):
        return not self.items
```

## Recap

```python listing
class Point:
    def __init__(self, x, y):   # runs on Point(1, 2)
        self.x, self.y = x, y
    def __repr__(self):         # what the REPL shows
        return f'Point({self.x}, {self.y})'
from dataclasses import dataclass
@dataclass
class P:                        # __init__, __repr__, and == for free
    x: int
```
