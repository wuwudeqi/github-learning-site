"""Read the source files, never the evaluation answers. HTML fixtures are simulated Wiki pages."""
from dataclasses import dataclass, field
from pathlib import Path
import json
from bs4 import BeautifulSoup, Tag
from pypdf import PdfReader


@dataclass(frozen=True)
class Section:
    doc_id: str
    section_id: str
    title: str
    heading: str
    text: str
    metadata: dict = field(default_factory=dict)


def render_block(node: Tag) -> str:
    if node.name == "pre":
        return "```\n" + node.get_text().strip("\n") + "\n```"
    if node.name in {"ol", "ul"}:
        return "\n".join(f"{i}. {li.get_text(' ', strip=True)}" if node.name == "ol"
                         else f"- {li.get_text(' ', strip=True)}"
                         for i, li in enumerate(node.find_all("li", recursive=False), 1))
    if node.name == "table":
        rows = [[cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
                for row in node.find_all("tr")]
        return "\n".join(" | ".join(cells) for cells in rows if cells)
    return node.get_text("\n", strip=True)


def parse_html(path: Path, metadata: dict) -> list[Section]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    main = soup.find("main") or soup.find("article")
    if main is None:
        raise ValueError(f"{path.name}: missing main/article; choose a site-specific body selector")
    for node in main.select("script, style, nav, aside, footer"):
        node.decompose()
    for anchor in main.find_all("a", href=True):
        label, href = anchor.get_text(" ", strip=True), anchor["href"]
        anchor.replace_with(label if label == href else f"{label} ({href})")
    sections = []
    # h2 sections are the fixture's authoring contract. Nested tables/lists keep their text.
    for heading in main.find_all("h2"):
        section_id = heading.get("id")
        if not section_id:
            raise ValueError(f"{path.name}: h2 needs a stable id")
        parts = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling.name == "h2":
                break
            if isinstance(sibling, Tag):
                text = render_block(sibling)
                if text:
                    parts.append(text)
        text = "\n\n".join(parts).strip()
        if text:
            sections.append(Section(metadata["doc_id"], section_id, metadata["title"],
                                    heading.get_text(" ", strip=True), text,
                                    {k: v for k, v in metadata.items() if k != "sections"}))
    if not sections:
        raise ValueError(f"{path.name}: no usable sections; inspect extraction before indexing")
    return sections


def parse_pdf(path: Path, metadata: dict) -> list[Section]:
    """Text PDF only. Page boundaries are provenance; they are not reliable semantic headings."""
    sections = []
    for page_no, page in enumerate(PdfReader(path).pages, 1):
        text = (page.extract_text() or "").strip()
        if not text:
            raise ValueError(f"{path.name} page {page_no}: no text; OCR/layout review required")
        sections.append(Section(metadata["doc_id"], f"page-{page_no}", metadata["title"],
                                f"第 {page_no} 页", text,
                                {**metadata, "source_kind": "pdf", "page": page_no}))
    return sections


def load_corpus(root: Path) -> list[Section]:
    records = [json.loads(line) for line in (root / "data/corpus.jsonl").read_text().splitlines() if line]
    seen = set()
    sections = []
    for record in records:
        if record["doc_id"] in seen:
            raise ValueError("duplicate document id")
        seen.add(record["doc_id"])
        parsed = parse_html(root / record["source_path"], record)
        expected_ids = {s["section_id"] for s in record["sections"]}
        if {s.section_id for s in parsed} != expected_ids:
            raise ValueError(f"{record['doc_id']}: HTML and manifest section IDs differ")
        sections.extend(parsed)
    return sections
