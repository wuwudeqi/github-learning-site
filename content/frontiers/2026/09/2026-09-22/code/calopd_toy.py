"""Synthetic log-probability arithmetic only; no model or training is run."""
import json
import platform
from pathlib import Path

def calibrate(student, teacher, interventions, scale):
    delta = [x - teacher for x in interventions]
    low = teacher - scale * max(0.0, -min(delta))
    high = teacher + scale * max(0.0, max(delta))
    return {
        'student': student, 'teacher': teacher, 'scale': scale,
        'low': round(low, 8), 'high': round(high, 8),
        'opd': round(teacher-student, 8),
        'calopd': round(max(low-student, 0.0)-max(student-high, 0.0), 8),
    }

rows = [calibrate(s, -1.0, [-0.9, -1.1], scale)
        for scale in [2, 5] for s in [-1.5, -1.0, -0.5]]
result = {
    'kind': 'synthetic arithmetic; not a trained model benchmark',
    'runtime': platform.python_version(),
    'teacher': -1.0,
    'interventions': [-0.9, -1.1],
    'rows': rows,
}
destination = Path(__file__).with_name('calopd-result.json')
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
