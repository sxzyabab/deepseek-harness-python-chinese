"""事件总线、派发模式与事件增广类型。"""
from .工具 import 符号,可释放列表,聚合错误,是否thenable,绑到,设符号#导入符号与聚合错误
from .上下文 import 上下文#导入上下文

def 是否中断(值):
    """判断事件结果是否应终止 bail 风格派发。"""
    return 值 is not None and 值 is not False#这三类值不算中断

class 事件服务:
    """安装为 ctx.events 并混入每个上下文的事件总线。"""
    def __init__(自身,ctx):
        """构造时挂上内部的 internal/listener 与 internal/update 钩子。"""
        自身.ctx=ctx#所属上下文
        自身._追踪器={'property':'ctx','noShadow':True}#追踪器
        设符号(自身,符号.追踪器,自身._追踪器)#符号追踪器
        自身._钩子={}#事件名到监听记录
        自身._hooks=自身._钩子#英文别名

        def 监听分流(上下文对象,事件名,监听器,选项):
            """非全局的 update 监听改挂到光纤本地。"""
            if 事件名=='internal/update' and not 选项.get('global'):
                表=上下文对象.fiber._钩子.get('internal/update')#光纤级表
                if 表 is None:
                    表=可释放列表()#新建
                    上下文对象.fiber._钩子['internal/update']=表#写入
                if 选项.get('prepend'):
                    return 表.前插(监听器)#前置
                return 表.压入(监听器)#追加
            return None#走默认登记
        自身.on('internal/listener',监听分流)

        def 本地更新(光纤对象,配置,不保存,下一步):
            """先跑光纤本地 update 钩子。"""
            回调们=list(光纤对象._钩子.get('internal/update') or [])#拷贝
            def 续体():
                """先跑本地钩子，没有了再进内建 next。"""
                if 回调们:
                    回调=回调们.pop(0)#下一个本地钩子
                    return 回调(光纤对象,配置,不保存,续体)#以光纤为 this 继续
                return 下一步()#内建续体
            return 续体()#启动本地钩子链
        自身.on('internal/update',本地更新,{'global':True,'prepend':True})#全局前置

    def dispatch(自身,模式,参数列表):
        """解析一次派发要用的监听器，并应用上下文过滤。"""
        thisArg=None#派发 this
        if 参数列表 and (是否派发this(参数列表[0])):
            thisArg=参数列表.pop(0)#首参是对象或函数则当作 this
        名称=参数列表.pop(0)#事件名
        if isinstance(名称,str) and not 名称.startswith('internal/'):
            自身.emit('internal/dispatch',模式,名称,参数列表,thisArg)#诊断事件
        过滤=None#过滤器
        if thisArg is not None:
            过滤=thisArg.__dict__.get(上下文.过滤) if hasattr(thisArg,'__dict__') else None#过滤器
            if 过滤 is None:
                过滤=getattr(thisArg,'_过滤',None)#服务过滤方法
        结果=[]#绑定后的回调
        for 钩子 in 自身._钩子.get(名称) or []:
            通过=钩子.get('global')#全局钩子
            if not 通过 and 过滤:
                未绑定=getattr(过滤,'__func__',过滤)#揭开绑定
                通过=未绑定(thisArg,钩子['ctx'])#filter.call(thisArg, ctx)
            elif not 通过:
                通过=True#无过滤则保留
            if 通过:
                结果.append(绑到(钩子['callback'],thisArg))#绑到派发 this
        return 结果#回调列表

    def parallel(自身,*位置参数):
        """并发运行监听器并等待全部完成。"""
        参数=list(位置参数)#可变
        回调列表=自身.dispatch('emit',参数)#解析
        错误列表=[]#失败
        锁=threading.Lock()#收集锁
        线程列表=[]#工作线程
        def 运行(回调):
            """在线程里跑一个监听器。"""
            try:
                返回=回调(*参数)#调用
                if 是否thenable(返回):
                    返回.等待()#等待
            except Exception as 错误:
                锁.acquire()#加锁
                错误列表.append(错误)#收集
                锁.release()#解锁
        for 回调 in 回调列表:
            线程=threading.Thread(target=运行,args=(回调,))#工作线程
            线程列表.append(线程)#登记
            线程.start()#启动
        for 线程 in 线程列表:
            线程.join()#等待
        if 错误列表:
            raise 聚合错误(错误列表)#聚合成 AggregateError

    def emit(自身,*位置参数):
        """同步运行监听器，不等待它们返回的 Promise。"""
        参数=list(位置参数)#可变
        for 回调 in 自身.dispatch('emit',参数):
            回调(*参数)#逐个同步调用

    def serial(自身,*位置参数):
        """按序运行监听器并等待每一个，直到有人返回 bail 值。"""
        参数=list(位置参数)#可变
        for 回调 in 自身.dispatch('serial',参数):
            结果=回调(*参数)#调用
            if 是否thenable(结果):
                结果=结果.等待()#等待
            if 是否中断(结果):
                return 结果#立刻返回

    def bail(自身,*位置参数):
        """同步按序运行监听器，直到有人返回 bail 值。"""
        参数=list(位置参数)#可变
        for 回调 in 自身.dispatch('bail',参数):
            结果=回调(*参数)#不等待
            if 是否中断(结果):
                return 结果#立刻返回

    def waterfall(自身,*位置参数):
        """把监听器组合到最终 next 回调周围。"""
        参数=list(位置参数)#可变
        回调们=自身.dispatch('waterfall',参数)#外层到内层
        内层=参数.pop()#最内层续体
        def 下一步(*位置参数):
            """还有监听器就取下一个，否则进内建行为。"""
            if 回调们:
                回调=回调们.pop(0)#下一个
                return 回调(*参数)#当前监听器最后一参是 next
            return 内层(*参数)#内建忽略多余参数
        参数.append(下一步)#把续体放回
        return 下一步()#从最外层开始

    def register(自身,标签,钩子表,回调,选项):
        """把一条监听记录作为副作用存到当前光纤。"""
        def 执行体():
            """写入监听记录。"""
            记录={'ctx':自身.ctx,'callback':回调}#记录
            记录.update(选项)#选项
            if 选项.get('prepend'):
                钩子表.insert(0,记录)#前置
            else:
                钩子表.append(记录)#追加
            def 释放():
                """光纤卸载时按回调引用删除。"""
                return 自身.unregister(钩子表,回调)#删除
            return 释放#释放器
        return 自身.ctx.fiber.effect(执行体,标签)#登记副作用

    def unregister(自身,钩子表,回调):
        """删除一条已存储的监听记录。"""
        下标=0#扫描
        while 下标<len(钩子表):
            if 钩子表[下标].get('callback') is 回调:
                钩子表.pop(下标)#删掉
                return True#确实移除
            下标+=1#前进
        return False#未找到

    def on(自身,事件名,监听器,选项=None):
        """注册由当前光纤持有的事件监听器。"""
        if not isinstance(选项,dict):
            选项={'prepend':选项}#布尔值解释为 prepend
        自身.ctx.fiber.断言活动()#已释放禁止登记
        监听器=自身.ctx.reflect.绑定(监听器)#追踪到当前上下文
        结果=自身.bail(自身.ctx,'internal/listener',事件名,监听器,选项)#允许核心拦截
        if 结果:
            return 结果#用 bail 值替代默认登记
        钩子表=自身._钩子.get(事件名)#全局钩子表
        if 钩子表 is None:
            钩子表=[]#新建
            自身._钩子[事件名]=钩子表#写入
        if isinstance(事件名,str):
            标签='ctx.on('+json.dumps(事件名)+')'#诊断标签
        else:
            标签='ctx.on('+str(事件名)+')'#符号名
        return 自身.register(标签,钩子表,监听器,选项)#作为光纤副作用

    def once(自身,事件名,监听器,选项=None):
        """登记第一次调用后自行注销的事件监听器。"""
        释放器盒=[]#保存释放器
        def 一次性(*位置参数):
            """先卸掉自身再跑原始监听器。"""
            if 释放器盒:
                释放器盒[0]()#先卸掉
            return 监听器(*位置参数)#跑原始
        释放器=自身.on(事件名,一次性,选项)#登记
        释放器盒.append(释放器)#保存
        return 释放器#可提前取消

def 是否派发this(值):
    """首参是对象或函数则当作派发 this。"""
    if 值 is None:
        return True#typeof null === object
    if isinstance(值,(str,bytes,int,float,bool)):
        return False#原始值当事件名或参数
    return True#对象或函数

isBailed=是否中断#英文别名
EventsService=事件服务#英文别名
