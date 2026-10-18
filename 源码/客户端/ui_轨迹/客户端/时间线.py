import math
from .轨迹记录 import 格式化毫秒时长#毫秒标签

__all__=['格式化时间线偏移','派生轨迹时间线','轨迹时间线焦点下标']

def 格式化时间线偏移(毫秒):
    '把时间线时长格式化成整毫秒标签'
    return 格式化毫秒时长(毫秒)

def 车道于(种类):
    '工具与子工具走第 2 道；消息与压缩块走第 1 道；其余走第 0 道'
    if 种类 in ('tool','subtool'):
        return 2
    if 种类 in ('message','compacted'):
        return 1
    return 0

def 有限(值):
    '有限数才可投影'
    return 值 is not None and not isinstance(值,bool) and isinstance(值,(int,float)) and math.isfinite(值)

def 派生轨迹时间线(轮次列表,模式='sequence'):
    '按记录时间或等宽操作投影；没有可见记录时为 None'
    if 模式!='sequence':
        实际时长=模式 in ('duration','actual')#保留各段真实长度
        压缩空闲=模式=='duration'#去掉空闲间隙
        定时轮次=[]
        for 轮次 in 轮次列表:
            原始跨度=[]
            for 组 in 轮次['groups']:
                for 格 in 组['cells']:
                    if 格.get('requestOnly') is True:
                        continue
                    if not 有限(格.get('startedAt')):
                        continue
                    时长毫秒=max(0,格['timeSeconds']*1000) if 有限(格.get('timeSeconds')) else 0
                    原始跨度.append({
                        'start':格['startedAt'],
                        'end':格['startedAt']+时长毫秒,
                        'index':格['index'],
                        'isError':格.get('isError') is True,
                        'kind':格['kind'],
                        'label':格.get('text') or '',
                        'lane':车道于(格['kind']),
                    })
            if len(原始跨度)>0:
                定时轮次.append({'turn':轮次['turn'],'rawSpans':原始跨度})
        全部原始=[]
        for 轮次 in 定时轮次:
            全部原始.extend(轮次['rawSpans'])
        if len(全部原始)==0:
            return None
        已去掉={}
        累计去掉=0
        覆盖到=None
        for 跨度 in sorted(全部原始,key=lambda 项:(项['start'],项['end'])):
            if 压缩空闲 and 覆盖到 is not None and 跨度['start']>覆盖到:
                累计去掉+=跨度['start']-覆盖到
            已去掉[id(跨度)]=累计去掉
            覆盖到=跨度['end'] if 覆盖到 is None else max(覆盖到,跨度['end'])
        跨度列表=[]
        轮次边界=[]
        for 轮次 in 定时轮次:
            投影=[]
            for 跨度 in 轮次['rawSpans']:
                偏移=已去掉.get(id(跨度),0)
                终点=跨度['end'] if 实际时长 else 跨度['start']
                投影.append({
                    **跨度,
                    'start':跨度['start']-偏移,
                    'end':终点-偏移,
                })
            跨度列表.extend(投影)
            if 轮次['turn'] is not None:
                轮次边界.append({
                    'turn':轮次['turn'],
                    'time':min(项['start'] for 项 in 投影),
                })
        return {
            'start':min(项['start'] for 项 in 跨度列表),
            'end':max(项['end'] for 项 in 跨度列表),
            'spans':跨度列表,
            'turnBoundaries':轮次边界,
        }
    跨度列表=[]
    轮次边界=[]
    for 轮次 in 轮次列表:
        格子=[]
        for 组 in 轮次['groups']:
            for 格 in 组['cells']:
                if 格.get('requestOnly') is not True:
                    格子.append(格)
        if len(格子)==0:
            continue
        if 轮次['turn'] is not None:
            轮次边界.append({'turn':轮次['turn'],'time':len(跨度列表)})
        起点=len(跨度列表)
        for 偏移,格 in enumerate(格子):
            跨度列表.append({
                'start':起点+偏移,
                'end':起点+偏移+1,
                'index':格['index'],
                'isError':格.get('isError') is True,
                'kind':格['kind'],
                'label':格.get('text') or '',
                'lane':车道于(格['kind']),
            })
    if len(跨度列表)==0:
        return None
    return {
        'start':0,
        'end':len(跨度列表),
        'spans':跨度列表,
        'turnBoundaries':轮次边界,
    }

def 轨迹时间线焦点下标(轮次列表,区间,模式='sequence'):
    '找出闭区间选区内任一时刻处于活动的记录'
    模型=派生轨迹时间线(轮次列表,模式)
    if 模型 is None:
        return set()
    return set(
        跨度['index']
        for 跨度 in 模型['spans']
        if 跨度['start']<=区间['end'] and 跨度['end']>=区间['start']
    )
