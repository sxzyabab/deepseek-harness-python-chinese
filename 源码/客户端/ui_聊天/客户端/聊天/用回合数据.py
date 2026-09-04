"""订阅某回合按键位置数据 store 中的一个值。

对齐上游 `ui-chat/src/client/chat/use-turn-data.ts`。公开面仅中文名。
"""

__all__=['空源','用回合数据值']#仅中文公开名

空源={#缺席时的空源
    'getSnapshot':lambda:None,#恒 None
    'subscribe':lambda *_:(lambda:None),#空订阅
}#EMPTY_SOURCE 结束

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 用回合数据值(数据,键):#读回合数据键值
    """节点在回合外时数据缺席则空源。"""
    源=空源#默认
    if 数据 is not None:#有 store
        取源=取字段(数据,'source')#source 方法
        if callable(取源):#可调
            源=取源(键) or 空源#按键
    取快=取字段(源,'getSnapshot')#快照
    return 取快() if callable(取快) else None#当前值
