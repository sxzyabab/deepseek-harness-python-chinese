from urllib.parse import quote as 百分编码
from . import 文案
from . import 只读撰写器
from . import 子智能体报头谱系
from . import 侧栏聊天

__all__=['文案','只读撰写器','子智能体报头谱系','侧栏聊天','命名空间','依赖','应用','选择只读子智能体']

命名空间=文案.命名空间
依赖=['sessions','uiWorkspace','slots','locale','sidebarRight']

def 选择只读子智能体(属主):
    '一次性历史、未知模式，或父会话离线且子会话已停时认领编写器'
    会话=属主['session'] if isinstance(属主,dict) and 'session' in 属主 else None
    if not isinstance(会话,dict):
        return None
    子=会话['subagent'] if 'subagent' in 会话 else None
    if 子 is None:
        return None
    if 子['address']['mode']=='unknown':
        return {'reason':'unknown'}
    if 子['address']['mode']=='one-shot':
        return {'reason':'one-shot'}
    if 子.get('parentAvailable') is not False:
        return None
    if 会话.get('running') is True:
        return None
    return {'reason':'parent-unavailable'}

def 应用(上下文,配置=None):
    '登记子智能体目录、侧栏聊天和只读编写器'
    def 登记词典():
        '登记本插件中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-subagent: dictionaries')

    def 挂侧栏(子上下文):
        '资源和侧栏类型到齐后登记聊天'
        def 登记资源():
            '打开时持留子会话，中止后释放'
            def 打开(资源地址,选项):
                '持留到中止。坏地址直接抛出'
                信号=选项['signal']
                地址=侧栏聊天.解析子智能体聊天地址(资源地址)
                if 地址 is None:
                    raise RuntimeError('ui-subagent: invalid chat resource address "'+str(资源地址)+'"')
                def 已请求中止():
                    'AbortSignal 认 aborted，资源层的 Event 认 is_set'
                    if hasattr(信号,'aborted'):
                        return 信号.aborted is True
                    return 信号.is_set()
                if 已请求中止():
                    return
                引用=子上下文.sessions.retain(地址,{'source':'sidebarChat','signal':信号})
                try:
                    yield {'ok':True,'value':{'address':地址,'reference':引用}}
                    if not 已请求中止():
                        信号.wait()
                finally:
                    引用.release()
            return 子上下文.resources.register({'protocol':'subagentchat','open':打开})
        子上下文.副作用(登记资源,'ui-subagent: Sidebar chat resources')

        def 可打开(地址):
            '地址能解析才打开'
            return 侧栏聊天.解析子智能体聊天地址(地址) is not None

        def 标题(地址):
            '没有子会话时用聊天，否则用投影标签或子标识'
            解析=侧栏聊天.解析子智能体聊天地址(地址)
            if 解析 is None:
                return '聊天'
            子=解析['childSessionId']
            行=子上下文.sessions.list.getSnapshot()['byId']
            摘要=行[子] if isinstance(行,dict) and 子 in 行 else None
            if not isinstance(摘要,dict):
                return 子
            投影=摘要.get('projectionValues')
            子投影=投影.get('subagent') if isinstance(投影,dict) else None
            标签=子投影.get('label') if isinstance(子投影,dict) else None
            if 标签 is None:
                return 子
            return 标签

        def 登记类型():
            '登记侧栏种'
            return 子上下文.sidebarRightTabs.register({
                'id':侧栏聊天.子智能体聊天标识,
                'kind':'subagentchat',
                'patterns':[侧栏聊天.子智能体聊天地址前缀+'**'],
                'priority':'builtin',
                'canOpen':可打开,
                'title':标题,
            })
        子上下文.副作用(登记类型,'ui-subagent: Sidebar chat type')

        def 登记体():
            '登记标签体'
            return 子上下文.slots.register({
                'name':'sidebar.right.pane.tab',
                'key':侧栏聊天.子智能体聊天标识,
                'children':{'sidebar.chat.conversation':{'kind':'single','scope':'session'}},
            },侧栏聊天.侧栏聊天标签)
        def 等标签槽():
            '等标签槽声明后再登记'
            return 子上下文.slots.inject('sidebar.right.pane.tab',登记体)
        子上下文.副作用(等标签槽,'ui-subagent: Sidebar chat body')

        def 登记对话():
            '登记嵌入对话'
            return 子上下文.slots.register({
                'name':'sidebar.chat.conversation',
            },侧栏聊天.对话槽面板)
        def 等对话槽():
            '等对话槽声明后再登记'
            return 子上下文.slots.inject('sidebar.chat.conversation',登记对话)
        子上下文.副作用(等对话槽,'ui-subagent: Sidebar Conversation')

    上下文.依赖启动(['resources','sidebarRightTabs'],挂侧栏)

    def 目录动作面(_父会话标识=None):
        '打开子项、侧栏打开、刷新投影'
        def 打开子(地址):
            '主工作区打开'
            上下文.uiWorkspace.openSession(地址)
        def 侧栏打开子(地址):
            '侧栏新窗格打开'
            查询='parent='+百分编码(str(地址['parentSessionId']),safe="-_.!~*'()")+'&mode='+百分编码(str(地址['mode']),safe="-_.!~*'()")
            资源=侧栏聊天.子智能体聊天地址前缀+百分编码(str(地址['childSessionId']),safe="-_.!~*'()")+'?'+查询
            上下文.sidebarRight.openResource(资源,{
                'kind':'subagentchat',
                'preferNewPane':True,
            })
        def 刷新投影(父会话标识):
            '刷新这一会话的投影'
            上下文.sessions.refreshProjections(父会话标识)
        return {
            'openChild':打开子,
            'openChildAside':侧栏打开子,
            'refreshProjection':刷新投影,
        }

    def 登记谱系():
        '标题旁谱系'
        return 上下文.slots.register({
            'name':'conversation.session.header.lineage',
            'locale':命名空间,
            'inject':目录动作面,
        },子智能体报头谱系.子智能体报头谱系)
    上下文.slots.inject('conversation.session.header.lineage',登记谱系)

    def 登记目录():
        '标题动作带里的下级数量，排在预设标签和后台任务之间'
        return 上下文.slots.register({
            'name':'conversation.session.header.actions',
            'id':'subagent-catalog',
            'order':10,
            'locale':命名空间,
            'inject':目录动作面,
        },子智能体报头谱系.子智能体名录动作)
    上下文.slots.inject('conversation.session.header.actions',登记目录)

    def 登记只读():
        '只读编写器'
        return 上下文.slots.register({
            'name':'conversation.composer',
            'priority':-10,
            'locale':命名空间,
            'select':选择只读子智能体,
        },只读撰写器.只读撰写器)
    上下文.slots.inject('conversation.composer',登记只读)

inject=依赖
apply=应用
