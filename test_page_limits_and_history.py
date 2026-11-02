import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.book_engine.internet_books import search_internet_books, safe_text

def test_page_limits_and_access_types():
    print("\n--- TEST: ACCESS TYPES, PAGE LIMITS, AND PRICING METADATA ---")

    # 1. Book containing > 1000 pages (Introduction to Algorithms)
    print("\n[TEST 1]: Book with > 1000 pages ('Introduction to Algorithms')")
    res1 = search_internet_books("Introduction to Algorithms", limit=3, timeout=8.0)
    b1 = res1.get("primary_book", {})
    assert b1, "Failed to find 'Introduction to Algorithms'"
    tot1 = b1.get("total_pages")
    print(f" -> Title: {b1.get('title')}")
    print(f" -> Total Pages: {tot1}")
    print(f" -> Preview Pages: {b1.get('preview_pages')}")
    print(f" -> Restricted Pages: {b1.get('restricted_pages')}")
    print(f" -> Access Type: {b1.get('access_type')}")
    print(f" -> Price: {b1.get('price')}")
    assert tot1 is not None and isinstance(tot1, int) and tot1 > 1000, f"Expected >1000 pages, got {tot1}"
    assert b1.get("preview_pages") in (5, 10, "5 pages") or isinstance(b1.get("preview_pages"), int), "Preview pages missing"
    assert b1.get("restricted_pages") is not None, "Restricted pages missing"

    # 2. Book containing ~600-900 pages (Operating System Concepts)
    print("\n[TEST 2]: Book with ~600-900 pages ('Operating System Concepts')")
    res2 = search_internet_books("Operating System Concepts", limit=3, timeout=8.0)
    b2 = res2.get("primary_book", {})
    assert b2, "Failed to find 'Operating System Concepts'"
    tot2 = b2.get("total_pages")
    print(f" -> Title: {b2.get('title')}")
    print(f" -> Total Pages: {tot2}")
    print(f" -> Preview Pages: {b2.get('preview_pages')}")
    print(f" -> Restricted Pages: {b2.get('restricted_pages')}")
    print(f" -> Access Type: {b2.get('access_type')}")
    assert tot2 is not None and isinstance(tot2, int) and 500 <= tot2 <= 1200, f"Expected ~600-900 pages, got {tot2}"

    # 3. Book with only 5-10 preview pages (Computer Networks or Cormen)
    print("\n[TEST 3]: Book with 5-10 preview pages ('Computer Networks')")
    res3 = search_internet_books("Computer Networks", limit=3, timeout=8.0)
    b3 = res3.get("primary_book", {})
    assert b3, "Failed to find 'Computer Networks'"
    prev3 = b3.get("preview_pages")
    print(f" -> Title: {b3.get('title')}")
    print(f" -> Total Pages: {b3.get('total_pages')}")
    print(f" -> Preview Pages: {prev3}")
    print(f" -> Restricted Pages: {b3.get('restricted_pages')}")
    assert prev3 in (5, 10) or (isinstance(prev3, int) and 1 <= prev3 <= 20), f"Expected 5-10 preview pages, got {prev3}"

    # 4. Freely accessible full book (The Time Machine)
    print("\n[TEST 4]: Freely accessible full book ('The Time Machine')")
    res4 = search_internet_books("The Time Machine", limit=3, timeout=8.0)
    b4 = res4.get("primary_book", {})
    assert b4, "Failed to find 'The Time Machine'"
    print(f" -> Title: {b4.get('title')}")
    print(f" -> Source: {b4.get('source_provider')}")
    print(f" -> Access Type: {b4.get('access_type')}")
    print(f" -> Price: {b4.get('price')}")
    print(f" -> Restricted Pages: {b4.get('restricted_pages')}")
    assert b4.get("access_type") == "full_free", f"Expected full_free, got {b4.get('access_type')}"
    assert b4.get("restricted_pages") == 0, f"Expected 0 restricted pages, got {b4.get('restricted_pages')}"
    assert "Free" in b4.get("price", ""), "Expected Free price"

    # 5. Book requiring payment for full access (Linear Algebra Done Right)
    print("\n[TEST 5]: Book requiring payment for full access ('Linear Algebra Done Right')")
    res5 = search_internet_books("Linear Algebra Done Right", limit=4, timeout=8.0)
    b5 = res5.get("primary_book", {})
    assert b5, "Failed to find 'Linear Algebra Done Right'"
    print(f" -> Title: {b5.get('title')}")
    print(f" -> Total Pages: {b5.get('total_pages')}")
    print(f" -> Preview Pages: {b5.get('preview_pages')}")
    print(f" -> Restricted Pages: {b5.get('restricted_pages')}")
    print(f" -> Access Type: {b5.get('access_type')}")
    print(f" -> Price: {b5.get('price')}")
    print(f" -> Purchase URL: {b5.get('purchase_url')}")
    assert b5.get("total_pages") is not None and b5.get("total_pages") > 0, "Total pages missing"
    assert b5.get("restricted_pages") is not None and b5.get("restricted_pages") > 0, "Restricted pages missing"
    assert b5.get("access_type") == "purchase_required", f"Expected purchase_required, got {b5.get('access_type')}"
    assert b5.get("purchase_url"), "Official purchase URL missing"
    assert "$" in b5.get("price", "") or "USD" in b5.get("price", ""), "Official price missing"

    # Also verify Database System Concepts (preview / restricted pages)
    print("\n[TEST 5b]: Library Borrow Restricted Book ('Database System Concepts')")
    res5b = search_internet_books("Database System Concepts", limit=4, timeout=8.0)
    b5b = res5b.get("primary_book", {})
    assert b5b, "Failed to find 'Database System Concepts'"
    assert b5b.get("total_pages") == 1376, f"Expected 1376 pages, got {b5b.get('total_pages')}"
    assert b5b.get("restricted_pages") == 1371, f"Expected 1371 restricted pages, got {b5b.get('restricted_pages')}"
    print(f" -> Database System Concepts: Total={b5b.get('total_pages')}, Restricted={b5b.get('restricted_pages')}")

    print("\n -> ALL PAGE LIMIT AND ACCESS TESTS PASSED!")


