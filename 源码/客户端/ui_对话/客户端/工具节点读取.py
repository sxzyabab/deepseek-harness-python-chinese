"""经内部聊天节点索引读工具生命周期。

对齐上游 `ui-conversation/src/client/chat/tool-node-reader.ts`。公开面仅中文名。
快照、节点与块为 dict；节点仓为含 get/values 的 dict。
"""

__all__=['根工具调用','查找工具调用','工具节点']#仅中文公开名

def 工具上下文键(种,标识):
    """对齐 conversationContextKey。"""
    return f'{种}:{标识}'#种:id

def 工具节点(节点):
    """仅 kind 为 tool-call 时返回。"""
    if 节点 is None:#空
        return None#无
    if 'kind' in 节点 and 节点['kind']=='tool-call':#匹配
        return 节点#原样
    return None#否

def 根工具调用(快照,根调用标识):
    """当前窗口已物化则返回根块。"""
    聊天=快照['chat'] if 快照 is not None and 'chat' in 快照 else None#聊天面
    节点表=聊天['nodes'] if 聊天 is not None and 'nodes' in 聊天 else None#节点仓
    if 节点表 is None:#无仓
        return None#无
    节点=节点表['get'](工具上下文键('tool-call',根调用标识))#仓 get
    工具=工具节点(节点)#收窄
    if 工具 is None:#非工具
        return None#无
    数据=工具['data'] if 'data' in 工具 else None#数据
    return 数据['root'] if 数据 is not None and 'root' in 数据 else None#根生命周期

def 查找工具调用(快照,调用标识):
    """深度优先走子调用树。"""
    def 访问(块):
        """命中本块或子树。"""
        标识=块['callId'] if 'callId' in 块 else None#callId
        if 标识==调用标识:#命中
            return 块#本块
        子列表=块['subCalls'] if 'subCalls' in 块 and 块['subCalls'] is not None else []#子
        for 子 in 子列表:#子调用
            命中=访问(子)#递归
            if 命中 is not None:#命中
                return 命中#短路
        return None#未命中
    聊天=快照['chat'] if 快照 is not None and 'chat' in 快照 else None#聊天面
    节点表=聊天['nodes'] if 聊天 is not None and 'nodes' in 聊天 else None#节点仓
    if 节点表 is None:#无表
        return None#无
    迭代=节点表['values']()#仓 values
    for 节点 in 迭代:#逐节点
        工具=工具节点(节点)#收窄
        if 工具 is None:#非工具
            continue#跳过
        数据=工具['data'] if 'data' in 工具 else None#数据
        根=数据['root'] if 数据 is not None and 'root' in 数据 else None#根
        if 根 is None:#非工具
            continue#跳过
        命中=访问(根)#查找
        if 命中 is not None:#命中
            return 命中#返回
    return None#未物化
