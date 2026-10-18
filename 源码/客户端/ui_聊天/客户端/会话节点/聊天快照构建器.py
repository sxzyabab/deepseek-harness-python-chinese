from ..约定.聊天可见性 import 是可见聊天节点
from ..约定.聊天节点 import 是运行中工具
from ..约定.组树 import 在该层或更外
from .事件投影 import 会话召回标签,技能调用名
from .回合导航 import 回合导航项,回合导航项相同
from .回合过程呈现 import 聊天回合过程投影
from .节点工厂 import 位置坐标
from .组树段 import 组树段

__all__=['有序可见聊天节点','技能名投影','聊天快照构建器','聊天视图定义','登记聊天会话视图']

空键=[]
空回合=[]
空项=[]
空列表=[]
文档位置在后=4


def 通知订阅(监听集合,标签):
    '一个回调失败不挡住其余'
    for 监听 in list(监听集合):
        try:
            监听()
        except Exception as 错误:
            print(标签+' subscriber failed:',错误)


def 引用相同(左,右):
    '长度和每一项身份都一样'
    if len(左)!=len(右):
        return False
    下标=0
    for 值 in 左:
        if 值 is not 右[下标]:
            return False
        下标+=1
    return True


def 缓存源(表,键,创建):
    '同一个键始终是同一份源'
    if 键 not in 表:
        表[键]=创建()
    return 表[键]


def 斜杠序号(项):
    '技能索引按锚序号排'
    return 项.get('seq') or 0


def 贡献锚(项):
    '旧切片按锚排'
    if isinstance(项,dict):
        return 项.get('anchorSeq') or 0
    return 0


def 消息序号(项):
    '定稿节点按序号排'
    if isinstance(项,dict):
        return 项.get('seq') or 0
    return 0


def 锚序号(节点):
    '排序用的锚'
    序号=节点.get('anchorSeq') if isinstance(节点,dict) else 0
    if isinstance(序号,bool) or not isinstance(序号,(int,float)):
        return 0
    return 序号


class 可变聊天源:
    '分键源。getSnapshot 读当前值，publish 在身份变了时通知'
    def __init__(自身,读取,标签):
        '记下读取函数和诊断标签'
        自身.读取=读取
        自身.标签=标签
        自身.监听=set()
        自身.已发布=读取()

    def getSnapshot(自身):
        '当前值'
        return 自身.读取()

    def subscribe(自身,监听):
        '订阅发布。返回退订'
        自身.监听.add(监听)

        def 退订():
            '拆掉这一份监听'
            自身.监听.discard(监听)

        return 退订

    def publish(自身):
        '值的身份变了才通知'
        下一=自身.getSnapshot()
        if 自身.已发布 is 下一:
            return
        自身.已发布=下一
        通知订阅(自身.监听,自身.标签)


class 回合种类节点:
    '按写入建索引。有人读的时候才排出顺序'
    def __init__(自身):
        '空集合'
        自身.节点={}
        自身.当前=空列表
        自身.脏=False
        自身.可观察=None

    def source(自身):
        '这一类节点数据的可观察源'
        if 自身.可观察 is None:
            自身.可观察=可变聊天源(自身.读,'[ui-chat] turn kind nodes')
        return 自身.可观察

    def set(自身,节点):
        '写入或替换。数据和锚都没变就不标脏'
        先前=自身.节点.get(节点.get('key'))
        自身.节点[节点.get('key')]=节点
        if 先前 is not None and 先前.get('data') is 节点.get('data') and 先前.get('anchorSeq')==节点.get('anchorSeq'):
            return
        自身.脏=True

    def delete(自身,键):
        '拿掉这个键'
        if 键 in 自身.节点:
            del 自身.节点[键]
        自身.脏=True

    def publish(自身):
        '有源才发布'
        if 自身.可观察 is not None:
            自身.可观察.publish()

    def 读(自身):
        '脏了就按锚重排，交出数据列表'
        if 自身.脏:
            列=list(自身.节点.values())
            列.sort(key=锚序号)
            自身.当前=[项.get('data') for 项 in 列]
            自身.脏=False
        return 自身.当前


