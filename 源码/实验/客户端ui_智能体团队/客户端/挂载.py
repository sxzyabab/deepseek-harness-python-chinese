"""源码安全的 Agent Teams 浏览器注册与 Remote 挂载生命周期。

对齐上游 `client-ui-agent-team/src/client/mount.ts`。公开面仅中文名。
"""
from ....内核.智能体循环.辅助 import 解开#等待承诺
from .团队动作 import 团队动作#动作 UI
from .文案 import 命名空间,中文,英文#词典

__all__=['注入','挂载智能体团队界面','登记界面']#仅中文公开名

注入=['sessions','remote','slots','locale']#依赖
inject=注入#Cordis 别名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 领导会话标识(会话服务,会话标识):#映射 Lead
    """把当前会话映射到 Team Lead 会话。"""
    绑定=会话服务.binding(会话标识) if hasattr(会话服务,'binding') else None#绑定
    快照=取字段(取字段(绑定,'session'),'getSnapshot')#快照方法
    if callable(快照):#有快照
        子=取字段(快照(),'subagent')#子地址
        地址=取字段(子,'address')#地址
        父=取字段(地址,'parentSessionId')#父会话
        if 父 is not None:#有父
            return 父#Lead
    return 会话标识#自身即 Lead

def 登记界面(上下文):#注册 UI
    """登记词典与标题栏动作槽。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'client-ui-agent-team: dictionaries')#词典
    会话们=上下文.sessions#会话服务

    def 加载(会话标识):#加载总览
        """读总览 Remote。"""
        return 解开(上下文.remote.agentTeams.view(领导会话标识(会话们,会话标识)))#读总览

    def 建任务(会话标识,输入):#建任务
        """建任务 Remote。"""
        return 解开(上下文.remote.agentTeams.createTask(领导会话标识(会话们,会话标识),输入))#建任务

    def 更新任务(会话标识,输入):#更新任务
        """更新任务 Remote。"""
        请求=dict(输入) if isinstance(输入,dict) else {#拷贝
            'taskId':取字段(输入,'taskId'),#任务 id
            'expectedRevision':取字段(输入,'expectedRevision'),#版本
            'action':取字段(输入,'action'),#动作
        }#骨架
        所有者=请求.pop('owner',None) if isinstance(请求,dict) else 取字段(输入,'owner')#拆 owner
        if 所有者 is not None:#有 owner
            请求['owner']=所有者#写回
        for 键 in ('subject','description','blockedBy','writeScopes'):#可选字段
            值=取字段(输入,键)#读
            if 值 is not None and 键 not in 请求:#补齐
                请求[键]=值#写入
        return 解开(上下文.remote.agentTeams.updateTask(领导会话标识(会话们,会话标识),请求))#更新

    def 打开队友(会话标识,成员):#打开 teammate
        """打开 teammate 子会话。"""
        if 取字段(成员,'role')!='teammate':#仅 teammate
            return#返回
        父会话=领导会话标识(会话们,会话标识)#Lead
        解开(会话们.refreshSubagents(父会话))#刷新子列表
        当前=取字段(取字段(会话们,'list'),'getSnapshot')#当前列表
        if callable(当前) and 取字段(当前(),'current')!=会话标识:#当前会话已变
            return#返回
        会话们.openSubagent({#打开子会话
            'parentSessionId':父会话,#父会话
            'childSessionId':取字段(成员,'id'),#子会话
            'mode':'continuable',#可续模式
        })#打开结束

    动作={'load':加载,'createTask':建任务,'updateTask':更新任务,'openTeammate':打开队友}#注入动作
    上下文.slots.inject(#注入槽位
        'conversation.session.header.actions',#槽位名
        lambda:上下文.slots.register({#登记槽位
            'name':'conversation.session.header.actions',#槽位名
            'id':'agent-team',#插件 id
            'order':20,#排序
            'locale':命名空间,#词典命名空间
            'inject':lambda:动作,#注入动作
        },团队动作),#挂标题栏动作
    )#inject 结束

def 挂载智能体团队界面(上下文,贡献):#挂载 Team UI
    """挂载一份生成的 Team Remote contribution，再注册其浏览器 UI。"""
    卸远程=解开(上下文.remote.$mount(贡献))#挂 Remote
    界面=上下文.inject(['sessions','remote.agentTeams','slots','locale'],登记界面)#注入 UI
    try:#等就绪
        解开(界面)#等待 UI
    except Exception:#失败
        解开(界面.dispose())#失败卸 UI
        解开(卸远程())#失败卸 Remote
        raise#上抛
    def 卸除():#卸除器
        """卸 UI 与 Remote。"""
        解开(界面.dispose())#卸 UI
        解开(卸远程())#卸 Remote
    return 卸除#卸除器
