"""`@deepseek-ai/dsh-client-store` 的本包拥有不变量配套。

对齐上游 `store/src/invariant.ts`。公开面仅中文名。

无运行时不变量：本包导出库引擎且不创建进程全局状态；每个存储实例由其归属测试覆盖。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-client-store'#本包的不变量所有权名
名称='client-store-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时检查：存储实例由归属测试覆盖。"""
    return#不挂监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
