import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  canonicalSubject,
  validateTopicDeduplication,
  validateExpandedSelections,
} from "../scripts/check-frontiers.mjs";
const audit = JSON.parse(
  readFileSync("docs/frontiers-source-audits/2026-09-10.json", "utf8"),
);
const dir = "content/frontiers/2026/09/2026-09-10/";
const articles = {
  models: readFileSync(dir + "02-开源模型.md", "utf8"),
  papers: readFileSync(dir + "03-论文精选.md", "utf8"),
};
test("canonical model, paper version, and repository aliases share identities", () => {
  assert.equal(
    canonicalSubject("https://github.com/Owner/Repo.git/"),
    canonicalSubject("https://github.com/owner/repo/releases"),
  );
  assert.equal(
    canonicalSubject("https://arxiv.org/pdf/2609.04280v1"),
    canonicalSubject("https://arxiv.org/abs/2609.04280v2"),
  );
});
test("same model or news project cannot occupy two sections under different names", () => {
  const errors = validateTopicDeduplication([
    { id: "news", sourceUrl: "https://github.com/Tencent/teamai-cli" },
    { id: "project", repositoryUrl: "https://github.com/tencent/TEAMAI-CLI/" },
  ]);
  assert.match(errors.join("\n"), /duplicate topic/);
  const linked = validateTopicDeduplication([
    {
      id: "news",
      sourceUrl: "https://example.com/announcement",
      subjectKeys: ["model:tencent/auk"],
    },
    { id: "model", sourceUrl: "https://huggingface.co/tencent/AuK" },
  ]);
  assert.equal(linked.length, 1);
});
test("current six model and paper selections have matching evidence and distinct topics", () => {
  assert.deepEqual(validateExpandedSelections(audit, articles), []);
});
test("omitting a model, moving evidence, or repeating a paper fails validation", () => {
  const missing = structuredClone(audit);
  missing.expandedSelections.models.pop();
  assert.ok(
    validateExpandedSelections(missing, articles).some((x) =>
      x.includes("expected 6 models"),
    ),
  );
  const source = structuredClone(audit);
  source.expandedSelections.papers[0].sourceUrl =
    "https://arxiv.org/abs/2609.00000v1";
  assert.ok(
    validateExpandedSelections(source, articles).some((x) =>
      x.includes("missing papers source"),
    ),
  );
  const duplicate = structuredClone(audit);
  duplicate.expandedSelections.papers[1].sourceUrl =
    duplicate.expandedSelections.papers[0].sourceUrl;
  assert.ok(
    validateExpandedSelections(duplicate, articles).some((x) =>
      x.includes("duplicate topic"),
    ),
  );
});
