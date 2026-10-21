import os
from ...异常 import 注入模块样式文件,标样式模块,挂上,接上
from ..约定.快照 import 会话阶段
from .宽度控件 import 会话宽度控件

__all__=['主面板']

样式模块='conversation-root'

class 主面板:
    '主会话框：页眉、内容工厂，以及活动阶段的宽度手柄'
    def __init__(自身,属性):
        '记下 props 并画出根'
        自身.属性=属性
        自身.根=None
        自身.宽度=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 渲染(自身):
        '回放中的空白会话先藏起撰写器，摘要已证明空白的除外'
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
            会话标识=属性.get('sessionId')
            会话=属性['useSession'](lambda 快照:快照)
            对话=属性['useConversation'](lambda 快照:快照)
            if 会话 is None or 对话 is None:
                外壳阶段='blank'
            else:
                外壳阶段=会话阶段(会话,对话)
            打开状态=None if 会话 is None else 会话.get('openState')
            def 读摘要空白(列表):
                '列表摘要里的 blank。没有会话标识则为 None'
                if 会话标识 is None:
                    return None
                摘要=列表['byId'].get(会话标识) if isinstance(列表,dict) else None
                if 摘要 is None:
                    return None
                return 摘要.get('blank')
            摘要空白=属性['useSessions'](读摘要空白)
            子=None if 会话 is None else 会话.get('subagent')
            父级未定=isinstance(子,dict) and isinstance(子.get('address'),dict) and 子['address'].get('mode')=='continuable' and 子.get('parentAvailable') is None
            落定=会话标识 is not None and (
                (外壳阶段=='blank' and 打开状态=='loading' and 摘要空白 is not True)
                or 父级未定
            )
            英雄=会话标识 is None or (外壳阶段=='blank' and (打开状态=='open' or 摘要空白 is True))
            if 落定:
                阶段='settling'
            elif 英雄:
                阶段='hero'
            else:
                阶段='active'
            旧=自身.根
            父=旧.parentNode if 旧 is not None else (属性['parent'] if 'parent' in 属性 else None)
            根=文档.createElement('div')
            根.className='root'
            标样式模块(根,样式模块)
            根.setAttribute('data-phase',阶段)
            挂上(根,属性['renderSlot']('conversation.header',{'window':窗口}))
            挂上(根,属性['renderFactorySlot']('conversation.content',{
                'variant':'main',
                'phase':阶段,
                'hero':英雄,
                'window':窗口,
            },{
                'slots':{'widthControls':会话宽度控件},
            }))
            自身.根=接上(旧,根,父)
            if not 自身.已订:
                def 变更():
                    '阶段变了就重画主面板'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 名 in ('useSession','useConversation','useSessions'):
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
