from .类型 import 安全整数上限,表面事件类型 as 表面事件类型元组
from .已知事件类型 import 已知会话事件类型,消息投影事件类型

__all__=[
    '是否可进表面类型','是否表面事件','是否追加表面事件','是否替换表面事件',
    '事件派生消息','校验会话事件数据','校验表面元数据','折叠表面','表面视图',
]

表面事件类型=frozenset(表面事件类型元组)

class 表面错误(Exception):
    """内核会话表面包的异常基类。"""

def 是否可进表面类型(类型):
    """某事件类型能否加入模型可见表面（对齐类型.表面事件类型）。"""
    return 类型 in 表面事件类型

def 是否表面事件(事件):
    """把事件收窄为带必需标记的可进表面事件。"""
    if ('type' not in 事件) or 事件['type'] not in 表面事件类型:
        return False
    return 'surfaceOp' in 事件

def 是否追加表面事件(事件):
    """把事件收窄为追加源表面事件。"""
    return 是否表面事件(事件) and 事件['surfaceOp']=='append'

def 是否替换表面事件(事件):
    """把事件收窄为表面替换。"""
    return 是否表面事件(事件) and 事件['surfaceOp']!='append'

def 事件派生消息(事件,投影消息=None):
    """把单条事件投影成它派生出的 LLM 消息；不产出消息则为 None。调用方重建模型输入时传入同一前缀 foldSurface 的 projectedMessages；无该表则读原始事件内容。"""
    if 投影消息 is not None:
        序号=事件['seq'] if 'seq' in 事件 else None
        if 序号 in 投影消息:
            return 投影消息[序号]
    类型=事件['type'] if 'type' in 事件 else None
    if 类型=='user/message':
        return 事件['data']
    if 类型=='system/message' or 类型=='assistant/message':
        消息=事件['data']['message']
        if len(消息['content'])==0:
            return None
        return 消息
    if 类型=='tool/result':
        return 事件['data']['message']
    return None

def 是否记录(值):
    """载荷字段是否为 JSON 对象（非数组或标量）。"""
    return isinstance(值,dict)

def 校验会话事件数据(事件,主题):
    """拒绝非规范请求头字段与自相矛盾的工具失败元数据。"""
    数据=事件['data'] if 'data' in 事件 else None
    类型=事件['type'] if 'type' in 事件 else None
    if 类型=='request/header':
        if not 是否记录(数据):
            raise 表面错误(主题+' 的 data 必须是对象')
        头=数据['header'] if 'header' in 数据 else None
        if not 是否记录(头):
            raise 表面错误(主题+' 的 header 必须是对象')
        if 'system' in 头:
            raise 表面错误(主题+' 必须省略 header.system；改用 system/message')
        工具=头['tools'] if 'tools' in 头 else None
        if isinstance(工具,list) and len(工具)==0:
            raise 表面错误(主题+' 必须省略空的 tools')
        默认=头['adapterDefaults'] if 'adapterDefaults' in 头 else None
        if 是否记录(默认) and len(默认)==0:
            raise 表面错误(主题+' 必须省略空的 adapterDefaults')
    elif 类型=='tool/result':
        if not 是否记录(数据):
            raise 表面错误(主题+' 的 data 必须是对象')
        if 'error' not in 数据:
            return
        消息=数据['message'] if 'message' in 数据 else None
        内容=消息['content'] if 是否记录(消息) and 'content' in 消息 else None
        块=内容[0] if isinstance(内容,list) and len(内容)>0 else None
        if (not 是否记录(块)) or ('isError' not in 块) or 块['isError'] is not True:
            raise 表面错误(主题+' 的 error 要求 message content[0].isError === true')

def 创建折叠状态():
    """创建空的表面折叠状态。"""
    return {'nodes':[],'replaceGeneration':0,'contentGeneration':0,'projectedMessages':{},'projections':[]}

def 是否事件序号(值):
    """运行时值是否为非负安全事件序号。"""
    if isinstance(值,bool):
        return False#布尔不是整数
    if isinstance(值,int):
        return 值>=0 and 值<=安全整数上限
    if isinstance(值,float) and 值.is_integer():
        return 值>=0 and 值<=安全整数上限
    return False

def 是否替换操作(值):
    """运行时值是否正好是位置替换形态。"""
    if not isinstance(值,dict):
        return False
    if len(值)!=3:
        return False
    if 'op' not in 值 or 'startSeq' not in 值 or 'endSeq' not in 值:
        return False
    if 值['op']!='replace':
        return False
    return 是否事件序号(值['startSeq']) and 是否事件序号(值['endSeq'])

