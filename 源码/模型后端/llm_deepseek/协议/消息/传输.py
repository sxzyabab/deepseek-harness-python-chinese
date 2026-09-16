"""把 HTTP 与带内消息错误归一成提供方中性失败。"""
import re,time#Retry-After 与时钟
from email.utils import parsedate_to_datetime as 解析日期时间#HTTP 日期
from ....llm import (
    是否上下文窗口溢出,#溢出
    是否配额耗尽,#配额
    大模型错误,#错误
    提供方请求标识,#请求 id
)#llm 词表

__all__=('提供方错误细节','提供方错误')#仅中文公开名

纯秒形=re.compile(r'^\d+(?:\.\d+)?$')#Retry-After 秒

def 提供方错误细节(原始):
    """只读 Files 恢复用到的提供方错误字段。"""
    if not isinstance(原始,dict):#非对象
        return ''#空
    错误=原始.get('error')#错误
    if not isinstance(错误,dict):#非对象
        return ''#空
    return ' '.join(段 for 段 in (错误.get('code'),错误.get('type'),错误.get('message')) if isinstance(段,str))#拼接

def 提供方错误(原始,状态,头=None):
    """分类提供方错误，不信任任意响应字段。"""
    信封=原始 if isinstance(原始,dict) else {}#信封
    错误=信封.get('error') if isinstance(信封.get('error'),dict) else {}#错误
    消息=错误['message'] if isinstance(错误.get('message'),str) else 'DeepSeek Messages request failed ('+str(状态 if 状态 is not None else 'stream error')+')'#消息
    类型=错误['type'] if isinstance(错误.get('type'),str) else ''#类型
    细节=类型+' '+(错误['code'] if isinstance(错误.get('code'),str) else '')+' '+消息#细节
    if 状态==401 or 状态==403 or 类型 in ('authentication_error','permission_error'):#认证
        码='AUTH'#认证
    elif 是否配额耗尽(细节) or 状态==402:#配额
        码='QUOTA'#配额
    elif 状态==429 or 类型=='rate_limit_error':#限流
        码='RATE_LIMIT'#限流
    elif 是否上下文窗口溢出(细节):#溢出
        码='CONTEXT_WINDOW_EXCEEDED'#溢出
    elif 状态==400 or 状态==413 or 类型=='invalid_request_error':#非法
        码='INVALID_REQUEST'#非法
    elif (状态 is not None and 状态>=500) or 类型 in ('api_error','overloaded_error'):#服务端
        码='SERVER'#服务端
    else:#其余
        码='SERVER' if 状态 is None else 'HTTP_'+str(状态)#流内或 HTTP
    等待原文=None#Retry-After
    标识原文=None#请求 id
    if 头 is not None:#有头
        等待原文=头.getheader('retry-after')#等待
        标识原文=头.getheader('request-id') or 头.getheader('x-request-id') or 头.getheader('x-deepseek-request-id')#id
    延迟=None#毫秒
    if 等待原文 is not None:#有等待
        if 纯秒形.match(str(等待原文)):#秒
            候选=float(等待原文)*1000#毫秒
            if 候选>0:#正
                延迟=候选#记下
        else:#日期
            try:#解析
                时刻=解析日期时间(等待原文)#日期
                候选=int(时刻.timestamp()*1000)-int(time.time()*1000)#差值
                if 候选>0:#正
                    延迟=候选#记下
            except (TypeError,ValueError,OverflowError):#无法解析
                延迟=None#无
    选项={}#事实
    if 状态 is not None:#有状态
        选项['status']=状态#状态
    if 标识原文:#有 id
        选项['requestId']=提供方请求标识(标识原文)#品牌
    if 延迟 is not None:#有等待
        选项['providerRetryAfterMs']=延迟#等待
    return 大模型错误(消息,码,选项)#错误
