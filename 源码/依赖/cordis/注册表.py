"""插件登记与依赖声明。"""
from weakref import WeakKeyDictionary as 弱键字典
from ..工具 import 设置内部数据,构建外层栈#内部槽写入与外层栈
from .纤程 import 纤程,纤程运行时#纤程与同插件共用记录

def 取入口(插件):
    """按 Cordis 识别顺序取出插件入口：类、函数、对象的 apply。"""
    if isinstance(插件,type):
        return 插件#类插件
    if callable(插件):
        return 插件#函数插件
    入口=getattr(插件,'apply',None)#对象插件只读 apply
    if callable(入口):
        return 入口#对象入口
    return None#不是插件

def 声明依赖(服务名,配置=None):
    """在插件类上声明一项服务依赖的装饰器。"""
    def 装饰器(类):
        """写入 inject 槽。"""
        if not isinstance(类,type):
            raise TypeError('依赖声明只能用在插件类上')#只支持类
        if 'inject' not in 类.__dict__:
            继承=getattr(类,'inject',None)#父类上的依赖声明
            类.inject=dict(继承) if isinstance(继承,dict) else {}#本类新建一份
        类.inject[服务名]=配置#该依赖的拦截配置
        return 类#原类
    return 装饰器

def 收成依赖表(声明,结果=None):
    """把列表、映射或类继承来的 inject 收成 服务名→拦截配置。"""
    if 结果 is None:
        结果={}#新建结果表
    if 声明 is None:
        return 结果#没有声明
    if isinstance(声明,list):
        if len(声明)==0:
            return 结果#空列表
        for 服务名 in 声明:
            结果[服务名]=None#列表形态不带拦截配置
        return 结果
    if isinstance(声明,dict):
        for 服务名 in 声明:
            结果[服务名]=声明[服务名]#带拦截配置
        return 结果
    return 结果#其它形态视为没有

class 带依赖的插件:
    """把一个回调包成带 inject 与 apply 的对象插件。"""
    def __init__(自身,依赖声明,回调):
        """记下框架槽。"""
        自身.inject=依赖声明#服务依赖
        自身.apply=回调#插件入口
        自身.name=getattr(回调,'__name__',None)#显示名

class 插件注册表:
    """安装为 上下文.注册表 的插件登记表。以插件对象引用为键。"""
    def __init__(自身,上下文):
        """建立以插件对象为键的运行记录表。"""
        自身.所属上下文=上下文#所属上下文
        设置内部数据(自身,'追踪器',{'追踪属性':'所属上下文'})#调用方上下文重绑
        自身._编号计数=0#纤程编号计数器
        自身._运行记录表=弱键字典()#插件对象→运行记录

    @property
    def 下一编号(自身):
        """分配下一个纤程编号，从 1 起。"""
        自身._编号计数+=1#先自增
        return 自身._编号计数#新编号

    @property
    def 数量(自身):
        """已登记的插件运行记录数。"""
        return len(自身._运行记录表)

    def 取运行记录(自身,插件):
        """查出该插件的运行记录。"""
        return 自身._运行记录表.get(插件)

    def 已登记(自身,插件):
        """该插件是否已有运行记录。"""
        return 插件 in 自身._运行记录表

    def 有(自身,插件):
        """该插件是否已有运行记录。"""
        return 插件 in 自身._运行记录表

    def 删掉插件(自身,插件):
        """拆掉该插件的全部纤程并删除运行记录。"""
        记录=自身._运行记录表.pop(插件,None)#摘下记录
        if 记录 is None:
            return None#没有登记
        for 一条 in list(记录.纤程表):
            一条.拆除()#逐条卸载
        return 记录

    def 删除(自身,插件):
        """拆掉该插件的全部纤程并删除运行记录。"""
        return 自身.删掉插件(插件)#同一入口

    def 全部回调(自身):
        """已登记的插件对象列表。"""
        return list(自身._运行记录表)

    def 全部运行记录(自身):
        """已登记的运行记录列表。"""
        return list(自身._运行记录表.values())

    def 依赖启动(自身,依赖声明,回调):
        """等所需依赖都可用之后再启动回调。"""
        return 自身.启动插件(带依赖的插件(依赖声明,回调))#包成对象插件后启动

    def 启动插件(自身,插件,配置=None,外层栈=None):
        """在当前上下文启动插件，返回它的纤程。"""
        if 外层栈 is None:
            外层栈=构建外层栈()#捕获调用方调用栈
        入口=取入口(插件)#调用入口
        if 入口 is None:
            raise TypeError('插件必须是函数、类，或带 apply 方法的对象，收到的是 '+type(插件).__name__)
        自身.所属上下文.纤程.断言活动()#已拆除的纤程不能再挂插件
        记录=自身._运行记录表.get(插件)#已有记录
        if 记录 is None:
            名称=getattr(插件,'name',None)#框架槽 name
            if 名称 is None:
                名称=getattr(插件,'__name__',None)#函数或类名
            记录=纤程运行时(名称,入口,getattr(插件,'Config',None))#新建运行时
            记录.插件=插件#身份是插件对象
            自身._运行记录表[插件]=记录#以插件对象为键
        return 纤程(自身.所属上下文,配置,收成依赖表(getattr(插件,'inject',None)),记录,外层栈)#启动新纤程
