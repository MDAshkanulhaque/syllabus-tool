import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.book_engine.internet_books import (
    search_internet_books,
    format_internet_books_chat_response,
)
from frontend.app import is_internet_book_query, is_book_search_query

target_queries = [
    "Project Gutenberg",
    "Advanced Engineering Mathematics by Erwin Kreyszig",
    "story book",
    "Search for Python programming books",
]

print("=================================================================")
print("TESTING TARGET QUERIES: ROUTING & REAL SEARCH EXECUTION")
print("=================================================================")

for q in target_queries:
    is_net = is_internet_book_query(q)
    print(f"\nQuery: '{q}'")
    print(f" -> is_internet_book_query: {is_net}")
    assert is_net, f"Query '{q}' was expected to route to Internet Book Search!"

    res = search_internet_books(q, limit=5, timeout=4)
    total = res.get("total_found", 0)
    print(f" -> Providers contacted: {res.get('providers_contacted')}")
    print(f" -> Providers successful: {res.get('providers_successful')}")
    print(f" -> Providers failed: {res.get('providers_failed')}")
    print(f" -> Total books retrieved: {total}")
    assert total > 0, f"Query '{q}' returned 0 books!"

    top = res["results"][0]
    print(f" -> Top Result: '{top.get('title')}' by {top.get('authors')}")
    print(f" -> Reading Status: {top.get('reading_status')} (URL: {bool(top.get('reading_url'))})")
    print(f" -> Download Status: {top.get('download_status')} (URL: {bool(top.get('download_url'))})")

    # Verify formatted markdown
    formatted = format_internet_books_chat_response(res)
    assert "Internet Book Search Results" in formatted
    print(f" -> Formatted Markdown length: {len(formatted)} chars")

print("\n=================================================================")
print("ALL 4 TARGET QUERIES ROUTED & RETRIEVED REAL ONLINE RESULTS!")
print("=================================================================")
