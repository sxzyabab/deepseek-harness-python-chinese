import re
from ...工具.超时 import 超时原因

__all__=['分类下载失败','语音下载错误']

码表=(
    ('dns',re.compile(r'^(ENOTFOUND|EAI_AGAIN)$')),
    ('timeout',re.compile(r'^(ETIMEDOUT|ERR_SOCKET_CONNECTION_TIMEOUT|UND_ERR_(CONNECT|HEADERS|BODY)_TIMEOUT)$')),
    ('certificate',re.compile(r'^(CERT_[A-Z_]+|ERR_TLS_CERT_ALTNAME_INVALID|DEPTH_ZERO_SELF_SIGNED_CERT|SELF_SIGNED_CERT_IN_CHAIN|UNABLE_TO_VERIFY_LEAF_SIGNATURE|UNABLE_TO_GET_ISSUER_CERT_LOCALLY)$')),
    ('storage',re.compile(r'^(ENOSPC|EDQUOT|EACCES|EPERM|EROFS)$')),
    ('network',re.compile(r'^(ECONNREFUSED|ECONNRESET|ENETUNREACH|EHOSTUNREACH|EPIPE|UND_ERR_SOCKET)$')),
)

def 分类下载失败(失败):
    """检查网络与文件系统原因，不公开其消息。"""
    待办=[失败]
    已访=set()
    原因='unknown'
    while 待办:
        错误=待办.pop(0)
        if not isinstance(错误,Exception) or 错误 in 已访:
            continue
        已访.add(错误)
        if isinstance(错误,超时原因) or getattr(错误,'name',None)=='TimeoutError':
            return {'reason':'timeout'}
        码=getattr(错误,'code',None)
        if isinstance(码,str):
            for 种,模式 in 码表:
                if 模式.match(码):
                    return {'reason':种,'code':码}
        if isinstance(错误,TypeError) and str(错误)=='fetch failed':
            原因='network'
        因=getattr(错误,'__cause__',None)
        if 因 is not None:
            待办.append(因)
        if isinstance(错误,ExceptionGroup):
            待办.extend(错误.exceptions)
    return {'reason':原因}

class 语音下载错误(Exception):
    """公开细节不含原始原因、凭据、签名 URL 与本地路径。"""
    def __init__(自身,下载,原因=None):
        """记下结构化下载失败。"""
        码段=' ('+下载['code']+')' if 下载.get('code') else ''
        状态=下载.get('status')
        状态段='' if 状态 is None else ' (HTTP '+str(状态)+')'
        super().__init__('Unable to prepare '+下载['resource']+' from '+下载['source']+': '+下载['reason']+码段+状态段)
        自身.download=下载
        if 原因 is not None:
            自身.__cause__=原因
