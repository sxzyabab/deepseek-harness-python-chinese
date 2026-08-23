"""作用域派发的包内不变量。

对齐上游 `@deepseek-ai/dsh-scope/invariant`。公开面仅中文名；Cordis 加载槽 `name`/`inject`/`apply` 为协议兼容别名，不入 `__all__`。
"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from .作用域事件 import 按事件取主体解析器,未登记#导入主体解析
from . import 是否作用域载体,获取载体键#导入载体判定与键读取

包名='@deepseek-ai/dsh-scope'#本包名（登记到 invariants 服务时用）
名称='scope-invariant'#配套插件名（字面量对齐上游）
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖声明槽

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#安装作用域不变量
    """把作用域派发贡献安装进其子注册光纤。"""
    def 监听(_模式,事件名,参数,派发接收者):#检查载体与主体
        """检查作用域过滤事件的载体与主体。"""
        解析器=按事件取主体解析器(事件名)#取该事件的主体解析器
        if 解析器 is 未登记:#非作用域过滤事件
            return#非作用域过滤事件则放过
        if not 是否作用域载体(派发接收者):#this 不是作用域载体
            失败(
                '"'+事件名+'" is a scope-filtered event but was dispatched without a scope carrier — '#缺载体
                +'pass scopeTarget(base, subject) as the dispatch thisArg (agent events: use agentEvents(ctx, agent))'#用法（诊断字面量对齐上游）
            )#缺少载体则失败
        if 解析器 is not None and 获取载体键(派发接收者) is not 解析器(参数):#载体键与参数主体不一致
            失败(
                '"'+事件名+'" was dispatched with a scope carrier keyed to a DIFFERENT subject than its arguments name — '#主体不同
                +"the carrier key and the event's subject must be the same object (use agentEvents(ctx, agent))"#须同一对象
            )#主体不一致则失败
    上下文对象.on('internal/dispatch',监听,{'global':True})#全局监听，覆盖全部作用域过滤事件

def 应用(上下文对象):#注册作用域不变量配套
    """注册作用域不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记贡献并返回拆除器

apply=应用#Cordis 插件入口槽
