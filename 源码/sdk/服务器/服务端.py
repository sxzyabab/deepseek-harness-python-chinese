"""进程外 harness SDK 的 JSON-RPC 方法与通知。

对齐上游 `sdk/server/src/server.ts`。公开面仅中文名。外围上下文拥有插件、持久化与已配置的适配器。
"""
import os#默认工作目录与路径解析
from .. import llm_deepseek#DeepSeek LLM 插件模块
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待
聚合错误=cordis.工具.聚合错误#聚合错误
from ..llm import 创建用户消息#用户消息工厂
from ..作用域 import 获取载体键#作用域载体键
from ..会话 import 会话标识#会话 id 品牌构造

__all__=['装备SDKJSONRPC服务端','成功状态']#仅中文公开名

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 子智能体父(载体):#从服务所拥有的作用域载体上取回发起委托的父智能体
    """载体键即父智能体。"""
    return 获取载体键(载体)#路由键

def 成功状态(原因,选项):#把停止原因映射为线状态
    """针对 SDK 回合与子智能体结局的部署侧状态映射。"""
    if 原因=='completed':#正常完成
        return 'ok'#视为 ok
    if 原因=='max-tokens' and 取字段(选项,'maxTokensAsSuccess') is True:#可选把 max-tokens 也映射为 ok
        return 'ok'#成功
    return 'error'#其余为 error

