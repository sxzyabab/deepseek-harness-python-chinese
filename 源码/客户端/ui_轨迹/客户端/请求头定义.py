"""轨迹请求头事实的 ConversationNode Definition。

对齐上游 `ui-trajectory/src/client/trajectory-request-header-definition.ts`。公开面仅中文名。
"""
import json#tools 序列化比对
from .定义公共 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 取字段#读字段

__all__=['登记轨迹请求头定义']#仅中文公开名

def 请求提示(匹配):#从请求头抽出提示快照
    """config、system、tools 组成的提示快照。"""
    事件=取字段(匹配,'event')#匹配事件
    if 取字段(事件,'type')!='request/header':#起点必须是请求头
        raise Exception('trajectory-request-header start requires request/header')#运行时错误字符串保持英文
    头=取字段(取字段(事件,'data'),'header')#取出请求头载荷
    工具=取字段(头,'tools')#tools
    return {'config':取字段(头,'config'),'system':取字段(头,'system') or '','tools':工具 if isinstance(工具,list) else []}#提示快照

def 提示变更(上一条,提示,匹配):#对比提示快照，产出变更
    """有实质变化才返回，否则 None。"""
    事件=取字段(匹配,'event')#须是 request/header 命中
    if 取字段(事件,'type')!='request/header':#非请求头
        return None#无法比变更
    if 上一条 is None and 取字段(取字段(事件,'data'),'reason')!='initial':#无 previous 且非 initial
        return None#不报变更
    系统变=上一条 is not None and 取字段(上一条,'system')!=取字段(提示,'system')#system 文本不同
    工具变=上一条 is not None and json.dumps(取字段(上一条,'tools'),ensure_ascii=False)!=json.dumps(取字段(提示,'tools'),ensure_ascii=False)#tools 变了
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
    变更={'seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'kind':种类}#组装提示变更
    if 上一条 is not None:#有 previous 才展开对照
        变更['previous']=上一条#对照
    return 变更#RequestPromptChange

def 请求头开始(_上下文,匹配,读取器):#用 request/header 命中初始化状态
    """抽出提示快照并对比上一条。"""
    提示=请求提示(匹配)#抽出本次提示快照
    上一条节点=读取器.previous('trajectory-request-header')#上一条同种节点
    上一条=取字段(取字段(上一条节点,'state'),'prompt') if 上一条节点 is not None else None#取其 prompt 快照
    变更=提示变更(上一条,提示,匹配)#对比得到变更
    事实={'seq':取字段(取字段(匹配,'event'),'seq'),'time':取字段(取字段(匹配,'event'),'time'),'prompt':提示,'location':取字段(匹配,'location')}#请求头事实
    if 变更 is not None:#有变更才展开
        事实['change']=变更#变更
    return 事实#请求头事实

def 请求头匹配(事件):#只匹配请求头事件
    """用序号当节点 id。"""
    if 取字段(事件,'type')=='request/header':#请求头
        return {'id':str(取字段(事件,'seq')),'role':'start'}#起步
    return None#其余不匹配

def 请求头构建视图(上下文):#包成请求头贡献
    """尚无状态则不贡献。"""
    状态=取字段(上下文,'state')#请求头事实
    if 状态 is None:#尚无状态
        return None#不贡献
    return 轨迹节点(上下文,取字段(状态,'seq'),{'kind':'request-header','header':状态})#包成请求头贡献

轨迹请求头定义={#请求头节点 Definition
    'kind':'trajectory-request-header',#节点种类
    'target':'trajectory',#贡献目标为轨迹
    'match':请求头匹配,#匹配
    'start':请求头开始,#播种
    'update':lambda 上下文,_匹配:取字段(上下文,'state'),#请求头无后续更新
    'buildViewNode':请求头构建视图,#投影
}#定义结束

def 登记轨迹请求头定义(上下文):#向会话事件注册请求头 Definition
    """注册轨迹请求头事实的 ConversationNode Definition。"""
    上下文.conversationEvents.register(轨迹请求头定义)#注册请求头节点