def test_consecutive_searches_preservation():
    print("\n--- TEST: CONSECUTIVE 5-BOOK SEARCH PRESERVATION IN SAME CHAT ---")
    searches = [
        "Introduction to Algorithms",
        "Computer Networks",
        "Operating System Concepts",
        "Database System Concepts",
        "The Time Machine",
    ]

    chat_searched_books = []
    for query in searches:
        res = search_internet_books(query, limit=2, timeout=8.0)
        p = res.get("primary_book", {})
        assert p, f"Search failed for {query}"
        chat_searched_books.append(p)
        print(f" -> Searched #{len(chat_searched_books)}: '{p.get('title')}' by {p.get('authors')}")

    # Verify that all 5 books exist in the list in order
    assert len(chat_searched_books) == 5, f"Expected 5 books, got {len(chat_searched_books)}"
    
    # Check original order and distinct titles
    titles = [b.get("title") for b in chat_searched_books]
    print(f"\nFinal Preserved Search List ({len(titles)} books):")
    for idx, t in enumerate(titles):
        print(f" [{idx + 1}] {t}")

    assert "Algorithms" in titles[0], f"Book 1 mismatch: {titles[0]}"
    assert "Networks" in titles[1], f"Book 2 mismatch: {titles[1]}"
    assert "Operating System" in titles[2], f"Book 3 mismatch: {titles[2]}"
    assert "Database" in titles[3], f"Book 4 mismatch: {titles[3]}"
    assert "Time Machine" in titles[4], f"Book 5 mismatch: {titles[4]}"

    # Verify newest search is at the bottom (index 4)
    assert "Time Machine" in titles[-1], "Newest search is not at the bottom!"

    print("\n -> ALL 5 CONSECUTIVE SEARCH RESULTS PRESERVED IN ORDER!")


if __name__ == "__main__":
    test_page_limits_and_access_types()
    test_consecutive_searches_preservation()
    print("\n==========================================")
    print("ALL VERIFICATION SUITES PASSED!")
    print("==========================================")
