"""插件光纤生命周期、副作用与配置校验辅助。"""
import types
from cosmokit import 定义属性,是否可空#导入属性定义与空值判断
from .工具 import (
    符号,#共享符号
    拼接错误,#错误栈拼接
    可释放列表,#可释放列表
    取可追踪,#可追踪包装
    是否构造器,#构造器判断
    是否对象,#对象判断
    构建外层栈,#外层栈
    承诺,#可等待结果
    是否thenable,#thenable 判断
)
from .上下文 import 上下文#导入上下文

校验错误品牌=object()#校验错误品牌
未激活标记='__INACTIVE__'#未激活世代标记
副作用惯性={}#释放器到进行中清理

class 校验错误(TypeError):
    """插件配置未通过标准 schema 校验时抛出的错误。"""
    def __init__(自身,问题列表):
        """用 schema 问题列表拼出聚合消息。"""
        行=[]#问题行
        for 问题 in 问题列表:
            消息=问题.get('message') if isinstance(问题,dict) else str(问题)#消息
            路径=问题.get('path') if isinstance(问题,dict) else None#路径
            if 路径:
                行.append(f'  - {消息} (at {".".join(str(项) for 项 in 路径)})')#带路径
            else:
                行.append(f'  - {消息}')#只输出消息
        super().__init__('invalid config:\n'+'\n'.join(行))#聚合消息
        自身.name='ValidationError'#错误名
        自身.校验错误品牌=True#品牌

def 解析配置(运行时,配置):
    """插件运行时启动前校验并规范化配置。"""
    if not 运行时 or not 运行时.get('Config') if isinstance(运行时,dict) else not getattr(运行时,'Config',None):
        return 配置#没有 schema
    模式=运行时['Config'] if isinstance(运行时,dict) else 运行时.Config#schema
    标准=模式.get('~standard') if isinstance(模式,dict) else getattr(模式,'标准协议',None)#标准协议
    if 标准 is None and hasattr(模式,'标准协议'):
        标准=模式.标准协议#属性
    if not 标准:
        return 配置#没有标准协议
    结果=标准['validate'](配置) if isinstance(标准,dict) else 标准['validate'](配置)#校验
    if 是否thenable(结果) or (isinstance(结果,dict) and 'then' in 结果):
        raise TypeError('Async config validation is not supported')#异步校验未实现
    if isinstance(结果,dict) and 结果.get('issues'):
        raise 校验错误(结果['issues'])#聚合成校验错误
    if isinstance(结果,dict):
        return 结果.get('value')#规范化后的值
    return 结果#通过

def 运行释放器(释放器):
    """先跑释放器本身，若有进行中的清理则加入。"""
    结果=释放器()#先跑释放器
    进行中=副作用惯性.get(释放器)#进行中的清理
    if 进行中:
        return 进行中()#加入
    return 结果#本次结果

def 发出插件拆除(上下文对象,光纤对象):
    """通知插件已拆除，且不允许单个观察者打断拥有者清理。"""
    参数=['internal/plugin',光纤对象]#派发参数
    try:
        回调列表=上下文对象.events.dispatch('emit',参数)#解析监听器
    except Exception as 错误:
        上下文对象.logger.error(错误)#记下错误
        return#不继续
    for 回调 in 回调列表:
        try:
            返回=回调(*参数)#同步调用
            if 是否thenable(返回):
                try:
                    返回.等待()#等待异步
                except Exception as 错误:
                    上下文对象.logger.error(错误)#异步拒绝记日志
        except Exception as 错误:
            上下文对象.logger.error(错误)#记下后继续

class 光纤状态:
    """一条插件光纤的生命周期状态。"""
    等待=0#等待依赖
    加载中=1#正在加载
    已激活=2#已激活
    失败=3#启动失败
    已释放=4#已释放
    卸载中=5#正在卸载

FiberState=光纤状态#英文别名
光纤状态.PENDING=光纤状态.等待#英文别名
光纤状态.LOADING=光纤状态.加载中#英文别名
光纤状态.ACTIVE=光纤状态.已激活#英文别名
光纤状态.FAILED=光纤状态.失败#英文别名
光纤状态.DISPOSED=光纤状态.已释放#英文别名
光纤状态.UNLOADING=光纤状态.卸载中#英文别名

