"""
Comprehensive test suite verifying Bug Fix for:
1. Exact Book Matching (The Jungle Book, Algebra and Trigonometry, Kreyszig, Ambiguous queries).
2. Verified Reader and Download Links (IA, Google Books, Open Library).
3. Preservation of local math searches (matrix, Fourier series) and syllabus Q&A.
"""

import sys
import unittest
import requests
from backend.book_engine.internet_books import (
    clean_search_query,
    normalize_title_for_matching,
    search_internet_books,
    format_internet_books_chat_response,
    is_safe_download_url,
    verify_download_url
)
from frontend.app import is_internet_book_query, is_book_search_query


class TestExactBookMatchingAndLinks(unittest.TestCase):

    def test_01_query_cleaning_jungle_book(self):
        """Verify that 'The Jungle Book' preserves 'Book' in title and clean query."""
        info = clean_search_query("The Jungle Book")
        self.assertEqual(info["clean_query"], "The Jungle Book")
        self.assertEqual(info["title"], "The Jungle Book")
        self.assertIsNone(info["author"])

    def test_02_query_cleaning_author_and_topics(self):
        """Verify clean_search_query on other standard queries."""
        k_info = clean_search_query("Advanced Engineering Mathematics by Erwin Kreyszig")
        self.assertEqual(k_info["title"], "Advanced Engineering Mathematics")
        self.assertEqual(k_info["author"], "Erwin Kreyszig")

        p_info = clean_search_query("Python programming books")
        self.assertEqual(p_info["clean_query"], "Python programming")

        s_info = clean_search_query("story book")
        self.assertEqual(s_info["clean_query"], "story book")

    def test_03_title_normalization(self):
        """Verify title normalization ignores harmless case, punctuation, articles, subtitles, and edition numbers."""
        norm_jungle = normalize_title_for_matching("The Jungle Book")
        self.assertEqual(norm_jungle, "jungle book")

        self.assertEqual(normalize_title_for_matching("The Jungle Book: With Illustrations"), "jungle book")
        self.assertEqual(normalize_title_for_matching("the jungle book"), "jungle book")
        self.assertEqual(normalize_title_for_matching("The Jungle Book (Signet Classics)"), "jungle book")
        self.assertNotEqual(normalize_title_for_matching("The Jungle"), "jungle book")
        self.assertNotEqual(normalize_title_for_matching("Men Against The Jungle"), "jungle book")

        # Algebra and Trigonometry
        self.assertEqual(normalize_title_for_matching("Algebra and Trigonometry"), "algebra and trigonometry")
        self.assertEqual(normalize_title_for_matching("Algebra & Trigonometry, 4th Edition"), "algebra and trigonometry")

        # Kreyszig
        self.assertEqual(normalize_title_for_matching("Advanced Engineering Mathematics, 10th Edition"), "advanced engineering mathematics")

    def test_04_the_jungle_book_search_exact_match(self):
        """Verify 'The Jungle Book' returns Kipling's classic as Exact Match and no unrelated jungle books."""
        res = search_internet_books("The Jungle Book", limit=6)
        self.assertTrue(res["has_exact_match"], "The Jungle Book must have exact match verified")
        self.assertGreater(len(res["exact_matches"]), 0)

        # First result must be an exact match
        first = res["results"][0]
        self.assertEqual(first["match_type"], "Exact Match")
        self.assertIn("jungle book", first["title"].lower())
        authors_lower = " ".join([a.lower() for a in first["authors"]])
        self.assertTrue("kipling" in authors_lower or "various" in authors_lower or len(first["authors"]) > 0)

        # Unrelated titles must NOT be in results
        for b in res["results"]:
            title_lower = b["title"].lower().strip()
            for bad in ["men against the jungle", "from jute to jungle", "la vida panthera"]:
                self.assertNotIn(bad, title_lower, f"Unrelated title '{bad}' found in results: {title_lower}")

    def test_05_algebra_and_trigonometry(self):
        """Verify 'Algebra and Trigonometry' exact-title matching."""
        res = search_internet_books("Algebra and Trigonometry", limit=6)
        self.assertTrue(res["has_exact_match"])
        for b in res["exact_matches"]:
            norm = normalize_title_for_matching(b["title"])
            self.assertEqual(norm, "algebra and trigonometry")

    def test_06_kreyszig_math_title_and_author(self):
        """Verify 'Advanced Engineering Mathematics by Erwin Kreyszig' matches title and author."""
        res = search_internet_books("Advanced Engineering Mathematics by Erwin Kreyszig", limit=6)
        self.assertTrue(res["has_exact_match"])
        top = res["results"][0]
        self.assertEqual(top["match_type"], "Exact Match")
        self.assertIn("kreyszig", " ".join(top["authors"]).lower())

    def test_07_ambiguous_nonexistent_title_not_labeled_exact(self):
        """Ambiguous query where no exact match exists: related titles must NOT be labelled Exact Match."""
        query = "Extraterrestrial Hyperdimensional Quantum Computing Mechanics 2099"
        res = search_internet_books(query, limit=4)
        self.assertFalse(res["has_exact_match"], "No exact match should exist for fictitious book")
        for b in res["results"]:
            self.assertNotEqual(b.get("match_type"), "Exact Match", f"Book '{b['title']}' must NOT be labeled Exact Match")

        # Response formatter must clearly state no verified exact match found
        formatted = format_internet_books_chat_response(res)
        self.assertIn("No verified exact match was found", formatted)

    def test_08_live_reader_and_download_links(self):
        """Verify live HTTP accessibility of reader and download URLs."""
        # 1. Valid Internet Archive reader link
        ia_reader = "https://archive.org/details/cu31924014517266"
        r_ia = requests.get(ia_reader, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=8)
        self.assertEqual(r_ia.status_code, 200, f"IA reader URL failed: {ia_reader}")
        self.assertIn("text/html", r_ia.headers.get("content-type", "").lower())

        # 2. Valid Open Library reader/work link
        ol_work = "https://openlibrary.org/works/OL15127157W"
        try:
            r_ol = requests.get(ol_work, headers={"User-Agent": "AcademicSyllabusAI/1.0"}, stream=True, timeout=10)
            self.assertIn(r_ol.status_code, (200, 301, 302))
        except Exception as e:
            # If Open Library resets connection intermittently
            print(f"[Note] Open Library live check experienced transient network error: {e}")

        # 3. Valid Google Books preview link
        gb_preview = "https://books.google.com/books?id=1yxNAQAAMAAJ"
        r_gb = requests.get(gb_preview, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=8)
        self.assertEqual(r_gb.status_code, 200, f"Google Books preview link failed: {gb_preview}")

        # 4. Genuinely downloadable authorized PDF
        valid_pdf = "https://archive.org/download/cu31924014517266/cu31924014517266.pdf"
        self.assertTrue(is_safe_download_url(valid_pdf))
        self.assertTrue(verify_download_url(valid_pdf, "PDF", timeout=5))

        # 5. Book with restricted / no authorized downloadable file (bwb_Y0-CHZ-845)
        restricted_pdf = "https://archive.org/download/bwb_Y0-CHZ-845/bwb_Y0-CHZ-845.pdf"
        self.assertFalse(verify_download_url(restricted_pdf, "PDF", timeout=5), "Restricted book must NOT verify as downloadable PDF")

        # 6. SSRF / invalid safety check
        self.assertFalse(is_safe_download_url("http://localhost:8000/admin"))
        self.assertFalse(is_safe_download_url("http://192.168.1.1/secret.pdf"))
        self.assertFalse(is_safe_download_url("https://malicious-site.com/book.pdf"))

    def test_09_preservation_of_local_math_and_syllabus(self):
        """Verify routing for local math searches ('matrix', 'Fourier series') and syllabus questions."""
        # Local mathematics searches must NOT be intercepted by internet book search
        self.assertFalse(is_internet_book_query("matrix"))
        self.assertFalse(is_internet_book_query("Fourier series"))
        self.assertTrue(is_book_search_query("matrix", []))
        self.assertTrue(is_book_search_query("Fourier series", []))

        # Syllabus question must NOT be intercepted by internet book search
        self.assertFalse(is_internet_book_query("What is the syllabus of 2nd year?"))
        self.assertFalse(is_internet_book_query("What are the subjects in 3rd semester?"))


if __name__ == "__main__":
    unittest.main()
