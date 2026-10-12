import sys
import re
import json
from pathlib import Path
from collections import defaultdict

INDEX_FILE = Path("backend/book_index/pages_index.json")

with open(INDEX_FILE, "r", encoding="utf-8") as f:
    all_pages = json.load(f)

# Group all index pages by (book_name, chapter_heading, section_heading)
# to know the full boundary and all continuation pages of every section
book_sections_map = defaultdict(lambda: defaultdict(list))
for p in all_pages:
    b_name = p["book_name"]
    sec_key = (p.get("chapter_heading") or "Unavailable", p.get("section_heading") or "Unavailable")
    book_sections_map[b_name][sec_key].append(p)

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.casefold()
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def tokenize(text):
    return re.findall(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", normalize_text(text))

def get_query_terms(query_words):
    terms = set(query_words)
    for w in query_words:
        terms.add(w)
        if w == "matrix":
            terms.add("matrices")
        elif w == "matrices":
            terms.add("matrix")
        elif w == "eigenvalue" or w == "eigenvalues":
            terms.add("eigenvalue")
            terms.add("eigenvalues")
            terms.add("eigenvector")
            terms.add("eigenvectors")
        elif w.endswith("ies"):
            terms.add(w[:-3] + "y")
        elif w.endswith("es"):
            terms.add(w[:-2])
        elif w.endswith("s"):
            terms.add(w[:-1])
        else:
            terms.add(w + "s")
            terms.add(w + "es")
    return terms

def search_sections(query):
    norm_q = normalize_text(query)
    q_words = tokenize(norm_q)
    if not q_words:
        return {}
    q_word_set = set(q_words)
    term_variants = get_query_terms(q_words)

    # Output structure: book_name -> list of sections
    results_by_book = {}

    for b_name, sections in book_sections_map.items():
        matched_sections = []
        for (ch_title, sec_title), pages in sections.items():
            # Check if this section contains the query
            # We check both:
            # 1. Any page contains all query words
            # 2. Section heading or chapter heading contains query words
            sec_searchable = " ".join(p.get("search_text", "") for p in pages)
            sec_words = set(tokenize(sec_searchable))
            
            # Heading text
            heading_text = normalize_text(f"{ch_title} {sec_title}")
            heading_words = set(tokenize(heading_text))
            
            # Condition: either query words in section body, or query words in section heading
            has_body_match = q_word_set.issubset(sec_words)
            has_heading_match = any(t in heading_text for t in term_variants) or q_word_set.issubset(heading_words)
            
            if not (has_body_match or has_heading_match):
                continue
                
            # Score this section
            score = 100.0
            if norm_q in sec_searchable:
                score += 30.0
                
            # Heading boosts
            sec_lower = sec_title.lower()
            ch_lower = ch_title.lower()
            if any(t in sec_lower for t in term_variants) and "unavailable" not in sec_lower:
                score += 60.0
                if any(k in sec_lower for k in ["introduction", "basic", "definition", "concept", "addition", "multiplication"]):
                    score += 25.0
            if any(t in ch_lower for t in term_variants) and "unavailable" not in ch_lower:
                score += 40.0
                
            # Occurrences count
            occurrences = sum(len(re.findall(rf"\b{re.escape(t)}\b", sec_searchable)) for t in term_variants)
            score += min(occurrences * 0.5, 40.0)
            
            # Page ranges
            pdf_pages = [p["pdf_page"] for p in pages]
            pdf_start, pdf_end = min(pdf_pages), max(pdf_pages)
            
            printed = [p["printed_page"] for p in pages if p["printed_page"] != "Unavailable"]
            if printed:
                printed_start, printed_end = printed[0], printed[-1]
                printed_range = f"{printed_start}–{printed_end}" if printed_start != printed_end else str(printed_start)
            else:
                printed_range = "Unavailable"
                
            pdf_range = f"{pdf_start}–{pdf_end}" if pdf_start != pdf_end else str(pdf_start)
            
            # Full content of this section (all pages merged in order)
            pages_sorted = sorted(pages, key=lambda x: x["pdf_page"])
            full_content_parts = []
            for p in pages_sorted:
                full_content_parts.append(f"--- [Physical PDF Page {p['pdf_page']} | Printed Book Page {p['printed_page']}] ---\n" + p.get("text", "").strip())
            full_section_content = "\n\n".join(full_content_parts)
            
            matched_sections.append({
                "book_name": b_name,
                "chapter_heading": ch_title,
                "section_heading": sec_title,
                "pdf_start": pdf_start,
                "pdf_end": pdf_end,
                "pdf_range": pdf_range,
                "printed_range": printed_range,
                "page_count": len(pages),
                "matching_pages": [p["pdf_page"] for p in pages if q_word_set.issubset(set(tokenize(p.get("search_text", ""))))],
                "score": round(score, 2),
                "full_content": full_section_content,
                "pages": pages_sorted
            })
            
        matched_sections.sort(key=lambda s: (-s["score"], s["pdf_start"]))
        results_by_book[b_name] = matched_sections

    return results_by_book

# Let's test on Matrix, Vector, Eigenvalues
for test_q in ["Matrix", "Vector", "Eigenvalues"]:
    res = search_sections(test_q)
    print(f"\n==============================================")
    print(f"SEARCH SECTIONS FOR '{test_q}':")
    for b_name, sec_list in res.items():
        print(f"Book: {b_name} -> {len(sec_list)} relevant sections")
        for idx, s in enumerate(sec_list[:3], 1):
            print(f"  [{idx}] Sec: {s['section_heading']} | Ch: {s['chapter_heading'][:30]} | PDF: {s['pdf_range']} | Printed: {s['printed_range']} | Score: {s['score']} | Total Pages: {s['page_count']}")
