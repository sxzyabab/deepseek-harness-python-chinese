import json,re
from urllib.parse import urlparse
from requests import request as 发请求
from ...工具.超时 import 已中止

__all__=['平台认证错误','平台来源','浏览器网址','平台头','初始化形态','交换形态','请求平台','请求账号','登出账号','登录来源']

保留头=frozenset(['authorization','x-dsh-auth-token','host','content-length','transfer-encoding','connection','content-type'])
回环主机=frozenset(['localhost','127.0.0.1','::1'])
登录来源形态=re.compile(r'^http://(?:localhost|127\.0\.0\.1|\[::1\]):([0-9]+)/?\Z',re.ASCII|re.IGNORECASE)
正文上限=65536

class 平台认证错误(Exception):
    """稳定码，不携带响应体或授权 URL。"""
    def __init__(自身,码):
        """码为 network/protocol/expired/storage。"""
        super().__init__('account: '+码)
        自身.code=码

def 平台来源(值,允许回环http):
    """HTTPS 平台端点，或显式开启的回环 HTTP。"""
    解析=urlparse(值)
    主机=解析.hostname or ''
    回环=主机 in 回环主机
    if (解析.username or 解析.password or 解析.path not in ('','/')
            or 解析.query or 解析.fragment
            or not (解析.scheme=='https' or (允许回环http and 回环 and 解析.scheme=='http'))):
        raise ValueError('account: platformOrigin 必须是 HTTPS 来源或显式开启的回环 HTTP 来源')
    return 解析.scheme+'://'+解析.netloc

def 浏览器网址(值,来源,路径,改写来源=False):
    """校验平台拥有的浏览器目的地。"""
    try:
        解析=urlparse(值)
    except ValueError:
        print('[deepseek-account] 浏览器网址已拒绝',{'path':路径,'reason':'invalid-url'})
        raise 平台认证错误('protocol')
    允许来源=解析.scheme+'://'+解析.netloc==来源 or (改写来源 and 解析.scheme=='https')
    if not 允许来源 or 解析.path!=路径 or 解析.username or 解析.password or 解析.fragment:
        print('[deepseek-account] 浏览器网址已拒绝',{
            'path':路径,
            'originMismatch':not 允许来源,
            'pathMismatch':解析.path!=路径,
            'hasCredentials':bool(解析.username or 解析.password),
            'hasFragment':bool(解析.fragment),
        })
        raise 平台认证错误('protocol')
    if 改写来源:
        return 来源+解析.path+(('?'+解析.query) if 解析.query else '')
    return 值

def 平台头(值表):
    """校验仅发往平台来源的部署头。"""
    名集=set()
    结果={}
    for 名,值 in 值表.items():
        键=名.lower()
        if 键 in 保留头 or 键 in 名集:
            raise ValueError('account: requestHeaders 含保留或重复头')
        if '\r' in 值 or '\n' in 值 or '\r' in 名 or '\n' in 名:
            raise ValueError('account: requestHeaders 含非法头')
        名集.add(键)
        结果[键]=值
    return 结果

def 初始化形态(值):
    """成功的初始化载荷。"""
    if not isinstance(值,dict):
        return None
    网址=值.get('authorize_url')
    标识=值.get('authorize_id')
    过期=值.get('expires_in')
    if not isinstance(网址,str) or 网址=='':
        return None
    if not isinstance(标识,str) or 标识=='':
        return None
    if isinstance(过期,bool) or not isinstance(过期,(int,float)) or 过期<=0:
        return None
    return {'authorize_url':网址,'authorize_id':标识,'expires_in':过期}

def 交换形态(值):
    """成功的换码载荷。"""
    if not isinstance(值,dict):
        return None
    令牌=值.get('token')
    网址=值.get('authorized_url')
    if not isinstance(令牌,str) or re.search(r'[^\x21-\x7e]',令牌) is not None:
        return None
    if not isinstance(网址,str) or 网址=='':
        return None
    结果={'token':令牌,'authorized_url':网址}
    if 'user' in 值:
        结果['user']=值['user']
    return 结果

