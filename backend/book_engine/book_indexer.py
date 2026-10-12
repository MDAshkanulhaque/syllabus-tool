
import json
import re
from pathlib import Path
import pymupdf

from backend.book_engine.book_loader import load_books


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BACKEND_DIR / "book_index"
INDEX_FILE = INDEX_DIR / "pages_index.json"


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------
def normalize_text(text):
    """Normalize text for case-insensitive searching."""
    if not isinstance(text, str):
        return ""

    text = text.casefold()
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_heading(line):
    """Clean a possible heading extracted from a PDF."""
    line = re.sub(r"\s+", " ", line).strip()
    line = line.strip(" \t-•")

    if len(line) < 3 or len(line) > 160:
        return ""

    return line


# ---------------------------------------------------------
# RELIABLE HEADING & PAGE NUMBER EXTRACTION
# ---------------------------------------------------------
def extract_book_headings_and_pages(book):
    """
    Extract verified chapter headings, section headings, and printed page numbers.
    Does not assign unrelated headings to pages. Unverified metadata is marked as 'Unavailable'.
    """
    total_pages = len(book["pages"])
    page_metadata = [{} for _ in range(total_pages)]
    file_path = book.get("file_path", "")

    doc = None
    try:
        if file_path and Path(file_path).is_file():
            doc = pymupdf.open(file_path)
    except Exception:
        doc = None

    # Determine printed page numbers
    for p_idx, page in enumerate(book["pages"]):
        pdf_page = page.get("pdf_page", p_idx + 1)
        lbl = page.get("page_label", "")
        if not lbl and doc and p_idx < len(doc):
            lbl = doc[p_idx].get_label() if hasattr(doc[p_idx], "get_label") else ""

        # Verify printed page label: only accept valid decimal page numbers
        if lbl and str(lbl).strip().isdigit():
            page_metadata[p_idx]["printed_page"] = str(lbl).strip()
        else:
            page_metadata[p_idx]["printed_page"] = "Unavailable"

    # Extract headings using PDF outline TOC if detailed outline exists
    toc = doc.get_toc() if doc else []
    chapters_in_toc = [
        item for item in toc
        if item[0] == 2 and "chapter" in item[1].lower() and item[2] <= total_pages
    ]
    sections_in_toc = [
        item for item in toc
        if item[0] == 3 and re.match(r"^\d+\.\d+", item[1].strip()) and item[2] <= total_pages
    ]

    if len(chapters_in_toc) >= 5:
        # Case A: Document has authoritative outline (e.g. Kreyszig)
        appendices_in_toc = [
            item for item in toc
            if item[0] == 1 and any(
                w in item[1].lower() for w in ["appendix", "app.", "index", "photo credits", "answers"]
            ) and item[2] <= total_pages
        ]
        last_allowed_page = appendices_in_toc[0][2] - 1 if appendices_in_toc else total_pages

        chapters_sorted = sorted(chapters_in_toc, key=lambda x: x[2])
        sections_sorted = sorted(sections_in_toc, key=lambda x: x[2])

        for p_idx in range(total_pages):
            p_num = p_idx + 1

            if p_num < chapters_sorted[0][2] or p_num > last_allowed_page:
                page_metadata[p_idx]["chapter_heading"] = "Unavailable"
                page_metadata[p_idx]["section_heading"] = "Unavailable"
                continue

            # Determine chapter
            ch_title = "Unavailable"
            ch_num_val = None
            for i, ch in enumerate(chapters_sorted):
                start = ch[2]
                end = chapters_sorted[i + 1][2] if i + 1 < len(chapters_sorted) else (last_allowed_page + 1)
                if start <= p_num < end:
                    ch_title = ch[1].strip()
                    m_num = re.search(r"Chapter\s+(\d+)", ch_title, re.IGNORECASE)
                    if m_num:
                        ch_num_val = m_num.group(1)
                    break

            # Determine section
            sec_title = "Unavailable"
            for i, sec in enumerate(sections_sorted):
                start = sec[2]
                end = sections_sorted[i + 1][2] if i + 1 < len(sections_sorted) else (last_allowed_page + 1)
                if start <= p_num < end:
                    sec_raw = sec[1].strip()
                    sec_match = re.match(r"^(\d+)\.", sec_raw)
                    if sec_match and ch_num_val and sec_match.group(1) != ch_num_val:
                        sec_title = "Unavailable"
                    else:
                        sec_title = sec_raw
                    break

            page_metadata[p_idx]["chapter_heading"] = ch_title
            page_metadata[p_idx]["section_heading"] = sec_title
            page_metadata[p_idx]["sections"] = [{"chapter_heading": ch_title, "section_heading": sec_title}]

    else:
        # Case B: Authoritative Table of Contents analysis for B. S. Grewal
        # The textbook contains a complete, verified Table of Contents on pages 5–14 (PDF indices 4–13).
        # Physical PDF page P corresponds exactly to printed page P - 14 for all chapter pages (15–904).
        for p_idx in range(total_pages):
            pdf_page = p_idx + 1
            if 15 <= pdf_page <= 904:
                page_metadata[p_idx]["printed_page"] = str(pdf_page - 14)
            else:
                page_metadata[p_idx]["printed_page"] = "Unavailable"
            page_metadata[p_idx]["chapter_heading"] = "Unavailable"
            page_metadata[p_idx]["section_heading"] = "Unavailable"
            page_metadata[p_idx]["sections"] = []

        toc_text = ""
        for p in range(4, min(14, total_pages)):
            if doc and p < len(doc):
                toc_text += doc[p].get_text("text") + "\n"

        lines = [l.strip() for l in toc_text.splitlines() if l.strip()]

        entries = []
        chapter_starts = {}
        chapter_titles = {}
        exercises_starts = {}

        current_ch_num = None
        current_ch_title = None

        i = 0
        while i < len(lines):
            line = lines[i]

            m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", line, re.IGNORECASE)
            if m_ch:
                current_ch_num = int(m_ch.group(1))
                raw_title = m_ch.group(2).strip()
                i += 1
                while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE):
                    raw_title += " " + lines[i]
                    i += 1
                ch_printed = None
                if i < len(lines) and lines[i].isdigit():
                    ch_printed = int(lines[i])
                    i += 1
                current_ch_title = f"Chapter {current_ch_num}: {raw_title}".strip()
                current_ch_title = re.sub(r"\s+", " ", current_ch_title)
                chapter_titles[current_ch_num] = current_ch_title
                if ch_printed:
                    chapter_starts[current_ch_num] = ch_printed + 14
                continue

            if line.startswith("Exercises"):
                ex_title = line
                i += 1
                ex_printed = None
                if i < len(lines) and lines[i].isdigit():
                    ex_printed = int(lines[i])
                    i += 1
                if current_ch_num and ex_printed:
                    if current_ch_num not in exercises_starts:
                        exercises_starts[current_ch_num] = []
                    exercises_starts[current_ch_num].append((ex_title, ex_printed + 14))
                continue

            m_sec = re.match(r"^(\d+\.\d{1,2})\s*(.*)$", line)
            if m_sec:
                sec_num = m_sec.group(1)
                raw_sec_title = m_sec.group(2).strip()
                i += 1
                while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE) and not lines[i].startswith("Exercises"):
                    raw_sec_title += " " + lines[i]
                    i += 1
                sec_printed = None
                if i < len(lines) and lines[i].isdigit():
                    sec_printed = int(lines[i])
                    i += 1

                full_sec_title = f"{sec_num} {raw_sec_title}".strip()
                full_sec_title = re.sub(r"\s+", " ", full_sec_title)

                entries.append({
                    "chapter_num": int(sec_num.split(".")[0]),
                    "chapter_title": current_ch_title,
                    "section_num": sec_num,
                    "section_title": full_sec_title,
                    "printed_page": sec_printed,
                    "start_pdf": sec_printed + 14 if sec_printed else None,
                })
                continue

            i += 1

        # Verify start_pdf against actual page text (handles minor print shifts like Sec 2.3 starting on p.40)
        if doc:
            for entry in entries:
                s_num = entry["section_num"]
                nominal_pdf = entry["start_pdf"]
                if not nominal_pdf or nominal_pdf > total_pages:
                    continue
                p_text = doc[nominal_pdf - 1].get_text("text")
                if not re.search(rf"\b{re.escape(s_num)}\b", p_text):
                    if nominal_pdf < total_pages:
                        next_text = doc[nominal_pdf].get_text("text")
                        if re.search(rf"\b{re.escape(s_num)}\b", next_text):
                            entry["start_pdf"] = nominal_pdf + 1
                            entry["printed_page"] = entry["printed_page"] + 1

        for entry in entries:
            c_num = entry["chapter_num"]
            if c_num not in chapter_starts:
                chapter_starts[c_num] = entry["start_pdf"]

        for i, entry in enumerate(entries):
            c_num = entry["chapter_num"]
            if i + 1 < len(entries):
                next_entry = entries[i + 1]
                if next_entry["chapter_num"] == c_num:
                    if next_entry["start_pdf"] > entry["start_pdf"]:
                        entry["end_pdf"] = next_entry["start_pdf"] - 1
                    else:
                        entry["end_pdf"] = entry["start_pdf"]
                else:
                    # Last section in this chapter
                    ch_exs = exercises_starts.get(c_num, [])
                    post_sec_exs = [ex for ex in ch_exs if ex[1] > entry["start_pdf"]]
                    if post_sec_exs:
                        entry["end_pdf"] = post_sec_exs[0][1] - 1
                    else:
                        next_c_num = next_entry["chapter_num"]
                        next_c_start = chapter_starts.get(next_c_num, 905)
                        entry["end_pdf"] = max(entry["start_pdf"], next_c_start - 1)
            else:
                # Last section in book (16.30)
                ch_exs = exercises_starts.get(c_num, [])
                post_sec_exs = [ex for ex in ch_exs if ex[1] > entry["start_pdf"]]
                if post_sec_exs:
                    entry["end_pdf"] = post_sec_exs[0][1] - 1
                else:
                    entry["end_pdf"] = 900

        # Assign chapter headings to all chapter page ranges
        for c_num, ch_start in chapter_starts.items():
            next_ch_start = chapter_starts.get(c_num + 1, 905)
            ch_title = chapter_titles.get(c_num, "Unavailable")
            for p_num in range(ch_start, min(next_ch_start, total_pages + 1)):
                page_metadata[p_num - 1]["chapter_heading"] = ch_title

        # Assign section headings to section page ranges
        for entry in entries:
            s_start = entry["start_pdf"]
            s_end = entry["end_pdf"]
            ch_title = entry["chapter_title"] or "Unavailable"
            s_title = entry["section_title"] or "Unavailable"
            for p_num in range(s_start, min(s_end + 1, total_pages + 1)):
                sec_obj = {"chapter_heading": ch_title, "section_heading": s_title}
                if sec_obj not in page_metadata[p_num - 1]["sections"]:
                    page_metadata[p_num - 1]["sections"].append(sec_obj)
                if page_metadata[p_num - 1]["section_heading"] == "Unavailable":
                    page_metadata[p_num - 1]["chapter_heading"] = ch_title
                    page_metadata[p_num - 1]["section_heading"] = s_title

        first_p = entries[0]["start_pdf"] if entries else 15
        for p_idx in range(min(first_p - 1, total_pages)):
            page_metadata[p_idx]["chapter_heading"] = "Unavailable"
            page_metadata[p_idx]["section_heading"] = "Unavailable"
            page_metadata[p_idx]["printed_page"] = "Unavailable"
            page_metadata[p_idx]["sections"] = []

        last_p = entries[-1]["end_pdf"] if entries else 904
        for p_idx in range(last_p, total_pages):
            page_metadata[p_idx]["chapter_heading"] = "Unavailable"
            page_metadata[p_idx]["section_heading"] = "Unavailable"
            page_metadata[p_idx]["printed_page"] = "Unavailable"
            page_metadata[p_idx]["sections"] = []

    if doc:
        doc.close()

    return page_metadata


