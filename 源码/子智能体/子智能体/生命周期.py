import uuid#随机uuid
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
from ...内核.智能体 import 折叠已消费工作#导入已消费工作折叠
from .类型 import 子智能体运行标识#导入跑id品牌构造

def 渲染抛值(值):
    '渲染任何监听器抛出的值，不让强制转换逃出隔离'
    try:
        if isinstance(值,BaseException):#错误
            return 值.__class__.__name__+': '+str(值)#名与文案
        return str(值)#普通值
    except TypeError:
        return '<不可渲染的抛出值>'#不可渲染哨兵

def 创建生命周期发出(上下文,载体):
    '建造本缝每条边都经其发布的带隔离生命周期发射器。每个监听器独立隔离：同步抛出会被记录，而不饿死对等监听器'
    def 发出(名称,信息,父=None):
        '发布一条生命周期边'
        if 父 is None:#无作用域派发
            派发参数=[名称,信息]#无作用域
        else:#带作用域载体
            派发参数=[载体(父),名称,信息]#带作用域
        事件总线=获取内部数据(上下文,'属性链')['事件']#事件总线，不经壳
        for 回调 in 获取内部数据(事件总线,'解析监听器')(事件总线,'emit',派发参数):#逐监听器
            try:
                返回=回调(信息)#同步调用监听器
                if hasattr(返回,'然后'):#返回了期约
                    返回.捕获(lambda 错误,名称=名称: 上下文.日志.警告('subagent: '+名称+' listener rejected: '+渲染抛值(错误)))#拒绝只记警告
            except BaseException as 错误:
                上下文.日志.警告('subagent: '+名称+' listener threw: '+渲染抛值(错误))#记录抛出
    return 发出#生命周期发出

def 纪元停止原因(事件列表):
    '本子体纪元为何结束，供终态生命周期边与管理器自己的父投递使用。子体自己的日志是权威。事件为 dict'
    折叠=折叠已消费工作(事件列表)#折叠已消费工作
    结束=折叠['end'] if isinstance(折叠,dict) and 'end' in 折叠 else None#记账回合结束
    丢弃未跑=折叠['droppedUnrun'] if isinstance(折叠,dict) and 'droppedUnrun' in 折叠 else None#已接受但未跑的取消
    种类=None#回合结束种类
    if isinstance(结束,dict) and 'data' in 结束 and isinstance(结束['data'],dict):#有结束事件
        原因=结束['data']['reason'] if 'reason' in 结束['data'] else None#结束原因
        种类=原因['kind'] if isinstance(原因,dict) and 'kind' in 原因 else None#结束种类
    if 种类=='max-tokens':#token上限
        return 'max-tokens'#映射max-tokens
    if 种类=='aborted' or 种类=='interrupted':#已中止或打断
        return 'aborted'#映射aborted
    if 种类=='error':#错误
        return 'error'#映射error
    if 种类=='blocked':#被拦截
        return 'refusal'#映射refusal
    if 种类 is None or 种类=='completed':#没有记账回合或干净完成
        return 'aborted' if 丢弃未跑 else 'completed'#有未跑取消则aborted
    return 'error'#不当成成功

def 创建激活观察者(发出,提供方,子标识,父):
    '为一次本地或外部激活的驻留纪元建造观察者。驻留前的创建失败不发生命周期边'
    身份={'runId':子智能体运行标识(str(uuid.uuid4())),'provider':提供方,'id':子标识,'local':False}#开始时还不知道是不是本地
    def 开始(子=None):
        '纪元驻留后发布开始边。本地子是智能体，外部执行为空'
        身份['local']=子 is not None#只有拿到智能体才是本地
        发出('subagent/start',身份,父)#发布 start
    def 结算(结果):
        '拆除结局已知后恰好发布一次终态边。结果为子智能体结果'
        载荷=dict(身份)#共享身份
        载荷['stopReason']=结果['stopReason']#停止原因
        输出=结果['output'] if 'output' in 结果 and 结果['output'] is not None else []#输出
        if len(输出)>0:#有输出才带上
            载荷['lastAssistantMessage']=输出#带上
        发出('subagent/end',载荷,父)#终态边
    return {'start':开始,'settle':结算}#观察者
