# Database / MySQL Reference

---

## MCP Tool

### Invocation
```python
mcp__mcp_server_mysql__mysql_query(query="SELECT * FROM table LIMIT 10")
```

### Return format
```json
{
  "column_names": ["id", "name", "email"],
  "rows": [
    [1, "Alice", "alice@example.com"],
    [2, "Bob", "bob@example.com"]
  ]
}
```

---

## Safe Usage Rules

1. Start with read-only queries (SELECT) before any modifications
2. Always add LIMIT to SELECT queries (default LIMIT 100)
3. Select specific columns instead of `SELECT *`
4. Validate WHERE clauses with a SELECT before running UPDATE or DELETE
5. Use transactions for multi-statement modifications
6. Back up data before destructive operations

---

## Schema Discovery

### Databases
```sql
SHOW DATABASES;
SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA;
USE database_name;
SELECT DATABASE();                    -- current database
```

### Tables
```sql
SHOW TABLES;
SHOW TABLES LIKE 'prefix_%';
SHOW FULL TABLES;                     -- includes table type (BASE TABLE / VIEW)
SHOW TABLE STATUS;                    -- row count, engine, size, create time
SHOW TABLE STATUS LIKE 'table_name';
```

### Columns / Structure
```sql
DESCRIBE table_name;                  -- column, type, null, key, default, extra
SHOW COLUMNS FROM table_name;        -- same as DESCRIBE
SHOW FULL COLUMNS FROM table_name;   -- includes collation, privileges, comment
SHOW CREATE TABLE table_name;        -- full DDL with constraints
```

### Indexes
```sql
SHOW INDEX FROM table_name;
SHOW INDEX FROM table_name WHERE Key_name = 'PRIMARY';
```

### Variables / Status
```sql
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE '%timeout%';
SHOW GLOBAL STATUS;
SHOW PROCESSLIST;                     -- active connections/queries
```

### Information Schema
```sql
SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'dbname';

SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbname' AND TABLE_NAME = 'tablename';

SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'dbname' AND REFERENCED_TABLE_NAME IS NOT NULL;
```

---

## Query Patterns

### SELECT
```sql
-- Basic
SELECT col1, col2 FROM table WHERE condition LIMIT 100;

-- WHERE operators
WHERE col = 'value'
WHERE col != 'value'
WHERE col > 10
WHERE col BETWEEN 10 AND 20
WHERE col IN ('a', 'b', 'c')
WHERE col NOT IN (SELECT ...)
WHERE col LIKE 'prefix%'
WHERE col LIKE '%suffix'
WHERE col LIKE '%middle%'
WHERE col REGEXP '^[A-Z]{2}[0-9]+'
WHERE col IS NULL
WHERE col IS NOT NULL
WHERE condition1 AND condition2
WHERE condition1 OR condition2

-- ORDER BY
ORDER BY col ASC
ORDER BY col DESC
ORDER BY col1 ASC, col2 DESC

-- LIMIT / OFFSET
LIMIT 100
LIMIT 100 OFFSET 200
LIMIT 200, 100                -- offset, count (MySQL syntax)

-- DISTINCT
SELECT DISTINCT col FROM table;
SELECT COUNT(DISTINCT col) FROM table;
```

### JOINs
```sql
-- INNER JOIN (rows matching in both)
SELECT a.*, b.col FROM table_a a
INNER JOIN table_b b ON a.id = b.a_id;

-- LEFT JOIN (all from left, matching from right)
SELECT a.*, b.col FROM table_a a
LEFT JOIN table_b b ON a.id = b.a_id;

-- RIGHT JOIN (all from right, matching from left)
SELECT a.*, b.col FROM table_a a
RIGHT JOIN table_b b ON a.id = b.a_id;

-- CROSS JOIN (cartesian product)
SELECT a.*, b.* FROM table_a a CROSS JOIN table_b b;

-- Self join
SELECT e.name, m.name AS manager
FROM employees e LEFT JOIN employees m ON e.manager_id = m.id;

-- Multiple joins
SELECT o.id, c.name, p.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id;
```

### GROUP BY / HAVING
```sql
SELECT col, COUNT(*) as cnt
FROM table
GROUP BY col
HAVING cnt > 5
ORDER BY cnt DESC;

-- Group by multiple columns
SELECT year, month, SUM(amount)
FROM sales
GROUP BY year, month;

-- WITH ROLLUP (subtotals)
SELECT region, product, SUM(amount)
FROM sales
GROUP BY region, product WITH ROLLUP;
```

### Subqueries
```sql
-- In WHERE
SELECT * FROM orders WHERE customer_id IN (
    SELECT id FROM customers WHERE country = 'US'
);

-- Correlated subquery
SELECT * FROM orders o WHERE amount > (
    SELECT AVG(amount) FROM orders WHERE customer_id = o.customer_id
);

-- EXISTS
SELECT * FROM customers c WHERE EXISTS (
    SELECT 1 FROM orders WHERE customer_id = c.id
);

-- In FROM (derived table)
SELECT avg_amount FROM (
    SELECT customer_id, AVG(amount) as avg_amount FROM orders GROUP BY customer_id
) AS sub WHERE avg_amount > 1000;
```

