# Operating Systems

## Process vs thread
A process is a program in execution with its own address space and resources. A thread is a lightweight unit of execution inside a process; threads of the same process share code, data and heap but each has its own stack and registers. Threads are cheaper to create and to switch between, but a bug in one thread can affect the whole process.

## Process states
A process moves through new, ready, running, waiting (blocked) and terminated. The scheduler picks one process from the ready queue to run on the CPU.

## Context switch
A context switch saves the state of the running process (registers, program counter) and loads the saved state of the next one. It is pure overhead, because no useful work happens while it runs.

## CPU scheduling algorithms
FCFS (first come first served) is simple but suffers the convoy effect. SJF (shortest job first) minimises average waiting time but can starve long jobs; its preemptive version is SRTF. Round Robin gives each process a fixed time quantum and is fair and preemptive. Priority scheduling can starve low-priority processes, which is solved by aging. Multilevel queue scheduling keeps separate ready queues for different process classes.

## Deadlock and the four necessary conditions
A deadlock is a state where processes wait for each other forever. It needs all four Coffman conditions: mutual exclusion, hold and wait, no preemption, and circular wait. Prevention breaks at least one condition; avoidance (Banker's algorithm) grants resources only if the system stays in a safe state; detection and recovery finds and breaks deadlocks after they happen.

## Deadlock vs starvation
In a deadlock a set of processes is blocked forever waiting on each other. In starvation a process waits indefinitely because others keep getting priority, although the system as a whole keeps making progress. Aging prevents starvation.

## Paging vs segmentation
Paging splits memory into fixed-size pages (logical) and frames (physical); it avoids external fragmentation but can cause internal fragmentation. Segmentation splits a program into variable-size logical segments such as code, data and stack; it matches the programmer's view but can cause external fragmentation.

## Virtual memory and demand paging
Virtual memory lets a process use more memory than physically installed by keeping only the needed pages in RAM and the rest on disk. With demand paging a page is loaded only when it is accessed; accessing a page not in RAM causes a page fault.

## Thrashing
Thrashing happens when the system spends more time swapping pages in and out than executing processes, usually because too many processes compete for too little memory. Reducing the degree of multiprogramming or adding RAM helps.

## Page replacement algorithms
When memory is full a page must be evicted. FIFO evicts the oldest page and can show Belady's anomaly (more frames causing more faults). LRU evicts the least recently used page. Optimal evicts the page that will not be used for the longest time; it gives the fewest faults but cannot be implemented because it needs future knowledge.

## Semaphore vs mutex
A mutex is a locking mechanism with ownership: only the thread that locked it can unlock it, and it protects a critical section. A semaphore is an integer counter with wait (P) and signal (V) operations used for signalling and for limiting access to several identical resources; a binary semaphore takes values 0 and 1, a counting semaphore any non-negative value.

## Race condition and critical section
A race condition occurs when the outcome depends on the unpredictable order in which threads access shared data. The critical section is the code that accesses shared data; it must be protected so that only one thread at a time executes it, using locks, mutexes or semaphores.

## Kernel mode, user mode and system calls
The CPU runs in kernel mode for privileged operating system code and in user mode for applications. A system call is how a user program asks the kernel for a service such as reading a file; it switches the CPU into kernel mode.

## Inter-process communication
Processes communicate with pipes, message queues, shared memory, sockets and signals. Shared memory is the fastest because no kernel copy is needed per message, but it needs explicit synchronisation.

## Internal and external fragmentation
Internal fragmentation is wasted space inside an allocated block (a process gets a bigger block than it needs). External fragmentation is free memory split into many small non-contiguous holes that cannot satisfy a large request. Compaction or paging reduces external fragmentation.
