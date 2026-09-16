from .类型 import 安全整数上限,表面事件类型 as 表面事件类型元组#外来 JSON 上限与表面类型词表
from .已知事件类型 import 已知会话事件类型,消息投影事件类型#导入已知事件类型与消息投影类型

__all__=[#仅中文公开名
    '是否可进表面类型','是否表面事件','是否追加表面事件','是否替换表面事件',
    '事件派生消息','校验会话事件数据','校验表面元数据','折叠表面','表面管理器',
]#公开面结束

表面事件类型=frozenset(表面事件类型元组)#产出消息的事件类型集合

class 表面错误(Exception):
    """内核会话表面包的异常基类。"""

def 是否可进表面类型(类型):#类型是否可进表面
    """某事件类型能否加入模型可见表面（对齐类型.表面事件类型）。"""
    return 类型 in 表面事件类型#查集合

def 是否表面事件(事件):#是否表面事件
    """把事件收窄为带必需标记的可进表面事件。"""
    if ('type' not in 事件) or 事件['type'] not in 表面事件类型:#类型不对
        return False#类型不对
    return 'surfaceOp' in 事件#必须有表面操作

def 是否追加表面事件(事件):#是否追加表面事件
    """把事件收窄为追加源表面事件。"""
    return 是否表面事件(事件) and 事件['surfaceOp']=='append'#表面且操作为追加

def 是否替换表面事件(事件):#是否替换表面事件
    """把事件收窄为表面替换。"""
    return 是否表面事件(事件) and 事件['surfaceOp']!='append'#表面且不是追加

def 事件派生消息(事件,投影消息=None):#事件派生消息
    """把单条事件投影成它派生出的 LLM 消息；不产出消息则为 None。调用方重建模型输入时传入同一前缀 foldSurface 的 projectedMessages；无该表则读原始事件内容。"""
    if 投影消息 is not None:#有已提交投影
        序号=事件['seq'] if 'seq' in 事件 else None#事件序号
        if 序号 in 投影消息:#本序号已被投影改写
            return 投影消息[序号]#用投影副本
    类型=事件['type'] if 'type' in 事件 else None#事件类型
    if 类型=='user/message':#用户消息
        return 事件['data']#载荷即消息
    if 类型=='system/message' or 类型=='assistant/message':#系统或助手
        消息=事件['data']['message']#取出消息
        if len(消息['content'])==0:#空内容
            return None#空内容不进历史
        return 消息#取出消息
    if 类型=='tool/result':#工具结果
        return 事件['data']['message']#取出消息
    return None#非表面事件无消息

def 是否记录(值):#是否 JSON 对象记录
    """载荷字段是否为 JSON 对象（非数组或标量）。"""
    return isinstance(值,dict)#普通对象

def 校验会话事件数据(事件,主题):#校验会话事件数据
    """拒绝非规范请求头字段与自相矛盾的工具失败元数据。"""
    数据=事件['data'] if 'data' in 事件 else None#载荷
    类型=事件['type'] if 'type' in 事件 else None#类型
    if 类型=='request/header':#请求头
        if not 是否记录(数据):#data须对象
            raise 表面错误(主题+' 的 data 必须是对象')#data须对象
        头=数据['header'] if 'header' in 数据 else None#内层头
        if not 是否记录(头):#header须对象
            raise 表面错误(主题+' 的 header 必须是对象')#header须对象
        if 'system' in 头:#禁止 system
            raise 表面错误(主题+' 必须省略 header.system；改用 system/message')#禁止system
        工具=头['tools'] if 'tools' in 头 else None#工具
        if isinstance(工具,list) and len(工具)==0:#空工具
            raise 表面错误(主题+' 必须省略空的 tools')#须省略
        默认=头['adapterDefaults'] if 'adapterDefaults' in 头 else None#适配器默认
        if 是否记录(默认) and len(默认)==0:#空默认
            raise 表面错误(主题+' 必须省略空的 adapterDefaults')#须省略
    elif 类型=='tool/result':#工具结果
        if not 是否记录(数据):#data须对象
            raise 表面错误(主题+' 的 data 必须是对象')#data须对象
        if 'error' not in 数据:#无错误放过
            return#无错误放过
        消息=数据['message'] if 'message' in 数据 else None#消息
        内容=消息['content'] if 是否记录(消息) and 'content' in 消息 else None#内容
        块=内容[0] if isinstance(内容,list) and len(内容)>0 else None#首块
        if (not 是否记录(块)) or ('isError' not in 块) or 块['isError'] is not True:#须错误块
            raise 表面错误(主题+' 的 error 要求 message content[0].isError === true')#矛盾

