"""浏览器面子智能体提示与打断请求校验，以及 Remote 面稳定失败码。"""
from ...附件.附件.错误 import 附件错误
from ...typert.协议 import 远程错误
from ...工具.超时 import 已中止
from .错误 import 子智能体错误

__all__=['校验控制请求','拒绝提示']

def 校验控制请求(方法,载荷):
    """比品牌字符串编解码更严的载荷检查。失败抛 gateway/bad-request。"""
    if not isinstance(载荷,dict):
        raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'expected object'}]})
    if 方法=='subagent.prompt':
        要有=('parentSessionId','childSessionId','mode','delivery')
    else:
        要有=('parentSessionId','childSessionId','mode')
    问题=[]
    for 键 in 要有:
        值=载荷[键] if 键 in 载荷 else None
        if 键=='parentSessionId' or 键=='childSessionId':
            if not isinstance(值,str) or len(值)==0:
                问题.append({'path':[键],'message':'required non-empty string'})
        elif 键=='mode':
            if 值!='continuable':
                问题.append({'path':['mode'],'message':'expected continuable'})
        elif 键=='delivery':
            if 值!='queue' and 值!='steer':
                问题.append({'path':['delivery'],'message':'expected queue or steer'})
    if len(问题)>0:
        raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':问题})

def 拒绝提示(错误,子会话标识,信号):
    """拒绝一次续跑提示，不暴露提供方细节。始终抛 远程错误。"""
    取消=已中止(信号) or (isinstance(错误,子智能体错误) and 错误.code=='CANCELLED')
    if 取消:
        raise 远程错误('gateway/cancelled','subagent prompt was cancelled',{},错误)
    if isinstance(错误,附件错误):
        raise 远程错误('subagent/attachment-invalid',str(错误),{'reason':错误.code},错误)
    if isinstance(错误,子智能体错误):
        码=错误.code
        if 码=='MODEL_DOES_NOT_SUPPORT_IMAGES':
            raise 远程错误('subagent/attachment-invalid',str(错误),{'reason':码},错误)
        if 码=='NOT_RESUMABLE':
            raise 远程错误('subagent/not-resumable','subagent cannot be resumed',{'childSessionId':子会话标识},错误)
        if 码=='UNAUTHORIZED':
            raise 远程错误('subagent/unauthorized','subagent does not belong to this parent',{'childSessionId':子会话标识},错误)
        if (码=='DRAINING' or 码=='ACTIVATION_CLOSING' or 码=='ACTIVATION_LIMIT_REACHED'
            or 码=='CONTINUATION_UNAVAILABLE' or 码=='PERSISTENCE_UNAVAILABLE'):
            raise 远程错误('subagent/delivery-unavailable','subagent follow-up is temporarily unavailable',{'childSessionId':子会话标识},错误)
    raise 远程错误('gateway/internal','subagent prompt failed',{},错误)
