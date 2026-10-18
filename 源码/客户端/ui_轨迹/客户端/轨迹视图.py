import pywebbridge
import importlib.resources as 包资源
from .布局 import 追加轨迹流式布局,派生轨迹布局#折叠
from .时间线 import 轨迹时间线焦点下标#焦点
from .轨迹记录 import 轨迹记录身份#稳定身份
from .搜索索引 import 轨迹搜索索引#全文
from .快照构建 import 空轨迹快照#空目标
from .轨迹工具栏 import 轨迹工具栏#工具栏
from .轨迹时间线 import 轨迹时间线#总览
from .轨迹表实现 import 轨迹表#账本

样式文本=包资源.files(__package__).joinpath('视图.module.css').read_text(encoding='utf-8')

空轮次=set()
空记录=set()
搜索节流毫秒=3000
历史页节点数=50

def 含调用(调用列表,调用标识):
    '根或子调用里有没有这个标识'
    for 调用 in 调用列表 or []:
        if not isinstance(调用,dict):
            continue
        if 调用.get('callId')==调用标识 or 含调用(调用.get('subCalls'),调用标识):
            return True
    return False

def 最后格下标(轮次列表):
    '布局里最大的单元格下标'
    最后=0
    for 轮次 in 轮次列表:
        for 组 in 轮次.get('groups') or []:
            for 格 in 组.get('cells') or []:
                最后=max(最后,格.get('index') or 0)
    return 最后

def 时间线块(块):
    '时间线不带正文，只留结构和调用身份'
    if not isinstance(块,dict):
        return {'kind':'other','block':None}
    种类=块.get('kind')
    if 种类=='text':
        return {'kind':'text','text':''}
    if 种类=='reasoning':
        return {'kind':'reasoning','text':''}
    if 种类=='image':
        return 块
    if 种类=='tool-call':
        return {'kind':'tool-call','callId':块.get('callId'),'name':块.get('name'),'argsRaw':''}
    return {'kind':'other','block':None}

def 请求用量(值):
    '提供方用量收成轨迹用量字段'
    if not isinstance(值,dict):
        return None
    用量={}
    if 值.get('inputTokens') is not None:
        用量['input']=值['inputTokens']
    if 值.get('cacheReadTokens') is not None:
        用量['cacheRead']=值['cacheReadTokens']
    if 值.get('cacheWriteTokens') is not None:
        用量['cacheWrite']=值['cacheWriteTokens']
    if 值.get('outputTokens') is not None:
        用量['output']=值['outputTokens']
    if 值.get('reasoningTokens') is not None:
        用量['reasoning']=值['reasoningTokens']
    if len(用量)==0 and 值.get('inputTokens') is None and 值.get('outputTokens') is None:
        return 用量 if any(键 in 值 for 键 in ('inputTokens','cacheReadTokens','cacheWriteTokens','outputTokens','reasoningTokens')) else None
    return 用量

def 加用量(合计,用量):
    '把一份请求用量加进累计'
    if 用量 is None:
        return 合计
    结果={}
    for 源,目标 in (('input','input'),('cacheRead','cacheRead'),('cacheWrite','cacheWrite'),('output','output'),('reasoning','reasoning')):
        左=None if not isinstance(合计,dict) else 合计.get(源)
        右=用量.get(源)
        if 左 is None and 右 is None:
            continue
        结果[目标]=(左 or 0)+(右 or 0)
    return 结果

