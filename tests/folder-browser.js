async (page) => {
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  const home = page.url().split("#")[0];
  await page.goto(home);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator(".folder-link").first().waitFor();
  assert(
    (await page.locator(".folder-link").count()) === 4,
    "Root has four folders",
  );
  await page.locator('[data-view="笔记"]').click();
  await page.getByRole("link", { name: "transformer", exact: true }).waitFor();
  await page.getByRole("link", { name: "transformer", exact: true }).click();
  const folderURL = page.url();
  const titles = await page
    .locator(".document-table .document-title")
    .allTextContents();
  assert(
    titles.length === 2 && titles[0].includes("00") && titles[1].includes("01"),
    "Chapters naturally ordered",
  );
  assert(
    (await page.locator(".folder-link").count()) === 0,
    "Image and code folders hidden",
  );
  await page.reload();
  await page.locator(".document-table .document-title").first().waitFor();
  assert(
    page.url() === folderURL &&
      (await page.locator(".document-table tbody tr").count()) === 2,
    "Folder refresh",
  );
  await page
    .locator('.document-table a[href="#/read/transformer-01-foundations"]')
    .click();
  await page.locator(".markdown-content").waitFor();
  await page.waitForFunction(
    () =>
      [...document.querySelectorAll(".markdown-content img")].length === 2 &&
      [...document.querySelectorAll(".markdown-content img")].every(
        (i) => i.complete && i.naturalWidth > 0,
      ),
  );
  if (
    !(await page.locator(".complete-button").getAttribute("class")).includes(
      "is-complete",
    )
  )
    await page.locator(".complete-button").click();
  await page.locator(".reader-back").click();
  await page.locator(".reader").waitFor({ state: "detached" });
  await page.locator(".folder-breadcrumbs").waitFor();
  assert(page.url() === folderURL, "Return to exact folder");
  assert(
    (await page.locator(".completed-check").count()) === 1,
    "Reading state retained",
  );
  if (
    (await page
      .locator('[data-favorite="transformer-01-foundations"]')
      .getAttribute("aria-pressed")) !== "true"
  )
    await page.locator('[data-favorite="transformer-01-foundations"]').click();
  await page.locator('[data-view="favorites"]').click();
  await page.locator(".document-path").first().waitFor();
  assert(
    (await page.locator(".document-table .document-title").count()) >= 1,
    "Favorites direct documents",
  );
  await page.locator('[data-view="笔记"]').click();
  await page.getByRole("link", { name: "transformer", exact: true }).waitFor();
  await page.getByRole("searchbox", { name: "搜索资料" }).fill("梯度");
  await page.locator(".document-path").first().waitFor();
  assert(
    (await page.locator(".document-path").first().textContent()).includes(
      "transformer",
    ),
    "Search shows nested path",
  );
  await page.locator(".document-path").first().click();
  await page.waitForURL("**/#/browse/all/notes/transformer");
  await page.waitForFunction(
    () =>
      document.querySelector("#search")?.value === "" &&
      document.querySelectorAll(".document-table .document-title").length === 2,
  );
  await page.getByRole("searchbox", { name: "搜索资料" }).waitFor();
  assert(
    (await page.getByRole("searchbox", { name: "搜索资料" }).inputValue()) ===
      "",
    "Search path opens folder",
  );
  assert(
    (await page.locator(".document-table .document-title").count()) === 2,
    "Search directory contains chapters",
  );
  await page.getByRole("button", { name: "PDF", exact: true }).click();
  await page.locator("#reset-filters").click();
  assert(
    (await page.locator(".document-table .document-title").count()) === 2,
    "Clear empty filter retains folder",
  );
  await page
    .locator(".folder-breadcrumbs")
    .getByRole("link", { name: "笔记", exact: true })
    .click();
  await page.getByRole("link", { name: "transformer", exact: true }).waitFor();
  await page.goBack();
  await page
    .locator('.document-table a[href="#/read/transformer-01-foundations"]')
    .waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "output/playwright/folders-mobile.png" });
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    "No mobile horizontal overflow",
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: "output/playwright/folders-desktop.png" });
  await page.goto(home + "#/read/transformer-01-foundations");
  await page.reload();
  await page.locator(".markdown-content").waitFor();
  await page.locator(".reader-back").click();
  await page.locator(".reader").waitFor({ state: "detached" });
  await page.locator(".document-table .document-title").first().waitFor();
  assert(
    page.url().includes("/notes/transformer"),
    "Direct document returns to parent folder",
  );
  return "PASS: hierarchy, order, hidden assets, refresh, images, reading state, favorites, search, filters, breadcrumbs, history, mobile, direct links";
}
