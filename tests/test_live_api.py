import os
import sys
import unittest

# Ensure backend is on sys.path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app


class TestFastAPIBookEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_search_queries(self):
        queries = [
            "Search for Python programming books",
            "Find Advanced Engineering Mathematics by Erwin Kreyszig",
            "Search for a free linear algebra book",
            "Find books about artificial intelligence",
            "Search for Harry Potter",
            "Find the latest available edition of a database systems textbook",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.client.get("/books/search", params={"q": q})
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertIn("results", data)
                self.assertIn("cleaned_query", data)
                self.assertGreater(len(data["results"]), 0, f"Expected at least 1 result for '{q}'")
                top = data["results"][0]
                self.assertIn("title", top)
                self.assertIn("reading_status", top)
                self.assertIn("download_status", top)
                print(f"[OK] Endpoint Query: '{q}' -> Found {len(data['results'])} books. Top: '{top.get('title')}'")

    def test_safe_download_redirect(self):
        target = "https://archive.org/download/sample_id/sample.pdf"
        res = self.client.get("/books/download", params={"url": target}, follow_redirects=False)
        self.assertEqual(res.status_code, 307)
        self.assertEqual(res.headers.get("location"), target)
        print("[OK] Safe download redirect verified (HTTP 307)")

    def test_ssrf_protection(self):
        malicious_urls = [
            "http://192.168.1.1/secret.pdf",
            "http://localhost:8080/admin",
            "http://169.254.169.254/latest/meta-data",
            "ftp://example.com/file.txt",
            "javascript:alert(1)",
        ]
        for u in malicious_urls:
            with self.subTest(url=u):
                res = self.client.get("/books/download", params={"url": u}, follow_redirects=False)
                self.assertEqual(res.status_code, 400)
        print("[OK] SSRF protection blocked unauthorized targets (HTTP 400)")

    def test_empty_query(self):
        res = self.client.get("/books/search", params={"q": "   "})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["results"], [])
        print("[OK] Empty query gracefully returned empty result list")


if __name__ == "__main__":
    unittest.main()
