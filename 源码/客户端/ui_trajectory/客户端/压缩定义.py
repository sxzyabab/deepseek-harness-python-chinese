"""轨迹压缩请求与会话边界的 ConversationNode Definition。

对齐上游 `ui-trajectory/src/client/trajectory-compaction-definition.ts`。公开面仅中文名。
"""
from .定义公共 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 取字段#读字段

__all__=['登记轨迹压缩定义']#仅中文公开名

def 检查点标识(事件):#从用户消息里抽出 compact 插件写入的 compactionId
    """有合法 id 则返回，否则 None。"""
    if 取字段(事件,'type')!='user/message':#非用户消息
        return None#不是 checkpoint
    来源=取字段(取字段(事件,'data'),'source')#来源
    if 取字段(来源,'kind')=='plugin' and 取字段(来源,'plugin')=='compact':#compact 插件来源
        标识=取字段(来源,'compactionId')#压缩 id
        if isinstance(标识,str) and 标识!='':#非空字符串
            return 标识#合法
    return None#否则不是 checkpoint

def 事件压缩标识(事件):#从压缩生命周期事件上读 compactionId
    """有合法 id 则返回，否则 None。"""
    种类=取字段(事件,'type')#事件类型
    if 种类 not in ('compaction/start','compaction/summary','compaction/end'):#无关
        return None#无关
    值=取字段(取字段(事件,'data'),'compactionId')#取出 compactionId
    return 值 if isinstance(值,str) and 值!='' else None#非空字符串才算合法

def 状态转请求(状态):#把累积状态投影成 compaction RequestView
    """start 合法才返回视图。"""
    开始事件=取字段(取字段(状态,'start'),'event')#取出 start 命中上的事件
    if 取字段(开始事件,'type')!='compaction/start':#start 不是压缩开始
        return None#无法投影
    摘要事件=取字段(取字段(状态,'summary'),'event') if 取字段(状态,'summary') is not None else None#摘要事件
    结束事件=取字段(取字段(状态,'end'),'event') if 取字段(状态,'end') is not None else None#结束事件
    检查点事件=取字段(取字段(状态,'checkpoint'),'event') if 取字段(状态,'checkpoint') is not None else None#替换用户消息
    请求={#组装 compaction RequestView
        'purpose':'compaction',#用途固定为压缩
        'startSeq':取字段(开始事件,'seq'),#开始事件序号
        'turn':取字段(取字段(开始事件,'data'),'turn'),#所属回合
        'step':0,#压缩请求步号固定为 0
        'startedAt':取字段(开始事件,'time'),#开始时间
        'completedAt':取字段(结束事件,'time') if 取字段(结束事件,'type')=='compaction/end' else None,#已结束则填结束时间
        'status':'running' if 取字段(结束事件,'type')!='compaction/end' else ('complete' if 取字段(取字段(结束事件,'data'),'error') is None else 'error'),#状态
    }#请求主体
    if 取字段(结束事件,'type')=='compaction/end' and 取字段(取字段(结束事件,'data'),'error') is not None:#结束且带 error
        请求['error']=取字段(取字段(结束事件,'data'),'error')#展开错误字段
    if 取字段(摘要事件,'type')=='compaction/summary':#有摘要
        数据=取字段(摘要事件,'data')#摘要载荷
        请求['resultSeq']=取字段(摘要事件,'seq')#摘要事件序号
        请求['summary']=取字段(数据,'summary')#压缩摘要正文
        if 取字段(数据,'rawOutput') is not None:#有原始输出
            请求['rawOutput']=取字段(数据,'rawOutput')#展开
        请求['provenance']={'provider':取字段(数据,'provider'),'model':取字段(数据,'model')}#提供方与模型出处
        配置={'provider':取字段(数据,'provider'),'model':取字段(数据,'model'),'purpose':'compaction'}#回放配置
        if 取字段(数据,'maxTokens') is not None:#有上限
            配置['maxTokens']=取字段(数据,'maxTokens')#展开
        请求['requestConfig']=配置#挂配置
        if 取字段(数据,'usage') is not None:#有用量
            请求['usage']=取字段(数据,'usage')#展开
    if 取字段(检查点事件,'type')=='user/message':#有替换消息
        请求['replacementSeq']=取字段(检查点事件,'seq')#记下序号
    return 请求#RequestView

