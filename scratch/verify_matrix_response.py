import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections, format_book_sections_response

results = search_book_sections("matrix")
resp = format_book_sections_response("matrix", results)

grewal_secs = [s["section_heading"] for s in results.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])]
kreyszig_secs = [s["section_heading"] for s in results.get("advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1", [])]

# Check that weak/incidental matches are excluded
assert not any("14.5 Newton Raphson" in s for s in grewal_secs), "14.5 Newton Raphson must not be in Grewal sections"
assert not any("15.5 Newton Raphson" in s for s in grewal_secs), "15.5 Newton Raphson must not be in Grewal sections"
assert not any("16.5 Newton Raphson" in s for s in grewal_secs), "16.5 Newton Raphson must not be in Grewal sections"
assert not any("4.15 Objective Type" in s for s in grewal_secs), "4.15 Objective Type must not be in Grewal sections"
assert not any("3.9 Objective Type" in s for s in grewal_secs), "3.9 Objective Type must not be in Grewal sections"

# Check that genuinely relevant sections are preserved
assert any("3.2" in s and "Matrices" in s for s in grewal_secs), "3.2 Introduction To Matrices must be preserved"
assert "4.11 Power Method" in grewal_secs, "4.11 Power Method must be preserved"
assert "4.8 Eigenvalues and Eigenvectors" in grewal_secs, "4.8 Eigenvalues must be preserved"
assert "4.5 Factorization Method" in grewal_secs, "4.5 Factorization Method must be preserved"
assert "7.2 Matrix Multiplication" in kreyszig_secs, "7.2 Matrix Multiplication must be preserved"
assert "7.1 Matrices, Vectors: Addition and Scalar Multiplication" in kreyszig_secs, "7.1 must be preserved"
assert "8.1 The Matrix Eigenvalue Problem. Determining Eigenvalues and Eigenvectors" in kreyszig_secs, "8.1 must be preserved"
assert "7.8 Inverse of a Matrix. Gauss–Jordan Elimination" in kreyszig_secs, "7.8 must be preserved"

# Check response text
assert "14.5 Newton Raphson" not in resp, "14.5 Newton Raphson must not be in response text"
assert "4.15 Objective Type" not in resp, "4.15 Objective Type must not be in response text"
assert any("3.2" in line and "Matrices" in line for line in resp.splitlines()), "3.2 Introduction To Matrices must be in response text"
assert "7.2 Matrix Multiplication" in resp, "7.2 Matrix Multiplication must be in response text"

# Verify other queries are untouched
fourier_res = search_book_sections("Fourier Series")
assert any("11.1 Fourier Series" in s["section_heading"] for s in fourier_res.get("advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1", [])), "Fourier Series search must still work"

print("SUCCESS: All matrix tests, exclusions, preservations, and query integrity verified!")
