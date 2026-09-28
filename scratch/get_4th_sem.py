import requests

r = requests.post('http://127.0.0.1:8000/chat', json={'query': '4th sem ka syllabus'})
ans = r.json().get('answer', '')

with open('scratch/4th_sem_output.txt', 'w', encoding='utf-8') as f:
    f.write(ans)

print("Saved output, total chars:", len(ans))
