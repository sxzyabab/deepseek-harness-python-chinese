"""Fire-and-forget webhook 规则注册表与 Workspace 支撑的 Session 运行时。

对齐上游 `@deepseek-ai/dsh-webhook`。公开面仅中文名。
"""
import threading#中止信号
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis服务基类
from ...模型后端.llm import 错误链#错误链渲染
from ...工具.值 import 快照json值,深冻结#JSON快照与冻结
from .标识构造 import Webhook规则标识#规则标识
from .会话 import 创建Webhook会话#会话创建

__all__=['Webhook运行时','Webhook错误','Webhook已中止','Webhook规则标识']#仅中文公开名

class Webhook错误(Exception):
    """本包异常基类。"""

class Webhook已中止(Webhook错误):
    """规则拆除导致的中止。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出本包中止异常。"""
    if 已中止(信号):#已中止
        raise Webhook已中止('webhook rule was disposed')#抛出

class 中止控制器:
    """登记生命周期用的中止控制器。信号是 threading.Event。"""
    def __init__(自身):
        """创建配套 Event。"""
        自身.信号=threading.Event()#中止旗标

    def 中止(自身):
        """置位信号。"""
        自身.信号.set()#置位

def 快照投递(投递):
    """在跨规则分发前校验并分离一条投递。投递为线协议 dict。"""
    for 字段 in ('kind','source','deliveryId'):#字符串身份字段
        if 字段 not in 投递:#键不存在
            raise TypeError(f'webhook delivery {字段} must be a non-empty string')#拒绝
        值=投递[字段]#字段值
        if (not isinstance(值,str)) or 值.strip()=='':#非法
            raise TypeError(f'webhook delivery {字段} must be a non-empty string')#拒绝
    if 'receivedAt' not in 投递:#键不存在
        raise TypeError('webhook delivery receivedAt must be a non-negative safe integer')#拒绝
    收到于=投递['receivedAt']#收到时间
    if isinstance(收到于,bool) or (not isinstance(收到于,int)) or 收到于<0:#非法时间
        raise TypeError('webhook delivery receivedAt must be a non-negative safe integer')#拒绝
    快照=快照json值(投递)#无损快照
    if 快照 is None:#不能快照
        raise TypeError('webhook delivery must be lossless JSON')#拒绝
    return 深冻结(快照)#冻结快照

