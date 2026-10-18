from .轨迹节点 import 轨迹节点#目标信封

__all__=['登记轨迹压缩定义']

def 登记轨迹压缩定义(上下文):
    '登记轨迹压缩请求和会话边界'
    def 检查点标识(事件):
        '用户消息里的压缩检查点'
        if 事件.get('type')!='user/message':
            return None
        来源=(事件.get('data') or {}).get('source')
        if not isinstance(来源,dict):
            return None
        if 来源.get('kind')=='compact-checkpoint' and isinstance(来源.get('compactionId'),str) and 来源['compactionId']!='':
            return 来源['compactionId']
        return None

    def 压缩匹配(事件):
        '压缩开始、摘要、结束，以及对应检查点'
        类型=事件.get('type')
        if 类型 in ('compaction/start','compaction/summary','compaction/end'):
            值=(事件.get('data') or {}).get('compactionId')
            if isinstance(值,str) and 值!='':
                return {'id':值,'role':'start' if 类型=='compaction/start' else 'update'}
        检查点=检查点标识(事件)
        if 检查点 is None:
            return None
        return {'id':检查点,'role':'update'}

    def 压缩开始(_上下文,匹配,_读取器=None):
        '必须从 compaction/start 开'
        if 匹配['event'].get('type')!='compaction/start':
            raise Exception('trajectory-compaction start requires compaction/start')
        return {'start':匹配}

    def 压缩更新(上下文,匹配):
        '摘要、结束或检查点写进同一条状态'
        类型=匹配['event'].get('type')
        改=dict(上下文.get('state') or {})
        if 类型=='compaction/summary':
            改['summary']=匹配
            return 改
        if 类型=='compaction/end':
            改['end']=匹配
            return 改
        if 检查点标识(匹配['event']) is None:
            return 上下文.get('state')
        改['checkpoint']=匹配
        return 改

    def 压缩视图(上下文):
        '收成一条压缩请求'
        状态=上下文.get('state')
        if not isinstance(状态,dict):
            return None
        开始事件=(状态.get('start') or {}).get('event') or {}
        if 开始事件.get('type')!='compaction/start':
            return None
        摘要事件=(状态.get('summary') or {}).get('event') or {}
        结束事件=(状态.get('end') or {}).get('event') or {}
        检查点事件=(状态.get('checkpoint') or {}).get('event') or {}
        开始数据=开始事件.get('data') or {}
        请求={
            'purpose':'compaction',
            'startSeq':开始事件.get('seq'),
            'turn':开始数据.get('turn'),
            'step':0,
            'startedAt':开始事件.get('time'),
            'completedAt':结束事件.get('time') if 结束事件.get('type')=='compaction/end' else None,
            'status':'running' if 结束事件.get('type')!='compaction/end' else ('complete' if (结束事件.get('data') or {}).get('error') is None else 'error'),
        }
        if 结束事件.get('type')=='compaction/end' and (结束事件.get('data') or {}).get('error') is not None:
            请求['error']=结束事件['data']['error']
        if 摘要事件.get('type')=='compaction/summary':
            数据=摘要事件.get('data') or {}
            请求['resultSeq']=摘要事件.get('seq')
            请求['summary']=数据.get('summary')
            if 数据.get('rawOutput') is not None:
                请求['rawOutput']=数据['rawOutput']
            请求['providerMetadata']={'provider':数据.get('provider'),'model':数据.get('model')}
            配置={'provider':数据.get('provider'),'model':数据.get('model'),'purpose':'compaction'}
            if 数据.get('maxTokens') is not None:
                配置['maxTokens']=数据['maxTokens']
            请求['requestConfig']=配置
            if 数据.get('usage') is not None:
                请求['usage']=数据['usage']
        if 检查点事件.get('type')=='user/message':
            请求['replacementSeq']=检查点事件.get('seq')
        return 轨迹节点(上下文,请求['startSeq'],{'kind':'compaction','request':请求})

    def 会话结束匹配(事件):
        '会话结束种子各开一条'
        if 事件.get('type')=='session/end-seed':
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 会话结束开始(_上下文,匹配,_读取器=None):
        '记下序号和时间'
        return {'seq':匹配['event'].get('seq'),'time':匹配['event'].get('time')}

    def 会话结束更新(上下文,_匹配=None):
        '更新不改状态'
        return 上下文.get('state')

    def 会话结束视图(上下文):
        '有状态才贡献会话结束'
        状态=上下文.get('state')
        if 状态 is None:
            return None
        return 轨迹节点(上下文,状态.get('seq'),{'kind':'session-end','seq':状态.get('seq'),'time':状态.get('time')})

    上下文.uiConversation.events.register({
        'kind':'trajectory-compaction',
        'target':'trajectory',
        'match':压缩匹配,
        'start':压缩开始,
        'update':压缩更新,
        'buildViewNode':压缩视图,
    })
    上下文.uiConversation.events.register({
        'kind':'trajectory-session-end',
        'target':'trajectory',
        'match':会话结束匹配,
        'start':会话结束开始,
        'update':会话结束更新,
        'buildViewNode':会话结束视图,
    })
