"""模型文本渲染与通用工具调用呈现。"""
import json#JSON
from datetime import datetime#纪元毫秒转 ISO
from zoneinfo import ZoneInfo#UTC
from ..会话查询 import 抽取会话事件文本#文本抽取
from .工作区访问 import 工作区访问#标题与授权

def 格式化时间(值):
    """纪元毫秒转 UTC ISO。"""
    return datetime.fromtimestamp(值/1000,ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%S')+'Z'#ISO时间

def 可用性文本(记录):
    """渲染可用性标签。"""
    标签=[]#收集
    if 记录['live']:#活
        标签.append('live')#活
    if 记录['persisted']:#已持久
        标签.append('persisted')#持久
    return ', '.join(标签) if len(标签)>0 else 'unavailable'#拼接

def 序号列表(值列表):
    """序号列表。"""
    return 'none' if len(值列表)==0 else ', '.join(str(值) for 值 in 值列表)#序号列表

def 格式化空会话搜索():
    """空跨会话检索。"""
    return 'No prior session matches found.'#空句

def 格式化会话搜索(集合,标题表,已授权父集合):
    """渲染跨会话检索结果。"""
    if len(集合['items'])==0:#空结果
        return 格式化空会话搜索()#空句
    行=['Session search results ('+str(len(集合['items']))+'):']#标题行
    for 下标,命中 in enumerate(集合['items']):#逐条命中
        头=命中['header']#头
        父=头['parentSession'] if 'parentSession' in 头 else None#父会话
        if 父 is None:#根
            父文本='root'#根
        elif 父 in 已授权父集合:#可见父
            父文本=父#原id
        else:#工作区外
            父文本='[outside workspace]'#打码
        最佳=命中['bestMatch']#最佳命中
        行.extend(['',' '+str(下标+1)+'. Session '+头['id']+' — '+工作区访问['titleText'](标题表[头['id']]),
            '   Created: '+格式化时间(头['createdAt']),
            '   Parent: '+str(父文本),
            '   Availability: '+可用性文本(命中),
            '   Best match: seq '+str(最佳['seq'])+' | '+最佳['type']+' | '+最佳['surface']+' | '+格式化时间(最佳['time']),
            '   Snippet: '+最佳['snippet'],
        ])#一条命中块
    if 集合['capped']:#触顶
        行.extend(['','Result cap reached. Narrow the query or add filters to find additional matches.'])#提示
    return '\n'.join(行)#拼文本

def 格式化事件搜索(会话号,标题,集合):
    """渲染会话内事件检索。"""
    行=['Session '+str(会话号)+' — '+工作区访问['titleText'](标题)]#会话行
    if len(集合['items'])==0:#无命中
        行.extend(['','No prior event matches found.'])#空结果
        return '\n'.join(行)#返回
    行.extend(['','Event search results ('+str(len(集合['items']))+'):'])#结果标题
    for 下标,命中 in enumerate(集合['items']):#逐条
        行.extend([
            str(下标+1)+'. seq '+str(命中['seq'])+' | '+命中['type']+' | '+命中['surface']+' | '+格式化时间(命中['time']),
            '   Snippet: '+命中['snippet'],
        ])#事件行
    if 集合['capped']:#触顶
        行.extend(['','Result cap reached. Narrow the query or add filters to find additional matches.'])#提示
    return '\n'.join(行)#拼文本

def 渲染后代(行,节点列表,标题表):
    """把可见后代树写进行列。"""
    for 项 in 工作区访问['visitDescendants'](节点列表):#遍历
        缩进='  '*项['depth']#按深度缩进
        if 项['node'] is None:#洞
            行.append(缩进+'- [outside workspace subtree]')#占位
            continue#不展开
        标识=项['node']['record']['header']['id']#会话id
        记录=项['node']['record']#记录
        行.append(缩进+'- '+标识+' — '+工作区访问['titleText'](标题表[标识])+' | '+格式化时间(记录['header']['createdAt'])+' | '+可用性文本(记录))#后代行

def 格式化会话谱系(谱系,祖先列表,祖先边界,后代列表,标题表):
    """渲染会话谱系。"""
    目标头=谱系['target']['header']#目标头
    行=[
        'Session '+目标头['id']+' — '+工作区访问['titleText'](标题表[目标头['id']]),
        'Created: '+格式化时间(目标头['createdAt']),
        'Availability: '+可用性文本(谱系['target']),
        '','Ancestors (nearest first):',
    ]#头
    if len(祖先列表)==0 and not 祖先边界:#根会话
        行.append('- none (target is a root session)')#根
    for 记录 in 祖先列表:#可见祖先
        头=记录['header']#头
        行.append('- '+头['id']+' — '+工作区访问['titleText'](标题表[头['id']])+' | '+格式化时间(头['createdAt'])+' | '+可用性文本(记录))#祖先行
    if 祖先边界:#边界
        行.append('- [outside workspace boundary]')#占位
    行.extend(['','Descendants:'])#后代标题
    if len(后代列表)==0:#无后代
        行.append('- none')#无
    else:#有后代
        渲染后代(行,后代列表,标题表)#渲染树
    return '\n'.join(行)#拼文本

def 格式化事件追踪(会话号,标题,追踪):
    """渲染事件关系追踪。"""
    目标=追踪['target']#目标
    替换者=追踪['replacedBy'] if 'replacedBy' in 追踪 else 'none'#替换者
    return '\n'.join([
        'Session '+str(会话号)+' — '+工作区访问['titleText'](标题),
        'Target: seq '+str(目标['seq'])+' | '+目标['type']+' | '+目标['surface']+' | '+格式化时间(目标['time']),
        'Replaced by: '+str(替换者),
        'Replacement chain: '+序号列表(追踪['replacementChain'] if 'replacementChain' in 追踪 else []),
        'Events replaced by target: '+序号列表(追踪['replacedEventSeqs'] if 'replacedEventSeqs' in 追踪 else []),
        'Events cited directly as sources: '+序号列表(追踪['sourceEventSeqs'] if 'sourceEventSeqs' in 追踪 else []),
        'Direct derived events: '+序号列表(追踪['derivedEventSeqs'] if 'derivedEventSeqs' in 追踪 else []),
    ])#固定字段列表

def 格式化邻域事件(事件):
    """渲染相邻事件摘要。"""
    文本=抽取会话事件文本(事件)#语义文本
    行='- seq '+str(事件['seq'])+' | '+事件['type']+' | '+格式化时间(事件['time'])#元数据行
    if len(文本)==0:#无文本
        return 行+' | (no semantic text)'#标注
    return 行+'\n  '+文本.replace('\n','\n  ')#附文本

def 格式化事件读取(会话号,标题,窗口):
    """渲染带邻域的事件读取。"""
    目标序号=窗口['target']['seq']#目标序号
    前=[事件 for 事件 in 窗口['events'] if 事件['seq']<目标序号]#前窗口
    后=[事件 for 事件 in 窗口['events'] if 事件['seq']>目标序号]#后窗口
    行=[
        'Session '+str(会话号)+' — '+工作区访问['titleText'](标题),
        'Target event seq '+str(目标序号)+':',
        '```json',
        json.dumps(窗口['target'],ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2),
        '```',
    ]#头
    if len(前)>0:#有前邻
        行.extend(['','Before:']+[格式化邻域事件(事件) for 事件 in 前])#前邻
    if len(后)>0:#有后邻
        行.extend(['','After:']+[格式化邻域事件(事件) for 事件 in 后])#后邻
    return '\n'.join(行)#拼文本

def 呈现会话搜索调用(参数):
    """搜索卡。"""
    return {'card':'generic','kind':'search','title':'Search prior sessions','rawInput':参数['query']}#搜索卡

def 呈现事件搜索调用(参数):
    """搜索卡。"""
    return {'card':'generic','kind':'search','title':'Search session events','rawInput':参数['query']}#搜索卡

def 呈现会话谱系调用(参数):
    """读取卡。"""
    if 'session_id' not in 参数 or 参数['session_id'] is None:#当前会话
        return {'card':'generic','kind':'read','title':'Trace current session'}#读取卡
    return {'card':'generic','kind':'read','title':'Trace session '+str(参数['session_id']),'rawInput':参数['session_id']}#读取卡

def 呈现事件目标调用(动作,参数):
    """事件卡。"""
    输入={'seq':参数['seq']}#序号
    if 'session_id' in 参数 and 参数['session_id'] is not None:#有会话
        输入['session_id']=参数['session_id']#会话
    return {'card':'generic','kind':'read','title':动作+' '+str(参数['seq']),'rawInput':输入}#事件卡

呈现={
    'formatSessionSearch':格式化会话搜索,'formatEmptySessionSearch':格式化空会话搜索,
    'formatEventSearch':格式化事件搜索,'formatSessionTrace':格式化会话谱系,
    'formatEventTrace':格式化事件追踪,'formatEventRead':格式化事件读取,
    'presentSessionSearchCall':呈现会话搜索调用,'presentEventSearchCall':呈现事件搜索调用,
    'presentSessionTraceCall':呈现会话谱系调用,'presentEventTargetCall':呈现事件目标调用,
}#对外出口
