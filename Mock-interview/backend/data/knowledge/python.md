# Python

## List vs tuple
A list is mutable (items can be changed, added, removed) and written with square brackets. A tuple is immutable and written with parentheses. Tuples are slightly faster and smaller, and can be dictionary keys or set members when all their elements are hashable.

## Mutable and immutable types
Immutable: int, float, str, tuple, frozenset, bool. Mutable: list, dict, set, and most user-defined objects. A common pitfall is a mutable default argument such as def f(x, items=[]): the default list is created once and shared between calls; use None and create the list inside the function.

## is vs ==
== checks whether two values are equal. is checks whether two names refer to the very same object in memory (identity). Use is for None checks (x is None).

## Shallow copy vs deep copy
A shallow copy (copy.copy or list.copy()) creates a new container but the nested objects are still shared with the original. A deep copy (copy.deepcopy) recursively copies nested objects too, so changes to the copy never affect the original.

## Python dictionary
A dict stores key-value pairs in a hash table; keys must be hashable and unique. Average lookup, insert and delete are O(1). Since Python 3.7 dictionaries preserve insertion order.

## Generators and yield
A generator function uses yield to produce values one at a time and pauses between them, so values are computed lazily and memory use stays small even for huge sequences. A generator is an iterator; it can be consumed only once.

## Iterable vs iterator
An iterable (list, str, dict) can return an iterator via iter(). An iterator implements __next__ and remembers its position, raising StopIteration when exhausted.

## Decorators
A decorator is a function that takes another function and returns a new function that wraps it, adding behaviour such as logging, timing or authentication. The @decorator syntax placed above a function definition applies it.

## *args and **kwargs
*args collects extra positional arguments into a tuple. **kwargs collects extra keyword arguments into a dictionary. They let a function accept a variable number of arguments.

## Global Interpreter Lock (GIL)
In CPython the GIL is a mutex that lets only one thread execute Python bytecode at a time. So threads do not speed up CPU-bound code; use multiprocessing for CPU-bound work. Threads are still useful for I/O-bound work because the lock is released while waiting for I/O.

## Python memory management
CPython manages memory with reference counting: an object is freed when its count reaches zero. A cyclic garbage collector additionally cleans up reference cycles that reference counting cannot free.

## List comprehension
A list comprehension builds a list in one expression, for example [x * x for x in range(10) if x % 2 == 0]. It is concise and usually faster than an equivalent for loop that appends.

## Lambda functions
A lambda is a small anonymous function limited to a single expression, written lambda x: x + 1. Often used as a key function in sorted(), map() or filter().

## Context managers and the with statement
The with statement guarantees setup and cleanup around a block, for example closing a file automatically even if an error occurs. Objects support it by implementing __enter__ and __exit__ (or by using contextlib.contextmanager).

## Exception handling in Python
Use try to run code, except to handle specific errors, else for code that runs only if no exception occurred, and finally for cleanup that always runs. Catch specific exceptions rather than a bare except.

## __init__, self and __name__
__init__ is the initialiser called when an object is created, and self is the conventional name for the instance. The check if __name__ == "__main__": runs code only when the file is executed directly, not when it is imported.

## append vs extend
list.append(x) adds x as a single element at the end. list.extend(iterable) adds every element of the iterable. [1, 2].append([3, 4]) gives [1, 2, [3, 4]], while [1, 2].extend([3, 4]) gives [1, 2, 3, 4].

## Time complexity of common Python operations
list: indexing O(1), append amortised O(1), insert at front O(n), membership test (x in list) O(n). dict and set: lookup, insert and membership test average O(1). Sorting with sorted() or list.sort() is O(n log n).

## Virtual environments
A virtual environment (venv, virtualenv or a conda environment) isolates a project's installed packages from other projects and from the system Python, so each project can have its own dependency versions. Dependencies are usually listed in requirements.txt.

## Python language characteristics
Python is a high-level, dynamically typed, interpreted language (source is compiled to bytecode that the interpreter runs) that supports object-oriented, procedural and functional styles.
