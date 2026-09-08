import test from "node:test";
import assert from "node:assert/strict";
import { createDocumentLinkResolver } from "../src/document-links.js";
const base = "https://example.com/site/";
const asset = (path) =>
  base + path.split("/").map(encodeURIComponent).join("/");
const docs = [
  { id: "one", type: "MD", file: "documents/notes/topic/01-基础.md" },
  { id: "two", type: "MD", file: "documents/notes/other/01-基础.md" },
  { id: "paper", type: "PDF", file: "documents/papers/paper.pdf" },
];
const resolve = createDocumentLinkResolver(docs, asset);
const source = asset("documents/notes/topic/00-路线.md");
test("relative and encoded paths resolve by full catalog path", () => {
  assert.equal(resolve("01-基础.md", source), "#/read/one");
  assert.equal(resolve("./01-%E5%9F%BA%E7%A1%80.md", source), "#/read/one");
  assert.equal(resolve("../other/01-基础.md", source), "#/read/two");
  assert.equal(resolve("../../papers/paper.pdf", source), "#/read/paper");
  assert.equal(
    resolve("01-基础.md#本章目标", source),
    "#/read/one?section=" + encodeURIComponent("本章目标"),
  );
});
test("external, missing, unsafe and malformed links are not internal documents", () => {
  for (const href of [
    "https://other.example/site/documents/notes/topic/01-基础.md",
    "missing.md",
    "code/train.py",
    "mailto:reader@example.com",
    "javascript:alert(1)",
    "%E0%A4.md",
  ])
    assert.equal(resolve(href, source), null);
});
