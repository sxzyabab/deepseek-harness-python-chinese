"""沙箱政策的本包拥有会话事件不变量。"""
import json#诊断里序列化未知模式
from .会话模式 import 沙盒模式表

包名='@deepseek-ai/dsh-sandbox-policy'
名称='sandbox-policy-invariant'
依赖=['invariants']

def 校验事件(事件,失败):
    """校验本包拥有的事件字段，忽略无关事件。事件是 dict。"""
    if 事件['type']!='sandbox/mode':
        return
    模式=事件['data']['mode']
    if 模式 not in 沙盒模式表:
        失败('sandbox/mode carries unknown mode '+json.dumps(模式,ensure_ascii=False,separators=(',',':'),allow_nan=False))

def 安装(上下文,失败):
    """给已加载与新追加的沙箱模式安装校验。"""
    for 会话 in 上下文.sessions.列出():
        for 事件 in 会话.events:
            校验事件(事件,失败)
    def 内部派发(_模式,事件名,参数,*位置参数):
        """提交前检查 session/event。"""
        if 事件名!='session/event':
            return
        事件=参数[1]
        校验事件(事件,失败)
    上下文.监听('internal/dispatch',内部派发,{'全局':True})

安装.inject=['sessions']#还依赖 sessions

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已安装注册的 disposer。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
