import json,threading
from queue import Queue as 队列#单次落定门
from ...模型后端.llm import 断言永不,创建工具结果消息
from ..工具 import 工具体前中止,调度器符号
from .中止与并发 import 已中止,赛跑取值,全部排空队列,放入成功,循环错误

def 解析参数(原始):
    """解析模型参数：保留非法 JSON 为文本，空输入映射成空对象。"""
    if 原始 is None or 原始=='':
        return {}#空则空对象
    try:
        return json.loads(原始)#解析 JSON
    except (json.JSONDecodeError,TypeError,ValueError):
        return 原始#原样文本

def 追加工具调用(会话,轮次,步骤,块):
    """追加一次已启动调用，并返回其结果必须引用的事件序号。"""
    事件=会话.追加('tool/call',{
        'turn':轮次,#轮次
        'step':步骤,#步骤
        'callId':块['id'],#调用 id
        'name':块['name'],#工具名
        'arguments':块['arguments'],#参数
    })#追加事件
    return 事件['seq']#返回序号

def 追加工具结果(会话,轮次,步骤,块,结果,调用序号):
    """追加按模型顺序、链接到其调用事件的结果。"""
    消息=创建工具结果消息({
        'callId':块['id'],#调用 id
        'content':结果['content'],#内容
        'isError':结果['isError'],#是否错误
    })#结果消息
    载荷={
        'turn':轮次,#轮次
        'step':步骤,#步骤
        'message':消息,#结果消息
    }#结果载荷
    错误=结果['error'] if 'error' in 结果 else None#错误细节
    信息=错误['info'] if 错误 is not None and 'info' in 错误 else None#结构化信息
    if 信息 is not None:
        载荷['error']=信息#有错误详情则带上
    元=结果['meta'] if 'meta' in 结果 else None#呈现元数据
    if 元 is not None:
        载荷['meta']=元#有元数据则带上
    会话.追加('tool/result',载荷,{'surfaceOp':'append','sourceEventSeqs':[调用序号]})#追加到表面并引用调用

def 追加跳过的工具调用(会话,轮次,步骤,块):
    """为取消后跳过的模型调用追加可持久化的调用/结果对。"""
    调用序号=追加工具调用(会话,轮次,步骤,块)#先记下调用
    追加工具结果(会话,轮次,步骤,块,{
        'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],#模型可见错误文本
        'isError':True,#错误结局
        'error':{
            'message':'tool call aborted before dispatch',#错误消息
            'info':{'name':'AbortError','code':工具体前中止},#中止码
        },#错误详情
    },调用序号)#引用调用序号