### CTEs (Common Table Expressions)
```sql
WITH
  active_customers AS (
    SELECT customer_id, COUNT(*) as order_count
    FROM orders
    WHERE order_date > '2025-01-01'
    GROUP BY customer_id
  ),
  high_value AS (
    SELECT customer_id FROM active_customers WHERE order_count > 10
  )
SELECT c.name, ac.order_count
FROM customers c
JOIN active_customers ac ON c.id = ac.customer_id
WHERE c.id IN (SELECT customer_id FROM high_value);
```

### Window Functions
```sql
-- ROW_NUMBER
SELECT *, ROW_NUMBER() OVER (ORDER BY amount DESC) as rn FROM orders;

-- ROW_NUMBER per group
SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY date DESC) as rn
FROM orders;

-- RANK / DENSE_RANK
SELECT *, RANK() OVER (ORDER BY score DESC) as rank FROM students;
SELECT *, DENSE_RANK() OVER (ORDER BY score DESC) as dense_rank FROM students;

-- Running total
SELECT *, SUM(amount) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) as running_total
FROM transactions;

-- Moving average
SELECT *, AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma7
FROM daily_sales;

-- LAG / LEAD
SELECT *, LAG(amount, 1) OVER (ORDER BY date) as prev_amount,
         LEAD(amount, 1) OVER (ORDER BY date) as next_amount
FROM daily_sales;

-- NTILE
SELECT *, NTILE(4) OVER (ORDER BY amount DESC) as quartile FROM orders;

-- FIRST_VALUE / LAST_VALUE
SELECT *, FIRST_VALUE(amount) OVER (PARTITION BY customer_id ORDER BY date) as first_order
FROM orders;
```

---

## Aggregation Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `COUNT(*)` | Count all rows | `SELECT COUNT(*) FROM t` |
| `COUNT(col)` | Count non-NULL values | `SELECT COUNT(email) FROM t` |
| `COUNT(DISTINCT col)` | Count unique values | `SELECT COUNT(DISTINCT city) FROM t` |
| `SUM(col)` | Sum values | `SELECT SUM(amount) FROM t` |
| `AVG(col)` | Average | `SELECT AVG(price) FROM t` |
| `MIN(col)` | Minimum | `SELECT MIN(date) FROM t` |
| `MAX(col)` | Maximum | `SELECT MAX(score) FROM t` |
| `GROUP_CONCAT(col)` | Concatenate values | `SELECT GROUP_CONCAT(name SEPARATOR ', ') FROM t GROUP BY dept` |
| `GROUP_CONCAT(DISTINCT col ORDER BY col)` | Sorted unique concat | Full syntax |
| `STD(col)` / `STDDEV(col)` | Standard deviation | `SELECT STD(score) FROM t` |
| `VARIANCE(col)` | Variance | `SELECT VARIANCE(score) FROM t` |

---

## String Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `CONCAT(a, b, ...)` | Concatenate | `CONCAT(first, ' ', last)` |
| `CONCAT_WS(sep, a, b)` | Concat with separator | `CONCAT_WS(', ', city, state)` |
| `SUBSTRING(s, pos, len)` | Extract substring | `SUBSTRING(name, 1, 3)` |
| `LEFT(s, n)` | Left N chars | `LEFT(code, 2)` |
| `RIGHT(s, n)` | Right N chars | `RIGHT(phone, 4)` |
| `REPLACE(s, from, to)` | Replace occurrences | `REPLACE(url, 'http:', 'https:')` |
| `TRIM(s)` | Remove whitespace | `TRIM(name)` |
| `LTRIM(s)` / `RTRIM(s)` | Left/right trim | `LTRIM(name)` |
| `UPPER(s)` | Uppercase | `UPPER(code)` |
| `LOWER(s)` | Lowercase | `LOWER(email)` |
| `LENGTH(s)` | Byte length | `LENGTH(name)` |
| `CHAR_LENGTH(s)` | Character length | `CHAR_LENGTH(name)` |
| `LOCATE(sub, s)` | Find position | `LOCATE('@', email)` |
| `LPAD(s, len, pad)` | Left pad | `LPAD(id, 5, '0')` |
| `RPAD(s, len, pad)` | Right pad | `RPAD(name, 20, ' ')` |
| `REVERSE(s)` | Reverse string | `REVERSE(name)` |
| `REGEXP` | Regex match | `WHERE name REGEXP '^[A-Z]'` |
| `REGEXP_REPLACE(s, pat, rep)` | Regex replace | `REGEXP_REPLACE(phone, '[^0-9]', '')` |
| `REGEXP_SUBSTR(s, pat)` | Regex extract | `REGEXP_SUBSTR(text, '[0-9]+')` |
| `JSON_EXTRACT(col, path)` | JSON field | `JSON_EXTRACT(data, '$.name')` |
| `col->'$.path'` | JSON shorthand | `data->'$.address.city'` |
| `col->>'$.path'` | JSON unquoted | `data->>'$.name'` |

---

