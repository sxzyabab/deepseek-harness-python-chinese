"""反射与服务解析层。"""
from cosmokit import 定义属性,是否可空,映射值#导入属性定义与空值判断
from .工具 import 符号,取可追踪,叠属性,可释放列表#导入追踪与可释放列表
from .光纤 import 光纤状态#导入生命周期状态

保留字=['prototype','then']#不能当服务名走代理解析的保留字

def 是否特殊属性(属性):
    """符号、保留字、数字下标、下划线私有名走目标自身。"""
    if not isinstance(属性,str):
        return True#非字符串
    if 属性 in 保留字:
        return True#保留字
    if 属性.startswith('_'):
        return True#私有
    if 属性.isdigit():
        return True#纯数字
    return False#普通名

def 增强错误(错误):
    """去掉代理陷阱帧。"""
    return 错误#Python 无代理帧可剥

class 反射服务:
    """安装为 ctx.reflect 的反射与服务解析层。"""
    def __init__(自身,ctx):
        """混入自身与 fiber/registry/events 的方法。"""
        自身.ctx=ctx#所属上下文
        自身._追踪器={'property':'ctx','noShadow':True}#追踪器
        自身.存储={}#标签到实现记录
        自身.属性表={}#属性名到定义
        自身.混入('reflect',['get','set','provide','accessor','mixin','取','设','提供','访问器','混入'])#反射方法
        自身.混入('fiber',['runtime','effect'])#光纤方法
        自身.混入('registry',['inject','plugin'])#注册表方法
        自身.混入('events',['on','once','parallel','emit','serial','bail','waterfall'])#事件方法

    @staticmethod
    def 取属性(目标,属性):
        """为每个上下文对象实现服务解析。"""
        字典=object.__getattribute__(目标,'__dict__')#实例字典
        if 属性 in ('__dict__','__class__'):
            return object.__getattribute__(目标,属性)#内部
        if 是否特殊属性(属性):
            if 属性 in 字典:
                return 字典[属性]#实例自有
            return object.__getattribute__(目标,属性)#类型自有
        if 属性 in 字典:
            return 取可追踪(目标,字典[属性])#读出后再做成可追踪
        错误=Exception(f'cannot get property "{属性}" without inject')#未 inject
        反射=字典.get('reflect')#反射服务
        if 反射 is None:
            raise 错误#尚未安装反射
        定义=反射.属性表.get(属性)#已声明定义
        if 定义 and 定义.get('type')=='accessor':
            接收者=字典.get(符号.接收者)#接收者
            return 定义['get'](目标,接收者,错误)#访问器读取
        光纤=字典.get('fiber')#当前光纤
        if 光纤 is None or 光纤.runtime is None:
            return 反射.取(属性,False)#根光纤宽松读取
        def 下一步():
            """沿父光纤链找实现。"""
            隔离表=字典.get(符号.隔离) or {}#隔离表
            键=隔离表.get(属性)#当前标签
            光纤对象=光纤#从当前光纤上溯
            阴影=字典.get(符号.阴影)#阴影来源
            if 阴影 is not None and hasattr(阴影,'fiber'):
                光纤对象=阴影.fiber#用来源光纤
            while True:
                快照=getattr(光纤对象,'store',None)#加载快照
                if 快照 and 属性 in 快照:
                    return 取可追踪(目标,快照[属性].get('value') if isinstance(快照[属性],dict) else 快照[属性].value)#找到实现
                if 属性 in getattr(光纤对象,'inject',{}):
                    错误.args=(f'cannot get required service "{属性}" in inactive context',)#未激活
                    raise 错误#依赖未就绪
                if not 光纤对象.runtime:
                    raise 错误#上溯到根仍没有
                父隔离=(光纤对象.parent.__dict__.get(符号.隔离) or {}) if hasattr(光纤对象.parent,'__dict__') else {}#父隔离
                if 父隔离.get(属性)!=键:
                    raise 错误#不能越界
                光纤对象=光纤对象.parent.fiber#向父光纤查找
        try:
            return 目标.events.waterfall('internal/get',目标,属性,错误,下一步)#瀑布
        except Exception as 捕获:
            if 捕获 is 错误:
                raise 增强错误(捕获)#去掉代理帧
            raise 捕获#其它错误原样抛出

    @staticmethod
    def 写属性(目标,属性,值):
        """通过上下文代理写入服务。"""
        字典=object.__getattribute__(目标,'__dict__')#实例字典
        if 是否特殊属性(属性) or 属性 in ('__dict__','__class__'):
            字典[属性]=值#直接写
            return
        错误=Exception(f'cannot set property "{属性}" without provide')#未 provide
        反射=字典.get('reflect')#反射服务
        if 反射 is None:
            字典[属性]=值#构造期直接写
            return
        定义=反射.属性表.get(属性)#已声明定义
        if not 定义:
            光纤=字典.get('fiber')#当前光纤
            if 光纤 is None or 光纤.runtime is None:
                字典[属性]=值#根光纤允许挂自有属性
                return
            raise 增强错误(错误)#插件光纤禁止未提供就写
        if 定义.get('type')=='accessor':
            写入=定义.get('set')#可选 setter
            if not 写入:
                raise AttributeError(属性)#只读
            接收者=字典.get(符号.接收者)#接收者
            写入(目标,值,接收者,错误)#调用 setter
            return
        def 下一步():
            """默认写到提供方记录。"""
            return 反射.设(属性,值,错误)#写入实现
        try:
            目标.events.waterfall('internal/set',目标,属性,值,错误,下一步)#瀑布
        except Exception as 捕获:
            if 捕获 is 错误:
                raise 增强错误(捕获)#框架诊断
            raise 捕获#其它错误

    @staticmethod
    def 有属性(目标,属性):
        """询问属性是否存在。"""
        字典=object.__getattribute__(目标,'__dict__')#实例字典
        if 是否特殊属性(属性):
            return 属性 in 字典 or hasattr(type(目标),属性)#目标自身
        if 属性 in 字典:
            return True#实例已有
        反射=字典.get('reflect')#反射服务
        if 反射 and 属性 in 反射.属性表:
            return True#已声明
        return hasattr(type(目标),属性)#类型方法

    def 取(自身,名称,严格=True):
        """从存储读取服务，不要求事先 inject。"""
        实现=自身._取实现(名称,严格)#实现记录
        if 实现 is None:
            return None#尚未提供
        值=实现['value'] if isinstance(实现,dict) else 实现.value#服务值
        return 取可追踪(自身.ctx,值)#可追踪

    def _取实现(自身,名称,严格=True):
        """按隔离标签取实现记录。"""
        隔离表=自身.ctx.__dict__.get(符号.隔离) or {}#隔离表
        键=隔离表.get(名称)#当前标签
        实现=自身.存储.get(键) if 键 else None#按标签取
        if not 实现:
            return None#尚未提供
        光纤=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
        if 严格 and 光纤.state!=光纤状态.已激活:
            return None#未激活视为没有
        return 实现#实现记录

    def 设(自身,名称,值,错误=None):
        """覆盖已提供服务的值。"""
        隔离表=自身.ctx.__dict__.get(符号.隔离) or {}#隔离表
        键=隔离表.get(名称)#当前标签
        实现=自身.存储.get(键)#按标签取
        if not 实现:
            raise Exception(f'cannot set property "{名称}" without provide')#未 provide
        光纤=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
        if 光纤 is not 自身.ctx.fiber:
            raise Exception(f'cannot set property "{名称}" in multiple fibers')#禁止跨光纤
        if isinstance(实现,dict):
            实现['value']=值#覆盖
        else:
            实现.value=值#覆盖
        return True#写入成功

    def 提供(自身,名称,值=None,检查=None):
        """登记由当前光纤持有的服务实现。"""
        def 执行体():
            """登记实现并在卸载时注销。"""
            if 名称 not in 自身.属性表:
                自身.属性表[名称]={'type':'service'}#占位为服务
            elif 自身.属性表[名称].get('type')!='service':
                raise Exception(f'property "{名称}" is already declared as {自身.属性表[名称].get("type")}')#类型冲突
            自身.属性表[名称]={'type':'service'}#确保为服务
            根隔离=自身.ctx.root.__dict__.setdefault(符号.隔离,{})#根隔离表
            if 名称 not in 根隔离:
                根隔离[名称]=object()#新建标签
            键=自身.ctx.__dict__.get(符号.隔离,{}).get(名称)#当前标签
            实现={'name':名称,'value':值,'fiber':自身.ctx.fiber,'check':检查}#组装记录
            if 自身.存储.get(键):
                已有=自身.存储[键]#已有实现
                已有光纤=已有['fiber'] if isinstance(已有,dict) else 已有.fiber#提供方
                raise Exception(f'service "{名称}" has been registered at <{已有光纤.名称}>')#重复提供
            自身.存储[键]=实现#写入存储
            if 自身.ctx.fiber.store is not None:
                自身.ctx.fiber.store[名称]=_实现记录(实现)#写入快照
            if 自身.ctx.fiber.state==光纤状态.已激活:
                自身.通知([名称])#立刻唤醒依赖方
            def 释放():
                """注销该服务。"""
                自身.存储.pop(键,None)#从存储摘掉
                光纤列表=自身.通知([名称])#通知依赖方
                for 光纤 in 光纤列表:
                    光纤.等待()#等依赖方结算
                if 自身.ctx.fiber.store is not None:
                    自身.ctx.fiber.store.pop(名称,None)#删光纤快照
            return 释放#释放器
        return 自身.ctx.fiber.effect(执行体,f'ctx.provide({名称!r})')#作为副作用

    def 通知(自身,名称列表,过滤器=None):
        """重新求值所有需要给定服务之一的光纤。"""
        if 过滤器 is None:
            def 过滤器(ctx,名称):
                """同一隔离作用域。"""
                甲=(ctx.__dict__.get(符号.隔离) or {}).get(名称)#对方标签
                乙=(自身.ctx.__dict__.get(符号.隔离) or {}).get(名称)#本方标签
                return 甲 is 乙#同一标签
        光纤列表=[]#被刷新的光纤
        for 运行时 in 自身.ctx.registry.values():
            for 光纤 in 运行时['fibers'] if isinstance(运行时,dict) else 运行时.fibers:
                有更新=False#是否命中
                for 名称 in 名称列表:
                    if 名称 not in 光纤.inject:
                        continue#不依赖
                    if not 过滤器(光纤.ctx,名称):
                        continue#作用域不匹配
                    有更新=True#需要刷新
                    光纤._核对实现(名称)#重新核对
                if not 有更新:
                    continue#不刷新
                光纤._刷新()#重算世代
                光纤列表.append(光纤)#记入返回
        for 名称 in 名称列表:
            自身.ctx.events.emit(自身.ctx,'internal/service',名称,自身._取实现(名称,False) and (自身._取实现(名称,False).get('value') if isinstance(自身._取实现(名称,False),dict) else None))#广播
        return 光纤列表#被刷新光纤

    def 访问器(自身,名称,选项):
        """用 get/set 钩子定义计算型上下文属性。"""
        def 执行体():
            """登记访问器。"""
            if 名称 in 自身.属性表:
                raise Exception(f'property "{名称}" is already declared as {自身.属性表[名称].get("type")}')#重复声明
            定义={'type':'accessor'}#访问器
            定义.update(选项)#钩子
            自身.属性表[名称]=定义#登记
            def 释放():
                """移除该访问器。"""
                自身.属性表.pop(名称,None)#删除定义
            return 释放#释放器
        return 自身.ctx.fiber.effect(执行体,f'ctx.accessor({名称!r})')#副作用

    def 混入(自身,源,混入项):
        """把服务的选定成员直接暴露到 ctx 上。"""
        def 生成():
            """逐个成员登记访问器。"""
            if isinstance(混入项,list):
                条目=[(键,键) for 键 in 混入项]#同名映射
            else:
                条目=list(混入项.items())#显式映射
            def 取源(ctx,错误):
                """按属性名从上下文取源服务。"""
                return getattr(ctx,源)#源服务
            for 键,挂名 in 条目:
                def 读取(接收者,错误,源键=键):
                    """混入 get。"""
                    服务=取源(自身.ctx if not hasattr(读取,'ctx') else 自身.ctx,错误)#源服务
                    #读取时 this 是上下文，由访问器调用传入
                    return None#占位，下面用闭包重写
                def 制作读取(源键):
                    """生成读取钩子。"""
                    def 读取钩子(ctx,接收者,错误):
                        """从源服务读成员。"""
                        服务=ctx.__dict__.get(源)#源服务
                        if 是否可空(服务):
                            return 服务#源还不存在
                        值=getattr(服务,源键,None)#读成员
                        if not callable(值) or isinstance(值,type):
                            return 值#非方法
                        def 调用(*位置参数,**关键字参数):
                            """调用期把服务 ctx 重绑到调用方。"""
                            旧=getattr(服务,'ctx',None)#原上下文
                            服务.ctx=ctx#重绑
                            try:
                                return 值(*位置参数,**关键字参数)#调用
                            finally:
                                服务.ctx=旧#恢复
                        return 调用#绑方法
                    return 读取钩子#钩子
                def 制作写入(源键):
                    """生成写入钩子。"""
                    def 写入钩子(ctx,值,接收者,错误):
                        """把赋值落到源成员。"""
                        服务=getattr(ctx,源)#源服务
                        setattr(服务,源键,值)#写入
                        return True#成功
                    return 写入钩子#钩子
                yield 自身.访问器(挂名,{'get':制作读取(键),'set':制作写入(键)})#登记
        return 自身.ctx.fiber.effect(生成,f'ctx.mixin({源!r})')#生成器副作用

    def 追踪(自身,值):
        """把本上下文的追踪包装附到值上。"""
        return 取可追踪(自身.ctx,值)#可追踪值

    def 绑定(自身,回调):
        """包装回调，使调用时把参数追踪到本上下文。"""
        def 包装(*位置参数,**关键字参数):
            """参数做成可追踪再调用。"""
            新参=[自身.追踪(项) for 项 in 位置参数]#追踪位置参
            return 回调(*新参,**关键字参数)#调用
        return 包装#代理

    get=取#英文别名
    set=设#英文别名
    provide=提供#英文别名
    accessor=访问器#英文别名
    mixin=混入#英文别名
    trace=追踪#英文别名
    bind=绑定#英文别名

class _实现记录:
    """服务实现记录的属性访问包装。"""
    def __init__(自身,数据):
        """保存字段。"""
        自身.name=数据['name']#服务名
        自身.fiber=数据['fiber']#提供方光纤
        自身.value=数据['value']#服务值
        自身.check=数据.get('check')#可用性谓词

ReflectService=反射服务#英文别名
