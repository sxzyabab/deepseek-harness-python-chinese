import uuid,threading#随机uuid与后台观察
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
from ...内核.智能体 import 折叠已消费工作#导入已消费工作折叠
from .助手输出 import 最终助手输出#导入最终助手输出选取
from .类型 import 子智能体运行标识#导入跑id品牌构造

def 渲染抛值(值):
    """渲染任何监听器抛出的值，不让强制转换逃出隔离。"""
    try:
        if isinstance(值,BaseException):#错误
            return 值.__class__.__name__+': '+str(值)#名与文案
        return str(值)#普通值
    except TypeError:
        return '<不可渲染的抛出值>'#不可渲染哨兵

def 创建生命周期发出(上下文对象,载体):
    """建造本缝每条边都经其发布的带隔离生命周期发射器。每个监听器独立隔离：同步抛出会被记录，而不饿死对等监听器。"""
    def 发出(名称,信息,父=None):
        """发布一条生命周期边。"""
        if 父 is None:#无作用域派发
            派发参数=[名称,信息]#无作用域
        else:#带作用域载体
            派发参数=[载体(父),名称,信息]#带作用域
        事件总线=获取内部数据(上下文对象,'属性链')['事件']#事件总线，不经壳
        for 回调 in 获取内部数据(事件总线,'解析监听器')(事件总线,'emit',派发参数):#逐监听器
            try:
                回调(信息)#同步调用监听器
            except BaseException as 错误:
                上下文对象.日志.警告('子智能体：'+名称+' 监听器抛出：'+渲染抛值(错误))#记录抛出
    return 发出#生命周期发出

def 观察运行(发出,提供方,父,跑):
    """为一次被接受的一次性跑发出 start/end 生命周期对。返回同一跑，未改动。跑为对象，result 为操作任务。"""
    身份={#共享身份
        'runId':子智能体运行标识(str(uuid.uuid4())),#铸造跑id
        'provider':提供方,#提供方名
        'id':跑.id,#子会话id
        'local':跑.localAgent is not None,#是否进程内
    }#identity结束
    结果=跑.result#结果任务
    def 成功(结果值):
        """成功决议后发 end。结果值为 dict。"""
        载荷=dict(身份)#共享身份
        载荷['stopReason']=结果值['stopReason'] if isinstance(结果值,dict) and 'stopReason' in 结果值 else None#停止原因
        输出=结果值['output'] if isinstance(结果值,dict) and 'output' in 结果值 else None#最终输出
        if 输出 is not None and len(输出)>0:#有输出才带上
            载荷['lastAssistantMessage']=输出#带上
        发出('subagent/end',载荷,父)#终态边
    def 失败():
        """基础设施拒绝后发 error 终态。"""
        载荷=dict(身份)#共享身份
        载荷['stopReason']='error'#错误终态
        发出('subagent/end',载荷,父)#终态边
    def 观察():
        """终态观察在同步 start 发射之后跑，保持 start → end。"""
        try:
            成功(结果.等待())#等待后成功
        except BaseException:
            失败()#基础设施拒绝
    if 结果 is not None:#有结果任务
        threading.Thread(target=观察,daemon=True).start()#挂观察
    发出('subagent/start',身份,父)#发布start
    return 跑#原跑

def 纪元停止原因(事件列表):
    """本子体纪元为何结束，供终态生命周期边与管理器自己的父投递使用。子体自己的日志是权威。事件为 dict。"""
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
    """为一次可续跑 Activation 的驻留纪元建造观察者。观察者看到与一次性跑相同的词汇。驻留前的创建失败不发生命周期边。"""
    身份={'runId':子智能体运行标识(str(uuid.uuid4())),'provider':提供方,'id':子标识,'local':True}#共享身份，进程内
    边界=[0]#纪元后缀起点（用列表可变）
    捕获=[{'stopReason':'completed'}]#捕获的终态
    def 终态(失败):
        """解析 settle 将发布的终态事实，但不发布它们。"""
        if 失败 is None:#成功
            return 捕获[0]#成功用捕获事实
        return {'stopReason':'error'}#失败覆盖为error
    def 开始(子):
        """纪元驻留后发布开始边。子为智能体对象。"""
        事件列表=子.session.events#整份事件
        边界[0]=len(事件列表) if 事件列表 is not None else 0#记下后缀起点
        发出('subagent/start',身份,父)#发布start
    def 快照(子):
        """在子体仍登记时快照依赖子体的终态事实。"""
        事件列表=子.session.events#整份事件
        if 事件列表 is None:#无事件
            事件列表=[]#空
        自身后缀=事件列表[边界[0]:]#本纪元后缀
        输出=最终助手输出(自身后缀)#选取最终输出
        记={'stopReason':纪元停止原因(自身后缀)}#记下终态
        if 输出 is not None:#有输出才带上
            记['output']=输出#带上
        捕获[0]=记#保存
    def 结算(失败):
        """在拆除结局已知后恰好发布一次终态边。"""
        解析=终态(失败)#解析终态
        载荷=dict(身份)#共享身份
        载荷['stopReason']=解析['stopReason'] if 'stopReason' in 解析 else None#停止原因
        if 'output' in 解析 and 解析['output'] is not None:#有输出才带上
            载荷['lastAssistantMessage']=解析['output']#带上
        发出('subagent/end',载荷,父)#终态边
    return {'start':开始,'capture':快照,'terminal':终态,'settle':结算}#观察者实现
