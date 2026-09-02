"""模型会话标题共享策略（对齐上游 session-title-llm）。"""
import json#消息 JSON 帧
from ...依赖.schemastery import 字典字段,数字字段,字符串字段#配置字段
from ...模型后端.llm import 创建用户消息,深冻结#LLM 辅助
from ...工具.超时 import 截止#截止
from ..会话标题.归一 import 归一化会话标题#标题归一

会话标题超时码='SESSION_TITLE_TIMEOUT'#超时原因码
最大定时器延迟毫秒=2147483647#对齐 MAX_TIMER_DELAY_MS
配置字段={
    'targetWords':数字字段(默认值=None),#非 CJK 目标词数（必填由加载器校验）
    'targetCjkCharacters':数字字段(默认值=None),#CJK 目标字符
    'maxInputBytes':数字字段(默认值=None),#输入字节上限
    'maxOutputTokens':数字字段(默认值=None),#输出 token 上限
    'timeoutMs':数字字段(默认值=None),#超时
    'provider':字符串字段(),#可选路由
    'model':字符串字段(),#可选模型
}#字段表
会话标题llm配置模式=字典字段(配置字段)#配置模式

def 解析会话标题llm配置(配置):#解析配置
    """校验并冻结模型标题策略。"""
    if 配置 is None or not isinstance(配置,dict):#非法
        raise Exception('session-title-llm: configuration is required')#拒绝
    for 键 in ('targetWords','targetCjkCharacters','maxInputBytes','maxOutputTokens','timeoutMs'):#必填正整数
        值=配置.get(键)#读
        if not isinstance(值,int) or 值<=0:#非法
            raise Exception('session-title-llm: '+键+' must be a positive integer')#拒绝
    if 配置['timeoutMs']>最大定时器延迟毫秒:#超时过大
        raise Exception('session-title-llm: timeoutMs must not exceed '+str(最大定时器延迟毫秒))#拒绝
    有提供方='provider' in 配置 and 配置['provider'] is not None#有提供方
    有模型='model' in 配置 and 配置['model'] is not None#有模型
    if 有提供方!=有模型:#必须成对
        raise Exception('session-title-llm: provider and model must be supplied together')#拒绝
    return 深冻结(dict(配置))#冻结

def _系统提示(配置):#系统提示
    """语言感知系统提示。"""
    return '\n'.join([
        'Create a concise title for an AI coding-assistant session from the supplied human messages.',
        'Return only the title on one line, in plain text of natural language, with no quotes, prefix, explanation, Markdown, XML, or terminal control codes.',
        'Use the language of the messages.',
        'Aim for about '+str(配置['targetWords'])+' words in non-CJK languages or '+str(配置['targetCjkCharacters'])+' CJK characters.',
    ])#拼接

def _帧消息(消息们):#JSON 帧
    """把消息帧成 JSON。"""
    return 'Generate the session title from this JSON array of human messages:\n'+json.dumps(消息们,ensure_ascii=False)#帧

def 登记会话标题llm提供方(上下文,配置,标识,自动模式,选消息):#登记提供方
    """通过共享策略登记一个模型标题提供方。"""
    已解析=解析会话标题llm配置(配置)#解析
    def 生成(请求):#提供方 generate
        """调用 LLM 生成标题。"""
        return 用llm生成会话标题(上下文,已解析,请求,选消息(请求['messages']),标识)#生成
    上下文.sessionTitle.register({'id':标识,'automatic':自动模式,'generate':生成})#登记

def 用llm生成会话标题(上下文,配置,请求,选中消息,标题提供方标识):#LLM 生成
    """共享辅助 LLM 调用。"""
    信号=请求['signal']#取消信号
    if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已取消
        raise Exception('aborted')#取消
    if len(选中消息)==0:#无消息
        raise Exception('session-title-llm: at least one source message is required')#拒绝
    帧=_帧消息(选中消息)#帧
    if len(帧.encode('utf-8'))>配置['maxInputBytes']:#超长
        raise Exception('session-title-llm: input exceeds maxInputBytes')#拒绝
    路由=请求.get('route')#路由
    if 配置.get('provider') is not None:#显式路由
        路由={'provider':配置['provider'],'model':配置['model']}#覆盖
    elif 路由 is None:#无路由
        raise Exception('session-title-llm: no logged request route is available; configure provider and model together')#拒绝
    系统=_系统提示(配置)#系统
    消息=[创建用户消息({'content':[{'type':'text','text':帧}],'source':{'kind':'plugin','plugin':'dsh-session-title-llm'}})]#用户消息
    命令截止=截止(信号,配置['timeoutMs'],会话标题超时码)#截止
    选项=深冻结({'provider':路由['provider'],'model':路由['model'],'messages':消息,'system':系统,'maxTokens':配置['maxOutputTokens'],'sessionId':请求['session'].id,'purpose':'session-title','signal':命令截止.信号})#选项
    请求['session'].append('session/title-llm-request',{'titleProvider':标题提供方标识,'messageSeqs':[项['seq'] for 项 in 选中消息],'route':路由,'system':系统,'messages':消息,'maxTokens':配置['maxOutputTokens']})#日志
    文本块=[]#累积文本
    for 块 in 上下文.llm.stream(选项):#流式
        if 块.get('type')=='text-delta':#文本增量
            文本块.append(块.get('text',''))#追加
    标题=归一化会话标题(' '.join(文本块),2**31-1)#归一
    if len(标题)==0:#空
        raise Exception('session-title-llm: title model produced no text')#拒绝
    return {'title':标题,'messageSeqs':[项['seq'] for 项 in 选中消息],'model':路由}#结果

名称='session-title-llm'#库插件名（非 Cordis 根）
__all__=['会话标题超时码','会话标题llm配置模式','解析会话标题llm配置','登记会话标题llm提供方','用llm生成会话标题','名称']#公开面
