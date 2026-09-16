---
description: "通过共享的沙箱化 PTC Node 进程运行时执行工作流编排，保留工作流钩子、subagent 路由和调用方拥有的取消能力。"
kind: "package-reference"
---

# @deepseek-ai/dsh-workflow-ptc

[English](README.md) | 中文

## 概述

在全新 Node 进程中按调用 Session 的文件沙箱策略运行 JavaScript 工作流。脚本保留 `agent()`、`parallel()`、`pipeline()`、`phase()` 和 `log()` 钩子，委派的工作由 subagent 完成。同一个执行提供方服务 PTC 与工作流，包括需显式启用的 Ralph 循环。运行没有整体经过时间截止；取消会停止受管进程并释放子 agent。

## 目录

- [使用本包](#use-this-package)
- [理解实现](#understand-the-implementation)
- [进一步探索](#further-exploration)
- [模型体验](#model-experience)
- [已知限制与延期工作](#known-limitations-and-deferred-work)

-----

<a id="use-this-package"></a>
## 使用本包

在提供 subagent、沙箱策略和 Node PTC 运行时的组合中挂载本引擎。引擎在加载时拒绝非 TypeScript 的 PTC 提供方。

### 最小配置

```yaml
- name: '@deepseek-ai/dsh-workflow-ptc'
- name: '@deepseek-ai/dsh-tool-workflow'
```

| 字段 | 默认值 | 含义 |
|---|---|---|
| `provider` | `spawn` | `agent()` 调用使用的宿主侧 subagent 提供方。 |
| `maxConcurrentAgents` | `0` | 并发 `agent()` 上限；`0` 根据可用 CPU 并行度解析。 |
| `maxTotalAgents` | `1000` | 一次运行最多启动的 `agent()` 调用数。 |
| `maxItemsPerCall` | `4096` | 一次 `parallel()` 或 `pipeline()` 调用接受的条目数。 |
| `syncTimeoutMs` | `5000` | 脚本最初同步片段的 VM 超时时间，单位为毫秒。 |

### 结果与失败

脚本支持顶层 `await`；`meta` 和 `args` 作为 JSON 数据传入。无效元数据或无法解析的正文在运行发布前被拒绝。

### 文件政策与取消

引擎为 PTC 执行解析调用 Session 的常设文件政策与 cwd。工作流向 PTC 请求 `timeoutMs: null`。取消立即中止 PTC 进程及待启动或活跃的 subagent。

-----

<a id="understand-the-implementation"></a>
## 理解实现

工作流引擎负责编排；PTC 提供方负责进程启动、OS 约束、分帧传输与受管进程清理。

### 源码地图

| 文件 | 职责 |
|---|---|
| `__init__.py` | 引擎配置、请求校验与运行创建 |
| `宿主.py` | PTC 执行、子 agent 归属、结算与资源释放 |
| `宾客.py` | 基于 PTC Host 绑定的 guest 适配器 |
| `宾客源码.py` | 自包含 guest 程序源码 |
| `运行时.py` | VM 求值、辅助函数约定与组合器 |
| `领域.py` | 跨 VM realm 的无损 JSON 物化 |
| `元数据.py` | 元数据校验与规范化 |

-----

<a id="further-exploration"></a>
## 进一步探索

- 工作流服务——调用方拥有的运行与清理。
- Node PTC 运行时——文件策略、进程限制与部署选择。

-----

<a id="model-experience"></a>
## 模型体验

脚本每次调用 `agent()`，都会把提示词原样发送给 subagent 提供方。普通子 agent 失败使 `agent()` 以 `null` 兑现。

## 已知限制与延期工作

<a id="known-limitations-and-deferred-work"></a>

- 文件约束与清理继承提供方限制
- 工作流上限是协作式的
- 没有整体经过时间截止
- 子 agent 清理遵循提供方约定
- VM 不是安全边界
- 跨 realm 错误在脚本内无法通过 `instanceof Error`
