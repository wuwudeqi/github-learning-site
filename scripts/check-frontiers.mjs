import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const requiredProviders = [
  "OpenAI",
  "Anthropic",
  "Google",
  "Meta",
  "Microsoft",
  "xAI",
  "NVIDIA",
  "Alibaba",
  "DeepSeek",
  "ByteDance",
  "Tencent",
  "Baidu",
  "Zhipu",
  "Kimi",
  "MiniMax",
];

// This validates recorded evidence, not the truth or completeness of web research.
export function validateIssue(audit, news, date) {
  const errors = [];
  const require = (condition, message) => {
    if (!condition) errors.push(message);
  };
  require(audit.issueDate === date, "audit date must match the issue");
  require(Number.isFinite(
    Date.parse(audit.informationCutoff),
  ), "missing information cutoff");
  const coverage = audit.coverage ?? [];
  for (const provider of requiredProviders) {
    const records = coverage.filter((item) => item.provider === provider);
    require(records.length === 1, `one coverage record required: ${provider}`);
    const item = records[0];
    if (!item) continue;
    require(["read", "partial", "unavailable"].includes(
      item.status,
    ), `invalid coverage status: ${provider}`);
    require(/^https:\/\//.test(item.url ?? "") &&
      !!item.note?.trim(), `source and actual result required: ${provider}`);
    require(Number.isFinite(
      Date.parse(item.checkedAt),
    ), `missing check time: ${provider}`);
  }
  const candidates = audit.candidates ?? [];
  require(new Set(candidates.map((item) => item.id)).size ===
    candidates.length, "duplicate event id in candidates");
  const selected = candidates
    .filter((item) => item.selected)
    .sort((a, b) => a.order - b.order);
  require(selected.length ===
    15, `expected 15 selected events, got ${selected.length}`);
  for (const item of candidates) {
    require(!!item.reason?.trim(), `missing selection/exclusion reason: ${item.id}`);
    require(item.priority !== "must" ||
      item.selected, `important candidate omitted: ${item.id}`);
  }
  const sections = [
    ...news.matchAll(/^## (\d{2}) · (.+)\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm),
  ];
  require(sections.length ===
    15, `expected 15 news sections, got ${sections.length}`);
  const titles = sections.map((section) => section[2]);
  require(new Set(titles).size === titles.length, "duplicate news headline");
  for (const [index, item] of selected.entries()) {
    const section = sections[index];
    require(item.order === index + 1, `invalid selection order: ${item.id}`);
    require(section &&
      Number(section[1]) === index + 1 &&
      section[2] === item.title, `headline/order mismatch: ${item.id}`);
    require(/^https:\/\//.test(item.sourceUrl ?? "") &&
      section?.[3].includes(
        `(${item.sourceUrl})`,
      ), `missing matching source in news: ${item.id}`);
    require(/^\d{4}-\d{2}-\d{2}$/.test(item.eventDate ?? "") &&
      section?.[3].includes(
        item.eventDate,
      ), `missing event date in news: ${item.id}`);
    const age = (Date.parse(date) - Date.parse(item.eventDate)) / 86400000;
    require(Number.isFinite(age) &&
      age >= 0 &&
      age <= 7, `event outside seven-day window: ${item.id}`);
    require(age <= 1 ||
      section?.[3].includes(
        "近期补充",
      ), `older event missing label: ${item.id}`);
    if (item.kind === "project") {
      require(item.heat?.period === "daily" &&
        item.heat.starsAdded > 0 &&
        /^https:\/\//.test(item.heat.url ?? "") &&
        Number.isFinite(
          Date.parse(item.heat.observedAt),
        ), `missing recent project heat evidence: ${item.id}`);
    }
  }
  return errors;
}

async function findIssues(dir) {
  const issues = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) issues.push(...(await findIssues(fullPath)));
    else if (entry.name === "01-AI动态.md") issues.push(fullPath);
  }
  return issues;
}

async function main() {
  let count = 0;
  for (const file of await findIssues("content/frontiers")) {
    const date = path.basename(path.dirname(file));
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || date < "2026-09-09") continue;
    const audit = JSON.parse(
      await readFile(`docs/frontiers-source-audits/${date}.json`, "utf8"),
    );
    const errors = validateIssue(audit, await readFile(file, "utf8"), date);
    if (errors.length) throw new Error(`${date}:\n${errors.join("\n")}`);
    count++;
  }
  console.log(
    `前沿检查通过：${count} 期；每期 15 条、来源日期、厂商记录、重要候选与热点证据一致。`,
  );
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
