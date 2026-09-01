"""进程内一次性子智能体共享驱动（对齐 upstream subagent-in-process-driver）。"""
import threading,uuid#线程与子 id
from concurrent.futures import Future as _原生Future#结果 Future
from ...内核.会话 import 会话标识#品牌
from ...内核.智能体.已消费工作 import 折叠已消耗工作#foldConsumedWork
from ...模型后端.llm import 创建用户消息#用户消息
from ..子智能体.子体 import (
    追加委托策略覆盖,应用子体组合,捕获委托策略覆盖,子会话元数据,
    解析子智能体选项,解析子深度,断言子智能体最大深度,
)#子体组合
from ..子智能体.助手输出 import 最终助手输出#输出选取
from .结构化 import 附着结构化运行时,结构化输出工具名,结构化输出指令#结构化
__all__=['结构化输出工具名','结构化输出指令','启动进程内跑','默认']#公开面

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#方法
    if callable(等待):#可等待
        return 等待()#等待
    return 值#同步

def 至停止原因(原因):#TurnEndReason→SubagentStopReason
    种类=取字段(原因,'kind') if 原因 is not None else None#kind
    映射={'completed':'completed','max-tokens':'max-tokens','aborted':'aborted','blocked':'refusal'}#表
    return 映射.get(种类,'error')#默认 error

def 启动进程内跑(请求,选项=None):#startInProcessRun
    """建立并驱动一个进程内一次性子体。"""
    选项=选项 or {}#缺省
    断言子智能体最大深度(取字段(请求,'maxDepth'))#深度
    信号=取字段(请求,'signal')#取消
    if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已取消
        raise Exception('subagent request was aborted before child publication')#拒绝
    父=取字段(请求,'parent')#父智能体
    子深度=解析子深度(父,取字段(请求,'maxDepth'))#深度
    子标识=会话标识(str(uuid.uuid4()))#新 id
    种子=取字段(选项,'seed')#可选种子
    激活边界=len(种子) if 种子 is not None else 0#边界
    继承=捕获委托策略覆盖(父)#策略快照
    状态={'结构化':None,'已追加':False}#子体装配状态
    def 装配(子上下文):#setup
        追加委托策略覆盖(子上下文.agent.session,继承)#策略
        应用子体组合(子上下文,父,{'persona':取字段(请求,'persona'),'toolFilter':取字段(请求,'toolFilter')})#组合
        if 取字段(请求,'outputSchema') is not None:#结构化
            状态['结构化']=附着结构化运行时(子上下文,取字段(请求,'outputSchema'))#挂运行时
        def 步骤前(载荷,下一步):#descriptor append
            决策=解开(下一步())#下一步
            if (not 状态['已追加']) and 取字段(决策,'kind')=='enter':#首步
                状态['已追加']=True#标记
                子上下文.agent.session.append('subagent/descriptor',取字段(请求,'descriptor'))#追加
            return 决策#返回
        子上下文.on('agent/pre-step',步骤前)#监听
    句柄=解开(父.ctx.agents.create({
        'sessionId':子标识,'meta':子会话元数据(父,子深度,激活边界),
        **({} if 种子 is None else {'seed':种子}),
        'agentOptions':解析子智能体选项(父,取字段(请求,'agentOptions'),子深度),
        'signal':信号,'setup':装配,
    }))#创建
    return 驱动已发布跑(句柄,信号,取字段(请求,'prompt'),子标识,激活边界,状态['结构化'])#驱动

def 驱动已发布跑(句柄,信号,提示,子标识,边界,结构化):#drivePublishedRun
    """包装已发布子体的单回合生命周期。"""
    子=句柄.agent#子智能体
    旗标={'cancelled':False}#取消
    def 中止():#onAbort
        旗标['cancelled']=True#标记
        子.cancel({'kind':'parent'})#取消子
    if hasattr(信号,'addEventListener'):#Web 信号
        信号.addEventListener('abort',中止,{'once':True})#听一次
    elif hasattr(信号,'加入监听'):#中文信号
        信号.加入监听('abort',中止)#听一次
    if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已中止
        中止()#立刻
    未来=_原生Future()#结果
    def 工作者():#后台跑
        try:#单回合
            if not 旗标['cancelled']:#未取消
                子.followup(创建用户消息({'content':提示,'source':{'kind':'user'}}))#跟进
                解开(子.whenIdle())#等空闲
            捕获=None if 结构化 is None else 结构化['captured']()#结构化
            未来.set_result(读取结果(子,边界,旗标['cancelled'],捕获))#结算
        except BaseException as 错误:#失败
            未来.set_exception(错误)#拒绝
        finally:#拆监听
            if hasattr(信号,'removeEventListener'):信号.removeEventListener('abort',中止)#拆
    线程=threading.Thread(target=工作者,daemon=True)#线程
    线程.start()#启动
    class 结果代理:#thenable
        def wait(自身,超时=None):return 未来.result(超时)#等待
        def 等待(自身,超时=None):return 自身.wait(超时)#中文
    async def 处置():#dispose
        旗标['cancelled']=True#标记
        解开(句柄.dispose())#释放句柄
        未来.result()#等结果
    return {'id':子标识,'localAgent':子,'result':结果代理(),'dispose':处置}#跑句柄

def 读取结果(子,边界,已取消,结构化捕获):#readResult
    自有=子.session.events[边界:]#边界后事件
    账本=折叠已消耗工作(自有)#折叠
    结束=账本.get('end')#最后 turn/end
    输出=最终助手输出(自有) or []#助手输出
    记录=至停止原因(取字段(取字段(结束,'data',{}),'reason') if 结束 is not None else None)#停止
    停止='aborted' if 已取消 and 记录!='completed' else 记录#取消覆盖
    if 结构化捕获 is not None:#结构化
        if isinstance(结构化捕获,dict) and 'value' in 结构化捕获:#有值
            return {'output':输出,'structured':结构化捕获['value'],'stopReason':停止}#带结构
        if 停止=='completed':#完成却无捕获
            return {'output':输出,'stopReason':'error' if not 已取消 else 'aborted'}#降级
    return {'output':输出,'stopReason':停止}#普通

默认=启动进程内跑#中文默认
