"""@deepseek-ai/dsh-token-meter 的本包拥有不变量配套。对齐上游 `token-meter/src/invariant.ts`。公开面仅中文名。

无运行时不变量：token 估算是按次调用的输出，私有会话缓存在其事件变更边界失效。本包三条投影暴露观察流，但其模式固定 JSON 载荷；用量折叠会替换同一步的样本，因此最终样本纠正更早块时总量不必单调。组合折叠经与测量服务相同的计价启发式，并减去由该服务自身节点导出的影子价格，故其消息数字在构造上等于 `测量().surfaceTokens`，而不是值得在运行时观察的关系。
"""
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-token-meter'#本包的不变量所有权名
名称='token-meter-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(子上下文=None,失败=None):#空安装器
    """空安装器，不挂运行时检查；子上下文与失败由登记约定传入。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口（协议槽）