class 可变节点存储:
    '聊天节点仓库。分键源、贴底、回合种类和过程呈现都从这里发布'
    def __init__(自身):
        '空仓库。贴底按 exchange 分段'
        自身.按键={}
        自身.过程=聊天回合过程投影()
        自身.源={}
        自身.过程源={}
        自身.底源={}
        自身.交换=组树段('exchange')
        自身.脏键=set()
        自身.脏底=set()
        自身.脏过程=set()
        自身.回合种类={}
        自身.脏种类=set()
        自身.值缓存=空列表
        自身.值脏=False

    def get(自身,键):
        '按稳定键取节点'
        return 自身.按键.get(键)

    def source(自身,键):
        '这个键的节点源'
        def 创建():
            '读这个键的当前节点'
            def 读():
                '当前节点'
                return 自身.get(键)
            return 可变聊天源(读,'[ui-chat] node source '+str(键))
        return 缓存源(自身.源,键,创建)

    def bottomSource(自身,键):
        '这个键是否落在最新交换里'
        def 创建():
            '读贴底'
            def 读():
                '可见且回合在最新段'
                节点=自身.get(键)
                if not isinstance(节点,dict) or not 是可见聊天节点(节点):
                    return False
                return 自身.交换.在最新段(位置坐标(节点.get('location')).get('turn'))
            return 可变聊天源(读,'[ui-chat] node bottom source '+str(键))
        return 缓存源(自身.底源,键,创建)

    def settleBottom(自身,回合序,位置):
        '结算最新交换，进出的回合上的节点标成贴底脏'
        for 回合 in 自身.交换.结算(回合序 or []):
            for 键 in 位置.getTurn(回合):
                自身.脏底.add(键)

    def turnDataSource(自身,回合,种类):
        '这一回合、这一类节点数据的可观察源。计划尾用它取 submitted-plan'
        return 自身.回合种类表(回合,种类).source()

    def 回合种类表(自身,回合,种类):
        '懒建这一回合的种类表'
        种类表=缓存源(自身.回合种类,回合,dict)
        return 缓存源(种类表,种类,回合种类节点)

    def 更新回合种类(自身,先前,其后):
        '节点换回合或换种类时挪集合'
        之前=None if 先前 is None else 位置坐标(先前.get('location')).get('turn')
        之后=None if 其后 is None else 位置坐标(其后.get('location')).get('turn')
        if 先前 is not None and 之前 is not None and (之前!=之后 or 先前.get('kind')!=(其后.get('kind') if 其后 is not None else None)):
            集合=自身.回合种类表(之前,先前.get('kind'))
            集合.delete(先前.get('key'))
            自身.脏种类.add(集合)
        if 其后 is not None and 之后 is not None:
            集合=自身.回合种类表(之后,其后.get('kind'))
            集合.set(其后)
            自身.脏种类.add(集合)

    def processSource(自身,键):
        '这个键所属回合的过程呈现源'
        def 创建():
            '读过程呈现'
            def 读():
                '当前呈现'
                return 自身.process(键)
            return 可变聊天源(读,'[ui-chat] node process source '+str(键))
        return 缓存源(自身.过程源,键,创建)

    def process(自身,键):
        '这个节点所属回合的过程呈现'
        return 自身.过程.get(自身.get(键))

    def values(自身):
        '当前全部节点'
        if 自身.值脏:
            自身.值缓存=list(自身.按键.values())
            自身.值脏=False
        return 自身.值缓存

    def replace(自身,节点表):
        '整表替换，并跟踪贴底分段和回合种类'
        先前=dict(自身.按键)
        自身.按键={}
        for 节点 in 节点表 or []:
            if not isinstance(节点,dict):
                continue
            键=节点.get('key')
            自身.按键[键]=节点
            if 先前.get(键) is not 节点:
                自身.更新回合种类(先前.get(键),节点)
                自身.交换.跟踪(先前.get(键),节点)
                自身.脏键.add(键)
                自身.脏过程.add(键)
            if 键 in 先前:
                del 先前[键]
        for 键,旧 in 先前.items():
            自身.更新回合种类(旧,None)
            自身.交换.跟踪(旧,None)
            自身.脏键.add(键)
            自身.脏过程.add(键)
        自身.值缓存=list(自身.按键.values())
        自身.值脏=False

    def upsert(自身,节点表):
        '按键盖上。身份没变就跳过'
        变了=False
        for 节点 in 节点表 or []:
            if not isinstance(节点,dict):
                continue
            键=节点.get('key')
            if 自身.按键.get(键) is 节点:
                continue
            自身.更新回合种类(自身.按键.get(键),节点)
            自身.交换.跟踪(自身.按键.get(键),节点)
            自身.按键[键]=节点
            自身.脏键.add(键)
            自身.脏过程.add(键)
            变了=True
        if 变了:
            自身.值脏=True

    def touchProcesses(自身,回合集,位置):
        '这些回合上的节点过程源要发布'
        for 回合 in 回合集:
            for 键 in 位置.getTurn(回合):
                自身.脏过程.add(键)

    def replaceProcesses(自身,顺序,位置):
        '整表重算过程呈现'
        自身.touchProcesses(自身.过程.replace(顺序,位置,自身),位置)

    def updateProcesses(自身,回合集,位置):
        '只重算给出的回合'
        自身.touchProcesses(自身.过程.update(回合集,位置,自身),位置)

    def publish(自身):
        '把脏键、贴底、过程和回合种类发出去'
        脏=list(自身.脏键)
        脏底=set(自身.脏底)
        脏底.update(脏)
        脏过程=list(自身.脏过程)
        脏种类=list(自身.脏种类)
        自身.脏键.clear()
        自身.脏底.clear()
        自身.脏过程.clear()
        自身.脏种类.clear()
        for 键 in 脏:
            源=自身.源.get(键)
            if 源 is not None:
                源.publish()
        for 键 in 脏底:
            源=自身.底源.get(键)
            if 源 is not None:
                源.publish()
        for 键 in 脏过程:
            源=自身.过程源.get(键)
            if 源 is not None:
                源.publish()
        for 集合 in 脏种类:
            集合.publish()


def 步骤键(回合,步):
    '回合和步骤合成索引键'
    return str(回合)+':'+str(步)


def 更新索引(先前,下一可变):
    '成员列表没变就留着旧引用'
    下一={}
    键集=set(先前.keys())
    键集.update(下一可变.keys())
    for 键 in 键集:
        之前=先前.get(键,空键)
        候选=下一可变.get(键,空键)
        值=之前 if 引用相同(之前,候选) else 候选
        if len(候选)>0:
            下一[键]=值
    return 下一