def 压缩匹配(事件):#按 compactionId 或 checkpoint id 命中同一节点
    """start 开节点，其余更新。"""
    压缩标识=事件压缩标识(事件)#先从压缩生命周期事件取 id
    if 压缩标识 is not None:#命中压缩事件
        return {'id':压缩标识,'role':'start' if 取字段(事件,'type')=='compaction/start' else 'update'}#start 或 update
    检查点=检查点标识(事件)#再试 checkpoint 用户消息
    return None if 检查点 is None else {'id':检查点,'role':'update'}#有则作为更新

def 压缩开始(_上下文,匹配):#用 compaction/start 命中初始化状态
    """起点必须是压缩开始。"""
    if 取字段(取字段(匹配,'event'),'type')!='compaction/start':#起点必须是压缩开始
        raise Exception('trajectory-compaction start requires compaction/start')#运行时错误字符串保持英文
    return {'start':匹配}#记下 start 命中

def 压缩更新(上下文,匹配):#把后续命中并入状态
    """summary / end / checkpoint。"""
    种类=取字段(取字段(匹配,'event'),'type')#事件类型
    状态=取字段(上下文,'state')#当前状态
    if 种类=='compaction/summary':#摘要
        return {**状态,'summary':匹配}#记下摘要
    if 种类=='compaction/end':#结束
        return {**状态,'end':匹配}#记下结束
    if 检查点标识(取字段(匹配,'event')) is None:#不是 checkpoint
        return 状态#状态不变
    return {**状态,'checkpoint':匹配}#记下替换用户消息

def 压缩构建视图(上下文):#把状态投影成轨迹视图节点
    """投影失败则不贡献。"""
    状态=取字段(上下文,'state')#累积状态
    if 状态 is None:#尚无状态
        return None#不贡献
    请求=状态转请求(状态)#投影 RequestView
    if 请求 is None:#投影失败
        return None#不贡献
    return 轨迹节点(上下文,取字段(请求,'startSeq'),{'kind':'compaction','request':请求})#包成压缩贡献信封

轨迹压缩定义={#压缩请求节点 Definition
    'kind':'trajectory-compaction',#节点种类
    'target':'trajectory',#贡献目标为轨迹
    'match':压缩匹配,#匹配
    'start':压缩开始,#播种
    'update':压缩更新,#更新
    'buildViewNode':压缩构建视图,#投影
}#定义结束

会话结束定义={#会话结束节点 Definition
    'kind':'trajectory-session-end',#节点种类
    'target':'trajectory',#贡献目标为轨迹
    'match':lambda 事件:({'id':str(取字段(事件,'seq')),'role':'start'} if 取字段(事件,'type')=='session/end-seed' else None),#只匹配会话结束种子
    'start':lambda _上下文,匹配:{'seq':取字段(取字段(匹配,'event'),'seq'),'time':取字段(取字段(匹配,'event'),'time')},#记下序号与时间
    'update':lambda 上下文,_匹配:取字段(上下文,'state'),#无后续更新
    'buildViewNode':lambda 上下文:(None if 取字段(上下文,'state') is None else 轨迹节点(上下文,取字段(取字段(上下文,'state'),'seq'),{'kind':'session-end','seq':取字段(取字段(上下文,'state'),'seq'),'time':取字段(取字段(上下文,'state'),'time')})),#包成会话结束贡献
}#定义结束

def 登记轨迹压缩定义(上下文):#向会话事件注册两则 Definition
    """注册轨迹压缩请求与会话边界的 ConversationNode Definition。"""
    上下文.conversationEvents.register(轨迹压缩定义)#注册压缩请求节点
    上下文.conversationEvents.register(会话结束定义)#注册会话结束节点
