"""仅由私有模块状态支撑的 Remote 装饰器与显式网关绑定。

对齐上游 `@deepseek-ai/dsh-typert-protocol`。公开面仅中文名。严格反射仍是 Typert 编译器的职责；本模块提供运行时标记与可导出服务基类。
"""
import re,weakref#段名校验与原型标记弱表
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类

from .类型 import *#协议类型锚点
from .远程制品 import 透传模式,严格编解码,调用描述符,远程贡献#手写 Remote 制品辅助

__all__=[#仅中文公开名
    '是否合法远程段','查找策略失败','Typert查找失败','TypertLookupFailure',
    '绑定远程网关','远程服务','远程','远程作用域','远程方法们',
    '透传模式','严格编解码','调用描述符','远程贡献',
    'isTypertRemoteSegment','bindTypertRemote','TypertRemoteService','Remote','RemoteScope','remoteMethods',
]#公开面结束

远程段模式=re.compile(r'^[A-Za-z0-9_$.-]+$')#RPC 端点段合法字符
标记表=weakref.WeakKeyDictionary()#原型 → 方法名 → 标记

def 是否合法远程段(值):#判断是否为合法 Remote 段
    """用 Connection 端点语法测试一个生成的 Remote 名。"""
    return 值!='.' and 值!='..' and 远程段模式.match(值) is not None#排除点段并匹配字符集

class 查找策略失败(Exception):#lookup 策略拒绝错误
    """lookup 策略拒绝，其带类型的载荷属于当前边界适配器。"""
    def __init__(自身,失败载荷):#用适配器失败构造
        """包装一次适配器失败，不暴露被拒绝的身份。"""
        super().__init__('Typert lookup policy rejected the requested identity')#固定英文消息
        自身.name='TypertLookupFailure'#错误名
        自身.failure=失败载荷#适配器失败载荷

Typert查找失败=查找策略失败#中文别名（remotes 消费）
TypertLookupFailure=查找策略失败#上游名

def 校验段名(主语,值):#校验 Remote 段名
    """非法端点段则抛。"""
    if not 是否合法远程段(值):#非法
        raise TypeError('typert-protocol: '+主语+' must contain only RPC endpoint segment characters')#拒绝

def 绑定远程网关(服务实例,服务键,选项=None):#显式 Service→网关绑定
    """把一个可见 Service 字段绑定到 Cordis 键与 Remote 命名空间。"""
    if 选项 is None:#缺省选项
        选项={}#空
    校验段名('service key',服务键)#校验服务键
    命名空间=选项.get('namespace',服务键)#命名空间缺省为服务键
    校验段名('namespace',命名空间)#校验命名空间
    return {'service':服务实例,'serviceKey':服务键,'namespace':命名空间}#冻结形字典

class 远程服务(服务):#可导出的 Remote 服务基类
    """通过 Typert 网关暴露其注册名的 Cordis Service 基类。"""
    def __init__(自身,上下文,服务键,选项=None):#构造并绑定
        """注册该 Service，并把同一键绑定到 Typert 网关。"""
        super().__init__(上下文,服务键)#以服务键注册
        自身.typertRemote=绑定远程网关(自身,自身.name,选项 or {})#用注册名做网关绑定

def 记下标记(原型,方法名,调用模式,导出名=None):#把一条标记写入原型表
    """冲突则失败；相同则幂等忽略。"""
    表=标记表.get(原型)#取出该原型的方法表
    if 表 is None:#尚无表
        表={}#新建
        标记表[原型]=表#挂上
    标记={'invocation':dict(调用模式)}#要存储的标记
    if 导出名 is not None and 导出名!=方法名:#导出名与方法名不同
        标记['exportName']=导出名#记下
    当前=表.get(方法名)#已有标记
    if 当前 is not None:#同一方法被标过
        if 当前.get('exportName')==标记.get('exportName') and 当前['invocation']==标记['invocation']:#相同
            return#幂等忽略
        raise Exception('typert-protocol: Remote method "'+方法名+'" has conflicting invocation markers')#冲突
    表[方法名]=标记#写入

def 远程(方法或导出名=None):#直接 Remote 调用装饰器
    """把一个公开实例方法标为直接 Remote 调用；可带不同导出方法名。"""
    if callable(方法或导出名):#直接装饰
        方法=方法或导出名#被装饰方法
        记下标记(方法.__globals__.get(方法.__qualname__.rsplit('.',1)[0],方法),方法.__name__,{'kind':'direct'})#尽力记下——见下
        记下标记到函数(方法,{'kind':'direct'})#挂到函数自身供类装饰后收集
        return 方法#原样返回
    导出名=方法或导出名#工厂形式
    if 导出名 is not None:#有导出名
        校验段名('Remote export name',导出名)#校验
    def 装饰器(方法):#返回的方法装饰器
        """记下直接调用与可选导出名。"""
        记下标记到函数(方法,{'kind':'direct'},导出名)#挂到函数
        return 方法#原样
    return 装饰器#工厂

def 记下标记到函数(方法,调用模式,导出名=None):#把标记挂在函数属性上
    """类体执行时原型尚未就绪，先挂在函数上，由远程服务子类收集。"""
    标记={'invocation':dict(调用模式)}#标记
    if 导出名 is not None and 导出名!=方法.__name__:#不同导出名
        标记['exportName']=导出名#记下
    已有=getattr(方法,'_typert_remote_marker',None)#已有
    if 已有 is not None and 已有!=标记:#冲突
        raise Exception('typert-protocol: Remote method "'+方法.__name__+'" has conflicting invocation markers')#冲突
    方法._typert_remote_marker=标记#挂上

def 远程作用域(键,导出名=None):#作用域 Remote 装饰器工厂
    """为从某一个 Remote Scope 解析的方法创建装饰器。"""
    校验段名('Scope key',键)#校验作用域键
    if 导出名 is not None:#有导出名
        校验段名('Remote export name',导出名)#校验
    def 装饰器(方法):#方法装饰器
        """记下 Context 调用与可选导出名。"""
        记下标记到函数(方法,{'kind':'context','context':键},导出名)#挂上
        return 方法#原样
    return 装饰器#工厂

def 远程方法们(服务实例):#读取实例上的 Remote 标记
    """读取装饰器附着在活 Service 上的 Remote 标记。"""
    结果=[]#标记列表
    for 类 in type(服务实例).__mro__:#沿 MRO
        for 名,成员 in list(类.__dict__.items()):#类自有成员
            if not callable(成员):#非可调用
                continue#跳过
            标记=getattr(成员,'_typert_remote_marker',None)#函数上的标记
            if 标记 is None:#无标记
                continue#跳过
            项={'method':名,'invocation':dict(标记['invocation'])}#展开
            if 'exportName' in 标记:#有导出名
                项['exportName']=标记['exportName']#带上
            结果.append(项)#收入
    return 结果#按声明顺序近似

# 上游英文名对照
isTypertRemoteSegment=是否合法远程段#上游名
bindTypertRemote=绑定远程网关#上游名
TypertRemoteService=远程服务#上游名
Remote=远程#上游名
RemoteScope=远程作用域#上游名
remoteMethods=远程方法们#上游名
