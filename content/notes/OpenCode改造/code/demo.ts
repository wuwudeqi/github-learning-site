import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { summarize, reportCsv, formatCents } from './report.ts';
import { TaskRuntime } from './runtime.ts';
import type { CapabilitySnapshot, Tool } from './runtime.ts';

const outputDir = process.argv[2];
if (!outputDir) throw new Error('Usage: node --experimental-strip-types demo.ts /tmp/opencode-lab-demo');
const csv = await readFile(new URL('../data/normal.csv', import.meta.url), 'utf8');
const runtime = new TaskRuntime();
const snapshot: CapabilitySnapshot = {
  skill: 'department-report@1.0.0', mcp: 'fixture-file-tool@1.0.0',
  workflow: 'department-summary@1', model: 'fixture-plan@1',
};
const request = {
  actor: 'demo-user', channel: 'web' as const, conversation: 'demo-room', messageId: 'upload-001',
  instruction: '按部门汇总金额，不丢弃坏行，不重复计入相同 record_id。', csv,
};
// Fixed model replacement. This is NOT an LLM call or an OpenCode integration.
const fixturePlanner = () => ({ tool: 'sum_by_department' as const });
const tool: Tool = async ({ csv }, _snapshot, signal) => {
  signal.throwIfAborted();
  const plan = fixturePlanner();
  if (plan.tool !== 'sum_by_department') throw new Error('UNSUPPORTED_TOOL');
  return summarize(csv);
};
const { taskId } = runtime.create(request, snapshot);
await runtime.run(taskId, tool);
const state = runtime.view(taskId);
if (state.status !== 'completed' || !state.artifact) throw new Error('NO_ARTIFACT');
await mkdir(outputDir, { recursive: true });
// wx prevents silently overwriting previous outputs; choose a new directory when rerunning.
await writeFile(resolve(outputDir, 'summary.csv'), reportCsv(state.artifact.report), { flag: 'wx' });
await writeFile(resolve(outputDir, 'manifest.json'), JSON.stringify(state, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({
  mode: 'fixture-model + real-local-tool', taskId, status: state.status,
  rows: state.artifact.report.rowCount, total: formatCents(state.artifact.report.totalCents),
  events: runtime.eventsAfter(taskId, 0), outputDir: resolve(outputDir),
}, null, 2));
