import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import { writeFile } from "node:fs/promises";
const examples = [
  {
    file: "content/books/reading-handbook",
    id: "reading-handbook",
    title: "阅读手册：建立自己的知识体系",
    category: "书籍",
    description: "一份原创英文示例 PDF，体验翻页、缩放和阅读位置恢复。",
    heading: "A SMALL READING HANDBOOK",
    pages: 5,
    tags: ["阅读方法", "示例"],
  },
  {
    file: "content/papers/learning-study",
    id: "learning-study",
    title: "从阅读到理解：主动学习札记",
    category: "论文",
    description: "原创排版演示稿，用于验证论文 PDF 阅读体验，非正式研究论文。",
    heading: "FROM READING TO UNDERSTANDING",
    pages: 3,
    tags: ["学习方法", "示例"],
  },
];
const sections = [
  "Begin with a question",
  "Read with attention",
  "Connect the ideas",
  "Explain in your own words",
  "Return and reflect",
];
for (const item of examples) {
  const pdf = await PDFDocument.create();
  const regular = await pdf.embedFont(StandardFonts.Helvetica);
  const bold = await pdf.embedFont(StandardFonts.HelveticaBold);
  const serif = await pdf.embedFont(StandardFonts.TimesRoman);
  for (let n = 0; n < item.pages; n++) {
    const page = pdf.addPage([595, 842]);
    const green = rgb(0.12, 0.39, 0.32);
    page.drawText("RESOURCE FOLDER  /  ORIGINAL DEMO DOCUMENT", {
      x: 54,
      y: 788,
      size: 9,
      font: regular,
      color: green,
    });
    page.drawLine({
      start: { x: 54, y: 773 },
      end: { x: 541, y: 773 },
      thickness: 1,
      color: green,
    });
    page.drawText(item.heading, {
      x: 54,
      y: 716,
      size: 18,
      font: bold,
      color: green,
    });
    page.drawText(`${String(n + 1).padStart(2, "0")}   ${sections[n]}`, {
      x: 54,
      y: 664,
      size: 22,
      font: serif,
    });
    let y = 619;
    const paragraphs = [
      "This original sample is included to demonstrate the PDF reader. It is not a published book or research paper. Replace it with your own public learning materials when you are ready.",
      "Reading begins with curiosity. Before opening a document, write down a question you would like to answer. A clear question helps you choose what deserves your attention.",
      "Work through one section at a time. Identify the main claim, the supporting evidence, and the conditions under which the claim holds. Keep these parts separate in your notes.",
      "Understanding is more than remembering a sentence. Try explaining an idea without looking at the page. Use a concrete example, then check whether your explanation matches the source.",
      "Good notes create connections. Link a new concept to something you already understand, and record the uncertainty that remains. Questions are useful results of reading too.",
      "This page is selectable text. Use the toolbar to change the page or zoom. Close the reader and open it again to check that your reading position is restored in this browser.",
    ];
    for (const para of paragraphs) {
      const words = para.split(" ");
      let line = "";
      for (const word of words) {
        if (serif.widthOfTextAtSize(line + word, 12) > 475) {
          page.drawText(line, {
            x: 54,
            y,
            size: 12,
            font: serif,
            color: rgb(0.2, 0.22, 0.22),
          });
          y -= 19;
          line = "";
        }
        line += word + " ";
      }
      if (line) {
        page.drawText(line, {
          x: 54,
          y,
          size: 12,
          font: serif,
          color: rgb(0.2, 0.22, 0.22),
        });
        y -= 19;
      }
      y -= 18;
    }
    page.drawText(
      `RESOURCE FOLDER     |     Demonstration copy                                      ${n + 1} / ${item.pages}`,
      { x: 54, y: 38, size: 9, font: regular, color: green },
    );
  }
  await writeFile(item.file + ".pdf", await pdf.save());
  const { file, heading, pages, ...meta } = item;
  await writeFile(
    item.file + ".json",
    JSON.stringify(
      {
        ...meta,
        author: "资料夹 · 原创示例",
        date: "2026-09-05",
        sample: true,
      },
      null,
      2,
    ),
  );
}
console.log("Created two original sample PDFs.");
