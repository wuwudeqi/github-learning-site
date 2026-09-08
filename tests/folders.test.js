import test from "node:test";
import assert from "node:assert/strict";
import {
  folderEntries,
  browseURL,
  parseBrowse,
  naturalCompare,
  filename,
} from "../src/folders.js";
const doc = (path, type = "MD") => ({ file: "documents/" + path, type });
test("only reading documents create folders, at arbitrary nesting depth", () => {
  const docs = [
    doc("notes/transformer/10.md"),
    doc("notes/transformer/2.md"),
    doc("notes/transformer/deep/1.pdf", "PDF"),
    doc("notes/images/test.svg", "SVG"),
    doc("notes/code/train.py", "PY"),
    doc("notes/intro.md"),
    doc("notes-old/other.md"),
  ];
  const entries = folderEntries(docs, "notes");
  assert.deepEqual(entries.folders, [
    { name: "transformer", path: "notes/transformer", count: 3 },
  ]);
  assert.deepEqual(entries.files.map(filename), ["intro.md"]);
  const nested = folderEntries(docs, "notes/transformer");
  assert.deepEqual(nested.files.map(filename).sort(naturalCompare), [
    "2.md",
    "10.md",
  ]);
  assert.equal(nested.folders[0].name, "deep");
  assert.equal(folderEntries(docs, "notes/images").files.length, 0);
});
test("folder links preserve unicode, spaces and URL punctuation on refresh", () => {
  const path = "notes/中文 # 100%/chapter?";
  assert.deepEqual(parseBrowse(browseURL("笔记", path)), {
    view: "笔记",
    path,
  });
  assert.deepEqual(parseBrowse("#/"), { view: "all", path: "" });
  for (const hash of [
    "#/browse/all/%E0%A4",
    "#/browse/all/..",
    "#/browse/all/a%2Fb",
    "#/browse/笔记/books",
    "#/browse/favorites/notes",
  ])
    assert.equal(parseBrowse(hash), null);
});

test("frontiers first at root, newest dates first, chapter filenames unchanged", () => {
  const docs = [
    doc("notes/a.md"),
    doc("books/a.pdf", "PDF"),
    doc("papers/a.pdf", "PDF"),
    doc("frontiers/2026/09/2026-09-08/00.md"),
    doc("frontiers/2026/09/2026-09-09/01.md"),
    doc("frontiers/2025/12/2025-12-31/00.md"),
  ];
  assert.deepEqual(
    folderEntries(docs).folders.map((f) => f.name),
    ["frontiers", "papers", "books", "notes"],
  );
  assert.deepEqual(
    folderEntries(docs, "frontiers").folders.map((f) => f.name),
    ["2026", "2025"],
  );
  assert.deepEqual(
    folderEntries(docs, "frontiers/2026/09").folders.map((f) => f.name),
    ["2026-09-09", "2026-09-08"],
  );
  assert.deepEqual(parseBrowse(browseURL("前沿", "frontiers")), {
    view: "前沿",
    path: "frontiers",
  });
});
