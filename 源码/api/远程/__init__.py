"""远程贡献组装的宿主入口。

各归属包类型模块侧效拉入，使转发事件键面与宿主声明同源。
用显式成员断言代替形态门禁。
"""
import os,json,threading
from ...内核.作用域 import 获取载体键
from ...typert.协议 import 是否远程json值
from ...工具.双端队列 import 双端队列
from ...api.网关.网关 import 操作任务,已中止
from ...交互.命令 import 类型 as _命令类型#侧效：命令事件声明
from ...拓展.cordis服务端 import 类型 as _动态类型#侧效：动态包转发事件
from ...凭据.凭据 import 类型 as _凭据类型#侧效：凭证事件声明
from ...目标.目标 import 类型 as _目标类型#侧效：目标事件声明
from ...模型后端.llm import 类型 as _大模型类型#侧效：大模型事件声明
from ...预设.智能体预设 import 类型 as _预设类型#侧效：智能体预设事件
from ...配置.配置 import 类型 as _设置类型#侧效：设置事件声明
from ...交互.用户审批 import 类型 as _审批类型#侧效：用户审批事件声明
from ...交互.用户提问 import 类型 as _提问类型#侧效：用户提问事件声明
from .智能体查找 import (
    远程会话未找到,远程子智能体会话所有权,
    有远程子智能体所有者,远程子智能体所有权错误,
    查看远程会话,创建远程智能体解析器,
    远程查找错误码,远程查找错误,
    远程智能体结果成功,远程智能体结果失败,远程智能体结果,远程智能体选项,
)
from .远程事件 import 远程转发事件
from .类型 import (
    远程转发事件名,远程事件选择席位,可订阅远程事件名,
)
from . import 客户端 as 客户端面

包名='@deepseek-ai/dsh-api-remotes'
名称='api-remotes'
依赖=['typertGateway']

__all__=[
    '远程会话未找到','远程子智能体会话所有权',
    '有远程子智能体所有者','远程子智能体所有权错误',
    '查看远程会话','创建远程智能体解析器',
    '远程查找错误码','远程查找错误',
    '远程智能体结果成功','远程智能体结果失败','远程智能体结果','远程智能体选项',
    '远程转发事件','远程转发事件名',
    '远程事件选择席位','可订阅远程事件名',
    '包名','名称','依赖','应用','默认','客户端面',
]

def 应用(上下文):
    """登记本应用选定的 Cordis 事件源。"""
    def 登记():
        """把事件源交给网关。"""
        return 上下文.typertGateway.登记远程事件(远程事件源(上下文),{'home':os.path.expanduser('~')})
    上下文.副作用(登记,'api-remotes: forwarded Cordis event source')

def 远程事件源(上下文):
    """创建网关消费的唯一队列与监听器集。"""
    def 打开(信号):
        """挂上白名单监听并交出迭代器。"""
        队列=远程事件队列()
        拆除表=[]
        for 条目 in 远程转发事件:
            事件=条目['event']
            if 条目['mode']=='emit':
                def 发射(*位置参数,事件名=事件,目标=队列):
                    """把 emit 参数推进队列。"""
                    目标.推入({'event':事件名,'args':断言json参数(事件名,位置参数)})
                拆除表.append(上下文.监听(事件,发射))
            else:
                def 瀑布(*位置参数,事件名=事件,目标=队列):
                    """把作用域瀑布交给网关。"""
                    if len(位置参数)>=3:
                        载体,请求,下一步=位置参数[0],位置参数[1],位置参数[2]
                    elif len(位置参数)==2:
                        载体,请求,下一步=None,位置参数[0],位置参数[1]
                    else:
                        return None
                    载体智能体=获取载体键(载体)
                    if 载体智能体 is None:
                        return 下一步()
                    智能体=请求['agent'] if isinstance(请求,dict) and 'agent' in 请求 else getattr(请求,'agent',None)
                    if 智能体 is None or 智能体 is not 载体智能体:
                        raise TypeError('转发的作用域事件 '+json.dumps(事件名,ensure_ascii=False)+' 必须直接携带其智能体')
                    return 转发瀑布(目标,事件名,请求,{'value':智能体.ctx,'subject':智能体,'agentId':智能体.id},下一步)
                拆除表.append(上下文.监听(事件,瀑布))
        def 清理():
            """拆除监听。"""
            for 拆除 in 拆除表:
                拆除()
        return 队列.迭代(信号,清理)
    return 打开

