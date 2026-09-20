"""向 invariants 登记渲染器槽位变更约束。"""
包名='@deepseek-ai/dsh-client-ui-renderer'
名称='client-ui-renderer-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """拦截 slots/changed：键非法或版本未 bump 则 fail。"""
    def 派发时(_模式,事件名,参数):
        """只审计槽位变更事件。"""
        if 事件名!='slots/changed':
            return
        键=参数[0] if 参数 is not None and len(参数)>0 else None
        if not isinstance(键,str) or 键=='':
            失败("'slots/changed' 派发时没有槽键参数")
            return
        槽登记表=上下文.获取服务('slots')
        if 槽登记表 is not None and 槽登记表.getVersion(键)==0:
            失败("'slots/changed' 在 \""+键+"\" 上触发时版本尚未 bump — 必须先完成变更再发事件")
    上下文.监听('internal/dispatch',派发时,{'global':True})

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
