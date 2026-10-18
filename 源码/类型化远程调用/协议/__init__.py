import re
from ...依赖.cordis.服务 import 服务

from .异常 import 远程错误,查找策略失败,协议消息错误
from .拥有值 import 协议拥有值标记,协议拥有值,是否协议拥有值,构造协议拥有值
from .json值 import 是否远程json值,是否远程上行项
from .远程制品 import 透传模式,严格编解码,调用描述符,远程贡献,取远程错误
from .主体 import 主体于

__all__=[
    '是否合法远程段','查找策略失败',
    '绑定远程网关','远程服务','远程','远程作用域','远程方法列表',
    '透传模式','严格编解码','调用描述符','远程贡献','远程错误','取远程错误',
    '协议拥有值标记','协议拥有值','是否协议拥有值','构造协议拥有值',
    '是否远程json值','是否远程上行项',
    '主体于',
]

#常量
远程段模式=re.compile(r'^[A-Za-z0-9_$.-]+\Z',re.ASCII)
远程标记属性='_typert_remote_marker'

#工具
def 是否合法远程段(值):
    '端点段能否原样放进共享 RPC 载体。`.` 与 `..` 单独排除'
    return 值!='.' and 值!='..' and 远程段模式.match(值) is not None

def 校验段名(主语,值):
    '非法端点段则抛。主语只出现在给人看的说明里'
    if not isinstance(值,str) or not 是否合法远程段(值):
        raise TypeError(f'typert-protocol: {主语} 只能包含 RPC 端点段字符')

def 读取调用(_目标,_错误):
    '远程调用之外读 invocation 得到 None，避免未声明属性的反射错误'
    return None

def 提供调用访问器(上下文):
    '同一棵上下文树只在根上登记一次 invocation 访问器'
    根=getattr(上下文,'根',None)
    if 根 is None:
        return
    反射=getattr(根,'反射',None)
    属性表=None if 反射 is None else getattr(反射,'属性表',None)
    if not isinstance(属性表,dict) or 'invocation' in 属性表:
        return
    定义=getattr(根,'定义访问器',None)
    if not callable(定义):
        return
    定义('invocation',读取调用)

def 调用标记相同(左,右):
    '直接调用只比 kind；Context 调用还要比作用域键'
    if 左.get('kind')=='direct':
        return 右.get('kind')=='direct'
    if 右.get('kind')=='direct':
        return False
    return 左.get('context')==右.get('context')

def 记下标记到函数(方法,调用模式,导出名=None,模式=None):
    '类体执行时实例还不存在，标记先挂在函数上，读取时再按 MRO 收集'
    标记={'invocation':dict(调用模式)}
    if 导出名 is not None and 导出名!=方法.__name__:
        标记['exportName']=导出名
    if 模式 is not None:
        标记['mode']=模式
    已有=getattr(方法,远程标记属性,None)
    if 已有 is not None:
        导出相同=已有.get('exportName')==标记.get('exportName')
        模式相同=已有.get('mode')==标记.get('mode')
        if 导出相同 and 模式相同 and 调用标记相同(已有['invocation'],标记['invocation']):
            return
        raise 协议消息错误(f'typert-protocol: Remote 方法 "{方法.__name__}" 的调用标记冲突')
    setattr(方法,远程标记属性,标记)

def 直接装饰器(导出名=None,模式=None):
    '返回把直接调用标记写到方法上的装饰器'
    def 装饰器(方法):
        记下标记到函数(方法,{'kind':'direct'},导出名,模式)
        return 方法
    return 装饰器

#
def 绑定远程网关(服务实例,服务键,选项=None):
    '把可见服务字段绑到 Cordis 键与线路命名空间。命名空间缺省等于服务键，空串不算缺省'
    if 选项 is None:
        选项={}
    校验段名('服务键',服务键)
    if 'namespace' in 选项 and 选项['namespace'] is not None:
        命名空间=选项['namespace']
    else:
        命名空间=服务键
    校验段名('命名空间',命名空间)
    上下文=getattr(服务实例,'所属上下文',None)
    if 上下文 is not None:
        提供调用访问器(上下文)
    return {'service':服务实例,'serviceKey':服务键,'namespace':命名空间}

class 远程服务(服务):
    '通过网关暴露其注册名的服务基类。typertRemote 是网关按属性名读取的绑定'
    def __init__(自身,上下文,服务键,选项=None):
        '先以服务键登记，再用登记后的名称做网关绑定'
        super().__init__(上下文,服务键)
        if 选项 is None:
            选项={}
        自身.typertRemote=绑定远程网关(自身,自身.名称,选项)

def 远程(方法或导出名=None):
    '把公开实例方法标成直接远程调用。无参、字符串导出名，或恰好 mode 为 stream'
    if callable(方法或导出名):
        return 直接装饰器()(方法或导出名)
    if isinstance(方法或导出名,dict):
        if 方法或导出名.get('mode')!='stream' or len(方法或导出名)!=1:
            raise TypeError('typert-protocol: Remote 选项必须恰好包含 mode 为 "stream"')
        return 直接装饰器(None,'stream')
    if 方法或导出名 is not None:
        校验段名('Remote 导出名',方法或导出名)
    return 直接装饰器(方法或导出名)

def 远程作用域(键,导出名=None):
    '为从某一个远程作用域解析的方法创建装饰器'
    校验段名('作用域键',键)
    if 导出名 is not None:
        校验段名('Remote 导出名',导出名)
    def 装饰器(方法):
        记下标记到函数(方法,{'kind':'context','context':键},导出名)
        return 方法
    return 装饰器

def 远程方法列表(服务实例):
    '读取活实例上的远程标记。子类同名方法遮住基类，即使子类自己没有标记'
    结果=[]
    已见=set()
    for 类 in type(服务实例).__mro__:
        for 名,成员 in 类.__dict__.items():
            if 名 in 已见 or not callable(成员):
                continue
            已见.add(名)
            标记=getattr(成员,远程标记属性,None)
            if 标记 is None:
                continue
            项={'method':名,'invocation':dict(标记['invocation'])}
            if 'exportName' in 标记:
                项['exportName']=标记['exportName']
            if 'mode' in 标记:
                项['mode']=标记['mode']
            结果.append(项)
    return 结果