## Date Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `NOW()` | Current datetime | `SELECT NOW()` |
| `CURDATE()` | Current date | `SELECT CURDATE()` |
| `CURTIME()` | Current time | `SELECT CURTIME()` |
| `DATE(dt)` | Extract date part | `DATE(created_at)` |
| `TIME(dt)` | Extract time part | `TIME(created_at)` |
| `YEAR(dt)` | Year | `YEAR(date)` |
| `MONTH(dt)` | Month (1-12) | `MONTH(date)` |
| `DAY(dt)` | Day of month | `DAY(date)` |
| `HOUR(dt)` | Hour | `HOUR(time)` |
| `MINUTE(dt)` | Minute | `MINUTE(time)` |
| `SECOND(dt)` | Second | `SECOND(time)` |
| `DAYOFWEEK(dt)` | Day of week (1=Sun) | `DAYOFWEEK(date)` |
| `DAYNAME(dt)` | Day name | `DAYNAME(date)` |
| `MONTHNAME(dt)` | Month name | `MONTHNAME(date)` |
| `QUARTER(dt)` | Quarter (1-4) | `QUARTER(date)` |
| `WEEK(dt)` | Week number | `WEEK(date)` |
| `DATE_FORMAT(dt, fmt)` | Format date | `DATE_FORMAT(date, '%Y-%m-%d')` |
| `STR_TO_DATE(s, fmt)` | Parse string to date | `STR_TO_DATE('15/01/2025', '%d/%m/%Y')` |
| `DATE_ADD(dt, INTERVAL)` | Add interval | `DATE_ADD(date, INTERVAL 7 DAY)` |
| `DATE_SUB(dt, INTERVAL)` | Subtract interval | `DATE_SUB(NOW(), INTERVAL 1 MONTH)` |
| `DATEDIFF(d1, d2)` | Days between | `DATEDIFF(end, start)` |
| `TIMESTAMPDIFF(unit, d1, d2)` | Difference in unit | `TIMESTAMPDIFF(HOUR, start, end)` |
| `UNIX_TIMESTAMP(dt)` | To Unix time | `UNIX_TIMESTAMP(NOW())` |
| `FROM_UNIXTIME(ts)` | From Unix time | `FROM_UNIXTIME(1700000000)` |
| `LAST_DAY(dt)` | Last day of month | `LAST_DAY(date)` |

DATE_FORMAT codes: `%Y` (4-digit year), `%y` (2-digit), `%m` (month 01-12), `%d` (day 01-31), `%H` (hour 00-23), `%i` (minute 00-59), `%s` (second 00-59), `%W` (day name), `%M` (month name), `%a` (short day), `%b` (short month), `%p` (AM/PM)

INTERVAL units: `MICROSECOND`, `SECOND`, `MINUTE`, `HOUR`, `DAY`, `WEEK`, `MONTH`, `QUARTER`, `YEAR`, `SECOND_MICROSECOND`, `MINUTE_MICROSECOND`, `MINUTE_SECOND`, `HOUR_MICROSECOND`, `HOUR_SECOND`, `HOUR_MINUTE`, `DAY_MICROSECOND`, `DAY_SECOND`, `DAY_MINUTE`, `DAY_HOUR`, `YEAR_MONTH`

---

## Conditional Expressions

```sql
-- IF
SELECT IF(amount > 100, 'high', 'low') as category FROM orders;

-- CASE WHEN
SELECT
    CASE
        WHEN score >= 90 THEN 'A'
        WHEN score >= 80 THEN 'B'
        WHEN score >= 70 THEN 'C'
        ELSE 'F'
    END as grade
FROM students;

-- Simple CASE
SELECT CASE status WHEN 'A' THEN 'Active' WHEN 'I' THEN 'Inactive' ELSE 'Unknown' END FROM t;

-- IFNULL (return alt if NULL)
SELECT IFNULL(nickname, name) as display_name FROM users;

-- COALESCE (first non-NULL)
SELECT COALESCE(nickname, first_name, email, 'Unknown') as display FROM users;

-- NULLIF (return NULL if equal)
SELECT NULLIF(a, b) FROM t;    -- returns NULL if a = b, else a
```

---

## Export Targets

### Excel (openpyxl)
```python
import openpyxl
result = mcp__mcp_server_mysql__mysql_query(query="SELECT ...")
wb = openpyxl.Workbook()
ws = wb.active
ws.append(result["column_names"])
for row in result["rows"]:
    ws.append(row)
wb.save("/tmp/export.xlsx")
```

### CSV
```python
import csv
with open("/tmp/export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(result["column_names"])
    writer.writerows(result["rows"])
```

### Google Sheets
```bash
# Upload CSV then convert
gws drive files create --upload "/tmp/export.csv" --name "Export" --mimeType "application/vnd.google-apps.spreadsheet"
```

### JSON
```python
import json
data = [dict(zip(result["column_names"], row)) for row in result["rows"]]
with open("/tmp/export.json", "w") as f:
    json.dump(data, f, indent=2, default=str)
```

### PDF (reportlab)
```python
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

doc = SimpleDocTemplate("/tmp/export.pdf", pagesize=landscape(A4))
table_data = [result["column_names"]] + result["rows"]
table = Table(table_data)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
]))
doc.build([table])
```
