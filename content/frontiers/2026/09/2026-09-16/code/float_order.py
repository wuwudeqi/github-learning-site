"""A small, reproducible rounding example; not an Orthrus reproduction."""
import datetime
import json
import platform
import struct
import sys
from pathlib import Path


def f32(value):
    """Round to IEEE 754 binary32; return its exact value as a Python float."""
    return struct.unpack('!f', struct.pack('!f', value))[0]


def main():
    a, b, c = map(f32, (100_000_000.0, -100_000_000.0, 1.0))
    left_middle = f32(a + b)
    right_middle = f32(b + c)
    left = f32(left_middle + c)
    right = f32(a + right_middle)
    double_left = (a + b) + c
    double_right = a + (b + c)
    assert sys.float_info.mant_dig == 53, 'Example expects binary64 Python floats'
    assert (left, right) == (1.0, 0.0)
    assert (double_left, double_right) == (1.0, 1.0)
    result = {
        'executedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'python': platform.python_version(),
        'platform': platform.platform(),
        'inputs': {'a': a, 'b': b, 'c': c},
        'float32': {
            'left': {'expression': 'f32(f32(a + b) + c)', 'intermediate': left_middle, 'result': left},
            'right': {'expression': 'f32(a + f32(b + c))', 'intermediate': right_middle, 'result': right},
        },
        'float64': {'left': double_left, 'right': double_right},
        'verification': 'expected results and binary64 assumption asserted',
        'limits': 'Synthetic scalar example with explicit per-addition binary32 rounding; no model, GPU, BF16, or speed benchmark.',
    }
    dest = Path(__file__).with_name('float-results.json.txt')
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