class 位置索引:
    '可见顺序上的回合、步骤和前后位置'
    def __init__(自身):
        '空索引'
        自身.回合={}
        自身.步骤={}
        自身.位置={}

    def getTurn(自身,回合):
        '这个回合的节点键'
        return 自身.回合.get(回合,空键)

    def getStep(自身,回合,步):
        '这一步的节点键'
        return 自身.步骤.get(步骤键(回合,步),空键)

    def getPosition(自身,键):
        '分组用的前后键和回合'
        return 自身.位置.get(键)

    def rebuild(自身,顺序,存储):
        '按当前顺序重建。返回位置变了的回合'
        回合表={}
        步骤表={}
        位置表={}
        变了=set()
        下标=0
        for 键 in 顺序:
            节点=存储.get(键)
            位置节点=节点.get('location') if isinstance(节点,dict) else None
            if not isinstance(位置节点,dict):
                下标+=1
                continue
            坐标=位置坐标(位置节点)
            先前=自身.位置.get(键)
            前=顺序[下标-1] if 下标>0 else None
            后=顺序[下标+1] if 下标+1<len(顺序) else None
            位置={'turn':坐标.get('turn'),'previous':前,'next':后}
            未变=先前 is not None and 先前.get('turn')==位置['turn'] and 先前.get('previous')==前 and 先前.get('next')==后
            位置表[键]=先前 if 未变 else 位置
            if not 未变:
                if 先前 is not None and 先前.get('turn') is not None:
                    变了.add(先前.get('turn'))
                if 位置['turn'] is not None:
                    变了.add(位置['turn'])
            if 坐标.get('turn') is not None:
                回合键=回合表.get(坐标['turn'])
                if 回合键 is None:
                    回合键=[]
                    回合表[坐标['turn']]=回合键
                回合键.append(键)
                if 坐标.get('step') is not None:
                    步键=步骤键(坐标['turn'],坐标['step'])
                    步列=步骤表.get(步键)
                    if 步列 is None:
                        步列=[]
                        步骤表[步键]=步列
                    步列.append(键)
            下标+=1
        for 键,位置 in 自身.位置.items():
            if 键 not in 位置表 and 位置.get('turn') is not None:
                变了.add(位置.get('turn'))
        自身.位置=位置表
        自身.回合=更新索引(自身.回合,回合表)
        自身.步骤=更新索引(自身.步骤,步骤表)
        return list(变了)

    def touch(自身,节点表):
        '内容变了但没挪位置时，换一份列表身份让聚合读者失效'
        回合集=set()
        步骤集=set()
        for 节点 in 节点表:
            if not isinstance(节点,dict):
                continue
            坐标=位置坐标(节点.get('location'))
            回合=坐标.get('turn')
            if 回合 is None:
                continue
            键列=自身.回合.get(回合)
            if 键列 is None or 节点.get('key') not in 键列:
                continue
            回合集.add(回合)
            if 坐标.get('step') is not None:
                步骤集.add(步骤键(回合,坐标['step']))
        for 回合 in 回合集:
            键列=自身.回合.get(回合)
            if 键列 is not None:
                自身.回合[回合]=list(键列)
        for 步 in 步骤集:
            键列=自身.步骤.get(步)
            if 键列 is not None:
                自身.步骤[步]=list(键列)


class 导航索引:
    '已加载回合的轨道。内容没变就留着旧项'
    def __init__(自身):
        '空轨道'
        自身.当前=空项
        自身.按回合={}

    def items(自身):
        '当前轨道项'
        return 自身.当前

    def rebuild(自身,时间线,位置,节点):
        '结构动了才整表重导'
        下一=[]
        按回合={}
        顺序=时间线.get('turnOrder') if isinstance(时间线,dict) else []
        for 回合 in 顺序 or []:
            导出=回合导航项(回合,位置,节点)
            if 导出 is None:
                continue
            先前=自身.按回合.get(回合)
            项=先前 if 先前 is not None and 回合导航项相同(先前,导出) else 导出
            下一.append(项)
            按回合[回合]=项
        自身.按回合=按回合
        未变=len(下一)==len(自身.当前)
        if 未变:
            下标=0
            for 项 in 下一:
                if 项 is not 自身.当前[下标]:
                    未变=False
                    break
                下标+=1
        if not 未变:
            自身.当前=下一

    def touch(自身,回合集,位置,节点):
        '只重导内容变了的回合'
        if len(回合集)==0:
            return
        下一=[]
        变了=False
        下标=0
        for 项 in 自身.当前:
            if 项.get('turn') not in 回合集:
                下一.append(项)
            else:
                导出=回合导航项(项.get('turn'),位置,节点)
                if 导出 is None or 回合导航项相同(项,导出):
                    下一.append(项)
                else:
                    自身.按回合[项.get('turn')]=导出
                    下一.append(导出)
            if 下一[-1] is not 自身.当前[下标]:
                变了=True
            下标+=1
        if 变了:
            自身.当前=下一


def 回合状态(位置):
    '回合或步骤位置上的回合状态'
    if isinstance(位置,dict) and 位置.get('kind') in ('turn','step'):
        回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        return 回合.get('status')
    return None


def 过程输入变了(先前,其后,结构):
    '结构、回合状态、过程数据或回答步变了就要重算呈现'
    if 结构 or 先前 is None:
        return True
    if 回合状态(先前.get('location'))!=回合状态(其后.get('location')):
        return True
    if 先前.get('kind')=='turn-process' and 其后.get('kind')=='turn-process':
        return 先前.get('data') is not 其后.get('data')
    return (
        先前.get('kind')=='assistant-step'
        and 其后.get('kind')=='assistant-step'
        and isinstance(先前.get('data'),dict)
        and isinstance(其后.get('data'),dict)
        and 先前['data'].get('step')!=其后['data'].get('step')
    )


