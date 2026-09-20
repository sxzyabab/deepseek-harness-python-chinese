import json#JSON
from ...模型后端.llm import 是否循环请求,是否冻结#循环请求判定与冻结判定
from ..会话 import 折叠请求头#请求头折叠

包名='@deepseek-ai/dsh-agent-loop'
名称='agent-loop-invariant'
依赖=['invariants']

def 转json(值):
    """把值编成紧凑 JSON。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON

def 安装(上下文,失败):
    """把请求重建贡献安装进其子注册纤程。"""
    def 监听流(选项,下一步,*其余):
        """前置校验循环组装的请求后再委托。"""
        if not 是否循环请求(选项):
            return 下一步()#非循环请求则放过
        if not 是否冻结(选项):
            失败('循环组装的请求必须已冻结')#请求必须冻结
        if 'sessionId' not in 选项 or 选项['sessionId'] is None:
            失败('循环组装的请求必须携带会话 id')#必须带会话 id
        会话=上下文.sessions.获取(选项['sessionId'])#按 id 取在线会话
        if 会话 is None:
            失败('循环组装的请求必须携带在线会话 id，实际为 "'+str(选项['sessionId'])+'"')#必须是在线会话
        if not 是否冻结(选项['messages']):
            失败('循环组装的请求必须携带冻结的 messages 数组')#消息必须冻结
        事件列表=会话.events#会话日志
        有步骤=False#是否有步骤开始
        for 事件 in 事件列表:
            if 事件['type']=='step/start':
                有步骤=True#见到步骤开始
                break#已找到
        if not 有步骤:
            return 失败('循环组装的请求其会话日志中没有 step/start')#缺少 step/start
        头=折叠请求头(事件列表)#折叠请求头
        if 头 is None:
            return 失败('循环组装的请求其会话日志中没有 request/header 事件')#缺少 request/header
        期望=会话.派生消息()#按日志派生消息
        if 转json(选项['messages'])!=转json(期望):
            失败('会话 "'+str(会话.id)+'" 的 llm 请求与派发时耐久派生分叉（日志重建不同步）')#派发时耐久派生不同步
        配置=头['config']#折叠配置
        工具甲=选项['tools'] if 'tools' in 选项 and 选项['tools'] is not None else []#请求工具
        工具乙=头['tools'] if 'tools' in 头 and 头['tools'] is not None else []#头上工具
        选项系统=选项['system'] if 'system' in 选项 else None#请求系统（循环请求须缺席）
        选项温度=选项['temperature'] if 'temperature' in 选项 else None#请求温度
        配置温度=配置['temperature'] if 'temperature' in 配置 else None#配置温度
        选项上限=选项['maxTokens'] if 'maxTokens' in 选项 else None#请求上限
        配置上限=配置['maxTokens'] if 'maxTokens' in 配置 else None#配置上限
        选项停止=选项['stop'] if 'stop' in 选项 else None#请求停止
        配置停止=配置['stop'] if 'stop' in 配置 else None#配置停止
        # 系统提示走表面节点 0 的 messages，从不作为 system。
        头匹配=(选项['model']==配置['model']
            and 选项系统 is None
            and 选项温度==配置温度
            and 选项上限==配置上限
            and 转json(选项停止)==转json(配置停止)
            and 转json(工具甲)==转json(工具乙))#与折叠请求头逐项比对
        if not 头匹配:
            失败('会话 "'+str(会话.id)+'" 的 llm 请求与折叠请求头分叉')#与折叠请求头分叉
        return 下一步()#校验通过后继续
    上下文.监听('llm/stream',监听流,{'全局':True,'前置':True})#全局且前置

def 应用(上下文):
    """注册 Agent 循环不变量配套。"""
    return 上下文.invariants.register(包名,安装)#登记贡献并返回拆除器

应用.name=名称
应用.inject=依赖
安装.inject=['sessions']
default=应用#Cordis 默认导出槽
