from .节点工厂 import 聊天节点#聊天节点工厂
from .命令 import 压缩来源,压缩摘要,更新压缩状态#命令侧复用

__all__=['压缩定义','登记压缩会话节点']#仅中文公开名

def 回放压缩(上下文):
    """有则写入。"""
    匹配列表=上下文['matches'] if 'matches' in 上下文 else []#匹配
    摘要=None#摘要
    检查点=None#检查点
    for 候 in 匹配列表:#扫
        候事件=候['event'] if 'event' in 候 else {}#事件
        if 摘要 is None and 候事件['type']=='compaction/summary':#摘要
            摘要=候#记下
        if 检查点 is None and 压缩来源(候事件) is not None:#检查点
            检查点=候#记下
    态={}#空
    if 摘要 is not None:#有
        态['summary']=摘要#带上
    if 检查点 is not None:#有
        态['checkpoint']=检查点#带上
    return 态#回退

def 压缩匹配(事件):
    """无命令检查点 → 自动压缩；生命周期无源命令。"""
    检查=压缩来源(事件)#检查点
    if 检查 is not None and ('sourceCommandId' not in 检查 or 检查['sourceCommandId'] is None):#自动压缩检查点
        return {'id':检查['compactionId'],'role':'update'}#关联
    种=事件['type']#种
    if 种 in ('compaction/start','compaction/summary','compaction/end'):#生命周期
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        if 'sourceCommandId' in 数据 and 数据['sourceCommandId'] is not None:#有命令
            return None#交给 command
        压缩标识=数据['compactionId'] if 'compactionId' in 数据 else None#id
        if not isinstance(压缩标识,str) or 压缩标识=='':#非法
            return None#忽略
        return {'id':压缩标识,'role':'start' if 种=='compaction/start' else 'update'}#开或更新
    return None#其余

def 压缩开始(_上下文=None,_匹配项=None):
    """等后续证据。"""
    return {}#空

def 压缩更新(上下文,匹配项):
    """委托更新压缩状态。"""
    态=上下文['state'] if 'state' in 上下文 else {}#态
    return 更新压缩状态(态 if 态 is not None else {},匹配项)#折

def 压缩建视图(上下文):
    """检查点未落地则不渲染。"""
    态=上下文['state'] if 'state' in 上下文 else None#折叠
    if 态 is None:#无
        态=回放压缩(上下文)#回退
    if 'checkpoint' not in 态 or 态['checkpoint'] is None:#无检查点
        return None#不渲染
    摘要匹配=态['summary'] if 'summary' in 态 else None#摘要
    标记=压缩摘要(摘要匹配,态['checkpoint'])#可见标记
    return 聊天节点(上下文,'compaction',标记['seq'],标记)#节点

压缩定义={#自动压缩会话节点定义
    'kind':'compaction','target':'chat',#kind/目标
    'match':压缩匹配,'start':压缩开始,'update':压缩更新,'buildViewNode':压缩建视图,#生命周期
}#结束

def 登记压缩会话节点(上下文):
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(压缩定义)#登记
