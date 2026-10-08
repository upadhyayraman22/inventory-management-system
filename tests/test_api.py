"""End-to-end API tests for the inventory application."""

import tempfile
import unittest
from pathlib import Path

import app


class InventoryApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = app.DB_PATH
        self.original_threshold = app.app.config["LOW_STOCK_THRESHOLD"]
        app.DB_PATH = Path(self.temp_dir.name) / "inventory.db"
        app.app.config.update(TESTING=True)
        app.init_db()
        self.client = app.app.test_client()
        self.product = {
            "product_id": "SKU-001",
            "name": "Wireless Mouse",
            "category": "Accessories",
            "quantity": 10,
            "price": 599.50,
        }

    def tearDown(self):
        app.DB_PATH = self.original_db_path
        app.app.config["LOW_STOCK_THRESHOLD"] = self.original_threshold
        self.temp_dir.cleanup()

    def add_product(self):
        return self.client.post("/api/products", json=self.product)

    def test_frontend_page_contains_required_product_fields(self):
        response = self.client.get("/")
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for field_id in ("productId", "name", "category", "quantity", "price"):
            with self.subTest(field_id=field_id):
                self.assertIn(f'id="{field_id}"', page)
        self.assertNotIn("onclick=", page)
        for marker in ("lowStockFilter", "categoryFilter", "exportButton", "data-sort"):
            self.assertIn(marker, page)

    def test_add_and_list_product(self):
        response = self.add_product()
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(response.get_json()[0]["product_id"], "SKU-001")

    def test_duplicate_product_id_is_rejected(self):
        self.assertEqual(self.add_product().status_code, 201)
        response = self.client.post("/api/products", json={**self.product, "product_id": "sku-001"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "Product ID already exists.")

    def test_searches_by_id_name_and_category(self):
        self.add_product()
        for query in ("SKU-001", "mouse", "Accessories"):
            with self.subTest(query=query):
                response = self.client.get("/api/products", query_string={"search": query})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.get_json()), 1)

    def test_unavailable_search_returns_empty_list(self):
        response = self.client.get("/api/products", query_string={"search": "does-not-exist"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_update_product_quantity_and_price(self):
        self.add_product()
        response = self.client.put("/api/products/SKU-001", json={
            "name": "Wireless Mouse Pro",
            "category": "Accessories",
            "quantity": 3,
            "price": 749.00,
        })
        self.assertEqual(response.status_code, 200)

        product = self.client.get("/api/products/SKU-001").get_json()
        self.assertEqual(product["quantity"], 3)
        self.assertEqual(product["price"], 749.00)

    def test_negative_or_fractional_quantity_is_rejected(self):
        for quantity in (-1, 1.5):
            product = {**self.product, "product_id": f"SKU-{quantity}", "quantity": quantity}
            with self.subTest(quantity=quantity):
                response = self.client.post("/api/products", json=product)
                self.assertEqual(response.status_code, 400)

    def test_strict_types_lengths_and_error_messages(self):
        cases = [
            ({**self.product, "quantity": "10"}, "Quantity must be an integer."),
            ({**self.product, "quantity": True}, "Quantity must be an integer."),
            ({**self.product, "quantity": -1}, "Quantity must be zero or greater."),
            ({**self.product, "price": "5.00"}, "Price must be a number."),
            ({**self.product, "price": -1}, "Price must be zero or greater."),
            ({**self.product, "name": "x" * 121}, "Product name must be at most 120 characters."),
            ({**self.product, "category": []}, "Category must be a string."),
            ({**self.product, "product_id": ""}, "Product ID is required."),
        ]
        for product, error in cases:
            with self.subTest(error=error):
                response = self.client.post("/api/products", json=product)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.get_json()["error"], error)

    def test_apostrophe_values_are_stored_and_retrieved(self):
        product = {
            **self.product,
            "product_id": "O'REILLY-1",
            "name": "O'Reilly's Mouse",
            "category": "Owner's picks",
        }
        self.assertEqual(self.client.post("/api/products", json=product).status_code, 201)
        response = self.client.get("/api/products", query_string={"search": "O'Reilly"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["name"], "O'Reilly's Mouse")

    def test_negative_price_is_rejected(self):
        response = self.client.post("/api/products", json={**self.product, "price": -0.01})
        self.assertEqual(response.status_code, 400)

    def test_stock_cannot_be_reduced_below_zero(self):
        self.add_product()
        response = self.client.put("/api/products/SKU-001", json={
            "name": "Wireless Mouse",
            "category": "Accessories",
            "quantity": -1,
            "price": 599.50,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/products/SKU-001").get_json()["quantity"], 10)

    def test_delete_and_missing_product_responses(self):
        self.add_product()
        self.assertEqual(self.client.delete("/api/products/SKU-001").status_code, 200)
        self.assertEqual(self.client.get("/api/products/SKU-001").status_code, 404)
        self.assertEqual(self.client.delete("/api/products/not-found").status_code, 404)

    def test_low_stock_stats(self):
        self.product["quantity"] = 5
        self.add_product()
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["low_stock"], 1)
        self.assertEqual(response.get_json()["low_stock_threshold"], 5)

    def test_configured_low_stock_threshold_is_used_by_stats(self):
        app.app.config["LOW_STOCK_THRESHOLD"] = 3
        self.product["quantity"] = 4
        self.add_product()
        stats = self.client.get("/api/stats").get_json()
        self.assertEqual(stats["low_stock_threshold"], 3)
        self.assertEqual(stats["low_stock"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
