---
description: "账号页面使用经过认证的 Remote 操作和快照流。控制器提供登录状态，不返回 token 或 PKCE 私密数据。"
kind: "package-reference"
---

# @deepseek-ai/dsh-api-account-controller

## 概述

账号页面使用经过认证的 Remote 操作和快照流。控制器提供登录状态，不返回 token 或 PKCE 私密数据。

## 使用此包

account 命名空间提供 getState、getProfile、getBalance、startSignIn、cancelSignIn、signOut 和 watch。watch 先发送完整初始状态，随后发送完整状态变化；断开连接只停止观察，不取消登录。取消操作必须指定尝试 ID，防止旧页面取消新登录。

控制器向账号服务转发操作，不维护独立的账号状态，因此不发布 invariant。

## 模型体验

无。账号凭证只影响 HTTP 认证，不进入模型提示、会话日志或工具结果，不改变模型请求前缀。

## 已知限制

UI 断线后可通过 watch 恢复状态，但不能在宿主退出后恢复登录尝试。凭证和请求 token 解析不对 Remote 暴露。
