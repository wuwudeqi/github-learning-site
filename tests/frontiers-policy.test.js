import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { validateIssue } from "../scripts/check-frontiers.mjs";

const audit = JSON.parse(
  await readFile(
    new URL("../docs/frontiers-source-audits/2026-09-09.json", import.meta.url),
    "utf8",
  ),
);
const news = await readFile(
  new URL(
    "../content/frontiers/2026/09/2026-09-09/01-AI动态.md",
    import.meta.url,
  ),
  "utf8",
);
const check = (data, text = news) => validateIssue(data, text, "2026-09-09");

test("the regenerated issue has matching evidence and fifteen entries", () => {
  assert.deepEqual(check(audit), []);
});

test("a missing major announcement fails even if another item fills its slot", () => {
  const data = structuredClone(audit);
  data.candidates[0].selected = false;
  data.candidates[15].selected = true;
  data.candidates[15].order = 1;
  assert.ok(
    check(data).some((error) => error.includes("important candidate omitted")),
  );
});

test("unperformed source checks and unsupported project heat fail", () => {
  const data = structuredClone(audit);
  data.coverage = data.coverage.filter((item) => item.provider !== "OpenAI");
  delete data.candidates.find((item) => item.kind === "project").heat;
  const errors = check(data);
  assert.ok(
    errors.some((error) => error.includes("coverage record required: OpenAI")),
  );
  assert.ok(errors.some((error) => error.includes("heat evidence")));
});

test("missing article, wrong date, and duplicate events fail", () => {
  assert.ok(check(audit, news.replace("## 15 ·", "### 15 ·")).length);
  const data = structuredClone(audit);
  data.candidates[0].eventDate = "2026-08-01";
  data.candidates[1].id = data.candidates[0].id;
  const errors = check(data);
  assert.ok(errors.some((error) => error.includes("seven-day window")));
  assert.ok(errors.some((error) => error.includes("duplicate event")));
});