def 创建折叠状态():#空折叠状态
    """创建空的表面折叠状态。"""
    return {'nodes':[],'replaceGeneration':0,'contentGeneration':0,'projectedMessages':{},'projections':[]}#空节点、零代数与空投影

def 是否事件序号(值):#是否事件序号
    """运行时值是否为非负安全事件序号。"""
    if isinstance(值,bool):#布尔不是整数
        return False#布尔
    if isinstance(值,int):#整数
        return 值>=0 and 值<=安全整数上限#非负且安全
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>=0 and 值<=安全整数上限#非负且安全
    return False#其它类型

def 是否替换操作(值):#是否替换操作
    """运行时值是否正好是位置替换形态。"""
    if not isinstance(值,dict):#必须是记录
        return False#必须是记录
    if len(值)!=3:#恰好三键
        return False#恰好三键
    if 'op' not in 值 or 'startSeq' not in 值 or 'endSeq' not in 值:#必须有这三键
        return False#必须有这三键
    if 值['op']!='replace':#必须是 replace
        return False#必须是 replace
    return 是否事件序号(值['startSeq']) and 是否事件序号(值['endSeq'])#起止序号合法

def 取出表面操作(事件):#取出表面操作
    """校验事件本地的表面资格并返回其操作。"""
    类型=事件['type'] if 'type' in 事件 else None#事件类型
    if not 是否可进表面类型(类型):#类型不可进表面
        # 未知可忽略记录保留不透明元数据，不影响历史。
        if 类型 not in 已知会话事件类型 and ('ignorable' in 事件 and 事件['ignorable'] is True):#可忽略放过
            return None#可忽略放过
        if 'surfaceOp' in 事件:#却带了表面操作
            raise 表面错误('会话事件 "'+str(类型)+'" 不可进表面，不能携带 surfaceOp')#非法携带
        if 'sourceEventSeqs' in 事件:#却带了源序号
            raise 表面错误('会话事件 "'+str(类型)+'" 不可进表面，不能携带 sourceEventSeqs')#非法携带
        return None#非表面事件
    if 'surfaceOp' not in 事件:#可进表面却没有标记
        raise 表面错误('会话事件 "'+str(类型)+'" 可进表面，必须带 surfaceOp 标记')#缺少标记
    操作=事件['surfaceOp']#取出操作
    if 操作=='append':#追加
        return 操作#追加
    if 操作 is None or isinstance(操作,(str,bytes,int,float,bool,list)):#不是对象
        raise 表面错误('会话事件 "'+str(类型)+'" 携带了非法 surfaceOp')#非法操作
    if not isinstance(操作,dict):#不是记录
        raise 表面错误('会话事件 "'+str(类型)+'" 携带了非法 surfaceOp')#非法操作
    if not 是否替换操作(操作):#不是合法替换
        raise 表面错误('会话事件 "'+str(类型)+'" 携带了非法 replace surfaceOp')#非法替换
    return 操作#合法替换

