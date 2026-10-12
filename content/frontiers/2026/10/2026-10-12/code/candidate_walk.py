"""Synthetic, deterministic teaching example; not DCOCO or a speed benchmark.
Run with Python 3.10+: python3 candidate_walk.py > candidate-results.json
All candidate scores below are hand assigned. No model or network is used.
"""
import json
import platform
from datetime import datetime, timezone

CASES = [
    {'id': 'agreement', 'label': '搭配可纠正',
     'slots': [['These'], ['key', 'keys'], ['is', 'are'], ['missing']],
     'reference': ['These', 'keys', 'are', 'missing'],
     'scores': {'These|keys': 2, 'keys|are': 2, 'are|missing': 2}},
    {'id': 'coherent', 'label': '原候选已正确',
     'slots': [['The'], ['cat', 'cats'], ['sits', 'sit'], ['here']],
     'reference': ['The', 'cat', 'sits', 'here'],
     'scores': {'The|cat': 2, 'cat|sits': 2, 'sits|here': 2}},
    {'id': 'missing', 'label': '正确候选缺失',
     'slots': [['These'], ['key', 'lock'], ['is', 'was'], ['missing']],
     'reference': ['These', 'keys', 'are', 'missing'],
     'scores': {'These|key': 2, 'key|is': 2, 'is|missing': 2}},
    {'id': 'first', 'label': '首个候选错误',
     'slots': [['Those'], ['keys', 'key'], ['are', 'is'], ['missing']],
     'reference': ['These', 'keys', 'are', 'missing'],
     'scores': {'Those|keys': 2, 'keys|are': 2, 'are|missing': 2}},
]

def walk(case):
    # Rank *all* adjacent candidate pairs first, then follow the selected
    # predecessor. This is a conditional greedy walk, not global optimization.
    edges = [{(a, b): case['scores'].get(a+'|'+b, 0)
              for a in left for b in right}
             for left, right in zip(case['slots'], case['slots'][1:])]
    result = [case['slots'][0][0]]
    for candidates, scores in zip(case['slots'][1:], edges):
        result.append(max(candidates, key=lambda t: scores[(result[-1], t)]))
    return result

def accepted_prefix(draft, reference):
    n = 0
    for candidate, expected in zip(draft, reference):
        if candidate != expected:
            break
        n += 1
    return n

def toy_verify(draft, reference):
    # A KNOWN reference substitutes for the verifier in this demonstration.
    # This illustrates rejection/fallback only, not stochastic acceptance.
    n = accepted_prefix(draft, reference)
    return draft[:n] + reference[n:]

rows = []
for case in CASES:
    independent = [slot[0] for slot in case['slots']]
    conditional = walk(case)
    final = toy_verify(conditional, case['reference'])
    assert final == case['reference']
    rows.append({'id': case['id'], 'label': case['label'],
                 'independent': independent, 'conditional': conditional,
                 'reference': case['reference'],
                 'accepted_independent': accepted_prefix(independent, case['reference']),
                 'accepted_conditional': accepted_prefix(conditional, case['reference']),
                 'final_after_toy_verification': final})
print(json.dumps({'generatedAt': datetime.now(timezone.utc).isoformat(),
                  'python': platform.python_version(), 'platform': platform.platform(),
                  'dataType': 'hand-constructed synthetic cases and scores',
                  'scope': 'illustration of candidate selection and reference fallback; no speed or model accuracy claim',
                  'results': rows}, ensure_ascii=False, indent=2))
