"""`@deepseek-ai/dsh-webhook` 的本包拥有不变量配套。对齐上游 `webhook/src/invariant.ts`。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-webhook'#本包的不变量所有权名
名称='webhook-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 已兑现(值=None):#立刻兑现的操作任务
    """把值包成立即兑现的 thenable。"""
    class _任务:#同步任务
        def wait(自身,超时=None):#阻塞等待
            return 值#原样返回
        def 等待(自身,超时=None):#中文别名
            return 值#原样返回
    return _任务()#已完成

def 安装(上下文对象,失败):#安装 webhook 来源准入不变量
    """校验 webhook 来源消息已属于其 cwd 工作区。"""
    def 内部派发(_模式,事件名,参数,*剩余):#提交前检查
        """提交前检查 session/event。"""
        if 事件名!='session/event':#非会话事件
            return#放过
        会话,事件=参数[0],参数[1]#会话与事件
        if 取字段(事件,'type')!='agent/inbox/spliced':#非收件箱拼接
            return#放过
        插入们=取字段(取字段(事件,'data'),'inserted',[])#插入消息
        webhook消息=[消息 for 消息 in 插入们 if 取字段(取字段(消息,'source'),'kind')=='webhook']#webhook来源
        if len(webhook消息)==0:#没有 webhook 消息
            return#放过
        工作目录=取字段(取字段(会话,'header'),'cwd')#会话 cwd
        if 工作目录 is None:#无 cwd
            return 失败(f'webhook Session "{取字段(取字段(会话,"header"),"id")}" has no cwd')#失败
        拥有者们=[工作区 for 工作区 in 上下文对象.workspaceRegistry.list() if 取字段(会话,'id') in 取字段(工作区,'sessionIds',[])]#拥有者
        if len(拥有者们)!=1:#不是恰好一个
            return 失败(f'webhook Session "{取字段(取字段(会话,"header"),"id")}" belongs to {len(拥有者们)} Workspaces at prompt admission')#失败
        if 拥有者们[0].path!=工作目录:#cwd不一致
            失败(f'webhook Session "{取字段(取字段(会话,"header"),"id")}" cwd {repr(工作目录)} differs from its Workspace path')#失败
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

安装.inject=['workspaceRegistry']#安装时还要 workspaceRegistry

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
