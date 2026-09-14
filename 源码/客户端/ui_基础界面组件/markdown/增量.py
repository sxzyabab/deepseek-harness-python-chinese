
__all__=['未稳定尾部块数','增量Markdown解析器','块键']#仅中文公开名

未稳定尾部块数=2#保持未稳定的尾部块数

def 块键(节点,基址,下标):
    """绝对源码起始偏移；无 position 则负下标。节点为 dict。"""
    位=节点['position'] if 'position' in 节点 else None#位
    起点=None#start
    if 位 is not None:#有
        起=位['start'] if 'start' in 位 else None#start
        if 起 is not None:#有
            起点=起['offset'] if 'offset' in 起 else None#offset
    if 起点 is None:#缺
        return -(下标+1)#负下标
    return 基址+起点#绝对偏移

class 增量Markdown解析器:#只追加增量 markdown 解析器
    """调用方提供语法；一个实例累计一份流式文档。"""
    def __init__(自身,解析):
        """parse 与渲染这些块共用，切点才一致。"""
        自身.解析=解析#语法
        自身.上次文本=''#上次累计全文
        自身.尾起点=0#未稳定尾部在全文中的起点
        自身.已冻结=[]#已冻结的顶层块
        自身.代际=0#代际；非追加重置时递增
        自身.缓存=None#上次 update 结果

    def 更新(自身,文本):
        """相同输入幂等；非追加则换代丢掉冻结前缀。"""
        if 自身.缓存 is not None and 文本==自身.上次文本:#相同
            return 自身.缓存#缓存
        if 文本.startswith(自身.上次文本) is False:#不是追加
            自身.上次文本=''#清空
            自身.尾起点=0#回到文首
            自身.已冻结=[]#丢掉
            自身.代际+=1#换代
        自身.上次文本=文本#记下
        基址=自身.尾起点#切片基址
        根=自身.解析(文本[基址:])#只解析尾部
        块列=根['children'] if 'children' in 根 else None#子
        块列表=块列 if 块列 is not None else []#空则空表
        首未稳=max(0,len(块列表)-未稳定尾部块数)#第一个未稳定下标；判 length
        if 首未稳>0:#有可冻结前缀
            切点块=块列表[首未稳-1]#上一冻结块
            位=切点块['position'] if 'position' in 切点块 else None#位
            终=None#end.offset
            if 位 is not None:#有
                止=位['end'] if 'end' in 位 else None#end
                if 止 is not None:#有
                    终=止['offset'] if 'offset' in 止 else None#offset
            if 终 is None:#语法省略 position
                首未稳=0#全部留尾
            else:#有切点
                for 节点 in 块列表[:首未稳]:#将冻结
                    自身.已冻结.append({#冻结块
                        'node':节点,#节点
                        'key':块键(节点,基址,len(自身.已冻结)),#稳定 key
                    })#结束
                自身.尾起点=基址+终#下次只解析切点后
        尾=[]#未冻结尾部
        for 下标,节点 in enumerate(块列表[首未稳:]):#切尾
            尾.append({'node':节点,'key':块键(节点,基址,下标)})#赋 key
        自身.缓存={#本次分割
            'frozen':list(自身.已冻结),#已冻
            'tail':尾,#尾
            'generation':自身.代际,#代
        }#结束
        return 自身.缓存#返回
