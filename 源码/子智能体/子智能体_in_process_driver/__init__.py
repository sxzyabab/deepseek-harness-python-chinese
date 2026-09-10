"""进程内一次性子智能体共享驱动（对齐 upstream subagent-in-process-driver）。"""
import threading,uuid#线程与子 id
from concurrent.futures import Future as 原生结果#结果 Future
from ...内核.会话 import 会话标识#品牌
from ...内核.智能体.已消费工作 import 折叠已消费工作#foldConsumedWork
from ...模型后端.llm import 创建用户消息#用户消息
from ..子智能体.错误 import 子智能体错误#缝内失败
from ..子智能体.子体 import (
    追加委托策略覆盖,应用子体组合,捕获委托策略覆盖,子会话元数据,
    解析子智能体选项,解析子深度,断言子智能体最大深度,
)#子体组合
from ..子智能体.助手输出 import 最终助手输出#输出选取
from .结构化 import 附着结构化运行时,结构化输出工具名,结构化输出指令#结构化

__all__=['结构化输出工具名','结构化输出指令','启动进程内跑']#公开面

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():#尚未结算
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._原生结果.set_exception(子智能体错误(str(错误),'ERROR'))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

class 进程内跑:
    """持有者所有的进程内一次性跑。载荷字段 id/localAgent/result 对齐上游；拆除入口仅 销毁。"""
    def __init__(自身,标识,子,结果,拆除):
        """记下身份、子体、结果任务与拆除闭包。"""
        自身.id=标识#父作用域跑 id
        自身.localAgent=子#已发布进程内子体
        自身.result=结果#结果任务
        自身._拆除=拆除#拆除闭包

    def 销毁(自身):
        """取消剩余工作并等待句柄拆除。"""
        return 自身._拆除()#同一闭包

def 至停止原因(原因):
    """把回合结束原因 dict 映射成子智能体停止原因。"""
    if 原因 is None:#无原因
        return 'error'#默认 error
    种类=原因['kind'] if 'kind' in 原因 else None#kind
    if 种类=='completed':#完成
        return 'completed'#完成
    if 种类=='max-tokens':#上限
        return 'max-tokens'#上限
    if 种类=='aborted':#中止
        return 'aborted'#中止
    if 种类=='blocked':#拦截
        return 'refusal'#拒绝
    return 'error'#其余失败

def 启动进程内跑(请求,选项=None):
    """建立并驱动一个进程内一次性子体。请求与选项为 dict；父为智能体对象。"""
    if 选项 is None:#缺省
        选项={}#空
    断言子智能体最大深度(请求['maxDepth'] if 'maxDepth' in 请求 else None)#深度
    信号=请求['signal'] if 'signal' in 请求 else None#取消
    if 已中止(信号):#已取消
        raise 子智能体错误('subagent request was aborted before child publication','CANCELLED')#拒绝
    父=请求['parent']#父智能体
    子深度=解析子深度(父,请求['maxDepth'] if 'maxDepth' in 请求 else None)#深度
    子标识=会话标识(str(uuid.uuid4()))#新 id
    种子=选项['seed'] if 'seed' in 选项 else None#可选种子
    激活边界=len(种子) if 种子 is not None else 0#边界
    继承=捕获委托策略覆盖(父)#策略快照
    状态={'结构化':None,'已追加':False}#子体装配状态
    def 装配(子上下文,子=None):
        """子体创建窗口：策略、组合、可选结构化与描述符。子为已创建智能体；缺席时取自子上下文。"""
        智能体=子 if 子 is not None else 子上下文.agent#优先用工厂传入的子体
        追加委托策略覆盖(智能体.session,继承)#策略
        人设=请求['persona'] if 'persona' in 请求 else None#人设
        过滤=请求['toolFilter'] if 'toolFilter' in 请求 else None#过滤
        组合={}#组合
        if 人设 is not None:#有人设
            组合['persona']=人设#写入
        if 过滤 is not None:#有过滤
            组合['toolFilter']=过滤#写入
        应用子体组合(子上下文,父,组合)#组合
        if 'outputSchema' in 请求 and 请求['outputSchema'] is not None:#结构化
            状态['结构化']=附着结构化运行时(子上下文,请求['outputSchema'])#挂运行时
        def 步骤前(载荷,下一步):
            """首步进入时追加描述符。决策为 dict。"""
            决策=下一步()#下一步
            if (not 状态['已追加']) and 决策['kind']=='enter':#首步
                状态['已追加']=True#标记
                智能体.session.追加('subagent/descriptor',请求['descriptor'])#追加
            return 决策#返回
        子上下文.监听('agent/pre-step',步骤前)#监听
    创建选项={#创建选项
        'sessionId':子标识,#子会话 id
        'parentAgent':父,#委托父
        'meta':子会话元数据(父,子深度,种子 is not None),#元数据（是否 fork 种子）
        'agentOptions':解析子智能体选项(父,请求['agentOptions'] if 'agentOptions' in 请求 else None,子深度),#选项
        'signal':信号,#取消
        'setup':装配,#装配
    }#选项结束
    if 种子 is not None:#有种子
        创建选项['seed']=种子#写入
        创建选项['inheritedEventCount']=激活边界#继承计数
    句柄=父.ctx.agents.创建(创建选项)#创建
    return 驱动已发布跑(句柄,信号,请求['prompt'],子标识,激活边界,状态['结构化'])#驱动

