// Folder paths are relative to content/. Only catalogued reading formats form entries.
export const categoryRoots = { 论文: "papers", 书籍: "books", 笔记: "notes" };
export const folderLabels = { papers: "论文", books: "书籍", notes: "笔记" };
export const readable = (doc) => ["MD", "PDF", "EPUB"].includes(doc.type);
export const documentPath = (doc) => doc.file.replace(/^documents\//, "");
export const parentPath = (doc) =>
  documentPath(doc).split("/").slice(0, -1).join("/");
export const filename = (doc) => documentPath(doc).split("/").at(-1);
export const naturalCompare = (a, b) =>
  a.localeCompare(b, "zh-CN", { numeric: true });
export function folderEntries(docs, path = "") {
  const folders = new Map();
  const files = [];
  const prefix = path ? `${path}/` : "";
  for (const doc of docs.filter(readable)) {
    const full = documentPath(doc);
    if (!full.startsWith(prefix)) continue;
    const rest = full.slice(prefix.length);
    const parts = rest.split("/");
    if (parts.length === 1) files.push(doc);
    else {
      const name = parts[0];
      const item = folders.get(name) || { name, path: prefix + name, count: 0 };
      item.count++;
      folders.set(name, item);
    }
  }
  return {
    folders: [...folders.values()].sort((a, b) =>
      naturalCompare(a.name, b.name),
    ),
    files,
  };
}
export function browseURL(view = "all", path = "") {
  return (
    "#/browse/" +
    [view, ...path.split("/").filter(Boolean)].map(encodeURIComponent).join("/")
  );
}
export function parseBrowse(hash) {
  if (hash === "" || hash === "#/" || hash === "#")
    return { view: "all", path: "" };
  if (!hash.startsWith("#/browse/")) return null;
  try {
    const [view, ...parts] = hash
      .slice("#/browse/".length)
      .split("/")
      .map(decodeURIComponent);
    if (
      !["all", "recent", "favorites", ...Object.keys(categoryRoots)].includes(
        view,
      )
    )
      return null;
    if (parts.some((p) => !p || p === "." || p === ".." || p.includes("/")))
      return null;
    const path = parts.join("/");
    if (
      categoryRoots[view] &&
      path !== categoryRoots[view] &&
      !path.startsWith(categoryRoots[view] + "/")
    )
      return null;
    if (["recent", "favorites"].includes(view) && path) return null;
    return { view, path };
  } catch {
    return null;
  }
}
