"""当前 Team 任务快照的完整依赖校验。

对齐上游 `agent-team/src/task-graph.ts`。公开面仅中文名。
"""
__all__=['任务图错误','断言任务图候选']#仅中文公开名

class 任务图错误(Exception):#包私有图失败
    """包私有的任务依赖失败，供命令错误映射保留。"""
    def __init__(自身,消息,违例):#构造
        """记下文案与稳定违例类别。"""
        super().__init__(消息)#基类
        自身.name='TeamTaskGraphError'#固定名
        自身.violation=违例#违例种类
        自身.违例=违例#中文别名

def 断言任务图候选(当前,候选):#断言任务图合法
    """在替换一个候选快照后校验完整活动任务图。"""
    任务表={取字段(任务,'id'):任务 for 任务 in 当前}#当前图
    任务表[取字段(候选,'id')]=候选#套上候选
    for 任务 in 任务表.values():#逐任务
        if 取字段(任务,'status')=='deleted':#跳过 tombstone
            continue#下一任务
        已见=set()#本任务已见 blocker
        for 阻塞标识 in 取字段(任务,'blockedBy') or []:#逐依赖
            if 阻塞标识==取字段(任务,'id'):#自指
                raise 任务图错误('team task "'+str(取字段(任务,'id'))+'" cannot block itself','cycle')#自指
            if 阻塞标识 in 已见:#重复
                raise 任务图错误(#重复
                    'team task "'+str(取字段(任务,'id'))+'" repeats blocker "'+str(阻塞标识)+'"',#文案
                    'duplicate',#种类
                )#抛出
            阻塞=任务表.get(阻塞标识)#取 blocker
            if 阻塞 is None or 取字段(阻塞,'status')=='deleted':#缺失
                raise 任务图错误(#缺失
                    'blocker task "'+str(阻塞标识)+'" for "'+str(取字段(任务,'id'))+'" is missing or deleted',#文案
                    'missing',#种类
                )#抛出
            已见.add(阻塞标识)#记已见
    访问中=set()#DFS 灰集
    已访问=set()#DFS 黑集
    def 访问(标识):#DFS
        """深度优先环检测。"""
        if 标识 in 访问中:#成环
            raise 任务图错误('task dependency cycle includes "'+str(标识)+'"','cycle')#成环
        if 标识 in 已访问:#已完成
            return#返回
        任务=任务表.get(标识)#取节点
        if 任务 is None or 取字段(任务,'status')=='deleted':#无或已删
            return#返回
        访问中.add(标识)#入灰
        for 阻塞标识 in 取字段(任务,'blockedBy') or []:#先依赖
            访问(阻塞标识)#递归
        访问中.discard(标识)#出灰
        已访问.add(标识)#入黑
    for 任务 in 任务表.values():#全图扫
        访问(取字段(任务,'id'))#访问节点

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性
