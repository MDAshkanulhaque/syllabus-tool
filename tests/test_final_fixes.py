import unittest
import requests
import re
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.book_engine.internet_books import (
    search_internet_books,
    format_internet_books_chat_response,
    verify_download_url,
    get_ia_downloadable_file,
    are_same_canonical_work,
    merge_canonical_work_records
)
from frontend.app import (
    is_internet_book_query,
    is_local_textbook_query,
    is_syllabus_query,
    is_book_search_query
)

class TestFinalBookFixes(unittest.TestCase):

    def test_01_canonical_work_merging(self):
        """Verify that provider duplicate records are merged into ONE primary work."""
        r1 = {
            "title": "Calculus Made Easy",
            "authors": ["Thompson, Silvanus Phillips, 1851-1916"],
            "publisher": "Internet Archive",
            "published_year": "1910",
            "source_provider": "Internet Archive",
            "reading_status": "Free Reading",
            "reading_url": "https://archive.org/details/calculusmadeeasy1910",
            "download_status": "Download Unavailable",
            "download_url": "",
            "download_format": "",
            "price": "Free",
            "relevance_score": 100.0
        }
        r2 = {
            "title": "Calculus made easy",
            "authors": ["Silvanus P. Thompson"],
            "publisher": "Macmillan",
            "published_year": "1914",
            "isbn": "9781234567890",
            "source_provider": "Google Books",
            "reading_status": "Preview Only",
            "reading_url": "https://books.google.com/test",
            "download_status": "Download Unavailable",
            "download_url": "",
            "download_format": "",
            "price": "Check official seller",
            "relevance_score": 95.0
        }
        r3 = {
            "title": "Calculus Made Easy",
            "authors": ["Silvanus Thompson"],
            "publisher": "Project Gutenberg",
            "published_year": "1914",
            "source_provider": "Project Gutenberg",
            "reading_status": "Free Reading",
            "reading_url": "https://www.gutenberg.org/ebooks/33283",
            "download_status": "Free Download",
            "download_url": "https://www.gutenberg.org/ebooks/33283.epub.images",
            "download_format": "EPUB",
            "price": "Free (Public Domain)",
            "relevance_score": 110.0
        }

        self.assertTrue(are_same_canonical_work(r1, r2))
        self.assertTrue(are_same_canonical_work(r2, r3))

        merged = merge_canonical_work_records([r1, r2, r3], {"clean_query": "Calculus Made Easy"})
        self.assertEqual(merged["title"], "Calculus Made Easy")
        self.assertIn("Silvanus P. Thompson", merged["authors"])
        self.assertIn("Google Books", merged["contributing_providers"])
        self.assertIn("Project Gutenberg", merged["contributing_providers"])
        self.assertEqual(merged["download_status"], "Free Download")
        self.assertEqual(merged["download_format"], "EPUB")
        self.assertEqual(merged["reading_status"], "Free Full Text")
        self.assertEqual(merged["isbn"], "9781234567890")

    def test_02_calculus_made_easy_live_primary_result(self):
        """Verify Calculus Made Easy returns ONE primary book with verified working links."""
        res = search_internet_books("Calculus Made Easy", limit=8, timeout=6.0)
        self.assertIsNotNone(res.get("primary_book"))
        p = res["primary_book"]
        self.assertIn("Calculus Made Easy", p["title"])
        authors_str = " ".join(p.get("authors", []))
        self.assertIn("Thompson", authors_str)

        # Check reading URL returns HTTP 200
        if p.get("reading_url"):
            try:
                r = requests.head(p["reading_url"], headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
                self.assertEqual(r.status_code, 200, f"Reading link {p['reading_url']} failed with status {r.status_code}")
            except requests.exceptions.RequestException:
                r = requests.get(p["reading_url"], headers={"User-Agent": "Mozilla/5.0"}, stream=True, allow_redirects=True, timeout=10)
                self.assertEqual(r.status_code, 200, f"Reading link {p['reading_url']} failed with status {r.status_code}")

        # Check download URL returns HTTP 200 if offered
        if p.get("download_status") == "Free Download" and p.get("download_url"):
            valid_dl = verify_download_url(p["download_url"], expected_format=p.get("download_format", "PDF"), timeout=5.0)
            self.assertTrue(valid_dl, f"Download link {p['download_url']} did not verify successfully!")

        # Verify chat formatting shows ONE primary card
        formatted = format_internet_books_chat_response(res)
        self.assertIn("### 🎯 Primary Book Result", formatted)
        # Verify it does not display duplicate cards like "#### 1." and "#### 2." with same title
        self.assertNotIn("#### 2. Calculus Made Easy", formatted)

    def test_03_jungle_book_live_primary_result(self):
        """Verify The Jungle Book returns ONE primary book by Rudyard Kipling with verified links."""
        res = search_internet_books("The Jungle Book", limit=8, timeout=6.0)
        self.assertIsNotNone(res.get("primary_book"))
        p = res["primary_book"]
        self.assertIn("Jungle Book", p["title"])
        authors_str = " ".join(p.get("authors", []))
        self.assertIn("kipling", authors_str.lower())

        if p.get("reading_url"):
            r = requests.head(p["reading_url"], headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=5)
            self.assertEqual(r.status_code, 200)

        formatted = format_internet_books_chat_response(res)
        self.assertIn("### 🎯 Primary Book Result", formatted)
        self.assertNotIn("#### 2. The Jungle Book", formatted)

    def test_04_ramana_academic_citation(self):
        """Verify Ramana academic citation returns ONE primary book with verified bibliographic details and genuine links."""
        query = 'Ramana. B.V., "Higher Engineering Mathematics", McGraw Hill Education Pvt. Ltd, New Delhi, 2018'
        res = search_internet_books(query, limit=8, timeout=6.0)
        self.assertIsNotNone(res.get("primary_book"))
        p = res["primary_book"]
        self.assertIn("Higher Engineering Mathematics", p["title"])
        authors_str = " ".join(p.get("authors", []))
        self.assertIn("ramana", authors_str.lower())

        # If download URL is present, verify that it is genuine HTTP 200 PDF
        if p.get("download_status") == "Free Download" and p.get("download_url"):
            self.assertTrue(verify_download_url(p["download_url"], expected_format="PDF", timeout=5.0))

        if p.get("reading_url"):
            r = requests.head(p["reading_url"], headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=5)
            self.assertEqual(r.status_code, 200)

        formatted = format_internet_books_chat_response(res)
        self.assertIn("### 🎯 Primary Book Result", formatted)

    def test_05_grewal_commercial_textbook(self):
        """Verify Grewal commercial textbook does not claim fake free download and shows genuine status."""
        query = "Grewal. B.S., and Grewal. J.S., Numerical methods in Engineering and Science, Khanna Publishers, 9th Edition, New Delhi, 2007"
        res = search_internet_books(query, limit=8, timeout=6.0)
        self.assertIsNotNone(res.get("primary_book"))
        p = res["primary_book"]
        self.assertIn("Numerical", p["title"])
        authors_str = " ".join(p.get("authors", []))
        self.assertIn("Grewal", authors_str)
        self.assertNotEqual(p.get("download_status"), "Free Download")

    def test_06_reject_404_url(self):
        """Verify that broken or 404 URLs are rejected by verify_download_url."""
        fake_url = "https://archive.org/download/nonexistent_fake_item_999999/fake.pdf"
        self.assertFalse(verify_download_url(fake_url, expected_format="PDF", timeout=3.0))

    def test_07_intent_routing_separation(self):
        """Verify strict 3-mode separation: Mode 1 (Internet), Mode 2 (Local Math), Mode 3 (Syllabus)."""
        # Mode 1: Book titles & citations
        self.assertTrue(is_internet_book_query("Calculus Made Easy", []))
        self.assertTrue(is_internet_book_query("The Jungle Book", []))
        self.assertTrue(is_internet_book_query('Ramana. B.V., "Higher Engineering Mathematics", McGraw Hill, 2018', []))
        self.assertTrue(is_internet_book_query("Grewal B.S. Numerical Methods", []))

        # Mode 2: Explicit local search and bare math concepts
        self.assertTrue(is_local_textbook_query("Find the eigenvalues section in my Kreyszig PDF"))
        self.assertFalse(is_internet_book_query("Find the eigenvalues section in my Kreyszig PDF", []))
        self.assertFalse(is_internet_book_query("matrix", []))

        # Mode 3: Syllabus administrative Q&A
        self.assertTrue(is_syllabus_query("What are the course outcomes for Semester 3?"))
        self.assertFalse(is_internet_book_query("What are the course outcomes for Semester 3?", []))


if __name__ == "__main__":
    unittest.main()
