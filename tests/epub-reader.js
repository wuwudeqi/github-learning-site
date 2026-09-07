async (page) => {
  const home = page.url().split("#")[0];
  const assert = (ok, message) => {
    if (!ok) throw new Error(message);
  };
  await page.goto(home);
  await page.setViewportSize({ width: 1440, height: 1000 });
  if (
    await page
      .getByRole("button", { name: "切换浅色外观", exact: true })
      .count()
  )
    await page
      .getByRole("button", { name: "切换浅色外观", exact: true })
      .click();
  await page.getByRole("button", { name: "EPUB", exact: true }).click();
  assert(
    (await page.locator(".document-table tbody tr").count()) > 0,
    "EPUB filter",
  );
  await page.locator('a[href="#/read/epub-demo"]').last().click();
  await page.waitForFunction(() =>
    document.querySelector("#epub-position")?.textContent.includes("本章"),
  );
  await page
    .getByRole("combobox", { name: "EPUB 字号", exact: true })
    .selectOption("18");
  await page
    .getByRole("combobox", { name: "跳转章节", exact: true })
    .selectOption("0");
  await page.waitForFunction(() =>
    document.querySelector("#epub-position")?.textContent.includes("本章 1 /"),
  );
  const frame = page.frameLocator("#epub-viewer iframe").first();
  await frame
    .getByRole("heading", { name: "1. 为阅读留一点空间", exact: true })
    .waitFor();
  assert(
    await frame
      .locator("img")
      .evaluate((img) => img.complete && img.naturalWidth > 0),
    "Embedded image",
  );
  assert(
    !(
      await page.locator("#epub-viewer iframe").first().getAttribute("sandbox")
    ).includes("allow-scripts"),
    "Book scripts must stay disabled",
  );
  const before = await page.evaluate(
    () =>
      JSON.parse(localStorage.getItem("sen-space:reading:v1")).documents[
        "epub-demo"
      ].epubCfi,
  );
  await page.getByRole("button", { name: "下一页", exact: true }).click();
  await page.waitForFunction(
    (cfi) =>
      JSON.parse(localStorage.getItem("sen-space:reading:v1")).documents[
        "epub-demo"
      ].epubCfi !== cfi,
    before,
  );
  await page
    .getByRole("combobox", { name: "EPUB 字号", exact: true })
    .selectOption("24");
  await page.waitForFunction(
    () =>
      JSON.parse(localStorage.getItem("sen-space:reading:v1")).documents[
        "epub-demo"
      ].epubFontSize === 24,
  );
  await page
    .getByRole("combobox", { name: "跳转章节", exact: true })
    .selectOption("1");
  await page.waitForFunction(() =>
    document
      .querySelector("#epub-position")
      ?.textContent.includes("让笔记成为自己的语言"),
  );
  await page.getByRole("button", { name: "下一页", exact: true }).click();
  await page.waitForFunction(() =>
    document.querySelector("#epub-position")?.textContent.includes("本章 2 /"),
  );
  const saved = await page.evaluate(
    () =>
      JSON.parse(localStorage.getItem("sen-space:reading:v1")).documents[
        "epub-demo"
      ].epubCfi,
  );
  await page.reload();
  await page.waitForFunction(() =>
    document
      .querySelector("#epub-position")
      ?.textContent.includes("让笔记成为自己的语言"),
  );
  assert(
    (await page
      .getByRole("combobox", { name: "EPUB 字号", exact: true })
      .inputValue()) === "24",
    "Font restore",
  );
  assert(
    (await page.evaluate(
      () =>
        JSON.parse(localStorage.getItem("sen-space:reading:v1")).documents[
          "epub-demo"
        ].epubCfi,
    )) === saved,
    "CFI position restore",
  );
  const pending = page.waitForEvent("download");
  await page.getByRole("link", { name: "下载原文", exact: true }).click();
  assert(
    (await pending).suggestedFilename().endsWith(".epub"),
    "EPUB original download",
  );
  await page.getByRole("button", { name: "章节目录", exact: true }).click();
  await page
    .getByRole("button", { name: "带着问题再次阅读", exact: true })
    .click();
  await page.waitForFunction(() =>
    document
      .querySelector("#epub-position")
      ?.textContent.includes("带着问题再次阅读"),
  );
  await page.getByRole("link", { name: "返回书架", exact: true }).click();
  assert(
    (await page
      .locator(".topbar")
      .evaluate((el) => el.getBoundingClientRect().top)) < 100,
    "Return layout",
  );
  await page.getByRole("button", { name: "切换深色外观", exact: true }).click();
  await page.locator('a[href="#/read/epub-demo"]').first().click();
  await page.waitForFunction(() =>
    document.querySelector("#epub-position")?.textContent.includes("本章"),
  );
  assert(
    (await page
      .frameLocator("#epub-viewer iframe")
      .first()
      .locator("body")
      .evaluate((el) => getComputedStyle(el).color)) === "rgb(214, 225, 214)",
    "Dark EPUB theme",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "章节目录", exact: true }).click();
  await page
    .getByRole("button", { name: "为阅读留一点空间", exact: true })
    .click();
  await page.waitForFunction(() =>
    document
      .querySelector("#epub-position")
      ?.textContent.includes("为阅读留一点空间"),
  );
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    "Mobile overflow",
  );
  const external = await page.evaluate(() =>
    performance
      .getEntriesByType("resource")
      .filter(
        (r) =>
          r.name.startsWith("http") &&
          new URL(r.name).origin !== location.origin,
      )
      .map((r) => r.name),
  );
  assert(!external.length, "External dependencies: " + external.join(","));
  await page.getByRole("link", { name: "返回书架", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("button", { name: "切换浅色外观", exact: true }).click();
  return "PASS: EPUB filter, text, images, sandbox, pagination, chapter TOC, font, CFI restore, download, dark theme, mobile, return layout.";
};
