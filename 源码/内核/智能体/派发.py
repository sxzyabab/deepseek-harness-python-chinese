"""Agent 作用域的派发与提示词组装辅助。

对齐上游 `agent/src/dispatch.ts`。公开面仅中文名；派发器字典键为 `发出`／`串行`／`瀑布`。
"""
import threading#后台观察承诺
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#thenable 判断
from ..作用域 import 作用域目标#作用域载体构造

__all__=('智能体事件派发','智能体载体','智能体事件','发出智能体事件','为组装构建上下文')#仅中文公开名

class 智能体事件派发:#融合派发器协议；运行时为带中文键的字典
    """把 Agent 主体接到其作用域载体的派发器。键：发出／串行／瀑布。"""
    def 发出(自身,名称,载荷):#发即忘
        """在 Agent 作用域内发即忘通知。"""
        raise NotImplementedError('智能体事件派发.发出')#由智能体事件构造
    def 串行(自身,名称,载荷):#串行
        """在 Agent 作用域内按序等待派发。"""
        raise NotImplementedError('智能体事件派发.串行')#由智能体事件构造
    def 瀑布(自身,名称,载荷,*剩余):#瀑布
        """在 Agent 作用域内做环绕中间件派发。"""
        raise NotImplementedError('智能体事件派发.瀑布')#由智能体事件构造

def 智能体载体(智能体):#构建作用域载体
    """为一个 Agent 主体构建融合作用域载体。"""
    return 作用域目标(智能体,智能体)#以 Agent 自身为键

def 智能体事件(上下文对象,智能体,载体=None):#构建融合派发器
    """构建把 Agent 主体接到其作用域载体的派发器。返回键仅中文的字典。"""
    if 载体 is None:#未传入载体
        载体=智能体载体(智能体)#缺省当场建载体
    def 融合(载荷):#注入主体
        """注入主体，调用方载荷盖不过 agent。"""
        结果=dict(载荷)#展开载荷
        结果['agent']=智能体#注入主体
        return 结果#融合载荷
    def 发出(名称,载荷):#发即忘通知
        """在 Agent 作用域内发即忘通知。"""
        参数=[载体,名称,融合(载荷)]#载体、事件名、融合载荷
        回调列表=上下文对象.events.dispatch('emit',参数)#取出 emit 回调
        for 回调 in 回调列表:#逐个调用
            try:#收住同步抛错
                返回=回调(*参数)#调用监听器
                if 是否thenable(返回):#返回承诺
                    def 观察(返回值=返回,事件名=名称):#收住拒绝
                        """收住返回承诺的拒绝。"""
                        try:#收住拒绝
                            if hasattr(返回值,'等待'):#本库承诺
                                返回值.等待()#等待结算
                            else:#普通 thenable
                                返回值.then(lambda 值:None,lambda 错误:None)#thenable 结算
                        except Exception as 错误:#拒绝
                            上下文对象.logger.warn('agent event "'+事件名+'" listener rejected: '+str(错误))#记拒绝
                    线程=threading.Thread(target=观察)#后台观察
                    线程.daemon=True#不挡住退出
                    线程.start()#启动
            except Exception as 错误:#同步抛错
                上下文对象.logger.warn('agent event "'+名称+'" listener threw: '+str(错误))#记抛错
    def 串行(名称,载荷):#串行派发
        """在 Agent 作用域内按序等待派发。"""
        return 上下文对象.serial(载体,名称,融合(载荷))#经载体串行派发
    def 瀑布(名称,载荷,*剩余):#瀑布派发
        """在 Agent 作用域内做环绕中间件派发。"""
        return 上下文对象.waterfall(载体,名称,融合(载荷),*剩余)#经载体瀑布派发
    return {'发出':发出,'串行':串行,'瀑布':瀑布}#公开键仅中文

def 发出智能体事件(上下文对象,智能体,名称,载荷):#一次性发出
    """发出一条受控 Agent 通知，不分配常驻派发器。"""
    智能体事件(上下文对象,智能体)['发出'](名称,载荷)#临时派发器发即忘

def 为组装构建上下文(智能体,信号=None):#构建组装上下文
    """构建把 Agent 与作用域一起设好的提示词组装上下文。"""
    结果={'agent':智能体,'scope':智能体}#Agent 与作用域
    if 信号 is not None:#有轮次信号
        结果['signal']=信号#轮次信号
    return 结果#组装上下文
