__all__=['轨迹节点']

def 轨迹节点(上下文,锚点序号,数据):
    '把一条贡献包进引擎拥有的 target 信封'
    起点=上下文.get('start')#起始匹配
    位置=None#位置
    if isinstance(起点,dict):
        位置=起点.get('location')#匹配上的位置
    if 位置 is None:
        位置={'kind':'unresolved'}#尚未定位
    return {
        'key':上下文['key'],#上下文键
        'kind':上下文['kind'],#定义种类
        'id':上下文['id'],#业务身份
        'target':'trajectory',#轨迹目标
        'anchorSeq':锚点序号,#排序锚点
        'location':位置,#会话位置
        'data':数据,#贡献
    }
