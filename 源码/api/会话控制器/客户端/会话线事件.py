"""对原始 Session 日志响应做事件局部验收；载荷仍由所有者定义的 JSON。

对齐上游 `session-controller/src/client/session-wire-event.ts`。公开面仅中文名。
替换表面操作用 startSeq/endSeq（与追踪 surface 一致）；内核导出同名校验前在此内联。
"""
import math#负零判定
from ....内核.会话.类型 import 安全整数上限#外来 JSON 安全整数
from ....内核.会话.表面 import 是否可进表面类型#表面类型词表

__all__=['断言会话线事件']#仅中文公开名

接纳键=frozenset({#线信封已接纳键
    'type','seq','time','data','ignorable','surfaceOp','sourceEventSeqs',
})#接纳键结束

def _是记录(值):#是否普通对象
    """运行时值是否为非数组对象记录。"""
    return isinstance(值,dict)#仅 dict

def _是安全整数(值):#对齐 Number.isSafeInteger
    """运行时值是否为安全整数（布尔排除；整值浮点可）。"""
    if isinstance(值,bool):#布尔不是整数
        return False#布尔
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=安全整数上限#安全范围
    return False#其它

def _是非负安全序号(值):#seq：非负安全整数且拒 -0
    """对齐线信封 seq：安全整数、非负、且 Object.is(seq, -0) 拒绝。"""
    if not _是安全整数(值):#非安全整数
        return False#拒绝
    if isinstance(值,float) and math.copysign(1.0,值)<0:#浮点负零
        return False#拒 -0
    return 值>=0#非负

def _是事件序号(值):#对齐表面 isEventSeq
    """运行时值是否为非负安全事件序号（拒 -0）。"""
    return _是非负安全序号(值)#与线 seq 同规则

def _是否替换操作(值):#是否替换操作（追踪字段）
    """运行时值是否正好是位置替换形态（op + startSeq + endSeq）。"""
    if not isinstance(值,dict):#必须是记录
        return False#必须是记录
    if len(值)!=3:#恰好三键
        return False#恰好三键
    if 'op' not in 值 or 'startSeq' not in 值 or 'endSeq' not in 值:#追踪三键
        return False#必须有这三键
    if 值['op']!='replace':#必须是 replace
        return False#必须是 replace
    return _是事件序号(值['startSeq']) and _是事件序号(值['endSeq'])#起止序号合法

def _取出表面操作(事件):#取出表面操作（事件局部）
    """校验事件本地的表面资格并返回其操作；替换键为 startSeq/endSeq。"""
    类型=事件['type'] if 'type' in 事件 else None#事件类型
    if not 是否可进表面类型(类型):#类型不可进表面
        if 'surfaceOp' in 事件:#却带了表面操作
            raise Exception('session event "'+str(类型)+'" is not surface-eligible and cannot carry surfaceOp')#非法携带
        if 'sourceEventSeqs' in 事件:#却带了源序号
            raise Exception('session event "'+str(类型)+'" is not surface-eligible and cannot carry sourceEventSeqs')#非法携带
        return None#非表面事件
    if 'surfaceOp' not in 事件:#可进表面却没有标记
        raise Exception('session event "'+str(类型)+'" is surface-eligible and requires a surfaceOp marker')#缺少标记
    操作=事件['surfaceOp']#取出操作
    if 操作=='append':#追加
        return 操作#追加
    if 操作 is None or isinstance(操作,(str,bytes,int,float,bool,list)):#不是对象
        raise Exception('session event "'+str(类型)+'" carries an invalid surfaceOp')#非法操作
    if not isinstance(操作,dict):#不是记录
        raise Exception('session event "'+str(类型)+'" carries an invalid surfaceOp')#非法操作
    if not _是否替换操作(操作):#不是合法替换
        raise Exception('session event "'+str(类型)+'" carries an invalid replace surfaceOp')#非法替换
    return 操作#合法替换

