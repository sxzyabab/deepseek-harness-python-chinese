"""`@deepseek-ai/dsh-workspace` 的本包拥有不变量配套。对齐上游 workspace/src/invariant.ts。"""
包名='@deepseek-ai/dsh-workspace'#本包的不变量所有权名
名称='workspace-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

def 工作区标识(标识):
    """把字符串打成工作区 id 品牌。"""
    return 标识#品牌即字符串

def 安装(上下文对象,失败):
    """注册表实体缓存必须镜像持久表：旁路写入会在缓存仍发布实体时删除记录。变更是 dict。"""
    def 监听变更(变更):
        """domain/changed 监听。"""
        域=变更['domain'] if 'domain' in 变更 else None#域名
        表=变更['table'] if 'table' in 变更 else None#表名
        if 域!='workspace' or 表!='workspaces':#非工作区表
            return#忽略
        键=变更['key'] if 'key' in 变更 else None#记录键
        操作=变更['operation'] if 'operation' in 变更 else None#操作
        if 操作=='deleted':#删除
            if 上下文对象.workspaceRegistry.get(工作区标识(键)) is not None:#缓存仍发布
                失败("workspace record was deleted while the registry cache still publishes it — some write path bypassed ctx.workspaceRegistry")#失败
            return#删除路径结束
        if 上下文对象.workspaceRegistry.get(工作区标识(键)) is None:#持久落地但缓存无实体
            失败("workspace record landed durably but the registry cache holds no entity for it — the cache and the domain table have diverged")#失败
    上下文对象.监听('domain/changed',监听变更)#挂监听
    return None#无额外拆除

安装.inject=['workspaceRegistry']#安装前需要注册表

def 应用(上下文对象):
    """登记本包的不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
