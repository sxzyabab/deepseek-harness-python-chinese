"""默认 Agent 模型选择的包内不变量配套。

该服务没有独立事件关系：设置注册在当前选择能观察到任何可变值之前已经校验完毕。空安装器把这种缺失明确留在组合后的不变量集合里。

对齐上游 `agent-default-model/src/invariant.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-agent-default-model'#本包的不变量所有权名
名称='agent-default-model-invariant'#配套插件名（字面量不译）
注入=['invariants']#依赖 invariants 服务

__all__=('包名','名称','注入','安装','应用')#仅中文公开名

def 安装(*位置参数):#空安装器，不挂运行时检查
    """无运行时不变量：设置校验拥有唯一的可变值关系。位置参数由登记约定传入，此处忽略。"""
    return#不挂运行时检查

def 应用(上下文对象):#登记空贡献并返回拆除器
    """注册故意为空的不变量贡献，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记空贡献并返回拆除器
