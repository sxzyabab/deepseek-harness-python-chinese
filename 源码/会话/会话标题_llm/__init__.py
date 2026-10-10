'模型会话标题共享策略'
from ...基础设施.通用工具 import 紧凑json编码,utf8字节数

def 已中止(信号):
    '信号按 Event 定死。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 已置位
from ...依赖.schemastery import 字典字段,数字字段,字符串字段
from ...模型后端.llm import 创建用户消息,深冻结,块组装器#LLM 辅助
from ...工具.超时 import 截止#截止
from ..会话标题.归一 import 归一化会话标题#标题归一
from .异常 import 会话标题llm错误#本包异常

会话标题超时码='SESSION_TITLE_TIMEOUT'#超时原因码
最大定时器延迟毫秒=2147483647#定时器延迟上限（毫秒）
配置键=frozenset([#直接构造校验允许的键
    'maxInputBytes','maxOutputTokens','timeoutMs','provider','model',
])#键集
配置字段={
    'maxInputBytes':数字字段(),#输入字节上限
    'maxOutputTokens':数字字段(),#输出 token 上限
    'timeoutMs':数字字段(),#超时
    'provider':字符串字段(),#可选路由
    'model':字符串字段(),#可选模型
}#字段表
会话标题llm配置模式=字典字段(字典结构=配置字段)#配置模式

def 若已中止则抛出(信号):
    '已中止则抛 aborted'
    if 已中止(信号):#已中止
        raise 会话标题llm错误('aborted')#取消

def 断言正整数(名,值):
    '校验一项正整数上限'
    if isinstance(值,bool) or not isinstance(值,int) or 值<=0:#非法
        raise 会话标题llm错误('session-title-llm: '+名+' must be a positive integer')#拒绝

def 解析会话标题llm配置(配置):
    '校验并冻结模型标题策略'
    if 配置 is None or not isinstance(配置,dict):#非法
        raise 会话标题llm错误('session-title-llm: configuration is required')#拒绝
    for 键 in 配置.keys():#未知键
        if 键 not in 配置键:#未知
            raise 会话标题llm错误('session-title-llm: unknown config key "'+str(键)+'"')#拒绝
    for 键 in ('maxInputBytes','maxOutputTokens','timeoutMs'):#必填正整数
        if 键 not in 配置:#缺键
            raise 会话标题llm错误('session-title-llm: '+键+' must be a positive integer')#拒绝
        断言正整数(键,配置[键])#校验
    if 配置['timeoutMs']>最大定时器延迟毫秒:#超时过大
        raise 会话标题llm错误('session-title-llm: timeoutMs must not exceed '+str(最大定时器延迟毫秒))#拒绝
    有提供方='provider' in 配置#有提供方
    有模型='model' in 配置#有模型
    if 有提供方!=有模型:#必须成对
        raise 会话标题llm错误('session-title-llm: provider and model must be supplied together')#拒绝
    if 有提供方 and (not isinstance(配置['provider'],str) or len(配置['provider'])==0 or not isinstance(配置['model'],str) or len(配置['model'])==0):#空串
        raise 会话标题llm错误('session-title-llm: provider and model overrides must be non-empty strings')#拒绝
    return 深冻结(dict(配置))#冻结

def 解析路由(配置,请求):
    '显式成对覆盖，否则用 request/header 记下的路由'
    if 'provider' in 配置 and 'model' in 配置:#显式路由
        return {'provider':配置['provider'],'model':配置['model']}#覆盖
    if 'route' not in 请求 or 请求['route'] is None:#无路由
        raise 会话标题llm错误('session-title-llm: no logged request route is available; configure provider and model together')#拒绝
    return 请求['route']#记下的路由

def 终端结束(结束):
    '失败与中止抛出；停、工具、达到上限交给提供方解释'
    种类=结束.get('kind') if isinstance(结束,dict) else None#种类
    if 种类 in ('stop','tool-calls','max-tokens'):#提供方自行接受或拒绝
        return 结束#原样返回
    if 种类=='error' or 种类=='aborted':#运行失败或中止
        故障=结束.get('failure') if isinstance(结束,dict) else None#故障
        if not isinstance(故障,dict):#缺故障
            故障={}#空
        错误=会话标题llm错误(故障['message'] if 'message' in 故障 else '')#消息
        错误.code=故障['code'] if 'code' in 故障 else None#码
        raise 错误#抛出
    raise 会话标题llm错误('session-title-llm: unsupported finish reason "'+str(种类)+'"')#未知

