import os
from ...异常 import 注入模块样式文件,标样式模块,挂上,接上
from ..约定.快照 import 会话阶段

__all__=['会话报头']

样式模块='conversation-root'

class 会话报头:
    '会话出现之前也留着全局导航。有会话时把会话页眉放进标题行'
    def __init__(自身,属性):
        '记下 props 并画出常驻页眉'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 渲染(自身):
        '空白会话去掉标题和页签，但前导槽还在'
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
            会话=属性['useSession'](lambda 快照:快照)
            对话=属性['useConversation'](lambda 快照:快照)
            空白=会话 is None or 对话 is None or (会话.get('blank') and 会话阶段(会话,对话)=='blank')
            会话标识=属性.get('sessionId')
            类名='header'
            if 空白:
                类名=类名+' headerBlank'
            if 会话标识 is None:
                类名=类名+' headerSessionless'
            旧=自身.根
            父=旧.parentNode if 旧 is not None else (属性['parent'] if 'parent' in 属性 else None)
            头=文档.createElement('header')
            头.className=类名
            标样式模块(头,样式模块)
            头.setAttribute('data-window-drag','')
            前导=文档.createElement('div')
            前导.className='headerLeading'
            标样式模块(前导,样式模块)
            前导.setAttribute('data-conversation-header-leading','')
            挂上(前导,属性['renderSlot']('conversation.header.leading',{'window':窗口}))
            头.appendChild(前导)
            if 会话标识 is None:
                空行=文档.createElement('div')
                空行.className='titleRow'
                标样式模块(空行,样式模块)
                头.appendChild(空行)
            else:
                挂上(头,属性['renderSlot']('conversation.session.header',{
                    'hideChrome':空白,
                    'window':窗口,
                }))
            自身.根=接上(旧,头,父)
            if not 自身.已订:
                def 变更():
                    '会话或对话快照变了就重画页眉'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 名 in ('useSession','useConversation'):
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
