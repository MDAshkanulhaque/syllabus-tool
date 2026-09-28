# Syllabus Extraction CLI Tool

A 100% offline, deterministic, pure Python syllabus extraction tool built for the **Syllabus Extraction Evaluation Benchmark**.

---

## 🚀 Installation

Run the following command on a clean machine to install all dependencies:

```bash
pip install -r requirements.txt
```

---

## 💻 How to Run

### Task 1 — List all courses in the document
To read the PDF and list all extracted courses with code, title, and start page number:

```bash
python main.py --pdf <path_to_pdf>
```

**Example:**
```bash
python main.py --pdf "backend/uploads/rit.pdf"
```

---

### Task 2 — Read one course in full
To extract full details for a single target course code:

```bash
python main.py --pdf <path_to_pdf> --course <course_code>
```

**Example:**
```bash
python main.py --pdf "backend/uploads/rit.pdf" --course CS23311
```

---

## 📋 JSON Output Specification

* **Task 1** outputs JSON containing `document`, `course_count`, and `courses` list.
* **Task 2** outputs JSON containing `course`, `units` (with `topics` and Bloom taxonomy classification), `course_outcomes`, `programme_outcomes`, `co_po_matrix`, `books`, and `not_extracted` diagnostic report.
* Standard output (`stdout`) returns valid JSON with exit status `0`.

---

## 🧪 Test Results & Performance

Tested across 11 diverse college syllabus PDFs (VIT, Rajalakshmi Institute of Technology, Hindustan Institute of Technology, Panimalar, SSN, etc.):
- **Speed:** Wall-clock time under 2 seconds per document.
- **Repeatability:** 100% deterministic (identical JSON output across multiple runs).
- **Offline operation:** 100% local, no API keys or internet connection needed.
