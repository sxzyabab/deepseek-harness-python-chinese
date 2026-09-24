"""DeepSeek Files API 传输。"""
import time
from urllib.parse import quote
from requests import request as 发请求
from ..llm import 大模型错误,归属头
from .文件标识 import 深求文件标识
from .消息接口 import 消息接口根,消息文件测试通道

__all__=[
    '最小文件过期秒','最大文件过期秒','最大文件上传字节','最大存储文件数','最大存储文件字节',
    '深求文件错误','是否文件配额错误','深求文件客户端',
]

最小文件过期秒=3600
最大文件过期秒=2592000
最大文件上传字节=128*1024*1024
最大存储文件数=10000
最大存储文件字节=25*1024*1024*1024

class 深求文件错误(大模型错误):
    """Files API 操作失败，保留 HTTP 状态供恢复政策。"""
    def __init__(自身,消息,状态,详情):
        """记下可读失败、状态与分类详情。"""
        if 状态==401 or 状态==403:
            码='AUTH'
        elif 状态==429:
            码='RATE_LIMIT'
        elif 状态>=500:
            码='SERVER'
        else:
            码='FILES_API'
        super().__init__(消息,码,{'status':状态})
        自身.name='DeepSeekFilesError'
        自身.detail=详情

def 是否文件配额错误(错误):
    """上传失败是否报告存储或文件数配额。"""
    import re
    return isinstance(错误,深求文件错误) and re.search(r'(?:quota|storage|stored files|file count|too many files)',错误.detail,re.I) is not None

def 非法响应(操作):
    """畸形响应。"""
    return 大模型错误('DeepSeek Files API returned an invalid '+操作+' response.','INVALID_RESPONSE')

def 解析文件对象(值,操作):
    """校验提供方文件元数据。"""
    if not isinstance(值,dict):
        raise 非法响应(操作)
    创建=值.get('created_at')
    if isinstance(创建,str):
        创建于=int(time.mktime(time.strptime(创建[:19],'%Y-%m-%dT%H:%M:%S'))) if 'T' in 创建 else int(time.time())
    else:
        创建于=float('nan')
    if (not isinstance(值.get('id'),str) or 值['id']==''
        or 值.get('type')!='file'
        or not isinstance(值.get('mime_type'),str)
        or not isinstance(值.get('size_bytes'),int) or isinstance(值.get('size_bytes'),bool) or 值['size_bytes']<0
        or not isinstance(创建于,int) or 创建于<0
        or not isinstance(值.get('filename'),str) or 值['filename']==''):
        raise 非法响应(操作)
    return {'id':深求文件标识(值['id']),'bytes':值['size_bytes'],'createdAt':创建于,'filename':值['filename']}

def 提供方详情(值):
    """解析错误信封。"""
    if not isinstance(值,dict):
        return {'detail':''}
    错误=值.get('error')
    if not isinstance(错误,dict):
        return {'detail':''}
    消息=错误['message'] if isinstance(错误.get('message'),str) else None
    段=[项 for 项 in (错误.get('code'),错误.get('type'),错误.get('message')) if isinstance(项,str)]
    结果={'detail':' '.join(段)}
    if 消息 is not None:
        结果['message']=消息
    return 结果

class 深求文件客户端:
    """直接 Files 客户端，拒绝重定向以免凭证离开源。"""
    def __init__(自身,选项):
        """记下端点、密钥快照与可选测试传输。"""
        自身.密钥=选项['apiKey']
        自身.账号凭证=选项.get('accountCredential') is True
        自身.发=选项['fetch'] if 'fetch' in 选项 else 发请求
        自身.基址=消息接口根(选项['baseURL'])

    def 请求(自身,路径,方法,数据=None,文件=None,信号=None):
        """发请求；已中止原样抛出。"""
        from ...工具.超时 import 已中止
        头=dict(归属头())
        头['x-dsh-auth-token' if 自身.账号凭证 else 'x-api-key']=自身.密钥
        头['anthropic-version']='2023-06-01'
        头['anthropic-beta']=消息文件测试通道
        try:
            响应=自身.发(方法,自身.基址+路径,headers=头,data=数据,files=文件,allow_redirects=False,timeout=None)
        except Exception as 错误:
            if 已中止(信号):
                raise 错误
            raise 大模型错误('DeepSeek Files API request failed','TRANSPORT',{'cause':错误})
        if 响应.status_code>=200 and 响应.status_code<300:
            return 响应
        解析=None
        try:
            解析=响应.json()
        except Exception:
            pass
        提取=提供方详情(解析)
        raise 深求文件错误(提取.get('message') or 'DeepSeek Files API error (HTTP '+str(响应.status_code)+')',响应.status_code,提取['detail'])

    def 上传(自身,输入):
        """上传一张带显式过期的图。"""
        数据=输入['data']
        if len(数据)>最大文件上传字节:
            raise 大模型错误('DeepSeek Files API upload exceeds 128 MiB.','INVALID_REQUEST')
        过期=输入['expiresAfterSeconds']
        if (not isinstance(过期,int)) or isinstance(过期,bool) or 过期<最小文件过期秒 or 过期>最大文件过期秒:
            raise 大模型错误('DeepSeek file expiry must be between 3600 and 2592000 seconds.','INVALID_REQUEST')
        表={'expires_after[anchor]':'created_at','expires_after[seconds]':str(过期)}
        文件={'file':(输入['filename'],bytes(数据),输入['mediaType'])}
        响应=自身.请求('/files','POST',数据=表,文件=文件,信号=输入.get('signal'))
        try:
            体=响应.json()
        except Exception as 错误:
            raise 大模型错误('DeepSeek Files API returned invalid JSON for upload (HTTP '+str(响应.status_code)+').','INVALID_RESPONSE',{'status':响应.status_code,'cause':错误})
        文件对象=解析文件对象(体,'upload')
        文件对象['expiresAt']=文件对象['createdAt']+过期
        return 文件对象

    def 列出(自身,选项=None):
        """列一页提供方排序的文件。"""
        if 选项 is None:
            选项={}
        查询=[]
        if 选项.get('after') is not None:
            查询.append('after_id='+quote(str(选项['after'])))
        if 选项.get('limit') is not None:
            查询.append('limit='+str(选项['limit']))
        路径='/files'+('?'+'&'.join(查询) if 查询 else '')
        响应=自身.请求(路径,'GET',信号=选项.get('signal'))
        值=响应.json()
        if not isinstance(值,dict):
            raise 非法响应('list')
        首=值.get('first_id')
        尾=值.get('last_id')
        if (not isinstance(值.get('data'),list) or not isinstance(值.get('has_more'),bool)
            or (首 is not None and not isinstance(首,str))
            or (尾 is not None and not isinstance(尾,str))):
            raise 非法响应('list')
        页={'data':[解析文件对象(项,'list') for 项 in 值['data']],'hasMore':值['has_more']}
        if isinstance(首,str):
            页['firstId']=深求文件标识(首)
        if isinstance(尾,str):
            页['lastId']=深求文件标识(尾)
        return 页

    def 取回(自身,文件号,信号=None):
        """取回一个文件对象。"""
        响应=自身.请求('/files/'+quote(文件号,safe=''),'GET',信号=信号)
        return 解析文件对象(响应.json(),'retrieve')

    def 删除(自身,文件号,信号=None):
        """删除一个提供方文件。"""
        响应=自身.请求('/files/'+quote(文件号,safe=''),'DELETE',信号=信号)
        值=响应.json()
        if not isinstance(值,dict) or 值.get('id')!=文件号 or 值.get('type')!='file_deleted':
            raise 非法响应('delete')
