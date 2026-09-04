"""与 CDP 无关的 Cordis Context/Fiber 树快照模型。

对齐上游 `shared/cordis/snapshot.ts`。公开面仅中文名。
"""
from ..json import 是否普通对象#普通对象
from ..校验 import 精确键,精确对象,线上标识#校验

__all__=[#仅中文公开名
    'cordis树模式版本','cordis树最大深度',
    'cordis上下文树节点','cordis纤程树节点','cordis树节点','cordis树快照',
    '解析cordis树快照',
]#公开面结束

cordis树模式版本=0#快照模式版本
cordis树最大深度=256#最大嵌套深度

def cordis上下文树节点(objectHandle,children):#Context树节点
    """Cordis 树快照中的一个 Context 实体。"""
    return {'kind':'context','objectHandle':objectHandle,'children':tuple(children)}#Context

def cordis纤程树节点(objectHandle,uid,children):#Fiber树节点
    """Cordis 树快照中的一个 Fiber 实体。"""
    return {'kind':'fiber','objectHandle':objectHandle,'uid':uid,'children':tuple(children)}#Fiber

cordis树节点=dict#树节点联合

class cordis树快照:#树快照
    """一个界域可达 Cordis 树的不可变、可序列化状态。"""
    def __init__(自身,schemaVersion,revision,objectRegistryId,root,truncated):#构造
        """保存树快照字段。"""
        自身.schemaVersion=schemaVersion#模式版本
        自身.revision=revision#修订号
        自身.objectRegistryId=objectRegistryId#对象注册表标识
        自身.root=root#根Context
        自身.truncated=truncated#是否截断

def 解析节点(值,状态,最大节点,深度):#解析树节点
    """解析树节点。"""
    if 深度>cordis树最大深度:#超深
        raise Exception('inspector protocol: Cordis tree exceeds the depth limit')#英文诊断
    状态['count']+=1#计数
    if 状态['count']>最大节点:#超节点数
        raise Exception(f'inspector protocol: Cordis tree exceeds {最大节点} nodes')#英文诊断
    if not 是否普通对象(值) or 值.get('kind') not in ('context','fiber'):#种类未知
        raise Exception('inspector protocol: Cordis tree node must have a known kind')#英文诊断
    对象句柄=线上标识(值.get('objectHandle'),'objectHandle')#对象句柄
    if 对象句柄 in 状态['handles']:#重复句柄
        raise Exception('inspector protocol: Cordis tree repeats an object handle')#英文诊断
    状态['handles'].add(对象句柄)#记入句柄
    if not isinstance(值.get('children'),list):#children须数组
        raise Exception('inspector protocol: Cordis tree node children must be an array')#英文诊断
    if 值['kind']=='context':#Context分支
        精确键(值,['kind','objectHandle','children'],'Context tree node')#精确字段
        return {'kind':'context','objectHandle':对象句柄,'children':[解析节点(子,状态,最大节点,深度+1) for 子 in 值['children']]}#递归
    精确键(值,['kind','objectHandle','uid','children'],'Fiber tree node')#Fiber精确字段
    uid=值['uid']#uid
    if not isinstance(uid,int) or isinstance(uid,bool) or uid<1:#uid非法
        raise Exception('inspector protocol: Cordis Fiber uid must be a positive safe integer')#英文诊断
    if uid in 状态['fiberUids']:#重复uid
        raise Exception('inspector protocol: Cordis tree repeats a Fiber uid')#英文诊断
    状态['fiberUids'].add(uid)#记入uid
    if len(值['children'])!=1:#须一子
        raise Exception('inspector protocol: Cordis Fiber must own exactly one Context')#英文诊断
    上下文=解析节点(值['children'][0],状态,最大节点,深度+1)#解析唯一子
    if 上下文.get('kind')!='context':#子须Context
        raise Exception('inspector protocol: Cordis Fiber child must be a Context')#英文诊断
    return {'kind':'fiber','objectHandle':对象句柄,'uid':uid,'children':[上下文]}#Fiber

def 解析cordis树快照(值,最大节点):#解析树快照
    """解码并校验一次完整的 Cordis 树替换。"""
    记录=精确对象(值,['schemaVersion','revision','objectRegistryId','root','truncated'],'Cordis tree')#精确对象
    修订=记录['revision']#修订号
    if 记录['schemaVersion']!=cordis树模式版本 or not isinstance(修订,int) or isinstance(修订,bool) or 修订<1 or not isinstance(记录['truncated'],bool):#头非法
        raise Exception('inspector protocol: invalid Cordis tree header')#英文诊断
    状态={'count':0,'handles':set(),'fiberUids':set()}#解析状态
    根=解析节点(记录['root'],状态,最大节点,0)#解析根
    if 根.get('kind')!='context':#根须Context
        raise Exception('inspector protocol: Cordis tree root must be a Context')#英文诊断
    return cordis树快照(#快照
        schemaVersion=cordis树模式版本,#模式版本
        revision=修订,#修订号
        objectRegistryId=线上标识(记录['objectRegistryId'],'objectRegistryId'),#注册表标识
        root=根,#根
        truncated=记录['truncated'],#截断
    )#返回结束
