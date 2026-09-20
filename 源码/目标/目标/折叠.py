"""持久目标变更的纯回放折叠与严格解码器。"""
import json,math,re#JSON 片段、安全整数、阻塞码正则

from .运行时 import 目标变更版本,目标标识#载荷版本与目标 id 品牌

快照操作集合=set(('create','edit','pause','resume','complete','block'))#允许的非清除操作
阶段集合=set(('active','paused','blocked','complete'))#合法持久阶段
阻塞码模式=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z',re.ASCII)#小写短横线分类码
安全整数上界=9007199254740991#JSON 入口安全整数上界

class 目标折叠错误(Exception):
    """持久目标变更解码或回放失败。"""

def 空目标折叠状态():
    """构造空的回放累加器。没有当前目标或先前引用的可变状态。"""
    return {#全缺席
        'goal':None,#尚无当前目标
        'roundsStarted':0,#轮次从零计
        'createdAt':None,#无创建时间
        'updatedAt':None,#无变更时间
        'lastRef':None,#无最近引用
        'seenGoalIds':set(),#尚未见过任何 id
    }#结束空状态

def 是记录(值):
    """值是否为 JSON 记录而非数组。"""
    return isinstance(值,dict)#映射即记录

def 正整数(值,字段):
    """数据入口：要求一个正安全整数。"""
    if isinstance(值,bool):#布尔不是数字
        raise 目标折叠错误('goal change '+字段+' must be a positive safe integer')#按字段名失败
    if isinstance(值,int):#整数
        合法=值>=1 and 值<=安全整数上界#正且安全
    elif isinstance(值,float) and 值.is_integer() and math.isfinite(值):#整值浮点
        合法=值>=1 and 值<=安全整数上界#正且安全
    else:#其它
        合法=False#非法
    if not 合法:#非正安全整数
        raise 目标折叠错误('goal change '+字段+' must be a positive safe integer')#按字段名失败
    return int(值)#已校验正数

def 非负整数(值,字段):
    """数据入口：要求一个非负安全整数。"""
    if isinstance(值,bool):#布尔不是数字
        raise 目标折叠错误('goal change '+字段+' must be a non-negative safe integer')#按字段名失败
    if isinstance(值,int):#整数
        合法=值>=0 and 值<=安全整数上界#非负且安全
    elif isinstance(值,float) and 值.is_integer() and math.isfinite(值):#整值浮点
        合法=值>=0 and 值<=安全整数上界#非负且安全
    else:#其它
        合法=False#非法
    if not 合法:#负或非安全整数
        raise 目标折叠错误('goal change '+字段+' must be a non-negative safe integer')#按字段名失败
    return int(值)#已校验非负

def 解码阻塞原因(值):
    """解码一条规范阻塞说明。"""
    if (not 是记录(值)) or ','.join(sorted(值.keys()))!='code,message':#键必须恰好这两个
        raise 目标折叠错误('goal change goal.blockedReason must have exactly code and message fields')#键集不对
    码=值['code']#分类码
    说明=值['message']#说明
    if (not isinstance(码,str)) or 阻塞码模式.match(码) is None:#小写短横线
        raise 目标折叠错误('goal change goal.blockedReason.code must be lower-kebab-case')#分类码非法
    if (not isinstance(说明,str)) or len(说明.strip())==0 or 说明!=说明.strip():#非空且已规范化
        raise 目标折叠错误('goal change goal.blockedReason.message must be non-empty and normalized')#说明非法
    return {'code':码,'message':说明}#已校验原因

