from .轨迹节点 import 轨迹节点#目标信封

__all__=['登记轨迹请求头定义']

def 登记轨迹请求头定义(上下文):
    '登记轨迹系统提示节点和请求头事实'
    def 检视系统(先前,事件):
        '系统表面解释由对话服务提供'
        return 上下文.uiConversation.inspectSystemPrompt(先前,事件)

    def 检视请求(先前,事件,系统):
        '请求提示解释由对话服务提供'
        return 上下文.uiConversation.inspectRequestPrompt(先前,事件,系统)

    def 系统匹配(事件):
        '系统消息，以及非追加的表面操作'
        if 事件.get('type')=='system/message' or ('surfaceOp' in 事件 and 事件.get('surfaceOp')!='append'):
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 系统开始(_上下文,匹配,读取器):
        '没有请求头时只留下已知文本；有头时在自己的位置贡献变更'
        if 匹配['event'].get('type')=='assistant/live-chunk':
            raise Exception('system-message requires a durable event')
        先前记录=读取器['previous']('trajectory-system-message')
        先前=None if 先前记录 is None else 先前记录.get('state')
        状态=检视系统(先前,匹配['event'])
        节点=None if not isinstance(状态,dict) else 状态.get('effective')
        if isinstance(状态,dict) and 状态.get('uncertain'):
            头记录=读取器['previous']('trajectory-request-header')
            头=None if 头记录 is None else 头记录.get('state')
            if not isinstance(头,dict):
                return 状态
            提示=dict(头.get('prompt') or {})
            提示['system']=''
            改=dict(状态)
            改['header']={
                'seq':匹配['event'].get('seq'),
                'time':匹配['event'].get('time'),
                'location':匹配.get('location'),
                'prompt':提示,
            }
            return 改
        先前有效=None if not isinstance(先前,dict) else 先前.get('effective')
        先前文本=None if not isinstance(先前有效,dict) else 先前有效.get('text')
        引入=None if not isinstance(状态,dict) else 状态.get('introduced')
        if not isinstance(节点,dict) or 节点.get('text')==先前文本 or (isinstance(引入,dict) and not 引入.get('update')):
            改=dict(状态 or {})
            if isinstance(先前,dict) and 先前.get('header') is not None:
                改['header']=先前['header']
            return 改
        头记录=读取器['previous']('trajectory-request-header')
        头=None if 头记录 is None else 头记录.get('state')
        系统头=None if not isinstance(先前,dict) else 先前.get('header')
        if isinstance(系统头,dict) and (not isinstance(头,dict) or 系统头.get('seq',0)>头.get('seq',0)):
            上一=系统头
        else:
            上一=头
        if not isinstance(上一,dict):
            return 状态
        提示=dict(上一.get('prompt') or {})
        提示['system']=节点.get('text')
        改=dict(状态)
        改['header']={
            'seq':节点.get('seq'),
            'time':节点.get('time'),
            'prompt':提示,
            'change':{
                'seq':节点.get('seq'),
                'time':节点.get('time'),
                'kind':'system',
                'previous':上一.get('prompt'),
            },
            'location':匹配.get('location'),
        }
        return 改

    def 系统更新(上下文,_匹配=None):
        '更新不改状态'
        return 上下文.get('state')

    def 系统视图(上下文):
        '头的序号对上才贡献请求头，否则贡献系统提示文本'
        状态=上下文.get('state') or {}
        头=状态.get('header')
        起点=上下文.get('start') or {}
        if isinstance(头,dict) and 头.get('seq')==(起点.get('event') or {}).get('seq'):
            return 轨迹节点(上下文,头.get('seq'),{'kind':'request-header','header':头})
        提示=状态.get('introduced')
        事件=起点.get('event') or {}
        if isinstance(提示,dict) and 提示.get('text') not in (None,'') and 事件.get('type')=='system/message' and 事件.get('surfaceOp')=='append':
            return 轨迹节点(上下文,提示.get('seq'),{'kind':'system-prompt','prompt':提示})
        return None

    def 请求匹配(事件):
        '请求头各开一条'
        if 事件.get('type')=='request/header':
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 请求开始(_上下文,匹配,读取器):
        '叠上一份请求头或更新的系统头'
        if 匹配['event'].get('type')!='request/header':
            raise Exception('trajectory-request-header start requires request/header')
        头记录=读取器['previous']('trajectory-request-header')
        头=None if 头记录 is None else 头记录.get('state')
        系统记录=读取器['previous']('trajectory-system-message')
        系统状态=None if 系统记录 is None else 系统记录.get('state')
        系统头=None if not isinstance(系统状态,dict) else 系统状态.get('header')
        if isinstance(系统头,dict) and (not isinstance(头,dict) or 系统头.get('seq',0)>头.get('seq',0)):
            先前提示=系统头.get('prompt')
        else:
            先前提示=None if not isinstance(头,dict) else 头.get('prompt')
        系统=None if not isinstance(系统状态,dict) else 系统状态.get('effective')
        检视=检视请求(先前提示,匹配['event'],系统)
        提示=None if not isinstance(检视,dict) else 检视.get('prompt')
        变更=None if not isinstance(检视,dict) else 检视.get('change')
        if 变更 is None and isinstance(系统头,dict) and (not isinstance(头,dict) or 系统头.get('seq',0)>头.get('seq',0)):
            变更=系统头.get('change')
        状态={
            'seq':匹配['event'].get('seq'),
            'time':匹配['event'].get('time'),
            'prompt':提示,
            'location':匹配.get('location'),
        }
        if 变更 is not None:
            状态['change']=变更
        return 状态

    def 请求视图(上下文):
        '有状态才贡献请求头'
        if 上下文.get('state') is None:
            return None
        return 轨迹节点(上下文,上下文['state'].get('seq'),{'kind':'request-header','header':上下文['state']})

    上下文.uiConversation.events.register({
        'kind':'trajectory-system-message',
        'target':'trajectory',
        'match':系统匹配,
        'start':系统开始,
        'update':系统更新,
        'buildViewNode':系统视图,
    })
    上下文.uiConversation.events.register({
        'kind':'trajectory-request-header',
        'target':'trajectory',
        'match':请求匹配,
        'start':请求开始,
        'update':系统更新,
        'buildViewNode':请求视图,
    })
