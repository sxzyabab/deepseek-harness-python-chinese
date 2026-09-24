---
description: "配置显式产品使用事件、OTLP/HTTP 路由、批量发送与退出等待上限。"
kind: "package-reference"
---

# @deepseek-ai/dsh-host-product-telemetry-otel

## 概述

将选定的产品使用事件发送到 OTLP/HTTP 接收服务。事件包含名称、字符串摘要、发生时间，以及标量或单层对象属性。挂载插件不会自动采集信息；应用需要显式提交每个事件。发送采用尽力而为方式，不代表数据已入仓。

## 使用本包

在组合中挂载插件并提供应用标识；需要时可覆盖接收地址。内置配置档不挂载本插件。

字段：endpoint 默认生产 collector 地址；serviceName 与 serviceVersion 必填；channel 默认 dsh_otel_report；compression 为 gzip 或 none；maxExportBatchSize 默认 512；maxQueueSize 默认 2048；scheduledDelayMillis 默认 30000；timeoutMillis 默认 15000；exportTimeoutMillis 默认 20000；shutdownTimeoutMillis 默认 21000。

消费方注入 productTelemetry，调用提交接口送出明确选定的分析字段。插件不读取会话、账号、凭证或设备标识。

Python 侧用 HTTP JSON 导出，不安装全局 OpenTelemetry 提供方，不发布运行时不变量。

## 模型体验

无。插件仅发送显式分析记录，不提供模型上下文。

## 已知限制

队列仅存在于内存；队列溢出、网络故障和进程退出可能丢失事件。没有持久发件箱或入仓确认。
