
__all__=['查找工具调用']#仅中文公开名

def 工具节点(节点):
    """非工具则 None。节点为 dict。"""
    if 节点 is None:#空
        return None#无
    if 'kind' in 节点 and 节点['kind']=='tool-call':#工具
        return 节点#窄化
    return None#非

def 查找工具调用(快照,调用标识):
    """已在加载窗口物化时的当前工具生命周期。"""
    def 访问(块):
        """命中本块或子树。块为 dict。"""
        标识=块['callId'] if 'callId' in 块 else None#callId
        if 标识==调用标识:#命中
            return 块#返
        子列表=块['subCalls'] if 'subCalls' in 块 and 块['subCalls'] is not None else []#子
        for 子 in 子列表:#子
            找到=访问(子)#递归
            if 找到 is not None:#命中
                return 找到#返
        return None#未命中
    仓=快照['nodes']#节点 store；契约 dict
    值表=仓['values']()#全部
    for 节点 in 值表:#扫
        工具=工具节点(节点)#窄化
        if 工具 is None:#非工具
            continue#跳
        数据=工具['data'] if 'data' in 工具 else None#数据
        根=数据['root'] if 数据 is not None and 'root' in 数据 else None#根块
        if 根 is None:#非工具
            continue#跳
        找到=访问(根)#找
        if 找到 is not None:#命中
            return 找到#返
    return None#窗口内无
