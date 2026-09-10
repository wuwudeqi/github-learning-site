import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { amountToCents, summarize, reportCsv } from './report.ts';
import { TaskRuntime } from './runtime.ts';
import type { CapabilitySnapshot, Request, Tool } from './runtime.ts';

const fixture = (name: string): string => readFileSync(new URL(`../data/${name}`, import.meta.url), 'utf8');
const normal = fixture('normal.csv');
// This oracle is a manually calculated fixture; do not generate it from summarize().
const expected = JSON.parse(fixture('expected-report.txt'));
const capability: CapabilitySnapshot = {
  skill: 'department-report@1.0.0', mcp: 'fixture-file-tool@1.0.0',
  workflow: 'department-summary@1', model: 'fixture-plan@1',
};
const request = (changes: Partial<Request> = {}): Request => ({
  actor: 'user-1', channel: 'im', conversation: 'room-1', messageId: 'message-1',
  instruction: '按部门汇总金额', csv: normal, ...changes,
});
const tool: Tool = async ({ csv }) => summarize(csv);
function setup(changes: Partial<Request> = {}) {
  const runtime = new TaskRuntime();
  const { taskId } = runtime.create(request(changes), capability);
  return { runtime, taskId };
}
function gate() {
  let release!: () => void;
  const promise = new Promise<void>(resolve => { release = resolve; });
  return { promise, release };
}

