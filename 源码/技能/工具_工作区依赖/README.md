---
description: "load_workspace_dependencies 工具：返回随包附带的 Python、Node.js 与 pnpm 路径，载荷可原地使用或安装到 Harness 主目录。"
kind: "package-reference"
---

# @deepseek-ai/dsh-tool-workspace-dependencies

## 概述

自带脚本运行时的部署挂载本工具，让智能体询问随包的 Python、Node.js 与 pnpm 在哪里，而不是自行寻找系统解释器。工具返回路径与记录的发行版版本，不改 PATH，不改包管理器设置。

## 使用本包

与工具注册表一起挂载，给出载荷目录。配置校验在激活前要求非空 source 并拒绝空 root。

字段 source 必填，是含 runtime.json 与 dependencies/ 的载荷目录。字段 root 可选，设置时首次调用把载荷复制过去；未设置时校验后原地使用。

runtime.json 记录 desktopVersion、platform、arch、可选 payloadDigest、顶层 python 与可选的 node/pnpm 版本，以及完整的 pythonPackages 表。声明 pnpm 时必须同时声明 Node.js。

模型看到 load_workspace_dependencies 工具。结果是一个 JSON 对象：python 与 pythonPackages、pythonDistributions，以及载荷声明了才有的 node、nodePackages 与 pnpm。

## 已知限制

Linux 目标需要 glibc；尚未锁定 musl 载荷。Windows 上原地使用的载荷须在载体里已可执行。
