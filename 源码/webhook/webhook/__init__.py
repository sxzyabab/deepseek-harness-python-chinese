"""Fire-and-forget webhook rule registry and Workspace-backed Session runtime. 对齐上游 `@deepseek-ai/dsh-webhook`。"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis服务基类
from ...模型后端.llm import 错误链#错误链渲染
from ...工具.值 import 快照json值,深冻结#JSON快照与冻结
from .品牌 import Webhook规则标识#规则品牌
from .会话 import 创建Webhook会话#会话创建

__all__=['Webhook运行时','默认','default','Webhook规则标识']#公开面

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        if callable(getattr(值,'wait',None)):#Future风格
            return 值.wait()#等待
        return 值.等待()#thenable
    return 值#同步值

def 已兑现(值=None):#立刻兑现的操作任务
    """把值包成立即兑现的 thenable。"""
    class _任务:#同步任务
        def wait(自身,超时=None):#阻塞等待
            return 值#原样返回
        def 等待(自身,超时=None):#中文别名
            return 值#原样返回
    return _任务()#已完成

def 快照投递(投递):#校验并分离投递
    """在跨规则分发前校验并分离一条投递。"""
    for 字段 in ('kind','source','deliveryId'):#字符串身份字段
        值=取字段(投递,字段)#字段值
        if (not isinstance(值,str)) or 值.strip()=='':#非法
            raise TypeError(f'webhook delivery {字段} must be a non-empty string')#拒绝
    收到于=取字段(投递,'receivedAt')#收到时间
    if (not isinstance(收到于,int)) or 收到于<0:#非法时间
        raise TypeError('webhook delivery receivedAt must be a non-negative safe integer')#拒绝
    快照=快照json值(投递)#无损快照
    if 快照 is None:#不能快照
        raise TypeError('webhook delivery must be lossless JSON')#拒绝
    return 深冻结(快照)#冻结快照

class Webhook运行时(服务):#fire-and-forget 规则运行时
    """Fire-and-forget 规则运行时。注册为 `ctx.webhookRuntime`。"""
    inject=['agents','agentDefaultModel','agentPresets','permissionPresets','sessionTitle','workspaceRegistry']#依赖

    def __init__(自身,上下文):#构造运行时
        """安装 webhookRuntime 服务。"""
        super().__init__(上下文,'webhookRuntime')#注册服务名
        自身._规则={}#规则注册表
        自身._自身上下文=上下文#未追踪上下文
        自身._正在关闭=False#关闭旗标
        def 生命周期拆除():#运行时生命周期
            """关闭时中止并排空全部规则。"""
            自身._正在关闭=True#拒绝新注册
            import asyncio#并发拆除
            try:#排空
                loop=asyncio.get_event_loop()#事件循环
            except RuntimeError:#无循环
                loop=asyncio.new_event_loop()#新循环
            loop.run_until_complete(自身._等待全部规则拆除())#等待拆除
        上下文.effect(生命周期拆除,'webhookRuntime.lifecycle()')#effect名

    async def _等待全部规则拆除(自身):#等待全部规则拆除
        """并行拆除全部规则登记。"""
        任务们=[]#拆除任务
        for 登记 in list(自身._规则.values()):#全部规则
            任务们.append(自身._拆除登记(登记))#排队拆除
        if len(任务们)>0:#有任务
            import asyncio#并发
            await asyncio.gather(*任务们)#等待

    def 登记(自身,规则):#注册一条规则
        """注册一条受信任的程序化规则。"""
        if 自身._正在关闭:#正在关闭
            raise Exception('webhook runtime is closing')#拒绝
        规则号=取字段(规则,'id')#规则id
        if (not isinstance(规则号,str)) or 规则号.strip()=='':#非法id
            raise TypeError('webhook rule id must be a non-empty string')#拒绝
        种类=取字段(规则,'kind')#provider kind
        if (not isinstance(种类,str)) or 种类.strip()=='':#非法kind
            raise TypeError(f'webhook rule "{规则号}" kind must be a non-empty string')#拒绝
        if not callable(取字段(规则,'run')):#缺少 run
            raise TypeError(f'webhook rule "{规则号}" requires run()')#拒绝
        登记对象={'rule':规则,'controller':_中止控制器(),'active':set(),'closing':False,'disposal':None}#登记
        def 挂上():#effect登记
            """写入规则表并在拆除时清掉。"""
            if 自身._正在关闭:#正在关闭
                raise Exception('webhook runtime is closing')#拒绝
            if 规则号 in 自身._规则:#重复
                raise Exception(f'webhook rule "{规则号}" is already registered')#拒绝
            自身._规则[规则号]=登记对象#写入
            return lambda:自身._拆除登记(登记对象)#拆除器
        释放=自身.ctx.effect(挂上,f'webhookRuntime.register({规则号})')#effect
        async def 异步拆除():#异步拆除包装
            """等待 effect 拆除完成。"""
            释放()#同步拆除
        return 异步拆除#对外 disposer

    def 分发(自身,投递):#分发投递
        """启动每条当前匹配规则，并在任何回调结算前返回。"""
        if 自身._正在关闭:#正在关闭
            raise Exception('webhook runtime is closing')#拒绝
        快照=快照投递(投递)#分离投递
        for 登记 in list(自身._规则.values()):#全部规则
            if 登记['closing'] or 取字段(取字段(登记,'rule'),'kind')!=取字段(快照,'kind'):#跳过
                continue#不匹配或正在拆
            自身._启动调用(登记,快照)#启动调用

    def _启动调用(自身,登记,投递):#启动一次调用
        """启动一次受控调用并挂到登记拆除。"""
        def 跑():#调用体
            """执行规则并在需要时创建会话。"""
            登记['controller'].throwIfAborted()#已拆除则停
            请求=解开(取字段(取字段(登记,'rule'),'run')(投递,登记['controller'].signal))#跑规则
            登记['controller'].throwIfAborted()#再检取消
            if 请求 is not None:#要创建会话
                return 解开(创建Webhook会话(自身._自身上下文,投递,取字段(取字段(登记,'rule'),'id'),请求,登记['controller'].signal))#创建
            return None#无动作
        def 完成(结果=None):#成功
            """从活跃集合摘掉。"""
            登记['active'].discard(跟踪)#摘掉
            return 结果#原样
        def 失败(错误):#失败
            """记录失败并从活跃集合摘掉。"""
            登记['active'].discard(跟踪)#摘掉
            调用=f"webhook: provider={repr(取字段(投递,'kind'))} source={repr(取字段(投递,'source'))} delivery={repr(取字段(投递,'deliveryId'))} rule={repr(取字段(取字段(登记,'rule'),'id'))}"#诊断
            if 登记['controller'].signal.aborted:#已拆除
                自身._自身上下文.logger.debug(f'{调用} stopped after disposal: {错误链(错误)}')#调试
            else:#真失败
                自身._自身上下文.logger.warn(f'{调用} failed: {错误链(错误)}')#警告
            return None#吞掉
        跟踪=已兑现()#占位跟踪
        try:#执行
            完成(跑())#同步跑
        except Exception as 错误:#失败
            失败(错误)#记录
        登记['active'].add(跟踪)#挂上跟踪

    async def _拆除登记(自身,登记):#拆除一条登记
        """隐藏、中止，再排空活跃调用。"""
        if 登记['disposal'] is not None:#已拆
            return 登记['disposal']#复用
        async def 拆():#真正拆除
            """中止并等待活跃调用。"""
            登记['closing']=True#标记关闭
            自身._规则.pop(取字段(取字段(登记,'rule'),'id'),None)#从表删除
            登记['controller'].abort(Exception(f'webhook rule "{取字段(取字段(登记,"rule"),"id")}" was disposed'))#中止
            while len(登记['active'])>0:#等活跃调用
                import asyncio#等待
                await asyncio.sleep(0)#让出
        登记['disposal']=拆()#记下承诺
        return await 登记['disposal']#等待

class _中止控制器:#简易 AbortController
    """登记生命周期用的简易中止控制器。"""
    def __init__(自身):#构造
        自身.aborted=False#未中止
        自身.signal=自身#自引用
    def abort(自身,原因=None):#中止
        """标记已中止。"""
        自身.aborted=True#已中止
        自身.reason=原因#原因
    def throwIfAborted(自身):#已中止则抛
        """已中止则抛出原因。"""
        if 自身.aborted:#已中止
            raise 自身.reason if isinstance(自身.reason,BaseException) else Exception(str(自身.reason))#抛出

默认=Webhook运行时#默认导出
default=Webhook运行时#Cordis默认导出