def _断言出处(事件,被遮蔽序号):#校验出处（事件局部空遮蔽）
    """按替换区间校验引用的源事件序号；线路径仅传空遮蔽。"""
    原始=事件['sourceEventSeqs'] if 'sourceEventSeqs' in 事件 else None#原始源序号
    if 事件.get('type')=='assistant/message' and 原始 is not None:#助手消息不得带源序号
        raise Exception('assistant/message embeds its source stream and cannot carry sourceEventSeqs')#禁止
    已见=set()#已见源
    if 原始 is not None:#有出处字段
        if not isinstance(原始,list):#不是数组
            raise Exception('sourceEventSeqs on event at seq '+str(事件['seq'])+' must be an array when present')#必须是数组
        if len(原始)==0:#空数组
            raise Exception('sourceEventSeqs must not be empty')#不得空
        不早源=None#不早于当前的源
        for 源 in 原始:#逐个源
            if not _是事件序号(源):#不是合法序号
                raise Exception('session event "'+str(事件['type'])+'" sourceEventSeqs must densely contain non-negative safe integers')#必须是稠密非负安全整数
            已见.add(源)#记下
            if 不早源 is None and 源>=事件['seq']:#找到不早于当前的
                不早源=源#找到不早于当前的
        if len(已见)!=len(原始):#有重复
            raise Exception('sourceEventSeqs must not contain duplicates')#不得重复
        if 不早源 is not None:#引用了不更早的事件
            raise Exception('sourceEventSeqs must reference earlier events: '+str(不早源)+' >= current seq '+str(事件['seq']))#必须引用更早事件
    缺=[]#被遮蔽却未引用
    for 序号 in 被遮蔽序号:#被遮蔽序号
        if 序号 not in 已见:#未引用
            缺.append(序号)#记下缺失
    if len(缺)>0:#缺引用
        缺文=', '.join(str(项) for 项 in 缺)#拼缺失
        raise Exception('surface replace: sourceEventSeqs must include every shadowed surface node; missing '+缺文)#必须覆盖每个被遮蔽节点

def 校验会话事件数据(事件,主语):#校验事件载荷局部
    """拒绝非规范请求头字段与自相矛盾的工具失败元数据；不校验完整载荷或内嵌提供方流。"""
    数据=事件['data'] if 'data' in 事件 else None#载荷
    类型=事件['type'] if 'type' in 事件 else None#事件名
    if 类型=='request/header':#请求头
        if not _是记录(数据):#须对象
            raise Exception(主语+' data must be an object')#非对象
        头=数据['header'] if 'header' in 数据 else None#请求头
        if not _是记录(头):#须对象
            raise Exception(主语+' header must be an object')#非对象
        if 'system' in 头:#禁止 system
            raise Exception(主语+' must omit header.system; use system/message')#改走系统消息
        工具=头['tools'] if 'tools' in 头 else None#工具表
        if isinstance(工具,list) and len(工具)==0:#空 tools
            raise Exception(主语+' must omit empty tools')#须省略
        默认=头['adapterDefaults'] if 'adapterDefaults' in 头 else None#适配器默认
        if _是记录(默认) and len(默认)==0:#空默认
            raise Exception(主语+' must omit empty adapterDefaults')#须省略
    elif 类型=='tool/result':#工具结果
        if not _是记录(数据):#须对象
            raise Exception(主语+' data must be an object')#非对象
        if 'error' not in 数据:#无失败元数据
            return#放过
        消息=数据['message'] if 'message' in 数据 else None#消息
        内容=消息['content'] if _是记录(消息) and 'content' in 消息 else None#内容块表
        块=内容[0] if isinstance(内容,list) and len(内容)>0 else None#首块
        if not _是记录(块) or 块.get('isError') is not True:#须错误块
            raise Exception(主语+' error requires message content[0].isError === true')#矛盾

def 校验表面元数据(事件):#事件局部表面元数据
    """校验一条事件的表面元数据，不查日志或表面成员资格。替换引用 startSeq/endSeq。"""
    操作=_取出表面操作(事件)#资格与标记
    if 操作 is not None and 操作!='append' and (操作['startSeq']>=事件['seq'] or 操作['endSeq']>=事件['seq']):#替换须更早
        raise Exception('surface replace at seq '+str(事件['seq'])+': startSeq and endSeq must reference earlier events')#起止须更早
    if 操作 is not None:#有表面操作
        _断言出处(事件,[])#出处局部规则（无遮蔽）
    return 操作#已校验操作或 None

def 断言会话线事件(值):#断言线协议事件
    """拒绝非当前事件信封，且不剥离、不规范化线字段。

    区间成员与出处存在性依赖耐久日志，仍属 Host。
    值：follow 帧或历史页中收到的一条事件。
    信封或当前事件局部元数据无效时抛出。
    """
    主语='session wire event'#诊断主语（线协议文案原样英文）
    if not _是记录(值):#须对象
        raise Exception(主语+' must be an object')#非对象
    事件=值#按记录检视
    for 键 in 事件.keys():#逐键验收
        if 键 not in 接纳键:#意外字段
            raise Exception(主语+' has unexpected field '+str(键))#意外字段
    序号=事件['seq'] if 'seq' in 事件 else None#序号
    if (not isinstance(事件.get('type'),str)
        or not _是非负安全序号(序号)
        or not _是安全整数(事件['time'] if 'time' in 事件 else None)
        or 'data' not in 事件
        or ('ignorable' in 事件 and 事件['ignorable'] is not True)):#信封字段
        raise Exception(主语+' has an invalid envelope')#信封无效
    # 事件名与载荷可合并扩展；此处只跑事件局部所有者规则。
    校验表面元数据(事件)#校验表面元数据
    校验会话事件数据(事件,主语)#校验事件载荷
