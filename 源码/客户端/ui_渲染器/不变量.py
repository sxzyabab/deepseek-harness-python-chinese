from ...依赖 import cordis#外部依赖胶水

包名='@deepseek-ai/dsh-client-ui-renderer'#本包的不变量所有权名
名称='client-ui-renderer-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#安装检查
    """拦截 slots/changed：键非法或版本未 bump 则 fail。"""
    def 派发时(_模式,事件名,参数):#拦截派发
        """只关心槽位变更。"""
        if 事件名!='slots/changed':#无关
            return#结束
        键=参数[0] if 参数 is not None and len(参数)>0 else None#首参为槽键
        if not isinstance(键,str) or 键=='':#键非法
            失败("'slots/changed' dispatched without a slot key argument")#报告失败
            return#结束
        槽登记表=上下文对象.获取服务('slots')#取注册表
        if 槽登记表 is not None and 槽登记表.getVersion(键)==0:#有服务且版本未 bump
            失败(f"'slots/changed' fired for \"{键}\" before any mutation bumped its version — emission must follow the applied mutation")#报告
    上下文对象.监听('internal/dispatch',派发时,{'global':True})#全局监听

def 应用(上下文对象):#登记本包的不变式伴生
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记拆除器

name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
