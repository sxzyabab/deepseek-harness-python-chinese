from ....基础设施.通用工具 import 紧凑json编码,截断utf8字节,utf8字节数

__all__=[#公开面
    '上下文体','不透明体','选上下文体','最大字节','最大条目',
    '内容游程','为记录','指令变更','目录条目','快照段','召回会话',
]#公开面结束

最大字节=20000#正文界（UTF-8 字节）
最大条目=200#列表界

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 为记录(值):
    '非对象或数组则 None'
    return 值 if isinstance(值,dict) else None#记

def 是数(值):
    '整数排除 bool'
    return (isinstance(值,int) and not isinstance(值,bool)) or isinstance(值,float)#数

def 有界文本(文本,翻译):
    '超界附 truncated 标；按 UTF-8 字节截'
    字节数=utf8字节数(文本)#预算
    if 字节数<=最大字节:#未超
        return 文本#原文
    return f"{截断utf8字节(文本,最大字节)}\n{翻译('json.truncated',{'total':字节数})}"#截

def 字段值(值,翻译):
    '串/数/布尔原文；其余 JSON'
    if isinstance(值,str):#串
        文=值#文
    elif isinstance(值,bool) or 是数(值):#标量
        文=str(值)#串
    else:#结构
        文=紧凑json编码(值)#JSON
    return 有界文本(文,翻译)#界

def 内容游程(内容):
    '相邻 text 合并；未知块打断'
    游程=[]#游
    序列=内容 if 内容 is not None else []#缺则空
    for 块 in 序列:#逐块
        种=块['type'] if 'type' in 块 else None#种
        if 种!='text':#未知
            游程.append({'block':块})#块
            continue#下
        文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文
        if len(游程)>0 and 'text' in 游程[-1]:#并
            游程[-1]['text']+=文#拼
        else:#新
            游程.append({'text':文})#段
    return 游程#序

def 收集未知块(内容):
    '抽 block 游程'
    return [游['block'] for 游 in 内容游程(内容) if 'block' in 游]#块

def 模型面内容(内容,翻译):
    'text pre + 未知 JsonBlock'
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

def 未知块视图(块列表,翻译):
    '每块一个 JsonBlock'
    return [{#块
        'type':'JsonBlock','label':翻译('message.unknownBlock'),'payload':块,
    } for 块 in 块列表]#表

def 源字段(源,已渲染表单,翻译):
    'kind 恒隐；专属体再隐 form'
    记录=为记录(源)#记
    if 记录 is None:#无
        return None#空
    隐藏={'kind','form'} if 已渲染表单 is True else {'kind'}#隐
    行=[(键,值) for 键,值 in 记录.items() if 键 not in 隐藏]#行
    if len(行)==0:#空
        return None#空
    return {#dl
        'type':'fields','className':'fields',
        'rows':[{'key':键,'value':字段值(值,翻译)} for 键,值 in 行],
    }#结束

def 不透明体(内容,源,翻译):
    '模型面 + 源字段（保留 form）'
    return {'type':'opaque-body','content':模型面内容(内容,翻译),'fields':源字段(源,False,翻译)}#体

def 指令变更(源):
    '全有或全无'
    记录=为记录(源)#记
    列表=记录['changes'] if 记录 is not None and 'changes' in 记录 else None#表
    if not isinstance(列表,list):#非表
        return None#否
    变更=[]#出
    见过=set()#去重
    for 项 in 列表:#逐项
        条=为记录(项)#记
        if 条 is None:#坏
            return None#全否
        路径=条['path'] if 'path' in 条 else None#路
        if not isinstance(路径,str) or 路径=='':#坏
            return None#否
        动作=条['action'] if 'action' in 条 else None#动
        if 动作 not in ('set','replace','remove'):#坏
            return None#否
        if 路径 in 见过:#重
            continue#跳
        见过.add(路径)#记
        行={'action':动作,'path':路径}#行
        摘要=条['digest'] if 'digest' in 条 else None#摘要
        if isinstance(摘要,str):#摘要
            行['digest']=摘要#附
        变更.append(行)#加
    return None if len(变更)==0 else 变更#出

def 指令动作键(动作,基线):
    'remove / loaded / added / updated'
    if 动作=='remove':#删
        return 'message.context.instructions.removed'#删
    if 基线 is True:#基线
        return 'message.context.instructions.loaded'#载
    return 'message.context.instructions.added' if 动作=='set' else 'message.context.instructions.updated'#增改

def 指令体(内容,源,翻译):
    '文件表 + 模型面'
    变更=指令变更(源)#变
    if 变更 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    记录=为记录(源)#记
    记=记录 if 记录 is not None else {}#记
    基线=记['baseline'] is True if 'baseline' in 记 else False#基线
    文件=[]#文件
    for 变 in 变更:#逐
        摘要=变['digest'] if 'digest' in 变 else None#摘要
        文件.append({'path':变['path'],'digest':摘要,'actionLabel':翻译(指令动作键(变['action'],基线))})#行
    return {#体
        'type':'instructions-body',#类型
        'files':文件,#文件
        'content':模型面内容(内容,翻译),#面
    }#结束

