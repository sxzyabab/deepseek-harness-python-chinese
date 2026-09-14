from .团队动作 import 团队动作#动作 UI
from .文案 import 命名空间,中文,英文#词典

__all__=['注入','挂载智能体团队界面','登记界面']#仅中文公开名

注入=['sessions','remote','slots','locale']#依赖

def 领导会话标识(会话服务,会话标识):#映射 Lead
    """把当前会话映射到 Team Lead 会话。"""
    绑定=会话服务.binding(会话标识)#绑定对象
    if 绑定 is None:#无绑定
        return 会话标识#自身即 Lead
    会话=绑定.session#会话对象
    if 会话 is None:#无会话
        return 会话标识#自身即 Lead
    快照=会话.getSnapshot()#快照 dict
    if 'subagent' not in 快照:#非子智能体
        return 会话标识#自身即 Lead
    子=快照['subagent']#子地址
    if 子 is None or 'address' not in 子:#无地址
        return 会话标识#自身即 Lead
    地址=子['address']#地址
    if 地址 is None or 'parentSessionId' not in 地址:#无父
        return 会话标识#自身即 Lead
    父=地址['parentSessionId']#父会话
    if 父 is not None:#有父
        return 父#Lead
    return 会话标识#自身即 Lead

def 登记界面(上下文):#注册 UI
    """登记词典与标题栏动作槽。"""
    def 卸词典():#词典拆除
        """登记词典并返回拆除器。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(卸词典,'client-ui-agent-team: dictionaries')#词典
    会话服务=上下文.sessions#会话服务

    def 加载(会话标识):#加载总览
        """读总览 Remote。"""
        return 上下文.remote.agentTeams.view(领导会话标识(会话服务,会话标识)).等待()#读总览

    def 建任务(会话标识,输入):#建任务
        """建任务 Remote。"""
        return 上下文.remote.agentTeams.createTask(领导会话标识(会话服务,会话标识),输入).等待()#建任务

    def 更新任务(会话标识,输入):#更新任务
        """更新任务 Remote。"""
        请求={#拷贝必填
            'taskId':输入['taskId'],#任务 id
            'expectedRevision':输入['expectedRevision'],#版本
            'action':输入['action'],#动作
        }#骨架
        if 'owner' in 输入 and 输入['owner'] is not None:#有 owner
            请求['owner']=输入['owner']#写回
        for 键 in ('subject','description','blockedBy','writeScopes'):#可选字段
            if 键 in 输入 and 输入[键] is not None:#有值
                请求[键]=输入[键]#写入
        return 上下文.remote.agentTeams.updateTask(领导会话标识(会话服务,会话标识),请求).等待()#更新

    def 打开队友(会话标识,成员):#打开 teammate
        """打开 teammate 子会话。"""
        if 成员['role']!='teammate':#仅 teammate
            return#返回
        父会话=领导会话标识(会话服务,会话标识)#Lead
        会话服务.refreshSubagents(父会话)#刷新子列表已同步
        当前=会话服务.list.getSnapshot()#当前列表
        if 当前['current']!=会话标识:#当前会话已变
            return#返回
        会话服务.openSubagent({#打开子会话
            'parentSessionId':父会话,#父会话
            'childSessionId':成员['id'],#子会话
            'mode':'continuable',#可续模式
        })#打开结束

    动作={'load':加载,'createTask':建任务,'updateTask':更新任务,'openTeammate':打开队友}#注入动作
    def 注入动作():#注入动作
        """登记标题栏动作槽。"""
        return 上下文.slots.register({#登记槽位
            'name':'conversation.session.header.actions',#槽位名
            'id':'agent-team',#插件 id
            'order':20,#排序
            'locale':命名空间,#词典命名空间
            'inject':动作,#注入动作
        },团队动作)#挂标题栏动作
    上下文.slots.inject('conversation.session.header.actions',注入动作)#注入槽位

def 挂载智能体团队界面(上下文,贡献):#挂载 Team UI
    """挂载一份生成的 Team Remote contribution，再注册其浏览器 UI。"""
    卸远程=上下文.remote.$mount(贡献).等待()#挂 Remote，得到拆除函数
    界面=上下文.依赖启动(['sessions','remote.agentTeams','slots','locale'],登记界面)#注入 UI
    try:#等就绪
        界面.等待()#等待插件树抛出启动失败
    except Exception:#挂载 UI 可能抛 DOM/插件错误，契约未定所以收不窄
        界面.dispose().等待()#失败卸 UI
        卸远程()#失败卸 Remote
        raise#上抛
    def 卸除():#卸除器
        """卸 UI 与 Remote。"""
        界面.dispose().等待()#卸 UI
        卸远程()#卸 Remote
    return 卸除#卸除器

inject=注入#Cordis 别名
