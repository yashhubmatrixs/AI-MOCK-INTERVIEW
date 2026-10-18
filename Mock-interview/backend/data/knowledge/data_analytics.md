# Data Analytics, BI and Data Mining

## ETL vs ELT
ETL (extract, transform, load) cleans and reshapes data before loading it into the warehouse. ELT loads raw data first and transforms it inside the warehouse, which suits modern, scalable cloud warehouses.

## OLTP vs OLAP
OLTP systems handle many small, fast transactions (banking, orders) with normalised tables. OLAP systems are optimised for analytical queries over large historical data, typically in a data warehouse with denormalised star or snowflake schemas.

## Star schema, fact and dimension tables
A star schema has a central fact table holding measurable events (sales amount, quantity) with foreign keys to surrounding dimension tables that hold descriptive attributes (date, product, customer, region). It makes analytical queries simple and fast. A snowflake schema further normalises the dimensions.

## Exploratory data analysis (EDA)
EDA summarises and visualises a dataset before modelling to understand distributions, spot missing values and outliers, check relationships between variables (correlation, scatter plots) and form hypotheses. Typical tools: describe(), histograms, box plots, correlation heatmaps.

## Handling outliers
Outliers can be detected with the IQR rule (values below Q1 - 1.5 x IQR or above Q3 + 1.5 x IQR) or a z-score beyond about 3. Decide whether they are errors or real extremes; options are to remove, cap (winsorize), transform (log) or keep them and use robust statistics such as the median.

## Mean vs median vs mode
The mean is the average and is sensitive to outliers. The median is the middle value and is robust to outliers, so it describes skewed data such as income better. The mode is the most frequent value.

## Correlation vs causation
Correlation means two variables move together; it does not prove that one causes the other, because a third factor may drive both or the link may be coincidence. Establishing causation needs controlled experiments such as randomised A/B tests.

## Hypothesis testing and p-value
A hypothesis test compares a null hypothesis (no effect) with an alternative. The p-value is the probability of seeing results at least as extreme as observed if the null hypothesis were true; a small value (commonly below 0.05) is taken as evidence against the null. It is not the probability that the null hypothesis is true.

## Pandas basics
In pandas a Series is one labelled column and a DataFrame is a table. loc selects by label while iloc selects by integer position. Common operations: merge (SQL-style join), concat (stack frames), groupby with aggregation, pivot_table, isnull, fillna, dropna, drop_duplicates and apply.

## NumPy array vs Python list
A NumPy array stores elements of a single type in contiguous memory and supports fast vectorised operations without Python loops, so it is much faster and more memory efficient than a list for numerical work.

## Power BI: Power Query, DAX and data model
Power BI uses Power Query (the M language) to connect to and transform data, a data model of related tables (ideally a star schema), and DAX (Data Analysis Expressions) for calculations. A measure is calculated at query time and responds to filters on the report. A calculated column is computed row by row when the data refreshes and stored in the model. Row-level security restricts which rows each user can see.

## Tableau: dimensions, measures and extracts
In Tableau, dimensions are categorical fields used to slice data (region, category) and measures are numeric fields that are aggregated (sales, profit). A live connection queries the source directly, while an extract is a compressed snapshot that is faster. Level of Detail (LOD) expressions FIXED, INCLUDE and EXCLUDE compute aggregations at a different granularity than the view. Blue pills are discrete and green pills are continuous.

## Data cleaning steps
Typical steps: remove duplicates, fix data types, handle missing values, standardise formats (dates, text case, units), correct inconsistent labels and validate values against allowed ranges or business rules.

## Data mining techniques
Common data mining tasks are classification (predict a category), regression (predict a number), clustering (group similar records), association rule mining (find items bought together, measured by support, confidence and lift; the Apriori algorithm is a classic method), and anomaly detection (find unusual records such as fraud).

## Association rules: support, confidence, lift
For a rule A to B, support is the fraction of all transactions that contain both A and B, confidence is the fraction of transactions with A that also contain B, and lift is confidence divided by the support of B; a lift above 1 means A and B occur together more than expected by chance.

## A/B testing
An A/B test randomly splits users into a control group (version A) and a treatment group (version B), measures a pre-chosen metric, and uses a statistical test to decide whether the difference is larger than chance would explain. Decide the sample size and metric in advance and avoid stopping the test early on a lucky result.

## Business analysis basics
A business analyst gathers and documents requirements from stakeholders (for example in a BRD, business requirements document), writes user stories with acceptance criteria, and bridges business and technical teams. SWOT analysis lists strengths, weaknesses, opportunities and threats. KPIs are the key metrics used to track whether goals are being met.
