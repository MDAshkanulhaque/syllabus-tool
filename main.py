import argparse
import json
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from syllabus_extractor import extract_courses_from_pdf, extract_course_details


def main():
    parser = argparse.ArgumentParser(description="Syllabus Extraction CLI Tool")
    parser.add_argument("--pdf", required=True, help="Path to syllabus PDF document")
    parser.add_argument("--course", required=False, default=None, help="Course code to read in full (Task 2)")

    args = parser.parse_args()

    pdf_path = args.pdf
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(pdf_path):
        sys.stderr.write(f"Error: File '{args.pdf}' not found.\n")
        sys.exit(1)

    filename = os.path.basename(pdf_path)

    if args.course:
        # Task 2 — read one course in full
        try:
            result = extract_course_details(pdf_path, args.course)
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as e:
            sys.stderr.write(f"Error extracting course '{args.course}': {str(e)}\n")
            sys.exit(1)
    else:
        # Task 1 — list all courses
        try:
            courses = extract_courses_from_pdf(pdf_path)
            result = {
                "document": filename,
                "course_count": len(courses),
                "courses": courses
            }
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as e:
            sys.stderr.write(f"Error extracting course list: {str(e)}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