class Cordis错误(Exception):
    """带稳定机器可读错误码的框架错误。"""
    码表={'INACTIVE_EFFECT':'cannot create effect on inactive context'}#错误码表

    def __init__(自身,码,消息=None):
        """未传消息则用错误码对应文本。"""
        super().__init__(消息 if 消息 is not None else 自身.码表.get(码,码))#消息
        自身.code=码#错误码

CordisError=Cordis错误#英文别名

class 光纤:
    """一次插件应用的运行时实例。"""
    def __init__(自身,parent,配置,inject,runtime,获取外层栈):
        """创建光纤。插件作者通常从 ctx.plugin() 取得光纤。"""
        自身.parent=parent#父上下文
        自身.inject=inject#依赖表
        自身.runtime=runtime#插件运行时
        自身._配置=配置#原始配置
        自身.config=None#当前生效配置
        自身.state=光纤状态.等待#默认等待依赖
        自身.store=None#加载快照
        自身.inertia=None#进行中的世代切换
        自身._钩子={}#光纤本地钩子表
        自身._释放器=可释放列表()#已登记副作用
        自身._错误=None#启动失败原因
        自身._工作快照={}#依赖实现的工作快照
        自身.uid=None#光纤编号
        自身.ctx=None#插件上下文
        自身.context=None#派发框架事件的上下文
        自身._钩子=自身._钩子#本地钩子
        自身._disposables=自身._释放器#英文别名
        自身._hooks=自身._钩子#英文别名

        def 收集(释放器):
            """把释放器登记到光纤副作用表。"""
            自身._释放器.压入(释放器)#登记

        if runtime:
            自身.uid=parent.registry.counter#分配编号
            自身.ctx=自身.context=parent.extend({'fiber':自身})#扩展出本光纤上下文
            注入项=list(inject.items()) if inject else []#展开依赖
            if 注入项:
                父拦截=parent.__dict__.get(上下文.拦截) or {}#父拦截表
                子拦截=dict(父拦截)#子表
                自身.ctx.__dict__[上下文.拦截]=子拦截#写入
                for 名称,配置项 in 注入项:
                    if 是否可空(配置项):
                        continue#无拦截配置
                    子拦截[名称]=配置项#写入拦截
            def 执行():
                """跑插件回调。"""
                回调=runtime['callback'] if isinstance(runtime,dict) else runtime.callback#入口
                if 是否构造器(回调):
                    实例=回调(自身.ctx,自身.config)#构造插件实例
                    钩子列表=getattr(实例,'_初始化钩子',None) or []#方法级钩子
                    if hasattr(实例,'__dict__'):
                        钩子列表=实例.__dict__.get(符号.初始化钩子,钩子列表)#符号钩子
                    for 钩子 in 钩子列表:
                        钩子()#依赖就绪后再调
                    初始化=getattr(实例,'_初始化',None)#初始化方法
                    if hasattr(实例,'__dict__'):
                        初始化=实例.__dict__.get(符号.初始化,初始化)#符号初始化
                    if 初始化:
                        return 初始化()#跑初始化
                    return None#无初始化
                return 回调(自身.ctx,自身.config)#函数插件
            自身._运行器={
                'epoch':未激活标记,#尚未激活
                'getOuterStack':获取外层栈,#外层栈
                'execute':执行,#执行体
                'collect':收集,#收集释放器
            }
            def 拆除体():
                """父光纤上的 ctx.plugin() 副作用。"""
                运行时光纤=runtime['fibers'] if isinstance(runtime,dict) else runtime.fibers#光纤表
                摘掉=运行时光纤.压入(自身)#登记自己
                def 释放():
                    """卸载插件并结算。"""
                    自身.uid=None#标记已释放
                    发出插件拆除(自身.context,自身)#通知观察者
                    回调=runtime['callback'] if isinstance(runtime,dict) else runtime.callback#身份键
                    if 自身.ctx.registry.has(回调):
                        摘掉()#从光纤表摘掉
                        剩余=list(运行时光纤)#存活光纤
                        if not 剩余:
                            自身.ctx.registry.delete(回调)#删除运行时
                    自身._设世代(未激活标记)#切到未激活
                    if not 自身.inertia:
                        def 回调状态():
                            """启动卸载。"""
                            自身.inertia=自身._卸载()#启动卸载
                            return 光纤状态.卸载中#进入卸载态
                        自身._更新状态(回调状态)#更新状态
                    while 自身.inertia:
                        if hasattr(自身.inertia,'等待'):
                            自身.inertia.等待()#等到当前过渡结束
                        else:
                            break#非承诺
                return 释放#拆除释放器
            自身.dispose=parent.fiber.effect(拆除体,'ctx.plugin()')#作为父光纤副作用
            try:
                自身.context.emit('internal/plugin',自身)#发布光纤创建
            except Exception as 错误:
                try:
                    自身.dispose()#异步拆除
                except Exception as 原因:
                    自身.ctx.logger.error(原因)#失败记日志
                raise 错误#继续抛出
            if 自身.uid is not None and parent.fiber.state!=光纤状态.卸载中:
                for 名称 in list(inject.keys()):
                    自身._核对实现(名称)#核对实现
                自身._刷新()#按依赖快照决定是否加载
        else:
            自身.uid=0#根编号
            自身.ctx=自身.context=parent#根上下文
            自身.state=光纤状态.已激活#一开始就是激活
            自身.store={}#空快照
            自身._运行器={
                'epoch':'',#根光纤没有未激活世代
                'getOuterStack':获取外层栈,#外层栈
                'execute':lambda:None,#没有插件回调
                'collect':收集,#收集根上副作用
            }
            自身.dispose=自身.重启#根光纤的拆除实际是重启

        自身._runner=自身._运行器#英文别名

    @property
    def 名称(自身):
        """插件显示名，继承最近的具名祖先，否则为 root。"""
        当前=自身#从自身上溯
        while True:
            运行时=当前.runtime#运行时
            名=None#显示名
            if 运行时 is not None:
                名=运行时.get('name') if isinstance(运行时,dict) else getattr(运行时,'name',None)#名称
            if 名:
                return 名#具名运行时
            父光纤=当前.parent.fiber#父光纤
            if 当前 is 父光纤:
                break#根光纤
            当前=父光纤#继续上溯
        return 'root'#没有显示名

    name=名称#英文别名走 property 不行，下面用 getter
    #名称已是 property，name 需要同行为

    def 断言活动(自身):
        """光纤已经释放则抛错。"""
        if 自身.uid is not None:
            return#仍有编号
        raise Cordis错误('INACTIVE_EFFECT')#禁止再挂副作用

    def _执行(自身,运行器):
        """执行副作用体并收集释放器。"""
        旧世代=运行器['epoch']#开始时的世代
        def 体(栈信息):
            """安全收集并按形态处理副作用。"""
            def 安全收集(释放器):
                """合法释放器才收集。"""
                if callable(释放器) and not isinstance(释放器,type):
                    运行器['collect'](释放器)#收集
                elif not 是否可空(释放器):
                    raise TypeError('Invalid effect')#形态非法
            副作用=运行器['execute']()#执行体
            if callable(副作用) and not isinstance(副作用,type) and not isinstance(副作用,types.GeneratorType):
                return 运行器['collect'](副作用)#直接返回释放器
            if 是否可空(副作用):
                return#没有返回值
            if not 是否对象(副作用):
                raise TypeError('Invalid effect')#形态非法
            if 是否thenable(副作用):
                return 副作用.then(安全收集)#兑现后再收集
            if isinstance(副作用,types.GeneratorType):
                栈信息.错误=Exception()#刷新内层栈锚点
                try:
                    while True:
                        项=next(副作用)#取下一个
                        安全收集(项)#登记
                except StopIteration as 结束:
                    安全收集(结束.value)#完成值
                return#迭代结束
            raise TypeError('Invalid effect')#其它对象非法
        return 拼接错误(体,运行器['getOuterStack'])#拼外层栈

    def effect(自身,执行体,标签='anonymous'):
        """在本光纤上登记带清理的副作用。"""
        自身.断言活动()#已释放则拒绝
        if 自身.state==光纤状态.卸载中:
            raise Cordis错误('INACTIVE_EFFECT')#卸载中不能再挂
        释放器列表=[]#本副作用收集到的释放器
        正在拆除=False#是否已经开始拆除
        拆除任务=None#拆除任务

        def 拆除():
            """按逆序运行已收集释放器。"""
            nonlocal 正在拆除,拆除任务#修改外层
            if 正在拆除:
                return 拆除任务#第二次调用
            正在拆除=True#标记已开始
            任务=None#链式等待
            取出=list(释放器列表)#拷贝
            释放器列表.clear()#清空
            取出.reverse()#逆序
            for 释放器 in 取出:
                结果=运行释放器(释放器)#立刻跑
                if 是否thenable(结果):
                    结果.等待()#等待异步
            拆除任务=任务#记下
            return 拆除任务#返回

        元={'label':标签,'children':[]}#诊断节点
        运行器={
            'execute':执行体,#副作用体
            'epoch':True,#仍有效
            'collect':None,#下面赋值
            'getOuterStack':构建外层栈(),#登记点调用栈
        }

        def 收集(释放器):
            """收到本层释放器。"""
            释放器列表.append(释放器)#本层
            自身._释放器.删除(释放器)#从光纤总表摘掉
            子=None#子树
            if hasattr(释放器,'__dict__'):
                子=释放器.__dict__.get(符号.副作用)#诊断树
            if 子:
                元['children'].append(子)#挂到本节点
        运行器['collect']=收集#写入收集器

        执行中=True#是否仍在同步执行阶段
        启动失败=False#同步启动是否失败
        进行中=None#进行中的拆除
        摘掉包装=lambda:False#从光纤总表摘掉包装器
        任务=None#执行体返回的任务

        def 收尾(回调):
            """执行拆除回调并摘掉包装器。"""
            nonlocal 进行中#修改外层
            try:
                结果=回调()#执行拆除
            except Exception:
                摘掉包装()#仍要摘掉
                raise#继续抛出
            if 是否thenable(结果):
                try:
                    结果.等待()#等待
                finally:
                    摘掉包装()#结算后摘掉
                return 结果#异步结果
            摘掉包装()#同步立刻摘掉
            return 结果#同步结果

        def 包装():
            """拆除该副作用。"""
            nonlocal 进行中#修改外层
            if not 运行器['epoch']:
                return 进行中 if 启动失败 else None#已失效
            运行器['epoch']=False#一次性
            def 回调():
                """等启动完成再拆。"""
                if 执行中:
                    if 是否thenable(任务):
                        任务.等待()#等启动
                    return 拆除()#再拆
                if 任务:
                    if 是否thenable(任务):
                        任务.等待()#等执行任务
                    return 拆除()#再拆
                return 拆除()#立刻拆
            return 收尾(回调)#收尾

        定义属性(包装,符号.副作用,元)#挂上诊断树
        副作用惯性[包装]=lambda:进行中#允许外层加入
        摘掉包装=自身._释放器.压入(包装)#先登记包装器
        try:
            任务=自身._执行(运行器)#立刻执行
        except Exception as 原因:
            执行中=False#离开同步执行
            启动失败=True#标记失败
            运行器['epoch']=False#失效
            try:
                进行中=收尾(拆除)#拆除已收集项
            except Exception as 错误:
                自身.ctx.logger.error(错误)#回滚失败记日志
            raise 原因#抛给调用方
        执行中=False#同步执行结束
        if 是否thenable(任务):
            try:
                任务.等待()#等待异步执行
            except Exception:
                if not 运行器['epoch']:
                    拆除()#已经失效则只跑拆除
                else:
                    收尾(拆除)#完整收尾
        自身._包装then(包装,任务,运行器,收尾,拆除)#可 await
        return 包装#释放器

    def _包装then(自身,包装,任务,运行器,收尾,拆除):
        """给释放器挂上 then，执行结束后交出拆除函数。"""
        def then(兑现=None,拒绝=None):
            """执行结束后交出拆除函数。"""
            try:
                if 是否thenable(任务):
                    任务.等待()#等执行
                def 异步拆除():
                    """失效后走完整收尾。"""
                    if not 运行器['epoch']:
                        return#已失效
                    运行器['epoch']=False#标记失效
                    return 收尾(拆除)#完整收尾
                结果=异步拆除#拆除函数
                if 兑现:
                    return 兑现(结果)#转发
                return 结果#拆除函数
            except Exception as 错误:
                if 拒绝:
                    return 拒绝(错误)#转发失败
                raise#继续抛
        包装.then=then#挂 then

    def 取副作用(自身):
        """返回当前已登记副作用的元数据。"""
        结果=[]#诊断树列表
        for 释放器 in 自身._释放器:
            元=None#诊断树
            if hasattr(释放器,'__dict__'):
                元=释放器.__dict__.get(符号.副作用)#取出
            if 元:
                结果.append(元)#带标签的项
        return 结果#树列表

    def _取状态(自身):
        """按字段推导生命周期状态。"""
        if 自身.uid is None:
            return 光纤状态.已释放#编号已清空
        if 自身._错误:
            return 光纤状态.失败#有启动错误
        if 自身._运行器['epoch']!=未激活标记:
            return 光纤状态.已激活#已激活
        return 光纤状态.等待#等待依赖

    def _更新状态(自身,回调):
        """回调可指定新状态，变化则广播。"""
        旧=自身.state#旧状态
        指定=回调()#回调
        自身.state=指定 if 指定 is not None else 自身._取状态()#新状态
        if 旧==自身.state:
            return#没有变化
        自身.context.emit('internal/status',自身,旧)#广播变迁
        if 旧!=光纤状态.已激活 and 自身.state!=光纤状态.已激活:
            return#服务可见性不变
        存储=自身.ctx.reflect.存储#全部服务实现
        for 键 in list(存储.keys()):
            实现=存储[键]#实现记录
            光纤对象=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
            if 光纤对象 is not 自身:
                continue#不是本光纤
            名称=实现['name'] if isinstance(实现,dict) else 实现.name#服务名
            自身.ctx.reflect.通知([名称])#唤醒依赖方

    def _核对实现(自身,服务名):
        """核对实现是否可用并写入工作快照。"""
        实现=自身.ctx.reflect._取实现(服务名,True)#严格取激活实现
        if not 实现:
            自身._工作快照.pop(服务名,None)#从快照删掉
            return
        值=实现['value'] if isinstance(实现,dict) else 实现.value#服务值
        检查=实现.get('check') if isinstance(实现,dict) else 实现.check#谓词
        if 检查:
            try:
                if not 检查():
                    自身._工作快照.pop(服务名,None)#视为未提供
                    return
            except Exception as 错误:
                光纤对象=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
                光纤对象.ctx.logger.error(错误)#记日志
                自身._工作快照.pop(服务名,None)#视为未提供
                return
        自身._工作快照[服务名]=实现#写入工作快照

    def _刷新(自身):
        """按依赖快照决定是否加载。"""
        世代=''#从空世代开始
        for 名称 in list(自身.inject.keys()):
            实现=自身._工作快照.get(名称)#工作快照
            if not 实现:
                世代=未激活标记#不能激活
                break#不用再看
            光纤对象=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
            世代+=':'+str(光纤对象.uid)#用提供方编号组成世代
        自身._设世代(世代)#按新世代切换

    def _设世代(自身,世代):
        """按新世代决定加载或卸载。"""
        旧=自身._运行器['epoch']#当前世代
        if 世代==旧:
            return#没变化
        自身._运行器['epoch']=世代#先写入
        if 自身.inertia:
            return#已有过渡在跑
        def 回调():
            """选择加载或卸载。"""
            if 世代!=未激活标记 and 旧==未激活标记:
                自身.inertia=自身._加载()#启动加载
                return 光纤状态.加载中#进入加载态
            自身.inertia=自身._卸载()#启动卸载
            return 光纤状态.卸载中#进入卸载态
        自身._更新状态(回调)#更新状态

    def _解析配置(自身,配置):
        """允许拦截并改写配置，再走 schema 校验。"""
        配置=自身.context.waterfall(自身,'internal/config',配置,lambda:配置)#瀑布
        return 解析配置(自身.runtime,配置) if 自身.runtime else 配置#有运行时则校验

    def _加载(自身):
        """跑插件回调并收集副作用。"""
        任务=承诺()#本轮过渡
        自身.store=dict(自身._工作快照)#冻成加载快照
        旧世代=自身._运行器['epoch']#本轮世代
        try:
            if 自身._运行器['epoch']==旧世代:
                自身.config=自身._解析配置(自身._配置)#解析配置
                自身._执行(自身._运行器)#跑插件回调
                自身._错误=None#成功则清掉旧错误
        except Exception as 原因:
            自身.ctx.logger.error(原因)#记下启动错误
            自身._错误=原因#保存
            自身._运行器['epoch']=未激活标记#回到未激活
        def 回调():
            """加载后决定是否接着卸载。"""
            if 自身._运行器['epoch']==旧世代:
                自身.inertia=None#过渡结束
                return None#用推导状态
            自身.inertia=自身._卸载()#接着卸载
            return 光纤状态.卸载中#进入卸载态
        自身._更新状态(回调)#更新状态
        任务.兑现()#完成本轮
        return 任务#惯性

    def _卸载(自身):
        """运行全部释放器并清掉加载快照。"""
        任务=承诺()#本轮过渡
        for 释放器 in 自身._释放器.清空():
            try:
                def 体(栈信息):
                    """运行释放器并等待。"""
                    栈信息.错误=Exception()#刷新锚点
                    运行释放器(释放器)#运行
                拼接错误(体,自身._运行器['getOuterStack'])#拼外层栈
            except Exception as 原因:
                自身.ctx.logger.error(原因)#记下后继续
        自身.store=None#清掉快照
        def 回调():
            """卸载后决定是否接着加载。"""
            if 自身._运行器['epoch']==未激活标记:
                自身.inertia=None#过渡结束
                return None#用推导状态
            自身.inertia=自身._加载()#接着加载
            return 光纤状态.加载中#进入加载态
        自身._更新状态(回调)#更新状态
        任务.兑现()#完成本轮
        return 任务#惯性

    def 等待(自身):
        """等待当前生命周期工作，并重新抛出启动错误。"""
        while 自身.inertia:
            if hasattr(自身.inertia,'等待'):
                自身.inertia.等待()#等到当前过渡结束
            else:
                break#非承诺
        if 自身._错误:
            raise 自身._错误#抛给调用方
        return 自身#返回光纤本身

    def 重启(自身):
        """拆除并立刻用当前配置重新加载本插件。"""
        自身.断言活动()#已释放则拒绝
        自身._设世代(未激活标记)#先卸载
        自身._刷新()#再按依赖决定是否重新加载
        自身.等待()#等到过渡结束

    def update(自身,配置,不保存=False):
        """校验并应用新配置，然后重启插件。"""
        自身.断言活动()#已释放则拒绝
        自身._配置=配置#先记下原始配置
        if 自身.state!=光纤状态.已激活:
            自身._错误=None#清掉旧错误
            自身._设世代(未激活标记)#重置世代
            自身._刷新()#依赖齐了就会加载
            return#未激活时不跑 update 瀑布
        配置=自身._解析配置(配置)#先校验
        def 内建(*位置参数):
            """写入生效配置并重启。"""
            自身.config=配置#生效配置
            自身._错误=None#清掉旧错误
            return 自身.重启()#卸载再加载
        return 自身.context.waterfall(自身,'internal/update',配置,不保存,内建)#更新瀑布

    assertActive=断言活动#英文别名
    getEffects=取副作用#英文别名
    await_=等待#英文别名
    restart=重启#英文别名
    _checkImpl=_核对实现#英文别名
    _refresh=_刷新#英文别名

    @property
    def name(自身):
        """插件显示名。"""
        return 自身.名称#委托

Fiber=光纤#英文别名
ValidationError=校验错误#英文别名
resolveConfig=解析配置#英文别名
