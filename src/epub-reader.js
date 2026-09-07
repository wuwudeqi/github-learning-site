import ePub from "epubjs";

// EPUB renders in sandboxed frames; all reader controls stay in the site document.
export async function openEPUB({
  doc,
  initial,
  element,
  onProgress,
  isCurrent,
  assetURL,
  escapeHTML,
  icon,
}) {
  let book,
    rendition,
    disposed = false,
    resizeObserver,
    resizeTimer;
  let busy = false,
    currentLocation,
    fontSize = Math.max(14, Math.min(28, Number(initial.epubFontSize) || 18));
  const cleanups = [];
  const cleanup = () => {
    if (disposed) return;
    disposed = true;
    clearTimeout(resizeTimer);
    resizeObserver?.disconnect();
    cleanups.forEach((fn) => fn());
    book?.destroy();
  };
  async function bounded(promise) {
    let timer;
    try {
      return await Promise.race([
        promise,
        new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error("EPUB 打开超时")), 25000);
        }),
      ]);
    } finally {
      clearTimeout(timer);
    }
  }
  try {
    const response = await fetch(assetURL(doc.file));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.arrayBuffer();
    if (!isCurrent()) return cleanup;
    book = ePub(undefined, { replacements: "blobUrl" });
    await bounded(book.open(data, "binary"));
    const navigation = await bounded(book.loaded.navigation);
    if (!isCurrent()) {
      cleanup();
      return cleanup;
    }
    const chapters = [];
    const flatten = (items, depth = 0) =>
      items.forEach((item) => {
        chapters.push({ href: item.href, label: item.label.trim(), depth });
        if (item.subitems?.length) flatten(item.subitems, depth + 1);
      });
    flatten(navigation.toc || []);
    if (!chapters.length)
      book.spine.spineItems.forEach((item, i) =>
        chapters.push({ href: item.href, label: `第 ${i + 1} 章`, depth: 0 }),
      );
    element.innerHTML = `<div class="sen-epub-layout"><div class="sen-epub-toolbar"><button class="read-button" id="epub-toc-toggle" aria-label="章节目录" aria-expanded="false">${icon("book")}<span>章节目录</span></button><label class="sen-epub-chapter-select"><span class="sr-only">跳转章节</span><select id="epub-chapter" aria-label="跳转章节">${chapters.map((c, i) => `<option value="${i}">${"　".repeat(Math.min(c.depth, 3))}${escapeHTML(c.label)}</option>`).join("")}</select></label><label class="sen-epub-font"><span>字号</span><select id="epub-font" aria-label="EPUB 字号">${[14, 16, 18, 20, 22, 24, 28].map((n) => `<option value="${n}" ${n === fontSize ? "selected" : ""}>${n}px</option>`).join("")}</select></label></div><div class="sen-epub-middle"><aside class="sen-epub-toc" aria-label="电子书目录" hidden><h2>章节目录</h2><nav>${chapters.map((c, i) => `<button data-epub-chapter="${i}" style="padding-left:${15 + Math.min(c.depth, 3) * 12}px">${escapeHTML(c.label)}</button>`).join("")}</nav></aside><div class="sen-epub-stage"><div id="epub-viewer" aria-label="EPUB 正文"></div></div></div><div class="sen-epub-footer"><button id="epub-prev" class="read-button">${icon("left")}上一页</button><span id="epub-position" role="status">正在排版…</span><button id="epub-next" class="read-button">下一页${icon("right")}</button></div><div id="epub-message" class="sen-epub-message" role="status"></div></div>`;
    const viewer = element.querySelector("#epub-viewer");
    const stage = element.querySelector(".sen-epub-stage");
    const chapterSelect = element.querySelector("#epub-chapter");
    const position = element.querySelector("#epub-position");
    const previous = element.querySelector("#epub-prev");
    const next = element.querySelector("#epub-next");
    rendition = book.renderTo(viewer, {
      width: stage.clientWidth,
      height: stage.clientHeight,
      flow: "paginated",
      spread: "none",
      manager: "default",
      allowScriptedContent: false,
      allowPopups: false,
    });
    const dark = document.documentElement.dataset.theme === "dark";
    rendition.themes.default({
      body: {
        color: `${dark ? "#d6e1d6" : "#283d36"} !important`,
        background: `${dark ? "#202d25" : "#fff"} !important`,
        "font-family": '"Songti SC", "Microsoft YaHei", serif',
        "line-height": "1.85 !important",
      },
      p: { "line-height": "1.85 !important" },
      img: { "max-width": "100% !important", "object-fit": "contain" },
      a: { color: `${dark ? "#80b9a0" : "#237665"} !important` },
    });
    rendition.themes.fontSize(`${fontSize}px`);
    function displayMessage(text) {
      if (!disposed) element.querySelector("#epub-message").textContent = text;
    }
    const chapterFor = (href) => {
      const clean = (value) => decodeURI(value || "").split("#")[0];
      return chapters.findIndex((c) => clean(c.href) === clean(href));
    };
    rendition.on("relocated", (location) => {
      if (disposed || !isCurrent()) return;
      currentLocation = location;
      const start = location.start;
      const chapterIndex = chapterFor(start.href);
      const chapter =
        chapterIndex >= 0
          ? chapters[chapterIndex].label
          : `第 ${start.index + 1} 章`;
      if (chapterIndex >= 0) chapterSelect.value = String(chapterIndex);
      element
        .querySelectorAll("[data-epub-chapter]")
        .forEach((btn) =>
          btn.classList.toggle(
            "active",
            Number(btn.dataset.epubChapter) === chapterIndex,
          ),
        );
      const page = start.displayed?.page || 1;
      const total = start.displayed?.total || 1;
      position.textContent = `${chapter} · 本章 ${page} / ${total} 页`;
      previous.disabled = busy || !!location.atStart;
      next.disabled = busy || !!location.atEnd;
      const progress = location.atEnd
        ? 1
        : Math.min(
            1,
            (start.index + (page - 1) / total) /
              Math.max(1, book.spine.spineItems.length),
          );
      onProgress({
        epubCfi: start.cfi,
        epubHref: start.href,
        chapter,
        progress,
        epubFontSize: fontSize,
      });
    });
    function setBusy(value) {
      busy = value;
      chapterSelect.disabled = value;
      element.querySelector("#epub-font").disabled = value;
      element
        .querySelectorAll("[data-epub-chapter]")
        .forEach((button) => (button.disabled = value));
      previous.disabled = value || !!currentLocation?.atStart;
      next.disabled = value || !!currentLocation?.atEnd;
    }
    async function navigate(action) {
      if (busy || disposed) return;
      setBusy(true);
      displayMessage("");
      try {
        await bounded(action());
      } catch (error) {
        if (!disposed) {
          console.error(error);
          displayMessage("暂时无法打开该章节，请重试或下载原书阅读。");
        }
      } finally {
        if (!disposed) setBusy(false);
      }
    }
    previous.onclick = () => navigate(() => rendition.prev());
    next.onclick = () => navigate(() => rendition.next());
    const jump = (i) => navigate(() => rendition.display(chapters[i].href));
    chapterSelect.onchange = () => jump(Number(chapterSelect.value));
    const toc = element.querySelector(".sen-epub-toc");
    const toggle = element.querySelector("#epub-toc-toggle");
    toggle.onclick = () => {
      toc.hidden = !toc.hidden;
      toggle.setAttribute("aria-expanded", String(!toc.hidden));
    };
    element.querySelectorAll("[data-epub-chapter]").forEach(
      (btn) =>
        (btn.onclick = () => {
          jump(Number(btn.dataset.epubChapter));
          if (innerWidth < 700) {
            toc.hidden = true;
            toggle.setAttribute("aria-expanded", "false");
          }
        }),
    );
    element.querySelector("#epub-font").onchange = (e) =>
      navigate(async () => {
        const cfi = currentLocation?.start.cfi;
        fontSize = Number(e.target.value);
        onProgress({ epubFontSize: fontSize });
        rendition.themes.fontSize(`${fontSize}px`);
        if (cfi) await rendition.display(cfi);
      });
    const onKey = (e) => {
      if (
        disposed ||
        !isCurrent() ||
        e.altKey ||
        e.ctrlKey ||
        e.metaKey ||
        ["INPUT", "SELECT", "TEXTAREA", "BUTTON"].includes(e.target?.tagName)
      )
        return;
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault();
        navigate(() =>
          e.key === "ArrowLeft" ? rendition.prev() : rendition.next(),
        );
      }
      if (e.key === "Escape") location.hash = "/";
    };
    document.addEventListener("keydown", onKey);
    rendition.on("keydown", onKey);
    cleanups.push(() => document.removeEventListener("keydown", onKey));
    rendition.hooks.content.register((contents) => {
      contents.document.documentElement.lang ||= "zh-CN";
      const iframe = viewer.querySelector("iframe");
      if (iframe) iframe.title = `${doc.title} · EPUB 正文`;
    });
    try {
      await bounded(
        rendition.display(initial.epubCfi || initial.epubHref || undefined),
      );
    } catch (error) {
      if (!initial.epubCfi && !initial.epubHref) throw error;
      await bounded(rendition.display());
      displayMessage("原阅读位置已变化，已从开头打开。");
    }
    if (!isCurrent()) {
      cleanup();
      return cleanup;
    }
    let lastWidth = stage.clientWidth,
      lastHeight = stage.clientHeight;
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (disposed || !isCurrent()) return;
        const w = stage.clientWidth,
          h = stage.clientHeight;
        if (w > 0 && h > 0 && (w !== lastWidth || h !== lastHeight)) {
          lastWidth = w;
          lastHeight = h;
          rendition.resize(w, h, currentLocation?.start.cfi);
        }
      }, 120);
    });
    resizeObserver.observe(stage);
    return cleanup;
  } catch (error) {
    cleanup();
    if (isCurrent()) {
      element.innerHTML = `<div class="empty-state">${icon("book")}<h3>这本 EPUB 暂时无法在线打开</h3><p>请确认它是完整、未加 DRM 的 EPUB 文件。你也可以下载后用本机阅读器打开。</p><a class="read-button primary" href="${assetURL(doc.file)}" download>下载原书 ${icon("download")}</a></div>`;
      console.error(error);
    }
    return cleanup;
  }
}
