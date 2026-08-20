"""对只追加文本流做块级增量 markdown 解析。

对齐上游 `ui-primitives/src/markdown/incremental.ts`。公开面仅中文名。
每个流式分块若重解析整份累计文档，成本对最终回复长度是二次的。
CommonMark 块解析按行进行，追加文本最多只能改写解析前沿——最后一个顶层块——
因此更早的块已经定稿。本解析器冻结除末尾未稳定尾部块以外的全部块，
只重解析它们后面的源码尾部。
"""

__all__=['未稳定尾部块数','增量Markdown解析器','块键']#仅中文公开名

未稳定尾部块数=2#保持未稳定的尾部块数

def 块键(节点,基址,下标):#块的稳定渲染 key
    """绝对源码起始偏移；无 position 则负下标。"""
    位=None#position
    if isinstance(节点,dict):#映射
        位=节点.get('position')#位
    else:#对象
        位=getattr(节点,'position',None)#位
    起点=None#start
    if 位 is not None:#有
        起=位.get('start') if isinstance(位,dict) else getattr(位,'start',None)#start
        if 起 is not None:#有
            起点=起.get('offset') if isinstance(起,dict) else getattr(起,'offset',None)#offset
    if 起点 is None:#缺
        return -(下标+1)#负下标
    return 基址+起点#绝对偏移

class 增量Markdown解析器:#只追加增量 markdown 解析器
    """调用方提供语法；一个实例累计一份流式文档。"""

    def __init__(自身,解析):#注入语法
        """parse 与渲染这些块共用，切点才一致。"""
        自身.解析=解析#语法
        自身.上次文本=''#上次累计全文
        自身.尾起点=0#未稳定尾部在全文中的起点
        自身.已冻结=[]#已冻结的顶层块
        自身.代际=0#代际；非追加重置时递增
        自身.缓存=None#上次 update 结果

    def 更新(自身,文本):#折叠累计文本，给出冻结/尾部分割
        """相同输入幂等；非追加则换代丢掉冻结前缀。"""
        if 自身.缓存 is not None and 文本==自身.上次文本:#相同
            return 自身.缓存#缓存
        if not 文本.startswith(自身.上次文本):#不是追加
            自身.上次文本=''#清空
            自身.尾起点=0#回到文首
            自身.已冻结=[]#丢掉
            自身.代际+=1#换代
        自身.上次文本=文本#记下
        基址=自身.尾起点#切片基址
        根=自身.解析(文本[基址:])#只解析尾部
        if isinstance(根,dict):#映射根
            块们=根.get('children') or []#子
        else:#对象根
            块们=getattr(根,'children',None) or []#子
        首未稳=max(0,len(块们)-未稳定尾部块数)#第一个未稳定下标
        if 首未稳>0:#有可冻结前缀
            切点块=块们[首未稳-1]#上一冻结块
            位=切点块.get('position') if isinstance(切点块,dict) else getattr(切点块,'position',None)#位
            终=None#end.offset
            if 位 is not None:#有
                止=位.get('end') if isinstance(位,dict) else getattr(位,'end',None)#end
                if 止 is not None:#有
                    终=止.get('offset') if isinstance(止,dict) else getattr(止,'offset',None)#offset
            if 终 is None:#语法省略 position
                首未稳=0#全部留尾
            else:#有切点
                for 节点 in 块们[:首未稳]:#将冻结
                    自身.已冻结.append({#冻结块
                        'node':节点,#节点
                        'key':块键(节点,基址,len(自身.已冻结)),#稳定 key
                    })#结束
                自身.尾起点=基址+终#下次只解析切点后
        尾=[]#未冻结尾部
        for 下标,节点 in enumerate(块们[首未稳:]):#切尾
            尾.append({'node':节点,'key':块键(节点,基址,下标)})#赋 key
        自身.缓存={#本次分割
            'frozen':list(自身.已冻结),#已冻
            'tail':尾,#尾
            'generation':自身.代际,#代
        }#结束
        return 自身.缓存#返回
