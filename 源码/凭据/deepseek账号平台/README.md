---
description: "通过系统浏览器登录，并将账号凭证保存在现有本地凭证存储中。本地取消会阻止迟到的回调和兑换响应使用户登录。"
kind: "package-reference"
---

# @deepseek-ai/dsh-deepseek-account-platform

## 概述

通过系统浏览器登录，并将账号凭证保存在现有本地凭证存储中。本地取消会阻止迟到的回调和兑换响应使用户登录。

新申请将调用方的界面语言映射为平台的 en_US 或 zh_CN；进行中的申请保留发起时的语言。

getPlatformSession 仅在已存授权的 issuer 与 platformOrigin 一致时导出该授权。desktopPlatform 默认为 null，此时请求携带 x-client-platform: web；Desktop 提供 darwin 或 win32 时改为 desktop-mac 或 desktop-win。

## 使用此包

getProfile / getBalance 将保存的授权 token 通过 x-dsh-auth-token 请求头，向 platformOrigin 上的用户资料与摘要接口发起请求。在插件行配置 platformOrigin、allowLoopbackHttp、requestTimeoutMs 和 attemptTimeoutMs。HTTP 仅用于显式启用的本机开发。

提供者先在现有宿主 webServer 注册 /oauth/callback，再调用 auth_init；校验 state、使用 S256 PKCE 授权码兑换一次。浏览器地址默认要求匹配配置的平台来源，并始终要求固定的 /dsh/authorize 或 /dsh/authorized 路径。

不发布运行时 invariant：账号是否存在直接读取凭证存储。

## 模型体验

无。账号凭证只影响 HTTP 认证。

## 已知限制

浏览器登录需要宿主 webServer，仅支持带显式端口的本机 HTTP。账号 token 没有过期或刷新流程。远程退登失败不会恢复本地登录态。开发授权不能认证生产请求。
