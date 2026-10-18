# DBMS and SQL

## ACID properties
ACID describes reliable database transactions. Atomicity: a transaction happens completely or not at all. Consistency: a transaction moves the database from one valid state to another, respecting constraints. Isolation: concurrent transactions do not interfere with each other. Durability: once committed, data survives crashes.

## Normalization and normal forms
Normalization organises tables to reduce redundancy and update anomalies. 1NF: every column holds atomic values, no repeating groups. 2NF: in 1NF and no non-key column depends on only part of a composite key (no partial dependency). 3NF: in 2NF and no non-key column depends on another non-key column (no transitive dependency). BCNF: for every functional dependency, the left side is a candidate key. Denormalization deliberately adds redundancy to speed up reads.

## Types of keys
A super key is any set of columns that uniquely identifies a row. A candidate key is a minimal super key. The primary key is the candidate key chosen to identify rows: unique and not null, one per table. A foreign key refers to the primary key of another table and enforces referential integrity. A composite key uses more than one column. A unique key enforces uniqueness but, unlike a primary key, allows NULL values and a table may have several.

## SQL joins
INNER JOIN returns only rows with matches in both tables. LEFT JOIN returns all rows from the left table and matching rows from the right (NULL where none). RIGHT JOIN is the mirror image. FULL OUTER JOIN returns all rows from both; MySQL has no FULL OUTER JOIN, so it is emulated with LEFT JOIN UNION RIGHT JOIN. CROSS JOIN returns the Cartesian product. A self join joins a table to itself.

## WHERE vs HAVING
WHERE filters individual rows before grouping and cannot use aggregate functions. HAVING filters groups after GROUP BY and can use aggregates such as COUNT(*) > 5.

## DELETE vs TRUNCATE vs DROP
DELETE removes rows one by one, accepts a WHERE clause, and can be rolled back inside a transaction. TRUNCATE removes all rows quickly, cannot take a WHERE clause, and resets AUTO_INCREMENT counters; in MySQL it is DDL and commits implicitly. DROP removes the whole table, including its structure.

## Database indexes
An index is a data structure, usually a B-tree or B+ tree, that lets the database find rows without scanning the whole table. It speeds up reads (WHERE, JOIN, ORDER BY) but uses extra storage and slows INSERT, UPDATE and DELETE because the index must be maintained. A composite index follows the leftmost-prefix rule. In InnoDB the primary key is the clustered index that determines the physical order of rows.

## Transaction isolation levels
From weakest to strongest: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE. Anomalies: a dirty read sees uncommitted data; a non-repeatable read gets different values when re-reading the same row; a phantom read sees new rows appear on re-running a query. MySQL InnoDB defaults to REPEATABLE READ.

## SQL vs NoSQL
SQL (relational) databases such as MySQL and PostgreSQL store data in tables with a fixed schema, use SQL, and provide strong ACID guarantees. NoSQL databases (MongoDB document store, Redis key-value, Cassandra wide-column, Neo4j graph) have flexible schemas and often scale horizontally more easily, trading some consistency guarantees.

## UNION vs UNION ALL
UNION combines the results of two queries and removes duplicate rows. UNION ALL keeps duplicates and is faster because it skips the de-duplication step. Both need the same number of columns with compatible types.

## Second highest salary query
Common approaches: SELECT MAX(salary) FROM employee WHERE salary < (SELECT MAX(salary) FROM employee); or SELECT DISTINCT salary FROM employee ORDER BY salary DESC LIMIT 1 OFFSET 1; or use a window function such as DENSE_RANK() OVER (ORDER BY salary DESC) and pick rank 2 (MySQL 8.0 and later). DENSE_RANK handles ties correctly.

## Stored procedure vs function
A stored procedure is a saved block of SQL that can take input and output parameters and may perform data changes; it is called with CALL. A function must return a value and can be used inside SQL expressions such as a SELECT list.

## Views
A view is a saved SELECT query presented as a virtual table. It simplifies complex queries and can restrict which columns users see. A normal view stores no data itself.

## CHAR vs VARCHAR
CHAR(n) is fixed length and pads shorter values with spaces; VARCHAR(n) is variable length and stores only the characters used plus a small length prefix. Use CHAR for values of constant length such as country codes.

## InnoDB vs MyISAM
InnoDB is the default MySQL storage engine: it supports transactions (ACID), row-level locking and foreign keys. MyISAM does not support transactions or foreign keys and locks the whole table on writes.

## COUNT(*) vs COUNT(column) and NULL handling
COUNT(*) counts all rows. COUNT(column) counts only rows where that column is not NULL. NULL means unknown, so comparisons with = NULL never match; use IS NULL or IS NOT NULL.

## Transaction control
BEGIN (or START TRANSACTION) starts a transaction, COMMIT makes its changes permanent, ROLLBACK undoes them, and SAVEPOINT marks a point you can roll back to.

## Subquery vs join
A subquery is a query nested inside another. A join combines tables side by side. Joins are often faster and easier for the optimiser, but a subquery can be clearer for a filter such as WHERE id IN (SELECT ...).

## Database deadlock
A deadlock occurs when two transactions each hold a lock the other needs, so neither can proceed. The database detects it and rolls back one transaction (the victim). Reduce deadlocks by accessing tables and rows in a consistent order and keeping transactions short.

## ER model
An entity-relationship model describes entities (things), attributes (their properties) and relationships between them with a cardinality of one-to-one, one-to-many or many-to-many. A many-to-many relationship is implemented with a junction (bridge) table holding two foreign keys.

## Aggregate functions and GROUP BY
Aggregate functions such as COUNT, SUM, AVG, MIN and MAX summarise many rows into one value. GROUP BY splits rows into groups so the aggregate is calculated per group; every non-aggregated column in the SELECT list must appear in GROUP BY.
