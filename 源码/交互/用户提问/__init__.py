"""用户提问能力缝（ctx.userQuestions）的服务定义：在人类回答问题之前暂停一次智能体工具调用的 UI 后端服务。面向模型的工具住在 @deepseek-ai/dsh-tool-ask-user；UI 包提供那个唯一活动的提供方。"""
from cordis import 服务#Cordis 服务基类
from cordis.工具 import 已兑现,是否thenable#立刻兑现与可等待判定
from llm import 装备错误#Harness 错误基类
from .类型 import (#再导出线路安全问答类型
    询问用户问题选项,#可选答案
    询问用户问题意图,#展示意图
    询问用户问题项,#一条问题
    询问用户问题答案项,#一条答案
    询问用户问题答案,#整份回答
)#类型再导出结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

class 询问用户问题请求:#向人类要一份答案的请求（运行时结构，非线路 TypedDict）
    """向人类要一份答案的请求。"""
    def __init__(自身,questions,agent=None,signal=None):#问题列表与可选智能体/取消信号
        """记下问题、可选调用智能体与中止信号。"""
        自身.questions=questions#要展示的问题
        自身.agent=agent#精确存活的调用智能体；请求来自智能体工具调用时提供
        自身.signal=signal#所属工具/步骤的中止信号

class 用户提问提供方:#用户提问的 UI 侧提供方协议
    """用户提问的 UI 侧提供方。"""
    def ask(自身,request):#向 UI 要答案
        """向 UI 收集人类答案。"""
        raise NotImplementedError#由 UI 包实现

class 用户提问错误(装备错误):#用户提问失败的稳定错误分类
    """用户提问失败的稳定错误分类。"""
    def __init__(自身,消息,码,options=None):#构造带码错误
        """记下人类可读拒绝原因与稳定分类码。"""
        if options is None:#无额外选项
            装备错误.__init__(自身,消息,码)#交给装备错误
        else:#带 cause 等选项
            装备错误.__init__(自身,消息,码,options)#交给装备错误
        自身.name='UserQuestionError'#固定错误名

class 用户提问服务(服务):#ctx.userQuestions：一个活动 UI 提供方外加 ask() API
    """ctx.userQuestions：一个活动 UI 提供方外加 ask() API。"""
    def __init__(自身,上下文):#把本服务登记为 userQuestions
        """以 userQuestions 名安装服务。"""
        super().__init__(上下文,'userQuestions')#以 userQuestions 名安装服务
        自身.提供方=None#当前唯一提供方

    def 登记提供方(自身,提供方):#登记 UI 提供方；一个上下文里只能有一个活动提供方
        """登记 UI 提供方。一个上下文里只能有一个活动提供方。返回注销本提供方的拆除器。"""
        def 装():#effect 内安装
            """effect 内安装唯一提供方。"""
            if 自身.提供方 is not None:#已有提供方
                raise 用户提问错误('a user-questions provider is already registered','DUPLICATE_PROVIDER')#拒绝重复
            自身.提供方=提供方#装上提供方
            def 拆():#拆除时清槽
                """拆除时清槽。"""
                自身.提供方=None#卸掉提供方
            return 拆#拆除器
        拆除=自身.ctx.effect(装,'userInteraction.registerProvider()')#绑回本服务
        def 对外拆除():#对外返回 disposer
            """调用 effect 拆除器。"""
            拆除()#拆除
        return 对外拆除#disposer

    def ask(自身,request):#向活动 UI 提供方提问并等待用户回答
        """向活动 UI 提供方提问并等待用户回答。调用方提供智能体时，人类交互只对精确存活的运行时根有效。"""
        信号=取字段(request,'signal')#可选取消信号
        if 信号 is not None and 取字段(信号,'aborted'):#调用前已取消
            raise 用户提问错误('ask_user_question was aborted before the user answered','ASK_ABORTED')#报告已中止
        问题们=取字段(request,'questions')#问题列表
        if 问题们 is None or len(问题们)==0:#至少要有一题
            raise 用户提问错误('ask_user_question requires at least one question','EMPTY_QUESTIONS')#拒绝空列表
        智能体=取字段(request,'agent')#可选调用智能体
        if 智能体 is not None:#带了智能体就要验所有权
            注册表=自身.ctx.get('agents')#取智能体注册表
            if 注册表 is None or 注册表.get(取字段(智能体,'id')) is not 智能体:#不是精确存活实例
                raise 用户提问错误(#拒绝非存活调用方
                    'human interaction requires the exact live calling agent when an agent is supplied',#须精确存活文案（字面量不译）
                    'CALLER_NOT_LIVE')#非存活码
            if 智能体 not in 注册表.roots():#被别的智能体拥有
                raise 用户提问错误(#子智能体没有人类回答者
                    'human interaction is unavailable while the calling agent is owned by another live agent; '#委托不可用文案前半（字面量不译）
                    +"include the unresolved question or decision in the child agent's final result",#委托不可用文案后半（字面量不译）
                    'DELEGATED_CALLER')#委托调用方码
        #展示意图断言类型表达不了的两件事：点名的批准标签是本问题自己的选项之一；计划评审带着它所评审的计划。
        for 题目 in 问题们:#逐题检查意图
            意图=取字段(题目,'intent')#可选展示意图
            if 意图 is None:#无意图则跳过
                continue#跳过
            选项们=取字段(题目,'options') or []#选项列表，缺省空
            批准=取字段(意图,'approve')#批准选项标签
            if not any(取字段(选项,'label')==批准 for 选项 in 选项们):#批准标签不在选项里
                raise 用户提问错误(#意图与选项对不上
                    'question '+str(取字段(题目,'id'))+' declares intent '+str(取字段(意图,'kind'))#批准标签错位文案前半（字面量不译）
                    +' whose approve label '+repr(批准)+' names none of its options',#批准标签错位文案后半（字面量不译）
                    'BAD_INTENT')#坏意图码
            if 取字段(题目,'detail') is None:#计划评审必须带细节
                raise 用户提问错误(#缺评审对象
                    'question '+str(取字段(题目,'id'))+' declares intent '+str(取字段(意图,'kind'))#缺评审细节文案前半（字面量不译）
                    +' without the detail it reviews',#缺评审细节文案后半（字面量不译）
                    'BAD_INTENT')#坏意图码
        if 自身.提供方 is None:#没有 UI 提供方
            raise 用户提问错误('no user-questions provider is registered','NO_PROVIDER')#拒绝无提供方
        return 已兑现(解开(自身.提供方.ask(request)))#交给 UI 收集答案

default=用户提问服务#默认导出提问服务
默认=用户提问服务#中文默认导出
