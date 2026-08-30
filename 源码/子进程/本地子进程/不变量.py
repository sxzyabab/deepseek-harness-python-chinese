"""`@deepseek-ai/dsh-subprocess-local` 的本包拥有不变量配套。

对齐上游 `subprocess-local/src/invariant.ts`。公开面仅中文名；无英文别名。

无运行时不变量：本包在所属缝已强制的约定之外，不暴露独立事件序列或可变数据关系。
"""
from ...依赖 import cordis#外部依赖胶水
__all__=('包名','名称','注入','安装','应用')#仅中文公开名

包名='@deepseek-ai/dsh-subprocess-local'#本包在不变量注册表中的名字
名称='subprocess-local-invariant'#配套不变量插件名（字面量不译）
注入=['invariants']#预留包所有权前必须具备的服务

def 安装(*位置参数):#空安装器
    """无运行时不变量：本包在所属缝已强制的约定之外，不暴露独立事件序列或可变数据关系。位置参数由登记约定传入，此处忽略。"""
    return#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器
