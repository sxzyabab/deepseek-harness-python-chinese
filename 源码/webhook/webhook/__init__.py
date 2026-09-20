import threading
from ...依赖 import cordis
服务=cordis.服务
from ...模型后端.llm import 错误链
from ...工具.值 import 快照json值,深冻结
from .标识构造 import Webhook规则标识
from .会话 import 创建Webhook会话

包名='@deepseek-ai/dsh-webhook'
名称='webhook'
依赖=['agents','agentDefaultModel','agentPresets','permissionPresets','sessionTitle','workspaceRegistry']

__all__=['包名','名称','依赖','默认','Webhook运行时','Webhook错误','Webhook已中止','Webhook规则标识']

class Webhook错误(Exception):
    """本包异常基类。"""

class Webhook已中止(Webhook错误):
    """规则拆除导致的中止。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    """已中止则抛出本包中止异常。"""
    if 已中止(信号):
        raise Webhook已中止('webhook 规则已拆除')

class 中止控制器:
    """登记生命周期用的中止控制器。信号是 threading.Event。"""
    def __init__(自身):
        """创建配套 Event。"""
        自身.信号=threading.Event()

    def 中止(自身):
        """置位信号。"""
        自身.信号.set()

def 快照投递(投递):
    """在跨规则分发前校验并分离一条投递。投递为线协议 dict。"""
    for 字段 in ('kind','source','deliveryId'):#字符串身份字段
        if 字段 not in 投递:
            raise TypeError(f'webhook 投递 {字段} 必须是非空字符串')
        值=投递[字段]
        if (not isinstance(值,str)) or 值.strip()=='':
            raise TypeError(f'webhook 投递 {字段} 必须是非空字符串')
    if 'receivedAt' not in 投递:
        raise TypeError('webhook 投递 receivedAt 必须是非负安全整数')
    收到于=投递['receivedAt']
    if isinstance(收到于,bool) or (not isinstance(收到于,int)) or 收到于<0:#bool 是 int 子类，需先排除
        raise TypeError('webhook 投递 receivedAt 必须是非负安全整数')
    快照=快照json值(投递)
    if 快照 is None:
        raise TypeError('webhook 投递必须是无损 JSON')
    return 深冻结(快照)

class Webhook运行时(服务):
    """即发即弃的规则运行时，注册为 webhookRuntime 服务。"""
    inject=依赖

    def __init__(自身,上下文):
        """安装 webhookRuntime 服务。"""
        super().__init__(上下文,'webhookRuntime')
        自身._规则={}
        自身._自身上下文=上下文
        自身._正在关闭=False
        def 生命周期拆除():
            """关闭时中止并排空全部规则。"""
            自身._正在关闭=True
            自身._等待全部规则拆除()
        上下文.副作用(生命周期拆除,'webhookRuntime.lifecycle()')

    def _等待全部规则拆除(自身):
        """同步拆除全部规则登记。"""
        for 登记 in list(自身._规则.values()):
            自身._拆除登记(登记)

    def 登记(自身,规则):
        """注册一条受信任的程序化规则。规则为 dict。"""
        if 自身._正在关闭:
            raise Webhook错误('webhook 运行时正在关闭')
        规则号=规则['id']
        if (not isinstance(规则号,str)) or 规则号.strip()=='':
            raise TypeError('webhook 规则 id 必须是非空字符串')
        种类=规则['kind']
        if (not isinstance(种类,str)) or 种类.strip()=='':
            raise TypeError(f'webhook 规则 "{规则号}" 的 kind 必须是非空字符串')
        if not callable(规则['run']):
            raise TypeError(f'webhook 规则 "{规则号}" 需要 run()')
        登记对象={'rule':规则,'controller':中止控制器(),'active':set(),'closing':False,'disposal':None}
        def 挂上():
            """写入规则表并在拆除时清掉。"""
            if 自身._正在关闭:
                raise Webhook错误('webhook 运行时正在关闭')
            if 规则号 in 自身._规则:
                raise Webhook错误(f'webhook 规则 "{规则号}" 已登记')
            自身._规则[规则号]=登记对象
            def 拆除():
                """等待登记拆除完成。"""
                自身._拆除登记(登记对象)
            return 拆除
        自身.ctx.副作用(挂上,f'webhookRuntime.register({规则号})')
        def 对外拆除():
            """拆除本条登记。"""
            自身._拆除登记(登记对象)
        return 对外拆除

    def 分发(自身,投递):
        """启动每条当前匹配规则，并在任何回调结算前返回。"""
        if 自身._正在关闭:
            raise Webhook错误('webhook 运行时正在关闭')
        快照=快照投递(投递)
        for 登记 in list(自身._规则.values()):
            if 登记['closing'] or 登记['rule']['kind']!=快照['kind']:
                continue
            自身._启动调用(登记,快照)

    def _启动调用(自身,登记,投递):
        """启动一次受控调用并挂到登记拆除。"""
        跟踪=object()
        登记['active'].add(跟踪)
        def 执行规则调用():
            """执行规则并在需要时创建会话。"""
            若已中止则抛出(登记['controller'].信号)
            请求=登记['rule']['run'](投递,登记['controller'].信号)
            若已中止则抛出(登记['controller'].信号)
            if 请求 is not None:
                return 创建Webhook会话(自身._自身上下文,投递,登记['rule']['id'],请求,登记['controller'].信号)
            return None
        try:
            执行规则调用()
        except Webhook已中止 as 错误:
            调用=f"webhook: provider={repr(投递['kind'])} source={repr(投递['source'])} delivery={repr(投递['deliveryId'])} rule={repr(登记['rule']['id'])}"
            自身._自身上下文.日志.调试(f'{调用} stopped after disposal: {错误链(错误)}')
        except Webhook错误 as 错误:
            调用=f"webhook: provider={repr(投递['kind'])} source={repr(投递['source'])} delivery={repr(投递['deliveryId'])} rule={repr(登记['rule']['id'])}"
            自身._自身上下文.日志.警告(f'{调用} failed: {错误链(错误)}')
        except TypeError as 错误:
            调用=f"webhook: provider={repr(投递['kind'])} source={repr(投递['source'])} delivery={repr(投递['deliveryId'])} rule={repr(登记['rule']['id'])}"
            自身._自身上下文.日志.警告(f'{调用} failed: {错误链(错误)}')
        finally:
            登记['active'].discard(跟踪)

    def _拆除登记(自身,登记):
        """隐藏、中止，再排空活跃调用。"""
        if 登记['disposal'] is not None:
            return 登记['disposal']
        登记['closing']=True
        自身._规则.pop(登记['rule']['id'],None)
        登记['controller'].中止()
        登记['active'].clear()
        登记['disposal']=True
        return 登记['disposal']

默认=Webhook运行时
name=名称#框架槽
inject=依赖#框架槽
default=默认#框架槽
