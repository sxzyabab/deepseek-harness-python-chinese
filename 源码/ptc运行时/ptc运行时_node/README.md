---
description: "在全新 Node 进程中运行 TypeScript 程序，使用会话文件系统沙箱、受管清理以及可配置的执行与输出限制。"
kind: "package-reference"
---

# @deepseek-ai/dsh-ptc-runtime-node

[English](README.md) | 中文

## 概述

在与 Bash 相同的平台沙箱策略下执行模型编写的 TypeScript，并通过异步绑定调用 Host 提供的函数。每次调用启动一个全新的 Node 进程，返回捕获日志、精确 JSON 值或结构化失败。直接 Node API 在所选限制内仍可使用。经过时间截止、输出上限和 V8 堆限制约束执行；取消和完成都会终止受管进程范围。请求受限模式但沙箱后端不可用时，执行失败。

## 目录

- [使用本包](#use-this-package)
- [理解实现](#understand-the-implementation)
- [进一步探索](#further-exploration)
- [模型体验](#model-experience)
- [已知限制与延后工作](#known-limitations-and-deferred-work)
- [开发备注](#dev-note)

-----

<a id="use-this-package"></a>
## 使用本包

在提供 `fs`、`subprocess`、`sandbox` 与 `sandboxPolicy` 的组合中挂载本提供方。`dsh-tools` 的 PTC 模式传入调用 Session 的目录和常设策略；直接运行时消费方在执行前解析这些选项。

### 配置

在所需服务可用后，配置提供方条目：

```yaml
- name: '@deepseek-ai/dsh-ptc-runtime-node'
  config:
    timeoutMs: 120000
    maxTimeoutMs: 600000
    maxOutputBytes: 67108864
    maxOldGenerationSizeMb: 512
    maxMessageBytes: 134217728
    maxPendingCalls: 128
    graceMs: 3000
```

| 字段 | 默认值 | 含义 |
|---|---|---|
| `timeoutMs` | `120,000` | 默认经过时间截止，包括嵌套工具与审批等待 |
| `maxTimeoutMs` | `600,000` | 解析器应用的经过时间截止上限 |
| `maxOutputBytes` | `67,108,864` | 序列化日志与完成值或诊断的合计预算 |
| `maxOldGenerationSizeMb` | `512` | V8 老生代堆上限，单位 MiB |
| `maxMessageBytes` | `134,217,728` | 控制帧、未完成参数字节和排队控制写入的上限 |
| `maxPendingCalls` | `128` | 同时进行的 Host 绑定调用数量上限 |
| `graceMs` | `3,000` | 受管终止与输出排空宽限时间 |
| `nodeExecutable` | 当前 Node 可执行文件 | 在子进程执行世界中解析的可执行文件 |
| `bootstrapPath` | 包内 bootstrap | 该执行世界中预先安装的构建后 bootstrap 的可选绝对路径 |

`resolve(request)` 补全 cwd、数值或 null 截止选择与执行策略；`run(spec)` 接受这些已解析输入，不补缺省值。

### 执行与结果

程序是异步函数体：支持顶层 `await` 与 `return`，且只接受可擦除 TypeScript。成功调用以 `result.value` 返回无损 JSON 值，以 `result.logs` 返回捕获文本。`result.sandbox` 独立于程序结果报告所选模式、观察到的拒绝，以及后端完整或部分的强制能力。

直接文件系统、网络与子进程操作仍是 Node 操作，受所选 OS 沙箱约束。嵌套 Host 绑定通过控制通道调用；PTC 工具调用保留注册表的可见性、排序、日志和审批规则。运行程序不会改变 Session 的常设策略，也不会在拒绝后自动重放程序。

### 截止时间与取消

省略 `timeoutMs` 使用配置的经过时间默认值；数值请求经过验证并封顶。服务调用方可以显式传入 `timeoutMs: null` 来省略经过时间定时器。启用的截止覆盖运行时准备和执行，包括等待嵌套工具或审批的时间。超时或取消通过 Host 的受管进程所有者停止同步循环；成功完成也会清理该受管范围。

### 失败

程序解析错误与抛出异常为 `exception`；截止到期为 `timeout`；取消为 `abort`；畸形或超量控制通信为 `protocol`；约束不可用为 `sandbox-unavailable`；进程提前退出或受管清理失败为 `worker-exit`。有损完成值为 `invalid-output`，外层结果超限为 `output-limit`。

-----

<a id="understand-the-implementation"></a>
## 理解实现

Host 负责策略、截止时间、绑定查找和进程清理。子进程负责程序求值与绑定代理；即使使用预期的控制描述符，模型编写的代码仍是不可信对端。

### 启动与控制

Host 在配置的执行世界中解析可执行文件与 bootstrap，通过 `ctx.sandbox` 等待 argv 限制准备完成，再通过 `ctx.subprocess` 启动。带长度分帧的 JSON 与 stdout/stderr 分开传输。

### 源码索引

| 文件 | 职责 |
|---|---|
| `__init__.py` | 配置、解析、策略、绑定与受管执行 |
| `启动.py` | 可执行文件／bootstrap 参数与执行世界资源映射 |
| `进程.py` | 子进程握手、环境清空与程序生命周期 |
| `引导.py` | 程序求值、绑定代理与输出捕获 |
| `通道.py` | 分帧、有界写入与协议失败 |
| `输出账本.py` | Host 外层结果计量 |

-----

<a id="further-exploration"></a>
## 进一步探索

- PTC 运行时服务——请求、已解析 spec 与结果。
- 子进程提供方——受管进程范围与平台限制。

-----

<a id="model-experience"></a>
## 模型体验

通过 `dsh-tools` 的 PTC 模式与 `dsh-workflow-ptc` 间接提供。中间绑定通信不进入模型历史。

## 已知限制与延后工作

<a id="known-limitations-and-deferred-work"></a>

- 约束继承所选后端的限制
- 堆上限不是进程树内存限制
- 清理继承子进程的可观测范围
- 执行是一次性的
- 输出上限拒绝超量内容，而不保留每个字节
- 绑定在传输接纳时受限
- console shim 有五个方法：`log`、`info`、`warn`、`error` 与 `debug`

<a id="dev-note"></a>
### 开发备注

timeout 讨论记录 yield、总生命周期、审批等待计时和进程树 CPU/RSS 上限的开放选择。