def 回合过程呈现表(节点表):
    '可见节点上的控制锚和最早过程锚'
    呈现={}
    for 节点 in 节点表:
        if isinstance(节点,dict) and 节点.get('kind')=='turn-process' and isinstance(节点.get('data'),dict):
            回合=节点['data'].get('turn')
            当前=dict(呈现.get(回合) or {})
            当前['control']=节点
            呈现[回合]=当前
    for 节点 in 节点表:
        if not isinstance(节点,dict):
            continue
        位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}
        if 位置.get('kind') not in ('turn','step'):
            continue
        回合体=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
        回合=回合体.get('turn')
        当前=dict(呈现.get(回合) or {})
        控制=当前.get('control')
        控制锚=控制['data'].get('controlAnchorSeq') if isinstance(控制,dict) and isinstance(控制.get('data'),dict) else None
        起点=回合体.get('start') if isinstance(回合体.get('start'),dict) else None
        if 在该层或更外(节点,'input') and 控制锚 is not None and (控制锚==(起点.get('seq') if isinstance(起点,dict) else None) or 锚序号(节点)<控制锚):
            已有=当前.get('openingInputAnchor')
            当前['openingInputAnchor']=锚序号(节点) if 已有 is None else max(已有,锚序号(节点))
            呈现[回合]=当前
            continue
        if 在该层或更外(节点,'turn'):
            continue
        已有=当前.get('earliestProcessAnchor')
        当前['earliestProcessAnchor']=锚序号(节点) if 已有 is None else min(已有,锚序号(节点))
        呈现[回合]=当前
    return 呈现


def 呈现位置(节点,呈现表):
    '开口输入在前，过程控制夹在中间，其余保持原锚'
    位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}
    if 位置.get('kind') not in ('turn','step'):
        return {'anchor':锚序号(节点),'rank':0,'originalAnchor':锚序号(节点)}
    回合体=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
    呈现=呈现表.get(回合体.get('turn'))
    if 呈现 is None:
        return {'anchor':锚序号(节点),'rank':0,'originalAnchor':锚序号(节点)}
    开口=呈现.get('openingInputAnchor')
    if 开口 is not None and 锚序号(节点)<开口 and not 在该层或更外(节点,'turn'):
        return {'anchor':开口,'rank':2,'originalAnchor':锚序号(节点)}
    控制=呈现.get('control')
    if isinstance(控制,dict) and 节点.get('key')==控制.get('key'):
        if 开口 is None:
            最早=呈现.get('earliestProcessAnchor')
            return {'anchor':最早 if 最早 is not None else 锚序号(节点),'rank':-1,'originalAnchor':锚序号(节点)}
        return {'anchor':开口,'rank':1,'originalAnchor':锚序号(节点)}
    return {'anchor':锚序号(节点),'rank':0,'originalAnchor':锚序号(节点)}


def 有序可见聊天节点(节点表):
    '可见节点按呈现锚排序。开口输入在过程候选前面，合成控制夹在中间'
    可见=[节点 for 节点 in 节点表 if isinstance(节点,dict) and 是可见聊天节点(节点)]
    呈现=回合过程呈现表(可见)

    def 键(节点):
        '锚、秩、原锚、键'
        位=呈现位置(节点,呈现)
        return (位['anchor'],位['rank'],位['originalAnchor'],节点.get('key') or '')

    可见.sort(key=键)
    return 可见


def 引用消息序号(节点):
    '用户或插话消息的序号'
    if isinstance(节点,dict) and 节点.get('kind') in ('user','steering') and isinstance(节点.get('data'),dict):
        return 节点['data'].get('seq')
    return None


def 随后召回(节点):
    '紧跟在消息后面的召回上下文'
    if not isinstance(节点,dict) or 节点.get('kind')!='context' or not isinstance(节点.get('data'),dict):
        return None
    return {'messageSeq':节点['data'].get('seq',0)-1,'labels':会话召回标签(节点['data'].get('source'))}


def 带引用标签(节点,标签):
    '把召回标签写到直接消息上。空标签就拿掉字段'
    if not isinstance(节点,dict) or 节点.get('kind') not in ('user','steering'):
        return 节点
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    当前=数据.get('referenceLabels') if 'referenceLabels' in 数据 else 空键
    有标签='referenceLabels' in 数据
    if 引用相同(当前 if isinstance(当前,list) else [],标签) and 有标签==(len(标签)>0):
        return 节点
    新数据=dict(数据)
    if len(标签)==0:
        if 'referenceLabels' in 新数据:
            del 新数据['referenceLabels']
    else:
        新数据['referenceLabels']=标签
    新节点=dict(节点)
    新节点['data']=新数据
    return 新节点


class 引用标签投影:
    '把紧跟着的召回标签贴到前一条直接消息上'
    def __init__(自身):
        '空索引'
        自身.序号到键={}
        自身.序号到标签={}

    def replace(自身,节点表):
        '整表重建'
        自身.序号到键={}
        自身.序号到标签={}
        for 节点 in 节点表:
            序号=引用消息序号(节点)
            if 序号 is not None:
                自身.序号到键[序号]=节点.get('key')
            召回=随后召回(节点)
            if 召回 is not None and len(召回['labels'])>0:
                自身.序号到标签[召回['messageSeq']]=召回['labels']
        结果=[]
        for 节点 in 节点表:
            序号=引用消息序号(节点)
            if 序号 is None:
                结果.append(节点)
            else:
                结果.append(带引用标签(节点,自身.序号到标签.get(序号,空键)))
        return 结果

    def apply(自身,更新,存储):
        '只重贴受影响的消息'
        按键={}
        for 节点 in 更新:
            if isinstance(节点,dict):
                按键[节点.get('key')]=节点
        受影响=set()
        for 节点 in 更新:
            序号=引用消息序号(节点)
            if 序号 is not None:
                自身.序号到键[序号]=节点.get('key')
                受影响.add(序号)
            召回=随后召回(节点)
            if 召回 is None:
                continue
            当前=自身.序号到标签.get(召回['messageSeq'])
            if len(召回['labels'])==0:
                if 召回['messageSeq'] in 自身.序号到标签:
                    del 自身.序号到标签[召回['messageSeq']]
            else:
                if 当前 is not None and 引用相同(当前,召回['labels']):
                    自身.序号到标签[召回['messageSeq']]=当前
                else:
                    自身.序号到标签[召回['messageSeq']]=召回['labels']
            受影响.add(召回['messageSeq'])
        for 序号 in 受影响:
            键=自身.序号到键.get(序号)
            if 键 is None:
                continue
            节点=按键.get(键)
            if 节点 is None:
                节点=存储.get(键)
            if 节点 is None:
                continue
            按键[键]=带引用标签(节点,自身.序号到标签.get(序号,空键))
        return list(按键.values())


