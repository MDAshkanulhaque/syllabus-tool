import os
import sys
import unittest

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.book_engine.internet_books import (
    clean_search_query,
    search_internet_books,
    format_internet_books_chat_response,
    is_safe_download_url
)
from frontend.app import is_internet_book_query, is_book_search_query, perform_book_search


class TestFullOnlineSystem(unittest.TestCase):
    def test_01_target_query_routing(self):
        """Verify routing for all required search examples."""
        online_queries = [
            "Algebra and Trigonometry",
            "Advanced Engineering Mathematics by Erwin Kreyszig",
            "Project Gutenberg",
            "story book",
            "novel",
            "Python programming books",
            "Computer Networks by Andrew Tanenbaum",
            "Data Science books",
            "free linear algebra books",
            "Find books about artificial intelligence",
        ]
        for q in online_queries:
            with self.subTest(query=q):
                is_net = is_internet_book_query(q)
                self.assertTrue(is_net, f"Query '{q}' was expected to be recognized as an internet book query!")
                print(f"[PASS] Online Route: '{q}' -> is_internet_book_query=True")

    def test_02_preserve_local_math_queries(self):
        """Verify ordinary mathematics topics route to local textbooks and do not trigger internet books initially."""
        math_queries = ["matrix", "fourier series", "laplace transform", "eigenvalues"]
        for q in math_queries:
            with self.subTest(query=q):
                self.assertFalse(is_internet_book_query(q), f"'{q}' should NOT trigger internet book query directly!")
                self.assertTrue(is_book_search_query(q, []), f"'{q}' MUST trigger local book search query!")
                resp = perform_book_search(q)
                self.assertIn("Book Search Results for", resp)
                print(f"[PASS] Local Math Search: '{q}' -> Returned local indexed sections.")

    def test_03_preserve_syllabus_queries(self):
        """Verify syllabus queries route to syllabus engine and never trigger book searches."""
        syllabus_queries = [
            "What is the syllabus of 2nd year?",
            "How many credits for DBMS?",
            "List all subjects in semester 4",
        ]
        for q in syllabus_queries:
            with self.subTest(query=q):
                self.assertFalse(is_internet_book_query(q))
                self.assertFalse(is_book_search_query(q, []))
                print(f"[PASS] Syllabus Route: '{q}' -> Routes to syllabus engine.")

    def test_04_live_online_search_all_required_queries(self):
        """Smoke test actual multi-provider search for the 7 primary user queries."""
        test_queries = [
            "Algebra and Trigonometry",
            "Advanced Engineering Mathematics by Erwin Kreyszig",
            "Project Gutenberg",
            "story book",
            "Python programming books",
            "free linear algebra books",
            "Computer Networks by Andrew Tanenbaum",
        ]
        for q in test_queries:
            with self.subTest(query=q):
                res = search_internet_books(q, limit=5, timeout=5)
                self.assertGreater(res.get("total_found", 0), 0, f"No books found for '{q}'!")
                top = res["results"][0]
                formatted = format_internet_books_chat_response(res)
                self.assertTrue("Internet Book Search Results" in formatted or "Curated Book Collection" in formatted)
                print(f"[PASS] Live Query: '{q}' -> Found {res['total_found']} books. Top: '{top.get('title')}' by {top.get('authors')}")


    def test_05_access_status_separation(self):
        """Verify independent reading vs download access and price validation."""
        sample_res = {
            "query": "Test Catalog",
            "total_found": 3,
            "providers_contacted": ["Open Library", "Internet Archive"],
            "providers_successful": ["Open Library", "Internet Archive"],
            "providers_failed": [],
            "results": [
                {
                    "title": "Public Domain Classic",
                    "authors": ["Author A"],
                    "published_year": "1905",
                    "reading_status": "Free Reading",
                    "reading_url": "https://archive.org/details/classic",
                    "download_status": "Free Download",
                    "download_url": "https://archive.org/download/classic/classic.pdf",
                    "download_format": "PDF",
                    "price": "Free",
                    "cover_url": "https://covers.openlibrary.org/b/id/123-M.jpg"
                },
                {
                    "title": "Restricted Modern Textbook",
                    "authors": ["Author B"],
                    "published_year": "2021",
                    "reading_status": "Preview Only",
                    "reading_url": "https://books.google.com/books?id=123",
                    "download_status": "Paid Download",
                    "download_url": "",
                    "price": "USD 49.99",
                    "purchase_url": "https://play.google.com/store/books/details?id=123"
                },
                {
                    "title": "Library Borrow Work",
                    "authors": ["Author C"],
                    "published_year": "2015",
                    "reading_status": "Borrow / Login Required",
                    "reading_url": "https://openlibrary.org/works/OL999W",
                    "download_status": "Download Unavailable",
                    "download_url": "",
                    "price": "Price unavailable — check official seller",
                    "purchase_url": "https://openlibrary.org/works/OL999W"
                }
            ]
        }
        formatted = format_internet_books_chat_response(sample_res)
        self.assertIn("🟢 **Free Reading**", formatted)
        self.assertIn("🟢 **Free Download**", formatted)
        self.assertIn("🟡 **Preview Only**", formatted)
        self.assertIn("💳 **Paid Download**", formatted)
        self.assertIn("USD 49.99", formatted)
        self.assertIn("🔒 **Borrow / Login Required**", formatted)
        self.assertIn("![Public Domain Classic Cover](https://covers.openlibrary.org/b/id/123-M.jpg)", formatted)
        print("[PASS] Access status separation, cover images, and verified pricing correctly formatted.")

    def test_06_ssrf_safety(self):
        """Verify URL validation blocks dangerous SSRF targets and permits legitimate domains."""
        self.assertTrue(is_safe_download_url("https://archive.org/download/item/file.pdf"))
        self.assertTrue(is_safe_download_url("https://ia800100.us.archive.org/file.pdf"))
        self.assertTrue(is_safe_download_url("https://www.gutenberg.org/files/1234/1234-pdf.pdf"))
        self.assertFalse(is_safe_download_url("http://192.168.1.1/secret.pdf"))
        self.assertFalse(is_safe_download_url("http://localhost:8080/data"))
        self.assertFalse(is_safe_download_url("file:///etc/passwd"))
        print("[PASS] SSRF protection validated.")


if __name__ == "__main__":
    unittest.main()
