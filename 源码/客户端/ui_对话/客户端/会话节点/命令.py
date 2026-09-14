from ..服务 import 对话错误#本包异常
from .节点工厂 import 聊天节点#聊天节点工厂
from .事件面 import 是替换面事件#面辅助

__all__=['命令定义','登记命令会话节点','压缩来源','压缩摘要','更新压缩状态']#仅中文公开名

压缩插件='compact'#压缩插件名

def 自运行建命令(匹配项):
    """起始必须是 command/run。"""
    事件=匹配项['event']#事件
    if 事件['type']!='command/run':#必须
        raise 对话错误('command start requires command/run')#硬失败
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    参数=数据['args'] if 'args' in 数据 else None#参数
    return {#斜杠命令
        'kind':'command',#种
        'seq':事件['seq'],#序号
        'time':事件['time'] if 'time' in 事件 else None,#时刻
        'commandId':数据['commandId'] if 'commandId' in 数据 else None,#身份
        'name':数据['name'] if 'name' in 数据 else None,#名
        'args':参数,#参数
        'outcome':None,#尚未完成
    }#结束

def 自完成叠命令(匹配项,先前=None):
    """更新必须是 command/done。"""
    事件=匹配项['event']#事件
    if 事件['type']!='command/done':#必须
        raise 对话错误('command update requires command/done')#硬失败
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    源序号=None#源事件序号
    if 'kind' in 数据 and 数据['kind']=='success':#成功才可能带
        候选=数据['sourceEventSeq'] if 'sourceEventSeq' in 数据 else None#候选
        if isinstance(候选,int) and not isinstance(候选,bool) and 候选>=0:#非负
            源序号=候选#采纳
    结局={'kind':数据['kind'] if 'kind' in 数据 else None}#结局
    if 'text' in 数据 and 数据['text'] is not None:#有正文
        结局['text']=数据['text']#带上
    if 源序号 is not None:#有源序号
        结局['sourceEventSeq']=源序号#带上
    return {#叠结局
        'kind':'command',#种
        'seq':先前['seq'] if 先前 is not None else 事件['seq'],#保留起始
        'time':先前['time'] if 先前 is not None and 'time' in 先前 else (事件['time'] if 'time' in 事件 else None),#保留起始
        'commandId':数据['commandId'] if 'commandId' in 数据 else None,#身份
        'name':先前['name'] if 先前 is not None and 'name' in 先前 else None,#保留名
        'args':先前['args'] if 先前 is not None and 'args' in 先前 else None,#保留参数
        'outcome':结局,#结局
    }#结束

def 压缩来源(事件):
    """对不上则 None。"""
    if 事件['type']!='user/message' or not 是替换面事件(事件):#非
        return None#对不上
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    来源=数据['source'] if 'source' in 数据 and 数据['source'] is not None else {}#来源
    if ('kind' not in 来源) or 来源['kind']!='plugin' or ('plugin' not in 来源) or 来源['plugin']!=压缩插件:#非 compact
        return None#对不上
    压缩标识=来源['compactionId'] if 'compactionId' in 来源 else None#压缩 id
    if not isinstance(压缩标识,str):#非串
        return None#对不上
    出={'compactionId':压缩标识}#关联
    if 'sourceCommandId' in 来源 and 来源['sourceCommandId'] is not None:#有
        出['sourceCommandId']=来源['sourceCommandId']#带上
    return 出#关联身份

def 压缩摘要(匹配项,检查点):
    """摘要与遮蔽读数。"""
    摘要=None#正文
    遮蔽条=None#条目数
    遮蔽令牌=None#token 数
    事件=匹配项['event'] if 匹配项 is not None and 'event' in 匹配项 else None#摘要事件
    if 事件 is not None and 事件['type']=='compaction/summary':#有摘要
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        原文=数据['summary'] if 'summary' in 数据 else None#摘要
        if isinstance(原文,list):#块数组
            文=''#拼
            for 块 in 原文:#扫
                if 'type' in 块 and 块['type']=='text':#文本
                    文+=块['text'] if 'text' in 块 and 块['text'] is not None else ''#拼
            摘要=None if 文.strip()=='' else 文#全空白则 null
        序号列表=数据['shadowedSeqs'] if 'shadowedSeqs' in 数据 else None#遮蔽序号
        if isinstance(序号列表,list) and all(isinstance(序,int) and not isinstance(序,bool) and 序>=0 for 序 in 序号列表):#合法
            遮蔽条=len(序号列表)#条数
        令牌数=数据['shadowedTokenCount'] if 'shadowedTokenCount' in 数据 else None#token
        if isinstance(令牌数,int) and not isinstance(令牌数,bool) and 令牌数>=0:#合法
            遮蔽令牌=令牌数#采纳
    检查事件=检查点['event']#检查点事件
    return {#压缩摘要节点
        'kind':'compaction',#种
        'seq':检查事件['seq'],#检查点序号
        'time':检查事件['time'] if 'time' in 检查事件 else None,#时刻
        'summary':摘要,#正文
        'summaryEventSeq':事件['seq'] if 事件 is not None else None,#摘要序号
        'shadowedItemCount':遮蔽条,#条目
        'shadowedTokenCount':遮蔽令牌,#token
    }#结束

