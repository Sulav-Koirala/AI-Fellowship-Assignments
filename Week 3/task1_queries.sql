-- 1. Question: List all products
SELECT * FROM products;

-- 2. Question: Get all customers
SELECT * FROM customers;

-- 3. Question: Show all orders
SELECT * FROM orders;

-- 4. Question: List all employees
SELECT * FROM employees;

-- 5. Question: Get all offices
SELECT * FROM offices;

-- 6. Question: Show all product lines
SELECT * FROM productlines;

-- 7. Question: List all payments
SELECT * FROM payments;

-- 8. Question: Get product names and prices
SELECT productName, buyPrice FROM products;

-- 9. Question: Get customer names and cities
SELECT customerName, city FROM customers;

-- 10. Question: List employee first and last names
SELECT firstName, lastName FROM employees;

-- 11. Question: Get all order dates
SELECT orderDate FROM orders;

-- 12. Question: Show product vendor list
SELECT DISTINCT productVendor FROM products;

-- 13. Question: Get all product codes
SELECT productCode FROM products;

-- 14. Question: List all countries from offices
SELECT DISTINCT country FROM offices;

-- 15. Question: Show all order statuses
SELECT DISTINCT status FROM orders;

-- 16. Question: Get all payment amounts
SELECT amount FROM payments;

-- 17. Question: List all job titles
SELECT DISTINCT jobTitle FROM employees;

-- 18. Question: Get customer phone numbers
SELECT customerName, phone FROM customers;

-- 19. Question: Show product MSRP values
SELECT productName, MSRP FROM products;

-- 20. Question: List order numbers
SELECT orderNumber FROM orders;

-- 21. Question: Get orders with customer names
SELECT o.orderNumber, c.customerName FROM orders o JOIN customers c ON o.customerNumber = c.customerNumber;

-- 22. Question: Get employees with office city
SELECT e.firstName, e.lastName, o.city FROM employees e JOIN offices o ON e.officeCode = o.officeCode;

-- 23. Question: Get payments with customer names
SELECT p.checkNumber, p.amount, c.customerName FROM payments p JOIN customers c ON p.customerNumber = c.customerNumber;

-- 24. Question: Get order details with product names
SELECT od.orderNumber, p.productName, od.quantityOrdered, od.priceEach FROM orderdetails od JOIN products p ON od.productCode = p.productCode;

-- 25. Question: Get products with product line description
SELECT p.productName, pl.textDescription FROM products p JOIN productlines pl ON p.productLine = pl.productLine;

-- 26. Question: Get customers with sales rep names
SELECT c.customerName, e.firstName, e.lastName FROM customers c LEFT JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber;

-- 27. Question: Get orders with customer city
SELECT o.orderNumber, c.city FROM orders o JOIN customers c ON o.customerNumber = c.customerNumber;

-- 28. Question: Get employees and their manager
SELECT e.firstName AS EmployeeFirst, e.lastName AS EmployeeLast, m.firstName AS ManagerFirst, m.lastName AS ManagerLast FROM employees e LEFT JOIN employees m ON e.reportsTo = m.employeeNumber;

-- 29. Question: Get orderdetails with product vendor
SELECT od.orderNumber, od.productCode, p.productVendor FROM orderdetails od JOIN products p ON od.productCode = p.productCode;

-- 30. Question: Get payments with customer country
SELECT p.checkNumber, p.amount, c.country FROM payments p JOIN customers c ON p.customerNumber = c.customerNumber;

-- 31. Question: Count customers per country
SELECT country, COUNT(*) AS customer_count FROM customers GROUP BY country;

-- 32. Question: Total payments per customer
SELECT customerNumber, SUM(amount) AS total_payments FROM payments GROUP BY customerNumber;

-- 33. Question: Number of orders per status
SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status;

-- 34. Question: Products per product line
SELECT productLine, COUNT(*) AS product_count FROM products GROUP BY productLine;

-- 35. Question: Employees per office
SELECT officeCode, COUNT(*) AS employee_count FROM employees GROUP BY officeCode;

-- 36. Question: Total stock per product vendor
SELECT productVendor, SUM(quantityInStock) AS total_stock FROM products GROUP BY productVendor;

-- 37. Question: Average buy price per product line
SELECT productLine, AVG(buyPrice) AS avg_buy_price FROM products GROUP BY productLine;

-- 38. Question: Orders per customer
SELECT customerNumber, COUNT(*) AS order_count FROM orders GROUP BY customerNumber;

-- 39. Question: Max MSRP per product line
SELECT productLine, MAX(MSRP) AS max_msrp FROM products GROUP BY productLine;

-- 40. Question: Min buy price per vendor
SELECT productVendor, MIN(buyPrice) AS min_buy_price FROM products GROUP BY productVendor;

-- 41. Question: Total number of customers
SELECT COUNT(*) AS total_customers FROM customers;

-- 42. Question: Total number of products
SELECT COUNT(*) AS total_products FROM products;

-- 43. Question: Total revenue from payments
SELECT SUM(amount) AS total_revenue FROM payments;

-- 44. Question: Average product price
SELECT AVG(buyPrice) AS avg_price FROM products;

-- 45. Question: Max payment amount
SELECT MAX(amount) AS max_payment FROM payments;

-- 46. Question: Min payment amount
SELECT MIN(amount) AS min_payment FROM payments;

-- 47. Question: Count total orders
SELECT COUNT(*) AS total_orders FROM orders;

-- 48. Question: Total quantity in stock
SELECT SUM(quantityInStock) AS total_stock FROM products;

-- 49. Question: Average MSRP
SELECT AVG(MSRP) AS avg_msrp FROM products;

-- 50. Question: Number of employees
SELECT COUNT(*) AS total_employees FROM employees;