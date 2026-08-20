"""持久目标变更的纯回放折叠与严格解码器。"""
import json,math,re#JSON 片段、安全整数、阻塞码正则
from .运行时 import 目标变更版本,目标标识#载荷版本与目标 id 品牌

快照操作集合=set(('create','edit','pause','resume','complete','block'))#允许的非清除操作
阶段集合=set(('active','paused','blocked','complete'))#合法持久阶段
阻塞码模式=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')#小写短横线分类码

def 空目标折叠状态():#构造空的回放累加器
    """构造空的回放累加器。没有当前目标或先前引用的可变状态。"""
    return {#全缺席
        'goal':None,#尚无当前目标
        'roundsStarted':0,#轮次从零计
        'createdAt':None,#无创建时间
        'updatedAt':None,#无变更时间
        'lastRef':None,#无最近引用
        'seenGoalIds':set(),#尚未见过任何 id
    }#结束空状态

def 是否安全整数(值):#对齐 Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return -(2**53)<值<(2**53)#安全整数范围
    if isinstance(值,float):#浮点
        if not 值.is_integer():#非整值
            return False#不是整数
        return math.isfinite(值) and -(2**53)<值<(2**53)#有限且在安全范围
    return False#其它类型

def 是记录(值):#值是否为 JSON 记录而非数组
    """值是否为 JSON 记录而非数组。"""
    return isinstance(值,dict)#映射即记录

def 正整数(值,字段):#要求一个正安全整数
    """要求一个正安全整数。"""
    if (not isinstance(值,(int,float))) or isinstance(值,bool) or (not 是否安全整数(值)) or 值<1:#非正安全整数
        raise Exception('goal change '+字段+' must be a positive safe integer')#按字段名失败
    return int(值)#已校验正数

def 非负整数(值,字段):#要求一个非负安全整数
    """要求一个非负安全整数。"""
    if (not isinstance(值,(int,float))) or isinstance(值,bool) or (not 是否安全整数(值)) or 值<0:#负或非安全整数
        raise Exception('goal change '+字段+' must be a non-negative safe integer')#按字段名失败
    return int(值)#已校验非负

def 解码阻塞原因(值):#解码一条规范阻塞说明
    """解码一条规范阻塞说明。"""
    if (not 是记录(值)) or ','.join(sorted(值.keys()))!='code,message':#键必须恰好这两个
        raise Exception('goal change goal.blockedReason must have exactly code and message fields')#键集不对
    码=值['code']#分类码
    说明=值['message']#说明
    if (not isinstance(码,str)) or 阻塞码模式.match(码) is None:#小写短横线
        raise Exception('goal change goal.blockedReason.code must be lower-kebab-case')#分类码非法
    if (not isinstance(说明,str)) or len(说明.strip())==0 or 说明!=说明.strip():#非空且已规范化
        raise Exception('goal change goal.blockedReason.message must be non-empty and normalized')#说明非法
    return {'code':码,'message':说明}#已校验原因

def 解码快照(值):#解码并校验一份快照
    """解码并校验一份快照。"""
    if not 是记录(值):#必须是记录
        raise Exception('goal change goal must be a record')#必须是记录
    if (not isinstance(值.get('id'),str)) or len(值['id'])==0:#非空字符串 id
        raise Exception('goal change goal.id must be a non-empty string')#id 非法
    陈述=值.get('objective')#陈述
    if (not isinstance(陈述,str)) or len(陈述.strip())==0 or 陈述!=陈述.strip():#非空且已规范化
        raise Exception('goal change goal.objective must be non-empty and normalized')#陈述非法
    阶段=值.get('phase')#阶段
    if (not isinstance(阶段,str)) or 阶段 not in 阶段集合:#阶段必须合法
        raise Exception('goal change goal.phase is invalid')#阶段非法
    if 阶段=='blocked':#阻塞必须带原因
        期望键='blockedReason,id,maxGoalRounds,objective,phase,revision'#阻塞键集
    else:#其余键集
        期望键='id,maxGoalRounds,objective,phase,revision'#其余键集
    if ','.join(sorted(值.keys()))!=期望键:#键必须恰好匹配阶段
        raise Exception('goal change goal for phase '+阶段+' must have exactly '+期望键+' fields')#键集不对
    快照={#已校验快照
        'id':目标标识(值['id']),#打成品牌
        'revision':正整数(值['revision'],'goal.revision'),#正数修订
        'objective':陈述,#已规范化陈述
        'phase':阶段,#阶段
        'maxGoalRounds':正整数(值['maxGoalRounds'],'goal.maxGoalRounds'),#正数上限
    }#快照字段结束
    if 阶段=='blocked':#仅阻塞带原因
        快照['blockedReason']=解码阻塞原因(值['blockedReason'])#解码原因
    return 快照#已校验快照

