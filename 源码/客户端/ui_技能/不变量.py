"""`@deepseek-ai/dsh-client-ui-skill` 的本包拥有不变量配套。

对齐上游 `ui-skill/src/invariant.ts`。公开面仅中文名。

无运行时不变量：斜杠源、语言字典与带键 toolview 都是注册表拥有的注册，
其拆除由 HMR 安全规格证明。它们不发射 cordis 事件，也不拥有跨插件可变状态。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-client-ui-skill'#本包的不变量所有权名
名称='client-ui-skill-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象=None,失败=None):#空安装器
    """无运行时检查：拆除由 HMR 安全规格证明。"""
    return#不挂监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
