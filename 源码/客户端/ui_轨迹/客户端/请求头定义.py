"""轨迹请求头事实的 ConversationNode Definition。

对齐上游 `ui-trajectory/src/client/trajectory-request-header-definition.ts`。公开面仅中文名。
"""
import json#tools 序列化比对
from .轨迹节点 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 轨迹错误#本包异常

__all__=['登记轨迹请求头定义']#仅中文公开名

def 请求提示(匹配):#从请求头抽出提示快照
    """config、system、tools 组成的提示快照。"""
    事件=匹配['event'] if 'event' in 匹配 else None#匹配事件
    if 事件 is None or 事件['type']!='request/header':#起点必须是请求头
        raise 轨迹错误('trajectory-request-header start requires request/header')#运行时错误字符串保持英文
    数据=事件['data'] if 'data' in 事件 else None#载荷
    头=数据['header'] if 数据 is not None and 'header' in 数据 else None#取出请求头载荷
    工具=头['tools'] if 头 is not None and 'tools' in 头 else None#tools
    return {#提示快照
        'config':头['config'] if 头 is not None and 'config' in 头 else None,#配置
        'system':头['system'] if 头 is not None and 'system' in 头 and 头['system'] is not None else '',#系统
        'tools':工具 if isinstance(工具,list) else [],#工具列表
    }#快照结束

def 提示变更(上一条,提示,匹配):#对比提示快照，产出变更
    """有实质变化才返回，否则 None。"""
    事件=匹配['event'] if 'event' in 匹配 else None#须是 request/header 命中
    if 事件 is None or 事件['type']!='request/header':#非请求头
        return None#无法比变更
    数据=事件['data'] if 'data' in 事件 else None#载荷
    原因=数据['reason'] if 数据 is not None and 'reason' in 数据 else None#原因
    if 上一条 is None and 原因!='initial':#无 previous 且非 initial
        return None#不报变更
    系统变=上一条 is not None and 上一条['system']!=提示['system']#system 文本不同
    工具前=json.dumps(上一条['tools'],ensure_ascii=False,separators=(',',':'),allow_nan=False) if 上一条 is not None else None#上一条 tools
    工具后=json.dumps(提示['tools'],ensure_ascii=False,separators=(',',':'),allow_nan=False)#本次 tools
    工具变=上一条 is not None and 工具前!=工具后#tools 变了
    if 上一条 is not None and not 系统变 and not 工具变:#有 previous 但都没变
        return None#无实质变化
    if 上一条 is None:#尚无上一条
        种类='initial'#记为初始
    elif 系统变 and 工具变:#系统与工具都变
        种类='system-and-tools'#两种都变
    elif 系统变:#只变系统
        种类='system'#系统
    else:#只变工具
        种类='tools'#工具
    变更={'seq':事件['seq'],'time':事件['time'],'kind':种类}#组装提示变更
    if 上一条 is not None:#有 previous 才展开对照
        变更['previous']=上一条#对照
    return 变更#RequestPromptChange

def 请求头开始(_上下文,匹配,读取器):#用 request/header 命中初始化状态
    """抽出提示快照并对比上一条。"""
    提示=请求提示(匹配)#抽出本次提示快照
    上一条节点=读取器.previous('trajectory-request-header')#上一条同种节点
    上态=上一条节点['state'] if 上一条节点 is not None and 'state' in 上一条节点 else None#状态
    上一条=上态['prompt'] if 上态 is not None and 'prompt' in 上态 else None#取其 prompt 快照
    变更=提示变更(上一条,提示,匹配)#对比得到变更
    事件=匹配['event']#匹配事件
    事实={'seq':事件['seq'],'time':事件['time'],'prompt':提示,'location':匹配['location'] if 'location' in 匹配 else None}#请求头事实
    if 变更 is not None:#有变更才展开
        事实['change']=变更#变更
    return 事实#请求头事实

def 请求头匹配(事件):#只匹配请求头事件
    """用序号当节点 id。"""
    if 事件['type']=='request/header':#请求头
        return {'id':str(事件['seq']),'role':'start'}#起步
    return None#其余不匹配

def 请求头更新(上下文,_匹配):#请求头无后续更新
    """状态原样。"""
    return 上下文['state'] if 'state' in 上下文 else None#原样

def 请求头构建视图(上下文):#包成请求头贡献
    """尚无状态则不贡献。"""
    状态=上下文['state'] if 'state' in 上下文 else None#请求头事实
    if 状态 is None:#尚无状态
        return None#不贡献
    return 轨迹节点(上下文,状态['seq'] if 'seq' in 状态 else None,{'kind':'request-header','header':状态})#包成请求头贡献

轨迹请求头定义={#请求头节点 Definition
    'kind':'trajectory-request-header',#节点种类
    'target':'trajectory',#贡献目标为轨迹
    'match':请求头匹配,#匹配
    'start':请求头开始,#播种
    'update':请求头更新,#请求头无后续更新
    'buildViewNode':请求头构建视图,#投影
}#定义结束

def 登记轨迹请求头定义(上下文):#向会话事件注册请求头 Definition
    """注册轨迹请求头事实的 ConversationNode Definition。"""
    上下文.conversationEvents.register(轨迹请求头定义)#注册请求头节点
