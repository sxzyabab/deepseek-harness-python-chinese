---
description: "账号使用方可读取本地登录状态、发起或取消浏览器登录，并在保留 API Key 的情况下退出。"
kind: "package-reference"
---

# @deepseek-ai/dsh-deepseek-account

## 概述

账号使用方可读取本地登录状态、发起或取消浏览器登录，并在保留 API Key 的情况下退出。宿主模型使用方仅能为提供者配置的推理来源解析账号凭证。

getPlatformSession 为原生平台内嵌提供仅限宿主的 origin/token 快照，退登时返回 null。账号控制器 RPC 和客户端状态不包含此方法及快照。

desktopClientHeaders 将原生平台 darwin 和 win32 映射为 Desktop 账号与更新策略请求共用的请求头；null 不添加请求头。

## 使用此包

AccountProfile.avatarUrl 是可选的账号头像 URL。该服务定义账号操作和可重连的状态快照。平台提供者负责协议和授权记录。凭证仅限宿主；API 控制器只导出状态与操作，不导出 resolveToken。

服务只定义账号操作，不维护第二份凭证索引，因此不发布 invariant。

## 模型体验

无。账号凭证只影响 HTTP 认证，不进入模型提示、会话日志或工具结果。

## 已知限制

账号 token 没有过期或刷新流程。退出时先移除本地授权，再由提供者在后台撤销；远程退登失败不会恢复本地登录态。资料和余额查询失败保留已存储授权。
