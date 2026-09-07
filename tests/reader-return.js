async (page) => {
  const home = page.url().split("#")[0];
  await page.goto(home);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('[data-view="论文"]').click();
  const expectedPapers = await page.locator(".document-table tbody tr").count();
  const expectedTotal = Number(
    await page.locator('[data-view="all"] small').textContent(),
  );
  for (let visit = 0; visit < 2; visit++) {
    await page
      .getByRole("link", {
        name: "Attention Is All You Need（Transformer 原始论文）",
        exact: true,
      })
      .click();
    await page.waitForFunction(
      () => document.querySelector("#pdf-total")?.textContent === "15",
    );
    await page.getByRole("link", { name: "返回书架", exact: true }).click();
    await page.locator(".reader").waitFor({ state: "detached" });
    const layout = await page.evaluate(() => ({
      rows: document.querySelectorAll(".document-table tbody tr").length,
      topbarTop: document.querySelector(".topbar").getBoundingClientRect().top,
      listTop: document.querySelector(".document-table").getBoundingClientRect()
        .top,
      sidebarPosition: getComputedStyle(
        document.querySelector('[aria-label="主导航"]'),
      ).position,
      inert: document.querySelector(".workspace").inert,
      readerOpen: !!document.querySelector(".reader"),
      viewportHeight: innerHeight,
    }));
    if (
      layout.rows !== expectedPapers ||
      layout.sidebarPosition !== "fixed" ||
      layout.topbarTop > 100 ||
      layout.listTop >= layout.viewportHeight ||
      layout.inert ||
      layout.readerOpen
    )
      throw new Error(
        "RETURN_BOOKSHELF_LAYOUT_BROKEN " + JSON.stringify(layout),
      );
  }
  await page.locator('[data-view="all"]').click();
  await page.locator('a[href="#/read/git-learning-notes"]').last().click();
  await page.locator(".markdown-content").waitFor();
  await page.getByRole("link", { name: "返回书架", exact: true }).click();
  await page.locator(".reader").waitFor({ state: "detached" });
  if (
    (await page.locator(".document-table tbody tr").count()) !== expectedTotal
  )
    throw new Error("Book list missing after PDF-to-Markdown navigation");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "打开导航", exact: true }).click();
  await page.locator('[data-view="论文"]').click();
  const mobile = await page.evaluate(() => ({
    top: document.querySelector(".topbar").getBoundingClientRect().top,
    listTop: document.querySelector(".document-table").getBoundingClientRect()
      .top,
    width: document.documentElement.scrollWidth,
    viewport: innerWidth,
    height: innerHeight,
  }));
  if (
    mobile.top > 100 ||
    mobile.listTop >= mobile.height ||
    mobile.width > mobile.viewport
  )
    throw new Error("MOBILE_LAYOUT_BROKEN " + JSON.stringify(mobile));
  await page.setViewportSize({ width: 1440, height: 1000 });
  return "PASS: PDF return twice, preserved category, Markdown return, mobile layout.";
}