def 解码快照(值):
    """解码并校验一份快照。"""
    if not 是记录(值):#必须是记录
        raise 目标折叠错误('goal change goal must be a record')#必须是记录
    标识=值['id'] if 'id' in 值 else None#id
    if (not isinstance(标识,str)) or len(标识)==0:#非空字符串 id
        raise 目标折叠错误('goal change goal.id must be a non-empty string')#id 非法
    陈述=值['objective'] if 'objective' in 值 else None#陈述
    if (not isinstance(陈述,str)) or len(陈述.strip())==0 or 陈述!=陈述.strip():#非空且已规范化
        raise 目标折叠错误('goal change goal.objective must be non-empty and normalized')#陈述非法
    阶段=值['phase'] if 'phase' in 值 else None#阶段
    if (not isinstance(阶段,str)) or 阶段 not in 阶段集合:#阶段必须合法
        raise 目标折叠错误('goal change goal.phase is invalid')#阶段非法
    if 阶段=='blocked':#阻塞必须带原因
        期望键='blockedReason,id,maxGoalRounds,objective,phase,revision'#阻塞键集
    else:#其余键集
        期望键='id,maxGoalRounds,objective,phase,revision'#其余键集
    if ','.join(sorted(值.keys()))!=期望键:#键必须恰好匹配阶段
        raise 目标折叠错误('goal change goal for phase '+阶段+' must have exactly '+期望键+' fields')#键集不对
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

def 解码引用(值):
    """解码并校验一份引用。"""
    if (not 是记录(值)) or ','.join(sorted(值.keys()))!='id,revision':#恰好两键
        raise 目标折叠错误('goal clear tombstone must have exactly id and revision fields')#键集不对
    标识=值['id'] if 'id' in 值 else None#id
    if (not isinstance(标识,str)) or len(标识)==0:#非空 id
        raise 目标折叠错误('goal clear tombstone id must be a non-empty string')#id 非法
    return {'id':目标标识(值['id']),'revision':正整数(值['revision'],'cleared.revision')}#品牌加正数修订

def 解码目标变更(值):
    """解码自称目标变更的值。无关值返回 None；畸形目标变更让回放大声失败。"""
    if (not 是记录(值)) or ('kind' not in 值) or 值['kind']!='goal/change':#不是本事件
        return None#放过
    版本=值['version'] if 'version' in 值 else None#版本
    if 版本!=目标变更版本:#版本必须钉死
        raise 目标折叠错误('unsupported goal change version '+str(版本))#未知版本
    操作=值['operation'] if 'operation' in 值 else None#操作
    if 操作=='clear':#清除墓碑
        允许=sorted(['cleared','clearedAt','kind','operation','version'])#墓碑允许键
        if sorted(值.keys())!=允许:#键必须恰好这些
            raise 目标折叠错误('goal clear change must have exactly '+','.join(允许)+' fields')#键集不对
        return {#已校验墓碑
            'kind':'goal/change',#事件标签
            'version':目标变更版本,#当前版本
            'operation':'clear',#清除
            'cleared':解码引用(值['cleared']),#墓碑引用
            'clearedAt':非负整数(值['clearedAt'],'clearedAt'),#清除时间
        }#结束墓碑
    if (not isinstance(操作,str)) or 操作 not in 快照操作集合:#操作必须是已知快照动词
        raise 目标折叠错误('goal change operation is invalid')#操作非法
    允许=sorted(['createdAt','goal','kind','operation','roundsStarted','updatedAt','version'])#快照允许键
    if sorted(值.keys())!=允许:#键必须恰好这些
        raise 目标折叠错误('goal snapshot change must have exactly '+','.join(允许)+' fields')#键集不对
    创建于=非负整数(值['createdAt'],'createdAt')#创建时间
    更新于=非负整数(值['updatedAt'],'updatedAt')#变更时间
    if 更新于<创建于:#时间倒退
        raise 目标折叠错误('goal change updatedAt cannot precede createdAt')#时间倒退
    return {#已校验整快照变更
        'kind':'goal/change',#事件标签
        'version':目标变更版本,#当前版本
        'operation':操作,#已收窄操作
        'goal':解码快照(值['goal']),#完整快照
        'roundsStarted':非负整数(值['roundsStarted'],'roundsStarted'),#已接纳轮次
        'createdAt':创建于,#创建时间
        'updatedAt':更新于,#变更时间
    }#结束快照变更

