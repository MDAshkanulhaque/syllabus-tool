import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from frontend.app import is_internet_book_query, is_book_search_query, perform_book_search
from backend.main import DOCUMENT_ENGINES, AcademicSyllabusQAEngine

print("=== 1. VERIFY ORDINARY MATHEMATICS QUERY 'matrix' ===")
q_math = "matrix"
assert not is_internet_book_query(q_math), "'matrix' should NOT be an internet book query!"
assert is_book_search_query(q_math, []), "'matrix' MUST be a local book search query!"
math_resp = perform_book_search(q_math)
assert "Book Search Results for" in math_resp
assert "NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL" in math_resp or "advanced-engineering-mathematics" in math_resp
print("[PASS] Local textbook search for 'matrix' works and returns indexed book sections.")

print("\n=== 2. VERIFY SYLLABUS QUERY (e.g. 'What is the syllabus of 2nd year?') ===")
q_syl = "What is the syllabus of 2nd year?"
assert not is_internet_book_query(q_syl), "Syllabus query should NOT route to internet books!"
assert not is_book_search_query(q_syl, []), "Syllabus query should NOT route to local books!"
print("[PASS] Syllabus query correctly routed to syllabus engine.")

print("\n=== 3. VERIFY ONE PROVIDER TIMING OUT DOES NOT BECOME 'NO BOOKS FOUND' ===")
from backend.book_engine.internet_books import format_internet_books_chat_response

# Simulated partial timeout: Google Books and Internet Archive timed out, but Open Library returned 1 book
partial_res = {
    "query": "Linear Algebra",
    "total_found": 1,
    "providers_contacted": ["Google Books", "Open Library", "Internet Archive"],
    "providers_successful": ["Open Library"],
    "providers_failed": ["Google Books", "Internet Archive"],
    "results": [
        {
            "title": "Linear Algebra",
            "authors": ["Kenneth Hoffman"],
            "published_year": "1971",
            "reading_status": "Free Reading",
            "reading_url": "https://openlibrary.org/works/OL123",
            "download_status": "Free Download",
            "download_url": "https://archive.org/download/test.pdf"
        }
    ]
}
msg = format_internet_books_chat_response(partial_res)
assert "Linear Algebra" in msg
assert "No matching books found" not in msg
assert "timeout" in msg.lower()
print("[PASS] Partial provider timeout does not result in false 'no books found'; successful books are displayed.")

print("\n=== 4. VERIFY GENUINE NO-RESULTS VS COMPLETE NETWORK TIMEOUT ===")
all_failed_res = {
    "query": "Random Query",
    "total_found": 0,
    "providers_contacted": ["Google Books", "Open Library", "Internet Archive"],
    "providers_successful": [],
    "providers_failed": ["Google Books", "Open Library", "Internet Archive"],
    "results": []
}
err_msg = format_internet_books_chat_response(all_failed_res)
assert "Network / Connection Error" in err_msg
assert "No matching books found across public book libraries" not in err_msg
print("[PASS] All providers failing produces clear network/connection error instead of misleading 'no matching books'.")

genuine_empty_res = {
    "query": "XylophonicZebra9999",
    "total_found": 0,
    "providers_contacted": ["Google Books", "Open Library", "Internet Archive"],
    "providers_successful": ["Google Books", "Open Library", "Internet Archive"],
    "providers_failed": [],
    "results": []
}
empty_msg = format_internet_books_chat_response(genuine_empty_res)
assert "No matching books found across public book libraries" in empty_msg
print("[PASS] Genuine empty search properly displays 'No matching books found'.")

print("\n=================================================================")
print("ALL EDGE CASES & VERIFICATION CHECKS PASSED!")
print("=================================================================")
