import importlib.resources as 包资源
from urllib.parse import quote as 百分编码,unquote as 百分解码,urlparse as 解析网址,parse_qs as 解析查询#地址
from nicegui import ui as 界面
from ..异常 import 页面失败文案

__all__=['登记侧栏聊天','子智能体聊天地址','解析子智能体聊天地址','子智能体聊天标识']

def _读样式():
    '读同目录样式。失败时异常文案只有样式读不到，不含路径'
    try:
        原文=包资源.files(__package__).joinpath('侧栏聊天.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None
    return 原文.replace('.root','.subagent-chat-root')

界面.add_css(_读样式(),shared=True)

子智能体聊天标识='@deepseek-ai/dsh-client-ui-subagent'
子智能体聊天地址前缀='dsh-resource://subagentchat/session/'

def 子智能体聊天地址(地址):
    '把子智能体地址编成侧栏资源地址'
    查询='parent='+百分编码(地址['parentSessionId'],safe='')+'&mode='+百分编码(地址['mode'],safe='')
    return 子智能体聊天地址前缀+百分编码(地址['childSessionId'],safe='')+'?'+查询

def 解析子智能体聊天地址(值):
    '解析侧栏聊天资源地址'
    try:
        网址=解析网址(值)
    except ValueError:
        return None
    if 网址.scheme!='dsh-resource' or 网址.hostname is None or 网址.hostname.lower()!='subagentchat':
        return None
    段表=[段 for 段 in 网址.path.split('/') if 段!='']
    if len(段表)!=2 or 段表[0]!='session':
        return None
    查询=解析查询(网址.query)
    父表=查询['parent'] if 'parent' in 查询 else []
    模式表=查询['mode'] if 'mode' in 查询 else []
    父=父表[0] if len(父表)>0 else None
    模式=模式表[0] if len(模式表)>0 else None
    if 父 is None or 父=='' or 模式 not in ('one-shot','continuable','unknown'):
        return None
    try:
        子=百分解码(段表[1])
    except (ValueError,UnicodeError):
        return None
    return {'parentSessionId':父,'childSessionId':子,'mode':模式}

def 子智能体聊天资源提供者(会话面):
    '打开时持留子会话，拆除时释放'
    def 打开(资源地址,选项):
        '持留至中止'
        信号=选项['signal'] if 'signal' in 选项 else None
        地址=解析子智能体聊天地址(资源地址)
        if 地址 is None:
            说明=页面失败文案('ui-subagent: invalid chat resource address "'+str(资源地址)+'"')
            raise RuntimeError(说明)
        if 信号 is not None and 信号.is_set():
            return
        引用=会话面.retain(地址,{'source':'sidebarChat','signal':信号})
        try:
            yield {'ok':True,'value':{'address':地址,'reference':引用}}
            if 信号 is not None:
                信号.wait()
        finally:
            引用.release()
    return {'protocol':'subagentchat','open':打开}

def 固定聊天对话视图(属性):
    '嵌入会话只渲染 chat 视图'
    return 属性['renderSlot']('conversation.session',{'view':'chat'})

class 对话槽面板:
    '子会话 Conversation 宿主'
    def __init__(自身,属性):
        '记下。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        需要=('useSession','useConversation','useSessions','sessionId','renderFactorySlot')
        if all(键 in 自身.属性 for 键 in 需要):
            自身.渲染()
    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '嵌入 variant'
        需要=('useSession','useConversation','useSessions','sessionId','renderFactorySlot')
        if not all(键 in 自身.属性 for 键 in 需要):#槽位还没齐
            return#不画
        用会话=自身.属性['useSession']
        用对话=自身.属性['useConversation']
        用会话表=自身.属性['useSessions']
        会话标识=自身.属性['sessionId']
        def 原样(值):
            '原样返回快照'
            return 值
        会话=用会话(原样)
        对话=用对话(原样)
        if not isinstance(会话,dict) or not isinstance(对话,dict):#快照还没到
            return#不画
        目标=对话['activeTargets'] if 'activeTargets' in 对话 else ()#空集与缺键都是没有目标
        空白='blank' in 会话 and 会话['blank'] is True#显式空白
        等待='awaitingFirstTurn' in 会话 and 会话['awaitingFirstTurn'] is True#显式等待首轮
        在跑='running' in 会话 and 会话['running'] is True#显式在跑
        活跃=len(目标)>0 or ((not 空白) and (not 等待)) or 在跑
        尝试='promptAttempted' in 会话 and 会话['promptAttempted'] is True#显式已尝试
        壳阶段='active' if 活跃 else ('engaging' if 尝试 else 'blank')
        def 选自(快照):
            'blank'
            行=快照['byId'][会话标识] if 'byId' in 快照 and 会话标识 in 快照['byId'] else None
            return 行['blank'] if 行 is not None and 'blank' in 行 else None
        摘要空=用会话表(选自)
        子=会话['subagent'] if 'subagent' in 会话 and isinstance(会话['subagent'],dict) else None
        地址=子['address'] if 子 is not None and 'address' in 子 and isinstance(子['address'],dict) else None
        父待定=(地址 is not None and 地址.get('mode')=='continuable' and ('parentAvailable' not in 子 or 子['parentAvailable'] is None))
        开态=会话['openState'] if 'openState' in 会话 else None
        结算中=(壳阶段=='blank' and 开态=='loading' and 摘要空 is not True) or 父待定
        英雄=壳阶段=='blank' and (开态=='open' or 摘要空 is True)
        阶段='settling' if 结算中 else ('hero' if 英雄 else 'active')
        with 界面.column().classes('sidebar-chat-panel subagent-chat-root'):
            自身.属性['renderFactorySlot']('conversation.content',{'variant':'embedded','phase':阶段,'hero':英雄},{'slots':{'views':固定聊天对话视图}})
    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 侧栏聊天标签:
    '把聊天资源的子引用包进 Conversation 槽'
    def __init__(自身,属性):
        '记下。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'useTabInfo' in 自身.属性 and 'useResource' in 自身.属性:
            自身.渲染()
    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '资源未就绪则空；会话区里再画对话槽'
        if 'useTabInfo' not in 自身.属性 or 'useResource' not in 自身.属性:#槽位还没齐
            return#不画
        标签=自身.属性['useTabInfo']()['tab']
        资源=自身.属性['useResource'](标签['contentId'])
        值=资源['value'] if isinstance(资源,dict) and 'value' in 资源 else None
        if 值 is None:
            return
        引用=值['reference'] if isinstance(值,dict) and 'reference' in 值 else None
        def 画对话():
            '在会话作用域里画嵌入对话'
            if 'renderSlot' in 自身.属性:
                自身.属性['renderSlot']('sidebar.chat.conversation',{})
        with 界面.column().classes('sidebar-chat subagent-chat-root'):
            提供=自身.属性['SessionProvider'] if 'SessionProvider' in 自身.属性 else None
            if callable(提供) and 引用 is not None:
                提供({'session':引用,'children':画对话})
            else:
                画对话()
    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 登记侧栏聊天(上下文,翻译):
    '登记聊天资源属主与右侧栏呈现'
    def 登记资源():
        '登记协议'
        return 上下文.resources.register(子智能体聊天资源提供者(上下文.sessions))
    上下文.副作用(登记资源,'ui-subagent: Sidebar chat resources')
    def 可打开(地址):
        '能否打开'
        return 解析子智能体聊天地址(地址) is not None
    def 标题(地址):
        '标签标题'
        解析=解析子智能体聊天地址(地址)
        子=None if 解析 is None else 解析['childSessionId']
        if 子 is None:
            return 翻译('sidebar.chat')
        行=上下文.sessions.list.getSnapshot()['byId']
        摘要=行[子] if 子 in 行 else None
        if 摘要 is None:
            return 子
        投影=摘要['projectionValues'] if 'projectionValues' in 摘要 else None
        子投影=投影['subagent'] if 投影 is not None and 'subagent' in 投影 else None
        标签=子投影['label'] if 子投影 is not None and 'label' in 子投影 else None
        return 标签 if 标签 is not None else 子
    def 登记类型():
        '登记侧栏种'
        return 上下文.sidebarRightTabs.register({
            'id':子智能体聊天标识,
            'kind':'subagentchat',
            'patterns':[子智能体聊天地址前缀+'**'],
            'priority':'builtin',
            'canOpen':可打开,
            'title':标题,
        })
    上下文.副作用(登记类型,'ui-subagent: Sidebar chat type')
    def 登记体():
        '登记标签体'
        return 上下文.slots.inject('sidebar.right.pane.tab',lambda:上下文.slots.register({
            'name':'sidebar.right.pane.tab',
            'key':子智能体聊天标识,
            'children':{'sidebar.chat.conversation':{'kind':'single','scope':'session'}},
        },侧栏聊天标签))
    上下文.副作用(登记体,'ui-subagent: Sidebar chat body')
    def 登记对话():
        '登记嵌入对话'
        return 上下文.slots.inject('sidebar.chat.conversation',lambda:上下文.slots.register({
            'name':'sidebar.chat.conversation',
        },对话槽面板))
    上下文.副作用(登记对话,'ui-subagent: Sidebar Conversation')
