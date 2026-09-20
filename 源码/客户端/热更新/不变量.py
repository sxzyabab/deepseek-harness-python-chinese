"""向 invariants 登记热更新包检查：监视器须在纤程拆除后归零。"""
包名='@deepseek-ai/dsh-client-hmr'
名称='client-hmr-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """按基线差值检查：纤程创建时观察到的监视计数，必须在拆除排空后恢复。"""
    基线表={}
    def 内部插件(纤程):
        """只审计本插件纤程。"""
        if 纤程.名称!='client-hmr':
            return
        身份=id(纤程)
        if 纤程.编号 is not None:
            监视=上下文.__hmr_stat_watchers__
            基线表[身份]=监视
            return
        if 身份 not in 基线表:
            return
        基线=基线表[身份]
        纤程.等待()
        剩余=上下文.__hmr_stat_watchers__
        if 剩余>基线:
            失败('client-hmr 纤程已拆除，仍有 '+str(剩余-基线)+' 个 bundle 统计监视器未排空')
    上下文.事件.监听('internal/plugin',内部插件,{'全局':True})

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
