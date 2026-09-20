"""登记工作区注册表与持久表镜像一致性检查。"""
包名='@deepseek-ai/dsh-workspace'
名称='workspace-invariant'
依赖=['invariants']

def 工作区标识(标识):
    """把字符串打成工作区 id。"""
    return 标识

def 安装(上下文,失败):
    """注册表实体缓存必须镜像持久表：旁路写入会在缓存仍发布实体时删除记录。变更是 dict。"""
    def 监听变更(变更):
        """校验 workspaces 表变更后缓存与持久是否同态。"""
        域=变更['domain'] if 'domain' in 变更 else None
        表=变更['table'] if 'table' in 变更 else None
        if 域!='workspace' or 表!='workspaces':
            return
        键=变更['key'] if 'key' in 变更 else None
        操作=变更['operation'] if 'operation' in 变更 else None
        if 操作=='deleted':
            if 工作区标识(键) in 上下文.workspaceRegistry:#缓存仍发布
                失败("workspace record was deleted while the registry cache still publishes it — some write path bypassed workspaceRegistry")
            return
        if 工作区标识(键) not in 上下文.workspaceRegistry:#持久落地但缓存无实体
            失败("workspace record landed durably but the registry cache holds no entity for it — the cache and the domain table have diverged")
    上下文.监听('domain/changed',监听变更)
    return None

安装.inject=['workspaceRegistry']#安装前需要注册表

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

__all__=['包名','名称','依赖','安装','应用']
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