def 目标来源(来源):
    """把模型归因收窄成合法目标来源。来源是 dict 或 None。"""
    if 来源 is None:#缺席
        return None#放过
    种类=来源['kind'] if 'kind' in 来源 else None#种类
    if 种类!='goal':#其它来源
        return None#放过
    目标号=来源['goalId'] if 'goalId' in 来源 else None#目标 id
    修订=来源['revision'] if 'revision' in 来源 else None#修订
    轮次=来源['round'] if 'round' in 来源 else None#轮次
    if (not isinstance(目标号,str)) or len(目标号)==0:#id 非法
        raise 目标折叠错误('goal message source is invalid')#来源畸形
    try:#修订与轮次走入口整数
        已修订=正整数(修订,'source.revision')#修订
        已轮次=正整数(轮次,'source.round')#轮次
    except 目标折叠错误:#入口失败
        raise 目标折叠错误('goal message source is invalid')#来源畸形
    return {'kind':'goal','goalId':目标号,'revision':已修订,'round':已轮次}#已收窄

def 要求同一定义(当前,下一,操作):
    """要求两份快照保留只有 edit 才能替换的字段。"""
    if 下一['objective']!=当前['objective'] or 下一['maxGoalRounds']!=当前['maxGoalRounds']:#被改了
        raise 目标折叠错误('goal '+操作+' cannot change objective or maxGoalRounds')#非 edit 禁止改定义

def 要求下一修订(当前,下一,操作):
    """要求恰好是当前目标的下一修订。"""
    if 下一['id']!=当前['id'] or 下一['revision']!=当前['revision']+1:#身份或步进不对
        raise 目标折叠错误('goal '+操作+' must advance the current goal by one revision')#比较交换失败

def 校验快照迁移(状态,变更,当前):
    """用前一投影校验一次非创建快照操作。"""
    下一=变更['goal']#下一快照
    要求下一修订(当前,下一,变更['operation'])#修订必须 +1
    if 状态['updatedAt'] is None:#缺时间戳
        raise 目标折叠错误('current goal fold lacks updatedAt')#缺时间戳
    if 变更['createdAt']!=状态['createdAt'] or 变更['updatedAt']<状态['updatedAt'] or 变更['roundsStarted']!=状态['roundsStarted']:#计数或时间被改
        raise 目标折叠错误('goal '+变更['operation']+' does not preserve the current counters and timestamps')#计数或时间被改
    操作=变更['operation']#动词
    if 操作=='edit':#编辑只改定义
        当前原因=当前['blockedReason'] if 'blockedReason' in 当前 else None#当前阻塞原因
        下一原因=下一['blockedReason'] if 'blockedReason' in 下一 else None#下一阻塞原因
        if 下一['phase']!=当前['phase'] or json.dumps(下一原因,ensure_ascii=False,separators=(',',':'),allow_nan=False)!=json.dumps(当前原因,ensure_ascii=False,separators=(',',':'),allow_nan=False):#阶段或原因被改
            raise 目标折叠错误('goal edit cannot change phase or blocked reason')#编辑越权
        return edit
    if 操作=='pause':#暂停
        要求同一定义(当前,下一,操作)#不得改定义
        if 当前['phase']!='active' or 下一['phase']!='paused':#必须 active→paused
            raise 目标折叠错误('goal pause has an invalid phase transition')#阶段非法
        return pause
    if 操作=='resume':#恢复
        要求同一定义(当前,下一,操作)#不得改定义
        可恢复=set(('active','paused','blocked'))#可恢复阶段
        if 当前['phase'] not in 可恢复 or 下一['phase']!='active' or 状态['roundsStarted']>=下一['maxGoalRounds']:#阶段或预算非法
            raise 目标折叠错误('goal resume has an invalid phase transition or exhausted round budget')#恢复失败
        return resume
    if 操作=='complete':#完成
        要求同一定义(当前,下一,操作)#不得改定义
        if 当前['phase']=='complete' or 下一['phase']!='complete':#不得从已完成再完成
            raise 目标折叠错误('goal complete has an invalid phase transition')#阶段非法
        return complete
    if 操作=='block':#阻塞
        要求同一定义(当前,下一,操作)#不得改定义
        if 当前['phase']!='active' or 下一['phase']!='blocked':#必须 active→blocked
            raise 目标折叠错误('goal block has an invalid phase transition')#阶段非法
        return block
    if 操作=='create':#创建不应走当前目标迁移
        raise 目标折叠错误('goal create cannot be validated as a current-goal transition')#走错路径
    raise 目标折叠错误('unknown goal snapshot operation')#运行时兜底

