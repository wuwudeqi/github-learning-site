import { createHash } from 'node:crypto';
import type { Report } from './report.ts';

export type CapabilitySnapshot = Readonly<{ skill: string; mcp: string; workflow: string; model: string }>;
export type Request = {
  actor: string; channel: 'cli' | 'web' | 'im'; conversation: string; messageId: string;
  instruction: string; csv: string;
};
export type Status = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type Event = { seq: number; type: string; detail: string };
export type Artifact = { report: Report; inputSha256: string; resultSha256: string };
type Task = {
  id: string; status: Status; request: Request; snapshot: CapabilitySnapshot;
  events: Event[]; controller: AbortController; artifact?: Artifact;
};
export type TaskView = { id: string; status: Status; snapshot: CapabilitySnapshot; artifact?: Artifact };
export type Tool = (request: Request, snapshot: CapabilitySnapshot, signal: AbortSignal) => Promise<Report>;
export const sha256 = (text: string): string => createHash('sha256').update(text).digest('hex');

// Single-process teaching runtime. No durable database, distributed lock or sandbox.
export class TaskRuntime {
  private tasks = new Map<string, Task>();
  private requests = new Map<string, { hash: string; taskId: string }>();
  private nextId = 1;

  create(request: Request, capability: CapabilitySnapshot): { taskId: string; reused: boolean } {
    if (![request.actor, request.conversation, request.messageId].every(value => value.length > 0)) {
      throw new Error('INVALID_IDENTITY');
    }
    // Fixed tuple avoids JSON property-order differences. Identity is supplied by a trusted adapter.
    const key = JSON.stringify([request.actor, request.channel, request.conversation, request.messageId]);
    const hash = sha256(JSON.stringify([request.instruction, request.csv]));
    const previous = this.requests.get(key);
    if (previous) {
      if (previous.hash !== hash) throw new Error('IDEMPOTENCY_CONFLICT');
      return { taskId: previous.taskId, reused: true };
    }
    const id = `task-${this.nextId++}`;
    const task: Task = {
      id, status: 'queued', request: { ...request }, snapshot: Object.freeze({ ...capability }),
      events: [], controller: new AbortController(),
    };
    // No await between lookup and insertion: atomic only within this synchronous process path.
    this.tasks.set(id, task);
    this.requests.set(key, { hash, taskId: id });
    this.append(task, 'task.created', 'Capabilities fixed for this task.');
    return { taskId: id, reused: false };
  }

  view(id: string): TaskView {
    const task = this.get(id);
    return structuredClone({ id: task.id, status: task.status, snapshot: task.snapshot, artifact: task.artifact });
  }

  eventsAfter(id: string, cursor: number): Event[] {
    const events = this.get(id).events;
    if (!Number.isSafeInteger(cursor) || cursor < 0 || cursor > events.length) throw new Error('INVALID_CURSOR');
    return events.filter(event => event.seq > cursor).map(event => ({ ...event }));
  }

  cancel(id: string): boolean {
    const task = this.get(id);
    if (task.status !== 'queued' && task.status !== 'running') return false;
    task.status = 'cancelled';
    this.append(task, 'task.cancelled', 'Late tool results will not be committed.');
    task.controller.abort(); // Cooperative signal; does not undo an external side effect.
    return true;
  }

  async run(id: string, tool: Tool): Promise<void> {
    const task = this.get(id);
    if (task.status !== 'queued') throw new Error(`INVALID_START: ${task.status}`);
    task.status = 'running';
    this.append(task, 'task.started', 'Tool started.');
    try {
      const report = await tool({ ...task.request }, task.snapshot, task.controller.signal);
      // run awaited arbitrary code, so status must be read again through a method.
      if (this.view(id).status !== 'running') return;
      const artifact: Artifact = {
        report: structuredClone(report), inputSha256: sha256(task.request.csv),
        resultSha256: sha256(JSON.stringify(report)),
      };
      // No await between terminal check and commit: controlled single-process winner.
      task.artifact = artifact;
      task.status = 'completed';
      this.append(task, 'task.completed', artifact.resultSha256);
    } catch (error) {
      if (this.view(id).status !== 'running') return;
      task.status = 'failed';
      this.append(task, 'task.failed', error instanceof Error ? error.message : String(error));
    }
  }

  private get(id: string): Task {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`UNKNOWN_TASK: ${id}`);
    return task;
  }
  private append(task: Task, type: string, detail: string): void {
    task.events.push({ seq: task.events.length + 1, type, detail });
  }
}
