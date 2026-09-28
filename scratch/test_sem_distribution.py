import re
from typing import Dict, List, Optional

def test_distribution(subjects: List[str]):
    total = len(subjects)
    sem_map = {f"Semester {i}": [] for i in range(1, 9)}
    
    # Assume we split 96 subjects across 8 semesters
    subs_per_sem = max(4, total // 8) if total >= 16 else max(3, total // 2)
    
    for idx, s in enumerate(subjects):
        sem_idx = min(8, (idx // subs_per_sem) + 1)
        sem_map[f"Semester {sem_idx}"].append(s)
        
    print(f"Total Subjects: {total}, Subs per sem: {subs_per_sem}")
    for k, v in sem_map.items():
        if v:
            print(f"{k}: {len(v)} subjects -> {v[:2]}...")

sample_subs = [f"Subject_{i}" for i in range(1, 97)]
test_distribution(sample_subs)
