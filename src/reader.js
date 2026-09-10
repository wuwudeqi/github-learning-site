import { marked } from "marked";
import DOMPurify from "dompurify";
import hljs from "highlight.js/lib/common";
import "highlight.js/styles/github.css";
import {
  enhanceCallouts,
  enhanceLearningFigures,
} from "./markdown-learning.js";
export async function openReader(ctx) {
  if (ctx.doc.type === "EPUB") {
    const { openEPUB } = await import("./epub-reader.js");
    return openEPUB(ctx);
  }
  return ctx.doc.type === "PDF" ? openPDF(ctx) : openMarkdown(ctx);
}
async function openMarkdown({
  doc,
  initial,
  element,
  onProgress,
  isCurrent,
  assetURL,
  escapeHTML,
  icon,
  resolveDocumentLink = () => null,
  initialAnchor,
}) {
  const response = await fetch(assetURL(doc.file));
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const source = await response.text();
  if (!isCurrent()) return () => {};
  const html = DOMPurify.sanitize(marked.parse(source), {
    FORBID_TAGS: [
      "iframe",
      "style",
      "form",
      "input",
      "button",
      "video",
      "audio",
      "source",
    ],
    FORBID_ATTR: ["style", "srcset"],
  });
  element.innerHTML = `<div class="markdown-layout"><div class="markdown-scroll" tabindex="0" aria-label="文章内容"><article class="markdown-article"><div class="article-kicker">${escapeHTML(doc.category)} <span> / </span> ${escapeHTML(doc.author)}</div><div class="markdown-content">${html}</div><div class="article-end"><span>✳</span><p>读到这里，停下来想一想。</p><small>把一个新想法，留给下一次阅读。</small></div></article></div><aside class="article-toc"><div class="toc-label">本页目录</div><nav></nav><div class="toc-foot">${icon("book")}<span>按自己的节奏，慢慢读。</span></div></aside></div>`;
  const content = element.querySelector(".markdown-content");
  enhanceCallouts(content);
  const isLearningNote = /^(budget-agent-|rag-|opencode-)/.test(doc.id);
  content.classList.toggle("learning-notes", isLearningNote);
  content
    .querySelectorAll("pre code")
    .forEach((block) => hljs.highlightElement(block));
  const url = assetURL(doc.file);
  content.querySelectorAll("[src]").forEach((el) => {
    try {
      const target = new URL(el.getAttribute("src"), url);
      if (target.origin !== location.origin) {
        const note = document.createElement("p");
        note.className = "blocked-resource";
        note.textContent = "外部图片未加载，请将图片与文档一起发布。";
        el.replaceWith(note);
      } else {
        el.src = target.href;
      }
    } catch {
      el.removeAttribute("src");
    }
  });
  content.querySelectorAll("a[href]").forEach((a) => {
    const href = a.getAttribute("href");
    if (href.startsWith("#")) {
      try {
        a.dataset.anchor = decodeURIComponent(href.slice(1));
      } catch {
        a.dataset.anchor = href.slice(1);
      }
      return;
    }
    try {
      const target = new URL(href, url);
      if (!["http:", "https:", "mailto:"].includes(target.protocol)) {
        a.removeAttribute("href");
        return;
      }
      const readerLink =
        !a.hasAttribute("download") && resolveDocumentLink(href, url);
      if (readerLink) {
        a.href = readerLink;
        a.removeAttribute("target");
        return;
      }
      a.href = target.href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    } catch {
      a.removeAttribute("href");
    }
  });
  if (isLearningNote) enhanceLearningFigures(content);
  const headings = [...content.querySelectorAll("h1,h2,h3")];
  const slugs = new Map();
  headings.forEach((h, i) => {
    const original = h.textContent
      .trim()
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s-]/gu, "")
      .replace(/\s+/g, "-");
    slugs.set(original, `section-${i}`);
    h.id = `section-${i}`;
  });
  const toc = element.querySelector(".article-toc nav");
  toc.innerHTML =
    headings
      .map(
        (h) =>
          `<a href="#${h.id}" class="toc-${h.tagName.toLowerCase()}" data-section="${h.id}">${escapeHTML(h.textContent)}</a>`,
      )
      .join("") || "<p>本文没有章节标题</p>";
  toc.querySelectorAll("a").forEach(
    (a) =>
      (a.onclick = (e) => {
        e.preventDefault();
        document
          .getElementById(a.dataset.section)
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }),
  );
  content.querySelectorAll("[data-anchor]").forEach(
    (a) =>
      (a.onclick = (e) => {
        e.preventDefault();
        const id = slugs.get(a.dataset.anchor) || a.dataset.anchor;
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
      }),
  );
  const scroller = element.querySelector(".markdown-scroll");
  let timer;
  let restoring = true;
  const oldProgress = Math.max(0, Math.min(1, Number(initial.progress) || 0));
  function update() {
    const available = scroller.scrollHeight - scroller.clientHeight;
    const progress =
      available > 0 ? Math.min(1, scroller.scrollTop / available) : 0;
    onProgress({ progress, scrollTop: scroller.scrollTop });
  }
  function activeHeading() {
    let active = headings[0];
    for (const h of headings) {
      if (
        h.getBoundingClientRect().top <
        scroller.getBoundingClientRect().top + 130
      )
        active = h;
    }
    toc
      .querySelectorAll("a")
      .forEach((a) =>
        a.classList.toggle("active", a.dataset.section === active?.id),
      );
  }
  const onScroll = () => {
    activeHeading();
    if (restoring) return;
    clearTimeout(timer);
    timer = setTimeout(update, 250);
  };
  scroller.addEventListener("scroll", onScroll, { passive: true });
  const images = [...content.querySelectorAll("img")];
  await Promise.all(
    images.map((img) =>
      img.complete
        ? Promise.resolve()
        : new Promise((resolve) => {
            img.onload = resolve;
            img.onerror = resolve;
            setTimeout(resolve, 1800);
          }),
    ),
  );
  if (!isCurrent()) return () => {};
  await new Promise((resolve) =>
    requestAnimationFrame(() => requestAnimationFrame(resolve)),
  );
  scroller.scrollTop =
    oldProgress * Math.max(0, scroller.scrollHeight - scroller.clientHeight);
  if (initialAnchor) {
    const targetId = slugs.get(initialAnchor) || initialAnchor;
    headings.find((h) => h.id === targetId)?.scrollIntoView({ block: "start" });
  }
  restoring = false;
  activeHeading();
  const flush = () => {
    clearTimeout(timer);
    update();
  };
  window.addEventListener("pagehide", flush);
  return () => {
    flush();
    scroller.removeEventListener("scroll", onScroll);
    window.removeEventListener("pagehide", flush);
  };
}
async function openPDF({
  doc,
  initial,
  element,
  onProgress,
  isCurrent,
  assetURL,
  escapeHTML,
  icon,
}) {
  const pdfjs = await import("pdfjs-dist");
  globalThis.pdfjsLib = pdfjs;
  const { getDocument, GlobalWorkerOptions } = pdfjs;
  const [{ EventBus, PDFViewer, PDFLinkService }, { default: workerURL }] =
    await Promise.all([
      import("pdfjs-dist/web/pdf_viewer.mjs"),
      import("pdfjs-dist/build/pdf.worker.min.mjs?url"),
      import("pdfjs-dist/web/pdf_viewer.css"),
    ]);
  if (!isCurrent()) return () => {};
  GlobalWorkerOptions.workerSrc = workerURL;
  element.innerHTML = `<div class="pdf-layout"><div class="pdf-toolbar"><div class="pdf-page-tools"><button class="icon-button" id="pdf-prev" aria-label="上一页">${icon("left")}</button><label>第 <input id="pdf-page" type="number" min="1" value="1" aria-label="页码"/> / <span id="pdf-total">—</span> 页</label><button class="icon-button" id="pdf-next" aria-label="下一页">${icon("right")}</button></div><label class="pdf-scale-label"><span>缩放</span><select id="pdf-scale" aria-label="PDF 缩放"><option value="page-width">适合宽度</option><option value="page-fit">适合页面</option><option value="0.75">75%</option><option value="1">100%</option><option value="1.25">125%</option><option value="1.5">150%</option><option value="2">200%</option></select></label><span class="pdf-hint">可选择文字 · 滚动翻页</span></div><div class="pdf-stage"><div id="pdf-container" tabindex="0" aria-label="PDF 内容"><div class="pdfViewer"></div></div></div></div>`;
  const container = element.querySelector("#pdf-container");
  const events = new EventBus();
  const linkService = new PDFLinkService({
    eventBus: events,
    externalLinkTarget: 2,
    externalLinkRel: "noopener noreferrer",
  });
  const viewer = new PDFViewer({
    container,
    viewer: container.querySelector(".pdfViewer"),
    eventBus: events,
    linkService,
    textLayerMode: 1,
    annotationMode: 0,
  });
  linkService.setViewer(viewer);
  let ready = false,
    disposed = false;
  const pageInput = element.querySelector("#pdf-page");
  const previous = element.querySelector("#pdf-prev"),
    next = element.querySelector("#pdf-next");
  const savePage = () => {
    if (ready && !disposed) {
      onProgress({
        page: viewer.currentPageNumber,
        pages: viewer.pagesCount,
        progress:
          viewer.pagesCount > 1
            ? (viewer.currentPageNumber - 1) / (viewer.pagesCount - 1)
            : 0,
      });
    }
  };
  events.on("pagesinit", () => {
    if (disposed) return;
    viewer.currentScaleValue = "page-width";
    viewer.currentPageNumber = Math.max(
      1,
      Math.min(Number(initial.page) || 1, viewer.pagesCount),
    );
    ready = true;
    refresh();
    savePage();
  });
  function refresh() {
    pageInput.value = viewer.currentPageNumber;
    pageInput.max = viewer.pagesCount;
    previous.disabled = viewer.currentPageNumber <= 1;
    next.disabled = viewer.currentPageNumber >= viewer.pagesCount;
  }
  events.on("pagechanging", () => {
    refresh();
    savePage();
  });
  previous.onclick = () => {
    viewer.currentPageNumber = Math.max(1, viewer.currentPageNumber - 1);
  };
  next.onclick = () => {
    viewer.currentPageNumber = Math.min(
      viewer.pagesCount,
      viewer.currentPageNumber + 1,
    );
  };
  pageInput.onchange = () => {
    viewer.currentPageNumber = Math.max(
      1,
      Math.min(viewer.pagesCount, Math.round(Number(pageInput.value) || 1)),
    );
    refresh();
  };
  pageInput.onkeydown = (e) => {
    if (e.key === "Enter") {
      pageInput.onchange();
      container.focus();
    }
  };
  element.querySelector("#pdf-scale").onchange = (e) =>
    (viewer.currentScaleValue = e.target.value);
  const loading = getDocument({
    url: assetURL(doc.file),
    cMapUrl: assetURL("pdf-assets/cmaps/"),
    cMapPacked: true,
    standardFontDataUrl: assetURL("pdf-assets/standard_fonts/"),
    wasmUrl: assetURL("pdf-assets/wasm/"),
    isEvalSupported: false,
  });
  const cleanup = () => {
    if (disposed) return;
    savePage();
    disposed = true;
    ready = false;
    window.removeEventListener("pagehide", savePage);
    viewer.setDocument(null);
    linkService.setDocument(null);
    loading.destroy().catch(() => {});
  };
  try {
    const pdf = await loading.promise;
    if (!isCurrent()) {
      cleanup();
      return () => {};
    }
    element.querySelector("#pdf-total").textContent = pdf.numPages;
    viewer.setDocument(pdf);
    linkService.setDocument(pdf);
    window.addEventListener("pagehide", savePage);
    return cleanup;
  } catch (err) {
    cleanup();
    throw err;
  }
}
