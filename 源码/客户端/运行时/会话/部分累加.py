"""PartialAccumulator：assistant/chunk 累加器。

对齐上游 `runtime/src/client/sessions/partial.ts`。公开面仅中文名。
把六种 StreamChunk 变体折进按块下标键控的助手块列表；块级不可变。
"""
from .会话快照 import 转助手块#导入块转换

__all__=['是否可见助手块','空助手块','部分累加器']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 是否可见助手块(类型):#是否可见块
    """一个流块会不会改 UI 展示的部分助手投影。

    @param 类型 - 流块判别标签。
    @returns 发布累加后的部分能否改变可见快照。
    """
    return 类型 in ('block-start','text-delta','reasoning-delta','tool-call-delta','block-end')#可见种类

def 空助手块(块种类):#空助手块
    """为一种流式助手块种类创建空的客户端投影。

    @param 块种类 - 线上块种类。
    @returns 准备接收增量的空投影块。
    """
    if 块种类=='text':#文本
        return {'kind':'text','text':''}#空文本
    if 块种类=='reasoning':#推理
        return {'kind':'reasoning','text':''}#空推理
    if 块种类=='tool-call':#工具调用
        return {'kind':'tool-call','callId':'','name':'','argsRaw':''}#空工具调用
    return {'kind':'other','block':None}#其它

class 部分累加器:#部分累加器
    """assistant/chunk 累加器：把 StreamChunk 折进助手块列表，块级不可变。"""

    def __init__(自身,回合,步骤,初始块=None):#绑定回合、步骤与可选前缀
        """@param 回合 - 所属智能体回合。
        @param 步骤 - 所属模型步骤。
        @param 初始块 - 历史回放之后开始累加时已物化的前缀。
        """
        if 初始块 is None:#无前缀
            初始块=[]#空
        自身.回合=回合#回合号
        自身.步骤=步骤#步骤号
        自身._块们=list(初始块)#复制前缀（故意稀疏）
        自身._已变=True#自上次快照后是否变过
        自身._快照={'turn':回合,'step':步骤,'blocks':list(初始块)}#初始快照

    def 推入(自身,块):#折一块
        """折进一块。

        @param 块 - 流块。
        @returns 是否引起可见变化（usage/finish 返回 False，跳过通知）。
        """
        类型=取字段(块,'type')#判别标签
        下标=取字段(块,'index')#块下标
        if 类型=='block-start':#块开始
            自身._确保槽(下标)#扩容
            自身._块们[下标]=空助手块(取字段(块,'blockType'))#放入空块
            自身._已变=True#标脏
            return True#可见
        if 类型=='text-delta':#文本增量
            自身._确保槽(下标)#扩容
            先前=自身._块们[下标]#该下标已有块
            旧文=取字段(先前,'text') if 取字段(先前,'kind')=='text' else ''#旧文本
            自身._块们[下标]={'kind':'text','text':旧文+取字段(块,'text')}#追加文本
            自身._已变=True#标脏
            return True#可见
        if 类型=='reasoning-delta':#推理增量
            自身._确保槽(下标)#扩容
            先前=自身._块们[下标]#该下标已有块
            旧文=取字段(先前,'text') if 取字段(先前,'kind')=='reasoning' else ''#旧推理
            自身._块们[下标]={'kind':'reasoning','text':旧文+取字段(块,'text')}#追加推理
            自身._已变=True#标脏
            return True#可见
        if 类型=='tool-call-delta':#工具调用增量
            自身._确保槽(下标)#扩容
            先前=自身._块们[下标]#该下标已有块
            if 取字段(先前,'kind')=='tool-call':#已有
                底座=先前#已有底座
            else:#空底座
                底座={'kind':'tool-call','callId':'','name':'','argsRaw':''}#空
            调用标识=取字段(底座,'callId') or str(取字段(块,'id'))#先有的 callId，否则用块 id
            名称=取字段(块,'name')#新名
            if 名称 is None:#缺新名
                名称=取字段(底座,'name')#旧名
            自身._块们[下标]={#换一块
                'kind':'tool-call',#工具调用
                'callId':调用标识,#callId
                'name':名称,#名
                'argsRaw':取字段(底座,'argsRaw')+取字段(块,'argumentsDelta'),#追加参数增量
            }#结束块
            自身._已变=True#标脏
            return True#可见
        if 类型=='block-end':#块结束
            自身._确保槽(下标)#扩容
            自身._块们[下标]=转助手块(取字段(块,'block'))#换成定稿块
            自身._已变=True#标脏
            return True#可见
        return False#usage / finish / 未知：不可见

    def 取部分(自身):#读部分投影
        """当前部分投影。

        @returns 缓存的快照（只有突变后 blocks 数组引用才会变）。
        """
        if 自身._已变:#有未发布的变化
            压实=[块 for 块 in 自身._块们 if 块 is not None]#压成渲染顺序
            自身._快照={'turn':自身.回合,'step':自身.步骤,'blocks':压实}#重建
            自身._已变=False#清脏
        return 自身._快照#稳定引用

    def _确保槽(自身,下标):#扩容稀疏数组
        """保证下标可写。"""
        while len(自身._块们)<=下标:#不够长
            自身._块们.append(None)#留下空洞
