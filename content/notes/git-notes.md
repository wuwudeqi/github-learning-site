---
id: git-learning-notes
title: Git 与 GitHub：从提交到发布
category: 笔记
author: Codex · 示例整理
date: '2026-09-07'
description: 理解工作区、提交与远程仓库，整理一套日常使用流程。
tags: [开发工具, Git]
sample: true
---
# Git 与 GitHub：从提交到发布

> 本文为演示阅读界面的原创示例笔记。

## 三个位置

Git 的日常操作围绕工作区、暂存区和提交历史进行。工作区是你正在编辑的文件；暂存区是你准备提交的变化；提交历史是已经保存的版本。

GitHub 则提供远程仓库，用于托管和协作。Git 本身不要求联网，你可以先在本地完成编辑和提交。

## 查看当前状态

在操作前，先确认自己所在的仓库以及当前改动：

```bash
git status
git diff
```

`git status` 告诉你哪些文件发生了变化。`git diff` 展示尚未暂存的具体修改。

## 创建一次提交

只把本次工作需要的文件放进暂存区，然后写一条说明清楚的提交信息。

```bash
git add content/notes/example.md
git commit -m "docs: add reading notes"
```

提交信息应描述改动的结果。例如「补充阅读笔记中的代码示例」比「更新文件」更容易理解。

## 同步远程仓库

```bash
git pull --ff-only
git push
```

当分支出现分歧时，先理解双方的变化再决定如何合并。不要为了消除报错而覆盖远程历史。

## 发布前的检查

| 检查项 | 为什么需要 |
| --- | --- |
| 文档能打开 | 避免错误链接 |
| 图片是本地相对路径 | 避免外部图片无法访问 |
| 文档编号保持稳定 | 保留阅读记录 |
| 文件总量在预算内 | 保证部署成功 |

## 常用命令回顾

```bash
git log --oneline -5
git diff --staged
git remote -v
```

分别用于回顾最近提交、检查暂存变化、查看远程地址。先观察，再修改，是维护资料库时很实用的习惯。
