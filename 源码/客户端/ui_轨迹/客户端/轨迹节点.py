"""把一条轨迹贡献包进引擎拥有的 target 信封，产出轨迹视图节点。

对齐上游 `ui-trajectory/src/client/trajectory-definition-common.ts`。公开面仅中文名。
"""

__all__=['轨迹节点']#仅中文公开名

def 轨迹节点(上下文,锚点序号,数据):#组装轨迹视图节点
    """把一条贡献包进引擎拥有的 target 信封。"""
    起点=上下文['start'] if 'start' in 上下文 else None#起点匹配
    位置=起点['location'] if 起点 is not None and 'location' in 起点 else None#起点位置
    if 位置 is None:#缺省未解析
        位置={'kind':'unresolved'}#未解析位置
    return {#引擎信封字段
        'key':上下文['key'] if 'key' in 上下文 else None,#节点键
        'kind':上下文['kind'] if 'kind' in 上下文 else None,#节点种类
        'id':上下文['id'] if 'id' in 上下文 else None,#节点 id
        'target':'trajectory',#投递到轨迹槽
        'anchorSeq':锚点序号,#锚点序号
        'location':位置,#会话位置
        'data':数据,#贡献载荷
    }#视图节点结束