def 断言源事件引用(事件,被遮蔽序号):#校验源事件引用
    """按先前日志条目与替换区间校验引用的源事件序号。"""
    原始=事件['sourceEventSeqs'] if 'sourceEventSeqs' in 事件 else None#原始源序号
    if 事件['type']=='assistant/message' and 原始 is not None:#助手消息不得带源序号
        raise 表面错误('assistant/message 内嵌其源流水，不能携带 sourceEventSeqs')#禁止
    已见=set()#已见源
    if 原始 is not None:#有出处字段
        if not isinstance(原始,list):#不是数组
            raise 表面错误('seq '+str(事件['seq'])+' 上的 sourceEventSeqs 若出现必须是数组')#必须是数组
        if len(原始)==0:#空数组
            raise 表面错误('sourceEventSeqs 不得为空')#不得空
        不早源=None#不早于当前的源
        for 源 in 原始:#逐个源
            if not 是否事件序号(源):#不是合法序号
                raise 表面错误('会话事件 "'+str(事件['type'])+'" 的 sourceEventSeqs 必须稠密包含非负安全整数')#必须是稠密非负安全整数
            已见.add(源)#记下
            if 不早源 is None and 源>=事件['seq']:#找到不早于当前的
                不早源=源#找到不早于当前的
        if len(已见)!=len(原始):#有重复
            raise 表面错误('sourceEventSeqs 不得含重复项')#不得重复
        if 不早源 is not None:#引用了不更早的事件
            raise 表面错误('sourceEventSeqs 必须引用更早事件: '+str(不早源)+' >= 当前 seq '+str(事件['seq']))#必须引用更早事件
    缺=[]#被遮蔽却未引用
    for 序号 in 被遮蔽序号:#被遮蔽序号
        if 序号 not in 已见:#未引用
            缺.append(序号)#记下缺失
    if len(缺)>0:#缺引用
        缺文=', '.join(str(项) for 项 in 缺)#拼缺失
        raise 表面错误('表面替换: sourceEventSeqs 必须包含每个被遮蔽的表面节点；缺少 '+缺文)#必须覆盖每个被遮蔽节点

def 校验表面元数据(事件):#校验表面元数据
    """校验一条事件的表面元数据，不检查其是否属于某日志或表面。"""
    操作=取出表面操作(事件)#取操作
    if 操作 is not None and 操作!='append':#替换
        if 操作['startSeq']>=事件['seq'] or 操作['endSeq']>=事件['seq']:#引用不更早
            raise 表面错误('seq '+str(事件['seq'])+' 处的表面替换: startSeq 与 endSeq 必须引用更早事件')#须引用更早
    if 操作 is not None:#有操作
        断言源事件引用(事件,[])#事件本地出处
    return 操作#返回操作

def 替换区间(状态,操作):#定位替换区间
    """定位一段替换区间，不改当前折叠状态。"""
    节点列表=状态['nodes']#当前表面节点
    try:#查起点
        起点下标=节点列表.index(操作['startSeq'])#起点下标
    except ValueError:#表面里没有起点
        raise 表面错误('表面替换: 起点 seq '+str(操作['startSeq'])+' 不在表面中')#起点不在表面
    try:#查终点
        终点下标=节点列表.index(操作['endSeq'])#终点下标
    except ValueError:#表面里没有终点
        raise 表面错误('表面替换: 终点 seq '+str(操作['endSeq'])+' 不在表面中')#终点不在表面
    if 起点下标>终点下标:#起点在终点之后
        raise 表面错误(
            '表面替换: 起点 seq '+str(操作['startSeq'])+'（下标 '+str(起点下标)+'）在终点 seq '+str(操作['endSeq'])+'（下标 '+str(终点下标)+'）之后'
        )#区间颠倒
    return {#区间
        'startIdx':起点下标,#起点下标
        'endIdx':终点下标,#终点下标
        'shadowedSeqs':节点列表[起点下标:终点下标+1],#含端切片
    }#区间

