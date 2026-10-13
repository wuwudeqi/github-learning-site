"""Synthetic protocol demo; no model, API or real personal data."""
import json
from pathlib import Path
CASES = [
    ("emoji-before-email", "用户🙂：联系李雷，邮箱 li.lei@example.com。", "li.lei@example.com"),
    ("arabic-after-emoji", "🙂 اكتب إلى علي الآن", "علي"),
    ("combining-accent", "cafe\u0301🙂: contact@example.com", "contact@example.com"),
]
rows=[]
for case, text, target in CASES:
    start=text.index(target);end=start+len(target)
    assert text[start:end]==target
    rows.append(dict(case=case,text=text,start=start,end=end,expected=target,
                     codePoints=len(text),utf8Bytes=len(text.encode('utf-8'))))
p=Path(__file__).with_name('span-inputs.json')
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(f'{len(rows)} synthetic code-point intervals written to {p.name}')
