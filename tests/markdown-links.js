async (page) => {
  const assert = (ok, message) => {
    if (!ok) throw new Error(message);
  };
  const base = page.url().split("#")[0];
  await page.goto(base + "#/read/transformer-00-roadmap");
  const next = page
    .locator(".markdown-content")
    .getByRole("link", { name: "01 参数、预测与训练", exact: true });
  await next.waitFor();
  assert(
    (await next.getAttribute("href")) === "#/read/transformer-01-foundations",
    "Internal reader link",
  );
  assert(
    (await next.getAttribute("target")) !== "_blank",
    "Same-tab navigation",
  );
  const external = page.locator(
    '.markdown-content a[href="https://huggingface.co/docs/transformers/main/en/chat_templating"]',
  );
  assert(
    (await external.getAttribute("target")) === "_blank",
    "External link preserved",
  );
  await next.click();
  await page
    .locator(".markdown-content h1")
    .filter({ hasText: "参数、预测与训练" })
    .waitFor();
  await page.waitForFunction(() =>
    [...document.querySelectorAll(".markdown-content img")].every(
      (i) => i.complete && i.naturalWidth > 0,
    ),
  );
  assert(
    (
      await page
        .locator(".markdown-content a")
        .filter({ hasText: "01_linear_learning.py" })
        .getAttribute("href")
    ).endsWith("/code/01_linear_learning.py"),
    "Code remains an asset link",
  );
  await page.goBack();
  await next.waitFor();
  assert(
    await page.locator(".markdown-scroll").evaluate((el) => el.scrollTop > 0),
    "Roadmap reading position restored",
  );
  await next.click();
  const back = page
    .locator(".markdown-content")
    .getByRole("link", { name: "返回总览", exact: true });
  await back.waitFor();
  await back.click();
  await next.waitFor();
  await page.goto(
    base +
      "#/read/transformer-01-foundations?section=" +
      encodeURIComponent("本章完成标准"),
  );
  const heading = page
    .locator(".markdown-content h2")
    .filter({ hasText: "本章完成标准" });
  await heading.waitFor();
  await page.waitForFunction(() => {
    const h = [...document.querySelectorAll(".markdown-content h2")].find(
      (h) => h.textContent === "本章完成标准",
    );
    const s = document.querySelector(".markdown-scroll");
    return (
      h &&
      s &&
      h.getBoundingClientRect().top >= s.getBoundingClientRect().top - 5 &&
      h.getBoundingClientRect().top < s.getBoundingClientRect().bottom
    );
  });
  await page.locator(".reader-back").click();
  await page.locator(".reader").waitFor({ state: "detached" });
  assert(
    page.url().includes("/notes/transformer"),
    "Return to folder after document chain",
  );
  return "PASS: 00 → 01 → 00, same tab, browser back/progress, external/code links, heading deep link, return folder";
}