def 目录条目(源):
    '空表仍是真目录；不可读才 None'
    记录=为记录(源)#记
    列表=记录['entries'] if 记录 is not None and 'entries' in 记录 else None#表
    if not isinstance(列表,list):#非
        return None#否
    出=[]#出
    for 项 in 列表:#逐
        条=为记录(项)#记
        if 条 is None:#坏
            return None#否
        名=条['name'] if 'name' in 条 else None#名
        描=条['description'] if 'description' in 条 else None#描
        if not isinstance(名,str) or 名=='' or not isinstance(描,str):#坏
            return None#否
        出.append({'name':名,'description':描})#加
    return 出#可空表

def 目录体(内容,源,翻译):
    '条目表；超界摘要'
    条目=目录条目(源)#条
    if 条目 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    记录=为记录(源)#记
    记=记录 if 记录 is not None else {}#记
    更新=记['update'] is True if 'update' in 记 else False#替换告示
    可见=条目[:最大条目]#可见
    余=len(条目)-len(可见)#余
    return {#体
        'type':'catalog-body',#类型
        'updateNotice':翻译('message.context.catalog.replaced') if 更新 is True else None,#告示
        'entries':可见,#条
        'more':翻译('message.context.catalog.more',{'count':余}) if 余>0 else None,#余
        'unknown':未知块视图(收集未知块(内容),翻译),#未知
    }#结束

def 快照段(源):
    '全有或全无'
    记录=为记录(源)#记
    列表=记录['sections'] if 记录 is not None and 'sections' in 记录 else None#表
    if not isinstance(列表,list):#非
        return None#否
    出=[]#出
    for 项 in 列表:#逐
        条=为记录(项)#记
        if 条 is None:#坏
            return None#否
        名=条['name'] if 'name' in 条 else None#名
        文=条['text'] if 'text' in 条 else None#文
        if not isinstance(名,str) or 名=='' or not isinstance(文,str):#坏
            return None#否
        出.append({'name':名,'text':文})#加
    return None if len(出)==0 else 出#出

def 快照体(内容,源,翻译):
    '取代告示 + 分段'
    段列表=快照段(源)#段
    if 段列表 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    return {#体
        'type':'snapshot-body',#类型
        'supersedes':翻译('message.context.snapshot.supersedes'),#告示
        'sections':[{'name':段['name'],'text':有界文本(段['text'],翻译)} for 段 in 段列表],#段
    }#结束

def 通知摘要(源):
    '折叠行一文'
    记录=为记录(源)#记
    摘要=记录['summary'] if 记录 is not None and 'summary' in 记录 else None#摘要
    return 摘要 if isinstance(摘要,str) and 摘要!='' else None#出

def 通知体(内容,翻译):
    '仅模型面'
    return {'type':'notice-body','content':模型面内容(内容,翻译)}#体

def 中继发送方(源):
    'senderSessionId'
    记录=为记录(源)#记
    发=记录['senderSessionId'] if 记录 is not None and 'senderSessionId' in 记录 else None#发
    return 发 if isinstance(发,str) and 发!='' else None#出

def 中继体(内容,源,翻译):
    '发送方 + 模型面'
    发=中继发送方(源)#发
    if 发 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    return {#体
        'type':'relay-body',#类型
        'sender':翻译('message.context.relay.from',{'session':发}),#发
        'content':模型面内容(内容,翻译),#面
    }#结束

def 召回会话(源):
    '全有或全无'
    记录=为记录(源)#记
    列表=记录['references'] if 记录 is not None and 'references' in 记录 else None#表
    if not isinstance(列表,list):#非
        return None#否
    出=[]#出
    for 项 in 列表:#逐
        条=为记录(项)#记
        if 条 is None:#坏
            return None#否
        标=条['label'] if 'label' in 条 else None#标
        留=条['retainedMessages'] if 'retainedMessages' in 条 else None#留
        略=条['omittedMessages'] if 'omittedMessages' in 条 else None#略
        截=条['truncated'] if 'truncated' in 条 else None#截
        if not isinstance(标,str) or 标=='' or not 是数(留) or not 是数(略) or not isinstance(截,bool):#坏
            return None#否
        出.append({'label':标,'retained':留,'omitted':略,'truncated':截})#加
    return None if len(出)==0 else 出#出

