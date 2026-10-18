from .复制代码 import 压缩中断错误#写进被打断的压缩请求

__all__=['空轨迹快照','轨迹快照构建器','轨迹视图定义','登记轨迹会话视图']

空列表=()#各空快照共用的空序列
空轨迹快照={
    'eventNodes':空列表,
    'eventLocations':{},
    'requests':空列表,
    'callSchemas':{},
    'partial':None,
    'runningCalls':空列表,
}

def 步键(回合,步号):
    'NUL 分隔回合与步'
    return str(回合)+'\u0000'+str(步号)

def 采集模式(块,按名工具,输出):
    '按工具名把调用时可见的 schema 记到 callId 上，并递归子调用'
    if not isinstance(块,dict):
        return
    if 'kind' in 块:
        调用=块.get('call')
        名称=调用.get('name') if isinstance(调用,dict) else None
    else:
        名称=块.get('name')
    模式=None if 名称 is None else 按名工具.get(名称)
    if 模式 is not None and 块.get('callId') is not None:
        输出[块['callId']]=模式
    for 孩子 in 块.get('subCalls') or []:
        采集模式(孩子,按名工具,输出)

def 工具调用焦点(调用标识):
    '轨迹焦点就是调用标识本身'
    return 调用标识

def 创建构建器():
    '每个会话目标一份新的构建器'
    return 轨迹快照构建器()