def 驱动已发布跑(句柄,信号,提示,子标识,边界,结构化):
    """包装已发布子体的单回合生命周期。句柄为已发表句柄对象。"""
    子=句柄.智能体#子智能体
    旗标={'cancelled':False}#取消
    def 中止():
        """取消子体当前回合。"""
        旗标['cancelled']=True#标记
        子.取消({'kind':'parent'})#取消子
    if 信号 is not None:#有信号
        def 盯中止():
            """等中止通道置位后取消子体。"""
            信号._事件.wait()#阻塞到中止
            中止()#取消
        threading.Thread(target=盯中止,daemon=True).start()#听中止
        if 已中止(信号):#已中止
            中止()#立刻
    结果任务=操作任务()#结果
    def 工作者():
        """后台跑单回合。"""
        try:#单回合
            if not 旗标['cancelled']:#未取消
                子.后续(创建用户消息({'content':提示,'source':{'kind':'user'}}))#跟进
                子.等到空闲()#等空闲
            捕获=None#结构化捕获
            if 结构化 is not None:#有结构化
                捕获=结构化['captured']()#读捕获
            结果任务.兑现(读取结果(子,边界,旗标['cancelled'],捕获))#结算
        except BaseException as 错误:#失败
            结果任务.拒绝(错误)#拒绝
    线程=threading.Thread(target=工作者,daemon=True)#线程
    线程.start()#启动
    def 拆除():
        """取消并拆除已发表句柄，再等结果落定。"""
        旗标['cancelled']=True#标记
        句柄.拆除().等待()#释放句柄
        结果任务.等待()#等结果
    return 进程内跑(子标识,子,结果任务,拆除)#跑句柄

def 读取结果(子,边界,已取消,结构化捕获):
    """从子会话后缀读取一次性结果。事件为 dict。"""
    自有=子.session.events[边界:]#边界后事件
    账本=折叠已消费工作(自有)#折叠
    结束=账本['end'] if 'end' in 账本 else None#最后 turn/end
    输出=最终助手输出(自有)#助手输出
    if 输出 is None:#无输出
        输出=[]#空
    原因=None#结束原因
    if 结束 is not None and 'data' in 结束:#有结束数据
        数据=结束['data']#数据
        if isinstance(数据,dict) and 'reason' in 数据:#有原因
            原因=数据['reason']#原因
    记录=至停止原因(原因)#停止
    停止='aborted' if 已取消 and 记录!='completed' else 记录#取消覆盖
    if 结构化捕获 is not None:#结构化
        if isinstance(结构化捕获,dict) and 'value' in 结构化捕获:#有值
            return {'output':输出,'structured':结构化捕获['value'],'stopReason':停止}#带结构
        if 停止=='completed':#完成却无捕获
            return {'output':输出,'stopReason':'error' if not 已取消 else 'aborted'}#降级
    return {'output':输出,'stopReason':停止}#普通