def 取出表面操作(事件):
    """校验事件本地的表面资格并返回其操作。"""
    类型=事件['type'] if 'type' in 事件 else None
    if not 是否可进表面类型(类型):
        #未知可忽略记录保留不透明元数据，不影响历史。
        if 类型 not in 已知会话事件类型 and ('ignorable' in 事件 and 事件['ignorable'] is True):
            return None
        if 'surfaceOp' in 事件:
            raise 表面错误('会话事件 "'+str(类型)+'" 不可进表面，不能携带 surfaceOp')
        if 'sourceEventSeqs' in 事件:
            raise 表面错误('会话事件 "'+str(类型)+'" 不可进表面，不能携带 sourceEventSeqs')
        return None
    if 'surfaceOp' not in 事件:
        raise 表面错误('会话事件 "'+str(类型)+'" 可进表面，必须带 surfaceOp 标记')
    操作=事件['surfaceOp']
    if 操作=='append':
        return 操作
    if 操作 is None or isinstance(操作,(str,bytes,int,float,bool,list)):
        raise 表面错误('会话事件 "'+str(类型)+'" 携带了非法 surfaceOp')
    if not isinstance(操作,dict):
        raise 表面错误('会话事件 "'+str(类型)+'" 携带了非法 surfaceOp')
    if not 是否替换操作(操作):
        raise 表面错误('会话事件 "'+str(类型)+'" 携带了非法 replace surfaceOp')
    return 操作

def 断言源事件引用(事件,被遮蔽序号):
    """按先前日志条目与替换区间校验引用的源事件序号。"""
    原始=事件['sourceEventSeqs'] if 'sourceEventSeqs' in 事件 else None
    if 事件['type']=='assistant/message' and 原始 is not None:
        raise 表面错误('assistant/message 内嵌其源流水，不能携带 sourceEventSeqs')
    已见=set()
    if 原始 is not None:
        if not isinstance(原始,list):
            raise 表面错误('seq '+str(事件['seq'])+' 上的 sourceEventSeqs 若出现必须是数组')
        if len(原始)==0:
            raise 表面错误('sourceEventSeqs 不得为空')
        不早源=None
        for 源 in 原始:
            if not 是否事件序号(源):
                raise 表面错误('会话事件 "'+str(事件['type'])+'" 的 sourceEventSeqs 必须稠密包含非负安全整数')
            已见.add(源)
            if 不早源 is None and 源>=事件['seq']:
                不早源=源
        if len(已见)!=len(原始):
            raise 表面错误('sourceEventSeqs 不得含重复项')
        if 不早源 is not None:
            raise 表面错误('sourceEventSeqs 必须引用更早事件: '+str(不早源)+' >= 当前 seq '+str(事件['seq']))
    缺=[]
    for 序号 in 被遮蔽序号:
        if 序号 not in 已见:
            缺.append(序号)
    if len(缺)>0:
        缺文=', '.join(str(项) for 项 in 缺)
        raise 表面错误('表面替换: sourceEventSeqs 必须包含每个被遮蔽的表面节点；缺少 '+缺文)

def 校验表面元数据(事件):
    """校验一条事件的表面元数据，不检查其是否属于某日志或表面。"""
    操作=取出表面操作(事件)
    if 操作 is not None and 操作!='append':
        if 操作['startSeq']>=事件['seq'] or 操作['endSeq']>=事件['seq']:
            raise 表面错误('seq '+str(事件['seq'])+' 处的表面替换: startSeq 与 endSeq 必须引用更早事件')
    if 操作 is not None:
        断言源事件引用(事件,[])
    return 操作

def 替换区间(状态,操作):
    """定位一段替换区间，不改当前折叠状态。"""
    节点列表=状态['nodes']
    try:
        起点下标=节点列表.index(操作['startSeq'])
    except ValueError:
        raise 表面错误('表面替换: 起点 seq '+str(操作['startSeq'])+' 不在表面中')
    try:
        终点下标=节点列表.index(操作['endSeq'])
    except ValueError:
        raise 表面错误('表面替换: 终点 seq '+str(操作['endSeq'])+' 不在表面中')
    if 起点下标>终点下标:
        raise 表面错误(
            '表面替换: 起点 seq '+str(操作['startSeq'])+'（下标 '+str(起点下标)+'）在终点 seq '+str(操作['endSeq'])+'（下标 '+str(终点下标)+'）之后'
        )
    return {
        'startIdx':起点下标,
        'endIdx':终点下标,
        'shadowedSeqs':节点列表[起点下标:终点下标+1],
    }