def 解码引用(值):#解码并校验一份引用
    """解码并校验一份引用。"""
    if (not 是记录(值)) or ','.join(sorted(值.keys()))!='id,revision':#恰好两键
        raise Exception('goal clear tombstone must have exactly id and revision fields')#键集不对
    if (not isinstance(值.get('id'),str)) or len(值['id'])==0:#非空 id
        raise Exception('goal clear tombstone id must be a non-empty string')#id 非法
    return {'id':目标标识(值['id']),'revision':正整数(值['revision'],'cleared.revision')}#品牌加正数修订

def 解码目标变更(值):#解码自称目标变更的值
    """解码自称目标变更的值。无关值返回 None；畸形目标变更让回放大声失败。"""
    if (not 是记录(值)) or 值.get('kind')!='goal/change':#不是本事件
        return None#放过
    if 值.get('version')!=目标变更版本:#版本必须钉死
        raise Exception('unsupported goal change version '+str(值.get('version')))#未知版本
    if 值.get('operation')=='clear':#清除墓碑
        允许=sorted(['cleared','clearedAt','kind','operation','version'])#墓碑允许键
        if sorted(值.keys())!=允许:#键必须恰好这些
            raise Exception('goal clear change must have exactly '+','.join(允许)+' fields')#键集不对
        return {#已校验墓碑
            'kind':'goal/change',#事件标签
            'version':目标变更版本,#当前版本
            'operation':'clear',#清除
            'cleared':解码引用(值['cleared']),#墓碑引用
            'clearedAt':非负整数(值['clearedAt'],'clearedAt'),#清除时间
        }#结束墓碑
    操作=值.get('operation')#操作
    if (not isinstance(操作,str)) or 操作 not in 快照操作集合:#操作必须是已知快照动词
        raise Exception('goal change operation is invalid')#操作非法
    允许=sorted(['createdAt','goal','kind','operation','roundsStarted','updatedAt','version'])#快照允许键
    if sorted(值.keys())!=允许:#键必须恰好这些
        raise Exception('goal snapshot change must have exactly '+','.join(允许)+' fields')#键集不对
    创建于=非负整数(值['createdAt'],'createdAt')#创建时间
    更新于=非负整数(值['updatedAt'],'updatedAt')#变更时间
    if 更新于<创建于:#时间倒退
        raise Exception('goal change updatedAt cannot precede createdAt')#时间倒退
    return {#已校验整快照变更
        'kind':'goal/change',#事件标签
        'version':目标变更版本,#当前版本
        'operation':操作,#已收窄操作
        'goal':解码快照(值['goal']),#完整快照
        'roundsStarted':非负整数(值['roundsStarted'],'roundsStarted'),#已接纳轮次
        'createdAt':创建于,#创建时间
        'updatedAt':更新于,#变更时间
    }#结束快照变更

def 目标来源(来源):#把模型归因收窄成合法目标来源
    """把模型归因收窄成合法目标来源。"""
    if 来源 is None:#缺席
        return None#放过
    if isinstance(来源,dict):#映射
        种类=来源.get('kind')#种类
        目标号=来源.get('goalId')#目标 id
        修订=来源.get('revision')#修订
        轮次=来源.get('round')#轮次
    else:#对象
        种类=getattr(来源,'kind',None)#种类
        目标号=getattr(来源,'goalId',None)#目标 id
        修订=getattr(来源,'revision',None)#修订
        轮次=getattr(来源,'round',None)#轮次
    if 种类!='goal':#其它来源
        return None#放过
    if (not isinstance(目标号,str)) or len(目标号)==0 or (not 是否安全整数(修订)) or 修订<1 or (not 是否安全整数(轮次)) or 轮次<1:#来源畸形
        raise Exception('goal message source is invalid')#来源畸形
    return {'kind':'goal','goalId':目标号,'revision':修订,'round':轮次}#已收窄

