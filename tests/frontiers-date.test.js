import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const cli = fileURLToPath(
  new URL("../scripts/check-frontiers.mjs", import.meta.url),
);

test("yesterday's issue cannot satisfy an explicitly requested publication date", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "frontiers-date-"));
  try {
    const old = path.join(root, "content/frontiers/2026/09/2026-09-08");
    await mkdir(old, { recursive: true });
    await writeFile(path.join(old, "01-AI动态.md"), "# Historical issue\n");
    const result = spawnSync(process.execPath, [cli, "--date", "2026-09-10"], {
      cwd: root,
      encoding: "utf8",
    });
    assert.notEqual(result.status, 0, "missing today's issue must fail");
    assert.match(result.stderr, /2026-09-10/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("the date argument is validated instead of silently ignored", () => {
  const result = spawnSync(process.execPath, [cli, "--date", "2026-02-30"], {
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /date|日期/i);
});
