import html
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.book_engine.internet_books import normalize_book_description, safe_text, safe_authors_list, search_internet_books


def test_metadata_normalization_types():
    print("\n--- TEST 1: METADATA NORMALIZATION FOR ARBITRARY DATA TYPES ---")
    
    test_cases = [
        ("None description", None, "Description not available."),
        ("Empty string", "", "Description not available."),
        ("Whitespace only", "   \n\t  ", "Description not available."),
        ("Normal string", "This is a great textbook on computer science.", "This is a great textbook on computer science."),
        ("List of strings", ["xix, 1292 p. : 24 cm", "Includes bibliographical references and index."], "xix, 1292 p. : 24 cm Includes bibliographical references and index."),
        ("List with mixed types", ["Volume 1", None, 1995, ["Nested Note"]], "Volume 1 1995 Nested Note"),
        ("Dictionary with 'value'", {"type": "/type/text", "value": "Open Library description text"}, "Open Library description text"),
        ("Dictionary with 'text'", {"text": "Schema description"}, "Schema description"),
        ("Dictionary arbitrary key-values", {"edition": "2nd", "note": "Classics"}, "2nd Classics"),
        ("Empty dictionary", {}, "Description not available."),
        ("Empty list", [], "Description not available."),
        ("Bytes content", b"Standard ASCII and UTF-8 \xc3\xa9 content", "Standard ASCII and UTF-8 é content"),
        ("HTML tags in description", "<p>A <b>modern</b> approach to <i>AI</i>.</p>", "A modern approach to AI."),
        ("Long string (> 500 chars)", "A" * 600, ("A" * 400) + "..."),
    ]

    for label, input_val, expected_start in test_cases:
        res = normalize_book_description(input_val, max_len=400)
        assert isinstance(res, str), f"[{label}] Expected str, got {type(res)}"
        # Verify html.escape never raises AttributeError!
        escaped = html.escape(res)
        assert isinstance(escaped, str), f"[{label}] html.escape failed!"
        if expected_start.endswith("..."):
            assert res.startswith(expected_start[:50]), f"[{label}] Mismatch: {res[:50]} vs {expected_start[:50]}"
        else:
            assert res == expected_start, f"[{label}] Expected '{expected_start}', got '{res}'"
        print(f" -> PASS: {label:30} => {res[:60]}")

    # Test safe_text helper
    assert safe_text(None) == ""
    assert safe_text(["A", "B"]) == "A, B"
    assert safe_text(b"Hello") == "Hello"
    assert safe_text({"name": "Wiley"}) == "Wiley"
    print(" -> PASS: safe_text helper handles None, list, bytes, and dicts safely.")

    # Test safe_authors_list helper
    assert safe_authors_list(None) == ["Unknown Author"]
    assert safe_authors_list("Thomas H. Cormen, Charles E. Leiserson") == ["Thomas H. Cormen", "Charles E. Leiserson"]
    assert safe_authors_list([{"name": "Andrew S. Tanenbaum"}, "David J. Wetherall"]) == ["Andrew S. Tanenbaum", "David J. Wetherall"]
    print(" -> PASS: safe_authors_list helper handles arbitrary inputs safely.")


def test_individual_book_searches():
    print("\n--- TEST 2: INDIVIDUAL SEARCHES FOR REQUIRED BOOKS ---")
    
    searches = [
        ("Introduction to Algorithms", "Thomas H. Cormen"),
        ("Computer Networks", "Andrew S. Tanenbaum"),
        ("Operating System Concepts", "Silberschatz"),
        ("Database System Concepts", "Silberschatz"),
        ("The Time Machine", "H. G. Wells"),
    ]

    for title_query, expected_author_snippet in searches:
        print(f"\n[SEARCHING]: '{title_query}'")
        res = search_internet_books(title_query, limit=4, timeout=8.0)
        p_book = res.get("primary_book") or (res.get("results", [{}])[0] if res.get("results") else {})
        assert p_book, f"No book record returned for '{title_query}'"

        # 1. Title verification
        b_title = safe_text(p_book.get("title"), "Book Title")
        assert b_title and b_title != "Book Title", f"Invalid title: {b_title}"

        # 2. Author verification
        b_authors = safe_authors_list(p_book.get("authors"))
        b_author_str = ", ".join(b_authors)
        assert any(expected_author_snippet.lower() in a.lower() for a in b_authors) or (expected_author_snippet.lower() in b_author_str.lower()), f"Expected author '{expected_author_snippet}' not in {b_authors}"

        # 3. Description normalization and safe escaping verification
        raw_desc = p_book.get("description")
        b_desc = normalize_book_description(raw_desc, max_len=400)
        assert isinstance(b_desc, str), f"Normalized description is not string: {type(b_desc)}"
        # MUST NEVER THROW ATTRIBUTEERROR!
        escaped_desc = html.escape(b_desc)
        assert escaped_desc, "Escaped description is empty!"

        # 4. Reading link & download status
        b_read_url = safe_text(p_book.get("reading_url"), "")
        assert b_read_url and ("http" in b_read_url or "openlibrary" in b_read_url or "archive.org" in b_read_url or "gutenberg" in b_read_url), f"Missing reading link for '{b_title}': {b_read_url}"

        # 5. Simulate frontend book card rendering snippet without error
        rendered_snippet = f"""
        <h2 class="book-title">{html.escape(b_title)}</h2>
        <span>{html.escape(b_author_str)}</span>
        <div class="book-desc">{html.escape(b_desc)}</div>
        <a href="{html.escape(b_read_url)}">Read Online</a>
        """
        assert rendered_snippet, "Rendered snippet failed!"

        print(f" -> PASS: '{b_title}' by {b_author_str}")
        print(f"    Reading URL: {b_read_url}")
        print(f"    Description: {b_desc[:90]}...")


def test_backend_endpoint():
    print("\n--- TEST 3: BACKEND /books/search API ENDPOINT ---")
    import requests
    try:
        r = requests.get("http://127.0.0.1:8000/books/search", params={"q": "Introduction to Algorithms"}, timeout=10)
        assert r.status_code == 200, f"Backend returned {r.status_code}"
        data = r.json()
        p = data.get("primary_book")
        assert p, "Backend returned no primary_book"
        desc = p.get("description")
        assert isinstance(desc, str), f"Backend description must be string, got {type(desc)}"
        print(f" -> PASS: Backend API returned clean string description: {desc[:80]}...")
    except requests.exceptions.ConnectionError:
        print(" -> SKIP: Backend server not currently running at 127.0.0.1:8000 (running direct tests only).")


if __name__ == "__main__":
    test_metadata_normalization_types()
    test_individual_book_searches()
    test_backend_endpoint()
    print("\n==========================================")
    print("ALL BOOK SEARCH CRASH FIX TESTS PASSED!")
    print("==========================================")
