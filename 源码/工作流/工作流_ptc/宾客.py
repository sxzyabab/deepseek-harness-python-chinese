"""在挂载的 PTC 运行时 Node 进程里执行一次工作流 VM。"""
import threading#进度与子结果线程
from .领域 import 渲染抛出#进度失败文本
from .运行时 import 工作流执行,任务#执行与未完成进度

__all__=['运行工作流宾客']#仅中文公开名

def 运行工作流宾客(宿主):#一次进度批次在飞
    """一次进度批次在飞。子拆除与终态结果前排空进度；PTC 与宿主拥有取消与清理。宿主是本运行拥有的 JSON 回调。初始化失败则抛。"""
    初始化=宿主.开始({})#引导
    排队=[]#未发进度
    在飞=[None]#进行中的进度任务
    进度错误=[None]#进度失败文本
    def 冲刷():#发出一批
        """没有在飞且有排队时发出一批。"""
        if 在飞[0] is not None or len(排队)==0:#忙或空
            return#忽略
        批次=list(排队)#本批
        排队.clear()#清空
        完成=任务()#本批任务
        在飞[0]=完成#记下
        def 发批次():#后台发
            """发给宿主再冲刷或记下失败。"""
            try:#发送
                宿主.进度(批次)#一批
                在飞[0]=None
                完成.兑现()#完成
                冲刷()#下一批
            except BaseException as 错误:#失败
                进度错误[0]=渲染抛出(错误)#记下
                排队.clear()#丢掉
                在飞[0]=None
                完成.兑现()#进度失败不拒绝宾客主路径
        工作=threading.Thread(target=发批次,daemon=True)#后台
        工作.start()#启动
    def 发送(事件):#一条进度
        """排队并尝试冲刷。"""
        if 进度错误[0] is not None:#已失败
            return#忽略
        排队.append(事件)#入队
        冲刷()#首批在同步脚本占循环前到达宿主
    def 排空():#等在飞结束
        """等到没有在飞批次。"""
        while 在飞[0] is not None:#还有
            在飞[0].等待()#等本批
    class 观察器:#进度观察
        """把执行进度变成宿主事件。"""
        def 阶段(自身,标题):#阶段
            """发 phase。"""
            发送({'type':'phase','title':标题})#阶段
        def 日志(自身,消息):#日志
            """发 log。"""
            发送({'type':'log','message':消息})#日志
        def 智能体开始(自身,信息):#开始
            """发 agent-start。"""
            发送({'type':'agent-start','info':信息})#开始
        def 智能体结束(自身,信息):#结束
            """发 agent-end。"""
            发送({'type':'agent-end','info':信息})#结束
    class 子端口:#子回调
        """经宿主绑定启动、观察与拆除子。"""
        def 启动智能体(自身,请求):#发布一个子
            """启动并包成宾客句柄。"""
            引用=宿主.启动子(请求)#发布
            调用标识=引用['callId']#回调 id
            子标识=引用['childId']#子 id
            结果任务=任务()#子结果
            def 等结果():#后台等
                """等宿主子结果。"""
                try:#等待
                    结果任务.兑现(宿主.子结果({'callId':调用标识}))#兑现
                except BaseException as 错误:#基础设施
                    结果任务.拒绝(错误)#拒绝
            threading.Thread(target=等结果,daemon=True).start()#启动
            class 句柄:#宾客句柄
                """已发布子句柄。"""
                def __init__(自身):#钉字段
                    """记下 id 与结果任务。"""
                    自身.id=子标识#子 id
                    自身.result=结果任务#结果
                def 销毁(自身):#拆除
                    """先排空进度再请宿主拆除。"""
                    排空()#进度先到
                    宿主.拆除子({'callId':调用标识})#拆除
            return 句柄()#句柄
    执行=工作流执行(初始化['meta'],初始化['body'],初始化['args'] if 'args' in 初始化 else None,初始化['limits'],观察器(),子端口())#执行
    结果=执行.驱动()#驱动
    排空()#终态前排空
    if 进度错误[0] is None:#进度成功
        return 结果#脚本结果
    return {'value':None,'stopReason':'error','error':进度错误[0],'agentsStarted':结果['agentsStarted']}#进度失败
