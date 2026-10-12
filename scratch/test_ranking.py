import re
import math
from pathlib import Path
import json

INDEX_FILE = Path("backend/book_index/pages_index.json")
with open(INDEX_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

query = "matrix"
normalized_query = "matrix"
query_words = ["matrix"]

def test_rank(records, query):
    scored = []
    for r in records:
        text = r.get("text", "")
        searchable_text = r.get("search_text", "")
        if not searchable_text or normalized_query not in searchable_text:
            continue
        
        # Base match score
        score = 100.0
        
        # Word occurrences
        occurrences = len(re.findall(r"\bmatrix\b", searchable_text, re.IGNORECASE))
        # Also stem/plural forms if query is matrix
        related_occurrences = len(re.findall(r"\bmatrices\b", searchable_text, re.IGNORECASE))
        total_term_freq = occurrences + related_occurrences
        
        # Term frequency score (logarithmic or weighted)
        score += min(total_term_freq * 1.5, 30.0)
        
        # Heading boosts
        sec = r.get("section_heading", "").lower()
        ch = r.get("chapter_heading", "").lower()
        
        # Check if query or related term is in section heading
        if any(term in sec for term in ["matrix", "matrices"]):
            score += 40.0
            # Extra boost for introductory/foundational sections
            if any(term in sec for term in ["introduction", "basic", "addition", "multiplication", "definition", "concept"]):
                score += 15.0
                
        # Check if query or related term is in chapter heading
        if any(term in ch for term in ["matrix", "matrices"]):
            score += 25.0
            
        # Check if the title or heading appears in the first few lines of text
        first_lines = " ".join(text.splitlines()[:5]).lower()
        if any(term in first_lines for term in ["matrix", "matrices"]):
            score += 10.0
            
        scored.append({
            "book_name": r.get("book_name"),
            "pdf_page": r.get("pdf_page"),
            "chapter": r.get("chapter_heading"),
            "section": r.get("section_heading"),
            "score": round(score, 2),
            "freq": total_term_freq
        })
        
    scored.sort(key=lambda x: -x["score"])
    return scored

results = test_rank(records, query)
print(f"Total matching: {len(results)}")
print("\nTop 15 Results:")
for idx, r in enumerate(results[:15], 1):
    print(f"#{idx}: Book={r['book_name'][:25]} | PDF={r['pdf_page']} | Ch={r['chapter'][:25]} | Sec={r['section'][:35]} | Score={r['score']}")
