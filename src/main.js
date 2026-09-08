import "./style.css";
import {
  categoryRoots,
  folderLabels,
  readable,
  documentPath,
  parentPath,
  filename,
  naturalCompare,
  folderEntries,
  browseURL,
  parseBrowse,
} from "./folders.js";
import {
  createElement,
  Library,
  Clock3,
  Star,
  FileText,
  BookOpen,
  NotebookPen,
  Search,
  ArrowUpRight,
  ArrowLeft,
  ArrowRight,
  Download,
  Sun,
  Moon,
  PanelLeftClose,
  X,
  ChevronLeft,
  ChevronRight,
  Check,
  Menu,
  FolderOpen,
  SlidersHorizontal,
  CircleHelp,
} from "lucide";
const glyphs = {
  library: Library,
  clock: Clock3,
  star: Star,
  file: FileText,
  book: BookOpen,
  note: NotebookPen,
  search: Search,
  arrow: ArrowUpRight,
  back: ArrowLeft,
  next: ArrowRight,
  download: Download,
  sun: Sun,
  moon: Moon,
  close: X,
  left: ChevronLeft,
  right: ChevronRight,
  check: Check,
  menu: Menu,
  folder: FolderOpen,
  filter: SlidersHorizontal,
  help: CircleHelp,
};
export const icon = (name, cls = "") => {
  const el = createElement(glyphs[name] || FileText, {
    width: 20,
    height: 20,
    "stroke-width": 1.7,
    "aria-hidden": "true",
    class: cls,
  });
  return el.outerHTML;
};
export const escapeHTML = (value = "") =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export const assetURL = (file) =>
  new URL(
    import.meta.env.BASE_URL +
      file.split("/").map(encodeURIComponent).join("/"),
    location.origin,
  ).href;
const STORE = "sen-space:reading:v1";
let persisted = { documents: {}, theme: "light" };
let storageAvailable = true;
try {
  const saved = JSON.parse(localStorage.getItem(STORE) || "null");
  if (
    saved &&
    typeof saved.documents === "object" &&
    saved.documents &&
    !Array.isArray(saved.documents)
  )
    persisted = {
      documents: saved.documents,
      theme: saved.theme === "dark" ? "dark" : "light",
    };
  localStorage.setItem(STORE, JSON.stringify(persisted));
} catch {
  storageAvailable = false;
}
const app = document.querySelector("#app");
let documents = [];
let view = "all",
  filter = "all",
  query = "",
  sort = "filename";
