__all__=['空源','用回合数据值']#仅中文公开名

def 空快照():
    """空源快照恒为 None。"""
    return None#无值

def 空拆除():
    """空订阅无可拆。"""
    return None#无事

def 空订阅(*位置参数):
    """空源不通知。"""
    return 空拆除#拆除器

空源={#缺席时的空源
    'getSnapshot':空快照,#恒 None
    'subscribe':空订阅,#空订阅
}#EMPTY_SOURCE 结束

def 用回合数据值(数据,键):
    """节点在回合外时数据缺席则空源。数据为带 source 的 dict。"""
    源=空源#默认
    if 数据 is not None and 'source' in 数据:#有 store
        命中=数据['source'](键)#按键
        源=命中 if 命中 is not None else 空源#缺则空
    return 源['getSnapshot']()#当前值
