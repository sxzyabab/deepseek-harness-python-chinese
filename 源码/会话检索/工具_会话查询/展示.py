"""模型文本渲染与通用工具调用展示。对齐上游 `tool-session-query/src/presentation.ts`。"""
import json,datetime#JSON与时间
from ..会话查询 import 抽取会话事件文本#文本抽取
from .工作区访问 import 工作区访问#标题与授权

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 格式化时间(值):return datetime.datetime.fromtimestamp(值/1000,datetime.timezone.utc).isoformat().replace('+00:00','Z')#ISO时间

def 可用性文本(记录):#渲染可用性
    """渲染可用性标签。"""
    标签=[项 for 项 in [('live' if 取字段(记录,'live') else None),('persisted' if 取字段(记录,'persisted') else None)] if 项 is not None]#收集
    return ', '.join(标签) if len(标签)>0 else 'unavailable'#拼接

def 序号列表(值们):return 'none' if len(值们)==0 else ', '.join(str(值) for 值 in 值们)#序号列表

def 格式化空会话搜索():return 'No prior session matches found.'#空跨会话检索

def 格式化会话搜索(集合,标题表,已授权父们):#渲染跨会话检索结果
    """渲染跨会话检索结果。"""
    if len(集合['items'])==0:#空结果
        return 格式化空会话搜索()#空句
    行=[f"Session search results ({len(集合['items'])}):"]#标题行
    for 下标,命中 in enumerate(集合['items']):#逐条命中
        父=取字段(取字段(命中,'header'),'parentSession')#父会话
        if 父 is None:#根
            父文本='root'#根
        elif 父 in 已授权父们:#可见父
            父文本=父#原id
        else:#工作区外
            父文本='[outside workspace]'#打码
        行.extend(['',f"{下标+1}. Session {取字段(取字段(命中,'header'),'id')} — {工作区访问['titleText'](标题表[取字段(取字段(命中,'header'),'id')])}",
            f"   Created: {格式化时间(取字段(取字段(命中,'header'),'createdAt'))}",
            f"   Parent: {父文本}",
            f"   Availability: {可用性文本(命中)}",
            f"   Best match: seq {取字段(取字段(命中,'bestMatch'),'seq')} | {取字段(取字段(命中,'bestMatch'),'type')} | {取字段(取字段(命中,'bestMatch'),'surface')} | {格式化时间(取字段(取字段(命中,'bestMatch'),'time'))}",
            f"   Snippet: {取字段(取字段(命中,'bestMatch'),'snippet')}",
        ])#一条命中块
    if 集合['capped']:#触顶
        行.extend(['','Result cap reached. Narrow the query or add filters to find additional matches.'])#提示
    return '\n'.join(行)#拼文本

def 格式化事件搜索(会话号,标题,集合):#渲染会话内事件检索
    """渲染会话内事件检索。"""
    行=[f"Session {会话号} — {工作区访问['titleText'](标题)}"]#会话行
    if len(集合['items'])==0:#无命中
        行.extend(['','No prior event matches found.'])#空结果
        return '\n'.join(行)#返回
    行.extend(['',f"Event search results ({len(集合['items'])}):"])#结果标题
    for 下标,命中 in enumerate(集合['items']):#逐条
        行.extend([
            f"{下标+1}. seq {取字段(命中,'seq')} | {取字段(命中,'type')} | {取字段(命中,'surface')} | {格式化时间(取字段(命中,'time'))}",
            f"   Snippet: {取字段(命中,'snippet')}",
        ])#事件行
    if 集合['capped']:#触顶
        行.extend(['','Result cap reached. Narrow the query or add filters to find additional matches.'])#提示
    return '\n'.join(行)#拼文本

def 渲染后代(行,节点们,标题表):#把可见后代树写进行列
    """把可见后代树写进行列。"""
    for 项 in 工作区访问['visitDescendants'](节点们):#遍历
        缩进='  '*项['depth']#按深度缩进
        if 项['node'] is None:#洞
            行.append(f"{缩进}- [outside workspace subtree]")#占位
            continue#不展开
        标识=取字段(取字段(项['node']['record'],'header'),'id')#会话id
        行.append(f"{缩进}- {标识} — {工作区访问['titleText'](标题表[标识])} | {格式化时间(取字段(取字段(项['node']['record'],'header'),'createdAt'))} | {可用性文本(项['node']['record'])}")#后代行