def 带技能名(节点,名称表):
    '把这一批技能名写到直接消息上'
    if not isinstance(节点,dict) or 节点.get('kind') not in ('user','steering'):
        return 节点
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    当前=数据.get('skillNames') if 'skillNames' in 数据 else 空键
    有名='skillNames' in 数据
    if 引用相同(当前 if isinstance(当前,list) else [],名称表) and 有名==(len(名称表)>0):
        return 节点
    新数据=dict(数据)
    if len(名称表)==0:
        if 'skillNames' in 新数据:
            del 新数据['skillNames']
    else:
        新数据['skillNames']=名称表
    新节点=dict(节点)
    新节点['data']=新数据
    return 新节点


def 斜杠条目(节点):
    '直接消息、技能注入，或其他种类构成的边界。不注入技能的上下文是透明的'
    if not isinstance(节点,dict):
        return None
    if 节点.get('kind') in ('user','steering'):
        return {'key':节点.get('key'),'seq':锚序号(节点),'kind':'message','name':None}
    if 节点.get('kind')=='context':
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        名=技能调用名(数据.get('source'))
        if 名 is None:
            return None
        return {'key':节点.get('key'),'seq':锚序号(节点),'kind':'skill','name':名}
    return {'key':节点.get('key'),'seq':锚序号(节点),'kind':'boundary','name':None}


def 斜杠相同(左,右):
    '序号、种类和技能名一样'
    return 左.get('seq')==右.get('seq') and 左.get('kind')==右.get('kind') and 左.get('name')==右.get('name')


class 技能名投影:
    '把同一步里加载的技能名贴到该批直接消息上。边界关掉一批，不跨回合'
    def __init__(自身):
        '空索引'
        自身.条目={}
        自身.有序=[]

    def replace(自身,节点表):
        '整表重建索引并贴名'
        自身.条目={}
        自身.有序=[]
        for 节点 in 节点表:
            条目=斜杠条目(节点)
            if 条目 is None:
                continue
            自身.条目[条目['key']]=条目
            自身.有序.append(条目)
        自身.有序.sort(key=斜杠序号)
        名称={}
        下标=0
        while 下标<len(自身.有序):
            if 自身.有序[下标].get('kind')=='boundary':
                下标+=1
                continue
            结束=自身.跑结束(下标)
            自身.分配跑(下标,结束,名称)
            下标=结束+1
        return [带技能名(节点,名称.get(节点.get('key'),空键)) for 节点 in 节点表]

    def apply(自身,更新,存储):
        '只重读分类变了的那几批'
        脏=[]
        for 节点 in 更新:
            if not isinstance(节点,dict):
                continue
            下一=斜杠条目(节点)
            先前=自身.条目.get(节点.get('key'))
            if 先前 is not None:
                if 下一 is not None and 斜杠相同(先前,下一):
                    if 下一.get('kind')=='message':
                        脏.append(下一.get('seq'))
                    continue
                自身.移除(先前)
                脏.append(先前.get('seq'))
            if 下一 is None:
                continue
            自身.插入(下一)
            脏.append(下一.get('seq'))
        if len(脏)==0:
            return 更新
        名称={}
        for 序号 in 脏:
            自身.收集周围(序号,名称)
        按键={}
        for 节点 in 更新:
            if isinstance(节点,dict):
                按键[节点.get('key')]=节点
        for 键,名单 in 名称.items():
            节点=按键.get(键)
            if 节点 is None:
                节点=存储.get(键)
            if 节点 is None:
                continue
            下一=带技能名(节点,名单)
            if 下一 is not 节点 or 键 in 按键:
                按键[键]=下一
        return list(按键.values())

    def 插入(自身,条目):
        '按序号插进有序表'
        自身.有序.insert(自身.下界(条目.get('seq')),条目)
        自身.条目[条目['key']]=条目

    def 移除(自身,条目):
        '从有序表拿掉'
        if 条目 in 自身.有序:
            自身.有序.remove(条目)
        if 条目.get('key') in 自身.条目:
            del 自身.条目[条目['key']]

    def 下界(自身,序号):
        '第一个序号不小于给定数的下标'
        低=0
        高=len(自身.有序)
        while 低<高:
            中=(低+高)//2
            现=自身.有序[中].get('seq')
            if 现 is None:
                现=float('inf')
            if 现<序号:
                低=中+1
            else:
                高=中
        return 低

    def 跑结束(自身,下标):
        '不含边界的这一跑的最后下标'
        结束=下标
        while 结束+1<len(自身.有序) and 自身.有序[结束+1].get('kind')!='boundary':
            结束+=1
        return 结束

    def 跑开始(自身,下标):
        '不含边界的这一跑的第一下标'
        开始=下标
        while 开始-1>=0 and 自身.有序[开始-1].get('kind')!='boundary':
            开始-=1
        return 开始

    def 分配跑(自身,开始,结束,名称):
        '这一跑里的技能名贴到每条直接消息'
        名单=[]
        下标=开始
        while 下标<=结束:
            条目=自身.有序[下标]
            if 条目.get('kind')=='skill' and 条目.get('name') is not None and 条目.get('name') not in 名单:
                名单.append(条目.get('name'))
            下标+=1
        下标=开始
        while 下标<=结束:
            条目=自身.有序[下标]
            if 条目.get('kind')=='message':
                名称[条目.get('key')]=名单
            下标+=1

    def 收集周围(自身,序号,名称):
        '重读这个序号两侧、不被边界切开的跑'
        处=自身.下界(序号)
        这里=自身.有序[处] if 处<len(自身.有序) else None
        if 这里 is not None and 这里.get('seq')==序号 and 这里.get('kind')!='boundary':
            自身.分配跑(自身.跑开始(处),自身.跑结束(处),名称)
            return
        if 处-1>=0 and 自身.有序[处-1].get('kind')!='boundary':
            自身.分配跑(自身.跑开始(处-1),处-1,名称)
        右=处+1 if 这里 is not None and 这里.get('seq')==序号 else 处
        if 右<len(自身.有序) and 自身.有序[右].get('kind')!='boundary':
            自身.分配跑(右,自身.跑结束(右),名称)


