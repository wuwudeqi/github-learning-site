"""Compare equal CPU work with and without cooperative asyncio yields.

Python 3.11+, standard library only. No network, no model, no extra process.
Run: python3 event_loop_probe.py --output results.json.txt
"""
import argparse
import asyncio
import json
import math
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path


async def trial(cooperative, iterations, chunk, period):
    loop = asyncio.get_running_loop()
    start = loop.time()
    ticks, delays = [], []
    stopped = False

    async def heartbeat():
        while not stopped:
            expected = loop.time() + period
            await asyncio.sleep(period)
            actual = loop.time()
            ticks.append(round((actual - start) * 1000, 4))
            delays.append(max(0, (actual - expected) * 1000))

    task = asyncio.create_task(heartbeat())
    await asyncio.sleep(period * 5)
    began = loop.time()
    total = 0
    # Both modes execute the same arithmetic and chunk boundaries.
    for offset in range(0, iterations, chunk):
        for i in range(offset, min(offset + chunk, iterations)):
            total += (i * 17) % 101
        if cooperative:
            await asyncio.sleep(0)
    ended = loop.time()
    await asyncio.sleep(period * 5)
    stopped = True
    await task
    ordered = sorted(delays)
    return {
        'mode': 'cooperative' if cooperative else 'blocking',
        'checksum': total,
        'work_ms': round((ended - began) * 1000, 4),
        'work_start_ms': round((began - start) * 1000, 4),
        'work_end_ms': round((ended - start) * 1000, 4),
        'max_heartbeat_delay_ms': round(max(delays), 4),
        'p95_heartbeat_delay_ms': round(ordered[math.ceil(.95 * len(ordered)) - 1], 4),
        'heartbeat_count': len(ticks),
        'tick_ms': ticks,
    }


async def main(args):
    results = []
    for repeat in range(args.repeats):
        # Alternate order so one mode does not always receive a cold start.
        for mode in ([False, True] if repeat % 2 == 0 else [True, False]):
            result = await trial(mode, args.iterations, args.chunk, .005)
            result['repeat'] = repeat + 1
            results.append(result)
    assert len({r['checksum'] for r in results}) == 1, 'CPU results differ'
    summaries = {}
    for mode in ('blocking', 'cooperative'):
        rows = [r for r in results if r['mode'] == mode]
        summaries[mode] = {
            k + '_median': round(statistics.median(r[k] for r in rows), 4)
            for k in ['work_ms', 'max_heartbeat_delay_ms', 'p95_heartbeat_delay_ms']
        }
    report = {
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'iterations': args.iterations,
        'chunk': args.chunk,
        'heartbeat_period_ms': 5,
        'repeats_per_mode': args.repeats,
        'checksum': results[0]['checksum'],
        'interpretation': 'Local scheduling demonstration; not storage throughput or model performance.',
        'summary': summaries,
        'trials': results,
    }
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'trials'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='results.json.txt')
    parser.add_argument('--iterations', type=int, default=4000000)
    parser.add_argument('--chunk', type=int, default=4096)
    parser.add_argument('--repeats', type=int, default=5)
    options = parser.parse_args()
    if min(options.iterations, options.chunk, options.repeats) <= 0:
        parser.error('iteration, chunk and repeat counts must be positive')
    asyncio.run(main(options))