def 格式化会话谱系(谱系,祖先们,祖先边界,后代们,标题表):#渲染会话谱系
    """渲染会话谱系。"""
    目标号=取字段(取字段(谱系,'target'),'header')#目标头
    行=[
        f"Session {取字段(目标号,'id')} — {工作区访问['titleText'](标题表[取字段(目标号,'id')])}",
        f"Created: {格式化时间(取字段(目标号,'createdAt'))}",
        f"Availability: {可用性文本(取字段(谱系,'target'))}",
        '','Ancestors (nearest first):',
    ]#头
    if len(祖先们)==0 and not 祖先边界:#根会话
        行.append('- none (target is a root session)')#根
    for 记录 in 祖先们:#可见祖先
        头=取字段(记录,'header')#头
        行.append(f"- {取字段(头,'id')} — {工作区访问['titleText'](标题表[取字段(头,'id')])} | {格式化时间(取字段(头,'createdAt'))} | {可用性文本(记录)}")#祖先行
    if 祖先边界:#边界
        行.append('- [outside workspace boundary]')#占位
    行.extend(['','Descendants:'])#后代标题
    if len(后代们)==0:#无后代
        行.append('- none')#无
    else:#有后代
        渲染后代(行,后代们,标题表)#渲染树
    return '\n'.join(行)#拼文本

def 格式化事件追踪(会话号,标题,追踪):#渲染事件关系追踪
    """渲染事件关系追踪。"""
    return '\n'.join([
        f"Session {会话号} — {工作区访问['titleText'](标题)}",
        f"Target: seq {取字段(取字段(追踪,'target'),'seq')} | {取字段(取字段(追踪,'target'),'type')} | {取字段(取字段(追踪,'target'),'surface')} | {格式化时间(取字段(取字段(追踪,'target'),'time'))}",
        f"Replaced by: {取字段(追踪,'replacedBy','none')}",
        f"Replacement chain: {序号列表(取字段(追踪,'replacementChain',[]))}",
        f"Events replaced by target: {序号列表(取字段(追踪,'replacedEventSeqs',[]))}",
        f"Events cited directly as sources: {序号列表(取字段(追踪,'sourceEventSeqs',[]))}",
        f"Direct derived events: {序号列表(取字段(追踪,'derivedEventSeqs',[]))}",
    ])#固定字段列表

def 格式化邻域事件(事件):#渲染相邻事件
    """渲染相邻事件摘要。"""
    文本=抽取会话事件文本(事件)#语义文本
    行=f"- seq {取字段(事件,'seq')} | {取字段(事件,'type')} | {格式化时间(取字段(事件,'time'))}"#元数据行
    if len(文本)==0:#无文本
        return 行+' | (no semantic text)'#标注
    return 行+'\n  '+文本.replace('\n','\n  ')#附文本

def 格式化事件读取(会话号,标题,窗口):#渲染带邻域的事件读取
    """渲染带邻域的事件读取。"""
    目标序号=取字段(取字段(窗口,'target'),'seq')#目标序号
    前=[事件 for 事件 in 取字段(窗口,'events') if 取字段(事件,'seq')<目标序号]#前窗口
    后=[事件 for 事件 in 取字段(窗口,'events') if 取字段(事件,'seq')>目标序号]#后窗口
    行=[
        f"Session {会话号} — {工作区访问['titleText'](标题)}",
        f"Target event seq {目标序号}:",
        '```json',
        json.dumps(取字段(窗口,'target'),indent=2,ensure_ascii=False),
        '```',
    ]#头
    if len(前)>0:#有前邻
        行.extend(['','Before:']+[格式化邻域事件(事件) for 事件 in 前])#前邻
    if len(后)>0:#有后邻
        行.extend(['','After:']+[格式化邻域事件(事件) for 事件 in 后])#后邻
    return '\n'.join(行)#拼文本

def 呈现会话搜索调用(参数):return {'card':'generic','kind':'search','title':'Search prior sessions','rawInput':取字段(参数,'query')}#搜索卡
def 呈现事件搜索调用(参数):return {'card':'generic','kind':'search','title':'Search session events','rawInput':取字段(参数,'query')}#搜索卡
def 呈现会话谱系调用(参数):return {'card':'generic','kind':'read','title':'Trace current session' if 取字段(参数,'session_id') is None else f"Trace session {取字段(参数,'session_id')}",**({} if 取字段(参数,'session_id') is None else {'rawInput':取字段(参数,'session_id')})}#读取卡
def 呈现事件目标调用(动作,参数):return {'card':'generic','kind':'read','title':f"{动作} {取字段(参数,'seq')}",'rawInput':{**({} if 取字段(参数,'session_id') is None else {'session_id':取字段(参数,'session_id')}),'seq':取字段(参数,'seq')}}#事件卡

展示={
    'formatSessionSearch':格式化会话搜索,'formatEmptySessionSearch':格式化空会话搜索,
    'formatEventSearch':格式化事件搜索,'formatSessionTrace':格式化会话谱系,
    'formatEventTrace':格式化事件追踪,'formatEventRead':格式化事件读取,
    'presentSessionSearchCall':呈现会话搜索调用,'presentEventSearchCall':呈现事件搜索调用,
    'presentSessionTraceCall':呈现会话谱系调用,'presentEventTargetCall':呈现事件目标调用,
}#对外出口
