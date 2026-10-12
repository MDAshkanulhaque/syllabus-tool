import pymupdf

doc = pymupdf.open('backend/books/advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1.pdf')
toc = doc.get_toc()

# Let's inspect the structure:
# Level 1: Part (e.g. PART B - Linear Algebra. Vector Calculus)
# Level 2: Chapter (e.g. Chapter 7: Linear Algebra: Matrices, Vectors, Determinants. Linear Systems)
# Level 3: Section (e.g. 7.1 Matrices, Vectors: Addition and Scalar Multiplication)
print(f"Total entries: {len(toc)}")
for item in toc[:35]:
    print(f"L{item[0]} (p.{item[2]}): {item[1]}")
