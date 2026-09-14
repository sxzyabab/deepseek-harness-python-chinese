from .作用域事件 import 按事件取主体解析器,未登记#导入主体解析
from . import 是否作用域载体,获取载体键#导入载体判定与键读取

包名='@deepseek-ai/dsh-scope'#本包名（登记到 invariants 服务时用）
名称='scope-invariant'#配套插件名（字面量对齐上游）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):
    """把作用域派发贡献安装进其子注册光纤。"""
    def 监听(_模式,事件名,参数,派发接收者):
        """检查作用域过滤事件的载体与主体。"""
        解析器=按事件取主体解析器(事件名)#取该事件的主体解析器
        if 解析器 is 未登记:
            return#非作用域过滤事件则放过
        if not 是否作用域载体(派发接收者):
            失败(
                '"'+事件名+'" 是作用域过滤事件，但派发时没有作用域载体 — '#缺载体
                +'请把 scopeTarget(base, subject) 作为派发 thisArg（智能体事件：用 agentEvents(ctx, agent)）'#用法
            )#缺少载体则失败
        if 解析器 is not None and 获取载体键(派发接收者) is not 解析器(参数):
            失败(
                '"'+事件名+'" 派发所用作用域载体的键与参数点名的主体不是同一个 — '#主体不同
                +'载体键与事件主体必须是同一对象（用 agentEvents(ctx, agent)）'#须同一对象
            )#主体不一致则失败
    上下文对象.监听('internal/dispatch',监听,{'全局':True})#全局监听，覆盖全部作用域过滤事件

def 应用(上下文对象):
    """注册作用域不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
