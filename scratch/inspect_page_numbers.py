import pymupdf
import re
from pathlib import Path

grewal_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
kreyszig_path = Path("backend/books/advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1.pdf")

def inspect_printed_pages_grewal():
    doc = pymupdf.open(grewal_path)
    print("=== GREWAL PRINTED PAGE SAMPLES ===")
    # Check across various pages: 1-14 (preface/contents), 15 (ch1 start), 16, 17, 107, 115, 200, 900
    for p_num in [1, 5, 14, 15, 16, 17, 107, 108, 114, 115, 116, 169, 207, 500, 940, 950]:
        page = doc[p_num - 1]
        text = page.get_text("text")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Top line and bottom line
        top = lines[0] if lines else ""
        bottom = lines[-1] if lines else ""
        print(f"PDF {p_num}: top='{top}' | bottom='{bottom}'")

def inspect_printed_pages_kreyszig():
    doc = pymupdf.open(kreyszig_path)
    print("\n=== KREYSZIG PRINTED PAGE SAMPLES ===")
    for p_num in [1, 10, 20, 27, 28, 29, 280, 281, 282, 283, 284, 285, 289, 290, 500, 1200]:
        page = doc[p_num - 1]
        text = page.get_text("text")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        top = lines[0] if lines else ""
        bottom = lines[-1] if lines else ""
        print(f"PDF {p_num}: top='{top}' | bottom='{bottom}'")

if __name__ == "__main__":
    inspect_printed_pages_grewal()
    inspect_printed_pages_kreyszig()