def json深相等(甲,乙):#JSON 深相等
    """会话事件 JSON 值域上的深结构相等。"""
    if 甲 is 乙:#同一引用
        return True#同一引用
    if isinstance(甲,bool) or isinstance(乙,bool):#至少一方是布尔
        return 甲 is 乙#布尔必须同一
    if isinstance(甲,(int,float)) and isinstance(乙,(int,float)) and not isinstance(甲,bool) and not isinstance(乙,bool):#双方数字
        return 甲==乙#JSON 数字相等
    if isinstance(甲,str) and isinstance(乙,str):#双方字符串
        return 甲==乙#字符串相等
    if 甲 is None or 乙 is None:#至少一方 null
        return 甲 is 乙#仅双方都是 null
    if isinstance(甲,list) or isinstance(乙,list):#至少一方是数组
        if not isinstance(甲,list) or not isinstance(乙,list) or len(甲)!=len(乙):#双方都须是等长数组
            return False#双方都须是等长数组
        下标=0#逐项
        while 下标<len(甲):#逐项递归
            if not json深相等(甲[下标],乙[下标]):#项不等
                return False#项不等
            下标+=1#下一项
        return True#逐项都等
    if not isinstance(甲,dict) or not isinstance(乙,dict):#非双方对象
        return False#非双方对象
    甲键=list(甲.keys())#甲方键
    if len(甲键)!=len(乙):#键数不同
        return False#键数不同
    for 键 in 甲键:#逐键
        if 键 not in 乙:#缺键
            return False#缺键
        if not json深相等(甲[键],乙[键]):#值不等
            return False#值不等
    return True#逐键都等

def 断言工具结果改写(事件,被遮蔽序号,事件列表,基序号):#校验工具结果改写
    """把工具结果替换限制为只改当前一条结果的内容。"""
    if 事件['type']!='tool/result':#非工具结果
        return#非工具结果放过
    if len(被遮蔽序号)!=1:#不是恰好一个节点
        raise 表面错误('tool/result 表面替换必须恰好改写一个当前节点')#必须只改一个
    for 原序号 in 被遮蔽序号:#被遮蔽的原事件
        窗口下标=原序号-基序号#窗口下标
        原事件=事件列表[窗口下标] if 0<=窗口下标<len(事件列表) else None#窗口内原事件
        if 原事件 is None or 原事件['type']!='tool/result':#目标不是当前工具结果
            raise 表面错误('tool/result 表面替换必须对准当前 tool/result')#必须对准当前 tool/result
        原载荷=dict(原事件['data'])#原载荷副本
        新载荷=dict(事件['data'])#替换载荷副本
        原结果=原事件['data']['message']['content'][0]#原第一条内容
        新结果=事件['data']['message']['content'][0]#新第一条内容
        原消息=dict(原事件['data']['message'])#保留消息其余
        原块=dict(原结果)#块副本
        原块['content']=None#内容置空
        原消息['content']=[原块]#抹掉内容
        原载荷['message']=原消息#写回
        新消息=dict(事件['data']['message'])#保留消息其余
        新块=dict(新结果)#块副本
        新块['content']=None#内容置空
        新消息['content']=[新块]#抹掉内容
        新载荷['message']=新消息#写回
        if not json深相等(原载荷,新载荷):#其余字段不同
            raise 表面错误('tool/result 表面替换只许改 content')#只许改内容

def 断言系统头改写(事件,状态,起点下标,被遮蔽序号,事件列表,基序号):#校验系统头改写
    """保护表面节点 0 上的系统提示。"""
    if 起点下标!=0:#非节点0放过
        return#非节点0放过
    头序号=状态['nodes'][0]#头节点序号
    头=事件列表[头序号-基序号] if 0<=(头序号-基序号)<len(事件列表) else None#头节点事件
    if 头 is None or 头['type']!='system/message':#头非系统放过
        return#头非系统放过
    if 事件['type']!='system/message' or len(被遮蔽序号)!=1:#须单节点系统改写
        raise 表面错误('表面替换: 节点 0 持有系统提示，只能由恰好覆盖该节点的 system/message 改写')#拒绝

