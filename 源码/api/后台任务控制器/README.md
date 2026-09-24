---
description: "宿主与客户端的作业控制：把一个会话看得到的名册与一个作业的保留输出镜像到浏览器，不触碰模型的消耗型游标，并代人类停止作业。"
kind: "package-reference"
---

# @deepseek-ai/dsh-api-job-controller

## 概述

本包拥有宿主的 jobController 服务与客户端 remote.job 命名空间。两条 Remote 流都是 jobs 的投影：job.list 以整集帧镜像一个会话看得到的作业；job.follow 从绝对字节偏移发送保留输出；job.kill 代人类停止作业。两条流都不触碰模型的消耗型游标与完成通知。

## 使用此包

job.list({ sessionId }) 产出该会话可见的集合。job.follow({ sessionId?, jobId, from? }) 先产出 opened 锚帧，再是聚合的 output 帧，结算后产出终态 status。job.kill({ sessionId, jobId }) 以 cancelled by the user 为原因取消可见作业，回答 requested 或 already-finished，看不到的 id 以 job/not-found 拒绝。

配置 observeFlushMs 默认 100 毫秒，observeMaxFrameBytes 默认 65536 字节。

客户端入口安装 jobs 服务：kill、watchRows、observe。

## 模型体验

无。作业观测是浏览器与宿主的控制状态，不注册提示词、工具或会话事件。

## 已知限制

环是尽力而为的实时预览。两条流都是进程本地的，宿主重启丢失环与名册。按会话的访问限制由注册表每次读取时的调用方参数强制。
