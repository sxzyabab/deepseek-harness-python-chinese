"""循环构建的 LLM 调用的包内请求重建不变量。"""
import json#JSON
from ...模型后端.llm import 是否循环请求,是否冻结#循环请求判定与冻结判定
from ..会话 import 折叠请求头#请求头折叠
from ...依赖 import cordis#外部依赖胶水
from .辅助 import 取#读字段

包名='@deepseek-ai/dsh-agent-loop'#本包名
名称='agent-loop-invariant'#配套插件名
注入=['invariants']#依赖 invariants 服务

def 转json(值):#按 JS JSON.stringify 的紧凑形态编码
    """按 JS JSON.stringify 的紧凑形态编码。"""
    return json.dumps(值,separators=(',',':'),ensure_ascii=False)#紧凑 JSON

def 安装(上下文对象,失败):#把请求重建贡献安装进其子注册光纤
    """把请求重建贡献安装进其子注册光纤。"""
    def 监听流(选项,下一步,*其余):#前置校验循环组装的请求后再委托
        """前置校验循环组装的请求后再委托。"""
        if not 是否循环请求(选项):#非循环请求
            return 下一步()#非循环请求则放过
        if not 是否冻结(选项):#请求未冻结
            失败('a loop-built request must be frozen')#请求必须冻结
        if 取(选项,'sessionId') is None:#没有会话 id
            失败('a loop-built request must carry a session id')#必须带会话 id
        会话=上下文对象.sessions.获取(取(选项,'sessionId'))#按 id 取在线会话
        if not 会话:#不是在线会话
            失败('a loop-built request must carry a live session id, got "'+str(取(选项,'sessionId'))+'"')#必须是在线会话
        if not 是否冻结(取(选项,'messages')):#消息数组未冻结
            失败('a loop-built request must carry a frozen messages array')#消息必须冻结
        事件们=会话.events#会话日志
        有步骤=False#是否有步骤开始
        for 事件 in 事件们:#扫描日志
            if 取(事件,'type')=='step/start':#步骤开始
                有步骤=True#见到步骤开始
                break#已找到
        if not 有步骤:#日志里没有步骤开始
            return 失败('a loop-built request with no step/start in its session log')#缺少 step/start
        头=折叠请求头(事件们)#折叠请求头
        if 头 is None:#没有请求头事件
            return 失败('a loop-built request with no request/header event in its session log')#缺少 request/header
        期望=会话.派生消息()#按日志派生消息
        if 转json(取(选项,'messages'))!=转json(期望):#与派生产物不一致
            失败('llm request for session "'+str(会话.id)+'" diverges from the dispatch-time durable derivation (log-reconstruction desync)')#派发时耐久派生不同步
        配置=取(头,'config')#折叠配置
        工具甲=取(选项,'tools')#请求工具
        if 工具甲 is None:#缺席
            工具甲=[]#缺省空表
        工具乙=取(头,'tools')#头上工具
        if 工具乙 is None:#缺席
            工具乙=[]#缺省空表
        头匹配=(取(选项,'model')==取(配置,'model')
            and 取(选项,'system')==取(头,'system')
            and 取(选项,'temperature')==取(配置,'temperature')
            and 取(选项,'maxTokens')==取(配置,'maxTokens')
            and 转json(取(选项,'stop'))==转json(取(配置,'stop'))
            and 转json(工具甲)==转json(工具乙))#与折叠请求头逐项比对
        if not 头匹配:#请求头字段不一致
            失败('llm request for session "'+str(会话.id)+'" diverges from the folded request header')#与折叠请求头分叉
        return 下一步()#校验通过后继续
    上下文对象.on('llm/stream',监听流,{'global':True,'prepend':True})#全局且前置

安装.inject=['sessions']#安装时还要 sessions

def 应用(上下文对象):#注册 Agent 循环不变量配套
    """注册 Agent 循环不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记贡献并返回拆除器
