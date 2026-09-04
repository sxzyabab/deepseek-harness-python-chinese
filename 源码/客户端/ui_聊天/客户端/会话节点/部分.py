"""流式 chunk 累加为部分 Assistant 投影。

对齐上游 `ui-chat/src/client/conversation-nodes/partial.ts`。公开面仅中文名。
"""
from .事件投影 import 空助手块,转助手块#块转换

__all__=['是可见助手块','部分累加器']#仅中文公开名

def 是可见助手块(类型):#是否可见 Assistant chunk
    """发布累计部分是否可能改变可见快照。"""
    return 类型 in ('block-start','text-delta','reasoning-delta','tool-call-delta','block-end')#可见类型

class 部分累加器:#部分累加器
    """assistant/chunk 累加器：块级不可变。"""

    def __init__(自身,回合,步,初始块=None):#构造
        """记下回合步骤与初始块。"""
        自身.回合=回合#轮次
        自身.步=步#步骤
        自身.块们=list(初始块 or [])#稀疏块表
        自身.已变=True#需重建
        自身.快照={'turn':回合,'step':步,'blocks':list(初始块 or [])}#缓存

    def push(自身,块):#折入 chunk
        """usage/finish 返回 False。"""
        种=块.get('type') if isinstance(块,dict) else getattr(块,'type',None)#类型
        下标=块.get('index',0) if isinstance(块,dict) else getattr(块,'index',0)#下标
        while len(自身.块们)<=下标:#扩容
            自身.块们.append(None)#空洞
        if 种=='block-start':#块开始
            块种=块.get('blockType') if isinstance(块,dict) else getattr(块,'blockType',None)#种类
            自身.块们[下标]=空助手块(块种)#占位
            自身.已变=True#变
            return True#可见
        if 种=='text-delta':#文本增量
            旧=自身.块们[下标]#先前
            旧文=旧.get('text','') if isinstance(旧,dict) and 旧.get('kind')=='text' else ''#旧文
            文=块.get('text','') if isinstance(块,dict) else getattr(块,'text','')#增量
            自身.块们[下标]={'kind':'text','text':旧文+文}#追加
            自身.已变=True#变
            return True#可见
        if 种=='reasoning-delta':#推理增量
            旧=自身.块们[下标]#先前
            旧文=旧.get('text','') if isinstance(旧,dict) and 旧.get('kind')=='reasoning' else ''#旧文
            文=块.get('text','') if isinstance(块,dict) else getattr(块,'text','')#增量
            自身.块们[下标]={'kind':'reasoning','text':旧文+文}#追加
            自身.已变=True#变
            return True#可见
        if 种=='tool-call-delta':#工具增量
            旧=自身.块们[下标]#先前
            if isinstance(旧,dict) and 旧.get('kind')=='tool-call':#已是
                底=旧#沿用
            else:#空
                底={'kind':'tool-call','callId':'','name':'','argsRaw':''}#空
            标识=块.get('id') if isinstance(块,dict) else getattr(块,'id',None)#id
            名=块.get('name') if isinstance(块,dict) else getattr(块,'name',None)#名
            增量=块.get('argumentsDelta','') if isinstance(块,dict) else getattr(块,'argumentsDelta','')#参增量
            自身.块们[下标]={#合并
                'kind':'tool-call',#工具
                'callId':底.get('callId') or str(标识 or ''),#callId
                'name':名 if 名 is not None else 底.get('name'),#名
                'argsRaw':底.get('argsRaw','')+增量,#参数
            }#结束
            自身.已变=True#变
            return True#可见
        if 种=='block-end':#块结束
            定=块.get('block') if isinstance(块,dict) else getattr(块,'block',None)#定稿
            自身.块们[下标]=转助手块(定)#定稿
            自身.已变=True#变
            return True#可见
        return False#usage/finish

    def toPartial(自身):#取部分快照
        """块数组引用仅在变更后更换。"""
        if 自身.已变:#需重建
            自身.快照={'turn':自身.回合,'step':自身.步,'blocks':[块 for 块 in 自身.块们 if 块 is not None]}#压缩
            自身.已变=False#清
        return 自身.快照#缓存
