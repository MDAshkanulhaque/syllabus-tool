with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

import re
idx = text.find("Chapter 11")
idx2 = text.find("Chapter 12")
print(text[idx:idx2])
