"""`@deepseek-ai/dsh-credentials` 的包内不变量配套。"""
包名='@deepseek-ai/dsh-credentials'#本包名
名称='credentials-invariant'#配套插件名
依赖=['invariants']

def 安装(上下文,失败):#安装凭证更新事件不变量
    """credentials/updated 只能在凭证服务仍存活时发出。"""
    def 监听更新(引用,*位置参数):#监听已提交的凭证更新
        """监听已提交的凭证更新。"""
        if 上下文.获取服务('credentials') is None:#服务已不在仍在发事件
            失败('credentials/updated for "'+str(引用)+'" emitted without a live credentials service')#报告拆除后泄漏
    上下文.监听('credentials/updated',监听更新)#更新监听结束

def 应用(上下文):#对外导出配套入口
    """登记本包的不变量配套。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用
default=应用
