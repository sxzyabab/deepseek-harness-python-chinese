from ..约定.快照 import 聊天节点源#可观察源

__all__=['空源','用回合数据值']#仅中文公开名

def 空快照():
    '空源快照恒为 None'
    return None#无值

def 空拆除():
    '空订阅无可拆'
    return None#无事

def 空订阅(*位置参数):
    '空源不通知'
    return 空拆除#拆除器

空源=聊天节点源(空快照,空订阅)#缺席时的空源

def 读源快照(源):
    '对象走方法；外部仍可能交来同名键'
    取=getattr(源,'getSnapshot',None)#方法
    if callable(取):
        return 取()#读
    if isinstance(源,dict):#键
        函数=源.get('getSnapshot')#键
        if callable(函数):
            return 函数()#读
    return None#无

def 用回合数据值(数据,键):
    '节点在回合外时数据缺席则空源。数据为带 source 的 dict'
    源=空源#默认
    if 数据 is not None and 'source' in 数据:#有 store
        命中=数据['source'](键)#按键
        源=命中 if 命中 is not None else 空源#缺则空
    return 读源快照(源)#当前值
