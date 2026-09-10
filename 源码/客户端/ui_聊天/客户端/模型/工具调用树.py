"""拥有 PTC Dispatch 配对的递归工具调用树。

对齐上游 `ui-chat/src/client/model/tool-call-tree.ts`。公开面仅中文名。
事件为会话事件 dict。
"""
import json#参数序列化

__all__=['最大工具调用树深','工具调用树']#仅中文公开名

最大工具调用树深=256#最大树深

def 同引用(左,右):
    """长度与每项 is。"""
    return len(左)==len(右) and all(甲 is 乙 for 甲,乙 in zip(左,右))#相等

class 工具调用树:
    """投影进对话快照的递归工具调用契约。"""
    def __init__(自身):
        """空表。"""
        自身.子表={}#父→子
        自身.深度={}#调用→深度
        自身.投影={}#投影缓存
        自身.修订=0#修订号

    def 重置(自身):
        """重放新窗口前忘记全部。"""
        自身.子表.clear()#清
        自身.深度.clear()#清
        自身.投影.clear()#清
        自身.修订+=1#升

    def 接受边(自身,父,子):
        """自环/已有父/超深拒。"""
        if 父==子 or 子 in 自身.深度:#自环或已有
            return False#拒
        父深=自身.深度[父] if 父 in 自身.深度 else 0#父深
        return 父深+1<=最大工具调用树深#不超深

    def 应用(自身,事件):
        """消费 PTC Dispatch 生命周期。事件为 dict。"""
        种=事件['type'] if 'type' in 事件 else None#种
        数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#载荷
        if 种=='tool/ptc-dispatch-start':#开始
            父=数据['parentCallId'] if 'parentCallId' in 数据 else None#父
            子=数据['subCallId'] if 'subCallId' in 数据 else None#子
            if 自身.接受边(父,子) is not True:#拒
                return True#仍消费
            参=数据['arguments'] if 'arguments' in 数据 else None#参数
            运行={#运行中
                'callId':子,'parentCallId':父,'name':数据['name'] if 'name' in 数据 else None,
                'argsRaw':json.dumps(参,ensure_ascii=False,separators=(',',':'),allow_nan=False),
                'turn':0,'step':0,'time':事件['time'] if 'time' in 事件 else None,'subCalls':[],
            }#结束
            兄弟=list(自身.子表[父]) if 父 in 自身.子表 and 自身.子表[父] is not None else []#兄弟
            自身.子表[父]=兄弟+[运行]#追加
            父深=自身.深度[父] if 父 in 自身.深度 else 0#父深
            自身.深度[子]=父深+1#深
            自身.修订+=1#升
            return True#消费
        if 种!='tool/ptc-dispatch':#非结果
            return False#未消费
        父=数据['parentCallId'] if 'parentCallId' in 数据 else None#父
        子=数据['subCallId'] if 'subCallId' in 数据 else None#子
        兄弟=list(自身.子表[父]) if 父 in 自身.子表 and 自身.子表[父] is not None else []#兄弟
        下标=-1#下标
        for 甲,候 in enumerate(兄弟):#扫
            号=候['callId'] if 'callId' in 候 else None#号
            if 号==子:#命中
                下标=甲#记下
                break#停
        if 下标<0 and 自身.接受边(父,子) is not True:#新边拒
            return True#消费
        正文=数据['content'] if 'content' in 数据 else None#正文
        参=数据['arguments'] if 'arguments' in 数据 else None#参数
        结算={#结果
            'kind':'tool-result','seq':事件['seq'] if 'seq' in 事件 else None,'time':事件['time'] if 'time' in 事件 else None,
            'callId':子,'call':{'name':数据['name'] if 'name' in 数据 else None,'argsRaw':json.dumps(参,ensure_ascii=False,separators=(',',':'),allow_nan=False)},
            'content':正文 if 正文 is not None else [],
            'isError':('isError' in 数据 and 数据['isError'] is True),'subCalls':[],
        }#结束
        if 下标<0:#追加
            自身.子表[父]=兄弟+[结算]#追加
            父深=自身.深度[父] if 父 in 自身.深度 else 0#父深
            自身.深度[子]=父深+1#深
        else:#替换
            换=[]#新兄弟
            for 甲,候 in enumerate(兄弟):#扫
                换.append(结算 if 甲==下标 else 候)#换
            自身.子表[父]=换#写
        自身.修订+=1#升
        return True#消费