class 远程事件队列:
    """把同步 Cordis 监听接到可拉取迭代。"""

    def __init__(自身):
        """构造空队列。"""
        自身.缓冲=双端队列()
        自身.等待事件=threading.Event()
        自身.已结束=False

    def 推入(自身,帧):
        """入队一帧。"""
        if 自身.已结束:
            return False
        自身.缓冲.尾推(帧)
        自身.等待事件.set()
        return True

    def 结束(自身,原因):
        """结束并拒绝挂起瀑布。"""
        if 自身.已结束:
            return
        自身.已结束=True
        while 自身.缓冲.大小>0:
            派发=自身.缓冲.头弹()
            if isinstance(派发,dict) and 'context' in 派发:
                派发['reject'](原因)
        自身.等待事件.set()

    def 迭代(自身,信号,清理):
        """拉取直至中止。"""
        try:
            while True:
                if 自身.已结束 or 已中止(信号):
                    return
                while 自身.缓冲.大小>0:
                    yield 自身.缓冲.头弹()
                if 自身.已结束 or 已中止(信号):
                    return
                自身.等待事件.clear()
                while not 自身.已结束 and not 已中止(信号) and 自身.缓冲.大小==0:
                    自身.等待事件.wait(0.05)
        finally:
            自身.结束(远程事件源结束原因(信号))
            清理()

def 远程事件源结束原因(信号):
    """源关闭原因。"""
    if 已中止(信号):
        return 信号._异常
    return Exception('api-remotes: 转发的 Remote 事件源已结束')

def 转发瀑布(队列,事件,请求,上下文,下一步):
    """把一次 Cordis 瀑布经网关挂起事件桥出。"""
    任务=操作任务()
    def 兑现(结局):
        """客户端结果或委托下一环。"""
        if 结局.get('kind')=='result':
            任务.兑现(结局.get('value'))
            return
        try:
            任务.兑现(下一步())
        except BaseException as 错误:
            任务.拒绝(错误)
    派发={
        'event':事件,'request':请求,'context':上下文,
        'resolve':兑现,'reject':任务.拒绝,
    }
    if not 队列.推入(派发):
        try:
            任务.兑现(下一步())
        except BaseException as 错误:
            任务.拒绝(错误)
    return 任务.等待()

def 断言json参数(事件,参数列表):
    """参数必须是无损 JSON。"""
    for 下标,参数 in enumerate(参数列表):
        if not 是否远程json值(参数):
            raise Exception('转发的宿主事件 "'+事件+'" 第 '+str(下标)+' 个参数不是无损 JSON 数据')
    return list(参数列表)

def _断言可转发白名单(白名单):
    """断言白名单每条均为选择席位键，且与席位键集合一致。"""
    席位键=frozenset(远程事件选择席位.__annotations__)
    if not isinstance(白名单,(tuple,list)):
        raise AssertionError('API_REMOTE_FORWARDED_EVENTS must be a sequence of event names')
    名单=[]
    for 项 in 白名单:
        if not isinstance(项,dict) or 'event' not in 项 or 'mode' not in 项:
            raise AssertionError('API_REMOTE_FORWARDED_EVENTS entries must be {event, mode}')
        if 项['mode'] not in ('emit','waterfall'):
            raise AssertionError('API_REMOTE_FORWARDED_EVENTS mode must be emit or waterfall')
        名单.append(项['event'])
    for 名 in 名单:
        if 名 not in 席位键:
            raise AssertionError('forwarded event '+repr(名)+' is not a TypertRemoteEventSelection key')
    if frozenset(名单)!=席位键:
        raise AssertionError('API_REMOTE_FORWARDED_EVENTS must match TypertRemoteEventSelection keys')

_断言可转发白名单(远程转发事件)#导入时门禁

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
