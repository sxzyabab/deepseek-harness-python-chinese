'由已有对话和会话日志模型支撑的、会话作用域侧边栏标签'

import weakref
from ..文案 import 命名空间
from .聊天节点.模型 import 聊天节点模型
from .聊天节点.文档对象 import 主聊天根
from .聊天节点.定位目标 import 解析聊天定位目标
from .聊天节点.选取器 import 检查器聊天选取器
from .会话日志.模型 import 会话日志模型
from .会话日志.聊天目标 import 会话日志聊天目标
from .视图 import 会话检查器视图

__all__=['登记检查器标签']

def 取(值,键):
    '字典字段或对象属性；没有则 None'
    if 值 is None:
        return None
    if isinstance(值,dict):
        return 值.get(键)
    return getattr(值,键,None)

def 登记检查器标签(上下文):
    '登记会话检查器侧边栏页及其会话作用域来源'
    活动={'选取器':None}
    已释放={'值':False}
    def 拆选取():
        '插件释放时拆掉自己的选取器，不调用面板回调'
        已释放['值']=True
        if 活动['选取器'] is not None:
            活动['选取器'].拆除()
    上下文.副作用(拆选取,'session-inspector: chat picker')
    翻译=上下文.locale.bind(命名空间)
    标识='@deepseek-ai/dsh-experimental-session-inspector'
    def 登记标签():
        '登记侧边栏标签和引导'
        return 上下文.sidebarRightTabs.register({
            'id':标识,
            'kind':'session-inspector-log',
            'title':lambda:翻译('tab.title'),
            'guide':[{'id':'open','order':60,'title':lambda:翻译('tab.title'),'description':lambda:翻译('tab.description')}],
        })
    上下文.副作用(登记标签,'session-inspector: sidebar tab')
    弱表=weakref.WeakKeyDictionary()
    号表={}
    def 取来源(绑定):
        '按绑定身份取已建来源'
        try:
            return 弱表.get(绑定)
        except TypeError:
            return 号表.get(id(绑定))
    def 存来源(绑定,来源):
        '弱引用失败时按编号留下'
        try:
            弱表[绑定]=来源
        except TypeError:
            号表[id(绑定)]=来源
    def 注入(会话标识):
        '按会话绑定复用模型'
        绑定=上下文.sessions.binding(会话标识)
        if 绑定 is None:
            raise RuntimeError(f'session-inspector: unknown Session {会话标识}')
        来源=取来源(绑定)
        if 来源 is None:
            对话=上下文.uiConversation.binding(绑定)
            聊天=聊天节点模型(对话)
            日志=会话日志模型(绑定.eventSource)
            def 聊天根(会话标识=会话标识):
                '当前主区就是这个会话时返回主对话根'
                当前=上下文.uiSession.adapter.current.getSnapshot()
                if 取(当前,'key')==会话标识:
                    return 主聊天根()
                return None
            def 选取聊天(所有者,已选取,已取消,聊天根=聊天根):
                '已释放或主对话不可用时不开始选取'
                if 已释放['值']:
                    return None
                if 活动['选取器'] is not None:
                    活动['选取器'].取消()
                选取器持有={'选取器':None}
                def 释放():
                    '这一次选取结束时清掉活动引用'
                    if 活动['选取器'] is 选取器持有['选取器']:
                        活动['选取器']=None
                选取器=检查器聊天选取器(聊天根,所有者,已选取,已取消,释放)
                选取器持有['选取器']=选取器
                if not 选取器.开始():
                    return None
                活动['选取器']=选取器
                def 停止():
                    '卸掉这一次选取'
                    选取器.拆除()
                return 停止
            def 解析目标(目标,对话=对话):
                '从当前对话快照解析定位坐标'
                快照=对话.snapshot.getSnapshot()
                视图=取(快照,'views')
                聊天视图=None if 视图 is None else 视图.get('chat')
                节点存储=取(聊天视图,'nodes')
                节点=() if 节点存储 is None else 节点存储.values()
                return 解析聊天定位目标(目标,节点 or [])
            def 记录类型(键,模式,聊天=聊天,日志=日志):
                '不额外订阅，只读当前类型'
                源=聊天.行(键) if 模式=='chat-node' else 日志.行(键)
                if 源 is None:
                    return None
                快照=源.getSnapshot()
                if 快照 is None:
                    return None
                return 快照.get('type') if isinstance(快照,dict) else getattr(快照,'type',None)
            def 日志聊天目标(键,日志=日志):
                '选中日志行在主对话里的位置'
                锚=日志.聊天锚(键)
                if 锚 is None:
                    return None
                return 会话日志聊天目标(锚)
            def 选取行(目标,模式,聊天=聊天,日志=日志,对话=对话):
                '对话分组直接匹配；日志则补上锚点和位置'
                if 模式=='chat-node':
                    return 聊天.选取(目标)
                快照=对话.snapshot.getSnapshot()
                视图=取(快照,'views')
                分组=None if 视图 is None else 视图.grouped('chat')
                引用=None
                if 目标.get('groupKey') is not None and 分组 is not None:
                    for 条目 in 取(分组,'entries') or []:
                        if 取(条目,'kind')=='group' and 取(条目,'key')==目标.get('groupKey'):
                            引用=条目
                            break
                组=None
                if 取(引用,'kind')=='group':
                    组=分组.groupSource(取(引用,'key')).getSnapshot()
                节点键=目标.get('nodeKey')
                if 节点键 is None and 组 is not None:
                    成员=取(组,'members') or []
                    if len(成员)>0:
                        节点键=取(成员[0],'key')
                节点=None
                if 节点键 is not None:
                    聊天视图=None if 视图 is None else 视图.get('chat')
                    存储=取(聊天视图,'nodes')
                    if 存储 is not None:
                        节点=存储.get(节点键)
                位置=取(节点,'location')
                补={}
                if 节点 is not None:
                    补['anchorSeq']=取(节点,'anchorSeq')
                    补['nodeKind']=取(节点,'kind')
                种类=取(位置,'kind')
                if 种类 in ('turn','step'):
                    补['turn']=取(取(位置,'turn'),'turn')
                if 种类=='step':
                    补['step']=取(取(位置,'step'),'step')
                return 日志.选取({**目标,**补})
            来源={
                'hooks':{'chatRows':聊天,'logRows':日志},
                'keyedHooks':{'chatRecord':聊天.行,'logRecord':日志.行},
                'chatRoot':聊天根,
                'pickChat':选取聊天,
                'resolveChatTargets':解析目标,
                'recordType':记录类型,
                'loadOlder':lambda:绑定.session.loadOlder(),
                'objects':聊天.对象(会话标识),
                'logChatTarget':日志聊天目标,
                'pickRow':选取行,
            }
            存来源(绑定,来源)
        return 来源
    def 登记槽():
        '登记这一页的槽'
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab',
            'key':标识,
            'locale':命名空间,
            'inject':注入,
        },会话检查器视图)
    上下文.slots.inject('sidebar.right.pane.tab',登记槽)
