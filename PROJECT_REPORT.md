# INVENTORY / PRODUCT MANAGEMENT SYSTEM

## 1. Title
Inventory / Product Management System

## 2. Aim
To design and develop an Inventory Management System web application that enables users to add, search, update stock, and delete product records using HTML, CSS, JavaScript, Python Flask and SQLite.

## 3. Objectives
1. Create a frontend for Product ID, Name, Category, Quantity and Price.
2. Implement Flask REST APIs for adding, viewing, searching, updating and deleting products.
3. Store product and stock data in SQLite.
4. Exchange JSON data between frontend and backend using HTTP requests.
5. Validate non-negative quantity and price values.
6. Display low-stock alerts dynamically using JavaScript Fetch API.
7. Test invalid and edge-case operations.

## 4. Problem Statement
Manual inventory records are difficult to search, update and maintain. This project provides a browser-based system for maintaining product information and stock levels with persistent database storage.

## 5. System Architecture
Browser (HTML/CSS/JavaScript)
        |
        | HTTP + JSON / Fetch API
        v
Python Flask REST API
        |
        | SQL
        v
SQLite Database

## 6. Functional Modules
- Product registration
- Product listing
- Product search
- Product update
- Product deletion
- Low-stock monitoring
- Dashboard statistics
- Input validation

## 7. Database Schema

Table: products

| Field | Type | Constraint |
|---|---|---|
| id | INTEGER | Primary Key |
| product_id | TEXT | Unique, Not Null |
| name | TEXT | Not Null |
| category | TEXT | Not Null |
| quantity | INTEGER | >= 0 |
| price | REAL | >= 0 |
| created_at | TEXT | Not Null |

## 8. REST API

GET /api/products
GET /api/products/<product_id>
POST /api/products
PUT /api/products/<product_id>
DELETE /api/products/<product_id>
GET /api/stats

## 9. Validation
- Required fields cannot be empty.
- Product ID must be unique.
- Quantity cannot be negative.
- Price cannot be negative.
- Non-existent products return an error response.

## 10. Testing

| Test | Expected Result |
|---|---|
| Add valid product | Product created |
| Duplicate Product ID | Error |
| Negative quantity | Error |
| Negative price | Error |
| Search existing product | Matching result |
| Search unavailable product | No result |
| Update existing product | Product updated |
| Delete existing product | Product removed |
| Delete unavailable product | Error |
| Quantity <= 5 | Low Stock status |

Automated verification is provided in `tests/test_api.py`. Run it with:
```bash
python -m unittest discover -s tests -v
```

The suite verifies CRUD behaviour, searching by ID/name/category, unavailable
searches, duplicate IDs, low-stock statistics, and invalid negative or fractional
stock quantities and negative prices.

## 11. Conclusion
The Inventory Management System demonstrates full-stack web development by integrating an HTML/CSS/JavaScript frontend, Flask REST backend and SQLite database. It implements CRUD operations, validation, dynamic Fetch API communication and low-stock monitoring.

## 12. Future Scope
Possible extensions include authentication, multiple user roles, supplier management, purchase/sales transactions, export to CSV/PDF, charts and cloud deployment.
