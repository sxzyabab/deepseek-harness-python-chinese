"""从已路由 Cordis 快照到对消费者中立树的纯投影。

对齐上游 `shared/cordis/projector.ts`。公开面仅中文名。
"""
from .模型 import cordis运行时树模式版本,cordis运行时源标识化#模式与源标识

__all__=[#仅中文公开名
    'cordis树源连接','cordis树源','cordis树源快照','cordis检查树','投影cordis运行时树',
]#公开面结束

def cordis树源连接(状态,reason=None):#树源连接态
    """保留的已路由快照是否仍有存活的源世代。"""
    if 状态=='connected':#已连接
        return {'state':'connected'}#已连接
    return {'state':'disconnected','reason':reason}#已断开

class cordis树源:#树源
    """一个源世代及其最新已路由 Cordis 快照。"""
    def __init__(自身,sourceId,kind,label):#构造
        """保存树源字段。"""
        自身.sourceId=sourceId#源标识
        自身.kind=kind#源种类
        自身.label=label#展示标签

class cordis树源快照:#源快照对
    """一个源世代及其最新已路由 Cordis 快照。"""
    def __init__(自身,source,snapshot,connection):#构造
        """保存源快照对字段。"""
        自身.source=source#源世代
        自身.snapshot=snapshot#已路由快照
        自身.connection=connection#连接状态

class cordis检查树:#检查树
    """投影为对消费者中立之前的已路由 Host/Client 快照。"""
    def __init__(自身,host,clients):#构造
        """保存检查树字段。"""
        自身.host=host#Host快照
        自身.clients=tuple(clients)#Client快照列表

def 投影节点(节点):#投影节点
    """投影节点。"""
    if 节点.get('kind')=='context':#Context分支
        return {'kind':'context','children':[投影节点(子) for 子 in 节点['children']]}#去句柄后递归
    return {'kind':'fiber','uid':节点['uid'],'children':[投影节点(节点['children'][0])]}#Fiber

def 投影领域(领域):#投影单个界域
    """投影单个界域。"""
    连接=领域.connection#连接态
    return {#界域
        'source':{#源身份
            'sourceId':cordis运行时源标识化(领域.source.sourceId),#投影源标识
            'kind':领域.source.kind,#种类
            'label':领域.source.label,#标签
        },#source结束
        'connection':({'state':'connected'} if 连接.get('state')=='connected' else {'state':'disconnected','reason':连接['reason']}),#连接
        'revision':领域.snapshot.revision,#修订号
        'truncated':领域.snapshot.truncated,#截断
        'root':投影节点(领域.snapshot.root),#投影根
    }#返回结束

def 投影cordis运行时树(树):#投影运行时树
    """从保留的 Cordis 快照剥去传输与活对象路由字段。"""
    return {#中立树
        'schemaVersion':cordis运行时树模式版本,#模式版本
        'host':None if 树.host is None else 投影领域(树.host),#投影Host
        'clients':[投影领域(项) for 项 in 树.clients],#投影Clients
    }#返回结束