def json深相等(甲,乙):
    """会话事件 JSON 值域上的深结构相等。"""
    if 甲 is 乙:
        return True
    if isinstance(甲,bool) or isinstance(乙,bool):
        return 甲 is 乙
    if isinstance(甲,(int,float)) and isinstance(乙,(int,float)) and not isinstance(甲,bool) and not isinstance(乙,bool):
        return 甲==乙
    if isinstance(甲,str) and isinstance(乙,str):
        return 甲==乙
    if 甲 is None or 乙 is None:
        return 甲 is 乙
    if isinstance(甲,list) or isinstance(乙,list):
        if not isinstance(甲,list) or not isinstance(乙,list) or len(甲)!=len(乙):
            return False
        下标=0
        while 下标<len(甲):
            if not json深相等(甲[下标],乙[下标]):
                return False
            下标+=1
        return True
    if not isinstance(甲,dict) or not isinstance(乙,dict):
        return False
    甲键=list(甲.keys())
    if len(甲键)!=len(乙):
        return False
    for 键 in 甲键:
        if 键 not in 乙:
            return False
        if not json深相等(甲[键],乙[键]):
            return False
    return True

def 断言工具结果改写(事件,被遮蔽序号,事件列表,基序号):
    """把工具结果替换限制为只改当前一条结果的内容。"""
    if 事件['type']!='tool/result':
        return
    if len(被遮蔽序号)!=1:
        raise 表面错误('tool/result 表面替换必须恰好改写一个当前节点')
    for 原序号 in 被遮蔽序号:
        窗口下标=原序号-基序号
        原事件=事件列表[窗口下标] if 0<=窗口下标<len(事件列表) else None
        if 原事件 is None or 原事件['type']!='tool/result':
            raise 表面错误('tool/result 表面替换必须对准当前 tool/result')
        原载荷=dict(原事件['data'])
        新载荷=dict(事件['data'])
        原结果=原事件['data']['message']['content'][0]
        新结果=事件['data']['message']['content'][0]
        原消息=dict(原事件['data']['message'])
        原块=dict(原结果)
        原块['content']=None
        原消息['content']=[原块]
        原载荷['message']=原消息
        新消息=dict(事件['data']['message'])
        新块=dict(新结果)
        新块['content']=None
        新消息['content']=[新块]
        新载荷['message']=新消息
        if not json深相等(原载荷,新载荷):
            raise 表面错误('tool/result 表面替换只许改 content')

def 断言系统头改写(事件,状态,起点下标,被遮蔽序号,事件列表,基序号):
    """保护表面节点 0 上的系统提示。"""
    if 起点下标!=0:
        return
    头序号=状态['nodes'][0]
    头=事件列表[头序号-基序号] if 0<=(头序号-基序号)<len(事件列表) else None
    if 头 is None or 头['type']!='system/message':
        return
    if 事件['type']!='system/message' or len(被遮蔽序号)!=1:
        raise 表面错误('表面替换: 节点 0 持有系统提示，只能由恰好覆盖该节点的 system/message 改写')

def 计划表面事件(状态,事件,期望序号,事件列表,基序号,投影列表):
    """在回放边界校验一条事件，并准备其原子折叠变迁。投影列表为插件拥有的纯解释器。"""
    if 事件['seq']!=期望序号:
        raise 表面错误('会话事件 seq '+str(事件['seq'])+' 不连续；期望 '+str(期望序号))
    表面操作=校验表面元数据(事件)
    类型=事件['type'] if 'type' in 事件 else None
    投影=None
    for 候选 in 投影列表:
        if 候选['type']==类型:
            投影=候选
            break
    if 投影 is not None:
        上下文={'nodes':状态['nodes'],'events':事件列表,'baseSeq':基序号,'messages':dict(状态['projectedMessages'])}
        return {'kind':'project','projection':投影,'messages':投影['project'](事件,上下文)}
    if 类型 in 消息投影事件类型:
        raise 表面错误('会话事件 "'+str(类型)+'" 需要消息投影；加载其归属插件或提供投影定义')
    if 表面操作 is None:
        return None
    if 表面操作=='append':
        return {'kind':'append','seq':事件['seq']}
    区间=替换区间(状态,表面操作)
    断言源事件引用(事件,区间['shadowedSeqs'])
    断言工具结果改写(事件,区间['shadowedSeqs'],事件列表,基序号)
    断言系统头改写(事件,状态,区间['startIdx'],区间['shadowedSeqs'],事件列表,基序号)
    return {
        'kind':'replace',
        'seq':事件['seq'],
        'start':表面操作['startSeq'],
        'end':表面操作['endSeq'],
        'startIdx':区间['startIdx'],
        'endIdx':区间['endIdx'],
        'shadowedSeqs':区间['shadowedSeqs'],
    }