let folderPath = "";
let readerReturn = "#/";
let lastBrowse = null;
let closeReader = null;
let routeToken = 0;
const record = (id) => persisted.documents[id] || {};
function save() {
  if (!storageAvailable) return;
  try {
    localStorage.setItem(STORE, JSON.stringify(persisted));
  } catch {
    storageAvailable = false;
    toast("浏览器无法保存记录，本次进度仅在当前页面保留。");
  }
}
function patchRecord(id, patch) {
  persisted.documents[id] = { ...record(id), ...patch };
  save();
}
function formatSize(size) {
  return size >= 1e6
    ? `${(size / 1e6).toFixed(1)} MB`
    : `${Math.max(1, Math.round(size / 1000))} KB`;
}
function formatDate(date) {
  return date.replaceAll("-", ".");
}
function badge(doc, large = false) {
  return `<span class="file-badge ${doc.type.toLowerCase()} ${large ? "large" : ""}" aria-label="${doc.type}"><span>${doc.type}</span></span>`;
}
function typeLabel(doc) {
  return doc.type === "MD" ? "Markdown" : doc.type;
}
function progressLabel(doc) {
  const r = record(doc.id);
  if (r.completed) return "已读完";
  if (doc.type === "EPUB" && r.chapter) return `读到：${escapeHTML(r.chapter)}`;
  if (doc.type === "PDF" && r.page)
    return `读到第 ${r.page}${r.pages ? ` / ${r.pages}` : ""} 页`;
  return r.visited
    ? `已阅读 ${Math.round((r.progress || 0) * 100)}%`
    : "尚未开始";
}
function bookmark(doc) {
  const starred = record(doc.id).favorite === true;
  return `<button class="icon-button favorite ${starred ? "active" : ""}" data-favorite="${doc.id}" title="${starred ? "取消收藏" : "收藏"}：${escapeHTML(doc.title)}" aria-label="${starred ? "取消收藏" : "收藏"}：${escapeHTML(doc.title)}" aria-pressed="${starred}">${icon("star")}</button>`;
}
function download(doc) {
  return `<a class="icon-button" href="${assetURL(doc.file)}" download="${escapeHTML(doc.file.split("/").at(-1))}" title="下载：${escapeHTML(doc.title)}" aria-label="下载：${escapeHTML(doc.title)}">${icon("download")}</a>`;
}
function toast(message) {
  document.querySelector(".toast")?.remove();
  const el = document.createElement("div");
  el.className = "toast";
  el.setAttribute("role", "status");
  el.textContent = message;
  document.body.append(el);
  setTimeout(() => el.remove(), 4500);
}
function applyTheme() {
  document.documentElement.dataset.theme = persisted.theme;
  document.querySelector('meta[name="theme-color"]').content =
    persisted.theme === "dark" ? "#192722" : "#237665";
}
applyTheme();
function shell() {
  app.innerHTML = `<a class="skip-link" href="#main-content">跳到主要内容</a><aside class="sen-sidebar" aria-label="主导航"><a href="#/" class="brand"><span class="brand-mark">夹</span><span>资料夹<small>A SPACE TO READ</small></span></a><div class="nav-caption">我的空间</div><nav class="main-nav"><button data-view="all">${icon("library")}<span>我的书架</span><small>${documents.length}</small></button><button data-view="recent">${icon("clock")}<span>最近阅读</span></button><button data-view="favorites">${icon("star")}<span>我的收藏</span><small id="favorite-count"></small></button></nav><div class="nav-divider"></div><div class="nav-caption">资料分类</div><nav class="category-nav">${[
    ["论文", "file"],
    ["书籍", "book"],
    ["笔记", "note"],
  ]
    .map(
      ([name, i]) =>
        `<button data-view="${name}">${icon(i)}<span>${name}</span><small>${documents.filter((d) => d.category === name).length}</small></button>`,
    )
    .join(
      "",
    )}</nav><div class="sen-sidebar-bottom"><div class="quiet-note"><span class="tiny-tree">✳</span><p>给思考留一点空间。</p><small>按自己的节奏，慢慢读。</small></div><button id="theme-toggle" class="theme-toggle"></button></div></aside><button class="sen-sidebar-scrim" aria-label="关闭导航"></button><div class="workspace"><header class="topbar"><div class="breadcrumb"><button class="icon-button mobile-menu" aria-label="打开导航">${icon("menu")}</button><span>个人阅读空间</span><span class="slash">/</span><span id="breadcrumb-current">我的书架</span></div><span class="local-status"><i></i>${storageAvailable ? "记录保存在此浏览器" : "当前浏览器无法保存记录"}</span></header><main id="main-content" tabindex="-1"></main><footer class="site-footer"><span>资料夹 <span class="footer-dot">·</span> 读过的，正在读的，值得再读的。</span><span>以阅读，连接新的想法 ${icon("arrow")}</span></footer></div><div id="reader-root"></div>`;
  document.querySelector(".brand").onclick = () => navigateLibrary("all");
  document.querySelectorAll("[data-view]").forEach((btn) => {
    btn.onclick = () => navigateLibrary(btn.dataset.view);
  });
  document.querySelector(".mobile-menu").onclick = () =>
    document.body.classList.add("nav-open");
  document.querySelector(".sen-sidebar-scrim").onclick = () =>
    document.body.classList.remove("nav-open");
  document.querySelector("#theme-toggle").onclick = () => {
    persisted.theme = persisted.theme === "dark" ? "light" : "dark";
    save();
    applyTheme();
    updateThemeButton();
  };
  updateThemeButton();
}
function updateThemeButton() {
  document.querySelector("#theme-toggle").innerHTML =
    `${icon(persisted.theme === "dark" ? "sun" : "moon")}<span>${persisted.theme === "dark" ? "切换浅色外观" : "切换深色外观"}</span><span class="theme-switch"><i></i></span>`;
}
function navigateLibrary(nextView) {
  filter = "all";
  query = "";
  sort = "filename";
  document.body.classList.remove("nav-open");
  const target = browseURL(nextView, categoryRoots[nextView] || "");
  if (location.hash === target) route();
  else location.hash = target;
}
function displayPath(path) {
  return path
    .split("/")
    .map((part, i) => (i === 0 ? folderLabels[part] || part : part))
    .join(" / ");
}
function folderBreadcrumbs() {
  const parts = folderPath.split("/").filter(Boolean);
  const links = [`<a href="${browseURL()}">我的书架</a>`];
  parts.forEach((part, i) => {
    const path = parts.slice(0, i + 1).join("/");
    const label = i === 0 ? folderLabels[part] || part : part;
    const crumbView =
      categoryRoots[view] && path.startsWith(categoryRoots[view])
        ? view
        : "all";
    links.push(
      `<span aria-hidden="true">/</span>${i === parts.length - 1 ? `<span aria-current="page">${escapeHTML(label)}</span>` : `<a href="${browseURL(crumbView, path)}">${escapeHTML(label)}</a>`}`,
    );
  });
  return `<nav class="folder-breadcrumbs" aria-label="文件夹路径">${links.join("")}</nav>`;
}
function filteredDocs() {
  let list = documents.filter(
    (d) =>
      (view === "all" ||
        (view === "recent" && record(d.id).visited) ||
        (view === "favorites" && record(d.id).favorite) ||
        d.category === view) &&
      (filter === "all" || d.type === filter),
  );
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  if (terms.length)
    list = list.filter((d) => {
      const hay = [
        d.title,
        d.author,
        d.description,
        documentPath(d),
        displayPath(parentPath(d)),
        ...d.tags,
        d.searchText,
      ]
        .join(" ")
        .toLocaleLowerCase();
      return terms.every((t) => hay.includes(t));
    });
  return list.sort((a, b) =>
    sort === "filename" && view !== "recent"
      ? naturalCompare(filename(a), filename(b))
      : sort === "title"
        ? a.title.localeCompare(b.title, "zh-CN")
        : view === "recent"
          ? (record(b.id).visited || 0) - (record(a.id).visited || 0)
          : sort === "oldest"
            ? a.date.localeCompare(b.date)
            : b.date.localeCompare(a.date),
  );
}
function renderLibrary() {
  const main = document.querySelector("main");
  if (!main) return;
  const titles = {
    all: "我的书架",
    recent: "最近阅读",
    favorites: "我的收藏",
    论文: "论文",
    书籍: "书籍",
    笔记: "学习笔记",
  };
  const currentTitle = folderPath
    ? folderPath.includes("/")
      ? folderPath.split("/").at(-1)
      : folderLabels[folderPath] || folderPath
    : titles[view];
  document.querySelector("#breadcrumb-current").textContent = currentTitle;
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.classList.toggle("selected", b.dataset.view === view);
    b.setAttribute("aria-current", b.dataset.view === view ? "page" : "false");
  });
  document.querySelector("#favorite-count").textContent = documents.filter(
    (d) => record(d.id).favorite,
  ).length;
  const recent = documents
    .filter((d) => record(d.id).visited && !record(d.id).completed)
    .sort((a, b) => record(b.id).visited - record(a.id).visited)
    .slice(0, 2);
  main.innerHTML = `<section class="page-heading"><div><div class="eyebrow">YOUR PERSONAL LIBRARY</div><h1>${escapeHTML(currentTitle)}<span class="heading-period">.</span></h1><p>${view === "all" ? "读过的，正在读的，值得再读的。" : view === "recent" ? "接着上次的地方，继续探索。" : view === "favorites" ? "把值得再读的内容，留在手边。" : "让好问题，带来新的理解。"}</p></div><label class="search-box">${icon("search")}<input id="search" type="search" placeholder="搜索标题、作者或正文…" value="${escapeHTML(query)}" aria-label="搜索资料" autocomplete="off"/><kbd>/</kbd></label></section>${view === "all" && !folderPath && !query.trim() && recent.length ? `<section class="continue-section"><div class="section-heading"><h2>${recent.length ? "继续阅读" : "从这一页开始"}</h2><span>${recent.length ? "留在上次的地方，等你回来" : "你的阅读空间，准备好了"}</span></div><div class="continue-grid">${(recent.length ? recent : [documents[0], documents.find((d) => d.type === "PDF")].filter(Boolean)).map((d, i) => `<article class="continue-card ${i === 0 ? "featured" : ""}"><div class="card-top"><span class="mini-label">${d.category} ${d.sample ? " / 示例" : ""}</span>${bookmark(d)}</div><div class="card-content">${badge(d, true)}<div><h3><a href="#/read/${d.id}">${escapeHTML(d.title)}</a></h3><p>${record(d.id).visited ? progressLabel(d) : escapeHTML(d.description)}</p></div></div><div class="card-bottom"><div class="card-progress"><div class="track"><i style="width:${record(d.id).completed ? 100 : Math.min(100, Math.round((record(d.id).progress || 0) * 100))}%"></i></div><small>${record(d.id).visited ? progressLabel(d) : `${typeLabel(d)} 文档 · ${formatSize(d.size)}`}</small></div><a class="read-button ${i === 0 ? "primary" : ""}" href="#/read/${d.id}">${record(d.id).visited ? "继续阅读" : "开始阅读"}${icon("next")}</a></div></article>`).join("")}</div></section>` : ""}<section class="library-section"><div class="section-heading library-title"><h2>${folderPath ? "当前文件夹" : view === "all" ? "全部资料" : titles[view]} <span id="result-count" class="count-badge"></span></h2>${documents.every((d) => d.sample) ? '<span class="sample-note">当前内容为示例，可替换为你的资料</span>' : ""}</div><div class="library-toolbar"><div class="type-tabs" role="group" aria-label="文件类型筛选">${[
    ["all", "全部"],
    ["PDF", "PDF"],
    ["MD", "Markdown"],
    ["EPUB", "EPUB"],
  ]
    .map(
      ([val, title]) =>
        `<button data-filter="${val}" class="${filter === val ? "selected" : ""}" aria-pressed="${filter === val}">${title}</button>`,
    )
    .join(
      "",
    )}</div><label class="sort-control">${icon("filter")}<select id="sort" aria-label="排序方式"><option value="filename">文件名排序</option><option value="newest">最近更新</option><option value="oldest">最早更新</option><option value="title">标题排序</option></select></label></div><div id="folder-navigation"></div><div id="document-list"></div><div class="library-bottom"><span id="list-summary"></span><span>PDF / Markdown / EPUB</span></div></section>`;
  document.querySelector("#search").oninput = (e) => {
    query = e.target.value;
    renderRows();
  };
  document.querySelector("#sort").value = sort;
  document.querySelector("#sort").onchange = (e) => {
    sort = e.target.value;
    renderRows();
  };
  document.querySelectorAll("[data-filter]").forEach(
    (b) =>
      (b.onclick = () => {
        filter = b.dataset.filter;
        document.querySelectorAll("[data-filter]").forEach((t) => {
          t.classList.toggle("selected", t.dataset.filter === filter);
          t.setAttribute("aria-pressed", String(t.dataset.filter === filter));
        });
        renderRows();
      }),
  );
  bindBookmarks(main);
  renderRows();
}
function renderRows() {
  const candidates = filteredDocs();
  const hierarchical = !query.trim() && !["recent", "favorites"].includes(view);
  const entries = hierarchical
    ? folderEntries(candidates, folderPath)
    : { folders: [], files: candidates };
  const list = entries.files;
  const container = document.querySelector("#document-list");
  if (!container) return;
  document.querySelector("#folder-navigation").innerHTML = ![
    "recent",
    "favorites",
  ].includes(view)
    ? folderBreadcrumbs() +
      (query.trim()
        ? `<p class="folder-hint">搜索当前分类的所有文件夹 · 清空搜索返回原目录</p>`
        : "")
    : "";
  document.querySelector("#result-count").textContent =
    entries.folders.length + list.length;
  document.querySelector("#list-summary").textContent = query.trim()
    ? `找到 ${list.length} 份相关资料`
    : hierarchical
      ? `${entries.folders.length} 个文件夹 · ${list.length} 份文档`
      : `共 ${list.length} 份资料 · 点击标题即可阅读`;
  const folderRows = entries.folders
    .map(
      (f) =>
        `<tr class="folder-row"><td><div class="document-name"><span class="folder-badge">${icon("folder")}</span><div><a class="document-title folder-link" href="${browseURL(view, f.path)}">${escapeHTML(folderPath ? f.name : folderLabels[f.name] || f.name)}</a><p>${escapeHTML(f.name)} / · ${f.count} 份文档（含子文件夹）</p></div></div></td><td><span class="topic-tag">文件夹</span></td><td class="meta-cell">—</td><td class="meta-cell date-cell">—</td><td><a class="icon-button" href="${browseURL(view, f.path)}" aria-label="打开文件夹 ${escapeHTML(f.name)}">${icon("right")}</a></td></tr>`,
    )
    .join("");
  container.innerHTML =
    list.length || entries.folders.length
      ? `<table class="document-table"><thead><tr><th scope="col">资料名称</th><th scope="col">分类与标签</th><th scope="col">大小</th><th scope="col">更新日期</th><th scope="col"><span class="sr-only">操作</span></th></tr></thead><tbody>${folderRows}${list
          .map(
            (d) =>
              `<tr><td><div class="document-name">${badge(d)}<div><a class="document-title" href="#/read/${d.id}">${escapeHTML(d.title)}${record(d.id).completed ? `<span class="completed-check" title="已读完">${icon("check")}</span>` : ""}</a><p title="${escapeHTML(documentPath(d))}">${escapeHTML(filename(d))}</p>${!hierarchical ? `<a class="document-path" href="${browseURL("all", parentPath(d))}">${escapeHTML(displayPath(parentPath(d)) || "我的书架")}</a>` : ""}</div></div></td><td><div class="tags"><span class="category-tag category-${d.category}">${d.category}</span>${d.tags
                .slice(0, 1)
                .map((t) => `<span class="topic-tag">${escapeHTML(t)}</span>`)
                .join(
                  "",
                )}</div></td><td class="meta-cell">${formatSize(d.size)}</td><td class="meta-cell date-cell">${formatDate(d.date)}</td><td><div class="row-actions">${bookmark(d)}${download(d)}</div></td></tr>`,
          )
          .join("")}</tbody></table>`
      : `<div class="empty-state">${icon(query ? "search" : view === "favorites" ? "star" : "book")}<h3>${query ? "还没有找到匹配的资料" : view === "favorites" ? "把喜欢的内容留在这里" : view === "recent" ? "阅读，从打开一份资料开始" : "当前文件夹没有符合条件的文档"}</h3><p>${query ? "试试更短的关键词，或切换文件类型。" : view === "favorites" ? "点击资料旁的星形图标，就能加入收藏。" : "回到书架，挑选一份想读的内容。"}</p><button id="reset-filters" class="read-button">${query ? "清除筛选" : "浏览全部资料"}${icon("next")}</button></div>`;
  bindBookmarks(container);
  document.querySelector("#reset-filters")?.addEventListener("click", () => {
    if (query.trim() || filter !== "all") {
      query = "";
      filter = "all";
      renderLibrary();
    } else navigateLibrary("all");
  });
}
function bindBookmarks(root) {
  root.querySelectorAll("[data-favorite]").forEach(
    (b) =>
      (b.onclick = () => {
        const id = b.dataset.favorite;
        patchRecord(id, { favorite: !record(id).favorite });
        const doc = documents.find((d) => d.id === id);
        document.querySelectorAll(`[data-favorite="${id}"]`).forEach((el) => {
          const starred = record(id).favorite;
          el.classList.toggle("active", starred);
          el.setAttribute("aria-pressed", String(starred));
          el.setAttribute(
            "aria-label",
            `${starred ? "取消收藏" : "收藏"}：${doc.title}`,
          );
          el.title = el.getAttribute("aria-label");
        });
        document.querySelector("#favorite-count").textContent =
          documents.filter((d) => record(d.id).favorite).length;
        if (view === "favorites" && !location.hash.startsWith("#/read/"))
          renderRows();
      }),
  );
}
async function route() {
  if (closeReader) {
    closeReader();
    closeReader = null;
  }
  const token = ++routeToken;
  document.body.classList.remove("reading");
  const root = document.querySelector("#reader-root");
  root.innerHTML = "";
  document.querySelector(".workspace").inert = false;
  document.querySelector(".sen-sidebar").inert = false;
  const match = location.hash.match(/^#\/read\/([^/]+)$/);
  if (!match) {
    const state = parseBrowse(location.hash);
    if (!state) {
      location.hash = browseURL();
      return;
    }
    if (lastBrowse && lastBrowse !== browseURL(state.view, state.path)) {
      query = "";
      filter = "all";
      sort = "filename";
    }
    view = state.view;
    folderPath = state.path;
    lastBrowse = browseURL(view, folderPath);
    document.title = `${folderPath ? displayPath(folderPath) : "我的书架"} · 资料夹`;
    renderLibrary();
    return;
  }
  const doc = documents.find((d) => d.id === match[1]);
  if (!doc) {
    toast("这份资料不存在或已移除。");
    location.hash = "/";
    return;
  }
  readerReturn =
    lastBrowse ||
    browseURL(
      Object.keys(categoryRoots).find(
        (key) => parentPath(doc).split("/")[0] === categoryRoots[key],
      ) || "all",
      parentPath(doc),
    );
  const initial = { ...record(doc.id) };
  patchRecord(doc.id, { visited: Date.now() });
  document.title = `${doc.title} · 资料夹`;
  document.body.classList.add("reading");
  document.querySelector(".workspace").inert = true;
  document.querySelector(".sen-sidebar").inert = true;
  root.innerHTML = `<section class="reader" aria-label="文档阅读器"><header class="reader-header"><a href="${readerReturn}" class="reader-back" aria-label="返回书架">${icon("back")}<span>返回列表</span></a><span class="reader-separator"></span><div class="reader-doc-title"><small>${doc.category} ${doc.sample ? "· 示例文档" : ""}</small><h1>${escapeHTML(doc.title)}</h1></div><div class="reader-actions">${bookmark(doc)}<button class="read-button complete-button ${initial.completed ? "is-complete" : ""}">${icon("check")}<span>${initial.completed ? "已读完" : "标记已读"}</span></button><a class="read-button primary" href="${assetURL(doc.file)}" download>${icon("download")}<span>下载原文</span></a></div></header><div id="reader-body"><div class="loading-state"><span class="spinner"></span>正在打开文档…</div></div><footer class="reader-footer"><span>${typeLabel(doc)} 阅读器</span><span id="reading-save-status">${storageAvailable ? "阅读进度自动保存在当前浏览器" : "本地存储不可用，进度仅在本页保留"}</span></footer></section>`;
  bindBookmarks(root);
  root.querySelector(".reader-back").focus();
  const complete = root.querySelector(".complete-button");
  complete.onclick = () => {
    const done = !record(doc.id).completed;
    patchRecord(doc.id, { completed: done, ...(done ? { progress: 1 } : {}) });
    complete.classList.toggle("is-complete", done);
    complete.querySelector("span").textContent = done ? "已读完" : "标记已读";
    toast(done ? "已标记为读完" : "已恢复为在读");
  };
  try {
    const { openReader } = await import("./reader.js");
    if (token !== routeToken) return;
    const cleanup = await openReader({
      doc,
      initial,
      element: document.querySelector("#reader-body"),
      onProgress: (patch) => {
        if (token !== routeToken) return;
        patchRecord(doc.id, patch);
      },
      isCurrent: () => token === routeToken,
      assetURL,
      escapeHTML,
      icon,
    });
    if (token !== routeToken) cleanup?.();
    else closeReader = cleanup;
  } catch (error) {
    if (token !== routeToken) return;
    console.error(error);
    document.querySelector("#reader-body").innerHTML =
      `<div class="empty-state">${icon("file")}<h3>暂时无法打开这份文档</h3><p>文件可能无法读取。你可以重新打开，或下载原文件阅读。</p><a class="read-button primary" href="${assetURL(doc.file)}" download>下载原文件 ${icon("download")}</a></div>`;
  }
}
window.addEventListener("hashchange", route);
window.addEventListener("keydown", (e) => {
  if (
    e.key === "/" &&
    !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) &&
    !document.body.classList.contains("reading")
  ) {
    e.preventDefault();
    document.querySelector("#search")?.focus();
  }
  if (e.key === "Escape") {
    document.body.classList.remove("nav-open");
    if (document.body.classList.contains("reading"))
      location.hash = readerReturn;
  }
});
window.addEventListener("storage", (e) => {
  if (e.key !== STORE || !e.newValue) return;
  try {
    const next = JSON.parse(e.newValue);
    if (next.documents && typeof next.documents === "object") {
      persisted = next;
      applyTheme();
      updateThemeButton();
      if (!document.body.classList.contains("reading")) renderLibrary();
    }
  } catch {}
});
try {
  const response = await fetch(assetURL("catalog.json"));
  if (!response.ok) throw new Error("资料目录加载失败");
  documents = (await response.json()).documents.filter(readable);
  shell();
  renderLibrary();
  await route();
} catch (error) {
  console.error(error);
  app.innerHTML = `<main class="startup-error"><span class="brand-mark">夹</span><h1>书架暂时没有打开</h1><p>请检查网络连接，然后重新加载页面。</p><button class="read-button primary" id="reload">重新加载</button></main>`;
  document.querySelector("#reload").onclick = () => location.reload();
}
