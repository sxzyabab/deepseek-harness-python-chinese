"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-storage-domain'
名称='storage-domain-invariant'
依赖=['invariants']

def 安装(上下文,失败):
    """每条 `domain/changed` 必须与发出该事件的域的权威内存状态一致。"""
    def 监听变更(变更):
        """核对一条域变更事件与内存状态。变更是 dict。"""
        域=上下文.storage.form('domain').get(变更['domain'])
        if 域 is None:
            失败("domain/changed for '"+变更['domain']+"' emitted while that domain is not open")
        if 变更['table']=='':#空表名表示全局写入
            if getattr(域,'global').get()!=变更['value']:#global 是关键字，只能 getattr 取属性
                失败("domain/changed global value for '"+变更['domain']+"' differs from the in-memory global")
            return
        当前=域.table(变更['table']).get(变更['key'])
        if 变更['operation']=='deleted':
            if 当前 is not None:
                失败("domain/changed deletion of '"+变更['domain']+"'."+"'"+变更['table']+"'['"+变更['key']+"'] emitted while the record is still in memory")
            return
        if 变更['operation']=='put' and 当前!=变更['value']:
            失败("domain/changed value for '"+变更['domain']+"'."+"'"+变更['table']+"'['"+变更['key']+"'] differs from the in-memory record")
    上下文.监听('domain/changed',监听变更,{'全局':True})

安装.inject=['storage']

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
