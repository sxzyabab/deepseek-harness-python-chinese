"""@deepseek-ai/dsh-tool-subagent-report 的本包拥有不变量配套。对齐上游 tool-subagent-report/src/invariant.ts。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-tool-subagent-report'#本包的不变量所有权名
名称='tool-subagent-report-invariant'#配套不变量插件名（字面量不译）
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis插件名槽
inject=注入#Cordis依赖声明槽

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：本适配器没有独立生命周期流；发送方授权与投递关系属于子智能体服务。"""
    return None#不挂运行时检查；子上下文与失败由登记约定传入

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口槽
