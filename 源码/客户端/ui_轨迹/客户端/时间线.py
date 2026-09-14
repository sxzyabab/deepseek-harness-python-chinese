from .轨迹记录 import 格式化毫秒时长#毫秒格式化

__all__=['格式化时间线偏移','派生轨迹时间线','轨迹时间线焦点下标']#仅中文公开名

def 格式化时间线偏移(毫秒):#格式化时间线偏移标签
    """把时间线时长格式化成整毫秒标签。"""
    return 格式化毫秒时长(毫秒)#委托整毫秒格式化

def 车道于(种类):#按格子种类选稳定三车道中的一道
    """工具与子工具走第 2 道；消息与压缩块走第 1 道；其余走第 0 道。"""
    if 种类 in ('tool','subtool'):#工具类
        return 2#第 2 道
    if 种类 in ('message','compacted'):#消息/压缩
        return 1#第 1 道
    return 0#其余

def 单元格区间(单元格):#格子的记录时间闭区间
    """从格子读出记录时间闭区间；没有起点则无法投影。有限性由布局入口 有限时间 校验。"""
    if 'startedAt' not in 单元格 or 单元格['startedAt'] is None:#没有起点
        return None#无法投影
    起点=单元格['startedAt']#起点
    秒=单元格['timeSeconds'] if 'timeSeconds' in 单元格 else None#自身秒数
    时长毫秒=max(0,秒*1000) if 秒 is not None else 0#有秒数才换算
    return {'start':起点,'end':起点+时长毫秒}#闭区间

def 跨度排序键(项):#按起点再终点
    """时间线扫描序。"""
    return (项['start'],项['end'])#键

def 派生定时时间线(轮次列表,实际时长,压缩空闲):#按记录时间派生时间线
    """按记录时间投影；可选择保留实际时长，以及是否压缩空闲间隙。"""
    定时轮=[]#有时间跨度的回合
    for 轮 in 轮次列表:#逐回合
        原始跨度=[]#本回合跨度
        组列表=轮['groups'] if 'groups' in 轮 and 轮['groups'] is not None else []#各组
        for 组 in 组列表:#各组
            格列表=组['cells'] if 'cells' in 组 and 组['cells'] is not None else []#各格
            for 单元格 in 格列表:#各格
                if 'requestOnly' in 单元格 and 单元格['requestOnly'] is True:#仅请求
                    continue#跳过
                区间=单元格区间(单元格)#读起止
                if 区间 is None:#无起点
                    continue#跳过
                种类=单元格['kind'] if 'kind' in 单元格 else None#种类
                原始跨度.append({#投影一条跨度
                    **区间,#起止
                    'index':单元格['index'] if 'index' in 单元格 else None,#账本下标
                    'isError':('isError' in 单元格 and 单元格['isError'] is True),#是否错误
                    'kind':种类,#种类
                    'label':单元格['text'] if 'text' in 单元格 else None,#文案
                    'lane':车道于(种类),#车道
                })#跨度结束
        if len(原始跨度)>0:#有跨度
            定时轮.append({'turn':轮['turn'] if 'turn' in 轮 else None,'rawSpans':原始跨度})#收下回合
    全部=[跨 for 轮 in 定时轮 for 跨 in 轮['rawSpans']]#全部原始跨度
    if len(全部)==0:#没有任何带时间的记录
        return None#无模型
    已去空闲按跨={}#每条跨度前已去掉的空闲量
    已去空闲=0#累计已去掉空闲
    覆盖到=None#已覆盖到的最晚终点
    for 跨 in sorted(全部,key=跨度排序键):#按起点再终点排序后扫
        if 压缩空闲 and 覆盖到 is not None and 跨['start']>覆盖到:#压缩空闲且出现间隙
            已去空闲+=跨['start']-覆盖到#间隙计入
        已去空闲按跨[id(跨)]=已去空闲#记下本跨度前的空闲偏移
        覆盖到=跨['end'] if 覆盖到 is None else max(覆盖到,跨['end'])#推进覆盖终点
    跨度列表=[]#投影跨度
    回合边界=[]#回合边界
    for 轮 in 定时轮:#按回合投影
        投影=[]#本回合投影
        for 跨 in 轮['rawSpans']:#逐跨度
            身份=id(跨)#跨度身份
            偏移=已去空闲按跨[身份] if 身份 in 已去空闲按跨 else 0#空闲偏移
            投影.append({#投影后的跨度
                **跨,#保留下标种类等
                'start':跨['start']-偏移,#起点去掉空闲
                'end':(跨['end'] if 实际时长 else 跨['start'])-偏移,#实际时长用终点，否则收成时间点
            })#投影结束
        跨度列表.extend(投影)#并入总跨度
        if 轮['turn'] is not None:#有回合号
            回合边界.append({'turn':轮['turn'],'time':min(项['start'] for 项 in 投影)})#最早投影起点
    return {#组装时间模型
        'start':min(项['start'] for 项 in 跨度列表),#最早起点
        'end':max(项['end'] for 项 in 跨度列表),#最晚终点
        'spans':跨度列表,#投影跨度
        'turnBoundaries':回合边界,#回合边界
    }#模型结束

