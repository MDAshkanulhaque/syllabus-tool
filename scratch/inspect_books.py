import pymupdf
import re
from pathlib import Path

grewal_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
kreyszig_path = Path("backend/books/advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1.pdf")

def inspect_grewal():
    doc = pymupdf.open(grewal_path)
    print("GREWAL total pages:", len(doc))
    for page_num in [15, 16, 17, 107, 108, 115, 116, 117, 118]:
        page = doc[page_num - 1]
        text = page.get_text("text")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        print(f"--- Grewal PDF Page {page_num} ---")
        print("First 5 lines:", lines[:5])
        print("Last 3 lines:", lines[-3:])

def inspect_kreyszig():
    doc = pymupdf.open(kreyszig_path)
    print("\nKREYSZIG total pages:", len(doc))
    for page_num in [280, 281, 282, 283, 284, 285, 289]:
        page = doc[page_num - 1]
        text = page.get_text("text")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        print(f"--- Kreyszig PDF Page {page_num} ---")
        print("First 5 lines:", lines[:5])
        print("Last 3 lines:", lines[-3:])

if __name__ == "__main__":
    inspect_grewal()
    inspect_kreyszig()
