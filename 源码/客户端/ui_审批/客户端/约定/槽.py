'一次可作答的审批。决定、委托和取消都从这里结算'
import threading
from .....基础设施.通用工具 import 启动守护线程#信号等待
from ...异常 import 审批委托#委托标记

__all__=['待决审批']

下一审批键=0#渲染身份序号，从 1 开始用


class 待决审批:
    '会话里一条还没作答的审批。kind、key、sessionId 给会话待处理交互用'
    def __init__(自身,会话标识,请求):
        '记下会话和呈现字段。信号已经中止就立刻结束'
        global 下一审批键
        下一审批键+=1#下一次用新键
        自身.kind='approval'#域判别
        自身.key='approval:'+str(下一审批键)#渲染键
        自身.sessionId=会话标识#所属会话
        自身.工具名=请求['toolName']#请求的工具
        自身.调用=请求['callId'] if 'callId' in 请求 else None#关联的工具调用
        自身.理由=请求['reason'] if 'reason' in 请求 else None#审计理由
        自身.展示理由=请求['displayReason'] if 'displayReason' in 请求 else None#按语言展示的文案
        自身._完成=threading.Event()#结算后门闩
        自身._结果箱={'value':None,'error':None}#决定或失败
        自身._委托=object()#这一次委托的身份
        自身._已结算=False#是否已经结算
        自身._卸取消=None#结算时卸下取消监听
        自身._接上取消(请求['signal'] if 'signal' in 请求 else None)#可能立刻中止

    @property
    def 可作答(自身):
        '还没结算就可以作答'
        return not 自身._已结算

    @property
    def 结果(自身):
        '阻塞到作答、委托或中止。委托抛审批委托，其它失败原样抛出'
        自身._完成.wait()#等到结算
        错误=自身._结果箱['error']#失败或委托
        if 错误 is None:
            return 自身._结果箱['value']#用户决定
        if 错误 is 自身._委托:
            raise 审批委托(自身._委托)#交给上一层识别委托
        if isinstance(错误,BaseException):
            raise 错误#原样抛出
        raise Exception(str(错误))#非异常的拒绝原因

    def 作答(自身,结果):
        '用用户的决定结束这次瀑布'
        def 写入():
            '记下决定并放行等待'
            自身._结果箱['value']=结果#决定
            自身._完成.set()#放行
        自身.收尾(写入)#只结算一次

    def 委托(自身):
        '把还没作答的请求交给瀑布下一环'
        if 自身._已结算:
            return#已经结束
        def 写入():
            '以这次委托的身份拒绝'
            自身._拒绝(自身._委托)#委托身份
        自身.收尾(写入)#只结算一次

    def 是委托(自身,原因):
        '这个失败是不是本次委托'
        if 原因 is 自身._委托:
            return True#直接拿到身份
        return isinstance(原因,审批委托) and 原因.标记 is 自身._委托#抛出的标记

    def 中止(自身,原因):
        '传输、作用域或插件结束时，拒绝还没作答的请求'
        if 自身._已结算:
            return#已经结束
        def 写入():
            '以给定原因拒绝'
            自身._拒绝(原因)#原原因
        自身.收尾(写入)#只结算一次

    def 收尾(自身,结算):
        '只允许结算一次，并先卸下取消监听'
        if 自身._已结算:
            raise Exception('pending approval '+自身.key+' is already settled')#二次结算
        自身._已结算=True#先记上
        if 自身._卸取消 is not None:
            卸=自身._卸取消#卸下函数
            自身._卸取消=None#避免再卸
            卸()#卸下监听或等待
        结算()#写入决定或失败

    def _拒绝(自身,原因):
        '记下失败并放行等待'
        自身._结果箱['error']=原因#失败或委托
        自身._完成.set()#放行

    def _接上取消(自身,信号):
        '信号中止时结束未作答的请求。浏览器信号走 abort，网关信号等 Event'
        if 信号 is None:
            return#没有取消通道
        def 中止时(_事件=None):
            '用信号上的原因结束这次审批。没有原因就用上游那句'
            原因=None#先空着
            if hasattr(信号,'reason'):
                原因=信号.reason#AbortSignal 的原因
            if 原因 is None and hasattr(信号,'_异常'):
                原因=信号._异常#网关信号上的异常
            if 原因 is None:
                原因=Exception('approval request was aborted')#没有原因时的固定句
            自身.中止(原因)#结束
        if hasattr(信号,'addEventListener'):
            信号.addEventListener('abort',中止时,{'once':True})#只听一次
            def 卸监听():
                '结算时卸下 abort'
                信号.removeEventListener('abort',中止时)#与添加时同一监听
            自身._卸取消=卸监听#交给收尾
            if 信号.aborted:
                中止时()#构造时已经中止
            return
        事件=信号._事件#网关中止信号的 Event
        if 事件.is_set():
            中止时()#构造时已经中止
            return
        停={'值':False}#收尾后不再采用这次等待
        def 等待中止():
            '信号置位后结束审批。结算后退出'
            while not 停['值']:
                到了=事件.wait(0.01)#短等，便于结算时停掉
                if 停['值']:
                    return#已经结算
                if 到了:
                    中止时()#信号已中止
                    return
        启动守护线程(等待中止)#不挡住构造
        def 卸等待():
            '结算后让等待退出'
            停['值']=True#下一轮循环退出
        自身._卸取消=卸等待#交给收尾
