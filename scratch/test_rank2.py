import sys
import re
import math
import json
from pathlib import Path
import pymupdf

from scratch.test_full_pipeline import build_test_index

test_records = build_test_index()

def get_query_terms(query_words):
    terms = set(query_words)
    for w in query_words:
        terms.add(w)
        if w == "matrix":
            terms.add("matrices")
        elif w == "matrices":
            terms.add("matrix")
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

def search_in_records(query, records):
    def normalize_text(text):
        if not isinstance(text, str):
            return ""
        text = text.casefold()
        text = re.sub(r"[\u2010-\u2015]", "-", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def tokenize(text):
        return re.findall(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", normalize_text(text))

    normalized_query = normalize_text(query)
    query_words = tokenize(normalized_query)
    query_word_set = set(query_words)
    all_term_variants = get_query_terms(query_words)
    results = []

    for record in records:
        text = record.get("text", "")
        searchable_text = record.get("search_text", "")
        if not searchable_text:
            continue

        page_words = tokenize(searchable_text)
        page_word_set = set(page_words)
        matched_words = query_word_set.intersection(page_word_set)

        # EXACT original matching condition: require all distinct query words!
        if matched_words != query_word_set:
            continue

        # ----------------- RELEVANCE SCORING -----------------
        score = 100.0

        # Exact phrase bonus
        if normalized_query in searchable_text:
            score += 25.0

        # Term frequency (exact word matches of query and variants)
        exact_counts = 0
        for term in all_term_variants:
            exact_counts += len(re.findall(rf"\b{re.escape(term)}\b", searchable_text))

        score += min(exact_counts * 1.5, 40.0)

        ch = (record.get("chapter_heading") or "").lower()
        sec = (record.get("section_heading") or "").lower()

        # Heading relevance
        sec_has_topic = any(term in sec for term in all_term_variants)
        if sec_has_topic and "unavailable" not in sec:
            score += 50.0
            # Foundational / introductory sections boost (defines/introduces topic)
            if any(k in sec for k in ["introduction", "basic", "definition", "addition", "multiplication", "inversion"]):
                score += 25.0

        ch_has_topic = any(term in ch for term in all_term_variants)
        if ch_has_topic and "unavailable" not in ch:
            score += 35.0
            if sec_has_topic:
                score += 15.0

        # Boost if the topic appears in the very top lines (title of page/section)
        first_lines = " ".join(text.splitlines()[:5]).lower()
        if any(re.search(rf"\b{re.escape(term)}\b", first_lines) for term in all_term_variants):
            score += 20.0

        results.append({
            "book_name": record.get("book_name"),
            "file_path": record.get("file_path"),
            "pdf_page": record.get("pdf_page"),
            "printed_page": record.get("printed_page"),
            "chapter_heading": record.get("chapter_heading"),
            "section_heading": record.get("section_heading"),
            "text": text,
            "score": round(score, 2),
        })

    results.sort(
        key=lambda item: (
            -item["score"],
            item["book_name"].casefold(),
            item["pdf_page"] or 0,
        )
    )
    return results

matrix_res = search_in_records("Matrix", test_records)
print(f"\n==========================================")
print(f"RESULTS FOR 'Matrix': Total = {len(matrix_res)}")
print(f"==========================================")
for idx, r in enumerate(matrix_res[:15], 1):
    print(f"#{idx}: Book={r['book_name'][:25]} | PDF p.{r['pdf_page']} (Printed p.{r['printed_page']}) | Score={r['score']}")
    print(f"     Ch:  {r['chapter_heading']}")
    print(f"     Sec: {r['section_heading']}")
