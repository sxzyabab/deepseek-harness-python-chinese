import os
import pywebbridge
from urllib.parse import unquote as 百分解码,urlparse as 解析网址,parse_qs as 解析查询
from ....ui_对话.异常 import 注入模块样式文件,模块节点,挂上
from ....ui_渲染器.客户端.绑定 import 作用域绑定上下文,用宿主

__all__=[
    '子智能体聊天标识',
    '子智能体聊天地址前缀',
    '解析子智能体聊天地址',
    '固定聊天对话视图',
    '对话槽面板',
    '侧栏聊天标签',
]

样式模块='sidebar-chat'
子智能体聊天标识='@deepseek-ai/dsh-client-ui-subagent'
子智能体聊天地址前缀='dsh-resource://subagentchat/session/'

def 解析子智能体聊天地址(值):
    '解析侧栏聊天资源地址。坏地址返回 None'
    try:
        网址=解析网址(值)
    except ValueError:
        return None
    if 网址.scheme!='dsh-resource' or 网址.hostname is None or 网址.hostname.lower()!='subagentchat':
        return None
    段表=[段 for 段 in 网址.path.split('/') if 段!='']
    if len(段表)!=2 or 段表[0]!='session':
        return None
    查询=解析查询(网址.query,keep_blank_values=True)
    父表=查询['parent'] if 'parent' in 查询 else []
    模式表=查询['mode'] if 'mode' in 查询 else []
    父=父表[0] if len(父表)>0 else None
    模式=模式表[0] if len(模式表)>0 else None
    if 父 is None or 父=='' or 模式 not in ('one-shot','continuable','unknown'):
        return None
    段=段表[1]
    索引=0
    长度=len(段)
    while 索引<长度:
        if 段[索引]=='%':
            if 索引+2>=长度:
                return None
            十六=段[索引+1:索引+3]
            if 十六[0] not in '0123456789abcdefABCDEF' or 十六[1] not in '0123456789abcdefABCDEF':
                return None
            索引+=3
        else:
            索引+=1
    return {
        'parentSessionId':父,
        'childSessionId':百分解码(段),
        'mode':模式,
    }

def 固定聊天对话视图(属性):
    '嵌入会话只渲染 chat 视图'
    return 属性['renderSlot']('conversation.session',{'view':'chat'})

class 对话槽面板:
    '子会话 Conversation 宿主'
    def __init__(自身,属性):
        '记下 props。有窗口就按阶段画出嵌入对话'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已订=False
        自身.退订=[]
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按活跃、空白和父会话是否已定，选出 settling、hero 或 active'
        属性=自身.属性
        if 'window' not in 属性:
            return None
        窗口=属性['window']
        文档=窗口.document
        if 自身.根 is not None:
            自身.根.remove()
        壳=文档.createElement('div')
        壳.style.display='contents'
        def 原样(值):
            '整份快照'
            return 值
        会话=属性['useSession'](原样)
        对话=属性['useConversation'](原样)
        会话标识=属性['sessionId']
        目标=对话['activeTargets']
        if hasattr(目标,'size'):
            有目标=目标.size>0
        else:
            有目标=len(目标)>0
        活跃=有目标 or ((not 会话['blank']) and (not 会话['awaitingFirstTurn'])) or 会话['running']
        if 活跃:
            壳阶段='active'
        elif 会话['promptAttempted']:
            壳阶段='engaging'
        else:
            壳阶段='blank'
        def 选自(快照):
            '这一行的 blank。没有行则缺席'
            表=快照['byId'] if isinstance(快照,dict) and 'byId' in 快照 else {}
            行=表[会话标识] if 会话标识 in 表 else None
            if not isinstance(行,dict) or 'blank' not in 行:
                return None
            return 行['blank']
        摘要空=属性['useSessions'](选自)
        子=会话['subagent'] if 'subagent' in 会话 else None
        if 子 is None:
            父待定=False
        else:
            父待定=子['address']['mode']=='continuable' and 子.get('parentAvailable') is None
        开态=会话['openState']
        结算中=(壳阶段=='blank' and 开态=='loading' and 摘要空 is not True) or 父待定
        英雄=壳阶段=='blank' and (开态=='open' or 摘要空 is True)
        if 结算中:
            阶段='settling'
        elif 英雄:
            阶段='hero'
        else:
            阶段='active'
        结果=属性['renderFactorySlot']('conversation.content',{
            'variant':'embedded',
            'phase':阶段,
            'hero':英雄,
            'window':窗口,
            'parent':壳,
        },{'slots':{'views':固定聊天对话视图}})
        挂上(壳,结果)
        if 'parent' in 属性 and 属性['parent'] is not None and 壳.parentNode is None:
            属性['parent'].appendChild(壳)
        自身.根=壳
        自身.订阅()
        return 壳

    def 订阅(自身):
        '快照变了就重画。节点离开页面就退订'
        if 自身.已订:
            return
        def 变更():
            '重画。根已经不在页面上就退订'
            if 自身.根 is None or 自身.根.parentNode is None:
                for 退 in 自身.退订:
                    退()
                自身.退订=[]
                自身.已订=False
                return
            自身.渲染()
        for 名 in ('useSession','useConversation','useSessions'):
            钩=自身.属性[名]
            if hasattr(钩,'_subscribe') and callable(钩._subscribe):
                自身.退订.append(钩._subscribe(变更))
                自身.已订=True

    def __call__(自身,属性=None):
        '槽位再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 侧栏聊天标签:
    '把聊天资源的子引用包进 Conversation 槽'
    def __init__(自身,属性):
        '记下 props。有窗口就画侧栏聊天根'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已订=False
        自身.退订=[]
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '资源还没有值时只留空根。有值时切到子会话再画对话槽'
        属性=自身.属性
        if 'window' not in 属性:
            return None
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '侧栏聊天样式',
            os.path.join(os.path.dirname(__file__),'侧栏聊天.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=模块节点(文档,'div',样式模块,'root')
            自身.根.setAttribute('data-sidebar-chat','')
        while 自身.根.firstChild is not None:
            自身.根.firstChild.remove()
        信息=属性['useTabInfo']()
        标签=信息['tab']
        资源=属性['useResource'](标签['contentId'])
        值=资源['value'] if isinstance(资源,dict) else None
        if 值 is not None:
            引用=值['reference']
            宿主=用宿主()
            适配器=宿主.scope('session')
            源=适配器['bindingSource'](引用)
            绑定=源['getSnapshot']()
            作用域绑定上下文.append(绑定)
            try:
                子=属性['renderSlot']('sidebar.chat.conversation',{
                    'window':窗口,
                    'parent':自身.根,
                })
            finally:
                作用域绑定上下文.pop()
            挂上(自身.根,子)
        if 'parent' in 属性 and 属性['parent'] is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        自身.订阅()
        return 自身.根

    def 订阅(自身):
        '资源或标签变了就重画'
        if 自身.已订:
            return
        def 变更():
            '重画。根离开页面就退订'
            if 自身.根 is None or 自身.根.parentNode is None:
                for 退 in 自身.退订:
                    退()
                自身.退订=[]
                自身.已订=False
                return
            自身.渲染()
        for 名 in ('useResource','useTabInfo'):
            钩=自身.属性.get(名)
            if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                自身.退订.append(钩._subscribe(变更))
                自身.已订=True

    def __call__(自身,属性=None):
        '槽位再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
