"""
Book search and indexing engine package.
"""
from backend.book_engine.book_search import (
    search_pages,
    search_book_sections,
    format_book_sections_response,
    group_results_by_section,
)
from backend.book_engine.intent_search import (
    detect_search_intent,
    search_books,
    search_book_topics,
    INTENT_BOOK_SEARCH,
    INTENT_TOPIC_SEARCH,
    INTENT_AMBIGUOUS,
)

__all__ = [
    "search_pages",
    "search_book_sections",
    "format_book_sections_response",
    "group_results_by_section",
    "detect_search_intent",
    "search_books",
    "search_book_topics",
    "INTENT_BOOK_SEARCH",
    "INTENT_TOPIC_SEARCH",
    "INTENT_AMBIGUOUS",
]