def 登记会话标题llm提供方(上下文,配置,标识,自动模式,选消息):
    '兼容仍把选消息交给共享层的提供方：目标长度从配置里取出后，再走预备请求'
    原文=dict(配置) if isinstance(配置,dict) else 配置#拷贝以便取出长度目标
    目标词=None#非 CJK 目标
    目标字=None#CJK 目标
    if isinstance(原文,dict):#对象配置
        目标词=原文.pop('targetWords',None)#取出
        目标字=原文.pop('targetCjkCharacters',None)#取出
    已解析=解析会话标题llm配置(原文)#校验执行控件
    def 系统提示():
        '旧提供方仍用的语言感知提示'
        return '\n'.join([
            'Create a concise title for an AI coding-assistant session from the supplied human messages.',
            'Return only the title on one line, **in plain text of natural language**, with no quotes, prefix, explanation, Markdown, XML, or terminal control codes. No code is allowed.',
            'Use the language of the messages.',
            'Aim for about '+str(目标词)+' words in non-CJK languages or '+str(目标字)+' CJK characters.',
        ])#拼接
    def 生成(请求):
        '选消息、帧成输入，再解释文本结果'
        选中=选消息(请求['messages'])#提供方选定的消息
        帧='Generate the session title from this JSON array of human messages:\n'+紧凑json编码(选中)#帧
        响应=用llm生成会话标题(上下文,已解析,请求,标识,{
            'system':系统提示(),#系统提示
            'input':帧,#用户输入
            'messageSeqs':[项['seq'] for 项 in 选中],#来源序号
            'selectReasoningEffort':lambda 模型:None,#不改推理力度
        })#执行
        if 响应['finish']['kind']=='max-tokens':#到上限
            raise 会话标题llm错误('session-title-llm: title output reached maxOutputTokens')#拒绝
        if 响应['finish']['kind']=='tool-calls':#要工具
            raise 会话标题llm错误('session-title-llm: title model unexpectedly requested a tool')#拒绝
        for 块 in 响应['blocks']:#筛工具调用
            if 块.get('type')=='tool-call':#含工具
                raise 会话标题llm错误('session-title-llm: title output must contain text only')#拒绝
        文本=' '.join(块['text'] for 块 in 响应['blocks'] if 块.get('type')=='text')#文本块
        标题=归一化会话标题(文本,2**53-1)#归一
        if len(标题)==0:#空
            raise 会话标题llm错误('session-title-llm: title model produced no text')#拒绝
        return {'title':标题,'messageSeqs':[项['seq'] for 项 in 选中],'model':响应['model']}#结果
    上下文.sessionTitle.登记提供方({'id':标识,'automatic':自动模式,'generate':生成})#登记

def 用llm生成会话标题(上下文,配置,请求,标题提供方标识,预备):
    '执行提供方预备好的辅助标题请求，不解释标题正文'
    若已中止则抛出(请求['signal'])#已取消
    if len(预备['messageSeqs'])==0:#无来源序号
        raise 会话标题llm错误('session-title-llm: at least one source message is required')#拒绝
    输入字节=utf8字节数(预备['input'])#UTF-8 字节
    if 输入字节>配置['maxInputBytes']:#超长
        raise 会话标题llm错误('session-title-llm: input is '+str(输入字节)+' bytes, exceeding maxInputBytes '+str(配置['maxInputBytes']))#拒绝
    路由=解析路由(配置,请求)#路由
    消息=[创建用户消息({'content':[{'type':'text','text':预备['input']}],'source':{'kind':'dsh-session-title-llm'}})]#用户消息
    最大令牌=配置['maxOutputTokens']#输出上限
    def 选择控件(控件,模型信息):
        '把提供方选出的推理力度并进控件'
        力度=预备['selectReasoningEffort'](模型信息)#提供方选择
        结果=dict(控件)#拷贝
        if 力度 is not None:#有力度
            结果['reasoningEffort']=力度#写入
        return 结果#返回
    命令截止=截止(请求['signal'],配置['timeoutMs'],会话标题超时码)#截止
    调用=上下文.llm.准备调用({'provider':路由['provider'],'model':路由['model'],'maxTokens':最大令牌},命令截止.信号,选择控件)#预备调用
    选项=深冻结({**调用['config'],'messages':消息,'system':预备['system'],'sessionId':请求['session'].id,'purpose':'session-title','signal':命令截止.信号})#选项
    记录={'titleProvider':标题提供方标识,'messageSeqs':list(预备['messageSeqs']),'route':路由,'system':预备['system'],'messages':消息,'maxTokens':最大令牌}#日志
    if 'reasoningEffort' in 调用['config']:#本次调用带了力度
        记录['reasoningEffort']=调用['config']['reasoningEffort']#记下
    请求['session'].append('session/title-llm-request',记录)#日志
    若已中止则抛出(命令截止.信号)#再取消
    组装器=块组装器()#组装
    for 块 in 调用['stream'](选项):#流式
        若已中止则抛出(命令截止.信号)#取消
        组装器.推入(块)#喂入
    若已中止则抛出(命令截止.信号)#结束后取消
    return {'blocks':组装器.块列表(),'finish':终端结束(组装器.结束),'model':路由}#交给提供方解释

包名='@deepseek-ai/dsh-session-title-llm'
名称='session-title-llm'
__all__=['包名','名称','会话标题超时码','会话标题llm配置模式','解析会话标题llm配置','登记会话标题llm提供方','用llm生成会话标题','会话标题llm错误']
