import {
  readdir,
  readFile,
  stat,
  mkdir,
  writeFile,
  rm,
  cp,
} from "node:fs/promises";
import path from "node:path";
import matter from "gray-matter";
const root = process.cwd();
const content = path.join(root, "content");
const output = path.join(root, "public");
const ids = new Set();
const docs = [];
async function walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(file);
      continue;
    }
    const extension = path.extname(file).toLowerCase();
    if (![".md", ".pdf", ".epub"].includes(extension)) continue;
    const relative = path.relative(content, file).split(path.sep).join("/");
    let meta,
      body = "";
    if (extension === ".md") {
      const parsed = matter(await readFile(file, "utf8"));
      meta = parsed.data;
      body = parsed.content;
    } else {
      try {
        meta = JSON.parse(
          await readFile(file.replace(/\.(pdf|epub)$/i, ".json"), "utf8"),
        );
      } catch {
        throw new Error(`${relative}: PDF / EPUB 需要同名 .json 元数据文件`);
      }
    }
    if (!meta.id || !/^[a-z0-9][a-z0-9-]*$/.test(meta.id) || ids.has(meta.id))
      throw new Error(`${relative}: id 必须为不重复的英文小写、数字或连字符`);
    if (!meta.title || !["论文", "书籍", "笔记"].includes(meta.category))
      throw new Error(`${relative}: 缺少标题或有效分类`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(meta.date)))
      throw new Error(`${relative}: date 必须是带引号的 YYYY-MM-DD`);
    ids.add(meta.id);
    const size = (await stat(file)).size;
    if (size > 100 * 1024 ** 2)
      throw new Error(`${relative}: 单文件超过 GitHub 常规仓库 100 MiB 限制`);
    docs.push({
      id: meta.id,
      title: String(meta.title),
      category: meta.category,
      author: String(meta.author || "个人整理"),
      description: String(meta.description || ""),
      tags: Array.isArray(meta.tags) ? meta.tags.map(String) : [],
      date: String(meta.date),
      sample: meta.sample === true,
      type: extension.slice(1).toUpperCase(),
      file: `documents/${relative}`,
      size,
      searchText: body
        .replace(/<[^>]*>/g, " ")
        .replace(/[#*`>\[\]]/g, " ")
        .slice(0, 180000),
    });
  }
}
await mkdir(output, { recursive: true });
await walk(content);
docs.sort((a, b) => b.date.localeCompare(a.date));
await rm(path.join(output, "documents"), { recursive: true, force: true });
await cp(content, path.join(output, "documents"), {
  recursive: true,
  filter: (source) =>
    !source.endsWith(".json") && !source.endsWith(".DS_Store"),
});
// Strip frontmatter from published Markdown, keeping downloadable source clean.
for (const doc of docs.filter((d) => d.type === "MD")) {
  const source = await readFile(path.join(output, doc.file), "utf8");
  await writeFile(
    path.join(output, doc.file),
    matter(source).content.trimStart(),
  );
}
await writeFile(
  path.join(output, "catalog.json"),
  JSON.stringify({ documents: docs }, null, 2),
);
// Regenerate vendor assets cleanly; stale copied files must not enter a release.
await rm(path.join(output, "pdf-assets"), { recursive: true, force: true });
for (const dir of ["cmaps", "standard_fonts", "wasm"]) {
  await cp(
    path.join(root, "node_modules/pdfjs-dist", dir),
    path.join(output, "pdf-assets", dir),
    { recursive: true },
  );
}
console.log(`已生成 ${docs.length} 份资料的目录及 Markdown 搜索索引。`);
