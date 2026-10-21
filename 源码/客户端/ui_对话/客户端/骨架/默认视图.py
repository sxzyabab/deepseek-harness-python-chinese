import os
from ...异常 import 注入模块样式文件,标样式模块,挂上,接上
from ..约定.快照 import 会话阶段
from ..视图选中项 import 解析活动视图

__all__=['默认会话视图']

样式模块='conversation-root'

class 默认会话视图:
    '滚动区里的活动视图。空白阶段返回空，同时把草稿交给持久化'
    def __init__(自身,属性):
        '记下份额。构造时挂上草稿写出'
        自身.属性=属性
        自身.根=None
        自身.已挂草稿=False
        自身.拆草稿=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 渲染(自身):
        '空白英雄不画视图区。有视图标识时只画那一个 conversation.view'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                '会话根样式',
                os.path.join(os.path.dirname(__file__),'会话根.module.css'),
                样式模块,
            )
            if not 自身.已挂草稿:
                自身.拆草稿=属性['bindDraftPersistence'](属性['actions']['setDraft'])
                属性['inputActions'].persistDraft()
                自身.已挂草稿=True
            页签列=属性['useConversationViews'](lambda 值:值)
            检视=属性['useInspectCall'](lambda 值:值)
            选中标识=属性['useStore'](lambda 快照:快照['view'])
            活动=解析活动视图(页签列,选中标识)
            会话=属性['useSession'](lambda 快照:快照)
            对话=属性['useConversation'](lambda 快照:快照)
            请求=属性['useStore'](lambda 快照:快照['viewRequest'] if 快照.get('viewRequest') is not None else None)
            旧=自身.根
            父=旧.parentNode if 旧 is not None else (属性['parent'] if 'parent' in 属性 else None)
            if 会话.get('blank') and 会话阶段(会话,对话)=='blank':
                自身.根=接上(旧,None,父)
            else:
                视图标识=属性['view'] if 属性.get('view') is not None else (None if 活动 is None else 活动['id'])
                区=文档.createElement('div')
                区.className='viewArea'
                标样式模块(区,样式模块)
                if 视图标识 is not None:
                    挂上(区,属性['renderSlot']('conversation.view',{
                        'inspectCall':检视,
                        'viewRequest':请求,
                        'openView':属性['openView'],
                        'completeViewRequest':属性['actions']['completeViewRequest'],
                        'window':窗口,
                    },{'only':视图标识}))
                自身.根=接上(旧,区,父)
            if not 自身.已订:
                def 变更():
                    '视图或会话变了就重画'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is not None and 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 名 in ('useConversationViews','useInspectCall','useStore','useSession','useConversation'):
                    钩=属性.get(名)
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        自身.退订.append(钩._subscribe(变更))
                自身.已订=True
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
