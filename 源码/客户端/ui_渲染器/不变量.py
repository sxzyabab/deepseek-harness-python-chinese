"""`@deepseek-ai/dsh-client-ui-renderer` 的本包拥有不变量配套。

对齐上游 `ui-renderer/src/invariant.ts`。公开面仅中文名。
校验每一次 `slots/changed` 派发时，其变更已作用到渲染器拥有的槽位注册表。
"""
from ...依赖 import cordis#外部依赖胶水

包名='@deepseek-ai/dsh-client-ui-renderer'#本包的不变量所有权名
名称='client-ui-renderer-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 已兑现(值=None):#立刻兑现的操作任务
    """把同步结果包成可 wait 的任务。"""
    class _任务:#内联已决议任务
        def wait(自身): return 值#英文 wait
        def 等待(自身): return 值#中文等待
    return _任务()#返回任务

def 安装(上下文对象,失败):#安装检查
    """拦截 slots/changed：键非法或版本未 bump 则 fail。"""
    def 派发时(_模式,事件名,参数):#拦截派发
        """只关心槽位变更。"""
        if 事件名!='slots/changed':#无关
            return#结束
        键=参数[0] if 参数 else None#首参为槽键
        if not isinstance(键,str) or 键=='':#键非法
            失败("'slots/changed' dispatched without a slot key argument")#报告失败
            return#结束
        槽们=上下文对象.get('slots')#取注册表
        if 槽们 is not None:#有服务
            取版本=getattr(槽们,'getVersion',None) or getattr(槽们,'版本',None)#版本入口
            版本=取版本(键) if callable(取版本) else 0#读版本
            if 版本==0:#版本未 bump
                失败(f"'slots/changed' fired for \"{键}\" before any mutation bumped its version — emission must follow the applied mutation")#报告
    上下文对象.on('internal/dispatch',派发时,{'global':True})#全局监听

def 应用(上下文对象):#登记本包的不变式伴生
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#异步登记面

apply=应用#Cordis 插件入口