空贡献={'anchorSeq':0,'nodes':空列表,'partial':None,'running':None}


def 旧贡献(节点):
    '兼容统计药丸的旧切片。隐藏的非助手行不贡献'
    if not isinstance(节点,dict):
        return 空贡献
    if 节点.get('visibility')!='visible' and 节点.get('kind')!='assistant-step':
        return 空贡献
    种类=节点.get('kind')
    数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
    if 种类 in ('user','steering','context','command','compaction','turn-error','turn-max-tokens','unknown'):
        return {'anchorSeq':锚序号(节点),'nodes':[数据],'partial':None,'running':None}
    if 种类=='assistant-step':
        if 数据.get('status')=='running':
            if 节点.get('visibility')!='visible':
                return 空贡献
            return {
                'anchorSeq':锚序号(节点),
                'nodes':空列表,
                'partial':{'turn':数据.get('turn'),'step':数据.get('step'),'blocks':数据.get('blocks')},
                'running':None,
            }
        终=数据.get('finalNode')
        return {'anchorSeq':锚序号(节点),'nodes':空列表 if 终 is None else [终],'partial':None,'running':None}
    if 种类=='tool-call':
        根=数据.get('root')
        if 是运行中工具(根):
            return {'anchorSeq':锚序号(节点),'nodes':空列表,'partial':None,'running':根}
        return {'anchorSeq':锚序号(节点),'nodes':[根],'partial':None,'running':None}
    if 种类=='manual-compaction':
        压缩=数据.get('compaction')
        节点列=[数据.get('command')] if 压缩 is None else [数据.get('command'),压缩]
        return {'anchorSeq':锚序号(节点),'nodes':节点列,'partial':None,'running':None}
    if 种类=='model-retry':
        return {'anchorSeq':锚序号(节点),'nodes':数据.get('attempts') or [],'partial':None,'running':None}
    return 空贡献


def 贡献相同(左,右):
    '锚、部分、运行中和节点身份都一样'
    if 左 is None:
        return False
    左部分=左.get('partial') if isinstance(左.get('partial'),dict) else None
    右部分=右.get('partial') if isinstance(右.get('partial'),dict) else None
    return (
        左.get('anchorSeq')==右.get('anchorSeq')
        and (左部分.get('blocks') if 左部分 else None) is (右部分.get('blocks') if 右部分 else None)
        and (左部分.get('turn') if 左部分 else None)==(右部分.get('turn') if 右部分 else None)
        and (左部分.get('step') if 左部分 else None)==(右部分.get('step') if 右部分 else None)
        and 左.get('running') is 右.get('running')
        and 引用相同(左.get('nodes') or [],右.get('nodes') or [])
    )


def 更新贡献索引(索引,键,贡献,在):
    '在就写入，不在就删'
    if 在:
        索引[键]=贡献
    elif 键 in 索引:
        del 索引[键]


def 定稿变了(先前,下一):
    '节点列表或锚变了'
    先前节点=先前.get('nodes') if isinstance(先前,dict) else 空列表
    return (not 引用相同(先前节点 or [],下一.get('nodes') or [])) or ((len(先前节点 or [])>0 or len(下一.get('nodes') or [])>0) and (None if 先前 is None else 先前.get('anchorSeq'))!=下一.get('anchorSeq'))


def 运行变了(先前,下一):
    '运行中的根或锚变了'
    先前运行=先前.get('running') if isinstance(先前,dict) else None
    return 先前运行 is not 下一.get('running') or ((先前运行 is not None or 下一.get('running') is not None) and (None if 先前 is None else 先前.get('anchorSeq'))!=下一.get('anchorSeq'))


def 部分变了(先前,下一):
    '部分块或锚变了'
    左=先前.get('partial') if isinstance(先前,dict) and isinstance(先前.get('partial'),dict) else None
    右=下一.get('partial') if isinstance(下一.get('partial'),dict) else None
    左空=左 is None
    右空=右 is None
    return (
        (None if 左空 else 左.get('blocks')) is (None if 右空 else 右.get('blocks'))
        and (None if 左空 else 左.get('turn'))==(None if 右空 else 右.get('turn'))
        and (None if 左空 else 左.get('step'))==(None if 右空 else 右.get('step'))
    ) is False or (((左 is not None) or (右 is not None)) and (None if 先前 is None else 先前.get('anchorSeq'))!=下一.get('anchorSeq'))