class 轨迹快照构建器:
    '带键适配器：保留旧的轨迹快照与舞台布局'
    def __init__(自身):
        '初始化节点表与贡献列表'
        自身.节点={}#键到视图节点
        自身.位置={}#键到贡献下标
        自身.贡献=[]#按锚点排好的贡献
        自身.empty=空轨迹快照#构建器缺省快照

    def replace(自身,输入):
        '整表替换后返回新快照'
        自身.节点.clear()
        for 节点 in 输入.get('nodes') or []:
            自身.节点[节点['key']]=节点
        自身.重建贡献()
        return 自身.快照()

    def apply(自身,输入):
        '按锚点是否变化决定就地替换或重排，返回新快照'
        结构变了=False
        for 节点 in 输入.get('upserts') or []:
            先前=自身.节点.get(节点['key'])
            自身.节点[节点['key']]=节点
            if 先前 is None or 先前.get('anchorSeq')!=节点.get('anchorSeq'):
                结构变了=True
                continue
            位置=自身.位置.get(节点['key'])
            if 位置 is None:
                结构变了=True
            else:
                自身.贡献[位置]=节点
        if 结构变了:
            自身.重建贡献()
        return 自身.快照()

    def 快照(自身):
        '按锚点序折叠贡献'
        按步请求头={}
        for 贡献 in 自身.贡献:
            数据=贡献.get('data') or {}
            if 数据.get('kind')!='request-header':
                continue
            头=数据.get('header') or {}
            位置=头.get('location') or {}
            if 位置.get('kind')!='step':
                continue
            回合=位置.get('turn') or {}
            步=位置.get('step') or {}
            键=步键(回合.get('turn'),步.get('step'))
            先前=按步请求头.get(键)
            条目={'latest':头}
            if 头.get('change') is not None:
                条目['change']=头['change']
            elif isinstance(先前,dict) and 先前.get('change') is not None:
                条目['change']=先前['change']
            按步请求头[键]=条目
        已代表提示=set()
        for 节点 in 自身.贡献:
            数据=节点.get('data') or {}
            if 数据.get('kind')=='request-header':
                头=数据.get('header') or {}
                if isinstance(头.get('change'),dict):
                    已代表提示.add(头['change'].get('seq'))
        系统提示=[]
        定稿=[]
        事件位置={}
        请求列表=[]
        边界=[]
        回合结束=[]
        调用模式={}
        已消费变更=set()
        上一请求头=None
        上一工具={}
        流式=None
        运行中=[]
        for 贡献 in 自身.贡献:
            数据=贡献.get('data') or {}
            种类=数据.get('kind')
            if 种类=='system-prompt':
                提示=数据.get('prompt') or {}
                if 提示.get('seq') not in 已代表提示:
                    系统提示.append(提示)
                continue
            if 种类=='request-header':
                上一请求头=数据.get('header')
                工具=上一请求头.get('prompt',{}).get('tools') if isinstance(上一请求头,dict) else []
                上一工具={}
                for 项 in 工具 or []:
                    if isinstance(项,dict) and 项.get('name') is not None:
                        上一工具[项['name']]=项
                continue
            if 种类=='node':
                节点=数据.get('node')
                if isinstance(节点,dict):
                    定稿.append(节点)
                    事件位置[节点.get('seq')]=贡献.get('location')
                continue
            if 种类=='assistant':
                请求=数据.get('request')
                头=None
                if isinstance(请求,dict):
                    精确=按步请求头.get(步键(请求.get('turn'),请求.get('step')))
                    if 精确 is not None:
                        头=精确
                    elif isinstance(上一请求头,dict) and 上一请求头.get('seq',0)<请求.get('startSeq',0):
                        头={'latest':上一请求头}
                        if 上一请求头.get('change') is not None:
                            头['change']=上一请求头['change']
                if 数据.get('node') is not None:
                    节点=数据['node']
                    提示=None if 头 is None else (头.get('latest') or {}).get('prompt')
                    if isinstance(提示,dict):
                        节点=dict(节点)
                        节点['requestConfig']=提示.get('config')
                    定稿.append(节点)
                if 数据.get('partial') is not None:
                    流式=数据['partial']
                if isinstance(请求,dict):
                    变更=None if 头 is None else 头.get('change')
                    带变更=isinstance(变更,dict) and 变更.get('seq') not in 已消费变更
                    叠=dict(请求)
                    if 头 is not None:
                        最新=头.get('latest') or {}
                        叠['prompt']=最新.get('prompt')
                        if isinstance(最新.get('prompt'),dict):
                            叠['requestConfig']=最新['prompt'].get('config')
                        if 带变更:
                            叠['promptChange']=变更
                    请求列表.append(叠)
                    if 带变更:
                        已消费变更.add(变更.get('seq'))
                continue
            if 种类=='tool':
                根=数据.get('root')
                if isinstance(根,dict):
                    if 'kind' in 根:
                        定稿.append(根)
                    else:
                        运行中.append(根)
                    if isinstance(上一请求头,dict) and 上一请求头.get('seq',0)<贡献.get('anchorSeq',0):
                        采集模式(根,上一工具,调用模式)
                continue
            if 种类=='compaction':
                if 数据.get('request') is not None:
                    请求列表.append(数据['request'])
                continue
            if 种类=='session-end':
                边界.append({'seq':数据.get('seq'),'time':数据.get('time')})
                continue
            结束={'turn':数据.get('turn'),'time':数据.get('time')}
            if 数据.get('error') is not None:
                结束['error']=数据['error']
            if 数据.get('errorCode') is not None:
                结束['errorCode']=数据['errorCode']
            回合结束.append(结束)
        请求列表.sort(key=lambda 项:项.get('startSeq') or 0)
        下一请求=0
        运行压缩=[]
        for 界 in 边界:
            while 下一请求<len(请求列表):
                请求=请求列表[下一请求]
                if 请求.get('startSeq',0)>=界.get('seq',0):
                    break
                if 请求.get('purpose')=='compaction' and 请求.get('status')=='running':
                    运行压缩.append(下一请求)
                下一请求+=1
            下标=运行压缩.pop() if len(运行压缩)>0 else None
            while 下标 is not None and 请求列表[下标].get('status')!='running':
                下标=运行压缩.pop() if len(运行压缩)>0 else None
            if 下标 is None:
                continue
            请求=请求列表[下标]
            if 请求.get('purpose')!='compaction':
                continue
            改=dict(请求)
            改['completedAt']=界.get('time')
            改['status']='error'
            改['error']=压缩中断错误
            请求列表[下标]=改
        末助手={}
        for 下标,请求 in enumerate(请求列表):
            if 请求.get('purpose')=='assistant':
                末助手[请求.get('turn')]=下标
        for 结束 in 回合结束:
            if 结束.get('error') is None:
                continue
            下标=末助手.get(结束.get('turn'))
            if 下标 is None:
                continue
            请求=请求列表[下标]
            if 请求.get('purpose')!='assistant':
                continue
            改=dict(请求)
            if 改.get('completedAt') is None:
                改['completedAt']=结束.get('time')
            改['status']='error'
            改['error']=结束['error']
            if 结束.get('errorCode') is not None:
                改['errorCode']=结束['errorCode']
            请求列表[下标]=改
        定稿.sort(key=lambda 项:项.get('seq') or 0)
        快照={
            'eventNodes':定稿,
            'eventLocations':事件位置,
            'requests':请求列表,
            'callSchemas':调用模式,
            'partial':流式,
            'runningCalls':运行中,
        }
        if len(系统提示)>0:
            快照['systemPrompts']=系统提示
        return 快照

    def 重建贡献(自身):
        '锚点优先，同锚点按 key'
        自身.贡献=sorted(自身.节点.values(),key=lambda 项:(项.get('anchorSeq') or 0,str(项.get('key') or '')))
        自身.位置.clear()
        for 下标,贡献 in enumerate(自身.贡献):
            自身.位置[贡献['key']]=下标

轨迹视图定义={
    'target':'trajectory',
    'toolCallFocus':工具调用焦点,
    'create':创建构建器,
}

def 登记轨迹会话视图(上下文):
    '登记舞台向的轨迹目标构建器'
    上下文.uiConversation.views.register(轨迹视图定义)
