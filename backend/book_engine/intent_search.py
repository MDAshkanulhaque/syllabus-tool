"""
Intelligent Search Intent Detection and Pipeline Separation.

Distinguishes between:
- BOOK_SEARCH: Searching for a book by title, author, ISBN, or work name.
- TOPIC_SEARCH: Searching for an academic concept, chapter, section, or subject inside indexed textbooks.
- AMBIGUOUS: When intent cannot be determined with certainty, allowing the user to choose.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from backend.book_engine.internet_books import (
    search_internet_books,
    CANONICAL_WORKS,
    normalize_title_for_matching,
    normalize_text_key,
    clean_search_query,
)
from backend.book_engine.book_search import (
    search_book_sections,
    format_book_sections_response,
    load_index,
    normalize_text as normalize_index_text,
)

INTENT_BOOK_SEARCH = "BOOK_SEARCH"
INTENT_TOPIC_SEARCH = "TOPIC_SEARCH"
INTENT_AMBIGUOUS = "AMBIGUOUS"

# -------------------------------------------------------------
# KNOWN AUTHORS INDEX & CANONICAL TITLES
# -------------------------------------------------------------
_INDEX_CACHE: Optional[List[Dict[str, Any]]] = None
_INDEXED_TOPICS_CACHE: Optional[Set[str]] = None
_INDEXED_CHAPTERS_CACHE: Optional[Set[str]] = None
_INDEXED_SECTIONS_CACHE: Optional[Set[str]] = None

KNOWN_AUTHORS: Dict[str, str] = {
    "thomas h. cormen": "Introduction to Algorithms",
    "thomas h cormen": "Introduction to Algorithms",
    "thomas cormen": "Introduction to Algorithms",
    "cormen": "Introduction to Algorithms",
    "charles e. leiserson": "Introduction to Algorithms",
    "ronald l. rivest": "Introduction to Algorithms",
    "clifford stein": "Introduction to Algorithms",
    "allen b. downey": "Think Python",
    "allen b downey": "Think Python",
    "allen downey": "Think Python",
    "downey": "Think Python",
    "abraham silberschatz": "Database System Concepts",
    "silberschatz": "Database System Concepts",
    "henry f. korth": "Database System Concepts",
    "s. sudarshan": "Database System Concepts",
    "peter b. galvin": "Operating System Concepts",
    "greg gagne": "Operating System Concepts",
    "erwin kreyszig": "Advanced Engineering Mathematics",
    "kreyszig": "Advanced Engineering Mathematics",
    "b.s. grewal": "Higher Engineering Mathematics",
    "b. s. grewal": "Higher Engineering Mathematics",
    "bs grewal": "Higher Engineering Mathematics",
    "grewal": "Higher Engineering Mathematics",
    "eric lehman": "Mathematics for Computer Science",
    "lehman": "Mathematics for Computer Science",
    "f. thomson leighton": "Mathematics for Computer Science",
    "albert r. meyer": "Mathematics for Computer Science",
    "gilbert brands": "Introduction to Computer Science",
    "sheldon axler": "Linear Algebra Done Right",
    "axler": "Linear Algebra Done Right",
    "silvanus p. thompson": "Calculus Made Easy",
    "silvanus thompson": "Calculus Made Easy",
    "stephen hawking": "A Brief History of Time",
    "hawking": "A Brief History of Time",
    "h.g. wells": "The Time Machine",
    "h. g. wells": "The Time Machine",
    "wells": "The Time Machine",
    "jane austen": "Pride and Prejudice",
    "austen": "Pride and Prejudice",
    "mary shelley": "Frankenstein",
    "shelley": "Frankenstein",
    "arthur conan doyle": "The Adventures of Sherlock Holmes",
    "conan doyle": "The Adventures of Sherlock Holmes",
    "rudyard kipling": "The Jungle Book",
    "kipling": "The Jungle Book",
    "munshi premchand": "Godan",
    "premchand": "Godan",
    "james clear": "Atomic Habits",
    "andrew tanenbaum": "Computer Networks",
    "tanenbaum": "Computer Networks",
}

BOOK_TITLE_PATTERNS = [
    r"^introduction\s+to\s+.+",
    r"^think\s+[a-z]+.*",
    r"^fundamentals\s+of\s+.+",
    r"^principles\s+of\s+.+",
    r"^elements\s+of\s+.+",
    r"^concepts\s+of\s+.+",
    r".+\s+system\s+concepts$",
    r".+\s+made\s+easy$",
    r".+\s+for\s+computer\s+science$",
    r".+\s+in\s+engineering\s+and\s+science$",
    r"^handbook\s+of\s+.+",
    r"^textbook\s+of\s+.+",
    r"^foundations?\s+of\s+.+",
    r"^the\s+art\s+of\s+.+",
    r".+\s+\d+(?:st|nd|rd|th)?\s+edition.*$",
    r".+\s+by\s+[a-z\s.]+$",
]

KNOWN_TECHNICAL_TOPICS: Set[str] = {
    # Mathematics & Engineering
    "matrix", "matrices", "determinant", "determinants", "probability", "statistics",
    "integration", "differentiation", "derivative", "derivatives", "integral", "integrals",
    "finite differences", "difference equation", "difference equations",
    "fourier series", "laplace transform", "laplace transforms", "fourier transform",
    "differential equation", "differential equations", "ordinary differential equations",
    "partial differential equations", "eigenvalues", "eigenvectors", "linear algebra",
    "linear programming", "simplex method", "transportation problem",
    "interpolation", "newton's divided difference", "lagrange interpolation",
    "numerical integration", "simpson's rule", "trapezoidal rule", "runge kutta",
    "euler method", "gauss elimination", "cramer's rule", "complex variables",
    "cauchy integral", "residue theorem", "series summation", "vector calculus",
    "divergence theorem", "green's theorem", "stokes theorem", "gradient", "divergence", "curl",
    # Computer Science & Technical concepts
    "python loops", "loops", "loop", "for loop", "while loop", "nested loops",
    "database normalization", "normalization", "1nf", "2nf", "3nf", "bcnf",
    "operating system scheduling", "cpu scheduling", "process scheduling",
    "round robin", "shortest job first", "first come first served",
    "data structures", "linked list", "linked lists", "binary search tree",
    "binary tree", "stack", "stacks", "queue", "queues", "graph traversal",
    "depth first search", "breadth first search", "sorting algorithms",
    "bubble sort", "quick sort", "merge sort", "heap sort", "hashing",
    "recursion", "dynamic programming", "relational algebra", "sql queries",
    "acid properties", "deadlock", "paging", "segmentation", "virtual memory",
    "cache memory", "concurrency", "mutual exclusion", "semaphores",
}


def _ensure_indexed_topics_loaded():
    """Extract and cache unique chapter and section topics from pages_index.json."""
    global _INDEX_CACHE, _INDEXED_TOPICS_CACHE, _INDEXED_CHAPTERS_CACHE, _INDEXED_SECTIONS_CACHE
    if _INDEXED_TOPICS_CACHE is not None:
        return

    _INDEXED_TOPICS_CACHE = set()
    _INDEXED_CHAPTERS_CACHE = set()
    _INDEXED_SECTIONS_CACHE = set()

    try:
        records = load_index()
        _INDEX_CACHE = records
        for r in records:
            ch = r.get("chapter_heading")
            if ch:
                clean_ch = re.sub(r"^chapter\s+\d+\s*:\s*", "", ch, flags=re.I).strip().lower()
                _INDEXED_CHAPTERS_CACHE.add(clean_ch)
                _INDEXED_TOPICS_CACHE.add(clean_ch)
            sec = r.get("section_heading")
            if sec:
                clean_sec = re.sub(r"^\d+(\.\d+)*\s*", "", sec).strip().lower()
                _INDEXED_SECTIONS_CACHE.add(clean_sec)
                _INDEXED_TOPICS_CACHE.add(clean_sec)
    except Exception as exc:
        print(f"Index loading warning: {exc}")


def detect_search_intent(query: str) -> str:
    """
    Identifies whether the user intention is:
    - BOOK_SEARCH: Title, author, ISBN, or specific textbook query.
    - TOPIC_SEARCH: Concept, chapter, section, mathematical formula, or technical topic.
    - AMBIGUOUS: Vague, single generic word, or conflicting match requiring user selection.
    """
    raw = (query or "").strip()
    if not raw:
        return INTENT_AMBIGUOUS

    q_lower = raw.lower()

    # 1. Explicit query prefixes
    book_prefixes = (
        "book:", "book search:", "find book:", "read book:", "download book:",
        "author:", "find book", "search book", "show book", "get book",
        "read online", "download pdf", "download epub", "find textbook"
    )
    for bp in book_prefixes:
        if q_lower.startswith(bp):
            return INTENT_BOOK_SEARCH

    topic_prefixes = (
        "topic:", "concept:", "explain:", "explain ", "what is ", "what are ",
        "how does ", "formula for ", "definition of ", "search inside book:",
        "in the book:", "from the book:", "search in book:", "find in book:"
    )
    for tp in topic_prefixes:
        if q_lower.startswith(tp):
            return INTENT_TOPIC_SEARCH

    # 2. ISBN Detection (9 to 13 digits)
    isbn_clean = re.sub(r"[-\s]", "", raw)
    if re.search(r"\b(?:isbn\s*(?:-?1[03])?\s*[:\-]?\s*)?([0-9]{9,13}[0-9xX])\b", q_lower) or (
        len(isbn_clean) in (10, 13) and isbn_clean[:-1].isdigit() and (isbn_clean[-1].isdigit() or isbn_clean[-1].upper() == "X")
    ):
        return INTENT_BOOK_SEARCH

    # 3. Citation / Work by Author pattern: e.g. "Calculus by Stewart", "Clean Code by Martin"
    if re.search(r"^.+?\s+by\s+[a-z\s.]+$", q_lower) or re.search(r"^.+?\s+\d+(?:st|nd|rd|th)?\s+ed(?:ition)?", q_lower):
        return INTENT_BOOK_SEARCH

    # 4. Check Known Book Authors (e.g. "Thomas H. Cormen", "Allen B. Downey", "Erwin Kreyszig")
    clean_auth_key = normalize_text_key(raw)
    if clean_auth_key in KNOWN_AUTHORS:
        return INTENT_BOOK_SEARCH

    for author_key in KNOWN_AUTHORS:
        if author_key == clean_auth_key or (len(clean_auth_key) > 5 and author_key in clean_auth_key) or (len(author_key) > 5 and clean_auth_key in author_key):
            return INTENT_BOOK_SEARCH

    # 5. Check Canonical Works and Book Catalogue
    norm_title = normalize_title_for_matching(raw)
    if norm_title in CANONICAL_WORKS:
        return INTENT_BOOK_SEARCH

    # Check if any canonical work title is a close match
    for cw_key, cw_val in CANONICAL_WORKS.items():
        if norm_title == cw_key or (len(norm_title) > 6 and cw_key in norm_title) or (len(cw_key) > 6 and norm_title in cw_key):
            return INTENT_BOOK_SEARCH
        canonical_title_norm = normalize_title_for_matching(cw_val.get("title", ""))
        if norm_title == canonical_title_norm:
            return INTENT_BOOK_SEARCH

    # 6. Check Syntactic Book Title Patterns
    for pat in BOOK_TITLE_PATTERNS:
        if re.search(pat, q_lower):
            return INTENT_BOOK_SEARCH

    # 7. Check Indexed Topics & Known Technical Concepts
    _ensure_indexed_topics_loaded()
    norm_q = normalize_index_text(raw)

    if norm_q in KNOWN_TECHNICAL_TOPICS or q_lower in KNOWN_TECHNICAL_TOPICS:
        return INTENT_TOPIC_SEARCH

    for tech_t in KNOWN_TECHNICAL_TOPICS:
        if tech_t in norm_q or norm_q in tech_t:
            return INTENT_TOPIC_SEARCH

    if _INDEXED_TOPICS_CACHE:
        if norm_q in _INDEXED_TOPICS_CACHE:
            return INTENT_TOPIC_SEARCH
        for idx_t in _INDEXED_TOPICS_CACHE:
            if idx_t and (idx_t == norm_q or (len(norm_q) > 4 and norm_q in idx_t)):
                return INTENT_TOPIC_SEARCH

    # 8. Check if words are distinct topic nouns
    words = re.findall(r"[a-z0-9]+", q_lower)
    if len(words) == 1 and words[0] in ("matrix", "matrices", "determinant", "determinants", "probability", "integration", "differentiation", "derivative", "derivatives"):
        return INTENT_TOPIC_SEARCH

    # 9. Multi-word title case without topic matches -> Check Book Title heuristic
    if 2 <= len(words) <= 6:
        original_words = raw.split()
        is_title_cased = all(w[0].isupper() for w in original_words if w.lower() not in ("of", "in", "the", "and", "a", "an", "for", "to", "with", "on", "by", "at"))
        if is_title_cased and original_words[0].lower() not in ("what", "how", "why", "when", "where", "explain", "find"):
            return INTENT_BOOK_SEARCH

    # 10. Single generic words or ambiguous terms
    return INTENT_AMBIGUOUS


# -------------------------------------------------------------
# PIPELINE 1: BOOK SEARCH (Metadata & Discovery Only)
# -------------------------------------------------------------
def search_books(query: str, limit: int = 6, timeout: float = 6.0) -> Dict[str, Any]:
    """
    Dedicated Book Search Pipeline.
    Searches book catalogue and internet public domain / academic records.
    Returns matching books ONLY.
    Never searches PDF sections or internal pages.
    """
    clean_q = (query or "").strip()
    clean_q = re.sub(
        r"^(?:book:|book search:|find book:|read book:|download book:|author:|find book|search book|show book|get book)\s*",
        "",
        clean_q,
        flags=re.IGNORECASE
    ).strip()

    if not clean_q:
        return {
            "status": "not_found",
            "query": query,
            "book": None,
            "other_editions": [],
            "all_books": [],
            "message": "Please enter a valid book title, author, or ISBN."
        }

    # Resolve author shorthand
    search_term = clean_q
    clean_auth_key = normalize_text_key(clean_q)
    if clean_auth_key in KNOWN_AUTHORS:
        mapped_work = KNOWN_AUTHORS[clean_auth_key]
        search_term = mapped_work

    res = search_internet_books(search_term, limit=limit, timeout=timeout)
    primary_book = res.get("primary_book")
    all_books = res.get("results", [])

    if not primary_book and all_books:
        primary_book = all_books[0]

    if primary_book:
        b_title = primary_book.get("title", clean_q)
        return {
            "status": "found",
            "query": clean_q,
            "book": primary_book,
            "other_editions": res.get("other_editions", []),
            "all_books": all_books,
            "search_res": res,
            "message": f"📖 Found book record for **{b_title}**."
        }

    return {
        "status": "not_found",
        "query": clean_q,
        "book": None,
        "other_editions": [],
        "all_books": [],
        "search_res": res,
        "message": f"📖 Book not found: No matching book record found for \"**{clean_q}**\"."
    }


# -------------------------------------------------------------
# PIPELINE 2: TOPIC SEARCH (Internal Textbook Sections Only)
# -------------------------------------------------------------
def search_book_topics(query: str) -> Dict[str, Any]:
    """
    Dedicated Topic Search Pipeline.
    Searches inside indexed textbook chapters, sections, and PDF pages.
    Returns matching PDF pages ONLY.
    Never replaces the book catalogue with unrelated books.
    """
    clean_topic = (query or "").strip()
    clean_topic = re.sub(
        r"^(?:topic:|concept:|explain:|explain|what is|what are|how does|formula for|definition of|search inside book:|in the book:|from the book:|search in book:|find in book:)\s*",
        "",
        clean_topic,
        flags=re.IGNORECASE
    ).strip()

    if not clean_topic:
        return {
            "status": "not_found",
            "topic": query,
            "sections_by_book": {},
            "total_sections": 0,
            "formatted_answer": "Please specify a topic or concept to search inside textbooks."
        }

    results_by_book = search_book_sections(clean_topic)
    total_sections = sum(len(secs) for secs in results_by_book.values())

    # Smart fallback for composite topics (e.g. 'Python Loops' -> 'loops', 'Database Normalization' -> 'normalization')
    if total_sections == 0:
        words = clean_topic.split()
        if len(words) > 1:
            for fallback_w in reversed(words):
                if len(fallback_w) > 3 and fallback_w.lower() not in ("python", "database", "system", "programming", "engineering"):
                    fallback_res = search_book_sections(fallback_w)
                    fallback_count = sum(len(secs) for secs in fallback_res.values())
                    if fallback_count > 0:
                        results_by_book = fallback_res
                        total_sections = fallback_count
                        break

    if total_sections > 0:
        formatted = format_book_sections_response(clean_topic, results_by_book)
        return {
            "status": "found",
            "topic": clean_topic,
            "sections_by_book": results_by_book,
            "total_sections": total_sections,
            "formatted_answer": formatted
        }

    return {
        "status": "not_found",
        "topic": clean_topic,
        "sections_by_book": {},
        "total_sections": 0,
        "formatted_answer": f"Information regarding topic '**{clean_topic}**' was not found in the indexed textbooks."
    }

