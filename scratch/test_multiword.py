import re
from pathlib import Path
import json

from scratch.test_section_search import search_sections

topics = [
    "Matrix",
    "Vector",
    "Eigenvalues aur Eigenvectors",
    "Differentiation",
    "Integration",
    "Differential Equations",
    "Numerical Methods",
    "Linear Independence",
    "Vector Spaces",
    "Matrix Multiplication"
]

for topic in topics:
    # Clean topic: remove Hinglish connectors like 'aur' -> 'and' or handle as separate terms
    clean_topic = re.sub(r"\b(?:aur|and)\b", " ", topic, flags=re.IGNORECASE).strip()
    res = search_sections(clean_topic)
    total_sections = sum(len(secs) for secs in res.values())
    print(f"Topic: '{topic}' (cleaned: '{clean_topic}') -> Total Sections: {total_sections}")
    for b_name, secs in res.items():
        if secs:
            top_sec = secs[0]
            print(f"   [{b_name[:20]}]: {len(secs)} secs | Top: '{top_sec['section_heading']}' (p.{top_sec['pdf_range']})")
        else:
            print(f"   [{b_name[:20]}]: 0 secs (No matching sections)")
