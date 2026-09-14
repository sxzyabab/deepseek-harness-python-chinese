import os,threading#默认工作目录与路径解析、创建去重
from concurrent.futures import Future as 原生结果#单次操作结果
from ...模型后端 import llm_deepseek#DeepSeek LLM 插件模块
from ...依赖 import cordis#外部依赖胶水
聚合错误=cordis.聚合错误#拆除失败聚合
from ...模型后端.llm import 创建用户消息#用户消息工厂
from ...内核.作用域 import 获取载体键#作用域载体键
from ...内核.会话 import 会话标识#会话 id 品牌构造

__all__=['装备SDKJSONRPC服务端','成功状态','SDK服务端错误','操作任务']#仅中文公开名

class SDK服务端错误(Exception):
    """本包异常基类。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身._未来.set_exception(SDK服务端错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

def 子智能体父(载体):
    """从服务所拥有的作用域载体上取回发起委托的父智能体。"""
    return 获取载体键(载体)#路由键

def 成功状态(原因,选项):
    """针对 SDK 回合与子智能体结局的部署侧状态映射。选项为 dict。"""
    if 原因=='completed':#正常完成
        return 'ok'#视为 ok
    if 原因=='max-tokens' and 'maxTokensAsSuccess' in 选项 and 选项['maxTokensAsSuccess'] is True:#可选把 max-tokens 也映射为 ok
        return 'ok'#成功
    return 'error'#其余为 error

class 装备SDKJSONRPC服务端:
    """基于一份已启动的 harness 上下文与一条传输对等端的 SDK 服务端。构造时订阅会话、智能体与子智能体生命周期事件，直至关闭；不支持再次初始化。"""
    def __init__(自身,上下文对象,传输,选项=None):
        """记下上下文、传输与选项，并挂上生命周期订阅。选项为 dict。"""
        自身.ctx=上下文对象#harness 上下文
        自身.传输=传输#JSON-RPC 对等端
        自身.选项=选项 if 选项 is not None else {}#部署选项，默认空
        自身.cwd=os.getcwd()#会话工作目录，默认进程 cwd
        自身.provider='deepseek-official'#提供方路由
        自身.model='deepseek-official'#模型名
        自身.maxTokens=None#可选输出 token 上限
        自身.llm光纤=None#按需挂载的 DeepSeek 适配器光纤
        自身.会话表={}#已创建会话记录 sessionId → {handle}
        自身.会话创建中={}#进行中的会话创建
        自身.拆除列表=[]#事件订阅拆除函数
        自身.关闭任务=None#关闭任务去重
        自身.正在关闭=False#是否已进入关闭
        自身.锁=threading.Lock()#会话创建互斥
        服务选项=自身.选项#捕获选项供子智能体结束回调使用
        def 会话事件(会话,事件):
            """向客户端发出会话事件。"""
            自身.传输.通知('session.event',{'sessionId':str(会话.id),'event':事件})#组装并发送
        自身.拆除列表.append(上下文对象.监听('session/event',会话事件))#登记拆除
        def 智能体状态(载荷):
            """发出会话状态通知。载荷为 dict。"""
            智能体=载荷['agent'] if 'agent' in 载荷 else None#智能体
            状态=载荷['status'] if 'status' in 载荷 else None#状态
            自身.传输.通知('session.status',{'sessionId':str(智能体.session.id),'status':状态})#发出
        自身.拆除列表.append(上下文对象.监听('agent/status',智能体状态))#登记拆除
        def 会话已创建(会话):
            """子智能体才有父会话。会话为对象，头为 dict。"""
            头=会话.header#会话头
            父会话=头['parentSession'] if isinstance(头,dict) and 'parentSession' in 头 else None#读取父会话
            if 父会话 is None:#无父会话
                return#不是子智能体启动
            自身.传输.通知('subagent.started',{#发出子智能体启动通知
                'parentSessionId':str(父会话),#父会话 id
                'childSessionId':str(会话.id),#子会话 id
            })#通知结束
        自身.拆除列表.append(上下文对象.监听('session/created',会话已创建))#登记拆除
        def 子智能体结束(载体,信息):
            """本协议只报告进程内子会话。信息为 dict。"""
            父=子智能体父(载体)#从作用域载体取父智能体
            if 'local' not in 信息 or 信息['local'] is not True:#远程运行不报告
                return#跳过
            载荷={#组装结束通知
                'provider':信息['provider'] if 'provider' in 信息 else None,#提供方名
                'agentId':str(信息['id'] if 'id' in 信息 else None),#子智能体 id
                'parentSessionId':str(父.session.id),#父会话 id
                'childSessionId':str(信息['id'] if 'id' in 信息 else None),#子会话 id
                'status':成功状态(信息['stopReason'] if 'stopReason' in 信息 else None,服务选项),#映射后的线状态
                'stopReason':信息['stopReason'] if 'stopReason' in 信息 else None,#原始停止原因
            }#载荷主体
            if 'lastAssistantMessage' in 信息 and 信息['lastAssistantMessage'] is not None:#有末条
                载荷['lastAssistantMessage']=信息['lastAssistantMessage']#附带
            传输.通知('subagent.finished',载荷)#发出
        自身.拆除列表.append(上下文对象.监听('subagent/end',子智能体结束))#登记拆除

    def 初始化(自身,参数):
        """配置 SDK 路由；仅在尚无主时挂载 DeepSeek 回退适配器。参数为 dict。"""
        上限=参数['maxTokens'] if 'maxTokens' in 参数 else None#可选上限
        if 上限 is not None:#若带了 maxTokens
            if isinstance(上限,bool) or (not isinstance(上限,int)) or 上限<=0:#必须是正整数
                raise TypeError('initialize 的 maxTokens 必须是正整数')#非法上限
        自身.cwd=os.path.abspath(参数['cwd'] if 'cwd' in 参数 else None)#解析并记下工作目录
        自身.provider=参数['provider'] if 'provider' in 参数 else None#记下提供方
        自身.model=参数['model'] if 'model' in 参数 else None#记下模型
        自身.maxTokens=上限#记下可选 token 上限
        if not 自身.有适配器(自身.provider):#上下文里还没有该提供方
            if 自身.provider!='deepseek-official':#非官方提供方缺失则失败
                raise SDK服务端错误('没有为提供方 "'+str(自身.provider)+'" 登记适配器')#失败
            光纤=自身.ctx.启动插件(llm_deepseek,{})#官方提供方则挂载 DeepSeek 回退
            光纤.等待()#等到适配器已登记
            自身.llm光纤=光纤#记下
        return {'serverInfo':{'name':'deepseek-harness-sdk-runtime','version':'0.0.1'}}#线稳定身份

    def 提示(自身,参数):
        """排队一条已标识的提示，后续活动不归到该次调用。参数为 dict。"""
        记录=自身.取或创建会话(参数['sessionId'] if 'sessionId' in 参数 else None)#取已有会话或惰性创建
        句柄=记录['handle']#智能体句柄
        智能体=句柄.智能体#智能体
        if 自身.ctx.agents.获取(智能体.id) is not 智能体:#句柄上的智能体已不在注册表
            raise SDK服务端错误('会话智能体已在服务端之外被拆除：'+str(参数['sessionId'] if 'sessionId' in 参数 else None))#拒绝
        消息=创建用户消息({'content':参数['contentBlocks'] if 'contentBlocks' in 参数 else None,'source':{'kind':'user'}})#构造用户消息
        智能体.后续(消息)#投入该会话智能体
        return {'messageId':消息.id}#返回已排队消息 id

    def 关闭(自身):
        """拆除服务端拥有的智能体、适配器与订阅直至静止。外围上下文继续运行。"""
        if 自身.关闭任务 is None:#首次调用才真正关闭
            自身.关闭任务=自身._执行关闭()#启动关闭并记忆
        return 自身.关闭任务#后续调用共用同一结果

    def _执行关闭(自身):
        """返回空对象。"""
        自身.正在关闭=True#标记进入关闭
        进行中=list(自身.会话创建中.values())#快照进行中的创建
        for 一项 in 进行中:#等创建结束
            try:
                一项.等待()#不论成败
            except BaseException:
                pass#继续
        自身.会话创建中.clear()#清空创建表
        记录列表=list(自身.会话表.values())#快照已有会话记录
        自身.会话表.clear()#清空会话表
        失败列表=[]#收集拆除失败
        while len(自身.拆除列表)>0:#逐个拆除事件订阅
            try:
                拆=自身.拆除列表.pop()#弹出
                if 拆 is not None:#有拆除器
                    拆()#调用
            except BaseException as 错误:
                失败列表.append(错误)#记录
        for 记录 in 记录列表:#拆除智能体句柄
            try:
                记录['handle'].拆除()#每个会话句柄 dispose
            except BaseException as 错误:
                失败列表.append(错误)#记录
        if 自身.llm光纤 is not None:#有挂载适配器
            try:
                自身.llm光纤.拆除()#拆除
            except BaseException as 错误:
                失败列表.append(错误)#记录
            自身.llm光纤=None#丢掉引用
        if len(失败列表)==1:#恰好一次失败
            raise 失败列表[0]#原样抛出
        if len(失败列表)>1:#多次失败
            raise 聚合错误(失败列表,'SDK 服务端拆除失败')#聚合
        return {}#成功则返回空对象

    def 处理请求(自身,方法,参数):
        """未知方法抛错（→ JSON-RPC 错误响应）。参数为 dict。"""
        载荷=参数 if isinstance(参数,dict) else {}#非对象则空对象
        if 方法=='initialize':#握手
            return 自身.初始化(载荷)#转为握手参数并处理
        if 方法=='session/prompt':#会话提示
            return 自身.提示(载荷)#转为提示参数并处理
        if 方法=='shutdown':#关闭
            return 自身.关闭()#执行关闭
        raise SDK服务端错误('未知的 DeepSeek Harness SDK 运行时方法：'+str(方法))#未知方法

    def 取或创建会话(自身,会话号):
        """已有则直接返回；否则启动创建并去重并发。"""
        if 自身.正在关闭:#关闭中拒绝新会话
            raise SDK服务端错误('SDK 服务端正在关闭')#拒绝
        应执行创建=False#是否由本调用执行创建
        with 自身.锁:#互斥
            已有=自身.会话表[会话号] if 会话号 in 自身.会话表 else None#查已完成记录
            if 已有 is not None:#已有
                return 已有#直接返回
            进行中=自身.会话创建中[会话号] if 会话号 in 自身.会话创建中 else None#查进行中的创建
            if 进行中 is not None:#已有创建任务
                创建=进行中#共用
            else:#新创建
                创建=操作任务()#共享任务
                自身.会话创建中[会话号]=创建#登记
                应执行创建=True#本调用执行
        if 应执行创建:#由本调用执行创建体
            try:
                选项={'provider':自身.provider,'model':自身.model}#智能体路由选项
                if 自身.maxTokens is not None:#有上限才写入
                    选项['maxTokens']=自身.maxTokens#上限
                句柄=自身.ctx.agents.创建({#创建智能体
                    'sessionId':会话标识(会话号),#品牌化会话 id
                    'meta':{'cwd':自身.cwd},#会话头工作目录
                    'agentOptions':选项,#路由选项
                })#create 结束
                记录={'handle':句柄}#包成会话记录
                自身.会话表[会话号]=记录#写入已创建表
                创建.兑现(记录)#兑现
            except BaseException as 错误:
                创建.拒绝(错误)#拒绝
            finally:
                自身.会话创建中.pop(会话号,None)#删除
        return 创建.等待()#结果

    def 有适配器(自身,提供方):
        """无 llm 服务则视为没有。"""
        llm=自身.ctx.获取服务('llm')#可选 llm 服务
        if llm is None:#无服务
            return False#没有
        for 条目 in llm.列出提供方():#逐个提供方
            if 'id' in 条目 and 条目['id']==提供方:#命中
                return True#有
        return False#没有
