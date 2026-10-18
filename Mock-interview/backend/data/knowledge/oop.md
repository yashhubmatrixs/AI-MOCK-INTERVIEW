# Object-Oriented Programming (OOP)

## Four pillars of OOP
The four pillars of object-oriented programming (OOPs) are abstraction, encapsulation, inheritance and polymorphism.

## Abstraction
Abstraction means hiding implementation details and exposing only the essential behaviour to the user. It is achieved with abstract classes and interfaces. Example: you call list.sort() without knowing which sorting algorithm runs inside.

## Encapsulation
Encapsulation bundles data (fields) and the methods that work on it into one class and restricts direct access to the data using access modifiers such as private, protected and public. Outside code goes through getters and setters, which lets the class validate changes. It is also called data hiding.

## Abstraction vs encapsulation
Abstraction hides complexity at the design level (what an object does). Encapsulation protects an object's internal state at the implementation level (how its data is guarded). Abstraction is achieved with abstract classes and interfaces; encapsulation is achieved with access modifiers and getters/setters.

## Inheritance
Inheritance lets a child (sub) class acquire the fields and methods of a parent (super) class, modelling an "is-a" relationship and enabling code reuse. Java does not allow a class to extend more than one class (to avoid the diamond problem) but a class can implement many interfaces. Python supports multiple inheritance and resolves method lookup with the MRO (method resolution order, C3 linearization).

## Polymorphism
Polymorphism means one interface, many forms. Compile-time (static) polymorphism is method overloading: same method name, different parameter lists, resolved by the compiler. Run-time (dynamic) polymorphism is method overriding: a subclass redefines a parent method, and the version that runs is chosen at run time based on the actual object (dynamic dispatch).

## Method overloading vs overriding
Overloading: same class, same name, different parameters (number, type or order); return type alone cannot differ; resolved at compile time. Overriding: subclass provides its own implementation of an inherited method with the same signature; resolved at run time; the overriding method cannot reduce visibility; static, final and private methods cannot be overridden.

## Abstract class vs interface
An abstract class can have fields, constructors, and both abstract and concrete methods, and a class can extend only one. An interface defines a contract of methods a class promises to implement, and a class can implement many interfaces. Since Java 8 interfaces may contain default and static methods; interface fields are implicitly public static final. Use an abstract class for shared state and partial implementation, an interface for a capability or contract.

## Class, object and constructor
A class is a blueprint; an object is an instance of that class with its own state. A constructor is a special method that initialises a new object. In Java it has the same name as the class and no return type; if you write none, the compiler supplies a default no-argument constructor. In Python the initialiser is __init__.

## Composition vs inheritance
Inheritance models "is-a" (Dog is an Animal). Composition models "has-a" (Car has an Engine) by holding another object as a field. Prefer composition when you only need to reuse behaviour, because it is more flexible and avoids tight coupling to a parent class.

## SOLID principles
S - Single Responsibility: a class should have one reason to change. O - Open/Closed: open for extension, closed for modification. L - Liskov Substitution: subclasses must be usable wherever the parent is expected. I - Interface Segregation: prefer small, specific interfaces. D - Dependency Inversion: depend on abstractions, not concrete classes.

## Access modifiers in Java
public: visible everywhere. protected: same package and subclasses. default (no keyword): same package only. private: same class only.

## Coupling and cohesion
Good design has low coupling (classes depend on each other as little as possible) and high cohesion (a class's members all relate to one purpose).

## Static vs instance members
A static member belongs to the class itself and is shared by all objects; an instance member belongs to one particular object. Static methods cannot directly use instance fields or this.
