"""
Comprehensive Test Suite for Universal Online Book Search System
Validates multi-provider integration (Google Books, Open Library, Internet Archive, Project Gutenberg),
exact book matching, category recommendations, live pricing, verified reading and download links,
error handling, SSRF security, and preservation of local mathematics and syllabus QA functionality.
"""

import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from backend.book_engine.internet_books import (
    clean_search_query,
    normalize_title_for_matching,
    score_and_rank_books,
    search_internet_books,
    format_internet_books_chat_response,
    is_safe_download_url,
    verify_download_url,
    clean_author_name,
    fetch_project_gutenberg,
    fetch_google_books,
    fetch_open_library,
    fetch_internet_archive,
)
from frontend.app import (
    is_internet_book_query,
    is_book_search_query,
    perform_book_search,
    is_local_textbook_query,
    is_syllabus_query
)


class TestUniversalBookSearch(unittest.TestCase):

    def test_01_query_intent_and_category_detection(self):
        """Verify distinguishing specific book titles from broad category/genre queries."""
        # 1. Specific title / author queries
        q_jungle = clean_search_query("The Jungle Book")
        self.assertFalse(q_jungle["is_category_search"])
        self.assertEqual(q_jungle["title"], "The Jungle Book")

        q_kreyszig = clean_search_query("Advanced Engineering Mathematics by Erwin Kreyszig")
        self.assertFalse(q_kreyszig["is_category_search"])
        self.assertEqual(q_kreyszig["title"], "Advanced Engineering Mathematics")
        self.assertEqual(q_kreyszig["author"], "Erwin Kreyszig")

        # 2. Broad category / genre queries
        q_prog = clean_search_query("Python programming books")
        self.assertTrue(q_prog["is_category_search"])

        q_stories = clean_search_query("story books")
        self.assertTrue(q_stories["is_category_search"])

        q_novels = clean_search_query("novels")
        self.assertTrue(q_novels["is_category_search"])

        q_children = clean_search_query("children's books")
        self.assertTrue(q_children["is_category_search"])

        q_med = clean_search_query("medical textbooks")
        self.assertTrue(q_med["is_category_search"])

    def test_02_exact_book_matching_priority(self):
        """Verify that exact title and author matches are scored higher and labeled Exact Match."""
        clean_info = clean_search_query("The Jungle Book by Rudyard Kipling")
        candidate_books = [
            {
                "title": "the jungle",
                "authors": ["Robert B. Downs"],
                "publisher": "Signet",
                "published_year": "1960",
                "reading_status": "Reading Unavailable",
                "download_status": "Download Unavailable"
            },
            {
                "title": "The Jungle Book",
                "authors": ["Rudyard Kipling"],
                "publisher": "Macmillan",
                "published_year": "1894",
                "reading_status": "Free Reading",
                "download_status": "Free Download"
            },
            {
                "title": "Men Against The Jungle",
                "authors": ["Ritchie Calder"],
                "publisher": "Allen & Unwin",
                "published_year": "1954",
                "reading_status": "Reading Unavailable",
                "download_status": "Download Unavailable"
            }
        ]
        ranked = score_and_rank_books(candidate_books, clean_info)
        top = ranked[0]
        self.assertEqual(top["title"], "The Jungle Book")
        self.assertEqual(top["match_type"], "Exact Match")
        self.assertGreater(top["relevance_score"], 90.0)
        self.assertNotEqual(ranked[1]["match_type"], "Exact Match")

    def test_03_category_search_collection_labeling(self):
        """Verify that broad category searches produce collection recommendations rather than false exact matches."""
        clean_info = clean_search_query("Python programming books")
        candidate_books = [
            {
                "title": "Python Crash Course",
                "authors": ["Eric Matthes"],
                "publisher": "No Starch Press",
                "description": "A hands-on introduction to Python programming",
                "published_year": "2019",
                "reading_status": "Borrow / Login Required",
                "download_status": "Download Unavailable"
            },
            {
                "title": "Automate the Boring Stuff with Python",
                "authors": ["Al Sweigart"],
                "publisher": "No Starch Press",
                "description": "Practical programming for total beginners",
                "published_year": "2015",
                "reading_status": "Free Reading",
                "download_status": "Free Download"
            }
        ]
        ranked = score_and_rank_books(candidate_books, clean_info)
        for b in ranked:
            self.assertEqual(b["match_type"], "Collection Pick")

        # Verify chat formatting for category search
        formatted = format_internet_books_chat_response({
            "query": "Python programming books",
            "clean_info": clean_info,
            "results": ranked,
            "has_exact_match": False
        })
        self.assertIn("Curated Book Collection", formatted)
        self.assertIn("[Collection Pick]", formatted)
        self.assertNotIn("No verified exact match was found", formatted)

    def test_04_project_gutenberg_provider(self):
        """Verify Project Gutenberg provider returns public domain literature."""
        info = clean_search_query("Pride and Prejudice by Jane Austen")
        books = fetch_project_gutenberg(info, timeout=4)
        self.assertIsInstance(books, list)
        if books:
            b = books[0]
            self.assertIn(b["reading_status"], ("Free Reading", "Free Full Text"))
            self.assertTrue(any(dom in b["reading_url"] for dom in ("gutenberg.org", "archive.org")))
            self.assertIn("Free", b["price"])

    def test_05_verified_reading_and_download_separation(self):
        """Verify reading permissions and download permissions are tracked separately."""
        # Borrow-only book
        borrow_res = {
            "query": "Recent Commercial Novel",
            "clean_info": clean_search_query("Recent Commercial Novel"),
            "results": [{
                "title": "Recent Commercial Novel",
                "authors": ["Famous Author"],
                "publisher": "Penguin",
                "published_year": "2022",
                "isbn": "9781234567890",
                "source_provider": "Internet Archive",
                "match_type": "Exact Match",
                "reading_status": "Borrow / Login Required",
                "reading_notes": "Borrowable digital copy (Free library account required)",
                "reading_url": "https://archive.org/details/test_borrow",
                "download_status": "Download Unavailable",
                "download_url": "",
                "price": "Free with borrowing account",
                "purchase_url": "https://archive.org/details/test_borrow"
            }],
            "exact_matches": [{
                "title": "Recent Commercial Novel",
                "authors": ["Famous Author"],
                "match_type": "Exact Match"
            }],
            "has_exact_match": True
        }
        fmt = format_internet_books_chat_response(borrow_res)
        self.assertIn("Borrow / Login Required", fmt)
        self.assertIn("Download Unavailable", fmt)
        self.assertNotIn("Free Download (PDF)", fmt)
        self.assertIn("Borrow / Read Online", fmt)

    def test_06_commercial_pricing_and_purchase_links(self):
        """Verify commercial books display price when verified and link to official store."""
        paid_res = {
            "query": "Paid Ebook Query",
            "clean_info": clean_search_query("Paid Ebook Query"),
            "results": [{
                "title": "Advanced Engineering Textbook",
                "authors": ["Author"],
                "publisher": "Academic Press",
                "published_year": "2023",
                "isbn": "9780000000000",
                "source_provider": "Google Books",
                "match_type": "Exact Match",
                "reading_status": "Preview Only",
                "reading_notes": "Google Books sample pages",
                "reading_url": "https://books.google.com/books?id=test",
                "download_status": "Paid Download",
                "download_url": "",
                "price": "USD 49.99",
                "purchase_url": "https://play.google.com/store/books/details?id=test"
            }],
            "exact_matches": [{
                "title": "Advanced Engineering Textbook",
                "match_type": "Exact Match"
            }],
            "has_exact_match": True
        }
        fmt = format_internet_books_chat_response(paid_res)
        self.assertIn("USD 49.99", fmt)
        self.assertIn("Paid Download", fmt)
        self.assertIn("Buy / Official Store", fmt)

    def test_07_download_security_ssrf_validation(self):
        """Verify that download endpoints strictly reject SSRF attempts and non-whitelisted domains."""
        self.assertTrue(is_safe_download_url("https://archive.org/download/item/book.pdf"))
        self.assertTrue(is_safe_download_url("https://books.google.com/books/download/book.pdf?id=123"))
        self.assertTrue(is_safe_download_url("https://www.gutenberg.org/files/11/11-pdf.pdf"))

        # Reject private / internal network addresses
        self.assertFalse(is_safe_download_url("http://localhost:8000/secret.pdf"))
        self.assertFalse(is_safe_download_url("http://127.0.0.1:8000/env"))
        self.assertFalse(is_safe_download_url("http://192.168.1.1/admin.pdf"))
        self.assertFalse(is_safe_download_url("http://10.0.0.1/private"))
        self.assertFalse(is_safe_download_url("http://169.254.169.254/latest/meta-data/"))
        # Reject malicious domains
        self.assertFalse(is_safe_download_url("https://evil-hacker-site.com/malware.exe"))

    def test_08_intelligent_routing_behavior(self):
        """Verify query routing accurately sends queries to internet books, local textbooks, or syllabus QA."""
        # 1. Online book queries
        self.assertTrue(is_internet_book_query("The Jungle Book", []))
        self.assertTrue(is_internet_book_query("NCERT Mathematics class 10", []))
        self.assertTrue(is_internet_book_query("Python programming books", []))
        self.assertTrue(is_internet_book_query("Advanced Engineering Mathematics by Erwin Kreyszig", []))
        self.assertTrue(is_internet_book_query("free download calculus textbook", []))
        self.assertTrue(is_internet_book_query("Calculus Made Easy", []))

        # 2. Local textbook queries (ordinary mathematics topics without internet book modifiers)
        self.assertTrue(is_book_search_query("matrix", []))
        self.assertTrue(is_book_search_query("Fourier series", []))
        self.assertFalse(is_internet_book_query("matrix", []))

        # 3. Explicit local textbook search queries
        self.assertTrue(is_local_textbook_query("Find the eigenvalues section in my Kreyszig PDF"))
        self.assertTrue(is_local_textbook_query("Explain the eigenvalues section from my uploaded textbook"))
        self.assertFalse(is_internet_book_query("Find the eigenvalues section in my Kreyszig PDF", []))

        # 4. Syllabus queries (must not route to internet books)
        self.assertFalse(is_internet_book_query("What is the attendance criteria for 2nd year?", []))
        self.assertFalse(is_internet_book_query("What are the course outcomes for Semester 3?", []))
        self.assertTrue(is_syllabus_query("What are the course outcomes for Semester 3?"))

    def test_09_multi_genre_live_integration(self):
        """Smoke test live search across distinct domains."""
        res1 = search_internet_books("The Jungle Book", limit=3, timeout=5)
        self.assertIsInstance(res1, dict)
        self.assertGreater(res1["total_found"], 0)
        self.assertTrue(res1["has_exact_match"])

        res2 = search_internet_books("story books", limit=3, timeout=5)
        self.assertIsInstance(res2, dict)
        self.assertGreater(res2["total_found"], 0)

    def test_10_syllabus_citation_query_ramana(self):
        """Specifically verify the syllabus citation for B.V. Ramana Higher Engineering Mathematics."""
        query = 'Ramana. B.V., "Higher Engineering Mathematics", McGraw Hill Education Pvt. Ltd, New Delhi, 2018'
        self.assertTrue(is_internet_book_query(query, []))

        info = clean_search_query(query)
        self.assertEqual(info["title"], "Higher Engineering Mathematics")
        self.assertEqual(info["author"], "Ramana. B.V")
        self.assertEqual(info["publisher"], "McGraw Hill")
        self.assertEqual(info["published_year"], "2018")
        self.assertIn("Ramana", info["surnames"])

        res = search_internet_books(query, limit=3, timeout=6)
        self.assertGreater(res["total_found"], 0)
        top = res["results"][0]
        self.assertIn("Higher Engineering Mathematics", top["title"])
        self.assertEqual(top["match_type"], "Exact Match")

    def test_11_citation_query_grewal(self):
        """Specifically verify the syllabus citation for B.S. Grewal Numerical Methods."""
        query = 'Grewal. B.S., and Grewal. J.S., Numerical methods in Engineering and Science, Khanna Publishers, 9th Edition, New Delhi, 2007'
        # 1. Routing check
        self.assertTrue(is_internet_book_query(query, []))

        # 2. Citation parsing check
        info = clean_search_query(query)
        self.assertEqual(info["title"], "Numerical methods in Engineering and Science")
        self.assertEqual(info["publisher"], "Khanna")
        self.assertEqual(info["published_year"], "2007")
        self.assertIn("Grewal", info["surnames"])

        # 3. Live search check
        res = search_internet_books(query, limit=3, timeout=6)
        self.assertGreater(res["total_found"], 0)
        top = res["results"][0]
        self.assertIn("Numerical Methods in Engineering and Science", top["title"])
        self.assertEqual(top["match_type"], "Exact Match")

    def test_12_calculus_made_easy_routing_and_search(self):
        """Verify Calculus Made Easy routes to internet books and finds Silvanus Thompson's book."""
        query = "Calculus Made Easy"
        # 1. Must route to Internet Book Search, NOT local textbook chapters
        self.assertTrue(is_internet_book_query(query, []))
        self.assertFalse(is_local_textbook_query(query))

        # 2. Live search returns actual book by Silvanus Thompson
        res = search_internet_books(query, limit=3, timeout=6)
        self.assertGreater(res["total_found"], 0)
        top = res["results"][0]
        self.assertEqual(top["title"], "Calculus Made Easy")
        self.assertEqual(top["match_type"], "Exact Match")
        self.assertIn(top["reading_status"], ("Free Full Text", "Free Reading"))

    def test_13_explicit_local_vs_internet_routing(self):
        """Verify explicit local textbook requests route to local search, not internet."""
        q_local_1 = "Find the eigenvalues section in my Kreyszig PDF"
        q_local_2 = "Explain the eigenvalues section from my uploaded textbook"
        q_math = "matrix"

        self.assertTrue(is_local_textbook_query(q_local_1))
        self.assertTrue(is_local_textbook_query(q_local_2))
        self.assertFalse(is_internet_book_query(q_local_1, []))
        self.assertFalse(is_internet_book_query(q_local_2, []))

        self.assertTrue(is_book_search_query(q_math, []))
        self.assertFalse(is_internet_book_query(q_math, []))

    def test_14_syllabus_admin_routing(self):
        """Verify administrative syllabus queries route to syllabus Q&A."""
        q_syl = "What are the course outcomes for Semester 3?"
        self.assertTrue(is_syllabus_query(q_syl))
        self.assertFalse(is_internet_book_query(q_syl, []))

    def test_15_pride_and_prejudice_single_result_and_attribute_integrity(self):
        """
        Regression Test 1-5:
        1. Pride and Prejudice shows one primary result, with no related-record list.
        2. Jane Austen is the author of the primary result.
        3. Its Gutenberg reading link opens the actual full text.
        4. Its EPUB link points to an authorized Gutenberg download.
        5. No unrelated 5-page Internet Archive preview restriction is attached to the Gutenberg edition.
        """
        from backend.book_engine.internet_books import get_book_readable_content

        res = search_internet_books("Pride and Prejudice", limit=5, timeout=6)
        self.assertIsInstance(res, dict)
        pb = res.get("primary_book")
        self.assertIsNotNone(pb)

        # 1 & 2. Author and title
        self.assertEqual(pb.get("title"), "Pride and Prejudice")
        self.assertIn("Jane Austen", pb.get("authors", []))

        # 3. Reading link points to Gutenberg HTML and opens readable text
        reading_url = pb.get("reading_url", "")
        self.assertIn("gutenberg.org", reading_url)
        self.assertEqual(pb.get("reading_status"), "Free Full Text")

        reader_data = get_book_readable_content(pb)
        self.assertTrue(reader_data.get("readable"))
        self.assertGreater(len(reader_data.get("sample_text", "")), 500)
        self.assertIn("Chapter I", reader_data.get("sample_text", "") + str(reader_data.get("headings", [])))

        # 4. EPUB download link points to authorized Gutenberg download
        download_url = pb.get("download_url", "")
        self.assertIn("gutenberg.org", download_url)
        self.assertIn(".epub", download_url)
        self.assertEqual(pb.get("download_status"), "Free Download")

        # 5. Page count and no 5-page preview leakage
        self.assertIsNone(pb.get("preview_pages"))
        self.assertEqual(pb.get("source_provider"), "Project Gutenberg")
        self.assertEqual(pb.get("edition"), "Project Gutenberg Public Domain Edition")
        self.assertEqual(pb.get("page_count_note"), "Full text available online; page count varies by format.")

        # Chat response formatting checks
        formatted = format_internet_books_chat_response(res)
        self.assertIn("Full text available online; page count varies by format.", formatted)
        self.assertNotIn("Other Editions & Related Records", formatted)
        self.assertNotIn("Public online preview: 5 pages", formatted)
        self.assertNotIn("Borrowing required for all 518 pages", formatted)
        self.assertNotIn("Pride and Prejudice and Zombies", formatted)

    def test_16_brief_history_of_time_copyright_restrictions(self):
        """
        Regression Test 6:
        A Brief History of Time retains its correct copyright and borrowing restrictions.
        """
        res = search_internet_books("A Brief History of Time", limit=5, timeout=6)
        self.assertIsInstance(res, dict)
        pb = res.get("primary_book")
        self.assertIsNotNone(pb)

        self.assertEqual(pb.get("title"), "A Brief History of Time")
        self.assertIn("Stephen Hawking", pb.get("authors", []))
        self.assertEqual(pb.get("reading_status"), "Limited Preview (5 Pages) / Borrow Required")
        self.assertEqual(pb.get("download_status"), "Download Unavailable")
        self.assertEqual(pb.get("total_pages"), 218)
        self.assertEqual(pb.get("preview_pages"), 5)
        self.assertIn("archive.org", pb.get("reading_url", ""))

        formatted = format_internet_books_chat_response(res)
        self.assertIn("218 pages (Public online preview: 5 pages | Borrowing required for all 218 pages)", formatted)
        self.assertIn("Limited Preview (5 Pages) / Borrow Required", formatted)
        self.assertIn("Download Unavailable", formatted)
        self.assertNotIn("Other Editions & Related Records", formatted)

    def test_17_linear_algebra_done_right_and_jungle_book(self):
        """
        Regression Tests 7 & 8:
        7. Linear Algebra Done Right returns Sheldon Axler's book.
        8. The Jungle Book returns Rudyard Kipling's book and its verified public-domain access.
        """
        # Linear Algebra Done Right
        res_la = search_internet_books("Linear Algebra Done Right", limit=5, timeout=6)
        pb_la = res_la.get("primary_book")
        self.assertIsNotNone(pb_la)
        self.assertEqual(pb_la.get("title"), "Linear Algebra Done Right")
        self.assertIn("Sheldon Axler", pb_la.get("authors", []))
        fmt_la = format_internet_books_chat_response(res_la)
        self.assertNotIn("Other Editions & Related Records", fmt_la)

        # The Jungle Book
        res_jb = search_internet_books("The Jungle Book", limit=5, timeout=6)
        pb_jb = res_jb.get("primary_book")
        self.assertIsNotNone(pb_jb)
        self.assertEqual(pb_jb.get("title"), "The Jungle Book")
        self.assertIn("Rudyard Kipling", pb_jb.get("authors", []))
        self.assertEqual(pb_jb.get("source_provider"), "Project Gutenberg")
        self.assertEqual(pb_jb.get("reading_status"), "Free Full Text")
        self.assertEqual(pb_jb.get("download_status"), "Free Download")
        self.assertEqual(pb_jb.get("page_count_note"), "Full text available online; page count varies by format.")
        fmt_jb = format_internet_books_chat_response(res_jb)
        self.assertIn("Full text available online; page count varies by format.", fmt_jb)
        self.assertNotIn("Other Editions & Related Records", fmt_jb)

    def test_18_local_textbook_and_syllabus_qa_preservation(self):
        """
        Regression Test 9:
        Verify local textbook search and syllabus Q&A continue to work seamlessly.
        """
        # Local textbook search
        self.assertTrue(is_local_textbook_query("Find chapters about linear algebra in my Kreyszig PDF"))
        self.assertTrue(is_local_textbook_query("Find eigenvalues in my uploaded mathematics books"))
        self.assertFalse(is_internet_book_query("Find chapters about linear algebra in my Kreyszig PDF", []))

        # Online book search
        self.assertTrue(is_internet_book_query("Linear Algebra Done Right", []))
        self.assertTrue(is_internet_book_query("The Jungle Book", []))
        self.assertTrue(is_internet_book_query("Pride and Prejudice", []))

        # Syllabus Q&A
        self.assertTrue(is_syllabus_query("What are the course outcomes in my syllabus?"))
        self.assertFalse(is_internet_book_query("What are the course outcomes in my syllabus?", []))

    def test_19_canonical_author_names(self):
        """
        Regression Test 19:
        Verify authoritative author names across all requested books:
        - The Time Machine — H. G. Wells
        - Frankenstein — Mary Wollstonecraft Shelley
        - Pride and Prejudice — Jane Austen
        - The Adventures of Sherlock Holmes — Arthur Conan Doyle
        - Alice's Adventures in Wonderland — Lewis Carroll
        - The Jungle Book — Rudyard Kipling
        - A Brief History of Time — Stephen Hawking
        - Linear Algebra Done Right — Sheldon Axler
        """
        author_cases = [
            ("Wells, H. G. (Herbert George), 1866-1946", "H. G. Wells"),
            ("Wells", "H. G. Wells"),
            ("Shelley, Mary Wollstonecraft, 1797-1851", "Mary Wollstonecraft Shelley"),
            ("Austen, Jane, 1775-1817", "Jane Austen"),
            ("Doyle, Arthur Conan, 1859-1930", "Arthur Conan Doyle"),
            ("Carroll, Lewis, 1832-1898", "Lewis Carroll"),
            ("Kipling, Rudyard, 1865-1936", "Rudyard Kipling"),
            ("Hawking, Stephen, 1942-2018", "Stephen Hawking"),
            ("Axler, Sheldon", "Sheldon Axler"),
            ("Sheldon Axler", "Sheldon Axler"),
        ]
        for raw, expected in author_cases:
            self.assertEqual(clean_author_name(raw), expected, f"Failed for {raw}")

        # Live book search queries
        res_tm = search_internet_books("The Time Machine", limit=3, timeout=5)
        self.assertEqual(res_tm["primary_book"]["authors"], ["H. G. Wells"])

        res_fr = search_internet_books("Frankenstein", limit=3, timeout=5)
        self.assertEqual(res_fr["primary_book"]["authors"], ["Mary Wollstonecraft Shelley"])

        res_sh = search_internet_books("The Adventures of Sherlock Holmes", limit=3, timeout=5)
        self.assertEqual(res_sh["primary_book"]["authors"], ["Arthur Conan Doyle"])

    def test_20_authentic_covers_and_image_metadata(self):
        """
        Regression Test 20:
        Verify authentic cover selection and image metadata:
        - Public domain Project Gutenberg items use official Gutenberg cover images
        - Avoid generic black placeholder icons
        - Bubble formatter preserves aspect ratio and prevents image distortion
        """
        res_tm = search_internet_books("The Time Machine", limit=3, timeout=5)
        pb = res_tm.get("primary_book")
        self.assertIsNotNone(pb)
        self.assertTrue(pb.get("cover_url", "").startswith("https://www.gutenberg.org/cache/epub/35/"))
        self.assertNotIn("/services/img/", pb.get("cover_url", ""))

        res_pp = search_internet_books("Pride and Prejudice", limit=3, timeout=5)
        pb_pp = res_pp.get("primary_book")
        self.assertIsNotNone(pb_pp)
        self.assertTrue(pb_pp.get("cover_url", "").startswith("https://www.gutenberg.org/cache/epub/1342/"))

        from frontend.app import format_chat_bubble_content
        formatted_bubble = format_chat_bubble_content(f"![The Time Machine Cover]({pb['cover_url']})")
        self.assertIn("object-fit: contain", formatted_bubble)
        self.assertIn("width: auto", formatted_bubble)

    def test_21_new_chat_and_conversation_state(self):
        """
        Regression Test 21:
        Verify + New Chat button behavior:
        1. Starts a fresh conversation with a unique ID.
        2. Clears active messages and pending book reader state.
        3. Preserves prior conversations in chat history without deletion.
        4. Restores prior conversation messages when re-selected.
        """
        import streamlit as st
        from frontend.app import handle_new_chat, handle_select_conv

        # Set up mock initial conversation
        conv1_id = "conv_test_1001"
        conv1_data = {
            "id": conv1_id,
            "title": "The Time Machine",
            "date": "Today",
            "file_name": "Syllabus_2024.pdf",
            "messages": [{"role": "user", "content": "The Time Machine"}, {"role": "assistant", "content": "Here is The Time Machine by H. G. Wells"}],
            "internet_book": {"title": "The Time Machine", "authors": ["H. G. Wells"]},
            "book_sections": None,
            "book_query": ""
        }
        st.session_state.history = [conv1_data]
        st.session_state.active_conv_id = conv1_id
        st.session_state.active_messages = list(conv1_data["messages"])
        st.session_state["last_internet_book"] = conv1_data["internet_book"]

        # User clicks "+ New Chat"
        handle_new_chat()

        # 1. New unique conversation ID created
        self.assertNotEqual(st.session_state.active_conv_id, conv1_id)
        self.assertTrue(st.session_state.active_conv_id.startswith("conv_"))
        # 2. Active messages and book reader state are cleared
        self.assertEqual(len(st.session_state.active_messages), 0)
        self.assertIsNone(st.session_state.get("last_internet_book"))
        # 3. Prior conversation preserved in history
        self.assertEqual(len(st.session_state.history), 1)
        self.assertEqual(st.session_state.history[0]["id"], conv1_id)

        # 4. User selects previous conversation
        handle_select_conv(conv1_id)
        self.assertEqual(st.session_state.active_conv_id, conv1_id)
        self.assertEqual(len(st.session_state.active_messages), 2)
        self.assertEqual(st.session_state["last_internet_book"]["title"], "The Time Machine")


if __name__ == "__main__":
    unittest.main()



