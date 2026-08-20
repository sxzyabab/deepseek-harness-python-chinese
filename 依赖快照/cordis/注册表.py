"""插件注册表、依赖注入与插件入口类型。"""
from cosmokit import 定义属性#导入不可枚举属性定义
from .工具 import 符号,可释放列表,构建外层栈#导入符号与可释放列表
from .光纤 import 光纤#导入光纤

def 是否可应用(对象):
    """对象插件必须带 apply 方法。"""
    return 对象 and not isinstance(对象,(str,bytes,int,float,bool)) and callable(getattr(对象,'apply',None))#带 apply

def 注入(服务名,配置=None):
    """在类或类方法上声明服务依赖的装饰器。"""
    def 装饰器(值):
        """类装饰器：写入静态 inject。"""
        if isinstance(值,type):
            if 'inject' not in 值.__dict__:
                父=getattr(值,'inject',None)#父类 inject
                值.inject={}#新建表
                if 父:
                    值.inject.update(父 if isinstance(父,dict) else {})#继承
                值.inject[符号.检查原型]=True#沿原型链合并
            值.inject[服务名]=配置#写入拦截配置
            return 值#类
        raise Exception('@Inject() can only be used on class or class methods')#只允许类或方法
    return 装饰器#工厂

def 解析注入(注入声明,结果=None):
    """把数组/对象/类继承的 inject 元数据收成普通映射。"""
    if 结果 is None:
        结果={}#空表
    if not 注入声明:
        return 结果#空声明
    if isinstance(注入声明,list):
        for 名称 in 注入声明:
            结果[名称]=None#无拦截配置
        return 结果#数组展开
    if isinstance(注入声明,dict) and 注入声明.get(符号.检查原型):
        解析注入({键:注入声明[键] for 键 in 注入声明 if 键 is not 符号.检查原型},结果)#本层
        return 结果#已填
    if isinstance(注入声明,dict):
        for 名称 in 注入声明:
            if 名称 is 符号.检查原型:
                continue#跳过标记
            结果[名称]=注入声明[名称] if 注入声明[名称] is not None else None#undefined 收成 null
        return 结果#对象展开
    return 结果#其它

注入.解析=staticmethod(解析注入)#挂到注入上
Inject=注入#英文别名
Inject.resolve=解析注入#英文别名

class 注册表服务:
    """安装为 ctx.registry 并混入每个上下文的插件注册表。"""
    def __init__(自身,ctx):
        """保存上下文与内部映射。"""
        自身.ctx=ctx#所属上下文
        自身._追踪器={'property':'ctx','noShadow':True}#追踪器
        自身._计数=0#光纤 uid 计数器
        自身._内部={}#回调到运行时记录

    @property
    def counter(自身):
        """分配下一个光纤 uid（每次读取都自增）。"""
        自身._计数+=1#先加再返回
        return 自身._计数#从 1 起

    @property
    def size(自身):
        """已登记的插件运行时数量。"""
        return len(自身._内部)#条目数

    def resolve(自身,插件):
        """把支持的插件形态解析成可执行回调。"""
        try:
            if callable(插件) and isinstance(插件,type):
                return 插件#类本身就是回调
            if callable(插件) and not isinstance(插件,type):
                return 插件#函数插件
            if 是否可应用(插件):
                return 插件.apply#对象插件取 apply
        except Exception:
            return None#吞掉 apply 访问器抛出的错误，当作无效插件
        return None#无效

    def get(自身,插件):
        """查找某插件的运行时记录。"""
        键=自身.resolve(插件)#身份回调
        return 自身._内部.get(键) if 键 else None#查表

    def has(自身,插件):
        """检查某插件是否已有登记的运行时。"""
        键=自身.resolve(插件)#身份回调
        return bool(键) and 键 in 自身._内部#表中有记录

    def delete(自身,插件):
        """释放某插件的全部运行光纤并删除其运行时记录。"""
        键=自身.resolve(插件)#身份回调
        运行时=自身._内部.get(键) if 键 else None#查出运行时
        if not 运行时:
            return#没有记录
        自身._内部.pop(键,None)#先从表中摘掉
        光纤表=运行时['fibers'] if isinstance(运行时,dict) else 运行时.fibers#光纤列表
        for 光纤对象 in list(光纤表):
            光纤对象.dispose()#触发卸载
        return 运行时#摘下的记录

    def keys(自身):
        """迭代已登记的插件回调。"""
        return 自身._内部.keys()#回调

    def values(自身):
        """迭代已登记的插件运行时。"""
        return 自身._内部.values()#运行时

    def entries(自身):
        """迭代 [回调, 运行时] 对。"""
        return 自身._内部.items()#键值对

    def forEach(自身,回调):
        """访问每一个已登记运行时。"""
        for 键,值 in 自身._内部.items():
            回调(值,键)#转发给回调

    def inject(自身,注入声明,回调):
        """所需依赖可用后启动回调。"""
        return 自身.plugin({'inject':注入声明,'apply':回调,'name':getattr(回调,'__name__',None)})#包成对象插件

    def plugin(自身,插件,配置=None,获取外层栈=None):
        """在当前上下文启动插件并返回其光纤。"""
        if 获取外层栈 is None:
            获取外层栈=构建外层栈()#捕获调用方栈
        回调=自身.resolve(插件)#解析可执行入口
        if not 回调:
            raise Exception('invalid plugin, expect function or object with an "apply" method, received '+type(插件).__name__)#无效形态
        自身.ctx.fiber.断言活动()#已释放禁止再挂插件
        运行时=自身._内部.get(回调)#已有运行时
        if not 运行时:
            名称=getattr(插件,'name',None) or getattr(插件,'__name__',None)#显示名
            if 名称=='apply':
                名称=None#apply 不能当显示名
            配置模式=getattr(插件,'Config',None)#schema
            运行时={'name':名称,'callback':回调,'fibers':可释放列表(),'Config':配置模式}#建立记录
            自身._内部[回调]=运行时#以回调为键登记
        注入声明=getattr(插件,'inject',None)#依赖声明
        光纤对象=光纤(自身.ctx,配置,解析注入(注入声明),运行时,获取外层栈)#启动新光纤
        def then(兑现=None,拒绝=None):
            """await 光纤即等待加载结算。"""
            try:
                结果=光纤对象.等待()#等待
                if 兑现:
                    return 兑现(结果)#转发成功
                return 结果#光纤
            except Exception as 错误:
                if 拒绝:
                    return 拒绝(错误)#转发失败
                raise#继续抛
        光纤对象.then=then#可 then
        return 光纤对象#可等待的光纤

RegistryService=注册表服务#英文别名
Plugin=object#插件形态占位
