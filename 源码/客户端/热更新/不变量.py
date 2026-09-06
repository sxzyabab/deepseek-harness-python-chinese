"""`@deepseek-ai/dsh-client-hmr` 的本包拥有不变量配套。

对齐上游 `hmr/src/invariant.ts`。公开面仅中文名。
拥有关系：节点半边启动的每个打包 stat 监视器必须随光纤一起消亡。
"""
包名='@deepseek-ai/dsh-client-hmr'#本包的不变量所有权名
名称='client-hmr-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):
    """按基线差值检查：光纤创建时观察到的监视计数，必须在拆除排空后恢复。"""
    基线表={}#光纤身份 → 创建时监视基线
    def 内部插件(光纤):
        """只审计本插件光纤。"""
        if 光纤.名称!='client-hmr':#插件显示名
            return#放过
        身份=id(光纤)#引用身份
        if 光纤.编号 is not None:#创建路径
            监视=上下文对象.__hmr_stat_watchers__#创建时监视器数
            基线表[身份]=监视#记下基线
            return#创建路径结束
        if 身份 not in 基线表:#未见过创建
            return#未见过创建
        基线=基线表[身份]#该光纤基线
        光纤.等待()#等到光纤拆除排空
        剩余=上下文对象.__hmr_stat_watchers__#拆除后仍存活的监视器数
        if 剩余>基线:#有残留
            失败('client-hmr fiber disposed but '+str(剩余-基线)+' bundle stat watcher(s) survived teardown')#报告残留监视器
    上下文对象.事件.监听('internal/plugin',内部插件,{'全局':True})#全局监听

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
