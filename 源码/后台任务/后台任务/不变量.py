"""本包拥有的后台任务事件协议不变量。"""
包名='@deepseek-ai/dsh-jobs'
名称='jobs-invariant'
依赖=['invariants']
终态集合=frozenset(['completed','killed','failed'])

__all__=['包名','名称','依赖','安装','应用']

def 回读(上下文,标识,所有者):
    """注册表对 id 的当前投影；记录已消失则为 None。"""
    try:
        return 上下文.jobs.获取(标识,所有者)
    except (TypeError,KeyError,ValueError,RuntimeError):
        return None

def 检查宣布(已读,宣布,处,失败):
    """宣布的投影必须与注册表自己的读取一致。"""
    标识=str(宣布['id'])
    for 键 in ('kind','label','owner','startedAt'):
        宣布值=宣布[键] if 键 in 宣布 else None
        已读值=已读[键] if 键 in 已读 else None
        if 已读值!=宣布值:
            失败(处+' for job '+标识+' announces '+键+' '+repr(宣布值)+' while the registry reads '+repr(已读值))
    宣布总量=宣布['output']['total']
    已读总量=已读['output']['total']
    if 宣布总量>已读总量:
        失败(处+' for job '+标识+' announces output total '+str(宣布总量)+' ahead of the registry\'s '+str(已读总量))

def 安装(上下文,失败):
    """安装逐任务协议以及事件对照读取的检查。"""
    阶段表={}

    def 收事件(事件):
        """对照注册表检查一次宣布。"""
        if 事件['type']=='output':
            标识=str(事件['id'])
            已读=回读(上下文,事件['id'],事件['owner'] if 'owner' in 事件 else None)
            if 已读 is None:
                失败('output announced for job '+标识+' that the registry no longer returns')
                return
            if 事件['total']>已读['output']['total']:
                失败('output announced for job '+标识+' at total '+str(事件['total'])+' ahead of the registry\'s '+str(已读['output']['total']))
            if 标识 not in 阶段表:
                阶段表[标识]='live'
            return
        任务=事件['job']
        标识=str(任务['id'])
        阶段=阶段表[标识] if 标识 in 阶段表 else None
        终态=任务['status'] in 终态集合
        类型=事件['type']
        if 类型=='registered':
            if 阶段 is not None:
                失败('registered announced for job '+标识+' after earlier events for the same id')
            if 终态 or ('finishedAt' in 任务 and 任务['finishedAt'] is not None):
                失败('registered job '+标识+' must announce a live status without finishedAt')
        elif 类型=='progress' or 类型=='stopping':
            if 阶段=='settled':
                失败(类型+' announced for job '+标识+' after its settlement')
            if 终态:
                失败(类型+' announced for job '+标识+' with a terminal status')
        elif 类型=='settled':
            if 阶段=='settled':
                失败('settled announced twice for job '+标识)
            if not 终态:
                失败('settled job '+标识+' must announce a terminal status, got '+repr(任务['status']))
            结束=任务['finishedAt'] if 'finishedAt' in 任务 else None
            if 结束 is None or 结束<任务['startedAt']:
                失败('settled job '+标识+' must announce finishedAt no earlier than startedAt')
            if 'progress' in 任务 and 任务['progress'] is not None:
                失败('settled job '+标识+' must announce a cleared progress line')
        elif 类型=='removed':
            if 阶段=='live':
                失败('removed announced for job '+标识+' before its settlement')
            if 回读(上下文,任务['id'],任务['owner'] if 'owner' in 任务 else None) is not None:
                失败('removed announced for job '+标识+' that the registry still returns')
            阶段表.pop(标识,None)
            return
        else:
            失败('unknown job event '+str(类型)+' for job '+标识)
            return
        已读=回读(上下文,任务['id'],任务['owner'] if 'owner' in 任务 else None)
        if 已读 is None:
            失败(类型+' announced for job '+标识+' that the registry does not return')
            return
        检查宣布(已读,任务,类型,失败)
        if 类型=='settled':
            已读结束=已读['finishedAt'] if 'finishedAt' in 已读 else None
            宣布结束=任务['finishedAt'] if 'finishedAt' in 任务 else None
            if 已读['status']!=任务['status'] or 已读结束!=宣布结束:
                失败(
                    'settled job '+标识+' announces '+str(任务['status'])+' at '+str(宣布结束)
                    +' while the registry reads '+str(已读['status'])+' at '+str(已读结束)
                )
        阶段表[标识]='settled' if 类型=='settled' else 'live'

    上下文.jobs.事件.订阅({'owners':'all'},收事件)

安装.inject=['jobs']

def 应用(上下文):
    """向 invariants 登记本包，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
default=应用