class 轨迹视图:
    '消费会话 trajectory 快照，折叠成轮次账本并支持加载更早历史'
    def __init__(自身,属性):
        '记下注入面，并画出视图'
        自身.属性=属性 or {}
        自身.收起轮次=set()
        自身.收起助手=set()
        自身.时间线选区=None
        自身.实际时间=False
        自身.查询=''
        自身.索引=轨迹搜索索引()
        自身.索引修订=0
        自身.索引定时=None
        自身.索引已初始化=False
        自身.选中时间线下标=None
        自身.时间线记录选择=None
        自身.时间线记录焦点=None
        自身.历史尾序号=None
        自身.历史节点限额=历史页节点数
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染时重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出工具栏、时间线和账本'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 文档.getElementById('轨迹视图样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹视图样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        完整=属性['useTrajectory'](lambda 照:照) if callable(属性.get('useTrajectory')) else 空轨迹快照
        if not isinstance(完整,dict):
            完整=空轨迹快照
        节点列表=完整.get('eventNodes') or []
        最新序号=None if len(节点列表)==0 else 节点列表[-1].get('seq')
        if 最新序号 is not None and (自身.历史尾序号 is None or 自身._尾下标(节点列表)<0):
            自身.历史尾序号=最新序号
        固定尾=最新序号 if 自身.历史尾序号 is None else 自身.历史尾序号
        尾下标=-1 if 固定尾 is None else 自身._末个不大于(节点列表,固定尾)
        if 尾下标<0 and 最新序号 is not None:
            尾结束=len(节点列表)
        else:
            尾结束=尾下标+1
        头下标=max(0,尾结束-自身.历史节点限额)
        视图请求=属性.get('viewRequest')
        巡检=视图请求.get('focus') if isinstance(视图请求,dict) and 视图请求.get('view')=='trajectory' else None
        if 巡检 is not None:
            巡检下标=-1
            for 位,节点 in enumerate(节点列表):
                if not isinstance(节点,dict):
                    continue
                if 节点.get('kind')=='assistant':
                    for 块 in 节点.get('blocks') or []:
                        if isinstance(块,dict) and 块.get('kind')=='tool-call' and 块.get('callId')==巡检:
                            巡检下标=位
                elif 节点.get('kind')=='tool-result' and 含调用([节点],巡检):
                    巡检下标=位
            if 0<=巡检下标<头下标:
                自身.历史节点限额+=头下标-巡检下标
                头下标=max(0,尾结束-自身.历史节点限额)
        if 头下标==0:
            检视=完整
        else:
            事件节点=list(节点列表)[头下标:]
            首序号=0 if len(事件节点)==0 else 事件节点[0].get('seq') or 0
            检视=dict(完整)
            检视['eventNodes']=事件节点
            检视['requests']=[请求 for 请求 in 完整.get('requests') or [] if 请求.get('startSeq',0)>=首序号 or (请求.get('resultSeq') or -1)>=首序号]
        def 读会话(选取):
            '没有钩子时当没有会话快照'
            if not callable(属性.get('useSession')):
                return None
            return 属性['useSession'](选取)
        历史加载中=读会话(lambda 快照:isinstance(快照,dict) and 快照.get('openState')=='loading') is True
        更早加载中=读会话(lambda 快照:isinstance(快照,dict) and 快照.get('loadingOlder') is True) is True
        会话还有更早=读会话(lambda 快照:isinstance(快照,dict) and 快照.get('hasMore') is True) is True
        还有更早=头下标>0 or 会话还有更早
        流式=检视.get('partial')
        定稿轮次=派生轨迹布局({
            'nodes':检视.get('eventNodes') or [],
            'eventLocations':检视.get('eventLocations'),
            'partial':None if not isinstance(流式,dict) else {'turn':流式.get('turn'),'step':流式.get('step'),'blocks':[]},
            'runningCalls':检视.get('runningCalls') or [],
            'requests':检视.get('requests') or [],
            'systemPrompts':检视.get('systemPrompts'),
            'callSchemas':检视.get('callSchemas'),
        })
        最后=最后格下标(定稿轮次)
        if not isinstance(流式,dict):
            时间线流式=None
        else:
            时间线流式={
                'turn':流式.get('turn'),
                'step':流式.get('step'),
                'blocks':[时间线块(块) for 块 in 流式.get('blocks') or []],
            }
            if 流式.get('timing') is not None:
                时间线流式['timing']=流式['timing']
        时间线轮次=追加轨迹流式布局(定稿轮次,时间线流式,最后)
        实测=False
        if callable(属性.get('useDuration')):
            实测=属性['useDuration'](lambda 值:值) is True
        if 实测 and 自身.实际时间:
            模式='actual'
        elif 实测:
            模式='duration'
        elif 自身.实际时间:
            模式='time'
        else:
            模式='sequence'
        部分搜索=追加轨迹流式布局([],流式 if isinstance(流式,dict) else None,最后)
        搜索布局=(定稿轮次,部分搜索)
        自身._同步索引(窗口,搜索布局)
        流式格=[]
        for 轮次 in 部分搜索:
            for 组 in 轮次.get('groups') or []:
                流式格.extend(组.get('cells') or [])
        命中身份=自身.索引.搜索(自身.查询)
        if 命中身份 is None:
            命中下标=None
        else:
            命中下标=set()
            for 轮次列表 in 搜索布局:
                for 轮次 in 轮次列表:
                    for 组 in 轮次.get('groups') or []:
                        for 格 in 组.get('cells') or []:
                            if 轨迹记录身份(格) in 命中身份:
                                命中下标.add(格['index'])
        焦点=None if 自身.时间线选区 is None else 轨迹时间线焦点下标(时间线轮次,自身.时间线选区,模式)
        编号=自身._请求编号(完整)
        可折叠轮次=[]
        for 轮次 in 时间线轮次:
            if 轮次.get('turn') is None:
                continue
            数=0
            for 组 in 轮次.get('groups') or []:
                for 格 in 组.get('cells') or []:
                    if 格.get('requestOnly') is not True and 格.get('kind')!='system':
                        数+=1
            if 数>1:
                可折叠轮次.append(轮次['turn'])
        全部轮次收起=len(可折叠轮次)>0 and all(回合 in 自身.收起轮次 for 回合 in 可折叠轮次)
        可折叠助手=[]
        for 轮次 in 时间线轮次:
            格子=[]
            for 组 in 轮次.get('groups') or []:
                格子.extend(组.get('cells') or [])
            for 位,格 in enumerate(格子):
                if 格.get('kind')!='message':
                    continue
                下一=格子[位+1] if 位+1<len(格子) else None
                if 下一 is not None and 下一.get('kind') in ('tool','subtool'):
                    可折叠助手.append(轨迹记录身份(格))
        全部助手收起=len(可折叠助手)>0 and all(标识 in 自身.收起助手 for 标识 in 可折叠助手)
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('div')
        根.className='root'
        根.setAttribute('data-conversation-composer-overlay','')
        def 改实测(下一):
            '写入实测时长并清掉时间线选区'
            自身.时间线选区=None
            if callable(属性.get('setActualDuration')):
                属性['setActualDuration'](下一)
            自身.渲染()
        def 改实际时间(下一):
            '在完整时间和压缩空闲之间切换'
            自身.实际时间=下一
            自身.时间线选区=None
            自身.渲染()
        def 切换全部轮次():
            '展开或收起每一个可折叠轮次'
            if 全部轮次收起:
                for 回合 in 可折叠轮次:
                    自身.收起轮次.discard(回合)
            else:
                for 回合 in 可折叠轮次:
                    自身.收起轮次.add(回合)
            自身.渲染()
        def 切换全部助手():
            '展开或收起每一个可折叠助手'
            if 全部助手收起:
                for 标识 in 可折叠助手:
                    自身.收起助手.discard(标识)
            else:
                for 标识 in 可折叠助手:
                    自身.收起助手.add(标识)
            自身.渲染()
        def 改查询(文本):
            '更新账本搜索'
            自身.查询=文本 or ''
            自身.渲染()
        轨迹工具栏({
            'window':窗口,
            'parent':根,
            'actualDuration':实测,
            'onActualDurationChange':改实测,
            'actualTime':自身.实际时间,
            'onActualTimeChange':改实际时间,
            'allTurnsCollapsed':全部轮次收起,
            'onToggleAllTurns':切换全部轮次,
            'allAssistantsCollapsed':全部助手收起,
            'onToggleAllAssistants':切换全部助手,
            'searchQuery':自身.查询,
            'onSearchQueryChange':改查询,
        })
        def 改选区(区间):
            '时间线选区'
            自身.时间线选区=区间
            自身.渲染()
        def 选记录(下标):
            '点时间线块时清掉选区并选中记录'
            自身.时间线选区=None
            自身.时间线记录选择={'index':下标}
            自身.选中时间线下标=下标
            自身.渲染()
        def 聚焦记录(下标):
            '点空白时把最近记录滚进视口'
            自身.时间线记录焦点={'index':下标}
            自身.渲染()
        轨迹时间线({
            'window':窗口,
            'parent':根,
            'turns':时间线轮次,
            'mode':模式,
            'range':自身.时间线选区,
            'hasEarlierRecords':还有更早,
            'onLoadEarlier':lambda:自身._加载更早(头下标>0),
            'selectedIndex':自身.选中时间线下标,
            'searchMatchIndexes':命中下标,
            'onRangeChange':改选区,
            'onRecordSelect':选记录,
            'onRecordFocus':聚焦记录,
        })
        账本=文档.createElement('div')
        账本.className='ledger'
        def 选中变化(下标):
            '账本选中写回时间线'
            自身.选中时间线下标=下标
        def 记录被选(下标):
            '选中记录若不在时间线焦点里就清掉选区'
            if 焦点 is not None and 下标 not in 焦点:
                自身.时间线选区=None
        def 清选区():
            '关掉详情时清掉时间线选区'
            自身.时间线选区=None
        def 切换轮次(回合):
            '展开或收起一轮'
            if 回合 in 自身.收起轮次:
                自身.收起轮次.discard(回合)
            else:
                自身.收起轮次.add(回合)
            自身.渲染()
        def 切换助手(标识):
            '展开或收起一个助手下的调用'
            if 标识 in 自身.收起助手:
                自身.收起助手.discard(标识)
            else:
                自身.收起助手.add(标识)
            自身.渲染()
        折行=属性.get('jsonStringWrapping')
        if isinstance(折行,dict):
            折行=dict(折行)
            折行['label']='自动换行'
        轨迹表({
            'window':窗口,
            'parent':账本,
            'stringWrapping':折行,
            'renderSlot':属性.get('renderSlot'),
            'loadImage':属性.get('loadImage'),
            'requestNumbers':编号,
            'turns':时间线轮次,
            'streamingCells':流式格,
            'timelineFocusIndexes':焦点,
            'searchMatchIndexes':命中下标,
            'onSelectedIndexChange':选中变化,
            'onRecordSelect':记录被选,
            'recordSelection':自身.时间线记录选择,
            'recordFocus':自身.时间线记录焦点,
            'historyLoading':历史加载中,
            'olderHistoryLoading':更早加载中,
            'historyStartSeq':0 if len(检视.get('eventNodes') or [])==0 else (检视['eventNodes'][0].get('seq') or 0),
            'hasOlderRecords':还有更早,
            'onLoadOlder':lambda:自身._加载更早(头下标>0),
            'onClearSelection':清选区,
            'collapsedTurns':自身.收起轮次,
            'onToggleTurn':切换轮次,
            'collapsedAssistants':自身.收起助手,
            'onToggleAssistant':切换助手,
            'inspectCallId':巡检,
            'onInspectApplied':属性.get('completeViewRequest'),
        })
        根.appendChild(账本)
        自身.根=根
        自身.时间线记录选择=None
        自身.时间线记录焦点=None
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根

    def _尾下标(自身,节点列表):
        '历史尾序号在当前节点里的位置'
        return 自身._末个不大于(节点列表,自身.历史尾序号)

    def _末个不大于(自身,节点列表,序号):
        '最后一个 seq 不大于序号的下标'
        下标=-1
        for 位,节点 in enumerate(节点列表):
            if isinstance(节点,dict) and 节点.get('seq',0)<=序号:
                下标=位
        return 下标

    def _加载更早(自身,内存里还有):
        '先吃已在内存的前缀，没有再向会话要一页'
        if not 内存里还有:
            加载=自身.属性.get('loadOlder')
            if not callable(加载) or 加载() is not True:
                return False
        自身.历史节点限额+=历史页节点数
        自身.渲染()
        return True

    def _同步索引(自身,窗口,搜索布局):
        '第一次立刻索引，之后按上游间隔节流'
        if not 自身.索引已初始化:
            自身.索引已初始化=True
            if 自身.索引.更新(搜索布局):
                自身.索引修订+=1
            return
        if 自身.索引定时 is not None:
            return
        def 到点():
            '节流到点后按最新布局更新索引'
            自身.索引定时=None
            if 自身.索引.更新(搜索布局):
                自身.索引修订+=1
                自身.渲染()
        自身.索引定时=窗口.setTimeout(到点,搜索节流毫秒)

    def _请求编号(自身,完整):
        '按出现顺序给助手请求和压缩请求编号，并累计用量'
        按步助手={}
        for 节点 in 完整.get('eventNodes') or []:
            if isinstance(节点,dict) and 节点.get('kind')=='assistant' and 节点.get('step',0)>0:
                按步助手[str(节点.get('turn'))+'\u0000'+str(节点.get('step'))]=节点
        按步请求={}
        for 请求 in 完整.get('requests') or []:
            if isinstance(请求,dict) and 请求.get('purpose')=='assistant':
                按步请求[str(请求.get('turn'))+'\u0000'+str(请求.get('step'))]=请求
        有序=[]
        for 请求 in 完整.get('requests') or []:
            if not isinstance(请求,dict):
                continue
            节点=None
            if 请求.get('purpose')=='assistant':
                节点=按步助手.get(str(请求.get('turn'))+'\u0000'+str(请求.get('step')))
            有序.append({'seq':请求.get('startSeq') or 0,'request':请求,'node':节点})
        for 键,节点 in 按步助手.items():
            if 键 not in 按步请求:
                有序.append({'seq':节点.get('seq') or 0,'request':None,'node':节点})
        有序.sort(key=lambda 项:项['seq'])
        编号=[]
        累计=None
        for 位,项 in enumerate(有序):
            请求=项['request']
            节点=项['node']
            用量=请求用量(None if not isinstance(请求,dict) else 请求.get('usage'))
            if 用量 is None and isinstance(节点,dict):
                用量=请求用量(节点.get('usage'))
            累计=加用量(累计,用量)
            if not isinstance(请求,dict) or 请求.get('purpose')!='compaction':
                回合=None if not isinstance(请求,dict) else 请求.get('turn')
                步号=None if not isinstance(请求,dict) else 请求.get('step')
                if 回合 is None and isinstance(节点,dict):
                    回合=节点.get('turn')
                if 步号 is None and isinstance(节点,dict):
                    步号=节点.get('step')
                if 回合 is None or 步号 is None:
                    continue
                行={
                    'seq':项['seq'],
                    'turn':回合,
                    'step':步号,
                    'group':'第 '+str(步号)+' 步',
                    'number':位+1,
                    'status':请求.get('status') if isinstance(请求,dict) and 请求.get('status') is not None else ('error' if isinstance(节点,dict) and 节点.get('interrupted') is True else 'complete'),
                }
                if isinstance(请求,dict):
                    for 键 in ('startedAt','completedAt','error','errorCode','retry','maxRetries','retryDelayMs','requestConfig'):
                        if 请求.get(键) is not None:
                            行[键]=请求[键]
                    if 请求.get('resultSeq') is not None:
                        行['resultSeq']=请求['resultSeq']
                    提供=(请求.get('providerMetadata') or {}).get('provider') if isinstance(请求.get('providerMetadata'),dict) else None
                    模型=(请求.get('providerMetadata') or {}).get('model') if isinstance(请求.get('providerMetadata'),dict) else None
                else:
                    提供=None
                    模型=None
                if 提供 is None and isinstance(节点,dict) and isinstance(节点.get('providerMetadata'),dict):
                    提供=节点['providerMetadata'].get('provider')
                if 模型 is None and isinstance(节点,dict) and isinstance(节点.get('providerMetadata'),dict):
                    模型=节点['providerMetadata'].get('model')
                if isinstance(节点,dict) and 节点.get('requestConfig') is not None and 行.get('requestConfig') is None:
                    行['requestConfig']=节点['requestConfig']
                if isinstance(节点,dict) and 行.get('completedAt') is None and not isinstance(请求,dict):
                    行['completedAt']=节点.get('time')
                if isinstance(节点,dict) and 行.get('resultSeq') is None:
                    行['resultSeq']=节点.get('seq')
                if 提供 is not None:
                    行['provider']=提供
                if 模型 is not None:
                    行['model']=模型
                if 用量 is not None:
                    行['usage']=用量
                if 累计 is not None:
                    行['cumulativeUsage']=累计
                编号.append(行)
                continue
            行={
                'seq':请求.get('startSeq'),
                'turn':请求.get('turn'),
                'step':0,
                'group':'压缩 '+str(请求.get('startSeq')),
                'number':位+1,
                'purpose':'compaction',
                'status':请求.get('status'),
                'startedAt':请求.get('startedAt'),
                'completedAt':请求.get('completedAt'),
            }
            if 请求.get('error') is not None:
                行['error']=请求['error']
            if 请求.get('errorCode') is not None:
                行['errorCode']=请求['errorCode']
            if 请求.get('status')!='running':
                行['resultSeq']=请求.get('startSeq')
            元=请求.get('providerMetadata') if isinstance(请求.get('providerMetadata'),dict) else {}
            if 元.get('provider') is not None:
                行['provider']=元['provider']
            if 元.get('model') is not None:
                行['model']=元['model']
            if 请求.get('requestConfig') is not None:
                行['requestConfig']=请求['requestConfig']
            if 用量 is not None:
                行['usage']=用量
            if 累计 is not None:
                行['cumulativeUsage']=累计
            编号.append(行)
        return 编号
