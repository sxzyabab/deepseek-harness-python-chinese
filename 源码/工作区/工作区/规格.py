"""工作区域声明：记录形态与域规格。"""
from ...存储.存储域 import 定义域,域表
__all__=[
    '工作区记录字段','工作区域状态字段','工作区记录','工作区域状态','工作区域规格',
]

工作区记录字段=('path','title','sessionIds','createdAt','updatedAt')

def _校验工作区记录(记录):
    """校验持久边界上的工作区记录形态。"""
    if not isinstance(记录,dict):
        raise TypeError('workspace record must be a dict')
    for 键 in 工作区记录字段:
        if 键 not in 记录:
            raise KeyError(f'workspace record missing {键}')
    if not isinstance(记录['sessionIds'],list):
        raise TypeError('workspace record.sessionIds must be a list')
    return 记录

工作区记录=_校验工作区记录

工作区域状态字段=('initialized','workspaceIds','archivedSessionIds')

def _校验工作区域状态(状态):
    """校验工作区域全局状态。"""
    if not isinstance(状态,dict):
        raise TypeError('workspace domain state must be a dict')
    if 'initialized' not in 状态 or 'workspaceIds' not in 状态:
        raise KeyError('workspace domain state missing required fields')
    if 'archivedSessionIds' not in 状态:#缺省归档列表
        状态={**状态,'archivedSessionIds':[]}
    if not isinstance(状态['workspaceIds'],list):
        raise TypeError('workspaceIds must be a list')
    if 'pendingMutation' in 状态 and 状态['pendingMutation'] is not None:#挂起变更
        挂起=状态['pendingMutation']
        if ('operation' not in 挂起) or 挂起['operation'] not in ('create','delete') or 'workspaceId' not in 挂起:
            raise ValueError('invalid pendingMutation')
    return 状态

工作区域状态=_校验工作区域状态

工作区域规格=定义域({
    'name':'workspace',
    'version':2,
    'global':{#全局单例
        'schema':工作区域状态,
        'initial':{'initialized':False,'workspaceIds':[],'archivedSessionIds':[]},#未引导初始态
    },
    'tables':{'workspaces':域表(工作区记录)},
})