def 执行一组(上下文,轮次,步骤,组,模式,信号,接受上下文):
    """跑一道独占屏障或并行池。"""
    会话=上下文.agents.要求发起方().session#取出会话
    上限=上下文.agentLoop.配置.最大并行工具调用#并行上限
    槽表=[None]*len(组)#按模型顺序的槽
    调用序号表=[-1]*len(组)#调用序号
    下一启动=0#下一启动下标
    已提交=0#已提交下标
    已启动=0#已启动数
    已中=已中止(信号)#是否已中止
    已结束=False#是否结束轮次
    调度失败=None#调度失败
    失败锁=threading.Lock()#首次失败锁
    def 抛调度失败():
        """有调度失败则抛。"""
        if 调度失败 is not None:
            raise 调度失败['error']#有失败则抛
    def 提交已就绪():
        """提交已就绪的连续槽。"""
        nonlocal 已提交,已结束#修改外层
        while 已提交<len(组):
            槽=槽表[已提交]#当前槽
            if 槽 is None:
                break#尚未落定
            调用=组[已提交]#对应调用
            调度器=上下文.tools[调度器符号]#分阶段调度器
            if 槽['needsPost']:
                结果=调度器['finalize'](槽['exec'],槽['result'])#后处理
            else:
                结果=调度器['finish'](槽['exec'],槽['result'])#直接收尾
            追加工具结果(会话,轮次,步骤,调用['block'],结果,调用序号表[已提交])#记下结果
            额外=结果['additionalContexts'] if 'additionalContexts' in 结果 and 结果['additionalContexts'] is not None else []#额外上下文
            for 上下文块 in 额外:
                接受上下文(上下文块)#接收额外上下文
            if 'concludesTurn' in 结果 and 结果['concludesTurn'] is True:
                已结束=True#合并结束旗标
            已提交+=1#前进提交
    在飞={}#在飞派发
    def 启动调用(下标):
        """启动一条调用。"""
        nonlocal 已启动,调度失败#修改外层
        调用=组[下标]#取出调用
        调用序号表[下标]=追加工具调用(会话,轮次,步骤,调用['block'])#先记下 tool/call
        已启动+=1#已启动加一
        调度器=上下文.tools[调度器符号]#分阶段调度器
        已准备=调度器['prepare'](调用['exec'])#预执行
        抛调度失败()#预执行后检查失败
        种类=已准备['kind']#准备结果
        if 种类=='dispatch':
            条任务=队列(1)#本条落定
            def 执行派发():
                """执行派发并填槽。"""
                nonlocal 调度失败#修改外层
                try:
                    结局=调度器['dispatch'](已准备['exec'])#派发
                    槽表[下标]={
                        'exec':已准备['exec'],#运行上下文
                        'result':结局['result'],#执行结果
                        'needsPost':结局['kind']=='post-result',#是否还要后处理
                    }#填槽
                except BaseException as 错误:
                    with 失败锁:
                        if 调度失败 is None:
                            调度失败={'error':错误}#记下首次失败
                放入成功(条任务,下标)#返回下标以便排空
            工作=threading.Thread(target=执行派发)#派发线程
            工作.daemon=True#不挡住退出
            工作.start()#启动
            在飞[下标]=条任务#记入在飞
        elif 种类=='post-result':
            槽表[下标]={
                'exec':已准备['exec'],#运行上下文
                'result':已准备['result'],#已有结果
                'needsPost':True,#仍要后处理
            }#填槽
        elif 种类=='final-result':
            槽表[下标]={
                'exec':已准备['exec'],#运行上下文
                'result':已准备['result'],#最终结果
                'needsPost':False,#直接收尾
            }#填槽
        else:
            断言永不(已准备,'tool-call scheduler prepare result')#不可达
    def 填池():
        """填满并行池。"""
        nonlocal 下一启动,已中#修改外层
        while (not 已中) and 下一启动<len(组) and len(在飞)<上限:
            下一条=组[下一启动]#下一条
            if 下一启动>0 and 模式=='parallel':
                下模式=上下文.tools.执行模式(下一条['exec'])['kind']#再分类
                if 下模式!='parallel':
                    break#再分类成独占则停
            启动调用(下一启动)#启动
            下一启动+=1#前进
            抛调度失败()#检查失败
            提交已就绪()#提交已就绪
            抛调度失败()#再检查
            if 已中止(信号):
                已中=True#记下中止
    try:
        填池()#先填满
        while len(在飞)>0:
            落定下标=赛跑取值(list(在飞.values()))#等最先落定
            在飞.pop(落定下标,None)#移出在飞
            抛调度失败()#检查失败
            提交已就绪()#提交已就绪
            抛调度失败()#再检查
            if 已中止(信号):
                已中=True#记下中止
            填池()#再补货
    except BaseException as 错误:
        if 调度失败 is None:
            调度失败={'error':错误}#记下首次失败
        全部排空队列(list(在飞.values()))#排空在飞
        raise 调度失败['error']#抛出失败
    if 已中:
        for 调用 in 组[已启动:]:
            追加跳过的工具调用(会话,轮次,步骤,调用['block'])#为未启动记下合成
        return {'consumed':len(组),'aborted':True,'concluded':已结束}#整组已消费
    if 已提交!=已启动:
        raise 循环错误('tool-call scheduler: uncommitted settled calls')#已启动必须已提交
    return {'consumed':已启动,'aborted':False,'concluded':已结束}#返回组结局

def 执行工具调用(上下文,轮次,步骤,工具调用列表,信号,接受上下文):
    """按在线并发模式调度一步助手工具调用。"""
    智能体=上下文.agents.要求发起方()#取出发起 Agent
    会话=智能体.session#取出会话
    已规划=[]#规划每条调用
    for 块 in 工具调用列表:
        已规划.append({
            'block':块,#调用块
            'exec':{
                'callId':块['id'],#调用 id
                'name':块['name'],#工具名
                'arguments':解析参数(块['arguments']),#解析参数
                'agent':智能体,#发起 Agent
                'signal':信号,#中止信号
            },#执行输入
        })#一条规划
    下一=0#下一未消费下标
    已结束=False#是否已结束轮次
    while 下一<len(已规划):
        首条=已规划[下一]#本组首条
        模式=上下文.tools.执行模式(首条['exec'])['kind']#当前执行模式
        组=已规划[下一:] if 模式=='parallel' else [首条]#并行吃剩余，独占只吃一条
        结局=执行一组(上下文,轮次,步骤,组,模式,信号,接受上下文)#执行一组
        下一+=结局['consumed']#前进消费数
        已结束=已结束 or 结局['concluded']#合并结束旗标
        if 结局['aborted']:
            for 调用 in 已规划[下一:]:
                追加跳过的工具调用(会话,轮次,步骤,调用['block'])#为跳过的记下合成结果
            return {'concluded':已结束}#带着结束旗标返回
    return {'concluded':已结束}#全部跑完
