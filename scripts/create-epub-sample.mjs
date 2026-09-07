import JSZip from "jszip";
import { writeFile } from "node:fs/promises";
const zip = new JSZip();
zip.file("mimetype", "application/epub+zip", { compression: "STORE" });
zip.file(
  "META-INF/container.xml",
  '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
);
const titles = ["为阅读留一点空间", "让笔记成为自己的语言", "带着问题再次阅读"];
const paras = [
  "阅读不必从完成一本书开始。先给自己留出一段安静的时间，选一个真正想弄懂的问题。把复杂内容拆成小节，按自己的节奏向前走。",
  "遇到陌生概念时，可以暂时停下来，寻找它与已有知识之间的联系。理解通常不是一次完成的，它需要例子、尝试和再次回顾。",
  "读完一段内容，试着合上书，用自己的话说明核心意思。如果仍然说不清楚，这不是失败，而是下一次阅读的方向。",
  "笔记可以很短：一个问题、一句解释、一个例子。不要急着把原文全部抄下来，更重要的是留下自己思考过的痕迹。",
  "隔一段时间回到同一页，你可能会注意到以前忽略的细节。新的经历会改变理解，而阅读也会改变我们观察事物的方式。",
  "这些文字是森空间的原创示例，用于测试 EPUB 的中文排版、章节目录、翻页与进度恢复。它不是正式出版的书籍，可以直接替换为你自己的公开资料。",
];
zip.file(
  "OEBPS/styles.css",
  "body{margin:0;padding:18px 24px;font-family:serif;}h1{font-size:1.65em;margin:1em 0;}h2{font-size:1.2em;margin-top:1.6em;}p{margin:1em 0;text-align:justify;}img{max-width:100%;height:auto;}",
);
zip.file(
  "OEBPS/images/reading.svg",
  '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="140" viewBox="0 0 640 140"><rect width="640" height="140" rx="12" fill="#e6efe8"/><path d="M110 105V38q40-20 80 0 40-20 80 0v67q-40-20-80 0-40-20-80 0zm80-67v67" fill="none" stroke="#237665" stroke-width="4"/><text x="320" y="79" font-size="22" fill="#237665" font-family="serif">A SPACE TO READ</text></svg>',
);
for (let i = 0; i < 3; i++)
  zip.file(
    `OEBPS/chapter-${i + 1}.xhtml`,
    `<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" lang="zh-CN"><head><title>${titles[i]}</title><link rel="stylesheet" type="text/css" href="styles.css"/></head><body><h1>${i + 1}. ${titles[i]}</h1>${i === 0 ? '<img src="images/reading.svg" alt="阅读示意图"/>' : ""}<p>森空间 · 原创 EPUB 示例</p>${Array.from({ length: 24 }, (_, n) => `${n % 6 === 0 ? `<h2>第 ${Math.floor(n / 6) + 1} 节 · 慢慢理解</h2>` : ""}<p>${paras[(n + i) % paras.length]}</p>`).join("")}</body></html>`,
  );
zip.file(
  "OEBPS/nav.xhtml",
  `<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>目录</title></head><body><nav epub:type="toc" id="toc"><h1>目录</h1><ol>${titles.map((t, i) => `<li><a href="chapter-${i + 1}.xhtml">${t}</a></li>`).join("")}</ol></nav></body></html>`,
);
zip.file(
  "OEBPS/content.opf",
  `<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" unique-identifier="book-id" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">urn:sen-space:epub-demo</dc:identifier><dc:title>慢慢读：森空间 EPUB 体验书</dc:title><dc:creator>森空间</dc:creator><dc:language>zh-CN</dc:language><meta property="dcterms:modified">2026-09-08T00:00:00Z</meta></metadata><manifest><item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml"/><item id="style" href="styles.css" media-type="text/css"/><item id="image" href="images/reading.svg" media-type="image/svg+xml"/>${titles.map((_, i) => `<item id="c${i + 1}" href="chapter-${i + 1}.xhtml" media-type="application/xhtml+xml"/>`).join("")}</manifest><spine>${titles.map((_, i) => `<itemref idref="c${i + 1}"/>`).join("")}</spine></package>`,
);
await writeFile(
  "content/books/epub-demo.epub",
  await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
);
await writeFile(
  "content/books/epub-demo.json",
  JSON.stringify(
    {
      id: "epub-demo",
      title: "慢慢读：森空间 EPUB 体验书",
      category: "书籍",
      author: "森空间 · 原创示例",
      date: "2026-09-08",
      description:
        "三章中文原创示例，体验 EPUB 翻页、章节目录、字号调整和阅读进度恢复。",
      tags: ["EPUB", "阅读方法", "示例"],
      sample: true,
    },
    null,
    2,
  ) + "\n",
);
console.log("已生成原创 EPUB 示例书。");
