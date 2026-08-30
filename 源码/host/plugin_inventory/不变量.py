"""本包拥有不变量配套。

对齐上游 `plugin-inventory/src/invariant.ts`。公开面仅中文名。
无运行时不变量：每份快照都直接从 Loader 拥有的状态投影。
"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-host-plugin-inventory'#本包所有权名
名称='host-plugin-inventory-invariant'#配套插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """无运行时检查：快照直接从 Loader 投影。"""
    return#不挂

def 应用(上下文对象):#注册不变量配套
    """登记本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
