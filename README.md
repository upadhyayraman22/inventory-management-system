# Stockroom Inventory Management System

A full-stack inventory application built with Flask, SQLite, and browser JavaScript.
It provides persistent product CRUD, live searching, filtering, sorting, low-stock
monitoring, and CSV export without page reloads.

## Technologies Used

- Python 3
- Flask
- SQLite
- HTML, CSS, and JavaScript
- Fetch API
- Node.js and npm (frontend syntax-check script)

## Features

- Add, list, search, update, and delete products through a JSON REST API.
- Product IDs are unique without regard to letter case (`sku-1` and `SKU-1` conflict).
- Strict server validation: JSON integer quantities, finite non-negative prices, and
  explicit limits for IDs (50), names (120), and categories (80) characters.
- Central low-stock setting, used by API statistics and every UI alert/status.
- Dynamic category and low-stock-only filters; sortable name, quantity, and price columns.
- CSV export of the products currently shown in the table.
- Toast notifications and inline form errors.
- Safe DOM event handling with `data-*` attributes—no inline `onclick` handlers, so
  product IDs and names containing apostrophes work correctly.

## Screenshots

### Dashboard and product catalogue

![Stockroom dashboard showing summary statistics, filters, product statuses, and actions](static/screenshots/dashboard.png)

### Inline form validation

![Add product dialog showing required-field validation errors](static/screenshots/validation-errors.png)

### Low-stock filter

![Product table filtered to show only a low-stock product](static/screenshots/low-stock-filter.png)

## Run

Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate            # macOS/Linux
# .venv\Scripts\activate             # Windows PowerShell
pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

SQLite data is created automatically at `instance/inventory.db`.

### Configure low stock

The threshold defaults to `5`. Set `LOW_STOCK_THRESHOLD` before starting Flask to
change it everywhere, for example:

```bash
LOW_STOCK_THRESHOLD=10 python app.py
```

On Windows PowerShell:

```powershell
$env:LOW_STOCK_THRESHOLD=10; python app.py
```

## Verify

Run the API and validation regression suite:

```bash
python -m unittest discover -s tests -v
```

Run the Node.js frontend syntax check:

```bash
npm test
```

The tests cover CRUD, all search fields, unavailable products, case-insensitive
duplicate IDs, apostrophes, strict validation/error messages, and threshold-driven
low-stock statistics.
