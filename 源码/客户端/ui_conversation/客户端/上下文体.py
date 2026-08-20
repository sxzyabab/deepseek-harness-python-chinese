"""上下文披露展开体：按 durable form 分发呈现。

对齐上游 `ui-conversation/src/client/chat/ContextBody.tsx`。公开面仅中文名。
未知/畸形 form 一律不透明体；列表全有或全无。
"""
import json as 编码#紧凑 JSON

__all__=[#公开面
    '上下文体','不透明体','选上下文体','最大字符','最大条目',
    '内容游程','为记录','指令变更','目录条目','快照段','召回会话',
]#公开面结束

最大字符=20000#正文界
最大条目=200#列表界

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 为记录(值):#可读记录形
    """非对象或数组则 None。"""
    return 值 if isinstance(值,dict) else None#记

def 有界文本(文本,翻译):#截断
    """超界附 truncated 标。"""
    if len(文本)<=最大字符:#未超
        return 文本#原文
    return f"{文本[:最大字符]}\n{翻译('json.truncated',{'total':len(文本)})}"#截

def 字段值(值,翻译):#源字段呈现
    """串/数/布尔原文；其余 JSON。"""
    if isinstance(值,str):#串
        文=值#文
    elif isinstance(值,(int,float,bool)):#标量
        文=str(值)#串
    else:#结构
        文=编码.dumps(值,ensure_ascii=False)#JSON
    return 有界文本(文,翻译)#界

def 内容游程(内容):#模型面游程
    """相邻 text 合并；未知块打断。"""
    游程=[]#游
    for 块 in (内容 or []):#逐块
        if 取字段(块,'type')!='text':#未知
            游程.append({'block':块})#块
            continue#下
        文=取字段(块,'text') or ''#文
        if 游程 and 'text' in 游程[-1]:#并
            游程[-1]['text']+=文#拼
        else:#新
            游程.append({'text':文})#段
    return 游程#序

def 未知块们(内容):#仅未知
    """抽 block 游程。"""
    return [游['block'] for 游 in 内容游程(内容) if 'block' in 游]#块

def 模型面内容(内容,翻译):#共享正文
    """text pre + 未知 JsonBlock。"""
    段=[]#段
    for 索引,游 in enumerate(内容游程(内容)):#逐游
        if 'text' in 游:#正文
            if 游['text']!='':#非空
                段.append({'type':'pre','className':'text','text':有界文本(游['text'],翻译),'key':索引})#pre
        else:#未知
            段.append({#JSON
                'type':'JsonBlock','key':索引,'label':翻译('message.unknownBlock'),
                'payload':游['block'],
            })#结束
    return 段#段

def 未知块视图(块们,翻译):#未知块列表
    """每块一个 JsonBlock。"""
    return [{#块
        'type':'JsonBlock','label':翻译('message.unknownBlock'),'payload':块,
    } for 块 in 块们]#表

def 源字段(源,已渲染表单,翻译):#键值表
    """kind 恒隐；专属体再隐 form。"""
    记录=为记录(源)#记
    if 记录 is None:#无
        return None#空
    隐藏={'kind','form'} if 已渲染表单 else {'kind'}#隐
    行=[(键,值) for 键,值 in 记录.items() if 键 not in 隐藏]#行
    if len(行)==0:#空
        return None#空
    return {#dl
        'type':'fields','className':'fields',
        'rows':[{'key':键,'value':字段值(值,翻译)} for 键,值 in 行],
    }#结束

def 不透明体(内容,源,翻译):#默认体
    """模型面 + 源字段（保留 form）。"""
    return {'type':'opaque-body','content':模型面内容(内容,翻译),'fields':源字段(源,False,翻译)}#体

