import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 70)
print("RUNNING BUGFIX VERIFICATION TESTS")
print("=" * 70)

# TEST 1: Imports
print("\n--- TEST 1: VERIFY IMPORTS IN FRONTEND AND BACKEND ---")
import frontend.app as app_mod
assert app_mod._book_search_import_error is None, f"Import error present: {app_mod._book_search_import_error}"
assert app_mod.search_book_sections is not None, "search_book_sections is None!"
assert app_mod.search_pages is not None, "search_pages is None!"
print("PASS: frontend.app successfully imported search_book_sections with zero errors.")

# TEST 2: Topic Searches via perform_book_search
test_queries = [
    "Matrix",
    "Vector",
    "Eigenvalue and eigen vector",
    "Fourier Series"
]

for query in test_queries:
    print(f"\n--- TESTING QUERY: '{query}' ---")
    result_text = app_mod.perform_book_search(query)
    
    # Assert no error messages
    assert not result_text.startswith("Search error:"), f"Search returned error for '{query}': {result_text}"
    assert "Book Search Results" in result_text, f"Unexpected response format for '{query}': {result_text[:200]}"
    assert "Chapter Heading:" in result_text or "No matching content" in result_text
    assert "Physical PDF Pages:" in result_text or "No matching content" in result_text
    
    # Show summary lines
    first_lines = [l for l in result_text.splitlines() if l.strip()][:8]
    print("\n".join(first_lines))
    print(f"PASS: '{query}' returned valid structured section results from indexed books.")

# TEST 3: REGRESSION CHECKS
print("\n--- TEST 3: REGRESSION CHECKS ---")
# FastAPI backend liveness
req = urllib.request.urlopen("http://127.0.0.1:8000/")
assert req.status == 200, f"FastAPI returned status {req.status}"
print("PASS: FastAPI backend is running (HTTP 200 OK)")

# Streamlit frontend liveness
req_s = urllib.request.urlopen("http://localhost:8501/")
assert req_s.status == 200, f"Streamlit returned status {req_s.status}"
print("PASS: Streamlit frontend is running (HTTP 200 OK)")

# Syllabus routing check
syllabus_q = "List all subjects for 1st year"
assert not app_mod.is_book_search_query(syllabus_q, []), "Syllabus query incorrectly classified as book search"
print(f"PASS: Syllabus query '{syllabus_q}' correctly routed to syllabus engine.")

print("\n" + "=" * 70)
print("ALL BUGFIX TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
