# 资料夹

一个部署在 GitHub Pages 上的个人阅读资料库。PDF、Markdown、EPUB 和阅读器资源均由本站提供，无外部 CDN、字体或在线预览服务。

## 已实现

- 桌面与手机书架，论文 / 书籍 / 笔记分类、文件类型筛选与排序。
- 标题、作者、标签、简介及 Markdown 正文搜索。PDF / EPUB 暂不做全文检索。
- PDF 连续阅读、翻页、页码跳转、缩放、文本选择和页码恢复。
- Markdown 排版、代码高亮、章节目录、本地图片及阅读位置恢复。
- EPUB 在线阅读、章节目录、翻页、字号调整、内嵌配图与 CFI 阅读位置恢复。
- 原文件下载、收藏、最近阅读、已读标记、深浅外观。
- 当前浏览器 localStorage 保存记录；不登录、不跨设备同步。
- 构建时自动生成目录、复制附件、检查发布容量。

附带 3 篇原创中文示例笔记、2 份原创英文 PDF 演示稿及 1 本原创中文 EPUB 体验书。它们不是正式出版书籍或研究论文，可直接删除或替换。没有伪造阅读记录。

## 本地运行

需要 Node.js 22.13 或以上。

```bash
npm ci
npm run dev
```

访问终端提供的 `/github-learning-site/` 地址。修改 `content/` 后重启开发服务器以更新目录。

```bash
npm run build
npm run preview
```

## 添加 Markdown

将文章放进 `content/notes/` 等目录，文件顶部填写元数据：

```yaml
---
id: attention-notes
title: 注意力机制阅读笔记
category: 笔记
author: 资料夹
date: "2026-09-08"
description: 用自己的话整理注意力机制。
tags: [人工智能, 阅读笔记]
---
```

下方正常书写 Markdown。`category` 可取「论文」「书籍」「笔记」。`date` 要用引号包围。`id` 使用唯一的英文小写、数字和连字符，修改标题或移动文件时保持 id 不变。

图片可以和文章一起放在目录里，用 `./images/figure.png` 等相对路径引用。外部图片不会自动加载，请先保存到本站。下载 Markdown 得到去掉元数据的原始正文；单独下载不会包含配图。Markdown 正文搜索索引每份最多保留 180,000 字符。

## 添加 PDF

例如放入 `content/books/my-book.pdf`，并添加同名 `content/books/my-book.json`：

```json
{
  "id": "my-book",
  "title": "我的公开书籍",
  "category": "书籍",
  "author": "作者姓名",
  "date": "2026-09-08",
  "description": "书籍简介",
  "tags": ["主题"]
}
```

无须填写文件大小、下载链接或总页数：构建器和阅读器会自动处理。正式资料不要设置 `sample: true`。

## 添加 EPUB

将未加 DRM 的 `.epub` 文件放入 `content/books/`，并按上面的 PDF 示例添加同名 `.json` 文件。生成器自动识别格式、统计大小，并加入 EPUB 筛选与下载入口。

阅读器支持普通 EPUB 2 / EPUB 3 电子书，优先适配可重排的文字书籍。书内字体、样式与图片从 EPUB 包中读取，脚本不执行，不依赖外部服务。DRM 加密书籍不支持，特殊固定版式或交互型电子书需要逐本验证。

进度保存为 EPUB CFI 内容位置，换字号后会重新排版；工具栏页码是当前章节的分页，可能随窗口和字号变化。书架进度比例按章节估算。下载保留原始 EPUB 文件。

## 发布到 GitHub Pages

工作流位于 `.github/workflows/deploy.yml`。在仓库 **Settings → Pages → Build and deployment** 中选择 **GitHub Actions**。推送 `main` 后会自动构建发布。

站点地址：[资料夹](https://wuwudeqi.github.io/github-learning-site/)。仓库已由所有者授权设为公开，使用免费的 GitHub Pages 与 GitHub Actions 发布。网站代码及资料均公开可访问。

若更换仓库名或使用根域名，修改 `vite.config.js` 的 `base`。

## 容量与网络

- 构建器统计最终 `dist/` 总大小，达到 800 MB 提醒，达到 1 GB 阻止发布。
- PDF 超过 100 MiB 会阻止生成，避免普通 Git 仓库拒绝推送。
- 文档在打开时加载，PDF 阅读器代码也按需加载。中文 PDF 所需 CMaps、标准字体和 WASM 都一起发布。
- 内容安全策略仅允许加载本站资源，外部链接仍可由读者主动打开。
- 未来可为附件增加 Releases 地址，但跨域 PDF 阅读需另行验证，当前版本不包含 Releases 存储适配。

## 阅读记录

键名为 `sen-space:reading:v1`，按文档稳定 id 保存收藏、阅读位置、完成状态和最后访问时间；外观偏好同样本地保存。关闭浏览器通常保留，清除网站数据或无痕会话可能丢失。同源浏览器标签页可共享记录；不同浏览器、不同电脑不会同步。

## 目录

```text
content/                文档和配图，人工维护
src/main.js             书架、搜索、收藏、路由及本地记录
src/reader.js           Markdown / PDF 阅读器
src/epub-reader.js      EPUB 阅读器
src/style.css           站点及阅读器外观
scripts/catalog.mjs     元数据检查、目录生成与资源复制
scripts/check-size.mjs   发布容量检查
public/                 favicon 和构建前自动生成资源
```

`public/catalog.json`、`public/documents/`、`public/pdf-assets/` 与 `dist/` 都是生成产物，不应手动修改或提交。用 `npm run build` 重新生成。