test('01 normal input agrees with independent department and total oracle', () => {
  assert.deepEqual(summarize(normal), expected);
  assert.equal(reportCsv(expected), 'department,amount\n研发,80.00\n销售,150.00\n');
});
test('02 integer cents retain exact values beyond Number safe integer range', () => {
  assert.equal(amountToCents('9007199254740993.01'), 900719925474099301n);
  assert.equal(amountToCents('0.10') + amountToCents('0.20'), 30n);
});
test('03 bad amounts fail instead of silently dropping or changing rows', () => {
  assert.throws(() => summarize(fixture('bad-amount.csv')), /INVALID_AMOUNT: 50元/);
  for (const value of ['1e2', '-1.00', '1.001', ' 1.00', '01.00']) {
    assert.throws(() => amountToCents(value), /INVALID_AMOUNT/);
  }
});
test('04 duplicate business IDs are rejected', () => {
  assert.throws(() => summarize(fixture('duplicate-id.csv')), /DUPLICATE_ID: R001/);
});
test('05 CSV contract rejects quotes, unexpected header and unsafe department labels', () => {
  assert.throws(() => summarize('record_id,department,amount\nA,"sales",1.00'), /INVALID_CSV/);
  assert.throws(() => summarize('id,department,amount\nA,sales,1.00'), /INVALID_HEADER/);
  assert.throws(() => summarize('record_id,department,amount\nA,=1+1,1.00'), /INVALID_DEPARTMENT/);
  assert.throws(() => summarize('record_id,department,amount\nA,-1,1.00'), /INVALID_DEPARTMENT/);
  assert.throws(() => summarize('record_id,department,amount\n'), /EMPTY_INPUT/);
});
test('06 input row order does not change report', () => {
  const lines = normal.trimEnd().split('\n');
  const reversed = [lines[0], ...lines.slice(1).reverse()].join('\n');
  assert.deepEqual(summarize(reversed), expected);
});
test('07 identical IM redelivery returns the same task without extra event', () => {
  const { runtime, taskId } = setup();
  assert.deepEqual(runtime.create(request(), capability), { taskId, reused: true });
  assert.equal(runtime.eventsAfter(taskId, 0).length, 1);
});
test('08 same identity key with changed input is an explicit conflict', () => {
  const { runtime } = setup();
  assert.throws(() => runtime.create(request({ csv: normal + '\n' }), capability), /IDEMPOTENCY_CONFLICT/);
  assert.throws(() => runtime.create(request({ instruction: '仅统计销售' }), capability), /IDEMPOTENCY_CONFLICT/);
});
test('09 actor, channel and conversation isolate idempotency scope', () => {
  const { runtime, taskId } = setup();
  const ids = [taskId];
  for (const changes of [{ actor: 'user-2' }, { channel: 'web' as const }, { conversation: 'room-2' }]) {
    ids.push(runtime.create(request(changes), capability).taskId);
  }
  assert.equal(new Set(ids).size, 4);
});
test('10 updating registry cannot alter an existing task capability snapshot', () => {
  const runtime = new TaskRuntime();
  const registry = { ...capability };
  const first = runtime.create(request(), registry).taskId;
  registry.skill = 'department-report@2.0.0';
  assert.equal(runtime.view(first).snapshot.skill, 'department-report@1.0.0');
  assert.equal(runtime.create(request(), registry).taskId, first);
  const second = runtime.create(request({ messageId: 'message-2' }), registry).taskId;
  assert.equal(runtime.view(second).snapshot.skill, 'department-report@2.0.0');
});
test('11 returned view cannot mutate internal task snapshot', () => {
  const { runtime, taskId } = setup();
  const external = runtime.view(taskId);
  (external.snapshot as { skill: string }).skill = 'tampered';
  assert.equal(runtime.view(taskId).snapshot.skill, capability.skill);
});
test('12 reconnect replays only events after the confirmed cursor', async () => {
  const { runtime, taskId } = setup();
  const initial = runtime.eventsAfter(taskId, 0);
  await runtime.run(taskId, tool);
  const recovered = runtime.eventsAfter(taskId, initial.at(-1)!.seq);
  assert.deepEqual([...initial, ...recovered].map(event => event.seq), [1, 2, 3]);
  assert.deepEqual(recovered.map(event => event.type), ['task.started', 'task.completed']);
  assert.deepEqual(runtime.eventsAfter(taskId, 3), []);
});
test('13 invalid cursors are rejected instead of hiding event gaps', () => {
  const { runtime, taskId } = setup();
  for (const cursor of [-1, 0.5, 2, NaN]) assert.throws(() => runtime.eventsAfter(taskId, cursor), /INVALID_CURSOR/);
});
test('14 cancel before start prevents tool invocation', async () => {
  const { runtime, taskId } = setup();
  let calls = 0;
  assert.equal(runtime.cancel(taskId), true);
  await assert.rejects(runtime.run(taskId, async () => { calls++; return expected; }), /INVALID_START: cancelled/);
  assert.equal(calls, 0);
});
test('15 cancelling before result commit wins even if tool ignores abort', async () => {
  const { runtime, taskId } = setup();
  const started = gate(), result = gate();
  let receivedSignal: AbortSignal | undefined;
  const running = runtime.run(taskId, async (_request, _snapshot, signal) => {
    receivedSignal = signal;
    started.release();
    await result.promise;
    return expected;
  });
  await started.promise;
  assert.equal(runtime.cancel(taskId), true);
  assert.equal(receivedSignal?.aborted, true);
  result.release();
  await running;
  assert.equal(runtime.view(taskId).status, 'cancelled');
  assert.equal(runtime.view(taskId).artifact, undefined);
  assert.equal(runtime.eventsAfter(taskId, 0).filter(event => event.type === 'task.completed').length, 0);
});
test('16 completed result wins over later cancel', async () => {
  const { runtime, taskId } = setup();
  await runtime.run(taskId, tool);
  assert.equal(runtime.cancel(taskId), false);
  assert.equal(runtime.view(taskId).status, 'completed');
  assert.deepEqual(runtime.view(taskId).artifact?.report, expected);
});
test('17 late tool failure cannot overwrite cancelled status', async () => {
  const { runtime, taskId } = setup();
  const started = gate(), failure = gate();
  const running = runtime.run(taskId, async () => {
    started.release(); await failure.promise; throw new Error('late failure');
  });
  await started.promise;
  runtime.cancel(taskId);
  failure.release();
  await running;
  assert.equal(runtime.view(taskId).status, 'cancelled');
  assert.equal(runtime.eventsAfter(taskId, 0).at(-1)?.type, 'task.cancelled');
});
test('18 normal tool failure produces failed terminal state without artifact', async () => {
  const { runtime, taskId } = setup({ csv: fixture('bad-amount.csv') });
  await runtime.run(taskId, tool);
  assert.equal(runtime.view(taskId).status, 'failed');
  assert.equal(runtime.view(taskId).artifact, undefined);
  assert.match(runtime.eventsAfter(taskId, 0).at(-1)!.detail, /INVALID_AMOUNT/);
  assert.equal(runtime.cancel(taskId), false);
});
test('19 a running task cannot execute a second tool', async () => {
  const { runtime, taskId } = setup();
  const finish = gate();
  let calls = 0;
  const running = runtime.run(taskId, async () => { calls++; await finish.promise; return expected; });
  await assert.rejects(runtime.run(taskId, tool), /INVALID_START: running/);
  finish.release(); await running;
  assert.equal(calls, 1);
});
test('20 artifact view is detached and provenance hashes are stable', async () => {
  const { runtime, taskId } = setup();
  await runtime.run(taskId, tool);
  const state = runtime.view(taskId);
  assert.match(state.artifact!.inputSha256, /^[a-f0-9]{64}$/);
  const originalHash = state.artifact!.resultSha256;
  state.artifact!.report.totalCents = '0';
  assert.equal(runtime.view(taskId).artifact!.report.totalCents, '23000');
  assert.equal(runtime.view(taskId).artifact!.resultSha256, originalHash);
});