def 要求同一定义(当前,下一,操作):#要求两份快照保留只有 edit 才能替换的字段
    """要求两份快照保留只有 edit 才能替换的字段。"""
    if 下一['objective']!=当前['objective'] or 下一['maxGoalRounds']!=当前['maxGoalRounds']:#被改了
        raise Exception('goal '+操作+' cannot change objective or maxGoalRounds')#非 edit 禁止改定义

def 要求下一修订(当前,下一,操作):#要求恰好是当前目标的下一修订
    """要求恰好是当前目标的下一修订。"""
    if 下一['id']!=当前['id'] or 下一['revision']!=当前['revision']+1:#身份或步进不对
        raise Exception('goal '+操作+' must advance the current goal by one revision')#比较交换失败

def 校验快照迁移(状态,变更,当前):#用前一投影校验一次非创建快照操作
    """用前一投影校验一次非创建快照操作。"""
    下一=变更['goal']#下一快照
    要求下一修订(当前,下一,变更['operation'])#修订必须 +1
    if 状态['updatedAt'] is None:#缺时间戳
        raise Exception('current goal fold lacks updatedAt')#缺时间戳
    if 变更['createdAt']!=状态['createdAt'] or 变更['updatedAt']<状态['updatedAt'] or 变更['roundsStarted']!=状态['roundsStarted']:#计数或时间被改
        raise Exception('goal '+变更['operation']+' does not preserve the current counters and timestamps')#计数或时间被改
    操作=变更['operation']#动词
    if 操作=='edit':#编辑只改定义
        当前原因=当前.get('blockedReason')#当前阻塞原因
        下一原因=下一.get('blockedReason')#下一阻塞原因
        if 下一['phase']!=当前['phase'] or json.dumps(下一原因,ensure_ascii=False)!=json.dumps(当前原因,ensure_ascii=False):#阶段或原因被改
            raise Exception('goal edit cannot change phase or blocked reason')#编辑越权
        return#结束 edit
    if 操作=='pause':#暂停
        要求同一定义(当前,下一,操作)#不得改定义
        if 当前['phase']!='active' or 下一['phase']!='paused':#必须 active→paused
            raise Exception('goal pause has an invalid phase transition')#阶段非法
        return#结束 pause
    if 操作=='resume':#恢复
        要求同一定义(当前,下一,操作)#不得改定义
        可恢复=set(('active','paused','blocked'))#可恢复阶段
        if 当前['phase'] not in 可恢复 or 下一['phase']!='active' or 状态['roundsStarted']>=下一['maxGoalRounds']:#阶段或预算非法
            raise Exception('goal resume has an invalid phase transition or exhausted round budget')#恢复失败
        return#结束 resume
    if 操作=='complete':#完成
        要求同一定义(当前,下一,操作)#不得改定义
        if 当前['phase']=='complete' or 下一['phase']!='complete':#不得从已完成再完成
            raise Exception('goal complete has an invalid phase transition')#阶段非法
        return#结束 complete
    if 操作=='block':#阻塞
        要求同一定义(当前,下一,操作)#不得改定义
        if 当前['phase']!='active' or 下一['phase']!='blocked':#必须 active→blocked
            raise Exception('goal block has an invalid phase transition')#阶段非法
        return#结束 block
    if 操作=='create':#创建不应走当前目标迁移
        raise Exception('goal create cannot be validated as a current-goal transition')#走错路径
    raise Exception('unknown goal snapshot operation')#运行时兜底

def 目标变更引用(变更):#返回快照或墓碑携带的修订身份
    """返回快照或墓碑携带的修订身份。"""
    if 变更['operation']=='clear':#墓碑用 cleared
        return 变更['cleared']#清除引用
    return {'id':变更['goal']['id'],'revision':变更['goal']['revision']}#快照引用