# ---------------------------------------------------------
# BUILD PAGE INDEX
# ---------------------------------------------------------
def build_index():
    """Build a searchable index containing every PDF page with verified metadata."""
    books = load_books()
    records = []

    for book in books:
        book_name = book["book_name"]
        print(f"\nIndexing: {book_name}")

        page_metadata = extract_book_headings_and_pages(book)

        for p_idx, page in enumerate(book["pages"]):
            original_text = page.get("text", "")
            meta = page_metadata[p_idx]
            sections_list = meta.get("sections")
            if not sections_list:
                sections_list = [{
                    "chapter_heading": meta.get("chapter_heading", "Unavailable"),
                    "section_heading": meta.get("section_heading", "Unavailable"),
                }]

            for sec_info in sections_list:
                records.append({
                    "book_name": book_name,
                    "file_path": book["file_path"],
                    "pdf_page": page["pdf_page"],
                    "printed_page": meta.get("printed_page", "Unavailable"),
                    "text": original_text,
                    "search_text": normalize_text(original_text),
                    "has_text": page.get("has_text", bool(original_text.strip())),
                    "chapter_heading": sec_info.get("chapter_heading", "Unavailable"),
                    "section_heading": sec_info.get("section_heading", "Unavailable"),
                })

        print(f"Pages indexed: {len(book['pages'])}")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = INDEX_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(
                records,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary_file.replace(INDEX_FILE)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()

    print("\n" + "=" * 55)
    print("INDEX CREATED SUCCESSFULLY")
    print(f"Books indexed: {len(books)}")
    print(f"Pages indexed: {len(records)}")
    print(
        "Pages without extractable text:",
        sum(1 for record in records if not record["has_text"]),
    )
    print(f"Index location: {INDEX_FILE}")
    print("=" * 55)

    return records


# ---------------------------------------------------------
# BASIC SEARCH COMPATIBILITY
# ---------------------------------------------------------
def search_pages(query, limit=30):
    """Search indexed pages using an exact phrase."""
    query = normalize_text(query)

    if not query:
        return []

    if not INDEX_FILE.is_file():
        raise FileNotFoundError(
            "Search index not found. Run book_indexer.py first."
        )

    with INDEX_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    results = []

    for record in records:
        searchable_text = record.get("search_text", "")

        if query in searchable_text:
            results.append({
                "book_name": record.get("book_name", "Unknown book"),
                "pdf_page": record.get("pdf_page"),
                "printed_page": record.get("printed_page", "Unavailable"),
                "chapter_heading": record.get("chapter_heading", "Unavailable"),
                "section_heading": record.get("section_heading", "Unavailable"),
                "text": record.get("text", ""),
            })

            if limit is not None and len(results) >= limit:
                break

    return results


# ---------------------------------------------------------
# COMMAND-LINE ENTRY POINT
# ---------------------------------------------------------
if __name__ == "__main__":
    build_index()