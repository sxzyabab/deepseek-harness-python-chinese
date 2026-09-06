"""会话节点工厂：合成序号偏移、位置解析、聊天节点信封、坐标收窄。

对齐上游 `ui-chat/src/client/conversation-nodes/common.ts`。公开面仅中文名。
"""

__all__=['聊天错误','聊天合成序号偏移','上下文位置','聊天节点','坐标']#仅中文公开名

class 聊天错误(Exception):#本包失败
    """ui-chat 包内的本地失败。"""

聊天合成序号偏移={#合成序号相对偏移
    'interruptedAssistant':-0.9,#中断 Assistant
    'interruptedFollowup':-0.8,#中断后续
    'processControl':-0.1,#过程控件
    'maxTokensNotice':0.05,#最大 token 通知
    'finalizedFollowup':0.1,#定稿后续
}#偏移结束

def 上下文位置(上下文):#从上下文取当前最佳事件位置
    """起点或首次匹配的位置，否则未解析。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点
    if 起点 is not None and 'location' in 起点:#有
        位=起点['location']#位置
        if 位 is not None:#有
            return 位#用起点
    匹配列表=上下文['matches'] if 'matches' in 上下文 else []#匹配
    if len(匹配列表)>0 and 'location' in 匹配列表[0]:#有
        位=匹配列表[0]['location']#首匹配位置
        if 位 is not None:#有
            return 位#用首匹配
    return {'kind':'unresolved'}#未解析

def 聊天节点(上下文,种类,锚点序号,数据,选项=None):#造一条最终聊天目标节点
    """用引擎持有的稳定键。"""
    if 选项 is None:#缺省
        选项={}#空
    位置=选项['location'] if 'location' in 选项 and 选项['location'] is not None else 上下文位置(上下文)#位置
    可见=选项['visibility'] if 'visibility' in 选项 else 'visible'#可见性
    return {#最终聊天节点
        'key':上下文['key'],#稳定键
        'kind':种类,#渲染器 kind
        'id':上下文['id'],#节点 id
        'target':'chat',#发到聊天面
        'anchorSeq':锚点序号,#排序锚点
        'location':位置,#位置
        'visibility':可见,#可见性
        'data':数据,#载荷
    }#结束

def 坐标(值):#读有限非负整数坐标
    """整数且 ≥0 才采纳；bool 不是坐标。"""
    if isinstance(值,bool):#bool 是 int 子类
        return None#拒
    if isinstance(值,int) and 值>=0:#非负整数
        return 值#采纳
    return None#否则
