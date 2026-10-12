import json

log_path = r"C:\Users\haque\.gemini\antigravity-ide\brain\04ac1a9c-25bb-4494-9492-6dc963d25464\.system_generated\logs\transcript.jsonl"
with open(log_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if 845 <= i <= 862:
            data = json.loads(line)
            src = data.get("source")
            tp = data.get("type")
            cnt = str(data.get("content", ""))[:120].replace("\n", " ")
            print(f"[{i}] {src} | {tp} | {cnt}")
