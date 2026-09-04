"""拥有 Code Dispatch 配对的递归工具调用树。

对齐上游 `ui-chat/src/client/model/tool-call-tree.ts`。公开面仅中文名。
"""
import json#参数序列化

__all__=['最大工具调用树深','工具调用树']#仅中文公开名

最大工具调用树深=256#最大树深

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 同引用(左,右):#引用序列相等
    """长度与每项 is。"""
    return len(左)==len(右) and all(甲 is 乙 for 甲,乙 in zip(左,右))#相等

class 工具调用树:#工具调用树
    """投影进对话快照的递归工具调用契约。"""

    def __init__(自身):#构造
        """空表。"""
        自身.子表={}#父→子
        自身.深度={}#调用→深度
        自身.投影={}#投影缓存
        自身.修订=0#修订号

    def reset(自身):#重置
        """重放新窗口前忘记全部。"""
        自身.子表.clear()#清
        自身.深度.clear()#清
        自身.投影.clear()#清
        自身.修订+=1#升

    def acceptEdge(自身,父,子):#是否允许边
        """自环/已有父/超深拒。"""
        if 父==子 or 子 in 自身.深度:#自环或已有
            return False#拒
        父深=自身.深度.get(父,0)#父深
        return 父深+1<=最大工具调用树深#不超深

    def apply(自身,事件):#应用事件
        """消费 code-dispatch 生命周期。"""
        种=取字段(事件,'type')#种
        数据=取字段(事件,'data') or {}#载荷
        if 种=='tool/code-dispatch-start':#开始
            父=取字段(数据,'parentCallId')#父
            子=取字段(数据,'subCallId')#子
            if not 自身.acceptEdge(父,子):#拒
                return True#仍消费
            运行={#运行中
                'callId':子,'parentCallId':父,'name':取字段(数据,'name'),
                'argsRaw':json.dumps(取字段(数据,'arguments'),ensure_ascii=False),
                'turn':0,'step':0,'time':取字段(事件,'time'),'subCalls':[],
            }#结束
            兄弟=list(自身.子表.get(父) or [])#兄弟
            自身.子表[父]=兄弟+[运行]#追加
            自身.深度[子]=自身.深度.get(父,0)+1#深
            自身.修订+=1#升
            return True#消费
        if 种!='tool/code-dispatch':#非结果
            return False#未消费
        父=取字段(数据,'parentCallId')#父
        子=取字段(数据,'subCallId')#子
        兄弟=list(自身.子表.get(父) or [])#兄弟
        下标=next((甲 for 甲,候 in enumerate(兄弟) if 取字段(候,'callId')==子),-1)#下标
        if 下标<0 and not 自身.acceptEdge(父,子):#新边拒
            return True#消费
        结算={#结果
            'kind':'tool-result','seq':取字段(事件,'seq'),'time':取字段(事件,'time'),
            'callId':子,'call':{'name':取字段(数据,'name'),'argsRaw':json.dumps(取字段(数据,'arguments'),ensure_ascii=False)},
            'content':取字段(数据,'content') if 取字段(数据,'content') is not None else [],
            'isError':取字段(数据,'isError') is True,'subCalls':[],
        }#结束
        if 下标<0:#追加
            自身.子表[父]=兄弟+[结算]#追加
            自身.深度[子]=自身.深度.get(父,0)+1#深
        else:#替换
            自身.子表[父]=[结算 if 甲==下标 else 候 for 甲,候 in enumerate(兄弟)]#换
        自身.修订+=1#升
        return True#消费
