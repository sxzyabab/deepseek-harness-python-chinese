---
description: "通过声明式 preset 选择 Agent 的工具、提示词和技能。同一进程可以运行多种组合。配置失败会显示在列表中；现有 Agent 保留已经使用的组合。"
kind: "package-reference"
---

# @deepseek-ai/dsh-agent-preset-registry

## 概述

通过声明式 preset 选择 Agent 的工具、提示词和技能。同一进程可以运行多种组合。配置失败会显示在列表中；现有 Agent 保留已经使用的组合。

## 使用此包

最小配置：

- id: agent-preset-registry
  name: '@deepseek-ai/dsh-agent-preset-registry'
  config:
    default: standard
- id: preset-standard
  name: '@deepseek-ai/dsh-agent-preset'
  config:
    id: standard
    plugins: []

字段 default 必填，是未显式指定时使用的 preset ID。

Web 内置定义来自 dsh-web-app bundle。定义使用普通插件行；注册表不扫描目录，也不接受 preset 路径。agent-preset-registry 条目的 selectedDefault 与 modeSelectionEnabled 保留用户默认值和选择器可见性；隐藏选择器时使用部署 default。

注册表不写入任何声明。read Remote 把一条声明的子插件列表按 entry-list YAML 方言（含 !!js 条件）渲染回来，供客户端展示 preset 的组成；没有任何接口接受 YAML 写回。新建 preset 或覆盖内置 preset 都是 bundle 补丁：插入一行 @deepseek-ai/dsh-agent-preset，或按该行 id 写覆盖补丁。

## 理解实现

每个声明在启动时创建注册表拥有的作用域和内存加载器树。更新或移除声明会让旧世代退役；智能体、子智能体和临时历史读取各自持有引用，最后一个引用释放后才销毁插件树。插件注册继承 preset 作用域，智能体作用域的父链接决定可见性。

激活审计检查导入失败、缺失服务和向全局泄漏的服务。导入失败、激活失败和泄漏会拒绝挂载。等待宿主服务的行保持挂载，每次读取和绑定都在宿主加载器树结算后重新审计。失败只禁用该定义的新绑定。会话日志保存 preset ID 和空白会话的切换记录。

__init__.py 负责注册、世代与智能体绑定。挂载.py 负责隔离插件树与激活审计。不变量.py 检查挂载后泄漏到全局的服务，以及模型请求前尚未绑定 preset 的智能体。

## 模型体验

没有直接内容：所选 preset 的 plugins 拥有模型可见的工具和提示词片段。本包自身没有 token 影响。已有智能体保留插件和提示词。新智能体从当前定义构建前缀。

## 已知限制

preset 不是安全沙箱：YAML 及插件可以执行宿主代码。用户覆盖替换完整子插件列表，不自动合并内置列表的未来更新。进程退出后不保存旧世代的插件实现。
