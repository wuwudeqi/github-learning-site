import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import matter from "gray-matter";
import {
  checkFrontiers,
  issueDirectory,
  issueFiles,
  validateDate,
} from "./check-frontiers.mjs";

async function filesIn(dir) {
  const result = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (
      entry.name.startsWith(".") ||
      entry.name === "__pycache__" ||
      /\.py[co]$/.test(entry.name)
    )
      continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) result.push(...(await filesIn(full)));
    else if (!entry.name.startsWith(".") && !entry.name.endsWith(".json"))
      result.push(full);
  }
  return result;
}

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");

async function main() {
  const args = process.argv.slice(2);
  if (args.length !== 2 || args[0] !== "--date") {
    throw new Error(
      "用法: node scripts/verify-frontiers-published.mjs --date YYYY-MM-DD",
    );
  }
  const date = validateDate(args[1]);
  await checkFrontiers(date);
  const base = "https://wuwudeqi.github.io/github-learning-site/";
  const fetchBytes = async (relative) => {
    const url = new URL(relative, base);
    url.searchParams.set("verify", String(Date.now()));
    const response = await fetch(url, {
      signal: AbortSignal.timeout(30000),
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`${response.status}: ${url.pathname}`);
    return Buffer.from(await response.arrayBuffer());
  };
  const catalog = JSON.parse((await fetchBytes("catalog.json")).toString());
  const dir = issueDirectory(date);
  for (const name of issueFiles) {
    const relative = path.join(dir, name).replace(/^content\//, "documents/");
    const document = catalog.documents?.find((item) => item.file === relative);
    if (!document || document.date !== date)
      throw new Error(`${date} 尚未进入线上目录: ${name}`);
  }
  const files = await filesIn(dir);
  const audit = JSON.parse(
    await readFile(`docs/frontiers-source-audits/${date}.json`, "utf8"),
  );
  const selectedPaperPaths = new Set(
    (audit.expandedSelections?.papers ?? []).map((paper) => paper.archivePath),
  );
  for (const file of await filesIn("content/papers/frontiers")) {
    if (!file.endsWith(".md")) continue;
    const { data } = matter(await readFile(file, "utf8"));
    if (String(data.date) !== date && !selectedPaperPaths.has(file)) continue;
    const relative = file.replace(/^content\//, "documents/");
    if (
      !catalog.documents?.some(
        (item) =>
          item.file === relative &&
          item.id === data.id &&
          item.date === String(data.date),
      )
    ) {
      throw new Error(`当期论文阅读卡尚未进入线上目录: ${file}`);
    }
    files.push(file);
  }
  for (const file of files) {
    const relative = file.replace(/^content\//, "documents/");
    const local = await readFile(file);
    // catalog.mjs removes frontmatter from published Markdown.
    const published = file.endsWith(".md")
      ? Buffer.from(matter(local.toString()).content.trimStart())
      : local;
    if (sha(published) !== sha(await fetchBytes(relative))) {
      throw new Error(`线上内容与本地不一致: ${relative}`);
    }
  }
  console.log(
    JSON.stringify({
      issueDate: date,
      verifiedFiles: files.length,
      verifiedAt: new Date().toISOString(),
      publishedUrl: `${base}#/read/frontiers-${date}-overview`,
    }),
  );
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