def 请求平台(来源,方法,体,信号,头):
    """读有界平台响应。"""
    return 平台请求(来源+'/auth-api/v0/dsh/'+方法,{
        'method':'POST',
        'headers':{**头,'content-type':'application/json'},
        'body':json.dumps(体,ensure_ascii=False,separators=(',',':'),allow_nan=False),
    },信号)

def 请求账号(来源,路径,令牌,信号,头):
    """用授予读固定账号端点。"""
    return 平台请求(来源+路径,{
        'method':'GET',
        'headers':{**头,'x-dsh-auth-token':令牌},
    },信号)

def 登出账号(来源,令牌,信号,头):
    """结束平台会话。"""
    平台请求(来源+'/auth-api/v0/users/logout',{
        'method':'POST',
        'headers':{**头,'x-dsh-auth-token':令牌},
    },信号)

def 平台请求(网址,发起,信号):
    """POST/GET 且不跟随重定向，正文上限 65536。"""
    路径=urlparse(网址).path
    print('[deepseek-account] 请求',{'path':路径,'method':发起['method']})
    if 已中止(信号):
        print('[deepseek-account] 请求失败',{'path':路径,'errorCode':'network','aborted':True})
        raise 平台认证错误('network')
    try:
        响应=发请求(
            发起['method'],
            网址,
            headers=发起['headers'],
            data=发起['body'] if 'body' in 发起 else None,
            allow_redirects=False,
            stream=True,
            timeout=120,
        )
    except Exception:
        print('[deepseek-account] 请求失败',{'path':路径,'errorCode':'network','aborted':已中止(信号)})
        raise 平台认证错误('network')
    print('[deepseek-account] 响应',{'path':路径,'status':响应.status_code})
    if 响应.status_code<200 or 响应.status_code>=300:
        响应.close()
        raise 平台认证错误('network')
    块列表=[]
    尺寸=0
    阶段='read-body'
    try:
        for 块 in 响应.iter_content(4096):
            if 已中止(信号):
                raise 平台认证错误('network')
            尺寸+=len(块)
            if 尺寸>正文上限:
                阶段='body-limit'
                raise 平台认证错误('protocol')
            块列表.append(块)
        阶段='parse-json'
        载荷=json.loads(b''.join(块列表).decode('utf-8'))
        if isinstance(载荷,dict) and isinstance(载荷.get('code'),int) and not isinstance(载荷.get('code'),bool):
            业务=载荷['data'] if isinstance(载荷.get('data'),dict) else None
            业务码=业务.get('biz_code') if 业务 is not None else None
            print('[deepseek-account] 响应码',{'path':路径,'code':载荷['code'],'bizCode':业务码})
        阶段='envelope'
        if not isinstance(载荷,dict) or 载荷.get('code')!=0 or not isinstance(载荷.get('data'),dict):
            print('[deepseek-account] 信封已拒绝',{'path':路径})
            raise 平台认证错误('protocol')
        阶段='business-code'
        if 载荷['data'].get('biz_code')!=0:
            raise 平台认证错误('protocol')
        return 载荷['data'].get('biz_data')
    except 平台认证错误:
        print('[deepseek-account] 响应已拒绝',{'path':路径,'stage':阶段,'errorCode':'protocol'})
        raise
    except Exception:
        print('[deepseek-account] 响应已拒绝',{'path':路径,'stage':阶段,'errorCode':'protocol'})
        raise 平台认证错误('protocol')
    finally:
        响应.close()

def 登录来源(值):
    """本机或 SSH 转发的回环 HTTP 来源，端口必须显式。"""
    try:
        解析=urlparse(值)
    except ValueError:
        raise 平台认证错误('protocol')
    匹配=登录来源形态.search(值)
    端口=匹配.group(1) if 匹配 is not None else None
    主机=解析.hostname or ''
    if (端口 is None or int(端口)==0 or 解析.scheme!='http'
            or 主机 not in 回环主机
            or 解析.username or 解析.password
            or 解析.path not in ('','/') or 解析.query or 解析.fragment):
        raise 平台认证错误('protocol')
    return 解析.scheme+'://'+主机+':'+str(int(端口))
