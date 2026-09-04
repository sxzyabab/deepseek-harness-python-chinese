"""非 CDP 读取器共用的、对消费者中立的 Cordis 运行时树。

对齐上游 `shared/cordis/model.ts`。公开面仅中文名。
"""
from .快照 import cordis树最大深度#最大嵌套深度
from ..身份 import 检查器id#品牌化
from ..json import 是否普通对象#普通对象
from ..校验 import 精确键,精确对象,线上标识#校验

__all__=[#仅中文公开名
    'cordis运行时树模式版本','cordis运行时源标识','cordis运行时源种类',
    'cordis运行时连接','cordis运行时源','cordis运行时上下文','cordis运行时纤程',
    'cordis运行时节点','cordis运行时领域','cordis运行时树',
    '解析cordis运行时树','cordis运行时源标识化',
]#公开面结束

cordis运行时树模式版本=0#运行时树模式版本

def cordis运行时源标识(值):#运行时源标识
    """一个被检查 Cordis 运行时对消费者可见的身份。"""
    return 值#烙印

cordis运行时源种类=('host','client')#运行时源种类

def cordis运行时连接(状态,reason=None):#连接状态联合
    """保留树所代表界域的可用性。"""
    if 状态=='connected':#已连接
        return {'state':'connected'}#已连接态
    return {'state':'disconnected','reason':reason}#已断开态

class cordis运行时源:#运行时源
    """一个 Cordis 界域对消费者可见的身份。"""
    def __init__(自身,sourceId,kind,label):#构造
        """保存运行时源字段。"""
        自身.sourceId=sourceId#源标识
        自身.kind=kind#源种类
        自身.label=label#展示标签

def cordis运行时上下文(children):#Context节点
    """对消费者中立的 Cordis 树中的一个 Context。"""
    return {'kind':'context','children':tuple(children)}#Context节点

def cordis运行时纤程(uid,children):#Fiber节点
    """对消费者中立的 Cordis 树中的一个 Fiber 及其拥有的 Context。"""
    return {'kind':'fiber','uid':uid,'children':tuple(children)}#Fiber节点

cordis运行时节点=dict#运行时节点联合

class cordis运行时领域:#运行时界域
    """一个 Cordis 界域最新保留的拓扑与可用性。"""
    def __init__(自身,source,connection,revision,truncated,root):#构造
        """保存运行时界域字段。"""
        自身.source=source#源身份
        自身.connection=connection#连接状态
        自身.revision=revision#修订号
        自身.truncated=truncated#是否截断
        自身.root=root#根Context

class cordis运行时树:#运行时树
    """最新 Host 与 Client Cordis 拓扑，不含路由或 CDP 标识。"""
    def __init__(自身,schemaVersion,host,clients):#构造
        """保存运行时树字段。"""
        自身.schemaVersion=schemaVersion#模式版本
        自身.host=host#Host界域
        自身.clients=tuple(clients)#Client界域列表

def 解析连接(值):#解析连接状态
    """解析连接状态。"""
    if not 是否普通对象(值):#须为对象
        raise Exception('inspector protocol: Cordis runtime connection must be an object')#英文诊断
    if 值.get('state')=='connected':#已连接
        精确键(值,['state'],'connected Cordis runtime connection')#仅state
        return {'state':'connected'}#已连接态
    if 值.get('state')=='disconnected' and isinstance(值.get('reason'),str):#已断开
        精确键(值,['state','reason'],'disconnected Cordis runtime connection')#state与reason
        return {'state':'disconnected','reason':值['reason']}#已断开态
    raise Exception('inspector protocol: invalid Cordis runtime connection')#英文诊断

