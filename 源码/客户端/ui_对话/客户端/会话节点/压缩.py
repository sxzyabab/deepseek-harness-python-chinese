"""自动压缩生命周期与落地检查点。

对齐上游 `ui-conversation/src/client/conversation-nodes/compaction.ts`。公开面仅中文名。
"""
from .公共 import 聊天节点#聊天节点工厂
from .命令 import 压缩来源,压缩摘要,更新压缩状态#命令侧复用
from .面辅助 import 取字段#字段

__all__=['压缩定义','登记压缩会话节点']#仅中文公开名

def 回放压缩(上下文):#从已加载匹配回退拼状态
    """有则写入。"""
    匹配们=取字段(上下文,'matches') or []#匹配
    摘要=next((候 for 候 in 匹配们 if 取字段(取字段(候,'event'),'type')=='compaction/summary'),None)#摘要
    检查点=next((候 for 候 in 匹配们 if 压缩来源(取字段(候,'event')) is not None),None)#检查点
    态={}#空
    if 摘要 is not None:#有
        态['summary']=摘要#带上
    if 检查点 is not None:#有
        态['checkpoint']=检查点#带上
    return 态#回退

def 压缩匹配(事件):#判定事件是否属于本节点
    """无命令检查点 → 自动压缩；生命周期无源命令。"""
    检查=压缩来源(事件)#检查点
    if 检查 is not None and 检查.get('sourceCommandId') is None:#自动压缩检查点
        return {'id':检查['compactionId'],'role':'update'}#关联
    种=取字段(事件,'type')#种
    if 种 in ('compaction/start','compaction/summary','compaction/end'):#生命周期
        数据=取字段(事件,'data') or {}#载荷
        if 取字段(数据,'sourceCommandId') is not None:#有命令
            return None#交给 command
        压缩标识=取字段(数据,'compactionId')#id
        if not isinstance(压缩标识,str) or 压缩标识=='':#非法
            return None#忽略
        return {'id':压缩标识,'role':'start' if 种=='compaction/start' else 'update'}#开或更新
    return None#其余

def 压缩开始(_上下文=None,_匹配项=None):#开节点时空状态
    """等后续证据。"""
    return {}#空

def 压缩更新(上下文,匹配项):#把摘要或检查点折进状态
    """委托更新压缩状态。"""
    return 更新压缩状态(取字段(上下文,'state') or {},匹配项)#折

def 压缩建视图(上下文):#组装可见 Chat 节点
    """检查点未落地则不渲染。"""
    态=取字段(上下文,'state')#折叠
    if 态 is None:#无
        态=回放压缩(上下文)#回退
    if 态.get('checkpoint') is None:#无检查点
        return None#不渲染
    标记=压缩摘要(态.get('summary'),态['checkpoint'])#可见标记
    return 聊天节点(上下文,'compaction',取字段(标记,'seq'),标记)#节点

压缩定义={#自动压缩会话节点定义
    'kind':'compaction','target':'chat',#kind/目标
    'match':压缩匹配,'start':压缩开始,'update':压缩更新,'buildViewNode':压缩建视图,#生命周期
}#结束

def 登记压缩会话节点(上下文):#注册自动压缩业务贡献
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(压缩定义)#登记