class 装备SDKJSONRPC服务端:#SDK JSON-RPC 服务端
    """基于一份已启动的 harness 上下文与一条传输对等端的 SDK 服务端。构造时订阅会话、智能体与子智能体生命周期事件，直至关闭；不支持再次初始化。"""
    def __init__(自身,上下文对象,传输,选项=None):#绑定上下文、传输与选项并订阅生命周期
        """记下上下文、传输与选项，并挂上生命周期订阅。"""
        自身.ctx=上下文对象#harness 上下文
        自身.传输=传输#JSON-RPC 对等端
        自身.选项=选项 or {}#部署选项，默认空
        自身.cwd=os.getcwd()#会话工作目录，默认进程 cwd
        自身.provider='deepseek-official'#提供方路由
        自身.model='deepseek-official'#模型名
        自身.maxTokens=None#可选输出 token 上限
        自身.llm光纤=None#按需挂载的 DeepSeek 适配器光纤
        自身.会话们={}#已创建会话记录 sessionId → {handle}
        自身.会话创建中={}#进行中的会话创建
        自身.拆除们=[]#事件订阅拆除函数
        自身.关闭任务=None#关闭任务去重
        自身.正在关闭=False#是否已进入关闭
        服务选项=自身.选项#捕获选项供子智能体结束回调使用
        def 会话事件(会话,事件):#订阅会话日志事件
            """向客户端发出会话事件。"""
            自身.传输.通知('session.event',{'sessionId':str(会话.id),'event':事件})#组装并发送
        自身.拆除们.append(上下文对象.on('session/event',会话事件))#登记拆除
        def 智能体状态(载荷):#订阅智能体状态
            """发出会话状态通知。"""
            智能体=取字段(载荷,'agent')#智能体
            状态=取字段(载荷,'status')#状态
            自身.传输.通知('session.status',{'sessionId':str(智能体.session.id),'status':状态})#发出
        自身.拆除们.append(上下文对象.on('agent/status',智能体状态))#登记拆除
        def 会话已创建(会话):#订阅会话创建
            """子智能体才有父会话。"""
            父会话=取字段(取字段(会话,'header'),'parentSession')#读取父会话
            if 父会话 is None:#无父会话
                return#不是子智能体启动
            自身.传输.通知('subagent.started',{#发出子智能体启动通知
                'parentSessionId':str(父会话),#父会话 id
                'childSessionId':str(会话.id),#子会话 id
            })#通知结束
        自身.拆除们.append(上下文对象.on('session/created',会话已创建))#登记拆除
        def 子智能体结束(载体,信息):#订阅子智能体结束；绑到把载体作为首参
            """本协议只报告进程内子会话。"""
            父=子智能体父(载体)#从作用域载体取父智能体
            if not 取字段(信息,'local'):#远程运行不报告
                return#跳过
            载荷={#组装结束通知
                'provider':取字段(信息,'provider'),#提供方名
                'agentId':str(取字段(信息,'id')),#子智能体 id
                'parentSessionId':str(父.session.id),#父会话 id
                'childSessionId':str(取字段(信息,'id')),#子会话 id
                'status':成功状态(取字段(信息,'stopReason'),服务选项),#映射后的线状态
                'stopReason':取字段(信息,'stopReason'),#原始停止原因
            }#载荷主体
            末条=取字段(信息,'lastAssistantMessage')#可选末条助手消息
            if 末条 is not None:#有末条
                载荷['lastAssistantMessage']=末条#附带
            传输.通知('subagent.finished',载荷)#发出
        自身.拆除们.append(上下文对象.on('subagent/end',子智能体结束))#登记拆除

    def 初始化(自身,参数):#处理 initialize 请求
        """配置 SDK 路由；仅在尚无主时挂载 DeepSeek 回退适配器。"""
        上限=取字段(参数,'maxTokens')#可选上限
        if 上限 is not None:#若带了 maxTokens
            if (not isinstance(上限,int)) or isinstance(上限,bool) or 上限<=0:#必须是正整数
                raise TypeError('initialize maxTokens must be a positive safe integer')#非法上限
        自身.cwd=os.path.abspath(取字段(参数,'cwd'))#解析并记下工作目录
        自身.provider=取字段(参数,'provider')#记下提供方
        自身.model=取字段(参数,'model')#记下模型
        自身.maxTokens=上限#记下可选 token 上限
        if not 自身.有适配器(自身.provider):#上下文里还没有该提供方
            if 自身.provider!='deepseek-official':#非官方提供方缺失则失败
                raise Exception('no adapter registered for provider "'+str(自身.provider)+'"')#失败
            自身.llm光纤=解开(自身.ctx.plugin(llm_deepseek,{}))#官方提供方则挂载 DeepSeek 回退
        return {'serverInfo':{'name':'deepseek-harness-sdk-runtime','version':'0.0.1'}}#线稳定身份

    def 提示(自身,参数):#处理 session/prompt
        """排队一条已标识的提示，后续活动不归到该次调用。"""
        记录=自身.取或创建会话(取字段(参数,'sessionId'))#取已有会话或惰性创建
        句柄=取字段(记录,'handle')#智能体句柄
        智能体=取字段(句柄,'智能体')#智能体
        if 自身.ctx.agents.获取(智能体.id) is not 智能体:#句柄上的智能体已不在注册表
            raise Exception('session agent was disposed outside the server: '+str(取字段(参数,'sessionId')))#拒绝
        消息=创建用户消息({'content':取字段(参数,'contentBlocks'),'source':{'kind':'user'}})#构造用户消息
        智能体.后续(消息)#投入该会话智能体
        return {'messageId':消息.id}#返回已排队消息 id

    def 关闭(自身):#处理 shutdown，去重并发
        """拆除服务端拥有的智能体、适配器与订阅直至静止。外围上下文继续运行。"""
        if 自身.关闭任务 is None:#首次调用才真正关闭
            自身.关闭任务=已兑现(自身._执行关闭())#启动关闭并记忆
        return 自身.关闭任务#后续调用共用同一承诺

    def _执行关闭(自身):#实际关闭序列
        """返回空对象。"""
        自身.正在关闭=True#标记进入关闭
        进行中=list(自身.会话创建中.values())#快照进行中的创建
        for 一项 in 进行中:#等创建结束
            try:#等待
                解开(一项)#不论成败
            except BaseException:#忽略
                pass#继续
        自身.会话创建中.clear()#清空创建表
        记录们=list(自身.会话们.values())#快照已有会话记录
        自身.会话们.clear()#清空会话表
        失败们=[]#收集拆除失败
        while len(自身.拆除们)>0:#逐个拆除事件订阅
            try:#单次拆除
                拆=自身.拆除们.pop()#弹出
                if 拆 is not None:#有拆除器
                    拆()#调用
            except BaseException as 错误:#记下
                失败们.append(错误)#记录
        for 记录 in 记录们:#拆除智能体句柄
            try:#dispose
                解开(取字段(记录,'handle').拆除())#每个会话句柄 dispose
            except BaseException as 错误:#记下
                失败们.append(错误)#记录
        if 自身.llm光纤 is not None:#有挂载适配器
            try:#拆适配器
                解开(自身.llm光纤.dispose())#拆除
            except BaseException as 错误:#记下
                失败们.append(错误)#记录
            自身.llm光纤=None#丢掉引用
        if len(失败们)==1:#恰好一次失败
            raise 失败们[0]#原样抛出
        if len(失败们)>1:#多次失败
            raise 聚合错误(失败们,'SDK server teardown failed')#聚合
        return {}#成功则返回空对象

    def 处理请求(自身,方法,参数):#按方法名派发
        """未知方法抛错（→ JSON-RPC 错误响应）。"""
        if 方法=='initialize':#握手
            return 自身.初始化(参数 or {})#转为握手参数并处理
        if 方法=='session/prompt':#会话提示
            return 自身.提示(参数 or {})#转为提示参数并处理
        if 方法=='shutdown':#关闭
            return 自身.关闭()#执行关闭
        raise Exception('unknown DeepSeek Harness SDK runtime method: '+str(方法))#未知方法

    def 取或创建会话(自身,会话号):#取会话或开始一次创建
        """已有则直接返回；否则启动创建并去重并发。"""
        if 自身.正在关闭:#关闭中拒绝新会话
            raise Exception('SDK server is shutting down')#拒绝
        已有=自身.会话们.get(会话号)#查已完成记录
        if 已有 is not None:#已有
            return 已有#直接返回
        进行中=自身.会话创建中.get(会话号)#查进行中的创建
        if 进行中 is not None:#已有创建承诺
            return 解开(进行中)#共用
        def 跑创建():#真正创建
            """按 SDK 会话 id 创建智能体。"""
            选项={'provider':自身.provider,'model':自身.model}#智能体路由选项
            if 自身.maxTokens is not None:#有上限才写入
                选项['maxTokens']=自身.maxTokens#上限
            句柄=解开(自身.ctx.agents.创建({#创建智能体
                'sessionId':会话标识(会话号),#品牌化会话 id
                'meta':{'cwd':自身.cwd},#会话头工作目录
                'agentOptions':选项,#路由选项
            }))#create 结束
            记录={'handle':句柄}#包成会话记录
            自身.会话们[会话号]=记录#写入已创建表
            return 记录#返回记录
        try:#启动创建
            自身.会话创建中[会话号]=已兑现(True)#占位防并发
            return 跑创建()#创建并返回
        finally:#无论成败都清掉进行中条目
            自身.会话创建中.pop(会话号,None)#删除

    def 有适配器(自身,提供方):#上下文是否已有该提供方适配器
        """无 llm 服务则视为没有。"""
        llm=自身.ctx.get('llm')#可选 llm 服务
        if llm is None:#无服务
            return False#没有
        for 条目 in llm.listProviders():#逐个提供方
            if 取字段(条目,'id')==提供方:#命中
                return True#有
        return False#没有