def 解析节点(值,状态,深度):#解析树节点
    """解析树节点。"""
    if 深度>cordis树最大深度:#超深
        raise Exception('inspector protocol: Cordis runtime tree exceeds the depth limit')#英文诊断
    if not 是否普通对象(值) or 值.get('kind') not in ('context','fiber'):#种类未知
        raise Exception('inspector protocol: Cordis runtime node must have a known kind')#英文诊断
    白名单=['kind','uid','children'] if 值.get('kind')=='fiber' else ['kind','children']#按种类
    记录=精确对象(值,白名单,'Cordis runtime node')#精确对象
    if not isinstance(记录.get('children'),list):#children须数组
        raise Exception('inspector protocol: Cordis runtime node children must be an array')#英文诊断
    if 记录['kind']=='context':#Context分支
        return {'kind':'context','children':[解析节点(子,状态,深度+1) for 子 in 记录['children']]}#递归
    uid=记录['uid']#Fiber唯一号
    if not isinstance(uid,int) or isinstance(uid,bool) or uid<1 or len(记录['children'])!=1:#非法
        raise Exception('inspector protocol: invalid Cordis runtime Fiber')#英文诊断
    if uid in 状态['fiberUids']:#重复uid
        raise Exception('inspector protocol: Cordis runtime tree repeats a Fiber uid')#英文诊断
    状态['fiberUids'].add(uid)#记入
    上下文=解析节点(记录['children'][0],状态,深度+1)#解析唯一子
    if 上下文.get('kind')!='context':#子须Context
        raise Exception('inspector protocol: Cordis runtime Fiber child must be a Context')#英文诊断
    return {'kind':'fiber','uid':uid,'children':[上下文]}#Fiber节点

def 解析领域(值,种类):#解析单个界域
    """解析单个界域。"""
    记录=精确对象(值,['source','connection','revision','truncated','root'],'Cordis runtime realm')#精确对象
    源=精确对象(记录['source'],['sourceId','kind','label'],'Cordis runtime source')#源对象
    标签=源.get('label')#标签
    if 源.get('kind')!=种类 or not isinstance(标签,str) or len(标签)==0 or len(标签)>256:#源形状非法
        raise Exception(f'inspector protocol: invalid {种类} Cordis runtime source')#英文诊断
    修订=记录['revision']#修订号
    if not isinstance(修订,int) or isinstance(修订,bool) or 修订<1 or not isinstance(记录['truncated'],bool):#头非法
        raise Exception('inspector protocol: invalid Cordis runtime realm header')#英文诊断
    根=解析节点(记录['root'],{'fiberUids':set()},0)#解析根节点
    if 根.get('kind')!='context':#根须为Context
        raise Exception('inspector protocol: Cordis runtime root must be a Context')#英文诊断
    return cordis运行时领域(#界域对象
        source=cordis运行时源(线上标识(源['sourceId'],'sourceId'),种类,标签),#源身份
        connection=解析连接(记录['connection']),#连接状态
        revision=修订,#修订号
        truncated=记录['truncated'],#截断标记
        root=根,#根Context
    )#返回结束

def 解析cordis运行时树(值):#解析运行时树
    """解码经检查器传输收到的、对消费者中立的树。"""
    记录=精确对象(值,['schemaVersion','host','clients'],'Cordis runtime tree')#精确对象
    if 记录['schemaVersion']!=cordis运行时树模式版本 or not isinstance(记录.get('clients'),list):#头非法
        raise Exception('inspector protocol: invalid Cordis runtime tree')#英文诊断
    宿主=None if 记录['host'] is None else 解析领域(记录['host'],'host')#解析Host
    客户端们=[解析领域(项,'client') for 项 in 记录['clients']]#解析各Client
    源标识们=set()#已见源标识
    for 领域 in (([宿主]+客户端们) if 宿主 is not None else 客户端们):#扫描全部界域
        if 领域.source.sourceId in 源标识们:#重复sourceId
            raise Exception('inspector protocol: Cordis runtime tree repeats a sourceId')#英文诊断
        源标识们.add(领域.source.sourceId)#记入
    return cordis运行时树(cordis运行时树模式版本,宿主,客户端们)#树对象

def cordis运行时源标识化(值):#投影源标识
    """把被检查源标识投影到消费者可见的 Cordis 身份命名空间。"""
    return 检查器id(值,'sourceId')#品牌化