def 更新压缩状态(态,匹配项):
    """未增加证据则保持引用。"""
    事件=匹配项['event']#事件
    if 事件['type']=='compaction/summary':#摘要
        return {**态,'summary':匹配项}#写入
    if 压缩来源(事件) is not None:#检查点
        return {**态,'checkpoint':匹配项}#写入
    return 态#保持

def 回放命令(上下文):
    """done / 检查点 / 摘要。"""
    匹配列表=上下文['matches'] if 'matches' in 上下文 else []#匹配
    完成=None#done
    检查点=None#检查点
    摘要=None#摘要
    for 候 in 匹配列表:#扫
        候事件=候['event'] if 'event' in 候 else {}#事件
        if 完成 is None and 候事件['type']=='command/done':#done
            完成=候#记下
        if 检查点 is None and 压缩来源(候事件) is not None:#检查点
            检查点=候#记下
        if 摘要 is None and 候事件['type']=='compaction/summary':#摘要
            摘要=候#记下
    if 检查点 is None:#无检查点
        return None if 完成 is None else {'command':自完成叠命令(完成)}#只回放命令
    源=压缩来源(检查点['event'])#关联
    if 源 is None or 'sourceCommandId' not in 源 or 源['sourceCommandId'] is None:#未挂命令
        return None if 完成 is None else {'command':自完成叠命令(完成)}#只回放命令
    检查事件=检查点['event']#检查点事件
    if 完成 is None:#合成 compact 命令
        命令={#合成
            'kind':'command','seq':检查事件['seq'],#序号
            'time':检查事件['time'] if 'time' in 检查事件 else None,#时刻
            'commandId':源['sourceCommandId'],'name':'compact','args':None,'outcome':None,#compact
        }#结束
    else:#有 done
        命令={**自完成叠命令(完成),'name':'compact'}#叠名
    态={'command':命令,'checkpoint':检查点}#回放
    if 摘要 is not None:#有摘要
        态['summary']=摘要#带上
    return 态#回放态

def 命令匹配(事件):
    """run/done；检查点挂命令；压缩生命周期挂源命令。"""
    种=事件['type']#种
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 种=='command/run':#开始
        return {'id':str(数据['commandId']),'role':'start'}#起始
    if 种=='command/done':#结束
        return {'id':str(数据['commandId']),'role':'update'}#更新
    检查=压缩来源(事件)#检查点
    if 检查 is not None and 'sourceCommandId' in 检查 and 检查['sourceCommandId'] is not None:#挂命令
        return {'id':str(检查['sourceCommandId']),'role':'update'}#更新
    if 种 in ('compaction/start','compaction/summary','compaction/end'):#压缩生命周期
        源命令=数据['sourceCommandId'] if 'sourceCommandId' in 数据 else None#源命令
        if 源命令 is not None:#有
            return {'id':str(源命令),'role':'update'}#更新
    return None#对不上

def 命令开始(_上下文,匹配项):
    """起始状态。"""
    return {'command':自运行建命令(匹配项)}#命令

def 命令更新(上下文,匹配项):
    """done 叠结局；其余压缩证据。"""
    事件=匹配项['event']#事件
    态=上下文['state']#态
    if 事件['type']=='command/done':#结束
        先前命令=态['command'] if 'command' in 态 else None#先前
        return {**态,'command':自完成叠命令(匹配项,先前命令)}#叠结局
    return 更新压缩状态(态,匹配项)#压缩证据

def 命令建视图(上下文):
    """普通命令或手动压缩。"""
    态=上下文['state'] if 'state' in 上下文 else None#态
    if 态 is None:#无
        态=回放命令(上下文)#回放
    if 态 is None:#无
        return None#不建
    命令=态['command']#命令
    if 命令['name']!='compact':#普通
        return 聊天节点(上下文,'command',命令['seq'],命令)#普通命令
    摘要匹配=态['summary'] if 'summary' in 态 else None#摘要
    压缩=None if 'checkpoint' not in 态 or 态['checkpoint'] is None else 压缩摘要(摘要匹配,态['checkpoint'])#摘要标记
    数据={'command':命令,'compaction':压缩}#合在一起
    锚=压缩['seq'] if 压缩 is not None else 命令['seq']#锚
    return 聊天节点(上下文,'manual-compaction',锚,数据)#手动压缩

命令定义={#斜杠命令生命周期定义
    'kind':'command','target':'chat',#kind/目标
    'match':命令匹配,'start':命令开始,'update':命令更新,'buildViewNode':命令建视图,#生命周期
}#结束

def 登记命令会话节点(上下文):
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(命令定义)#登记
