"""`@deepseek-ai/dsh-agent-team` 的不变量配套。"""
包名='@deepseek-ai/dsh-agent-team'#本包名
名称='agent-team-invariant'#配套名
注入=['invariants']#依赖
name=名称#Cordis 名
inject=注入#Cordis 注入

def 安装(子上下文=None,失败=None):return None#空安装

def 应用(上下文对象):return 已兑现(上下文对象.invariants.register(包名,安装))#登记

apply=应用#入口
