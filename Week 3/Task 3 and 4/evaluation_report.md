# Text-to-SQL Benchmark Evaluation Report

## Summary Metrics
# Only taken 3 question because of resource exhausion problem
- Total Benchmark Questions: 3
- SQL Execution Success Rate: 66.67%
- Total Failed Queries: 1
- Total Queries Requiring Auto-Repair: 0
- Average Query Generation Latency: 13387.89 ms

## Detailed Evaluation Output Table

| Question | Generated SQL | Executed Successfully | Retry Needed | Final Status | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| List all products | `SELECT   T1."productCode",   T1."productName",   T1."productLine",   T1."productScale",   T1."productVendor",   T1."productDescription",   T1."quantityInStock",   T1."buyPrice",   T1."MSRP" FROM products AS T1;` | Yes | No | SUCCESS | 15185.34 |
| Get all customers | `SELECT   "customerNumber",   "customerName",   "contactLastName",   "contactFirstName",   phone,   "addressLine1",   "addressLine2",   city,   state,   "postalCode",   country,   "salesRepEmployeeNumber",   "creditLimit" FROM customers;` | Yes | No | SUCCESS | 14717.31 |
| Show all orders | `N/A` | No | No | FAILED | 10261.01 |
