from .作用域事件 import 按事件取主体解析器,未登记
from . import 是否作用域载体,获取载体键

包名='@deepseek-ai/dsh-scope'
名称='scope-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """把作用域派发贡献安装进其子注册纤程。"""
    def 监听(_模式,事件名,参数,派发接收者):
        """检查作用域过滤事件的载体与主体。"""
        解析器=按事件取主体解析器(事件名)
        if 解析器 is 未登记:
            return
        if not 是否作用域载体(派发接收者):
            失败(
                '"'+事件名+'" 是作用域过滤事件，但派发时没有作用域载体 — '
                +'请把 scopeTarget(base, subject) 作为派发 thisArg（智能体事件：用 agentEvents(ctx, agent)）'
            )
        if 解析器 is not None and 获取载体键(派发接收者) is not 解析器(参数):
            失败(
                '"'+事件名+'" 派发所用作用域载体的键与参数点名的主体不是同一个 — '
                +'载体键与事件主体必须是同一对象（用 agentEvents(ctx, agent)）'
            )
    上下文.监听('internal/dispatch',监听,{'全局':True})

def 应用(上下文):
    """注册作用域不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

应用.name=名称
应用.inject=依赖
default=应用
