'远程失败码对应的文件口吻说明'
from .文案 import 中文,套入

__all__=['失败行','空失败办法']

def 失败码(失败):
    'RemoteFailure 的 code。对象或 dict 都行'
    if isinstance(失败,dict):
        return 失败['code'] if 'code' in 失败 else None
    return getattr(失败,'code',None)

def 失败消息(失败):
    '载体上的 message'
    if isinstance(失败,dict):
        return 失败['message'] if 'message' in 失败 else ''
    消息=getattr(失败,'message','')
    return '' if 消息 is None else 消息

def 失败细节(失败):
    '载体上的 details'
    if isinstance(失败,dict):
        细节=失败['details'] if 'details' in 失败 else {}
    else:
        细节=getattr(失败,'details',{})
    return 细节 if isinstance(细节,dict) else {}

def 失败行(失败):
    '用文件口吻说明出错原因。没点名的码带上载体消息'
    码=失败码(失败)
    if 码=='workspace-file/not-found':
        return 中文['error.notFound']
    if 码=='workspace-file/too-large':
        字节=失败细节(失败)['limit'] if 'limit' in 失败细节(失败) else 0
        if 字节>=1024*1024:
            限度=str(round(字节/(1024*1024)))+' MB'
        elif 字节>=1024:
            限度=str(round(字节/1024))+' KB'
        else:
            限度=str(字节)+' B'
        return 套入(中文['error.tooLarge'],{'limit':限度})
    if 码=='workspace-file/not-text':
        return 中文['error.notText']
    if 码=='workspace-file/not-regular-file':
        return 中文['error.notRegularFile']
    return 套入(中文['error.unavailable'],{'message':失败消息(失败)})

def 空失败办法(失败):
    '空预览旁边给什么动作。open 交给宿主打开，none 没有动作，其余重试'
    码=失败码(失败)
    if 码=='workspace-file/not-text' or 码=='workspace-file/too-large':
        return 'open'
    if 码=='workspace-file/not-found' or 码=='workspace-file/not-regular-file':
        return 'none'
    return 'retry'
