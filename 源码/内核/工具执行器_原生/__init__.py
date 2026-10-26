'原生执行器：可见工具直接调用，整批结算走工具运行时已有的分阶段调度'
import json,threading
from ...基础设施.通用工具 import 启动守护线程
from ...基础设施.js特性.promise import PromiseEX as 期约
from ...模型后端.llm import 断言永不,创建工具结果消息
from ..工具 import 工具体前中止
from ..工具.代码模式 import 已中止

__all__=(
    '原生工具执行器','执行工具批次','批次执行错误',
    '名称','注入','应用',
)#英文槽 name/inject/apply 不进此表

class 批次执行错误(Exception):
    '整批内部失败；只认已经提交的结果'
    def __init__(自身,原因,部分):
        '保留原因和已提交的部分结果'
        super().__init__('Tool batch execution failed')#机器比对的消息
        自身.name='ToolBatchExecutionError'#类名槽
        自身.cause=原因#原因
        自身.__cause__=原因#异常链
        自身.部分=部分#已提交结果

class 批次结算:
    '按模型顺序收集结果；有 log 时才写会话'
    def __init__(自身,输入):
        '记下这批的智能体和可选日志步骤'
        自身.输入=输入#原始批次
        自身.结果表=[]#按提交顺序
        自身.上下文表=[]#推迟的用户消息
        日志=输入.get('log')#可选步骤
        自身.日志=日志 if 日志 is not None else None#没有则不写会话
        自身.智能体=输入.get('agent')#写会话时必须有

    def 开始(自身,块):
        '有 log 时追加 tool/call，返回序号'
        if 自身.日志 is None:
            return None#不写会话
        事件=自身.智能体.session.追加('tool/call',{
            'turn':自身.日志['turn'],#轮次
            'step':自身.日志['step'],#步骤
            'callId':块['id'],#调用 id
            'name':块['name'],#工具名
            'arguments':块['arguments'] if 'arguments' in 块 else '',#原始参数
        })#追加调用
        return 事件['seq']#结果要引用它

    def 提交(自身,块,结果,调用序号):
        '提交一条已落定结果，并在有 log 时追加 tool/result'
        if 自身.日志 is not None:
            消息=创建工具结果消息({
                'callId':块['id'],#调用 id
                'content':结果['content'],#内容
                'isError':结果['isError'],#是否错误
            })#结果消息
            载荷={
                'turn':自身.日志['turn'],#轮次
                'step':自身.日志['step'],#步骤
                'message':消息,#结果消息
            }#结果载荷
            错误=结果.get('error')#错误细节
            信息=错误.get('info') if isinstance(错误,dict) else None#结构化信息
            if 信息 is not None:
                载荷['error']=信息#有错误详情则带上
            if 'meta' in 结果 and 结果['meta'] is not None:
                载荷['meta']=结果['meta']#呈现元数据
            自身.智能体.session.追加('tool/result',载荷,{
                'surfaceOp':'append',#追加到表面
                'sourceEventSeqs':[调用序号],#引用调用
            })#追加结果
        自身.结果表.append({'callId':块['id'],'result':结果})#模型顺序
        for 上下文块 in 结果.get('additionalContexts') or []:
            自身.上下文表.append(上下文块)#推迟上下文
        return 结果.get('concludesTurn') is True#是否结束本轮

    def 跳过(自身,块):
        '未开始的调用记一条派发前中止'
        序号=自身.开始(块)#先记调用
        自身.提交(块,{
            'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],#模型可见
            'isError':True,#错误
            'error':{
                'message':'tool call aborted before dispatch',#消息原样
                'info':{'name':'AbortError','code':工具体前中止},#体前码
            },#结构化
        },序号)#再记结果

    def 结果(自身,已结束=None):
        '交出已提交的批次结果'
        if 已结束 is None:
            已结束=False#从已提交结果推导
            for 项 in 自身.结果表:
                if 项['result'].get('concludesTurn') is True:
                    已结束=True#有一条结束本轮
                    break
        return {
            'results':list(自身.结果表),#拷贝
            'additionalContexts':list(自身.上下文表),#拷贝
            'concluded':已结束,#是否结束本轮
        }#批次结果

def 解析参数(原始):
    '非法 JSON 保持原文，空输入变成空对象'
    if 原始 is None or 原始=='':
        return {}#空对象
    try:
        return json.loads(原始)#解析
    except (json.JSONDecodeError,TypeError,ValueError):
        return 原始#原样文本

