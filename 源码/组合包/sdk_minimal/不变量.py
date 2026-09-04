"""`@deepseek-ai/dsh-sdk-minimal` 的本包拥有不变量配套。

对齐上游 `sdk-minimal`。公开面仅中文名。无运行时不变量：本包是静态补丁列表载体。
"""
from ...内核.智能体循环.辅助 import 已兑现#立刻兑现的操作任务

包名='@deepseek-ai/dsh-sdk-minimal'#本包的不变量所有权名
名称='sdk-minimal-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#空安装器
    """空安装器，不挂运行时检查。"""
    return#无检查

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
