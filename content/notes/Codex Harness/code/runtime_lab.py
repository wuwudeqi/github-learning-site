"""Deterministic mechanism lab; not Codex and not a real-model benchmark.

Events control ordering; no wall-clock sleeps or external services are used.
Run: python3 runtime_lab.py
"""

import asyncio
import copy
import json
import uuid
from types import MappingProxyType


TRACE = []
CHECKS = 0


def event(name):
    TRACE.append(name)


def check(condition, message):
    global CHECKS
    if not condition:
        raise AssertionError(message)
    CHECKS += 1
    print(f"PASS {CHECKS:02}: {message}")


def prompt_view(history):
    """A minimal ordinary function-call subset; IDs differ from Codex's IDs."""
    result = copy.deepcopy(history)
    outputs = {i['call_id'] for i in result if i['type'] == 'output'}
    repaired = []
    for item in result:
        repaired.append(item)
        if item['type'] == 'call' and item['call_id'] not in outputs:
            repaired.append({
                'type': 'output', 'call_id': item['call_id'], 'text': 'aborted',
                'item_id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'teaching-output:' + item['item_id'])),
            })
    return repaired


async def stream_and_drain():
    started_a, started_b = asyncio.Event(), asyncio.Event()
    done_b, release_a, stream_done = asyncio.Event(), asyncio.Event(), asyncio.Event()
    history = [{'type': 'user', 'text': 'read A and B; explain only'}]
    prompts = []
    current_registry = {'read': 'schema-v1'}
    step = MappingProxyType(dict(current_registry))

    async def tool(name):
        event('handler_start_' + name)
        if name == 'A':
            started_a.set()
            await release_a.wait()
        else:
            started_b.set()
            done_b.set()
        event('handler_done_' + name)
        return {'type': 'output', 'call_id': 'c-' + name, 'text': name, 'schema': step['read']}

    async def scripted_stream():
        event('model_request_1')
        prompts.append(copy.deepcopy(history))
        yield {'type': 'call', 'call_id': 'c-A', 'item_id': 'i-A', 'name': 'A'}
        await started_a.wait()
        yield {'type': 'call', 'call_id': 'c-B', 'item_id': 'i-B', 'name': 'B'}
        await started_b.wait()
        await done_b.wait()
        event('response_completed_1')
        stream_done.set()

    async def run():
        in_flight = []
        async for item in scripted_stream():
            history.append(item)
            event('record_call_' + item['name'])
            in_flight.append(asyncio.create_task(tool(item['name'])))
        # Tasks run concurrently, but observations are collected in insertion order.
        for pending in in_flight:
            output = await pending
            history.append(output)
            event('record_output_' + output['text'])
        event('model_request_2')
        prompts.append(copy.deepcopy(history))
        history.append({'type': 'message', 'text': 'explanation complete'})
        event('turn_finished')

    runner = asyncio.create_task(run())
    await stream_done.wait()
    check(not runner.done() and len(prompts) == 1,
          'response completion does not start the next model request before tools drain')
    check('handler_done_B' in TRACE and 'handler_done_A' not in TRACE,
          'B finishes while A is still blocked; actual execution is concurrent')
    current_registry['read'] = 'schema-v2'
    release_a.set()
    await runner
    outputs = [i for i in prompts[1] if i['type'] == 'output']
    check([i['text'] for i in outputs] == ['A', 'B'],
          'observation order is A then B despite B finishing first')
    check(all(i['schema'] == 'schema-v1' for i in outputs) and current_registry['read'] == 'schema-v2',
          'captured request capability view survives a later registry change')
    check(TRACE.index('record_call_A') < TRACE.index('handler_start_A')
          and TRACE.index('record_output_B') < TRACE.index('model_request_2'),
          'calls precede execution and observations precede follow-up inference')
    check(len(prompts[0]) == 1 and len(prompts[1]) == 5,
          'later inference sees accumulated observations; first prompt stays unchanged')


async def cancellation_race():
    terminal, release_completion, cancel, preserve_branch = (
        asyncio.Event(), asyncio.Event(), asyncio.Event(), asyncio.Event()
    )

    async def handler():
        terminal.set()  # Terminal business result exists; lifecycle cleanup is still pending.
        await release_completion.wait()
        return 'completed'

    async def runtime():
        task = asyncio.create_task(handler())
        cancellation = asyncio.create_task(cancel.wait())
        try:
            await asyncio.wait([task, cancellation], return_when=asyncio.FIRST_COMPLETED)
            if task.done():
                return await task
            if terminal.is_set():
                preserve_branch.set()
                return await task
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            return 'aborted'
        finally:
            cancellation.cancel()
            await asyncio.gather(cancellation, return_exceptions=True)

    runner = asyncio.create_task(runtime())
    await terminal.wait()
    cancel.set()
    await preserve_branch.wait()
    check(not runner.done(), 'cancellation after terminal result waits for lifecycle completion')
    release_completion.set()
    check(await runner == 'completed', 'late cancellation does not overwrite a completed result')


def history_and_baseline():
    history = [{'type': 'call', 'call_id': 'c-A', 'item_id': 'i-A'}]
    original = copy.deepcopy(history)
    first, second = prompt_view(history), prompt_view(history)
    check(history == original and len(first) == 2,
          'prompt-only repair leaves original history unchanged')
    check(first == second and first[1]['text'] == 'aborted',
          'repeated prompt repair yields stable ID and never fabricates success')
    changed = prompt_view([{'type': 'call', 'call_id': 'c-A', 'item_id': 'i-other'}])
    check(first[1]['item_id'] != changed[1]['item_id'],
          'synthetic identity depends on source item identity, not only call identity')

    actual = {'cwd': '/repo/a', 'allow_write': False}
    old_baseline = dict(actual)
    compacted = [{'summary': 'looked at the tests'}]

    def inject(baseline):
        delta = dict(actual) if baseline is None else {
            key: value for key, value in actual.items() if baseline.get(key) != value
        }
        return compacted + ([{'settings': delta}] if delta else [])

    stale, rebuilt = inject(old_baseline), inject(None)
    check(not any('settings' in i for i in stale) and rebuilt[-1]['settings'] == actual,
          'stale compaction baseline omits settings; reset baseline reinjects them')

    def decision(model_followup, pending, limit):
        followup = model_followup or pending
        return 'compact' if followup and limit else 'continue' if followup else 'stop_candidate'

    check(decision(False, True, False) == 'continue'
          and decision(True, False, True) == 'compact'
          and decision(False, False, True) == 'stop_candidate',
          'follow-up and context boundary jointly determine the outer-loop branch')


async def main():
    # This timeout is only a deadlock guard. No timing measurements are reported.
    await asyncio.wait_for(stream_and_drain(), timeout=10)
    await asyncio.wait_for(cancellation_race(), timeout=10)
    history_and_baseline()
    print('TRACE:', json.dumps(TRACE, ensure_ascii=False))
    print(f'{CHECKS} checks passed. Scripted model, Python teaching semantics; not Codex runtime validation.')


if __name__ == '__main__':
    asyncio.run(main())
