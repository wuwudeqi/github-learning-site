const CALLOUTS = {
  NOTE: { label: "举个例子", symbol: "i" },
  TIP: { label: "先记住", symbol: "✓" },
  IMPORTANT: { label: "面试重点", symbol: "★" },
  WARNING: { label: "容易踩坑", symbol: "!" },
};

// Work on sanitized DOM. Titles remain text; document HTML cannot add styles.
export function enhanceCallouts(content) {
  for (const quote of content.querySelectorAll("blockquote")) {
    const paragraph = quote.firstElementChild;
    if (paragraph?.tagName !== "P") continue;
    const first = paragraph.firstChild;
    if (first?.nodeType !== 3) continue;
    const match = first.textContent.match(
      /^\[!(NOTE|TIP|IMPORTANT|WARNING)\](?:[ \t]+([^\n]*))?(?:\n|$)/,
    );
    if (!match) continue;
    const type = match[1];
    const config = CALLOUTS[type];
    first.textContent = first.textContent.slice(match[0].length);
    if (!paragraph.textContent.trim() && !paragraph.children.length)
      paragraph.remove();
    const title = document.createElement("p");
    title.className = "reading-callout-title";
    const symbol = document.createElement("span");
    symbol.className = "reading-callout-symbol";
    symbol.setAttribute("aria-hidden", "true");
    symbol.textContent = config.symbol;
    title.append(
      symbol,
      document.createTextNode(match[2]?.trim() || config.label),
    );
    quote.classList.add(
      "reading-callout",
      `reading-callout-${type.toLowerCase()}`,
    );
    quote.setAttribute("role", "note");
    quote.prepend(title);
  }
}

export function enhanceLearningFigures(content) {
  for (const img of content.querySelectorAll("img")) {
    const parent = img.parentElement;
    // Only standalone figures; leave inline images and authored links alone.
    if (
      parent?.tagName !== "P" ||
      parent.children.length !== 1 ||
      parent.textContent.trim()
    )
      continue;
    let target;
    try {
      target = new URL(img.src);
    } catch {
      continue;
    }
    if (
      target.origin !== location.origin ||
      !["http:", "https:"].includes(target.protocol)
    )
      continue;
    const figure = document.createElement("figure");
    figure.className = "learning-figure";
    const link = document.createElement("a");
    link.href = target.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute(
      "aria-label",
      `查看大图：${img.alt || "文中示意图"}（新标签页）`,
    );
    link.append(img);
    const caption = document.createElement("figcaption");
    const label = document.createElement("span");
    label.textContent = img.alt || "示意图";
    const hint = document.createElement("span");
    hint.className = "learning-figure-hint";
    hint.textContent = "点击图片查看大图 ↗";
    caption.append(label, hint);
    figure.append(link, caption);
    parent.replaceWith(figure);
  }
}
