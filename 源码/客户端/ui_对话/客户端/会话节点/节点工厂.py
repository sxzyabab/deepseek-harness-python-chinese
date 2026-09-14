__all__=['聊天合成序号偏移','上下文位置','聊天节点','坐标']#仅中文公开名

聊天合成序号偏移={#合成序号相对偏移
    'interruptedAssistant':-0.9,#打断助手：落在关边界之前
    'interruptedFollowup':-0.8,#打断后的后续节点
    'maxTokensNotice':0.05,#max-tokens 提示：助手与回合尾之间
    'finalizedFollowup':0.1,#普通定稿后的后续
}#偏移结束

def 上下文位置(上下文):
    """从上下文取当前最佳事件位置。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    if 起点 is not None and 'location' in 起点 and 起点['location'] is not None:
        return 起点['location']#用起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 else []#匹配
    if len(匹配列表)>0 and 'location' in 匹配列表[0] and 匹配列表[0]['location'] is not None:
        return 匹配列表[0]['location']#用首匹配
    return {'kind':'unresolved'}#未解析

def 聊天节点(上下文,种类,锚点序号,数据,选项=None):
    """用引擎持有的稳定键。"""
    选项={} if 选项 is None else 选项#缺省
    if 'location' in 选项 and 选项['location'] is not None:
        位置=选项['location']#显式位置
    else:
        位置=上下文位置(上下文)#推导
    可见=选项['visibility'] if 'visibility' in 选项 else 'visible'#可见性
    return {#最终聊天节点
        'key':上下文['key'] if 'key' in 上下文 else None,#稳定键
        'kind':种类,#渲染器 kind
        'id':上下文['id'] if 'id' in 上下文 else None,#节点 id
        'target':'chat',#发到聊天面
        'anchorSeq':锚点序号,#排序锚点
        'location':位置,#位置
        'visibility':可见,#可见性
        'data':数据,#载荷
    }#结束

def 坐标(值):
    """有限非负整数坐标。bool 先排除。"""
    if isinstance(值,bool):
        return None#拒
    if isinstance(值,int) and 值>=0:
        return 值#采纳
    return None#否则
