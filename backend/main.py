from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import fitz
import os

from subject_detector import extract_subject_candidates
from qa_engine import AcademicSyllabusQAEngine


app = FastAPI(title="Syllabus Extraction & Chatbot Backend")


# Upload folder
UPLOAD_DIR = "uploads"
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

    # Check PDF
    if not file.filename.lower().endswith(".pdf"):
        return {
            "success": False,
            "message": "Only PDF files are allowed"
        }

    # Save uploaded PDF
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    content = file.file.read()

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