def 指令变更(源):#instructions changes
    """全有或全无。"""
    记录=为记录(源)#记
    列表=记录.get('changes') if 记录 is not None else None#表
    if not isinstance(列表,list):#非表
        return None#否
    变更=[]#出
    见过=set()#去重
    for 项 in 列表:#逐项
        条=为记录(项)#记
        if 条 is None:#坏
            return None#全否
        路径=条.get('path')#路
        if not isinstance(路径,str) or 路径=='':#坏
            return None#否
        动作=条.get('action')#动
        if 动作 not in ('set','replace','remove'):#坏
            return None#否
        if 路径 in 见过:#重
            continue#跳
        见过.add(路径)#记
        行={'action':动作,'path':路径}#行
        if isinstance(条.get('digest'),str):#摘要
            行['digest']=条['digest']#附
        变更.append(行)#加
    return None if len(变更)==0 else 变更#出

def 指令动作键(动作,基线):#文案键
    """remove / loaded / added / updated。"""
    if 动作=='remove':#删
        return 'message.context.instructions.removed'#删
    if 基线:#基线
        return 'message.context.instructions.loaded'#载
    return 'message.context.instructions.added' if 动作=='set' else 'message.context.instructions.updated'#增改

def 指令体(内容,源,翻译):#instructions
    """文件表 + 模型面。"""
    变更=指令变更(源)#变
    if 变更 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    记录=为记录(源) or {}#记
    基线=记录.get('baseline') is True#基线
    return {#体
        'type':'instructions-body',#类型
        'files':[{'path':变['path'],'digest':变.get('digest'),'actionLabel':翻译(指令动作键(变['action'],基线))} for 变 in 变更],
        'content':模型面内容(内容,翻译),#面
    }#结束

def 目录条目(源):#catalog
    """空表仍是真目录；不可读才 None。"""
    记录=为记录(源)#记
    列表=记录.get('entries') if 记录 is not None else None#表
    if not isinstance(列表,list):#非
        return None#否
    出=[]#出
    for 项 in 列表:#逐
        条=为记录(项)#记
        if 条 is None:#坏
            return None#否
        名=条.get('name')#名
        描=条.get('description')#描
        if not isinstance(名,str) or 名=='' or not isinstance(描,str):#坏
            return None#否
        出.append({'name':名,'description':描})#加
    return 出#可空表

def 目录体(内容,源,翻译):#catalog
    """条目表；超界摘要。"""
    条目=目录条目(源)#条
    if 条目 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    记录=为记录(源) or {}#记
    更新=记录.get('update') is True#替换告示
    可见=条目[:最大条目]#可见
    余=len(条目)-len(可见)#余
    return {#体
        'type':'catalog-body',#类型
        'updateNotice':翻译('message.context.catalog.replaced') if 更新 else None,#告示
        'entries':可见,#条
        'more':翻译('message.context.catalog.more',{'count':余}) if 余>0 else None,#余
        'unknown':未知块视图(未知块们(内容),翻译),#未知
    }#结束

def 快照段(源):#snapshot sections
    """全有或全无。"""
    记录=为记录(源)#记
    列表=记录.get('sections') if 记录 is not None else None#表
    if not isinstance(列表,list):#非
        return None#否
    出=[]#出
    for 项 in 列表:#逐
        条=为记录(项)#记
        if 条 is None:#坏
            return None#否
        名=条.get('name')#名
        文=条.get('text')#文
        if not isinstance(名,str) or 名=='' or not isinstance(文,str):#坏
            return None#否
        出.append({'name':名,'text':文})#加
    return None if len(出)==0 else 出#出

def 快照体(内容,源,翻译):#snapshot
    """取代告示 + 分段。"""
    段们=快照段(源)#段
    if 段们 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    return {#体
        'type':'snapshot-body',#类型
        'supersedes':翻译('message.context.snapshot.supersedes'),#告示
        'sections':[{'name':段['name'],'text':有界文本(段['text'],翻译)} for 段 in 段们],#段
    }#结束

def 通知摘要(源):#notice summary
    """折叠行一文。"""
    摘要=(为记录(源) or {}).get('summary')#摘要
    return 摘要 if isinstance(摘要,str) and 摘要!='' else None#出

