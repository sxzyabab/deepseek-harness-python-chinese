"""工作区域声明：记录 schema 与 defineDomain spec。对齐上游 workspace/src/spec.ts。"""
from ...存储.存储域 import 定义域,域表#域声明原语
__all__=[#仅中文公开名
    '工作区记录字段','工作区域状态字段','工作区记录','工作区域状态','工作区域域规格',
]#公开面结束

工作区记录字段=('path','title','sessionIds','createdAt','updatedAt')#持久记录字段

def _校验工作区记录(记录):#校验一条工作区记录
    """校验持久边界上的工作区记录形态。"""
    if not isinstance(记录,dict):#必须是映射
        raise TypeError('workspace record must be a dict')#拒绝
    for 键 in 工作区记录字段:#必填键
        if 键 not in 记录:#缺失
            raise KeyError(f'workspace record missing {键}')#拒绝
    if not isinstance(记录['sessionIds'],list):#成员必须是列表
        raise TypeError('workspace record.sessionIds must be a list')#拒绝
    return 记录#通过

工作区记录=_校验工作区记录#校验器别名

工作区域状态字段=('initialized','workspaceIds','archivedSessionIds')#全局状态字段

def _校验工作区域状态(状态):#校验域全局状态
    """校验工作区域全局状态。"""
    if not isinstance(状态,dict):#必须是映射
        raise TypeError('workspace domain state must be a dict')#拒绝
    if 'initialized' not in 状态 or 'workspaceIds' not in 状态:#必填
        raise KeyError('workspace domain state missing required fields')#拒绝
    if 'archivedSessionIds' not in 状态:#缺省归档列表
        状态={**状态,'archivedSessionIds':[]}#补默认
    if not isinstance(状态['workspaceIds'],list):#顺序必须是列表
        raise TypeError('workspaceIds must be a list')#拒绝
    if 状态.get('pendingMutation') is not None:#挂起变更
        挂起=状态['pendingMutation']#取出
        if 挂起.get('operation') not in ('create','delete') or 'workspaceId' not in 挂起:#非法
            raise ValueError('invalid pendingMutation')#拒绝
    return 状态#通过

工作区域状态=_校验工作区域状态#校验器别名

工作区域域规格=定义域({#工作区域 spec
    'name':'workspace',#域名
    'version':2,#域版本
    'global':{#全局单例
        'schema':工作区域状态,#全局 schema
        'initial':{'initialized':False,'workspaceIds':[],'archivedSessionIds':[]},#未引导初始态
    },#global 结束
    'tables':{'workspaces':域表(工作区记录)},#工作区表
})#spec 结束
