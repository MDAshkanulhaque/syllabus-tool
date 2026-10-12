import sys
import re
import math
import json
from pathlib import Path
import pymupdf

def build_test_index():
    books_dir = Path("backend/books")
    records = []
    
    for pdf_path in sorted(books_dir.glob("*.pdf")):
        book_name = pdf_path.stem
        print(f"Indexing {book_name}...")
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        
        # 1. Page labels (printed page numbers)
        page_labels = []
        for i in range(total_pages):
            lbl = doc[i].get_label()
            # Verify if valid printed decimal page number
            if lbl and lbl.isdigit():
                # Cross-verify with known textbook offset or text
                page_labels.append(lbl)
            else:
                page_labels.append("Unavailable")
                
        # 2. Extract Headings
        toc = doc.get_toc()
        chapters_in_toc = [item for item in toc if item[0] == 2 and "chapter" in item[1].lower()]
        sections_in_toc = [item for item in toc if item[0] == 3 and re.match(r"^\d+\.\d+", item[1].strip())]
        
        page_headings = [{} for _ in range(total_pages)]
        
        if len(chapters_in_toc) >= 5:
            # Kreyszig via TOC outline
            # Also find where Level 1 stops regular chapters (Appendices/Index)
            appendices_in_toc = [item for item in toc if item[0] == 1 and any(w in item[1].lower() for w in ["appendix", "app.", "index", "photo credits"])]
            last_allowed_page = appendices_in_toc[0][2] - 1 if appendices_in_toc else total_pages
            
            chapters_sorted = sorted(chapters_in_toc, key=lambda x: x[2])
            sections_sorted = sorted(sections_in_toc, key=lambda x: x[2])
            
            for p_idx in range(total_pages):
                p_num = p_idx + 1
                if p_num < chapters_sorted[0][2] or p_num > last_allowed_page:
                    page_headings[p_idx] = {
                        "chapter_heading": "Unavailable",
                        "section_heading": "Unavailable"
                    }
                    continue
                    
                ch_title = "Unavailable"
                for i, ch in enumerate(chapters_sorted):
                    start = ch[2]
                    end = chapters_sorted[i+1][2] if i + 1 < len(chapters_sorted) else (last_allowed_page + 1)
                    if start <= p_num < end:
                        ch_title = ch[1].strip()
                        break
                        
                sec_title = "Unavailable"
                for i, sec in enumerate(sections_sorted):
                    start = sec[2]
                    end = sections_sorted[i+1][2] if i + 1 < len(sections_sorted) else (last_allowed_page + 1)
                    if start <= p_num < end:
                        sec_raw = sec[1].strip()
                        sec_match = re.match(r"^(\d+)\.", sec_raw)
                        ch_match = re.search(r"Chapter\s+(\d+)", ch_title, re.IGNORECASE)
                        if sec_match and ch_match and sec_match.group(1) != ch_match.group(1):
                            sec_title = "Unavailable"
                        else:
                            sec_title = sec_raw
                        break
                        
                page_headings[p_idx] = {
                    "chapter_heading": ch_title,
                    "section_heading": sec_title
                }
        else:
            # Grewal via text extraction
            chapters = []
            for p_idx in range(total_pages):
                p_num = p_idx + 1
                text = doc[p_idx].get_text("text")
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                for idx, line in enumerate(lines[:6]):
                    m = re.match(r"^C\s*H\s*A\s*P\s*T\s*E\s*R\s*(\d+)$", line, re.IGNORECASE)
                    if m:
                        ch_num = int(m.group(1))
                        title_parts = []
                        for next_line in lines[idx+1:idx+4]:
                            if any(w in next_line.lower() for w in ["chapter objectives", "introduction", "unit", "contents"]):
                                break
                            title_parts.append(next_line)
                        title = " ".join(title_parts).strip()
                        full_ch_title = f"Chapter {ch_num}: {title.title()}" if title else f"Chapter {ch_num}"
                        chapters.append((p_num, ch_num, full_ch_title))
                        break
                        
            # Back matter in Grewal starts around page 931
            last_allowed_page = 930
            for c_idx, (ch_start, ch_num, ch_title) in enumerate(chapters):
                ch_end = chapters[c_idx + 1][0] if c_idx + 1 < len(chapters) else (last_allowed_page + 1)
                
                sections = []
                for p_num in range(ch_start, ch_end):
                    text = doc[p_num - 1].get_text("text")
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    for line in lines:
                        m = re.match(rf"^({ch_num}\.\d{{1,2}})\s+([A-Z][a-zA-Z0-9\s\-\,\(\)\/\–\—\:\.]{{2,80}})$", line)
                        if m:
                            sec_num = m.group(1)
                            sec_title = m.group(2).strip()
                            if not any(bad in sec_title for bad in ["=", "+", "dx", "dt", "Table", "Fig", "Example"]):
                                if not any(s[1] == sec_num for s in sections):
                                    sections.append((p_num, sec_num, f"{sec_num} {sec_title}"))
                                    
                for p_num in range(ch_start, ch_end):
                    p_idx = p_num - 1
                    sec_assigned = "Unavailable"
                    for s_idx, (s_start, s_num, s_title) in enumerate(sections):
                        s_end = sections[s_idx + 1][0] if s_idx + 1 < len(sections) else ch_end
                        if s_start <= p_num < s_end:
                            sec_assigned = s_title
                            break
                    page_headings[p_idx] = {
                        "chapter_heading": ch_title,
                        "section_heading": sec_assigned
                    }
                    
            first_ch_start = chapters[0][0] if chapters else total_pages + 1
            for p_idx in range(first_ch_start - 1):
                page_headings[p_idx] = {"chapter_heading": "Unavailable", "section_heading": "Unavailable"}
            for p_idx in range(last_allowed_page, total_pages):
                page_headings[p_idx] = {"chapter_heading": "Unavailable", "section_heading": "Unavailable"}
                
        # Build records
        for p_idx in range(total_pages):
            page_text = doc[p_idx].get_text("text")
            
            # Text normalization matching original
            norm_text = page_text.casefold()
            norm_text = re.sub(r"[\u2010-\u2015]", "-", norm_text)
            norm_text = re.sub(r"\s+", " ", norm_text).strip()
            
            records.append({
                "book_name": book_name,
                "file_path": str(pdf_path.resolve()),
                "pdf_page": p_idx + 1,
                "printed_page": page_labels[p_idx],
                "text": page_text,
                "search_text": norm_text,
                "has_text": bool(page_text.strip()),
                "chapter_heading": page_headings[p_idx]["chapter_heading"],
                "section_heading": page_headings[p_idx]["section_heading"]
            })
            
    print(f"Total pages indexed: {len(records)}")
    return records

