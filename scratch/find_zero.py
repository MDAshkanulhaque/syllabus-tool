with open("frontend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    s = line.strip()
    if s == "0" or s == "0," or s == "[0]" or s.endswith("= 0") or s == "0.0":
        print(f"Exact 0 on line {i}: {line}")
    elif " 0 " in s or "0)" in s or "(0" in s:
        if any(keyword in s for keyword in ["st.", "return", "print", "caption", "markdown"]):
            print(f"Potential 0 on line {i}: {line.strip()[:80]}")
