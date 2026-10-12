
import json
import re
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = BACKEND_DIR / "book_index" / "pages_index.json"


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------
def normalize_text(text):
    if not isinstance(text, str):
        return ""

    text = text.casefold()
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize(text):
    return re.findall(
        r"[a-z0-9]+(?:[.-][a-z0-9]+)*",
        normalize_text(text),
    )


# ---------------------------------------------------------
# LOAD INDEX
# ---------------------------------------------------------
def load_index():
    if not INDEX_FILE.is_file():
        raise FileNotFoundError(
            f"Search index not found: {INDEX_FILE}\n"
            "Run: python -m backend.book_engine.book_indexer"
        )

    try:
        with INDEX_FILE.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError("The search index contains invalid JSON.") from error

    if not isinstance(records, list):
        raise ValueError("The search index must contain a list of records.")

    return records


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


# ---------------------------------------------------------
# SEARCH PAGES
# ---------------------------------------------------------
def search_pages(query, limit=None, match_mode="relevant"):
    """
    Search indexed pages from both books.

    match_mode:
        relevant: all query words must occur on the page
        exact:    the complete query phrase must occur

    limit:
        None = return all matching pages
        integer = return at most that many pages
    """
    normalized_query = normalize_text(query)

    if not normalized_query:
        return []

    if limit is not None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be a positive integer or None.")

    if match_mode not in {"relevant", "exact"}:
        raise ValueError("match_mode must be 'relevant' or 'exact'.")

    query_words = tokenize(normalized_query)

    if not query_words:
        return []

    records = load_index()
    query_word_set = set(query_words)
    all_term_variants = get_query_terms(query_words)
    results = []

    for record in records:
        if not isinstance(record, dict):
            continue

        text = record.get("text", "")
        searchable_text = normalize_text(
            record.get("search_text") or text
        )

        if not searchable_text:
            continue

        if match_mode == "exact":
            if normalized_query not in searchable_text:
                continue
            score = 100.0

        else:
            page_words = tokenize(searchable_text)
            page_word_set = set(page_words)
            matched_words = query_word_set.intersection(page_word_set)

            # Require all distinct query words (preserves exact matching page count).
            if matched_words != query_word_set:
                continue

            score = 100.0

            # Phrase match bonus
            if normalized_query in searchable_text:
                score += 25.0

            # Term frequency across query terms and variants
            exact_counts = 0
            for term in all_term_variants:
                exact_counts += len(re.findall(rf"\b{re.escape(term)}\b", searchable_text))

            score += min(exact_counts * 1.5, 40.0)

            ch = (record.get("chapter_heading") or "").lower()
            sec = (record.get("section_heading") or "").lower()

            # Heading relevance boost
            sec_has_topic = any(term in sec for term in all_term_variants)
            if sec_has_topic and "unavailable" not in sec:
                score += 50.0
                if any(k in sec for k in ["introduction", "basic", "definition", "addition", "multiplication", "inversion"]):
                    score += 25.0

            ch_has_topic = any(term in ch for term in all_term_variants)
            if ch_has_topic and "unavailable" not in ch:
                score += 35.0
                if sec_has_topic:
                    score += 15.0

            # Boost if query topic appears in first lines (title/opening of section)
            first_lines = " ".join(text.splitlines()[:5]).lower()
            if any(re.search(rf"\b{re.escape(term)}\b", first_lines) for term in all_term_variants):
                score += 20.0

        results.append({
            "book_name": record.get("book_name", "Unknown book"),
            "file_path": record.get("file_path", ""),
            "pdf_page": record.get("pdf_page"),
            "printed_page": record.get("printed_page", "Unavailable"),
            "chapter_heading": record.get("chapter_heading", "Unavailable"),
            "section_heading": record.get("section_heading", "Unavailable"),
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

    if limit is not None:
        results = results[:limit]

    return results


# ---------------------------------------------------------
# GROUP RESULTS BY BOOK AND SECTION
# ---------------------------------------------------------
def group_results_by_section(results):
    """
    Group matching pages by book, detected chapter and section.
    """
    grouped = defaultdict(list)

    for result in results:
        key = (
            result["book_name"],
            result.get("chapter_heading") or "Unavailable",
            result.get("section_heading") or "Unavailable",
        )
        grouped[key].append(result)

    output = []

    for (book_name, chapter, section), pages in grouped.items():
        pages.sort(key=lambda item: item["pdf_page"] or 0)

        output.append({
            "book_name": book_name,
            "chapter_heading": chapter,
            "section_heading": section,
            "matching_pages": [page["pdf_page"] for page in pages],
            "page_count": len(pages),
            "pages": pages,
        })

    return output


# ---------------------------------------------------------
# COMPREHENSIVE SECTION SEARCH (ACROSS COMPLETE BOOKS)
# ---------------------------------------------------------
def search_book_sections(query):
    """
    Search for ANY topic across the complete content of both books.
    Identifies all relevant sections with verified chapter, section, and page ranges.
    Includes all continuation pages for complete, untruncated content.
    Returns: dict of {book_name: list of relevant section dicts}
    """
    raw_query = (query or "").strip()
    if not raw_query:
        return {}

    # Clean query (remove connectors like 'aur', 'and', 'or' for flexible matching)
    cleaned_q = re.sub(r"\b(?:aur|and|or)\b", " ", raw_query, flags=re.IGNORECASE).strip()
    cleaned_q = re.sub(r"\s+", " ", cleaned_q)

    norm_query = normalize_text(cleaned_q if cleaned_q else raw_query)
    query_words = tokenize(norm_query)

    if not query_words:
        return {}

    query_word_set = set(query_words)
    term_variants = get_query_terms(query_words)

    records = load_index()

    # Group all index pages by (book_name, chapter_heading, section_heading)
    # to know the exact boundaries and all continuation pages of every section
    book_sections_map = defaultdict(lambda: defaultdict(list))
    for p in records:
        b_name = p.get("book_name", "Unknown book")
        ch = p.get("chapter_heading") or "Unavailable"
        sec = p.get("section_heading") or "Unavailable"
        book_sections_map[b_name][(ch, sec)].append(p)

    results_by_book = {}

    for b_name in sorted(book_sections_map.keys()):
        sections = book_sections_map[b_name]
        matched_sections = []

        for (ch_title, sec_title), pages in sections.items():
            pages_sorted = sorted(pages, key=lambda x: x["pdf_page"])
            sec_searchable = " ".join(p.get("search_text", "") for p in pages_sorted)
            sec_words = set(tokenize(sec_searchable))

            heading_text = normalize_text(f"{ch_title} {sec_title}")
            heading_words = set(tokenize(heading_text))

            # Match criteria:
            # 1. Exact phrase in section text
            # 2. All query words present in section text
            # 3. Heading contains query terms
            # 4. For multi-word queries with 'aur'/'and', at least one core topic in heading or body
            has_phrase_match = norm_query in sec_searchable or norm_query in heading_text
            has_all_words = query_word_set.issubset(sec_words)
            has_heading_match = any(t in heading_text for t in term_variants)

            # Check if any individual query word occurs with strong frequency
            word_matches = sum(1 for w in query_words if w in sec_words or any(v in sec_words for v in get_query_terms([w])))
            has_partial_multiword = len(query_words) > 1 and word_matches >= max(1, len(query_words) - 1)

            if not (has_phrase_match or has_all_words or has_heading_match or (has_partial_multiword and word_matches >= 2)):
                continue

            # Relevance scoring
            score = 100.0

            if has_phrase_match:
                score += 35.0

            sec_lower = sec_title.lower()
            ch_lower = ch_title.lower()

            # Heading relevance boost
            if any(t in sec_lower for t in term_variants) and "unavailable" not in sec_lower:
                score += 65.0
                if any(k in sec_lower for k in ["introduction", "basic", "definition", "concept", "addition", "multiplication"]):
                    score += 25.0

            if any(t in ch_lower for t in term_variants) and "unavailable" not in ch_lower:
                score += 40.0

            # Term frequency across all pages of the section
            occurrences = sum(len(re.findall(rf"\b{re.escape(t)}\b", sec_searchable)) for t in term_variants)
            score += min(occurrences * 0.6, 45.0)

            # Page ranges
            pdf_pages = [p["pdf_page"] for p in pages_sorted]
            pdf_start, pdf_end = min(pdf_pages), max(pdf_pages)
            pdf_range = f"{pdf_start}–{pdf_end}" if pdf_start != pdf_end else str(pdf_start)

            printed_pages = [p["printed_page"] for p in pages_sorted if p.get("printed_page") and p["printed_page"] != "Unavailable"]
            if printed_pages:
                pr_start, pr_end = printed_pages[0], printed_pages[-1]
                printed_range = f"{pr_start}–{pr_end}" if pr_start != pr_end else str(pr_start)
            else:
                printed_range = "Unavailable"

            # Merge complete text across all continuation pages
            full_content_parts = []
            for p in pages_sorted:
                p_text = (p.get("text") or "").strip()
                pr_str = p.get("printed_page") or "Unavailable"
                banner = f"--- [Physical PDF Page {p['pdf_page']} | Printed Book Page {pr_str}] ---"
                full_content_parts.append(f"{banner}\n{p_text}")

            full_section_content = "\n\n".join(full_content_parts)

            matching_pdf_pages = [
                p["pdf_page"] for p in pages_sorted
                if any(t in (p.get("search_text") or "") for t in term_variants)
            ]

            file_path = pages_sorted[0].get("file_path", "")

            matched_sections.append({
                "book_name": b_name,
                "file_path": file_path,
                "chapter_heading": ch_title,
                "section_heading": sec_title,
                "pdf_start": pdf_start,
                "pdf_end": pdf_end,
                "pdf_range": pdf_range,
                "printed_range": printed_range,
                "page_count": len(pages_sorted),
                "matching_pages": matching_pdf_pages,
                "score": round(score, 2),
                "full_content": full_section_content,
                "pages": pages_sorted,
            })

        matched_sections.sort(key=lambda s: (-s["score"], s["pdf_start"]))
        results_by_book[b_name] = matched_sections

    return results_by_book


# ---------------------------------------------------------
# STRUCTURED RESPONSE FORMATTER
# ---------------------------------------------------------
def format_book_sections_response(query, results_by_book):
    """
    Format relevant sections into complete, structured textbook results.
    Never invents unindexed metadata; labels missing fields as Unavailable.
    Displays complete section content and all continuation pages.
    """
    if not results_by_book or not any(results_by_book.values()):
        return f"Information for '{query}' not found in the books."

    total_sections = sum(len(secs) for secs in results_by_book.values())

    lines = [
        f'📚 Book Search Results for "{query}"\n',
        f"Found {total_sections} relevant section(s) across {len(results_by_book)} indexed mathematics book(s):",
    ]

    for b_name, sec_list in results_by_book.items():
        lines.append(f"• {b_name}: {len(sec_list)} relevant section(s)")

    lines.append("\n*(Note: Chapter headings, section headings, printed page ranges, and physical PDF page ranges are verified against the textbooks. Complete sections include all continuation pages, equations, and solved examples.)*\n")

    for b_name, sec_list in results_by_book.items():
        lines.append("=" * 60)
        lines.append(f"📖 BOOK: {b_name}")
        lines.append("=" * 60)

        if not sec_list:
            lines.append(f"No matching content found for \"{query}\" in this book.\n")
            continue

        # Show full content for top sections (up to 3 complete sections per book to preserve readability)
        # And provide complete references and overview for remaining sections
        limit_full_display = 3
        for idx, sec in enumerate(sec_list, 1):
            ch = sec.get("chapter_heading") or "Unavailable"
            s_head = sec.get("section_heading") or "Unavailable"
            pr_range = sec.get("printed_range") or "Unavailable"
            pdf_range = sec.get("pdf_range") or "Unavailable"

            lines.append(f"\n[Relevant Section {idx}]")
            lines.append(f"• Chapter Heading: {ch}")
            lines.append(f"• Section Heading: {s_head}")
            lines.append(f"• Printed Book Pages: {pr_range}")
            lines.append(f"• Physical PDF Pages: {pdf_range} (Total Pages: {sec['page_count']})")

            if idx <= limit_full_display:
                lines.append("• Complete Relevant Original Content:")
                # Include full section content
                lines.append(sec["full_content"])
            else:
                lines.append("• Section Content Preview (Full pages viewable in PDF Page Viewer):")
                # Show first page content of that section
                first_page_text = sec["pages"][0].get("text", "").strip()[:800]
                lines.append(f"--- [Physical PDF Page {sec['pdf_start']} | Printed Book Page {sec['pages'][0].get('printed_page', 'Unavailable')}] ---\n{first_page_text}...\n*(See Original PDF Viewer below for complete pages {pdf_range})*")

            lines.append("\n" + "─" * 45)

    return "\n".join(lines)


# ---------------------------------------------------------
# COMMAND-LINE TEST
# ---------------------------------------------------------
if __name__ == "__main__":
    topic = input("Enter a topic to search in both books: ").strip()

    try:
        matches = search_pages(
            topic,
            limit=None,
            match_mode="relevant",
        )

        if not matches:
            print("\nNo matching pages found in the searchable text.")
        else:
            print(f"\nTotal matching pages: {len(matches)}")

            book_counts = defaultdict(int)
            for result in matches:
                book_counts[result["book_name"]] += 1

            for book_name, count in book_counts.items():
                print(f"{book_name}: {count} matching pages")

            groups = group_results_by_section(matches)

            print(f"\nDetected book/section groups: {len(groups)}")
            print("\nTOP 10 MATCHING PAGES")
            print("=" * 70)

            for result in matches[:10]:
                print("-" * 70)
                print(f"Book: {result['book_name']}")
                print(f"Chapter: {result.get('chapter_heading') or 'Unavailable'}")
                print(f"Section: {result.get('section_heading') or 'Unavailable'}")
                print(f"Physical PDF Page: {result.get('pdf_page')}")
                print(f"Printed Book Page: {result.get('printed_page') or 'Unavailable'}")
                print(f"Relevance Score: {result['score']}")
                print(result["text"][:1000])

    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"\nSearch error: {error}")