def 通知体(内容,翻译):#notice
    """仅模型面。"""
    return {'type':'notice-body','content':模型面内容(内容,翻译)}#体

def 中继发送方(源):#relay sender
    """senderSessionId。"""
    发=(为记录(源) or {}).get('senderSessionId')#发
    return 发 if isinstance(发,str) and 发!='' else None#出

def 中继体(内容,源,翻译):#relay
    """发送方 + 模型面。"""
    发=中继发送方(源)#发
    if 发 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    return {#体
        'type':'relay-body',#类型
        'sender':翻译('message.context.relay.from',{'session':发}),#发
        'content':模型面内容(内容,翻译),#面
    }#结束

def 召回会话(源):#recall references
    """全有或全无。"""
    记录=为记录(源)#记
    列表=记录.get('references') if 记录 is not None else None#表
    if not isinstance(列表,list):#非
        return None#否
    出=[]#出
    for 项 in 列表:#逐
        条=为记录(项)#记
        if 条 is None:#坏
            return None#否
        标=条.get('label')#标
        留=条.get('retainedMessages')#留
        略=条.get('omittedMessages')#略
        截=条.get('truncated')#截
        if not isinstance(标,str) or 标=='' or not isinstance(留,(int,float)) or not isinstance(略,(int,float)) or not isinstance(截,bool):#坏
            return None#否
        出.append({'label':标,'retained':留,'omitted':略,'truncated':截})#加
    return None if len(出)==0 else 出#出

def 召回体(内容,源,翻译):#recall
    """会话完整度 + 模型面。"""
    会话们=召回会话(源)#会
    if 会话们 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    行=[]#行
    for 会 in 会话们:#逐
        项={'label':会['label'],'counts':翻译('message.context.recall.counts',{'retained':会['retained'],'omitted':会['omitted']})}#项
        if 会['truncated']:#截
            项['truncated']=翻译('message.context.recall.truncated')#截标
        行.append(项)#加
    return {'type':'recall-body','sessions':行,'content':模型面内容(内容,翻译)}#体

def 选上下文体(表单,内容,源,翻译):#contextBody
    """返回 rendered/summary/body；不可读回退 opaque。"""
    不透={'rendered':None,'summary':None,'body':不透明体(内容,源,翻译)}#opaque
    if 表单=='instructions':#指令
        return 不透 if 指令变更(源) is None else {'rendered':'instructions','summary':None,'body':指令体(内容,源,翻译)}#出
    if 表单=='catalog':#目录
        return 不透 if 目录条目(源) is None else {'rendered':'catalog','summary':None,'body':目录体(内容,源,翻译)}#出
    if 表单=='snapshot':#快照
        return 不透 if 快照段(源) is None else {'rendered':'snapshot','summary':None,'body':快照体(内容,源,翻译)}#出
    if 表单=='notice':#通知
        摘要=通知摘要(源)#摘要
        return 不透 if 摘要 is None else {'rendered':'notice','summary':摘要,'body':通知体(内容,翻译)}#出
    if 表单=='relay':#中继
        return 不透 if 中继发送方(源) is None else {'rendered':'relay','summary':None,'body':中继体(内容,源,翻译)}#出
    if 表单=='recall':#召回
        return 不透 if 召回会话(源) is None else {'rendered':'recall','summary':None,'body':召回体(内容,源,翻译)}#出
    if 表单 is None:#无声明
        return 不透#opaque
    raise ValueError(f'unreachable context form: {表单}')#闭联合

class 上下文体:#披露体入口
    """读节点 form 后选体。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """选体包装。"""
        属性=自身.属性#props
        内容=取字段(属性,'content') or []#内容
        源=取字段(属性,'source')#源
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        表=取字段(属性,'form')#节点声明 form；缺席即透明
        选=选上下文体(表,内容,源,翻译)#选
        return {#根
            'type':'context-body',#类型
            'rendered':选['rendered'],#实渲 form
            'summary':选['summary'],#折叠摘要
            'body':选['body'],#体
            'cssModule':'聊天/上下文体.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