def 计划表面事件(状态,事件,期望序号,事件列表,基序号,投影列表):#计划表面变迁
    """在回放边界校验一条事件，并准备其原子折叠变迁。投影列表为插件拥有的纯解释器。"""
    if 事件['seq']!=期望序号:#序号不连续
        raise 表面错误('会话事件 seq '+str(事件['seq'])+' 不连续；期望 '+str(期望序号))#必须连续
    表面操作=校验表面元数据(事件)#校验表面元数据
    类型=事件['type'] if 'type' in 事件 else None#事件类型
    投影=None#匹配的解释器
    for 候选 in 投影列表:#按类型找解释器
        if 候选['type']==类型:#本事件类型
            投影=候选#命中
            break#只用一条
    if 投影 is not None:#插件拥有的消息改写
        上下文={'nodes':状态['nodes'],'events':事件列表,'baseSeq':基序号,'messages':dict(状态['projectedMessages'])}#投影前历史
        return {'kind':'project','projection':投影,'messages':投影['project'](事件,上下文)}#投影计划
    if 类型 in 消息投影事件类型:#需要解释器却未加载
        raise 表面错误('会话事件 "'+str(类型)+'" 需要消息投影；加载其归属插件或提供投影定义')#缺解释器
    if 表面操作 is None:#非表面
        return None#非表面
    if 表面操作=='append':#追加
        return {'kind':'append','seq':事件['seq']}#追加计划
    区间=替换区间(状态,表面操作)#定位区间
    断言源事件引用(事件,区间['shadowedSeqs'])#校验出处覆盖
    断言工具结果改写(事件,区间['shadowedSeqs'],事件列表,基序号)#工具结果只许改内容
    断言系统头改写(事件,状态,区间['startIdx'],区间['shadowedSeqs'],事件列表,基序号)#系统头保护
    return {#替换计划
        'kind':'replace',#替换
        'seq':事件['seq'],#替换事件序号
        'start':表面操作['startSeq'],#声明起点
        'end':表面操作['endSeq'],#声明终点
        'startIdx':区间['startIdx'],#起点下标
        'endIdx':区间['endIdx'],#终点下标
        'shadowedSeqs':区间['shadowedSeqs'],#被遮蔽
    }#替换计划

def 应用表面计划(状态,计划):#提交表面变迁
    """提交一条先前已校验的表面变迁。"""
    if 计划 is not None and 计划['kind']=='append':#追加
        状态['nodes'].append(计划['seq'])#接到尾部
    elif 计划 is not None and 计划['kind']=='replace':#替换
        起点=计划['startIdx']#起点下标
        终点=计划['endIdx']#终点下标
        状态['nodes'][起点:终点+1]=[计划['seq']]#区间换成新序号
        状态['replaceGeneration']+=1#代数加一
        状态['contentGeneration']+=1#内容代数加一
    elif 计划 is not None and 计划['kind']=='project':#消息投影
        for 序号,消息 in 计划['messages'].items():#按原序号写入
            状态['projectedMessages'][序号]=消息#投影副本
        状态['projections'].append(计划['projection'])#记下已用定义
        状态['contentGeneration']+=1#内容代数加一
    if 计划 is None or 计划['kind']!='replace':#非替换
        return None#非替换无元数据
    return {#替换元数据
        'seq':计划['seq'],#替换事件序号
        'start':计划['start'],#起点
        'end':计划['end'],#终点
        'shadowedSeqs':计划['shadowedSeqs'],#被遮蔽
    }#替换元数据

def 应用表面事件(状态,事件,期望序号,事件列表,基序号,投影列表):#应用一条事件
    """应用一条事件，仅在发生替换时返回替换元数据。"""
    计划=计划表面事件(状态,事件,期望序号,事件列表,基序号,投影列表)#先计划
    return 应用表面计划(状态,计划)#再提交

def 折叠表面(事件列表,投影列表=None):#完整折叠表面
    """经规范表面折叠回放一份完整会话日志。投影列表为插件拥有的纯解释器。"""
    if 投影列表 is None:#缺省无投影
        投影列表=[]#空表
    状态=创建折叠状态()#空状态
    替换列表=[]#替换历史
    下标=0#按序号扫描
    for 事件 in 事件列表:#按序号扫描
        替换=应用表面事件(状态,事件,下标,事件列表,0,投影列表)#应用事件
        if 替换 is not None:#记下替换
            替换列表.append(替换)#记下替换
        下标+=1#下一条
    return {'nodes':list(状态['nodes']),'replacements':替换列表,'projectedMessages':dict(状态['projectedMessages'])}#脱离结果

