
from pathlib import Path
import pymupdf


# Project paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
BOOKS_DIR = BACKEND_DIR / "books"


def load_books():
    """
    Load every PDF from backend/books.
    Preserve each page's extracted text and PDF page number.
    Original PDF files are never modified.
    """
    books = []

    if not BOOKS_DIR.is_dir():
        raise FileNotFoundError(
            f"Books folder not found: {BOOKS_DIR}"
        )

    pdf_files = sorted(
        path for path in BOOKS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF books found in: {BOOKS_DIR}"
        )

    for pdf_path in pdf_files:
        print(f"\nReading: {pdf_path.name}")

        try:
            with pymupdf.open(pdf_path) as pdf:
                if pdf.is_encrypted:
                    print("Skipped: PDF is encrypted.")
                    continue

                pages = []

                for page_index, page in enumerate(pdf):
                    page_text = page.get_text("text")
                    label = page.get_label() if hasattr(page, "get_label") else ""

                    pages.append({
                        "pdf_page": page_index + 1,
                        "page_label": label or "",
                        "text": page_text,
                        "has_text": bool(page_text.strip()),
                    })

                books.append({
                    "book_name": pdf_path.stem,
                    "file_path": str(pdf_path.resolve()),
                    "total_pages": len(pages),
                    "pages": pages,
                })

                empty_pages = sum(
                    1 for page in pages if not page["has_text"]
                )

                print(f"Loaded successfully: {pdf_path.name}")
                print(f"Total pages: {len(pages)}")
                print(f"Pages without extractable text: {empty_pages}")

        except (pymupdf.FileDataError, OSError) as error:
            print(f"Could not read {pdf_path.name}: {error}")
            continue

    if not books:
        raise RuntimeError(
            "No readable PDF books were loaded. "
            "Check the PDFs in the books folder."
        )

    return books


if __name__ == "__main__":
    loaded_books = load_books()

    total_pages = sum(
        book["total_pages"] for book in loaded_books
    )

    print("\n" + "=" * 40)
    print(f"Total books loaded: {len(loaded_books)}")
    print(f"Total PDF pages: {total_pages}")
    print("=" * 40)
