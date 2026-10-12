with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("CONTENTS • xi")
if idx == -1:
    idx = text.find("xi")
print(text[idx-50:idx+400])