def 目标变更引用(变更):
    """返回快照或墓碑携带的修订身份。"""
    if 变更['operation']=='clear':#墓碑用 cleared
        return 变更['cleared']#清除引用
    return {'id':变更['goal']['id'],'revision':变更['goal']['revision']}#快照引用

def 应用目标变更(状态,变更):
    """校验并把一条已解码变更应用到可变累加器。"""
    引用=目标变更引用(变更)#本条引用
    if 变更['operation']=='clear':#清除
        当前=状态['goal']#必须有当前目标
        if 当前 is None:#空清除
            raise 目标折叠错误('goal clear requires a current goal')#空清除
        要求下一修订(当前,变更['cleared'],变更['operation'])#墓碑修订 +1
        if 状态['updatedAt'] is None:#缺时间戳
            raise 目标折叠错误('current goal fold lacks updatedAt')#缺时间戳
        if 变更['clearedAt']<状态['updatedAt']:#清除时间不得倒退
            raise 目标折叠错误('goal clear timestamp cannot precede the current goal update')#时间非法
        状态['goal']=None#清掉当前
        状态['roundsStarted']=0#轮次归零
        状态['createdAt']=None#清掉创建时间
        状态['updatedAt']=None#清掉变更时间
        状态['lastRef']=引用#留下墓碑引用
        return#清除结束
    if 变更['operation']=='create':#创建
        if 变更['goal']['revision']!=1 or 变更['goal']['phase']!='active' or 变更['roundsStarted']!=0 or (状态['goal'] is not None and 状态['goal']['phase']!='complete') or 变更['goal']['id'] in 状态['seenGoalIds']:#创建前置失败
            raise 目标折叠错误('goal create requires a fresh active revision-one goal with zero rounds')#创建前置失败
        状态['seenGoalIds'].add(变更['goal']['id'])#记下已见 id
    else:#非创建快照操作
        当前=状态['goal']#必须有当前目标
        if 当前 is None:#空操作
            raise 目标折叠错误('goal '+变更['operation']+' requires a current goal')#空操作
        校验快照迁移(状态,变更,当前)#按动词校验迁移
    状态['goal']=变更['goal']#安装下一快照
    状态['roundsStarted']=变更['roundsStarted']#同步轮次
    状态['createdAt']=变更['createdAt']#同步创建时间
    状态['updatedAt']=变更['updatedAt']#同步变更时间
    状态['lastRef']=引用#记下本条引用

def 应用目标事件(状态,事件):
    """把一条会话事件应用到严格持久目标折叠。事件是 dict。"""
    种类=事件['type'] if 'type' in 事件 else None#事件类型
    if 种类=='goal/change':#域自有变更
        数据=事件['data'] if 'data' in 事件 else None#载荷
        变更=解码目标变更(数据)#严格解码
        if 变更 is None:#kind 对不上
            序号=事件['seq'] if 'seq' in 事件 else None#序号
            raise 目标折叠错误('goal change at session event '+str(序号)+' has an invalid kind')#kind 对不上
        应用目标变更(状态,变更)#应用到累加器
        return#本条处理完
    if 种类=='user/message':#可能是已接纳轮次
        数据=事件['data'] if 'data' in 事件 else None#消息载荷
        来源字段=数据['source'] if (数据 is not None and 'source' in 数据) else None#来源
        来源=目标来源(来源字段)#收窄目标来源
        if 来源 is None:#其它来源忽略
            return#放过
        当前=状态['goal']#当前快照
        if 当前 is None or 当前['phase']!='active' or 来源['goalId']!=当前['id'] or 来源['revision']!=当前['revision'] or 来源['round']!=状态['roundsStarted']+1 or 来源['round']>当前['maxGoalRounds']:#轮次对不上
            序号=事件['seq'] if 'seq' in 事件 else None#序号
            raise 目标折叠错误('goal round at session event '+str(序号)+' is not the next admitted round of the active goal')#轮次对不上
        状态['roundsStarted']=来源['round']#接纳本轮

def 折叠目标(事件列表):
    """从一段连续会话事件日志折叠当前目标状态。故意不含武装。"""
    状态=空目标折叠状态()#空累加器
    for 事件 in 事件列表:#按序应用
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
