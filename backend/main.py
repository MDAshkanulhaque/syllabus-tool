from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import fitz
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

from subject_detector import extract_subject_candidates
from qa_engine import AcademicSyllabusQAEngine
from book_engine.internet_books import (
    search_internet_books,
    is_safe_download_url,
    clean_search_query,
    get_book_readable_content
)



app = FastAPI(title="Syllabus Extraction & Chatbot Backend")


# Upload folder
_backend_uploads = os.path.join(os.path.dirname(__file__), "uploads")
UPLOAD_DIR = _backend_uploads if os.path.isdir(_backend_uploads) else "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory document QA engines cache
DOCUMENT_ENGINES = {}
LATEST_FILENAME = None


class ChatQueryRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None
    filename: Optional[str] = None


@app.get("/")
def home():
    return {
        "message": "Syllabus Extraction & Chatbot Backend is running"
    }


@app.post("/upload-syllabus")
def upload_syllabus(file: UploadFile = File(...)):
    raw_filename = file.filename or ""
    safe_filename = os.path.basename(raw_filename).strip()

    # Reject empty, null bytes, or directory traversal attempts
    if not safe_filename or ".." in raw_filename or "\x00" in raw_filename:
        return {
            "success": False,
            "message": "Invalid or unsafe filename provided"
        }

    # Check PDF extension
    if not safe_filename.lower().endswith(".pdf"):
        return {
            "success": False,
            "message": "Only PDF files are allowed"
        }

    upload_dir_abs = os.path.abspath(UPLOAD_DIR)
    os.makedirs(upload_dir_abs, exist_ok=True)
    file_path = os.path.abspath(os.path.join(upload_dir_abs, safe_filename))

    # Path traversal protection
    if not file_path.startswith(upload_dir_abs + os.sep) and file_path != upload_dir_abs:
        return {
            "success": False,
            "message": "Directory traversal attempt detected"
        }

    content = file.file.read()
    # Content-based magic bytes validation for PDF
    if not content.startswith(b"%PDF-"):
        return {
            "success": False,
            "message": "Uploaded file is not a valid PDF document"
        }

    with open(file_path, "wb") as f:
        f.write(content)

    # Read PDF
    document = fitz.open(file_path)

    full_text = ""

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()
        full_text += f"\n\n--- PAGE {page_number} ---\n\n"
        full_text += text

    # Store page count before closing PDF
    total_pages = len(document)

    document.close()

    # Detect possible subjects
    subjects = extract_subject_candidates(full_text)

    # Reset in-memory cache so newly uploaded PDF becomes sole active source of truth
    DOCUMENT_ENGINES.clear()

    global LATEST_FILENAME
    LATEST_FILENAME = file.filename
    DOCUMENT_ENGINES[file.filename] = AcademicSyllabusQAEngine(
        full_text=full_text,
        filename=file.filename,
        subjects=subjects,
        file_path=file_path
    )

    return {
        "success": True,
        "filename": file.filename,
        "pages": total_pages,
        "subject_count": len(subjects),
        "subjects_found": subjects,
        "text": full_text
    }


@app.post("/chat")
@app.post("/ask")
def chat_with_syllabus(req: ChatQueryRequest):
    user_query = req.query or req.question or ""
    target_filename = req.filename or LATEST_FILENAME

    if not target_filename or target_filename not in DOCUMENT_ENGINES:
        if target_filename and os.path.exists(os.path.join(UPLOAD_DIR, target_filename)):
            fp = os.path.join(UPLOAD_DIR, target_filename)
            doc = fitz.open(fp)
            full_text = ""
            for page_number, page in enumerate(doc, start=1):
                full_text += f"\n\n--- PAGE {page_number} ---\n\n" + page.get_text()
            doc.close()
            subjects = extract_subject_candidates(full_text)
            DOCUMENT_ENGINES[target_filename] = AcademicSyllabusQAEngine(
                full_text=full_text,
                filename=target_filename,
                subjects=subjects
            )
        elif os.listdir(UPLOAD_DIR):
            first_pdf = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")][0]
            fp = os.path.join(UPLOAD_DIR, first_pdf)
            doc = fitz.open(fp)
            full_text = ""
            for page_number, page in enumerate(doc, start=1):
                full_text += f"\n\n--- PAGE {page_number} ---\n\n" + page.get_text()
            doc.close()
            target_filename = first_pdf
            subjects = extract_subject_candidates(full_text)
            DOCUMENT_ENGINES[target_filename] = AcademicSyllabusQAEngine(
                full_text=full_text,
                filename=target_filename,
                subjects=subjects
            )
        else:
            return {
                "success": False,
                "answer": "No syllabus PDF uploaded yet. Please upload a PDF first.",
                "found": False
            }

    engine = DOCUMENT_ENGINES[target_filename]
    res = engine.answer_question(user_query)

    return {
        "success": True,
        "filename": target_filename,
        "query": user_query,
        "answer": res.get("answer", ""),
        "found": res.get("found", True),
        "details": res
    }


@app.get("/books/search")
def search_books_endpoint(q: str, limit: int = 8):
    if not q or not q.strip():
        return {
            "success": False,
            "message": "Query parameter 'q' is required",
            "results": [],
            "cleaned_query": ""
        }
    res = search_internet_books(q.strip(), limit=limit)
    clean_q = res.get("clean_info", {}).get("catalog_query", q.strip())
    return {
        "success": True,
        **res,
        "cleaned_query": clean_q
    }


@app.get("/books/download")
def download_book_endpoint(url: str):
    if not is_safe_download_url(url):
        raise HTTPException(
            status_code=400,
            detail="Invalid or unauthorized download URL"
        )
    return RedirectResponse(url=url, status_code=307)


@app.get("/books/read")
def read_book_endpoint(id: Optional[str] = None, url: Optional[str] = None, q: Optional[str] = None):
    target = id or url or q or ""
    if not target:
        raise HTTPException(
            status_code=400,
            detail="Parameter 'id', 'url', or 'q' is required"
        )
    return get_book_readable_content(target)