def 召回体(内容,源,翻译):
    '会话完整度 + 模型面'
    会话列表=召回会话(源)#会
    if 会话列表 is None:#不可读
        return 不透明体(内容,源,翻译)#回退
    行=[]#行
    for 会 in 会话列表:#逐
        项={'label':会['label'],'counts':翻译('message.context.recall.counts',{'retained':会['retained'],'omitted':会['omitted']})}#项
        if 会['truncated'] is True:#截
            项['truncated']=翻译('message.context.recall.truncated')#截标
        行.append(项)#加
    return {'type':'recall-body','sessions':行,'content':模型面内容(内容,翻译)}#体

def 选上下文体(表单,内容,源,翻译):
    '返回 rendered/summary/body；不可读回退 opaque'
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
    raise ValueError(f'不可达上下文形态: {表单}')#闭联合

class 上下文体:
    '读节点 form 后选体'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '选体包装'
        属性=自身.属性#props
        内容=属性['content'] if 'content' in 属性 and 属性['content'] is not None else []#内容
        源=属性['source'] if 'source' in 属性 else None#源
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        表=属性['form'] if 'form' in 属性 else None#节点声明 form；缺席即透明
        原译=翻译 if 翻译 is not 恒等翻译 else None#宿主文案
        def 取文案(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        翻译=取文案#词典
        选=选上下文体(表,内容,源,翻译)#选
        体=选['body']#体
        def 画段(段列表):
            '画出模型面正文或未知块。'
            if 段列表 is None:#无
                return#停
            for 段 in 段列表:#逐段
                种=段['type'] if 'type' in 段 else None#种
                if 种=='pre':#正文
                    文=段['text'] if 'text' in 段 and 段['text'] is not None else ''#文
                    if 文=='':#空
                        continue#跳
                    界面.label(文).classes('text')#正文
                else:#未知块
                    标=段['label'] if 'label' in 段 else 翻译('message.unknownBlock')#标签
                    界面.label(标)#标签
                    if 'payload' in 段 and 段['payload'] is not None:#载荷
                        界面.label(str(段['payload']))#载荷
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('上下文体')#体
        自身.画面.clear()#清空
        种类=体['type'] if isinstance(体,dict) and 'type' in 体 else ''#种类
        with 自身.画面:#体
            贴出失败(自身)
            if 种类=='instructions-body':#指令
                文件=体['files'] if 'files' in 体 and 体['files'] is not None else []#文件
                for 项 in 文件:#逐个
                    摘=项['digest'] if 'digest' in 项 and 项['digest'] is not None else ''#摘要
                    if 摘=='':#无摘要
                        界面.label(项['actionLabel']+' '+项['path'])#文件
                    else:#有摘要
                        界面.label(项['actionLabel']+' '+项['path']+' '+摘)#文件
                画段(体['content'] if 'content' in 体 else None)#面
            elif 种类=='catalog-body':#目录
                if 'updateNotice' in 体 and 体['updateNotice'] is not None:#告示
                    界面.label(体['updateNotice'])#告示
                条目=体['entries'] if 'entries' in 体 and 体['entries'] is not None else []#条
                for 条 in 条目:#逐条
                    界面.label(条['name']+'：'+条['description'])#条
                if 'more' in 体 and 体['more'] is not None:#余
                    界面.label(体['more'])#余
                未知=体['unknown'] if 'unknown' in 体 and 体['unknown'] is not None else []#未知
                for 块 in 未知:#未知块
                    界面.label(块['label'] if 'label' in 块 else 翻译('message.unknownBlock'))#标签
                    if 'payload' in 块 and 块['payload'] is not None:#载荷
                        界面.label(str(块['payload']))#载荷
            elif 种类=='snapshot-body':#快照
                if 'supersedes' in 体 and 体['supersedes'] is not None:#告示
                    界面.label(体['supersedes'])#告示
                分段=体['sections'] if 'sections' in 体 and 体['sections'] is not None else []#段
                for 段 in 分段:#逐段
                    界面.label(段['name'])#名
                    界面.label(段['text'])#文
            elif 种类=='relay-body':#中继
                if 'sender' in 体 and 体['sender'] is not None:#发送方
                    界面.label(体['sender'])#发送方
                画段(体['content'] if 'content' in 体 else None)#面
            elif 种类=='recall-body':#召回
                会话列表=体['sessions'] if 'sessions' in 体 and 体['sessions'] is not None else []#会话
                for 会 in 会话列表:#逐个
                    行文=会['label']+' '+会['counts']#行
                    if 'truncated' in 会 and 会['truncated'] is not None:#截断
                        行文=行文+' '+会['truncated']#截
                    界面.label(行文)#会话
                画段(体['content'] if 'content' in 体 else None)#面
            else:#不透明或通知
                画段(体['content'] if isinstance(体,dict) and 'content' in 体 else None)#面
                字段=体['fields'] if isinstance(体,dict) and 'fields' in 体 else None#字段
                if 字段 is not None and 'rows' in 字段 and 字段['rows'] is not None:#行
                    for 行 in 字段['rows']:#逐行
                        界面.label(str(行['key'])+'：'+str(行['value']))#字段

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
