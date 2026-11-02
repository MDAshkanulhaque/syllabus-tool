import time
import requests
import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.book_engine.internet_books import search_internet_books, SEARCH_CACHE

queries = [
    "The Jungle Book",
    "Calculus Made Easy",
    "Linear Algebra Done Right",
    "Higher Engineering Mathematics by B.V. Ramana",
    "Atomic Habits by James Clear"
]

def run_benchmarks(is_second_run=False):
    tag = "CACHED SEARCH (2nd RUN)" if is_second_run else "FRESH PROVIDER SEARCH (1st RUN)"
    print(f"\n==================== {tag} ====================")
    for q in queries:
        t0 = time.monotonic()
        res = search_internet_books(q, limit=8)
        dur = time.monotonic() - t0
        p = res.get("primary_book")
        from_cache = res.get("from_cache", False)

        r_code = "N/A"
        if p and p.get("reading_url"):
            try:
                r = requests.head(p["reading_url"], headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=4)
                r_code = str(r.status_code)
            except Exception:
                r_code = "Timeout/Error"

        dl_code = "N/A"
        if p and p.get("download_url"):
            try:
                r_dl = requests.head(p["download_url"], headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=4)
                dl_code = f"HTTP {r_dl.status_code}"
            except Exception:
                dl_code = "Timeout/Error"

        print(f"QUERY: \"{q}\"")
        print(f"  • Search Duration: {dur:.3f} seconds")
        print(f"  • Primary Title: {p.get('title') if p else 'N/A'}")
        print(f"  • Primary Author(s): {p.get('authors') if p else 'N/A'}")
        print(f"  • Number of Primary Results: {1 if p else 0} (Total Results: {res.get('total_found')})")
        print(f"  • Provider: {p.get('source_provider') if p else 'N/A'}")
        print(f"  • Source Identifier: {p.get('id') if p else 'N/A'}")
        print(f"  • Reading URL: {p.get('reading_url') if p else 'N/A'} (Status: {r_code})")
        dl_url = p.get('download_url') if p else None
        dl_status = p.get('download_status') if p else 'N/A'
        print(f"  • Download URL: {dl_url or 'None'} (Verified Status: {dl_status} | {dl_code})")
        print(f"  • Result Origin: {'Cache Hit' if from_cache else 'Fresh Provider Response'}")
        print("-" * 50)

if __name__ == "__main__":
    # 1. Fresh run (clear cache first)
    SEARCH_CACHE._search_cache.clear()
    SEARCH_CACHE._provider_cache.clear()
    SEARCH_CACHE._verify_cache.clear()
    run_benchmarks(is_second_run=False)

    # 2. Second run (demonstrates caching layer)
    run_benchmarks(is_second_run=True)
