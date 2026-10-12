import sys
sys.path.insert(0, ".")

from backend.book_engine.book_search import search_book_sections

print("=================================================================")
print("VERIFYING AFFECTED QUERIES AFTER BOUNDARY FIX")
print("=================================================================")

# 1. Least Squares
res_ls = search_book_sections("least squares")
g_ls = res_ls.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
g_ls_secs = [s["section_heading"] for s in g_ls]
print("\n--- 'least squares' in Grewal ---")
for s in g_ls:
    print(f"  [{s['category_key'].upper():7s}] {s['section_heading']} (PDF {s['pdf_range']}) | Matched: {len(s['matching_pages'])}/{s['page_count']}")
assert not any("14.30" in s for s in g_ls_secs), "14.30 Simplex Method must NOT appear in least squares!"
print("[PASS] 14.30 Simplex Method correctly excluded from 'least squares'")

# 2. Secant Method
res_secant = search_book_sections("secant method")
g_secant = res_secant.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
g_secant_secs = [s["section_heading"] for s in g_secant]
print("\n--- 'secant method' in Grewal ---")
for s in g_secant:
    print(f"  [{s['category_key'].upper():7s}] {s['section_heading']} (PDF {s['pdf_range']}) | Matched: {len(s['matching_pages'])}/{s['page_count']}")
assert not any("1.10" in s for s in g_secant_secs), "1.10 Objective Type must NOT appear in secant method!"
print("[PASS] 1.10 Objective Type correctly excluded from 'secant method'")

# 3. Bisection Method
res_bisect = search_book_sections("bisection method")
g_bisect = res_bisect.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
g_bisect_secs = [s["section_heading"] for s in g_bisect]
assert not any("1.10" in s for s in g_bisect_secs), "1.10 Objective Type must NOT appear in bisection method!"
print("[PASS] 1.10 Objective Type correctly excluded from 'bisection method'")

# 4. Interpolation
res_interp = search_book_sections("interpolation")
g_interp = res_interp.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
g_interp_secs = [s["section_heading"] for s in g_interp]
assert not any("6.12" in s for s in g_interp_secs), "6.12 Objective Type must NOT appear in interpolation!"
print("[PASS] 6.12 Objective Type correctly excluded from 'interpolation'")

# 5. Differential Equations
res_diff = search_book_sections("differential equations")
g_diff = res_diff.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
g_diff_secs = [s["section_heading"] for s in g_diff]
assert not any("9.10" in s for s in g_diff_secs), "9.10 Objective Type must NOT appear in differential equations!"
print("[PASS] 9.10 Objective Type correctly excluded from 'differential equations'")

# 6. Check that 14.30, 15.30, 16.30 boundaries are properly capped
res_matrix = search_book_sections("matrix")
g_matrix = res_matrix.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
for s in g_matrix:
    if "14.30" in s["section_heading"]:
        assert s["pdf_range"] == "764–767", f"Expected 764–767, got {s['pdf_range']}"
        assert 769 not in s["matching_pages"], "Page 769 should not be in matching pages"
    elif "15.30" in s["section_heading"]:
        assert s["pdf_range"] == "844–847", f"Expected 844–847, got {s['pdf_range']}"
    elif "16.30" in s["section_heading"]:
        assert s["pdf_range"] == "898–900", f"Expected 898–900, got {s['pdf_range']}"
print("[PASS] 14.30, 15.30, 16.30 boundaries verified (exercises excluded)")

print("\n=================================================================")
print("ALL VERIFICATION CHECKS PASSED!")
print("=================================================================")