def 派生轨迹时间线(轮次列表,模式='sequence'):#派生轨迹时间线模型
    """把每条可见记录投影到稳定的三车道时间线；没有可见记录时为 None。"""
    if 模式!='sequence':#非序列模式走时间投影
        return 派生定时时间线(轮次列表,模式 in ('duration','actual'),模式=='duration')#按时长或时刻投影
    跨度列表=[]#序列跨度累加器
    回合边界=[]#回合边界累加器
    for 轮 in 轮次列表:#逐回合
        组列表=轮['groups'] if 'groups' in 轮 and 轮['groups'] is not None else []#各组
        单元格列表=[]#摊平
        for 组 in 组列表:#各组
            格列表=组['cells'] if 'cells' in 组 and 组['cells'] is not None else []#各格
            for 单元格 in 格列表:#各格
                if 'requestOnly' in 单元格 and 单元格['requestOnly'] is True:#仅请求
                    continue#跳过
                单元格列表.append(单元格)#收下
        if len(单元格列表)==0:#无可见
            continue#跳过
        基数=len(跨度列表)#当前序列位置
        回合=轮['turn'] if 'turn' in 轮 else None#回合号
        if 回合 is not None:#有编号
            回合边界.append({'turn':回合,'time':基数})#边界
        for 偏移,单元格 in enumerate(单元格列表):#各占一格
            种类=单元格['kind'] if 'kind' in 单元格 else None#种类
            跨度列表.append({#序列跨度
                'start':基数+偏移,#起点
                'end':基数+偏移+1,#终点
                'index':单元格['index'] if 'index' in 单元格 else None,#下标
                'isError':('isError' in 单元格 and 单元格['isError'] is True),#错误
                'kind':种类,#种类
                'label':单元格['text'] if 'text' in 单元格 else None,#文案
                'lane':车道于(种类),#车道
            })#跨度结束
    if len(跨度列表)==0:#没有任何跨度
        return None#无模型
    return {'start':0,'end':len(跨度列表),'spans':跨度列表,'turnBoundaries':回合边界}#序列模型

def 轨迹时间线焦点下标(轮次列表,区间,模式='sequence'):#焦点区间内的记录下标
    """找出闭区间选区内任一时刻处于活动的记录。"""
    模型=派生轨迹时间线(轮次列表,模式)#先派生全域模型
    if 模型 is None:#无模型
        return set()#空
    起点=区间['start']#选区起点
    终点=区间['end']#选区终点
    return {跨['index'] for 跨 in 模型['spans'] if 跨['start']<=终点 and 跨['end']>=起点}#与选区相交
