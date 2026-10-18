import re
from urllib.parse import urlsplit,urlunsplit

__all__=['最大地址长度','解析浏览器地址']

最大地址长度=16*1024
显式方案=re.compile(r'^[A-Za-z][A-Za-z\d+.-]*:(?!\d+(?:[/?#]|$))')


def 解析浏览器地址(输入,应用源=None):
    '把地址栏的值收进 HTTP 和 HTTPS。成功带 target，拒绝带 reason'
    修剪=输入.strip()
    if 修剪=='':
        return {'ok':False,'reason':'empty'}
    if len(修剪)>最大地址长度:
        return {'ok':False,'reason':'invalid'}
    显式=显式方案.search(修剪) is not None
    候选=修剪 if 显式 else 'https://'+修剪
    try:
        拆=urlsplit(候选)
    except ValueError:
        return {'ok':False,'reason':'invalid'}
    if 拆.hostname is None or 拆.hostname=='':
        return {'ok':False,'reason':'invalid'}
    用户名=拆.username if 拆.username is not None else ''
    密码=拆.password if 拆.password is not None else ''
    if 用户名!='' or 密码!='':
        return {'ok':False,'reason':'credentials'}
    协议=拆.scheme.lower()+':'
    if 协议!='https:' and 协议!='http:':
        return {'ok':False,'reason':'protocol'}
    if 应用源 is not None and 应用源!='null':
        try:
            应用=urlsplit(应用源)
            if 应用.scheme!='' and 应用.netloc!='' and 拆.scheme+'://'+拆.netloc==应用.scheme+'://'+应用.netloc:
                return {'ok':False,'reason':'application-origin'}
        except ValueError:
            pass
    路径=拆.path if 拆.path!='' else '/'
    完整=urlunsplit((拆.scheme,拆.netloc,路径,拆.query,拆.fragment))
    return {
        'ok':True,
        'target':{
            'kind':'https' if 协议=='https:' else 'http',
            'url':完整,
            'title':拆.hostname,
        },
    }