def 应用表面计划(状态,计划):
    """提交一条先前已校验的表面变迁。"""
    if 计划 is not None and 计划['kind']=='append':
        状态['nodes'].append(计划['seq'])
    elif 计划 is not None and 计划['kind']=='replace':
        起点=计划['startIdx']
        终点=计划['endIdx']
        状态['nodes'][起点:终点+1]=[计划['seq']]
        状态['replaceGeneration']+=1
        状态['contentGeneration']+=1
    elif 计划 is not None and 计划['kind']=='project':
        for 序号,消息 in 计划['messages'].items():
            状态['projectedMessages'][序号]=消息
        状态['projections'].append(计划['projection'])
        状态['contentGeneration']+=1
    if 计划 is None or 计划['kind']!='replace':
        return None
    return {
        'seq':计划['seq'],
        'start':计划['start'],
        'end':计划['end'],
        'shadowedSeqs':计划['shadowedSeqs'],
    }

def 应用表面事件(状态,事件,期望序号,事件列表,基序号,投影列表):
    """应用一条事件，仅在发生替换时返回替换元数据。"""
    计划=计划表面事件(状态,事件,期望序号,事件列表,基序号,投影列表)
    return 应用表面计划(状态,计划)

def 折叠表面(事件列表,投影列表=None):
    """经规范表面折叠回放一份完整会话日志。投影列表为插件拥有的纯解释器。"""
    if 投影列表 is None:
        投影列表=[]
    状态=创建折叠状态()
    替换列表=[]
    下标=0
    for 事件 in 事件列表:
        替换=应用表面事件(状态,事件,下标,事件列表,0,投影列表)
        if 替换 is not None:
            替换列表.append(替换)
        下标+=1
    return {'nodes':list(状态['nodes']),'replacements':替换列表,'projectedMessages':dict(状态['projectedMessages'])}

class 表面视图:
    """增量有序表面视图与追加边界校验器。"""
    def __init__(自身,日志,基序号=0,投影列表=None):
        """连续完整日志或已加载事件窗口。投影列表为活借用的解释器。"""
        if 投影列表 is None:
            投影列表=[]
        自身._日志=日志
        自身._基序号=基序号
        自身._投影列表=投影列表
        自身._状态=创建折叠状态()
        自身._上次处理序号=基序号-1
        自身._待提交=None

    def 校验下一条(自身,事件):
        """校验下一个候选，不改已提交表面。"""
        自身._断言投影()
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:
            自身._追上增量()
        期望序号=自身._基序号+len(自身._日志)
        自身._待提交={
            'event':事件,
            'expectedSeq':期望序号,
            'plan':计划表面事件(自身._状态,事件,期望序号,自身._日志,自身._基序号,自身._投影列表),
        }

    @property
    def replaceGeneration(自身):
        """已折叠位置替换的单调计数。"""
        自身._断言投影()
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:
            自身._追上增量()
        return 自身._状态['replaceGeneration']

    @property
    def contentGeneration(自身):
        """已提交替换与插件拥有消息改写的单调计数。"""
        自身._断言投影()
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:
            自身._追上增量()
        return 自身._状态['contentGeneration']

    def 派生事件消息(自身,事件):
        """把已提交消息投影应用到一条事件。"""
        自身._断言投影()
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:
            自身._追上增量()
        return 事件派生消息(事件,自身._状态['projectedMessages'])

    @property
    def nodes(自身):
        """模型可见顺序的表面事件序号。"""
        自身._断言投影()
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:
            自身._追上增量()
        return 自身._状态['nodes']

    def _追上增量(自身):
        """折叠自上次访问以来追加的事件。"""
        末序号=自身._基序号+len(自身._日志)-1
        序号=自身._上次处理序号+1
        while 序号<=末序号:
            下标=序号-自身._基序号
            事件=自身._日志[下标]
            待提交=自身._待提交
            if 待提交 is not None and 待提交['event'] is 事件 and 待提交['expectedSeq']==序号:
                应用表面计划(自身._状态,待提交['plan'])
            else:
                应用表面事件(自身._状态,事件,序号,自身._日志,自身._基序号,自身._投影列表)
            if 待提交 is not None and 待提交['expectedSeq']<=序号:
                自身._待提交=None
            自身._上次处理序号=序号
            序号+=1

    def _断言投影(自身):
        """已用定义被卸下则拒绝继续派生。"""
        候选=自身._待提交
        待用=None
        if 候选 is not None:
            下标=候选['expectedSeq']-自身._基序号
            if 0<=下标<len(自身._日志) and 自身._日志[下标] is 候选['event']:
                待用=候选['plan']
        已用=list(自身._状态['projections'])
        if 待用 is not None and 待用['kind']=='project':
            已用.append(待用['projection'])
        for 投影 in 已用:
            if not any(项 is 投影 for 项 in 自身._投影列表):
                raise 表面错误('session message projection "'+str(投影['type'])+'" was removed or replaced; restore the session with its owning plugin')
