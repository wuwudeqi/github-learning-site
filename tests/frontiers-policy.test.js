import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { validateIssue, validateProjects } from "../scripts/check-frontiers.mjs";

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
const projects = await readFile(new URL(
  "../content/frontiers/2026/09/2026-09-09/04-开源项目.md", import.meta.url,
), "utf8");

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

test("the new application column contains ten projects with source and license links", () => {
  assert.deepEqual(validateProjects(audit.openSourceProjects, projects), []);
});

test("a missing or repeated project cannot fill the daily ten", () => {
  const data = structuredClone(audit.openSourceProjects);
  data.projects.pop();
  assert.ok(validateProjects(data, projects).some((error) => error.includes("expected 10")));
  const duplicate = structuredClone(audit.openSourceProjects);
  duplicate.projects[1].repositoryUrl = duplicate.projects[0].repositoryUrl.toUpperCase() + "/";
  assert.ok(validateProjects(duplicate, projects).some((error) => error.includes("duplicate")));
});

test("project evidence must be accessible from the matching article", () => {
  const data = structuredClone(audit.openSourceProjects);
  data.projects[0].licenseUrl = "https://example.com/unverified-license";
  assert.ok(validateProjects(data, projects).some((error) => error.includes("license evidence")));
  const missingSource = projects.replaceAll(data.projects[0].repositoryUrl + ")", "https://example.com/)");
  assert.ok(validateProjects(data, missingSource).some((error) => error.includes("project source")));
});
