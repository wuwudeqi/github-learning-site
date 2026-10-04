"""Deterministic synthetic labels: agreement with a teacher is not truth.
Python standard library only. Does not call or evaluate any real model.
"""
import json
import platform
from pathlib import Path

truth = [i % 2 for i in range(1000)]
teacher = truth.copy()
for i in range(200):
    teacher[i] = 1 - teacher[i]

students = {'copy': teacher.copy(), 'repair_10': teacher.copy(), 'damage_10': teacher.copy()}
for i in range(10):
    students['repair_10'][i] = truth[i]
for i in range(200, 210):
    students['damage_10'][i] = 1 - truth[i]

rows = []
for name, student in students.items():
    agree = sum(s == t for s, t in zip(student, teacher))
    correct = sum(s == y for s, y in zip(student, truth))
    rows.append({'scenario': name, 'n': len(truth), 'teacher_agree': agree,
                 'correct': correct, 'agreement_pct': 100 * agree / len(truth),
                 'accuracy_pct': 100 * correct / len(truth)})
assert [(r['teacher_agree'], r['correct']) for r in rows] == [(1000,800),(990,810),(990,790)]
result = {'synthetic': True, 'seed': None, 'design': 'deterministic 1000 binary labels; teacher wrong on first 200',
          'python': platform.python_version(), 'platform': platform.system(), 'machine': platform.machine(),
          'teacher_correct': 800, 'n':1000, 'coverage_pct':100, 'rows':rows}
out=Path(__file__).with_name('agreement-results.json')
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
