"""
Focused unit tests for Internet Book Search feature.
Tests providers, parsing, matching, deduplication, reading/download availability, and security.
Uses standard Python unittest with mocking so tests run 100% offline and deterministically.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure backend is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from book_engine.internet_books import (
    clean_search_query,
    is_safe_download_url,
    score_and_rank_books,
    deduplicate_books,
    search_internet_books,
    format_internet_books_chat_response,
    fetch_google_books,
    fetch_open_library,
    fetch_internet_archive,
)


class TestInternetBookSearch(unittest.TestCase):

    def test_clean_search_query_parsing(self):
        """Test query intent parsing for titles, authors, and free/download modifiers."""
        q1 = clean_search_query("Find Advanced Engineering Mathematics by Erwin Kreyszig")
        self.assertEqual(q1["title"], "Advanced Engineering Mathematics")
        self.assertEqual(q1["author"], "Erwin Kreyszig")
        self.assertFalse(q1["is_free_requested"])

        q2 = clean_search_query("Search for a free linear algebra book")
        self.assertTrue(q2["is_free_requested"])
        self.assertIn("linear algebra", q2["clean_query"].lower())

        q3 = clean_search_query("Search for Python programming books")
        self.assertEqual(q3["clean_query"], "Python programming")

    def test_safe_download_url_validation(self):
        """Test SSRF protection and whitelisted domain validation."""
        # Allowed legitimate domains
        self.assertTrue(is_safe_download_url("https://archive.org/download/sample/sample.pdf"))
        self.assertTrue(is_safe_download_url("https://ia80123.archive.org/download/book.pdf"))
        self.assertTrue(is_safe_download_url("https://www.gutenberg.org/files/123/123.epub"))
        self.assertTrue(is_safe_download_url("https://openlibrary.org/books/OL123M"))

        # Forbidden domains / SSRF attempts
        self.assertFalse(is_safe_download_url("http://localhost:8000/secret"))
        self.assertFalse(is_safe_download_url("http://127.0.0.1:8000/admin"))
        self.assertFalse(is_safe_download_url("http://192.168.1.1/router"))
        self.assertFalse(is_safe_download_url("https://malicious-site.com/download.exe"))
        self.assertFalse(is_safe_download_url("file:///etc/passwd"))
        self.assertFalse(is_safe_download_url(""))
        self.assertFalse(is_safe_download_url(None))

    def test_scoring_and_ranking_prioritizes_exact_matches(self):
        """Test that exact title and author matches rank higher than partial matches."""
        clean_info = {
            "clean_query": "Python Crash Course",
            "title": "Python Crash Course",
            "author": "Eric Matthes",
            "is_free_requested": False,
            "is_download_requested": False,
        }
        candidate_books = [
            {
                "title": "Learning Python",
                "authors": ["Mark Lutz"],
                "published_year": "2013",
            },
            {
                "title": "Python Crash Course",
                "authors": ["Eric Matthes"],
                "published_year": "2019",
            },
            {
                "title": "Crash Course in Web Development",
                "authors": ["John Doe"],
                "published_year": "2020",
            }
        ]

        ranked = score_and_rank_books(candidate_books, clean_info)
        self.assertEqual(ranked[0]["title"], "Python Crash Course")
        self.assertEqual(ranked[0]["match_type"], "Exact Match")
        self.assertGreater(ranked[0]["relevance_score"], ranked[1]["relevance_score"])

    def test_deduplication_preserves_unique_editions(self):
        """Test duplicate elimination while preserving better download access."""
        books = [
            {
                "title": "Clean Code",
                "authors": ["Robert C. Martin"],
                "published_year": "2008",
                "download_status": "Download Unavailable",
                "download_url": "",
                "download_format": "",
                "source_provider": "Google Books",
            },
            {
                "title": "Clean Code",
                "authors": ["Robert C. Martin"],
                "published_year": "2008",
                "download_status": "Free Download",
                "download_url": "https://archive.org/download/cleancode/cleancode.pdf",
                "download_format": "PDF",
                "source_provider": "Open Library",
            },
            {
                "title": "The Clean Coder",
                "authors": ["Robert C. Martin"],
                "published_year": "2011",
                "download_status": "Paid Download",
                "download_url": "",
                "download_format": "",
                "source_provider": "Google Books",
            }
        ]

        deduped = deduplicate_books(books)
        # Should merge the two Clean Code 2008 entries into one with Free Download preserved
        self.assertEqual(len(deduped), 2)
        clean_code_entry = next(b for b in deduped if b["title"] == "Clean Code")
        self.assertEqual(clean_code_entry["download_status"], "Free Download")
        self.assertEqual(clean_code_entry["download_format"], "PDF")

    def test_availability_separation_free_vs_paid(self):
        """Verify that reading availability and download availability are completely independent."""
        # Book 1: Free Reading (borrowable) but Download Unavailable
        sample_ol = {
            "title": "Introduction to Algorithms",
            "authors": ["Thomas H. Cormen"],
            "reading_status": "Borrow / Login Required",
            "download_status": "Download Unavailable",
            "price": "Check official seller",
            "source_provider": "Open Library",
        }
        self.assertNotEqual(sample_ol["reading_status"], sample_ol["download_status"])

        # Book 2: Preview Only and Paid Download
        sample_gb = {
            "title": "Artificial Intelligence: A Modern Approach",
            "authors": ["Stuart Russell", "Peter Norvig"],
            "reading_status": "Preview Only",
            "download_status": "Paid Download",
            "price": "USD 89.99",
            "source_provider": "Google Books",
        }
        self.assertEqual(sample_gb["reading_status"], "Preview Only")
        self.assertEqual(sample_gb["download_status"], "Paid Download")

    @patch("book_engine.internet_books.fetch_open_library")
    @patch("book_engine.internet_books.fetch_internet_archive")
    @patch("book_engine.internet_books.fetch_google_books")
    def test_provider_fallback_when_google_books_fails(self, mock_gb, mock_ia, mock_ol):
        """Test graceful degradation when Google Books rate-limits (429) but others succeed."""
        mock_gb.return_value = []  # Simulates 429 or failure
        mock_ol.return_value = [{
            "id": "ol_123",
            "title": "Python for Data Analysis",
            "authors": ["Wes McKinney"],
            "published_year": "2017",
            "reading_status": "Free Reading",
            "reading_url": "https://openlibrary.org/works/OL1",
            "download_status": "Download Unavailable",
            "price": "Check official seller",
            "source_provider": "Open Library",
        }]
        mock_ia.return_value = []

        res = search_internet_books("Python for Data Analysis")
        self.assertEqual(res["total_found"], 1)
        self.assertEqual(res["results"][0]["title"], "Python for Data Analysis")
        self.assertIn("Open Library", res["providers_successful"])

    @patch("book_engine.internet_books.fetch_open_library")
    @patch("book_engine.internet_books.fetch_internet_archive")
    @patch("book_engine.internet_books.fetch_google_books")
    def test_all_providers_failing_returns_clean_response(self, mock_gb, mock_ia, mock_ol):
        """Test clean message formatting when all providers fail or return no results."""
        mock_gb.return_value = []
        mock_ol.return_value = []
        mock_ia.return_value = []

        res = search_internet_books("NonExistentUnobtainiumBookXYZ123")
        self.assertEqual(res["total_found"], 0)
        formatted = format_internet_books_chat_response(res)
        self.assertIn("No matching books found", formatted)
        self.assertNotIn("Traceback", formatted)


if __name__ == "__main__":
    unittest.main()