class 表面管理器:#表面管理器
    """增量有序表面视图与追加边界校验器。"""
    def __init__(自身,日志,基序号=0,投影列表=None):#构造
        """连续完整日志或已加载事件窗口。投影列表为活借用的解释器。"""
        if 投影列表 is None:#缺省无投影
            投影列表=[]#空表
        自身._日志=日志#日志窗口
        自身._基序号=基序号#窗口起点
        自身._投影列表=投影列表#活借用同一张表
        自身._状态=创建折叠状态()#折叠状态
        自身._上次处理序号=基序号-1#尚未处理窗口内事件
        自身._待提交=None#待提交计划

    def 校验下一条(自身,事件):#校验下一条
        """校验下一个候选，不改已提交表面。"""
        自身._断言投影()#定义须仍在
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上已追加
        期望序号=自身._基序号+len(自身._日志)#下一条期望序号
        自身._待提交={#暂存计划
            'event':事件,#候选
            'expectedSeq':期望序号,#期望序号
            'plan':计划表面事件(自身._状态,事件,期望序号,自身._日志,自身._基序号,自身._投影列表),#纯计划
        }#暂存计划

    @property#替换代数
    def replaceGeneration(自身):#替换代数
        """已折叠位置替换的单调计数。"""
        自身._断言投影()#定义须仍在
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上
        return 自身._状态['replaceGeneration']#返回代数

    @property#内容代数
    def contentGeneration(自身):#内容代数
        """已提交替换与插件拥有消息改写的单调计数。"""
        自身._断言投影()#定义须仍在
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上
        return 自身._状态['contentGeneration']#返回代数

    def 派生事件消息(自身,事件):#投影一条事件
        """把已提交消息投影应用到一条事件。"""
        自身._断言投影()#定义须仍在
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上
        return 事件派生消息(事件,自身._状态['projectedMessages'])#带投影表派生

    @property#表面节点
    def nodes(自身):#表面节点
        """模型可见顺序的表面事件序号。"""
        自身._断言投影()#定义须仍在
        if 自身._上次处理序号<自身._基序号+len(自身._日志)-1:#尚未追上
            自身._追上增量()#先追上
        return 自身._状态['nodes']#返回节点

    def _追上增量(自身):#追上增量
        """折叠自上次访问以来追加的事件。"""
        末序号=自身._基序号+len(自身._日志)-1#窗口末序号
        序号=自身._上次处理序号+1#从下一条起
        while 序号<=末序号:#逐条追上
            下标=序号-自身._基序号#窗口下标
            事件=自身._日志[下标]#取出事件
            待提交=自身._待提交#待提交计划
            if 待提交 is not None and 待提交['event'] is 事件 and 待提交['expectedSeq']==序号:#正好是已校验候选
                应用表面计划(自身._状态,待提交['plan'])#提交计划
            else:#普通追加
                应用表面事件(自身._状态,事件,序号,自身._日志,自身._基序号,自身._投影列表)#现场计划并提交
            if 待提交 is not None and 待提交['expectedSeq']<=序号:#过期计划
                自身._待提交=None#过期计划清掉
            自身._上次处理序号=序号#记下已处理
            序号+=1#下一条

    def _断言投影(自身):#缓存不得长过解释器寿命
        """已用定义被卸下则拒绝继续派生。"""
        候选=自身._待提交#待提交计划
        待用=None#待提交投影计划
        if 候选 is not None:#有候选
            下标=候选['expectedSeq']-自身._基序号#窗口下标
            if 0<=下标<len(自身._日志) and 自身._日志[下标] is 候选['event']:#候选已进日志
                待用=候选['plan']#用该计划
        已用=list(自身._状态['projections'])#已提交定义
        if 待用 is not None and 待用['kind']=='project':#待提交也是投影
            已用.append(待用['projection'])#一并检查
        for 投影 in 已用:#每条已用定义
            if not any(项 is 投影 for 项 in 自身._投影列表):#被卸下或替换
                raise 表面错误('session message projection "'+str(投影['type'])+'" was removed or replaced; restore the session with its owning plugin')#须恢复插件