test_records = build_test_index()

# Test searching
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
    results = []

    # Query variations / synonyms for topic relevance
    topic_roots = [w.rstrip("s") for w in query_words if len(w) > 3]

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

        # Term frequency (exact word matches)
        exact_counts = 0
        for qw in query_words:
            # Count exact word matches
            exact_counts += len(re.findall(rf"\b{re.escape(qw)}\b", searchable_text))
            # Also count plural/singular
            if qw.endswith("s"):
                exact_counts += len(re.findall(rf"\b{re.escape(qw[:-1])}\b", searchable_text))
            elif qw == "matrix":
                exact_counts += len(re.findall(r"\bmatrices\b", searchable_text))

        # Add term frequency score (capped at 40 points)
        score += min(exact_counts * 1.5, 40.0)

        ch = (record.get("chapter_heading") or "").lower()
        sec = (record.get("section_heading") or "").lower()

        # Heading relevance
        # Section heading contains query word or root
        sec_has_topic = any(qw in sec or (root and root in sec) for qw in query_words for root in topic_roots)
        if sec_has_topic and "unavailable" not in sec:
            score += 50.0
            # Foundational / introductory sections boost
            if any(k in sec for k in ["introduction", "basic", "definition", "addition", "multiplication", "inversion"]):
                score += 20.0

        # Chapter heading contains query word or root
        ch_has_topic = any(qw in ch or (root and root in ch) for qw in query_words for root in topic_roots)
        if ch_has_topic and "unavailable" not in ch:
            score += 35.0
            # If both chapter and section are dedicated to topic
            if sec_has_topic:
                score += 15.0

        # Boost if the topic appears in the very top lines (title of page/section)
        first_lines = " ".join(text.splitlines()[:5]).lower()
        if any(re.search(rf"\b{re.escape(qw)}\b", first_lines) for qw in query_words):
            score += 15.0

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

vector_res = search_in_records("Vector", test_records)
print(f"\n==========================================")
print(f"RESULTS FOR 'Vector': Total = {len(vector_res)}")
print(f"==========================================")
for idx, r in enumerate(vector_res[:10], 1):
    print(f"#{idx}: Book={r['book_name'][:25]} | PDF p.{r['pdf_page']} (Printed p.{r['printed_page']}) | Score={r['score']}")
    print(f"     Ch:  {r['chapter_heading']}")
    print(f"     Sec: {r['section_heading']}")
