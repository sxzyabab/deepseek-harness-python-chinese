'带无损 Assistant 流子行的增量原始会话行'

from ......客户端.存储 import 创建快照存储
from ......模型后端.llm.助手流 import 展开助手流
from .流 import 助手日志流
from .分组 import 会话日志分组

__all__=['会话日志模型']

def 事件于(条目):
    '条目上的原始事件'
    if isinstance(条目,dict):
        return 条目.get('event')
    return getattr(条目,'event',None)

def 条目种类(条目):
    'transient 或持久条目种类'
    if isinstance(条目,dict):
        return 条目.get('type')
    return getattr(条目,'type',None)

def 寻找(条目表,谓词):
    '第一个满足谓词的条目'
    for 项 in 条目表:
        if 谓词(项):
            return 项
    return None

def 寻找最后(条目表,谓词):
    '最后一个满足谓词的条目'
    下标=len(条目表)-1
    while 下标>=0:
        if 谓词(条目表[下标]):
            return 条目表[下标]
        下标-=1
    return None

class 会话日志模型:
    '会话拥有的日志投影；只有表格被观察时才订阅'
    def __init__(自身,来源):
        '来源是与 Chat、轨迹共用的会话窗口'
        自身._来源=来源
        自身._行=创建快照存储([])
        自身._记录={}
        自身._根=[]
        自身._尝试={}
        自身._分组=会话日志分组()
        自身._已结算={}
        自身._流={}
        自身._修订=-1
        自身._订阅数=0
        自身._断开=None
        自身._接受(来源.getSnapshot())

    def getSnapshot(自身):
        '稳定的表格顺序；行内容有独立来源'
        return 自身._行.getSnapshot()

    def 聊天锚(自身,键):
        '恢复事件位置，不解释已格式化的单元格'
        自身._接受(自身._来源.getSnapshot())
        根=None
        for 项 in 自身._根:
            行键=项['row']['key']
            if 行键==键 or (项['stream'] is not None and 键.startswith(f'{行键}/chunk:')):
                根=项
                break
        if 根 is None:
            return None
        来源=自身._记录.get(键)
        记录=None if 来源 is None else 来源.getSnapshot()
        if 记录 is None:
            return None
        结果={'event':事件于(根['entry'])}
        if 根['row']['key']!=键:
            结果['chunk']=记录['value']
        return 结果

    def 选取(自身,目标):
        '在已加载日志里解析选中的 Chat 对象，不制造合成记录'
        窗口=自身._来源.getSnapshot()
        自身._接受(窗口)
        条目表=窗口.entries
        def 同一步(条目):
            '同一 Turn，步缺省时不限制步'
            数据=事件于(条目).get('data') or {}
            if 目标.get('turn') is None or 'turn' not in 数据 or 数据['turn']!=目标['turn']:
                return False
            if 目标.get('step') is None:
                return True
            return 'step' in 数据 and 数据['step']==目标['step']
        调用=None
        if 目标.get('callId') is not None:
            def 是调用(条目):
                'tool/call 且 callId 相同'
                事件=事件于(条目)
                return 事件.get('type')=='tool/call' and (事件.get('data') or {}).get('callId')==目标['callId']
            调用=寻找(条目表,是调用)
        锚=None
        if 目标.get('anchorSeq') is not None:
            锚=寻找(条目表,lambda 条目:事件于(条目).get('seq')==目标['anchorSeq'])
        助手=None
        if 目标.get('nodeKind')=='assistant-step':
            def 是助手(条目):
                '同一步上的助手消息、尝试或瞬态行'
                种类=事件于(条目).get('type')
                return 同一步(条目) and (种类 in ('assistant/message','assistant/attempt') or 条目种类(条目)=='transient')
            助手=寻找最后(条目表,是助手)
        步=None
        if 目标.get('step') is not None:
            步=寻找(条目表,lambda 条目:事件于(条目).get('type')=='step/start' and 同一步(条目))
        回合=None
        if 目标.get('turn') is not None:
            def 是回合(条目):
                'turn/start 且回合号相同'
                事件=事件于(条目)
                return 事件.get('type')=='turn/start' and (事件.get('data') or {}).get('turn')==目标['turn']
            回合=寻找(条目表,是回合)
        条目=调用 or 锚 or 助手 or 步 or 回合 or 寻找(条目表,同一步)
        if 条目 is None:
            return None
        事件=事件于(条目)
        if 条目种类(条目)=='transient':
            键=f"attempt:{(事件.get('data') or {}).get('attemptId')}"
        else:
            键=自身._已结算.get(事件.get('seq'),f"event:{事件.get('seq')}")
        if 目标.get('groupPart')=='reasoning':
            for 行 in 自身._行.getSnapshot():
                if 行.get('parent')!=键:
                    continue
                来源=自身._记录.get(行['key'])
                快照=None if 来源 is None else 来源.getSnapshot()
                值=None if 快照 is None else 快照.get('value')
                if isinstance(值,dict) and 值.get('type')=='block-start' and 值.get('blockType')=='reasoning':
                    return 行['key']
        return 键

    def subscribe(自身,监听):
        '结构失效回调，返回退订函数'
        停止=自身._行.subscribe(监听)
        if 自身._订阅数==0:
            def 接到():
                '窗口发布后接受快照'
                自身._接受(自身._来源.getSnapshot())
            订=getattr(自身._来源,'subscribe',None)
            自身._断开=订(接到) if 订 is not None else 自身._来源.订阅(接到)
            自身._接受(自身._来源.getSnapshot())
        自身._订阅数+=1
        def 退订():
            '最后一个订阅者离开时断开窗口'
            停止()
            自身._订阅数-=1
            if 自身._订阅数==0 and 自身._断开 is not None:
                自身._断开()
                自身._断开=None
        return 退订

    def 行(自身,键):
        '缓存的行来源；记录还没有时起初为空'
        记录=自身._记录.get(键)
        if 记录 is None:
            记录=创建快照存储(None)
            自身._记录[键]=记录
        return 记录

    def _放入(自身,键,记录):
        '值引用变了才写入'
        自身.行(键)
        来源=自身._记录[键]
        当前=来源.getSnapshot()
        if 当前 is None or 当前.get('value') is not 记录['value']:
            来源.set(记录)

    def _接受(自身,窗口):
        '追加复用游标；其余变更重建层级'
        if 窗口.revision==自身._修订:
            return
        变更=窗口.change
        if 变更.get('kind')=='settle-assistant' and 变更.get('entry') is not None:
            父=f"attempt:{变更.get('attemptId')}"
            if 父 in 自身._尝试:
                自身._已结算[事件于(变更['entry']).get('seq')]=父
        追加=窗口.revision==自身._修订+1 and 变更.get('kind')=='append'
        if not 追加:
            自身._根.clear()
            自身._尝试.clear()
            自身._分组=会话日志分组()
        下一=list(自身._行.getSnapshot()) if 追加 else []
        条目表=变更.get('entries') if 追加 else 窗口.entries
        for 条目 in 条目表:
            自身._添加(条目,下一)
        自身._修订=窗口.revision
        if not 追加:
            自身._修剪(下一)
        自身._行.set(下一)

    def _修剪(自身,行表):
        '离开窗口的行释放记录和已结算身份'
        保留={行['key'] for 行 in 行表}
        for 序号,键 in list(自身._已结算.items()):
            if 键 not in 保留:
                del 自身._已结算[序号]
        for 键,来源 in list(自身._记录.items()):
            if 键 not in 保留:
                来源.set(None)
                del 自身._记录[键]

    def _根行(自身,键,条目,行表,流=None):
        '经分组游标放入一条根行'
        行=自身._分组.追加({'key':键,'depth':0},事件于(条目))
        根={'row':行,'entry':条目,'stream':流,'ordinal':len(自身._根),'offset':len(行表)}
        自身._根.append(根)
        行表.append(行)
        return 根

    def _添加(自身,条目,行表):
        '瞬态分片并入 attempt；持久助手展开自己的流'
        if 条目种类(条目)=='transient':
            事件=事件于(条目)
            数据=事件.get('data') or {}
            尝试标识=数据.get('attemptId')
            回合=数据.get('turn')
            步=数据.get('step')
            分片=数据.get('chunk')
            父=f'attempt:{尝试标识}'
            尝试=自身._尝试.get(父)
            if 尝试 is None:
                尝试=自身._根行(父,条目,行表,助手日志流(父))
                自身._尝试[父]=尝试
            分片数=自身._加分片(尝试,行表,事件.get('time'),分片,f'{回合}/{步}')
            自身._放入(父,{
                'type':'assistant/live','identity':尝试标识,'location':f'{回合}/{步}',
                'time':事件.get('time'),
                'value':{'attemptId':尝试标识,'turn':回合,'step':步,'chunks':分片数},
            })
            return
        事件=事件于(条目)
        键=自身._已结算.get(事件.get('seq'),f"event:{事件.get('seq')}")
        数据=事件.get('data') or {}
        if 'turn' in 数据:
            位置=f"{数据['turn']}"+(f"/{数据['step']}" if 'step' in 数据 else '')
        else:
            位置=''
        自身._放入(键,{'type':事件.get('type'),'identity':str(事件.get('seq')),'time':事件.get('time'),'location':位置,'value':事件})
        if 事件.get('type') in ('assistant/message','assistant/attempt'):
            层级=助手日志流(键)
            根=自身._根行(键,条目,行表,层级)
            流=数据.get('stream')
            编号=id(流)
            分片表=自身._流.get(编号)
            if 分片表 is None:
                分片表=展开助手流(流)
                自身._流[编号]=分片表
            for 项 in 分片表:
                自身._加分片(根,行表,项['time'],项['chunk'],位置)
        else:
            自身._根行(键,条目,行表)

    def _加分片(自身,根,行表,时间,分片,位置):
        '向对应 block 插入一行，并在闭合时替换表头'
        流=根['stream']
        加入=流.追加(分片)
        行=加入['row']
        行表.insert(根['offset']+1+加入['position'],{**行,'depth':行['depth']+根['row']['depth']})
        if 'header' in 加入:
            头=加入['header']
            行表[根['offset']+1+头['position']]={**头['row'],'depth':头['row']['depth']+根['row']['depth']}
        序号=根['ordinal']+1
        while 序号<len(自身._根):
            自身._根[序号]['offset']+=1
            序号+=1
        自身._放入(加入['key'],{'type':分片['type'],'identity':str(加入['index']),'time':时间,'location':位置,'value':分片})
        if 'collapsed' in 加入:
            折叠=加入['collapsed']
            来源=自身._记录[折叠['key']]
            先前=来源.getSnapshot()
            if 先前.get('collapsedSummary')!=折叠['summary']:
                来源.set({**先前,'collapsedSummary':折叠['summary']})
        return 流.长度
