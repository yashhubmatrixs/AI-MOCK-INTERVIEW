# Java

## JDK, JRE and JVM
The JVM (Java Virtual Machine) runs compiled bytecode. The JRE (Java Runtime Environment) is the JVM plus the standard class libraries needed to run programs. The JDK (Java Development Kit) is the JRE plus development tools such as the javac compiler. Because source is compiled to platform-independent bytecode, Java is "write once, run anywhere".

## == vs equals() in Java
For objects, == compares references (whether both variables point to the same object), while equals() compares logical content if the class overrides it (String does). For primitives, == compares values. Use equals() to compare strings.

## String immutability and the string pool
Java String objects are immutable: once created they cannot change, so every modification creates a new object. String literals are stored in the string pool and reused. StringBuilder is a mutable, non-synchronized (faster) alternative; StringBuffer is mutable and synchronized (thread-safe).

## final, finally and finalize
final: a final variable cannot be reassigned, a final method cannot be overridden, a final class cannot be extended. finally: a block after try/catch that runs whether or not an exception occurred (except if the JVM exits). finalize(): a deprecated method the garbage collector could call before reclaiming an object.

## Checked vs unchecked exceptions
Checked exceptions (such as IOException) are verified at compile time and must be caught or declared with throws. Unchecked exceptions extend RuntimeException (such as NullPointerException or ArrayIndexOutOfBoundsException) and need not be declared. Errors (such as OutOfMemoryError) are serious problems that programs usually should not catch.

## Java collections framework
List keeps insertion order and allows duplicates (ArrayList, LinkedList). Set forbids duplicates (HashSet, LinkedHashSet keeps insertion order, TreeSet keeps sorted order). Map stores key-value pairs with unique keys (HashMap, LinkedHashMap, TreeMap). Queue/Deque model FIFO structures (PriorityQueue, ArrayDeque).

## ArrayList vs LinkedList
ArrayList is backed by a resizable array: O(1) random access by index, O(n) insert or remove in the middle. LinkedList is a doubly linked list: O(1) insert/remove once you hold the node, O(n) access by index. ArrayList is the better default.

## How HashMap works
HashMap stores entries in an array of buckets. The key's hashCode() decides the bucket; keys that land in the same bucket (a collision) are chained in a linked list, which Java 8 converts to a balanced tree when a bucket grows large (threshold 8). The default capacity is 16 and default load factor 0.75; the table resizes when it fills past that. Average get/put is O(1). HashMap allows one null key and is not thread-safe.

## hashCode and equals contract
If two objects are equal according to equals(), they must return the same hashCode(). Override both together, otherwise hash-based collections such as HashMap and HashSet misbehave.

## HashMap vs Hashtable vs ConcurrentHashMap
HashMap is not synchronized and allows one null key and null values. Hashtable is a legacy synchronized class that allows no nulls. ConcurrentHashMap is designed for concurrent access with finer-grained locking and is preferred over Hashtable.

## Garbage collection in Java
The JVM automatically reclaims heap memory used by objects that are no longer reachable. The heap is generational (young generation for new objects, old generation for long-lived ones). System.gc() is only a request, not a guarantee.

## Stack vs heap memory
The stack holds method call frames, local variables and references, and is cleaned up automatically when a method returns. The heap holds objects and is managed by the garbage collector. Each thread has its own stack; the heap is shared.

## Creating threads in Java
A thread can be created by extending Thread or implementing Runnable (preferred, because it leaves your class free to extend something else). Callable is like Runnable but can return a result and throw checked exceptions. The synchronized keyword lets only one thread at a time hold an object's monitor lock; volatile guarantees visibility of a variable's latest value across threads. A deadlock happens when threads wait on each other's locks forever.

## Java 8 features
Java 8 introduced lambda expressions, functional interfaces, the Stream API, Optional, default and static methods in interfaces, and the new java.time date-time API.

## this and super
this refers to the current object (for example to separate a field from a parameter with the same name or to call another constructor). super refers to the parent class (to call its constructor or an overridden method).

## Immutable class in Java
To make an immutable class: declare the class final, make all fields private and final, set them only in the constructor, provide no setters, and return copies of any mutable fields.
