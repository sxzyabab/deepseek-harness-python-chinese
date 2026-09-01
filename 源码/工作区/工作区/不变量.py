"""`@deepseek-ai/dsh-workspace` 的本包拥有不变量配套。对齐上游 workspace/src/invariant.ts。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-workspace'#本包的不变量所有权名
名称='workspace-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明

def 安装(上下文对象,失败):#安装域变更检查
    """注册表实体缓存必须镜像持久表：旁路写入会在缓存仍发布实体时删除记录。"""
    def 监听变更(变更):#domain/changed 监听
        if 变更.get('domain')!='workspace' or 变更.get('table')!='workspaces':#非工作区表
            return#忽略
        键=变更.get('key')#记录键
        if 变更.get('operation')=='deleted':#删除
            if 上下文对象.workspaceRegistry.get(工作区标识(键)) is not None:#缓存仍发布
                失败(f"workspace record '{键}' was deleted while the registry cache still publishes it — some write path bypassed ctx.workspaceRegistry")#失败
            return#删除路径结束
        if 上下文对象.workspaceRegistry.get(工作区标识(键)) is None:#持久落地但缓存无实体
            失败(f"workspace record '{键}' landed durably but the registry cache holds no entity for it — the cache and the domain table have diverged")#失败
    上下文对象.on('domain/changed',监听变更)#挂监听
    return None#无额外拆除

安装.inject=['workspaceRegistry']#安装前需要注册表
应用=lambda 上下文对象: 已兑现(上下文对象.invariants.register(包名,安装))#登记配套
apply=应用#Cordis 插件入口

def 工作区标识(标识):#品牌构造（避免循环导入）
    """把字符串打成工作区 id 品牌。"""
    return 标识#品牌即字符串
