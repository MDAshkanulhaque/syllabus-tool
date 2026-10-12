import re

with open("scratch/grewal_raw_toc.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

# Let's see lines 0 to 80
for idx, l in enumerate(lines[:80]):
    print(f"{idx:3d}: {l}")