class Webhook运行时(服务):
    """Fire-and-forget 规则运行时。注册为 `ctx.webhookRuntime`。"""
    inject=['agents','agentDefaultModel','agentPresets','permissionPresets','sessionTitle','workspaceRegistry']#依赖

    def __init__(自身,上下文):
        """安装 webhookRuntime 服务。"""
        super().__init__(上下文,'webhookRuntime')#注册服务名
        自身._规则={}#规则注册表
        自身._自身上下文=上下文#未追踪上下文
        自身._正在关闭=False#关闭旗标
        def 生命周期拆除():
            """关闭时中止并排空全部规则。"""
            自身._正在关闭=True#拒绝新注册
            自身._等待全部规则拆除()#同步拆除
        上下文.副作用(生命周期拆除,'webhookRuntime.lifecycle()')#副作用名

    def _等待全部规则拆除(自身):
        """同步拆除全部规则登记。"""
        for 登记 in list(自身._规则.values()):#全部规则
            自身._拆除登记(登记)#排队拆除

    def 登记(自身,规则):
        """注册一条受信任的程序化规则。规则为 dict。"""
        if 自身._正在关闭:#正在关闭
            raise Webhook错误('webhook runtime is closing')#拒绝
        规则号=规则['id']#规则id
        if (not isinstance(规则号,str)) or 规则号.strip()=='':#非法id
            raise TypeError('webhook rule id must be a non-empty string')#拒绝
        种类=规则['kind']#provider kind
        if (not isinstance(种类,str)) or 种类.strip()=='':#非法kind
            raise TypeError(f'webhook rule "{规则号}" kind must be a non-empty string')#拒绝
        if not callable(规则['run']):#缺少 run
            raise TypeError(f'webhook rule "{规则号}" requires run()')#拒绝
        登记对象={'rule':规则,'controller':中止控制器(),'active':set(),'closing':False,'disposal':None}#登记
        def 挂上():
            """写入规则表并在拆除时清掉。"""
            if 自身._正在关闭:#正在关闭
                raise Webhook错误('webhook runtime is closing')#拒绝
            if 规则号 in 自身._规则:#重复
                raise Webhook错误(f'webhook rule "{规则号}" is already registered')#拒绝
            自身._规则[规则号]=登记对象#写入
            def 拆除():
                """等待登记拆除完成。"""
                自身._拆除登记(登记对象)#拆除
            return 拆除#拆除器
        自身.ctx.副作用(挂上,f'webhookRuntime.register({规则号})')#副作用
        def 对外拆除():
            """拆除本条登记。"""
            自身._拆除登记(登记对象)#拆除
        return 对外拆除#对外 disposer

    def 分发(自身,投递):
        """启动每条当前匹配规则，并在任何回调结算前返回。"""
        if 自身._正在关闭:#正在关闭
            raise Webhook错误('webhook runtime is closing')#拒绝
        快照=快照投递(投递)#分离投递
        for 登记 in list(自身._规则.values()):#全部规则
            if 登记['closing'] or 登记['rule']['kind']!=快照['kind']:#跳过
                continue#不匹配或正在拆
            自身._启动调用(登记,快照)#启动调用

    def _启动调用(自身,登记,投递):
        """启动一次受控调用并挂到登记拆除。"""
        跟踪=object()#占位跟踪
        登记['active'].add(跟踪)#挂上跟踪
        def 跑():
            """执行规则并在需要时创建会话。"""
            若已中止则抛出(登记['controller'].信号)#已拆除则停
            请求=登记['rule']['run'](投递,登记['controller'].信号)#跑规则
            若已中止则抛出(登记['controller'].信号)#再检取消
            if 请求 is not None:#要创建会话
                return 创建Webhook会话(自身._自身上下文,投递,登记['rule']['id'],请求,登记['controller'].信号)#创建
            return None#无动作
        try:#执行
            跑()#同步跑
        except Webhook已中止 as 错误:#已拆除
            调用=f"webhook: provider={repr(投递['kind'])} source={repr(投递['source'])} delivery={repr(投递['deliveryId'])} rule={repr(登记['rule']['id'])}"#诊断
            自身._自身上下文.日志.调试(f'{调用} stopped after disposal: {错误链(错误)}')#调试
        except Webhook错误 as 错误:#本包失败
            调用=f"webhook: provider={repr(投递['kind'])} source={repr(投递['source'])} delivery={repr(投递['deliveryId'])} rule={repr(登记['rule']['id'])}"#诊断
            自身._自身上下文.日志.警告(f'{调用} failed: {错误链(错误)}')#警告
        except TypeError as 错误:#校验失败
            调用=f"webhook: provider={repr(投递['kind'])} source={repr(投递['source'])} delivery={repr(投递['deliveryId'])} rule={repr(登记['rule']['id'])}"#诊断
            自身._自身上下文.日志.警告(f'{调用} failed: {错误链(错误)}')#警告
        finally:#无论成败
            登记['active'].discard(跟踪)#摘掉

    def _拆除登记(自身,登记):
        """隐藏、中止，再排空活跃调用。"""
        if 登记['disposal'] is not None:#已拆
            return 登记['disposal']#复用
        登记['closing']=True#标记关闭
        自身._规则.pop(登记['rule']['id'],None)#从表删除
        登记['controller'].中止()#中止
        登记['active'].clear()#同步路径直接清空
        登记['disposal']=True#记下
        return 登记['disposal']#返回

default=Webhook运行时#框架槽
