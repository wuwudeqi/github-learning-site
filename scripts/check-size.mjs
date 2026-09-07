import { readdir, stat } from "node:fs/promises";
import path from "node:path";
async function size(dir) {
  let bytes = 0;
  for (const e of await readdir(dir, { withFileTypes: true }))
    bytes += e.isDirectory()
      ? await size(path.join(dir, e.name))
      : (await stat(path.join(dir, e.name))).size;
  return bytes;
}
const bytes = await size("dist");
console.log(`发布体积：${(bytes / 1e6).toFixed(1)} MB / 1000 MB`);
if (bytes >= 1e9) throw new Error("超过 1 GB 发布上限，请减少文件或迁移附件。");
if (bytes >= 8e8) console.warn("容量提醒：已达到 800 MB，请规划附件迁移。");
