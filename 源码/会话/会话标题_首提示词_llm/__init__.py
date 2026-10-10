'首提示词模型标题提供方'
import re#整行强调包装
from ...依赖.schemastery import 字典字段,数字字段#本提供方的长度目标
from ...基础设施.通用工具 import 紧凑json编码#消息帧
from ...模型后端.llm import 深冻结#冻结策略
from ..会话标题.归一 import 归一化会话标题#标题归一
from ..会话标题_llm import 解析会话标题llm配置,用llm生成会话标题,配置字段#共享执行
from ..会话标题_llm.异常 import 会话标题llm错误#模型标题失败

包名='@deepseek-ai/dsh-session-title-first-prompt-llm'
名称='session-title-first-prompt-llm'
依赖=['sessionTitle','llm','sessions']
配置=字典字段(字典结构={
    'targetWords':数字字段(),#非 CJK 目标词数
    'targetCjkCharacters':数字字段(),#CJK 目标字符
    **配置字段,#共享执行控件
})
强调包装=re.compile(r'^(?P<marker>\*{1,3})(?P<inner>\S(?:.*\S)?)\k<marker>$')#整行星号包装

__all__=['包名','名称','依赖','应用','默认','配置']

def 断言目标(名,值):
    '校验一项正整数标题长度目标'
    if isinstance(值,bool) or not isinstance(值,int) or 值<=0:#非法
        raise 会话标题llm错误('session-title-first-prompt-llm: '+名+' must be a positive integer')#拒绝
    return 值#原值

def 解析配置(配置值):
    '校验共享执行控件和本提供方的长度目标'
    if not isinstance(配置值,dict):#非法
        raise 会话标题llm错误('session-title-llm: configuration is required')#拒绝
    执行=dict(配置值)#拷贝
    if 'targetWords' not in 执行 or 'targetCjkCharacters' not in 执行:#缺目标
        raise 会话标题llm错误('session-title-first-prompt-llm: targetWords must be a positive integer')#拒绝
    目标词=执行.pop('targetWords')#取出
    目标字=执行.pop('targetCjkCharacters')#取出
    已解析=解析会话标题llm配置(执行)#共享控件
    return 深冻结({**dict(已解析),'targetWords':断言目标('targetWords',目标词),'targetCjkCharacters':断言目标('targetCjkCharacters',目标字)})#冻结

def 选择推理力度(模型):
    '选用该路由支持的最低推理力度'
    if not isinstance(模型,dict):#无模型信息
        return None#不改
    推理=模型.get('reasoning')#可选推理
    if not isinstance(推理,dict):#没有推理
        return None#不改
    力度=推理.get('efforts')#力度列表
    if not isinstance(力度,list) or len(力度)==0 or not isinstance(力度[0],dict):#没有首档
        return None#不改
    return 力度[0].get('id')#最低档

def 系统提示(配置):
    '从一条消息推导标题的语言感知系统指令'
    return '\n'.join([
        'Create a concise title for an AI coding-assistant session from the supplied human messages.',
        'Return only the title on one line, **in plain text of natural language**, with no quotes, prefix, explanation, Markdown, XML, or terminal control codes. No code is allowed.',
        'Use the language of the messages.',
        'Aim for about '+str(配置['targetWords'])+' words in non-CJK languages or '+str(配置['targetCjkCharacters'])+' CJK characters.',
        'If the messages give little to name, still return a short best-effort title, such as Greeting, instead of explaining.',
    ])#拼接

def 帧消息(消息列表):
    '把选定消息帧成 JSON，避免用户文本打断结构'
    return 'Generate the session title from this JSON array of human messages:\n'+紧凑json编码(消息列表)#帧

def 从输出取标题(文本):
    '取第一条非空行，并去掉包住整行的星号强调'
    行=''#默认空
    for 段 in re.split(r'\r?\n',文本):#逐行
        段=段.strip()#去空白
        if len(段)>0:#第一条非空
            行=段#采用
            break#停止
    匹配=强调包装.match(行)#整行包装
    if 匹配 is None:#不是整行强调
        return 行#原行
    标记=匹配.group('marker')#星号
    内部=匹配.group('inner')#内部
    if 标记 is None or 内部 is None or 标记 in 内部:#内部仍含标记
        return 行#保留原行
    return 内部#去掉一对标记

def 从响应取标题(响应):
    '拒绝工具调用和达到上限，并从文本块取出非空标题'
    种类=响应['finish']['kind']#结束种类
    if 种类=='tool-calls':#要工具
        raise 会话标题llm错误('session-title-llm: title output must contain text only')#拒绝
    if 种类=='max-tokens':#到上限
        raise 会话标题llm错误('session-title-llm: title output reached maxOutputTokens')#拒绝
    if 种类!='stop':#未知结束
        raise 会话标题llm错误('session-title-llm: unsupported finish reason "'+str(种类)+'"')#拒绝
    for 块 in 响应['blocks']:#筛工具调用
        if 块.get('type')=='tool-call':#含工具
            raise 会话标题llm错误('session-title-llm: title output must contain text only')#拒绝
    文本=' '.join(块['text'] for 块 in 响应['blocks'] if 块.get('type')=='text')#文本块
    标题=归一化会话标题(从输出取标题(文本),9007199254740991)#归一
    if len(标题)==0:#空
        raise 会话标题llm错误('session-title-llm: title model produced no text')#拒绝
    return 标题#标题

def 应用(上下文,配置值):
    '登记 first-prompt 自动模式提供方'
    已解析=解析配置(配置值)#校验
    def 生成(请求):
        '只用第一条人类消息生成标题'
        if len(请求['messages'])==0:#没有消息
            raise 会话标题llm错误('first-prompt title provider requires one human message')#拒绝
        首条=请求['messages'][0]#第一条
        响应=用llm生成会话标题(上下文,已解析,请求,名称,{
            'system':系统提示(已解析),#系统提示
            'input':帧消息([首条]),#只帧第一条
            'messageSeqs':[首条['seq']],#来源序号
            'selectReasoningEffort':选择推理力度,#最低力度
        })#执行
        return {'title':从响应取标题(响应),'messageSeqs':[首条['seq']],'model':响应['model']}#结果
    上下文.sessionTitle.登记提供方({'id':名称,'automatic':'first-prompt','generate':生成})#登记

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
