SCHEMA_CONTEXT = """
You are a Text-to-SQL expert working with the ClassicModels PostgreSQL database.

Tables:
1. productlines("productLine", "textDescription", "htmlDescription", image)
2. products("productCode", "productName", "productLine", "productScale", "productVendor",
            "productDescription", "quantityInStock", "buyPrice", "MSRP")
3. offices("officeCode", city, phone, "addressLine1", "addressLine2", state, country,
           "postalCode", territory)
4. employees("employeeNumber", "lastName", "firstName", extension, email, "officeCode",
             "reportsTo", "jobTitle")
5. customers("customerNumber", "customerName", "contactLastName", "contactFirstName",
             phone, "addressLine1", "addressLine2", city, state, "postalCode", country,
             "salesRepEmployeeNumber", "creditLimit")
6. payments("customerNumber", "checkNumber", "paymentDate", amount)
7. orders("orderNumber", "orderDate", "requiredDate", "shippedDate", status, comments,
          "customerNumber")
8. orderdetails("orderNumber", "productCode", "quantityOrdered", "priceEach",
                "orderLineNumber")

Key relationships:
- products."productLine" = productlines."productLine"
- employees."officeCode" = offices."officeCode"
- employees."reportsTo" = employees."employeeNumber"
- customers."salesRepEmployeeNumber" = employees."employeeNumber"
- payments."customerNumber" = customers."customerNumber"
- orders."customerNumber" = customers."customerNumber"
- orderdetails."orderNumber" = orders."orderNumber"
- orderdetails."productCode" = products."productCode"

Important rules:
- Return PostgreSQL only.
- Quote camelCase and mixed-case column names with double quotes.
- Generate read-only SQL only. Never write, mutate, create, or drop data.
""".strip()


DECOMPOSITION_PROMPT = """
{schema}

Analyze this question and break it into structured components.

Question: {question}

Return valid JSON only:
{{
  "intent": "what is being asked",
  "tables": ["table"],
  "columns": ["column"],
  "filters": "WHERE conditions or None",
  "joins": "JOIN path or None",
  "aggregation": "COUNT/SUM/AVG/GROUP BY/etc. or None"
}}
""".strip()


SQL_GENERATION_PROMPT = """
{schema}

Using this structured decomposition, generate one valid PostgreSQL SELECT query.

Decomposition:
{decomposition}

Original question:
{question}

Rules:
- Return only raw SQL.
- Use clear aliases.
- Add a LIMIT only when the user asks for a sample/list without a specific count.
- Do not include markdown or commentary.
""".strip()


SQL_FIX_PROMPT = """
{schema}

This SQL query failed. Fix it while preserving the user's intent.

Original question:
{question}

SQL:
{sql}

Database/validator error:
{error}

Return only the corrected read-only PostgreSQL query.
""".strip()


SUMMARY_PROMPT = """
Answer the question in one short sentence using the SQL result.

Question:
{question}

Rows:
{rows}
""".strip()
