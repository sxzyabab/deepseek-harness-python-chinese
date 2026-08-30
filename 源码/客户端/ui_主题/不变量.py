"""`@deepseek-ai/dsh-client-ui-theme` 的本包拥有不变量配套。

对齐上游 `ui-theme/src/invariant.ts`。公开面仅中文名。

无运行时不变量：设置作用域校验并发布持久主题段，
注册表随自身变更同步发出 `theme/change`。
Store 与注册表是否一致，由本包的 Host、作用域与服务行为规格直接覆盖。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-client-ui-theme'#本包的不变量所有权名
名称='client-ui-theme-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象=None,失败=None):#空安装器
    """无运行时检查：Host、作用域与服务行为规格直接覆盖一致性。"""
    return#不挂监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
