import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')
doc = fitz.open("backend/uploads/ssn.pdf")
print("Page 23 text sample:")
print(doc[22].get_text()[:400])
doc.close()