def 是正整数(值):
    '对齐 Number.isInteger，且至少为 1；布尔不是整数'
    if type(值) is bool:
        return False#布尔不是数字
    if type(值) is int:
        return 值>=1#整数
    if type(值) is float and 值.is_integer():
        return 值>=1#整值浮点
    return False#其余非法

def 执行工具批次(输入,工具,最大并行):
    '用工具运行时的准备、派发、最终化跑完一批；不另写一套管线'
    显式上限=输入.get('maxParallelToolCalls')#本批覆盖
    if 显式上限 is not None and not 是正整数(显式上限):
        raise ValueError('maxParallelToolCalls must be a positive integer')#机器比对
    结局=期约()#整批结算点

    def 跑一组(结算,组,模式,信号):
        '跑一道独占屏障或并行池'
        上限=显式上限 if 显式上限 is not None else 最大并行()#每组重读回调
        if not 是正整数(上限):
            raise ValueError('maxParallel must be a positive integer')#否则一组永远启动不了
        槽表=[None]*len(组)#按模型顺序
        调用序号表=[None]*len(组)#tool/call 序号
        下一启动=0#下一启动下标
        已提交=0#已提交下标
        已启动=0#已启动数
        已中=已中止(信号)#开始时是否已中止
        已结束=False#本组是否结束轮次
        调度失败=None#首次失败
        在飞={}#下标到门和盒子
        唤醒=threading.Event()#有一条派发落定

        def 抛调度失败():
            '有失败则抛出'
            if 调度失败 is not None:
                raise 调度失败#首次失败

        def 提交已就绪():
            '提交连续已落定的槽'
            nonlocal 已提交,已结束
            while 已提交<len(组):
                槽=槽表[已提交]#当前槽
                if 槽 is None:
                    break#还没落定
                调用=组[已提交]#对应调用
                if 槽['kind']=='post-result':
                    结果=工具.最终化调度执行(槽['exec'],槽['result'])#后执行再收尾
                elif 槽['kind']=='final-result':
                    结果=工具.收尾调度执行(槽['exec'],槽['result'])#只收尾
                else:
                    断言永不(槽,'tool-call scheduler prepare result')#不可达
                if 结算.提交(调用['block'],结果,调用序号表[已提交]):
                    已结束=True#合并结束旗标
                已提交+=1#前进

        def 等最先():
            '等在飞里最先落定的一条'
            while True:
                for 下标,条 in list(在飞.items()):
                    if 条['门'].is_set():
                        return 下标#已落定
                唤醒.wait()#等下一次落定
                唤醒.clear()#避免空转

        def 收一条(下标):
            '把一条在飞派发填进槽；失败只记第一次'
            nonlocal 调度失败
            条=在飞.pop(下标)#移出
            条['门'].wait()#保证盒子已写
            盒=条['盒']#派发结果
            if '错误' in 盒:
                if 调度失败 is None:
                    调度失败=盒['错误']#首次失败
                return#槽留空
            结局值=盒['值']#派发结局
            槽表[下标]={
                'exec':条['exec'],#运行上下文
                'kind':结局值['kind'],#是否还要后执行
                'result':结局值['result'],#执行结果
            }#填槽

        def 启动调用(下标):
            '准备一条；需要派发时放到工作线程'
            nonlocal 已启动
            调用=组[下标]#取出
            调用序号表[下标]=结算.开始(调用['block'])#先记 tool/call
            已启动+=1#已启动
            已准备=工具.准备调度执行(调用['exec'])#有序预执行
            抛调度失败()#准备后的失败
            种类=已准备['kind']#准备种类
            if 种类=='dispatch':
                门=threading.Event()#本条落定
                盒={}#值或错误
                def 执行派发(已准备=已准备,盒=盒,门=门):
                    '工作线程跑派发'
                    try:
                        盒['值']=工具.派发调度执行(已准备['exec'])#环绕和函数体
                    except BaseException as 错误:
                        盒['错误']=错误#记失败
                    门.set()#盒子已写
                    唤醒.set()#叫醒车道
                启动守护线程(执行派发)#派发线程
                在飞[下标]={'门':门,'盒':盒,'exec':已准备['exec']}#记入在飞
            elif 种类=='post-result' or 种类=='final-result':
                槽表[下标]={
                    'exec':已准备['exec'],#运行上下文
                    'kind':种类,#是否后执行
                    'result':已准备['result'],#已有结果
                }#不用派发
            else:
                断言永不(已准备,'tool-call scheduler prepare result')#不可达

        def 填池():
            '在上限内启动；并行组里再分类成独占就停'
            nonlocal 下一启动,已中
            while (not 已中) and 下一启动<len(组) and len(在飞)<上限:
                if 下一启动>0 and 模式=='parallel':
                    下模式=工具.执行模式(组[下一启动]['exec'])['kind']#再分类
                    if 下模式!='parallel':
                        break#留给下一道屏障
                启动调用(下一启动)#启动
                下一启动+=1#前进
                抛调度失败()#启动失败
                提交已就绪()#能提交的先提交
                抛调度失败()#提交失败
                if 已中止(信号):
                    已中=True#不再启动

        def 排空在飞():
            '等已启动的派发落定'
            while len(在飞)>0:
                收一条(等最先())#填槽

        try:
            填池()#先填
            while len(在飞)>0:
                收一条(等最先())#一条落定
                抛调度失败()#派发失败
                提交已就绪()#按序提交
                抛调度失败()#提交失败
                if 已中止(信号):
                    已中=True#停止补货
                填池()#再补
        except BaseException as 错误:
            if 调度失败 is None:
                调度失败=错误#记下首次
            排空在飞()#已启动的必须落定
            if 调度失败 is not None:
                raise 调度失败#排空后再抛
        if 已中:
            for 调用 in 组[已启动:]:
                结算.跳过(调用['block'])#未开始的记中止
            return {'consumed':len(组),'aborted':True,'concluded':已结束}#整组已处理
        if 已提交!=已启动:
            raise Exception('tool-call scheduler: uncommitted settled calls')#已启动必须已提交
        return {'consumed':已启动,'aborted':False,'concluded':已结束}#未启动的留给下一组

    def 同步批次():
        '规划、分组、在失败时带上已提交结果'
        结算=批次结算(输入)#收集器
        try:
            智能体=输入.get('agent')#可选智能体
            工具集=输入.get('toolSet')#本步准入；管线尚未读取
            信号=输入['signal']#取消
            已规划=[]#准备好的调用
            for 块 in 输入['calls']:
                执行={
                    'callId':块['id'],#调用 id
                    'name':块['name'],#工具名
                    'arguments':解析参数(块['arguments'] if 'arguments' in 块 else None),#解析参数
                    'signal':信号,#同一取消
                }#执行输入
                if 智能体 is not None:
                    执行['agent']=智能体#作用域
                if 工具集 is not None:
                    执行['toolSet']=工具集#管线目前不读
                已规划.append({'block':块,'exec':执行})#一条
            下一=0#下一组起点
            已结束=False#整批是否结束轮次
            while 下一<len(已规划):
                首条=已规划[下一]#本组首条
                模式=工具.执行模式(首条['exec'])['kind']#分类
                组=已规划[下一:] if 模式=='parallel' else [首条]#并行吃剩余
                组结局=跑一组(结算,组,模式,信号)#跑本组
                下一+=组结局['consumed']#前进
                if 组结局['concluded']:
                    已结束=True#合并
                if 组结局['aborted']:
                    for 条 in 已规划[下一:]:
                        结算.跳过(条['block'])#组间剩余
                    return 结算.结果(已结束)#中止后的结果
            return 结算.结果(已结束)#全部完成
        except BaseException as 错误:
            raise 批次执行错误(错误,结算.结果())#带上已提交部分

    def 跑():
        '工作线程跑完整批，再结算期约'
        try:
            结局.解决(同步批次())#成功
        except BaseException as 错误:
            结局.拒绝(错误)#失败
    启动守护线程(跑)#整批不占调用线程
    return 结局#调用方对期约链接

class 原生工具执行器:
    '直接执行可见能力，并负责整批结算'
    def __init__(自身,上下文,最大并行=None):
        '记下上下文；缺省并行上限是 10'
        if 最大并行 is None:
            def 最大并行():
                '缺省每组最多 10 个并行安全调用'
                return 10
        自身.上下文=上下文#挂载上下文
        自身.最大并行=最大并行#无覆盖时每组读取
        自身.段落表=()#原生执行器没有自己的提示词段

    def 描述(自身,工具列表):
        '把可见定义投影成模型模式，不脱离参数'
        模式列表=[]#模型模式
        for 定义 in 工具列表:
            模式列表.append(自身.上下文.tools.投影模式(定义,False))#不脱离
        return {'schemas':模式列表}#已知名由注册表补

    def 执行(自身,输入):
        '把整批交给已有的分阶段调度'
        return 执行工具批次(输入,自身.上下文.tools,自身.最大并行)#同一套管线

名称='native-tool-executor'#插件名保持字面量
注入=['tools']#工具注册表

def 应用(上下文,配置值=None):
    '在挂载作用域选择原生执行'
    上下文.tools.设置执行器(原生工具执行器(上下文))#挂上执行器

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
