---
description: "Client 代码界面与 Host read 卡片共享的唯一「扩展名 → 语法高亮语言」表。"
kind: "package-library"
---

# dsh-util-code-language

[English](README.md) | 中文

## 概述

本仓库唯一的「文件扩展名 → 语法高亮语言」表，供 Client 的文档 Code 预览、diff 审阅与 Host read 工具持久化的 `lang` 提示共同使用。`按路径解析语言` 以大小写不敏感的方式把文件名或路径映射为规范化 grammar id；`代码高亮扩展名列表` 列出预览注册可以声明的全部后缀。`按路径解析读取语言提示` 在同一张表上把 read 卡片的短 id 投影出来：已录制的会话已经持有该后缀的值时保持该持久化值不变，其余后缀取该语言的短名。该包可在无浏览器环境使用，不提供 Cordis service，也不持有运行时状态；真正的分词仍由 Client 高亮器负责。

## 运行时不变式

不发布伴生入口。这个工具不持有可变运行时关系。