def 应用目标变更(状态,变更):#校验并把一条已解码变更应用到可变累加器
    """校验并把一条已解码变更应用到可变累加器。"""
    引用=目标变更引用(变更)#本条引用
    if 变更['operation']=='clear':#清除
        当前=状态['goal']#必须有当前目标
        if 当前 is None:#空清除
            raise Exception('goal clear requires a current goal')#空清除
        要求下一修订(当前,变更['cleared'],变更['operation'])#墓碑修订 +1
        if 状态['updatedAt'] is None:#缺时间戳
            raise Exception('current goal fold lacks updatedAt')#缺时间戳
        if 变更['clearedAt']<状态['updatedAt']:#清除时间不得倒退
            raise Exception('goal clear timestamp cannot precede the current goal update')#时间非法
        状态['goal']=None#清掉当前
        状态['roundsStarted']=0#轮次归零
        状态['createdAt']=None#清掉创建时间
        状态['updatedAt']=None#清掉变更时间
        状态['lastRef']=引用#留下墓碑引用
        return#清除结束
    if 变更['operation']=='create':#创建
        if 变更['goal']['revision']!=1 or 变更['goal']['phase']!='active' or 变更['roundsStarted']!=0 or (状态['goal'] is not None and 状态['goal']['phase']!='complete') or 变更['goal']['id'] in 状态['seenGoalIds']:#创建前置失败
            raise Exception('goal create requires a fresh active revision-one goal with zero rounds')#创建前置失败
        状态['seenGoalIds'].add(变更['goal']['id'])#记下已见 id
    else:#非创建快照操作
        当前=状态['goal']#必须有当前目标
        if 当前 is None:#空操作
            raise Exception('goal '+变更['operation']+' requires a current goal')#空操作
        校验快照迁移(状态,变更,当前)#按动词校验迁移
    状态['goal']=变更['goal']#安装下一快照
    状态['roundsStarted']=变更['roundsStarted']#同步轮次
    状态['createdAt']=变更['createdAt']#同步创建时间
    状态['updatedAt']=变更['updatedAt']#同步变更时间
    状态['lastRef']=引用#记下本条引用

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 应用目标事件(状态,事件):#把一条会话事件应用到严格持久目标折叠
    """把一条会话事件应用到严格持久目标折叠。"""
    种类=取字段(事件,'type')#事件类型
    if 种类=='goal/change':#域自有变更
        变更=解码目标变更(取字段(事件,'data'))#严格解码
        if 变更 is None:#kind 对不上
            raise Exception('goal change at session event '+str(取字段(事件,'seq'))+' has an invalid kind')#kind 对不上
        应用目标变更(状态,变更)#应用到累加器
        return#本条处理完
    if 种类=='user/message':#可能是已接纳轮次
        来源=目标来源(取字段(取字段(事件,'data'),'source'))#收窄目标来源
        if 来源 is None:#其它来源忽略
            return#放过
        当前=状态['goal']#当前快照
        if 当前 is None or 当前['phase']!='active' or 来源['goalId']!=当前['id'] or 来源['revision']!=当前['revision'] or 来源['round']!=状态['roundsStarted']+1 or 来源['round']>当前['maxGoalRounds']:#轮次对不上
            raise Exception('goal round at session event '+str(取字段(事件,'seq'))+' is not the next admitted round of the active goal')#轮次对不上
        状态['roundsStarted']=来源['round']#接纳本轮

def 折叠目标(事件们):#从一段连续会话事件日志折叠当前目标状态
    """从一段连续会话事件日志折叠当前目标状态。故意不含武装。"""
    状态=空目标折叠状态()#空累加器
    for 事件 in 事件们:#按序应用
        应用目标事件(状态,事件)#按序步进
    结果={'roundsStarted':状态['roundsStarted']}#已接纳轮次
    if 状态['goal'] is not None:#有则拷贝快照
        结果['goal']=dict(状态['goal'])#脱离快照
        if 'blockedReason' in 状态['goal']:#有阻塞原因
            结果['goal']['blockedReason']=dict(状态['goal']['blockedReason'])#脱离原因
    if 状态['createdAt'] is not None:#有则带创建时间
        结果['createdAt']=状态['createdAt']#创建时间
    if 状态['updatedAt'] is not None:#有则带变更时间
        结果['updatedAt']=状态['updatedAt']#变更时间
    if 状态['lastRef'] is not None:#有则拷贝引用
        结果['lastRef']=dict(状态['lastRef'])#脱离引用
    return 结果#脱离投影