class 旧切片构建器:
    '作曲器统计和快照顶层旧字段的增量投影'
    def __init__(自身):
        '空切片'
        自身.贡献={}
        自身.定稿贡献={}
        自身.运行贡献={}
        自身.部分贡献={}
        自身.定稿=空列表
        自身.运行调用=空列表
        自身.部分=None
        自身.时间线=None
        自身.回合时机={}
        自身.回合结束={}

    def replace(自身,节点表,时间线):
        '整表重建'
        自身.贡献={}
        自身.定稿贡献={}
        自身.运行贡献={}
        自身.部分贡献={}
        for 节点 in 节点表:
            if not isinstance(节点,dict):
                continue
            贡献=旧贡献(节点)
            自身.贡献[节点.get('key')]=贡献
            自身.索引(节点.get('key'),贡献)
        自身.重建定稿()
        自身.重建运行()
        自身.重建部分()
        自身.更新时间线(时间线)
        return 自身.快照()

    def apply(自身,更新,时间线):
        '只重建变了的那一类'
        定稿脏=False
        运行脏=False
        部分脏=False
        for 节点 in 更新:
            if not isinstance(节点,dict):
                continue
            贡献=旧贡献(节点)
            先前=自身.贡献.get(节点.get('key'))
            if 贡献相同(先前,贡献):
                continue
            定稿脏=定稿脏 or 定稿变了(先前,贡献)
            运行脏=运行脏 or 运行变了(先前,贡献)
            部分脏=部分脏 or 部分变了(先前,贡献)
            自身.贡献[节点.get('key')]=贡献
            自身.索引(节点.get('key'),贡献)
        if 定稿脏:
            自身.重建定稿()
        if 运行脏:
            自身.重建运行()
        if 部分脏:
            自身.重建部分()
        自身.更新时间线(时间线)
        return 自身.快照()

    def 索引(自身,键,贡献):
        '分进定稿、运行和部分三张表'
        更新贡献索引(自身.定稿贡献,键,贡献,len(贡献.get('nodes') or [])>0)
        更新贡献索引(自身.运行贡献,键,贡献,贡献.get('running') is not None)
        更新贡献索引(自身.部分贡献,键,贡献,贡献.get('partial') is not None)

    def 重建定稿(自身):
        '按消息序号拼定稿节点'
        定稿=[]
        for 贡献 in 自身.定稿贡献.values():
            for 节点 in 贡献.get('nodes') or []:
                定稿.append(节点)
        定稿.sort(key=消息序号)
        if not 引用相同(自身.定稿,定稿):
            自身.定稿=定稿

    def 重建运行(自身):
        '按锚拼还在跑的工具根'
        列=list(自身.运行贡献.values())
        列.sort(key=贡献锚)
        运行=[]
        for 贡献 in 列:
            if 贡献.get('running') is not None:
                运行.append(贡献.get('running'))
        if not 引用相同(自身.运行调用,运行):
            自身.运行调用=运行

    def 重建部分(自身):
        '锚最大的那份部分助手'
        列=list(自身.部分贡献.values())
        列.sort(key=贡献锚)
        部分=None
        for 贡献 in reversed(列):
            if 贡献.get('partial') is not None:
                部分=贡献.get('partial')
                break
        左=自身.部分 if isinstance(自身.部分,dict) else None
        右=部分 if isinstance(部分,dict) else None
        if (None if 左 is None else 左.get('blocks')) is not (None if 右 is None else 右.get('blocks')) or (None if 左 is None else 左.get('turn'))!=(None if 右 is None else 右.get('turn')) or (None if 左 is None else 左.get('step'))!=(None if 右 is None else 右.get('step')):
            自身.部分=部分

    def 更新时间线(自身,时间线):
        '回合起止时间'
        if 自身.时间线 is 时间线:
            return
        自身.时间线=时间线
        时机={}
        结束表={}
        回合表=时间线.get('turns') if isinstance(时间线,dict) else {}
        值列=回合表.values() if isinstance(回合表,dict) else []
        for 回合 in 值列:
            if not isinstance(回合,dict):
                continue
            起点=回合.get('start')
            if isinstance(起点,dict):
                一条={'startTime':起点.get('time')}
                结束=回合.get('end')
                if isinstance(结束,dict):
                    一条['endTime']=结束.get('time')
                时机[回合.get('turn')]=一条
            结束=回合.get('end')
            if isinstance(结束,dict):
                结束表[回合.get('turn')]=结束.get('seq')
        自身.回合时机=时机
        自身.回合结束=结束表

    def 快照(自身):
        '当前旧切片'
        return {
            'nodes':自身.定稿,
            'turnTimings':自身.回合时机,
            'turnEnds':自身.回合结束,
            'partial':自身.部分,
            'runningCalls':自身.运行调用,
        }


def 位置身份(位置):
    '种类和坐标拼成比较串'
    坐标=位置坐标(位置)
    return str(位置.get('kind') if isinstance(位置,dict) else '')+':'+str(坐标.get('turn') or '')+':'+str(坐标.get('step') or '')


def 节点回合集(节点表):
    '这些节点落到的回合'
    回合=set()
    for 节点 in 节点表:
        if isinstance(节点,dict):
            号=位置坐标(节点.get('location')).get('turn')
            if 号 is not None:
                回合.add(号)
    return 回合


