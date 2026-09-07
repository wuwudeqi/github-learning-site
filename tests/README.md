# 阅读器返回书架回归检查

依赖 Playwright CLI。先运行 `npm run build` 和 `npm run preview -- --port 4173`。

```bash
playwright-cli --session reader-return open http://127.0.0.1:4173/github-learning-site/
playwright-cli --session reader-return run-code "$(cat tests/reader-return.js)"
```

也可将地址换成已部署站点。测试通过页面 UI 连续打开 PDF 并返回，检查列表位于可视区域内、侧栏固定定位、分类保留、页面可操作，再检查 Markdown 与手机布局。依赖保留 Attention Is All You Need 和 Git 示例笔记。

原始失败：PDF.js 的全局 `.sidebar` 样式把站点侧栏改成 `position: relative`，返回后顶部栏位于 y=764.5，论文列表位于 y=1122（1000px 高的窗口）。仅检查 DOM 行数和无报错不能捕获此问题。

## EPUB 阅读检查

```bash
playwright-cli --session epub-reader open http://127.0.0.1:4173/github-learning-site/
playwright-cli --session epub-reader run-code "$(cat tests/epub-reader.js)"
```

使用原创 EPUB 示例检查正文、配图、禁用书内脚本、翻页、章节目录、字号、刷新后准确续读、下载、深色模式、手机布局与返回书架。
