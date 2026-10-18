# Data Structures and Algorithms

## Big-O notation and time complexity
Big-O describes how running time or memory grows with input size n in the worst case, ignoring constants. Common classes from fastest to slowest: O(1) constant, O(log n) logarithmic, O(n) linear, O(n log n), O(n^2) quadratic, O(2^n) exponential. Space complexity measures the extra memory used.

## Array vs linked list
An array stores elements contiguously: O(1) access by index, O(n) insert or delete in the middle, fixed size (or amortised resizing). A linked list stores nodes connected by pointers: O(n) access, O(1) insert or delete at a known node, extra memory for pointers, and no random access.

## Stack and queue
A stack is LIFO (last in, first out) with push and pop; it is used for function call stacks, undo features, expression evaluation and balanced-bracket checking. A queue is FIFO (first in, first out) with enqueue and dequeue; it is used in scheduling, buffering and breadth-first search. A deque allows insertion and removal at both ends.

## Hash table and collision handling
A hash table maps keys to array positions using a hash function, giving average O(1) insert, lookup and delete (worst case O(n) when many keys collide). Collisions are handled by chaining (each bucket holds a list) or open addressing (probe for another free slot using linear probing, quadratic probing or double hashing).

## Binary search
Binary search finds a target in a sorted array by repeatedly comparing with the middle element and discarding half of the range, so it takes O(log n) time. Compute the middle as low + (high - low) / 2 to avoid integer overflow. It requires sorted data.

## Sorting algorithm complexities
Bubble, selection and insertion sort are O(n^2) (insertion sort is O(n) on nearly sorted input). Merge sort is O(n log n) in all cases, stable, and needs O(n) extra space. Quick sort is O(n log n) on average but O(n^2) in the worst case, in-place and not stable. Heap sort is O(n log n), in-place, not stable. Counting sort is O(n + k) for small integer ranges.

## Binary tree and binary search tree
A binary tree has at most two children per node. In a binary search tree (BST) every node's left subtree holds smaller keys and the right subtree larger keys, so search, insert and delete take O(h) where h is the height: O(log n) for a balanced tree and O(n) for a skewed one. An inorder traversal of a BST visits keys in sorted order. Self-balancing trees such as AVL and red-black trees keep the height O(log n).

## Tree traversals
Depth-first traversals: inorder (left, node, right), preorder (node, left, right), postorder (left, right, node). Level-order traversal is breadth-first and uses a queue.

## BFS vs DFS
Breadth-first search explores a graph level by level using a queue and finds the shortest path in an unweighted graph. Depth-first search goes as deep as possible along a branch first using recursion or a stack; it is used for cycle detection, topological sort and connected components. Both run in O(V + E) with an adjacency list.

## Graph representation and shortest paths
A graph can be stored as an adjacency matrix (O(V^2) space, O(1) edge lookup) or an adjacency list (O(V + E) space, better for sparse graphs). Dijkstra's algorithm finds shortest paths from one source when all edge weights are non-negative, in O((V + E) log V) with a priority queue. Bellman-Ford handles negative weights.

## Heap and priority queue
A binary heap is a complete binary tree where each parent is smaller (min-heap) or larger (max-heap) than its children. Insert and extract-min/max are O(log n); peeking at the top is O(1). A priority queue is commonly implemented with a heap.

## Dynamic programming
Dynamic programming solves problems with overlapping subproblems and optimal substructure by storing sub-results (memoization top-down or tabulation bottom-up) instead of recomputing them. Examples: Fibonacci, 0/1 knapsack, longest common subsequence, coin change.

## Recursion
A recursive function calls itself on a smaller input and needs a base case to stop; every call adds a stack frame, so very deep recursion can cause a stack overflow. Many recursions can be rewritten iteratively with an explicit stack.

## Two pointers and sliding window
Two pointers moves two indices through a sequence (often from both ends of a sorted array) to solve pair-sum and palindrome style problems in O(n). A sliding window keeps a moving range of elements to compute subarray or substring answers, such as the longest substring without repeating characters, in O(n).

## Find the first non-repeating element in an array
Make two passes. First count how many times each element occurs using a hash map (dictionary). Then scan the array in its original order and return the first element whose count is 1. Time O(n), extra space O(k) for k distinct elements.

## Check whether a string is a palindrome
Normalise the string (convert to lowercase and remove spaces and non-alphanumeric characters), then compare it with its reverse, or use two pointers moving inward from both ends. Time O(n); the two-pointer method needs O(1) extra space apart from the cleaned string.

## Check whether two strings are anagrams
Two strings are anagrams if they have the same length and the same count of every character. Count characters with a hash map or a fixed-size array (O(n) time), or compare the two sorted strings (O(n log n)).

## Find the second largest number without sorting
Scan the array once keeping two variables, largest and second_largest. For each value: if it is greater than largest, move largest into second_largest and update largest; otherwise if it is greater than second_largest and not equal to largest, update second_largest. Time O(n), space O(1). Handle arrays with fewer than two distinct values.

## Merge overlapping intervals
Sort the intervals by start value. Walk through them keeping a merged list: if the current interval starts at or before the end of the last merged interval, extend that end to the maximum of the two ends; otherwise append the current interval as new. Time O(n log n) because of the sort.

## Check whether a binary tree is height-balanced
A tree is height-balanced if, for every node, the heights of its left and right subtrees differ by at most 1. Do a postorder traversal that returns each subtree's height, and return a sentinel such as -1 as soon as any subtree is unbalanced. Time O(n), space O(h) for the recursion stack.

## Detect a cycle in a linked list
Floyd's tortoise-and-hare algorithm moves a slow pointer one step and a fast pointer two steps at a time; if they ever meet, the list has a cycle, and if the fast pointer reaches null there is none. Time O(n), space O(1).

## Reverse a linked list
Iterate through the list keeping three pointers (previous, current, next): save current.next, point current.next at previous, then advance previous and current. Time O(n), space O(1). A recursive version uses O(n) stack space.

## Valid parentheses
Use a stack: push every opening bracket; on a closing bracket the stack must be non-empty and its top must be the matching opener, which is popped. The string is valid if the stack is empty at the end. Time O(n).

## Two-sum problem
To find two numbers that add up to a target, scan the array once while storing each seen value in a hash map; for each element check whether target minus the element is already in the map. Time O(n), space O(n); the brute-force double loop is O(n^2).