class 聊天快照构建器:
    '聊天目标的增量构建器。节点源按键发布，贴底按交换分段，并带旧切片、引用标签和技能名'
    def __init__(自身):
        '空快照。分组输入先是整表替换'
        自身.存储=可变节点存储()
        自身.位置=位置索引()
        自身.导航=导航索引()
        自身.旧=旧切片构建器()
        自身.引用=引用标签投影()
        自身.技能=技能名投影()
        自身.顺序=空键
        自身.时间线=None
        自身.empty=自身.快照({'turnOrder':空回合,'turns':{}})
        自身.最近分组={
            'kind':'replace',
            'order':自身.顺序,
            'readNode':自身.读组节点,
            'readTurn':自身.读组回合,
            'readPosition':自身.读组位置,
            'timeline':自身.empty['timeline'],
        }

    def 读组节点(自身,键):
        '分组读取节点'
        return 自身.存储.get(键)

    def 读组回合(自身,回合):
        '这一回合的节点键'
        return 自身.位置.getTurn(回合)

    def 读组位置(自身,键):
        '这个键的前后位置'
        return 自身.位置.getPosition(键)

    def get(自身,键,默认=None):
        '组装器用字典方式取 replace、apply、groupInput、publish'
        if 键 in ('replace','apply','groupInput','publish','empty'):
            return getattr(自身,键)
        return 默认

    def __getitem__(自身,键):
        '组装器按键调用构建器方法'
        方法=自身.get(键)
        if 方法 is None:
            raise KeyError(键)
        return 方法

    def 快照(自身,时间线,旧=None):
        '当前顺序、节点仓库、位置、导航、时间线和旧切片'
        if 旧 is None:
            旧=自身.旧.replace(空列表,时间线)
        return {
            'order':自身.顺序,
            'nodes':自身.存储,
            'locations':自身.位置,
            'navigation':自身.导航,
            'timeline':时间线,
            'legacy':旧,
        }

    def replace(自身,输入):
        '整表替换。先贴引用标签和技能名，再排可见顺序'
        节点表=输入.get('nodes') if isinstance(输入,dict) else []
        节点表=自身.技能.replace(自身.引用.replace(节点表 or []))
        自身.存储.replace(节点表)
        自身.顺序=[节点.get('key') for 节点 in 有序可见聊天节点(自身.存储.values())]
        自身.位置.rebuild(自身.顺序,自身.存储)
        自身.存储.replaceProcesses(自身.顺序,自身.位置)
        时间线=输入.get('timeline') if isinstance(输入,dict) else {'turnOrder':[],'turns':{}}
        自身.存储.settleBottom(时间线.get('turnOrder') if isinstance(时间线,dict) else [],自身.位置)
        自身.导航.rebuild(时间线,自身.位置,自身.存储)
        自身.时间线=时间线
        自身.最近分组={
            'kind':'replace',
            'order':自身.顺序,
            'readNode':自身.读组节点,
            'readTurn':自身.读组回合,
            'readPosition':自身.读组位置,
            'timeline':时间线,
        }
        return 自身.快照(时间线,自身.旧.replace(节点表,时间线))

    def apply(自身,输入):
        '增量盖节点。结构变了才重排，内容变了只碰受影响的回合'
        更新=输入.get('upserts') if isinstance(输入,dict) else []
        更新=自身.技能.apply(自身.引用.apply(更新 or [],自身.存储),自身.存储)
        过程回合=set()
        结构=False
        仅内容=[]
        变化=[]
        for 节点 in 更新:
            if not isinstance(节点,dict):
                continue
            先前=自身.存储.get(节点.get('key'))
            if 先前 is not 节点:
                变化.append({'previous':先前,'current':节点})
            节点结构=(
                先前 is None
                or 先前.get('kind')!=节点.get('kind')
                or 先前.get('anchorSeq')!=节点.get('anchorSeq')
                or 先前.get('visibility')!=节点.get('visibility')
                or 先前.get('groupTree')!=节点.get('groupTree')
                or 位置身份(先前.get('location'))!=位置身份(节点.get('location'))
            )
            结构=结构 or 节点结构
            if not 节点结构:
                仅内容.append(节点)
            if 过程输入变了(先前,节点,节点结构):
                先前回合=None if 先前 is None else 位置坐标(先前.get('location')).get('turn')
                后回合=位置坐标(节点.get('location')).get('turn')
                if 先前回合 is not None:
                    过程回合.add(先前回合)
                if 后回合 is not None:
                    过程回合.add(后回合)
        自身.存储.upsert(更新)
        变序=[]
        if 结构:
            下一=[节点.get('key') for 节点 in 有序可见聊天节点(自身.存储.values())]
            if not 引用相同(自身.顺序,下一):
                自身.顺序=下一
            变序=自身.位置.rebuild(自身.顺序,自身.存储)
        自身.位置.touch(仅内容)
        自身.存储.updateProcesses(过程回合,自身.位置)
        时间线=输入.get('timeline') if isinstance(输入,dict) else {'turnOrder':[],'turns':{}}
        自身.存储.settleBottom(时间线.get('turnOrder') if isinstance(时间线,dict) else [],自身.位置)
        if 结构 or 时间线 is not 自身.时间线:
            自身.导航.rebuild(时间线,自身.位置,自身.存储)
        else:
            自身.导航.touch(节点回合集(仅内容),自身.位置,自身.存储)
        自身.时间线=时间线
        自身.最近分组={
            'kind':'apply',
            'changes':变化,
            'order':自身.顺序,
            'readNode':自身.读组节点,
            'readTurn':自身.读组回合,
            'readPosition':自身.读组位置,
            'timeline':时间线,
            'changedTurns':输入.get('changedTurns') if isinstance(输入,dict) and 输入.get('changedTurns') is not None else 空回合,
            'changedTurnOrders':变序,
        }
        return 自身.快照(时间线,自身.旧.apply(更新,时间线))

    def groupInput(自身):
        '上一批替换或增量，给过程组读'
        return 自身.最近分组

    def publish(自身):
        '发布脏了的分键源、贴底、过程和回合种类'
        自身.存储.publish()


def 创建构建器():
    '一份聊天视图一个构建器'
    return 聊天快照构建器()


def 视图活动(快照):
    '有不是命令的节点时，聊天目标算活动'
    顺序=快照.get('order') if isinstance(快照,dict) else []
    节点=快照.get('nodes') if isinstance(快照,dict) else None
    for 键 in 顺序 or []:
        当前=节点.get(键) if hasattr(节点,'get') else None
        if isinstance(当前,dict) and 当前.get('kind')!='command':
            return True
    return False


聊天视图定义={
    'target':'chat',
    'create':创建构建器,
    'isActive':视图活动,
}


def 登记聊天会话视图(上下文):
    '把聊天目标构建器登记进会话视图'
    上下文.uiConversation.views.register(聊天视图定义)
