"""@deepseek-ai/dsh-compaction-basic 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-compaction-basic'#本包的不变量所有权名
名称='compaction-basic-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 安装(子上下文=None,失败=None):#空安装器
    """无运行时不变量：本包不暴露独立事件序列或可变数据关系，超出其拥有 seam 已强制的约定。"""
    return None#不挂运行时检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis 插件入口
