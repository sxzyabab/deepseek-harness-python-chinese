"""已归档会话准入闸门：已归档会话及其子智能体后代在还原前不得跑模型步骤。"""
from ...内核.会话.类型 import 会话标识

名称='archived-session-gate'
依赖=['agents','sessions','workspaceRegistry']

__all__=['名称','依赖','应用','已归档会话之下']

def 已归档会话之下(上下文,智能体):
    """智能体所属会话或其子智能体谱系上的祖先是否已归档。分叉会话是独立对话。"""
    归档=上下文.workspaceRegistry.archivedSessionIds
    头=智能体.session.header
    已访=set()
    while 头['id'] not in 已访:
        if 头['id'] in 归档:
            return True
        已访.add(头['id'])
        if ('origin' not in 头 or 头['origin']!='subagent'
            or 'parentSession' not in 头 or 头['parentSession'] is None):
            return False
        父=上下文.sessions.get(头['parentSession'])
        if 父 is None:
            return 头['parentSession'] in 归档
        头=父.header
    return False

def 应用(上下文):
    """在 agent/pre-step 上拒绝已归档谱系的步骤。"""
    def 预步骤(载荷,下一步):
        """已归档则拒绝，否则交给下游。"""
        if 已归档会话之下(上下文,载荷['agent']):
            return {'kind':'reject'}
        return 下一步()
    上下文.监听('agent/pre-step',预步骤)

name=名称
inject=依赖
apply=应用
default=应用
