import re

def is_internet_book_query(text: str, attached_files: list = None) -> bool:
    """Determine if a query specifically targets internet book search / online reading / downloads."""
    if attached_files:
        return False
    clean = (text or "").strip()
    if not clean:
        return False
    q_lower = clean.lower()

    # Exclude syllabus-specific keywords unless explicit internet/book search is asked
    syllabus_indicators = [
        "semester", "sem", "credit", "credits", "regulation", "regulations",
        "exam", "exams", "marks", "passing", "attendance", "faculty", "hod", "fee", "fees"
    ]
    if any(re.search(r"\b" + re.escape(ind) + r"\b", q_lower) for ind in syllabus_indicators):
        if not any(k in q_lower for k in ["internet", "download", "read online", "google books", "open library", "gutenberg"]):
            return False

    # Explicit local textbook reference syntax like "in the book" or "from the book" -> local book search
    if re.search(r"\b(?:in|from)\s+(?:the\s+)?(?:books?|textbooks?)\b", q_lower):
        if not any(k in q_lower for k in ["internet", "download", "online", "free", "gutenberg", "open library"]):
            return False

    # 1. Explicit online / download / internet book triggers or public provider names
    if any(k in q_lower for k in [
        "internet book", "online book", "read online", "online reading",
        "free download", "paid download", "download book", "download pdf", "free book",
        "free pdf", "open library", "google books", "internet archive", "gutenberg",
        "project gutenberg", "downloadable", "open book", "ebook", "audiobook"
    ]):
        return True

    # 2. Author attribution: "<Title> by <Author>" (e.g., "Advanced Engineering Mathematics by Erwin Kreyszig")
    if re.search(r"\b[a-zA-Z0-9\s\-]{2,}\b\s+by\s+[a-zA-Z]", q_lower):
        return True

    # 3. Explicit book/literature nouns: "story book", "programming book", "calculus textbook", "novel"
    if re.search(r"\b(?:books?|textbooks?|ebooks?|novels?|story\s*books?)\b", q_lower):
        return True

    # 4. "latest [available] edition of ..."
    if re.search(r"\b(?:latest|newest|recent)(?:\s+available)?\s+edition\b", q_lower):
        return True

    # 5. Known famous book/novel titles or famous authors
    if re.search(r"\b(?:harry\s+potter|lord\s+of\s+the\s+rings|sherlock\s+holmes|pride\s+and\s+prejudice|great\s+gatsby|war\s+and\s+peace)\b", q_lower):
        return True
    if re.search(r"\b(?:erwin\s+kreyszig|b\s*\.?\s*s\s*\.?\s*grewal|james\s+stewart|tanenbaum|cormen)\b", q_lower):
        return True

    return False


test_cases = [
    # Problems to fix:
    ("Project Gutenberg", True, "Problem 1: Project Gutenberg should route to internet book search"),
    ("Advanced Engineering Mathematics by Erwin Kreyszig", True, "Problem 2: Title by Author should route to internet book search"),
    ("story book", True, "Problem 3: story book should route to internet book search"),
    ("Search for Python programming books", True, "General internet book search query"),
    
    # Other internet book queries:
    ("Find books about artificial intelligence", True, "Books about AI"),
    ("Search for a free linear algebra book", True, "Free linear algebra book"),
    ("Find the latest available edition of a database systems textbook", True, "Latest edition textbook"),
    ("Harry Potter", True, "Fiction title"),
    
    # Must NOT route to internet book search (Local mathematics search):
    ("matrix", False, "Ordinary math query: matrix"),
    ("fourier series", False, "Ordinary math query: fourier series"),
    ("laplace transform", False, "Ordinary math query: laplace transform"),
    ("eigenvalues", False, "Ordinary math query: eigenvalues"),
    ("matrix in the book", False, "Local textbook reference"),
    
    # Must NOT route to internet book search (Syllabus QA):
    ("What is the syllabus of 2nd year?", False, "Syllabus question: 2nd year"),
    ("How many credits for DBMS?", False, "Syllabus question: credits"),
    ("List all subjects in semester 4", False, "Syllabus question: semester"),
]

all_passed = True
for query, expected, desc in test_cases:
    actual = is_internet_book_query(query)
    status = "PASS" if actual == expected else "FAIL"
    if actual != expected:
        all_passed = False
    print(f"[{status}] '{query}' -> {actual} (expected {expected}) - {desc}")

print("\nOVERALL TEST RESULT:", "ALL PASSED" if all_passed else "SOME FAILED")
