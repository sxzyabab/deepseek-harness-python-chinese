import json

__all__=['登记轨迹工具定义']

最大深度=256#父子边允许的最大深度

class 密封参数:
    '工具/值 还没有 PartialArguments。这里只保住本包写进调用块的密封视图'
    def __init__(自身,原文,对象,无效=False):
        '记下原文、解析结果和是否无效'
        自身.原文=原文#原始文本
        自身.对象=对象#解析出的对象
        自身.invalid=无效#解析失败
        自身.isSealed=True#不可再追加

    def closed(自身):
        '密封视图不再接受追加'
        return True

    @staticmethod
    def 从文本(文本):
        '按文本解析。解析失败仍密封，并标无效'
        if not isinstance(文本,str) or 文本=='':
            return 密封参数('' if not isinstance(文本,str) else 文本,None,文本!='')
        try:
            return 密封参数(文本,json.loads(文本),False)
        except json.JSONDecodeError as 错误:#非法 JSON 仍密封
            return 密封参数(文本,None,True)

    @staticmethod
    def 从对象(对象):
        '按对象密封'
        return 密封参数(json.dumps(对象,ensure_ascii=False),对象,False)

密封参数.空=密封参数('',None,False)#没有上一份参数时用它

def 登记轨迹工具定义(上下文):
    '登记轨迹工具生命周期，含嵌套 PTC 分派'
    def 位置回合(匹配):
        '步或回合位置上的回合号'
        位置=匹配.get('location') or {}
        if 位置.get('kind') in ('step','turn') and isinstance(位置.get('turn'),dict):
            return 位置['turn'].get('turn') or 0
        return 0

    def 位置步号(匹配):
        '步位置上的步号'
        位置=匹配.get('location') or {}
        if 位置.get('kind')=='step' and isinstance(位置.get('step'),dict):
            return 位置['step'].get('step') or 0
        return 0

    def 接受边(状态,父,子):
        '拒绝自环、重复父和过深的子树'
        if 父==子 or 子 in 状态['parents']:
            return False
        游标=父
        父深=0
        祖先=set()
        while 游标 is not None:
            if 游标==子 or 游标 in 祖先:
                return False
            祖先.add(游标)
            父深+=1
            游标=状态['parents'].get(游标)
        待查=[{'callId':子,'depth':1}]
        后代=set()
        子深=0
        下标=0
        while 下标<len(待查):
            候选=待查[下标]
            下标+=1
            if 候选['callId'] in 后代:
                return False
            后代.add(候选['callId'])
            子深=max(子深,候选['depth'])
            for 嵌套 in 状态['children'].get(候选['callId']) or []:
                待查.append({'callId':嵌套,'depth':候选['depth']+1})
        return 父深+子深<=最大深度

    def 更新分派(状态,匹配):
        '开始或结算一条子调用'
        事件=匹配['event']
        if 事件.get('type') not in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):
            return 状态
        数据=事件.get('data') or {}
        父=str(数据.get('parentCallId'))
        子=str(数据.get('subCallId'))
        兄弟=list(状态['children'].get(父) or [])
        位=兄弟.index(子) if 子 in 兄弟 else -1
        if 位<0 and not 接受边(状态,父,子):
            return 状态
        if 事件.get('type')=='tool/ptc-dispatch-start' and 位>=0:
            return 状态
        调用表=dict(状态['calls'])
        if 事件.get('type')=='tool/ptc-dispatch-start':
            调用表[子]={
                'phase':'start',
                'callId':数据.get('subCallId'),
                'parentCallId':数据.get('parentCallId'),
                'name':数据.get('name'),
                'argsRaw':json.dumps(数据.get('arguments'),ensure_ascii=False),
                'args':密封参数.从对象(数据.get('arguments')),
                'turn':位置回合(匹配),
                'step':位置步号(匹配),
                'time':事件.get('time'),
                'subCalls':[],
            }
        else:
            先前=调用表.get(子)
            调用表[子]={
                'kind':'tool-result',
                'seq':事件.get('seq'),
                'time':事件.get('time'),
                'callId':数据.get('subCallId'),
                'parentCallId':数据.get('parentCallId'),
                'name':数据.get('name'),
                'args':先前.get('args') if isinstance(先前,dict) and 先前.get('args') is not None else 密封参数.从对象(数据.get('arguments')),
                'call':{'name':数据.get('name'),'argsRaw':json.dumps(数据.get('arguments'),ensure_ascii=False)},
                'callTime':None if not isinstance(先前,dict) or 'kind' in 先前 else 先前.get('time'),
                'content':数据.get('content') or [],
                'meta':数据.get('meta'),
                'isError':数据.get('isError') is True,
                'subCalls':[],
            }
            if 数据.get('error') is not None:
                调用表[子]['error']=数据['error']
        if 位>=0:
            改=dict(状态)
            改['calls']=调用表
            return 改
        子表=dict(状态['children'])
        子表[父]=兄弟+[子]
        父表=dict(状态['parents'])
        父表[子]=父
        return {'rootId':状态['rootId'],'calls':调用表,'children':子表,'parents':父表}

    def 投影调用(状态,调用标识,打断于,已访=None,深度=1):
        '把调用树投影成带 subCalls 的块。未结束且步已关则记成打断'
        if 已访 is None:
            已访=set()
        块=状态['calls'].get(调用标识)
        if 块 is None:
            return None
        if 调用标识 in 已访 or 深度>最大深度:
            拷贝=dict(块)
            拷贝['subCalls']=[]
            return 拷贝
        下一访=set(已访)
        下一访.add(调用标识)
        子调用=[]
        for 子标识 in 状态['children'].get(调用标识) or []:
            孩子=投影调用(状态,子标识,打断于,下一访,深度+1)
            if 孩子 is not None:
                子调用.append(孩子)
        if 'kind' in 块 or 打断于 is None:
            拷贝=dict(块)
            拷贝['subCalls']=子调用
            return 拷贝
        return {
            'kind':'tool-result',
            'seq':(打断于.get('seq') or 0)-0.8,
            'time':打断于.get('time'),
            'callId':块.get('callId'),
            **({} if 块.get('parentCallId') is None else {'parentCallId':块.get('parentCallId')}),
            'name':块.get('name'),
            'args':块.get('args'),
            'call':{'name':块.get('name'),'argsRaw':块.get('argsRaw')},
            'callTime':块.get('time'),
            'content':[],
            'isError':True,
            'error':{'name':'Interrupted','code':'interrupted'},
            'subCalls':子调用,
        }

    def 工具匹配(事件):
        '根调用、根结果，以及挂到 rootCallId 的分派'
        类型=事件.get('type')
        数据=事件.get('data') or {}
        if 类型=='tool/call':
            return {'id':str(数据.get('callId')),'role':'start'}
        if 类型=='tool/result':
            来源=(数据.get('message') or {}).get('source') or {}
            return {'id':str(来源.get('callId')),'role':'update'}
        if 类型 in ('tool/ptc-dispatch-start','tool/ptc-dispatch'):
            根=数据.get('rootCallId')
            if isinstance(根,str) and 根!='':
                return {'id':根,'role':'update'}
        return None

    def 工具开始(_上下文,匹配,_读取器=None):
        '根必须是工具调用'
        if 匹配['event'].get('type')!='tool/call':
            raise Exception('trajectory-tool-call start requires tool/call')
        数据=匹配['event'].get('data') or {}
        根={
            'phase':'start',
            'callId':str(数据.get('callId')),
            'name':数据.get('name'),
            'argsRaw':数据.get('arguments'),
            'args':密封参数.从文本(数据.get('arguments')),
            'turn':数据.get('turn'),
            'step':数据.get('step'),
            'time':匹配['event'].get('time'),
            'subCalls':[],
        }
        return {
            'rootId':根['callId'],
            'calls':{根['callId']:根},
            'children':{},
            'parents':{},
        }

    def 工具更新(上下文,匹配):
        '根结果替换根块；分派走子树'
        if 匹配['event'].get('type')!='tool/result':
            return 更新分派(上下文.get('state') or {'calls':{},'children':{},'parents':{},'rootId':None},匹配)
        状态=上下文.get('state') or {}
        先前=状态.get('calls',{}).get(状态.get('rootId'))
        运行=先前 if isinstance(先前,dict) and 'kind' not in 先前 else None
        事件=匹配['event']
        if 事件.get('type')!='tool/result':
            return 状态
        消息=(事件.get('data') or {}).get('message') or {}
        来源=消息.get('source') or {}
        结果={
            'kind':'tool-result',
            'seq':事件.get('seq'),
            'time':事件.get('time'),
            'callId':str(来源.get('callId')),
            'name':'' if 运行 is None else 运行.get('name') or '',
            'args':密封参数.空 if 运行 is None else 运行.get('args') or 密封参数.空,
            'call':None if 运行 is None else {'name':运行.get('name'),'argsRaw':运行.get('argsRaw')},
            'callTime':None if 运行 is None else 运行.get('time'),
            'content':消息.get('content'),
            'isError':消息.get('isError') is True,
            'meta':(事件.get('data') or {}).get('meta'),
            'subCalls':[],
        }
        if (事件.get('data') or {}).get('error') is not None:
            结果['error']=事件['data']['error']
        调用表=dict(状态.get('calls') or {})
        调用表[状态.get('rootId')]=结果
        改=dict(状态)
        改['calls']=调用表
        return 改

    def 工具视图(上下文):
        '投影根调用。没有状态时从结果匹配回放分派'
        状态=上下文.get('state')
        if 状态 is None:
            结果匹配=None
            for 匹配 in 上下文.get('matches') or []:
                if (匹配.get('event') or {}).get('type')=='tool/result':
                    结果匹配=匹配
                    break
            if 结果匹配 is None:
                return None
            事件=结果匹配['event']
            消息=(事件.get('data') or {}).get('message') or {}
            来源=消息.get('source') or {}
            根={
                'kind':'tool-result',
                'seq':事件.get('seq'),
                'time':事件.get('time'),
                'callId':str(来源.get('callId')),
                'name':'',
                'args':密封参数.空,
                'call':None,
                'callTime':None,
                'content':消息.get('content'),
                'isError':消息.get('isError') is True,
                'meta':(事件.get('data') or {}).get('meta'),
                'subCalls':[],
            }
            if (事件.get('data') or {}).get('error') is not None:
                根['error']=事件['data']['error']
            状态={'rootId':根['callId'],'calls':{根['callId']:根},'children':{},'parents':{}}
            for 匹配 in 上下文.get('matches') or []:
                状态=更新分派(状态,匹配)
        if 状态 is None:
            return None
        位置=(上下文.get('start') or {}).get('location') or {}
        打断=None
        if 位置.get('kind')=='step' and isinstance(位置.get('step'),dict) and 位置['step'].get('status')=='closed':
            打断=位置['step'].get('end')
        elif 位置.get('kind') in ('step','turn') and isinstance(位置.get('turn'),dict) and 位置['turn'].get('status')=='closed':
            打断=位置['turn'].get('end')
        根=投影调用(状态,状态.get('rootId'),打断)
        if 根 is None:
            return None
        锚点=(上下文.get('start') or {}).get('event',{}).get('seq')
        if 锚点 is None:
            锚点=根.get('seq') if 'kind' in 根 else ((上下文.get('matches') or [{}])[0].get('event') or {}).get('seq') or 0
        return 轨迹节点(上下文,锚点,{'kind':'tool','root':根})

    上下文.uiConversation.events.register({
        'kind':'trajectory-tool-call',
        'target':'trajectory',
        'match':工具匹配,
        'start':工具开始,
        'update':工具更新,
        'buildViewNode':工具视图,
    })
