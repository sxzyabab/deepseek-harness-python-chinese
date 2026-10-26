'测试和回环演示用的固定本地身份。不是认证边界'
from urllib.parse import parse_qsl,urlsplit,urlencode,urlunsplit
from ....基础设施.js特性 import PromiseEX as 期约
from .密钥 import 规范化身份

__all__=['模拟身份提供方']

class 模拟身份提供方:
    '按固定人设解析回调码'
    def __init__(自身,标识,人设):
        '标识不能空，至少要有一条人设'
        if 标识=='':
            raise ValueError('mock identity provider id must not be empty')
        if len(人设)==0:
            raise ValueError('mock identity provider requires at least one persona')
        自身.id=标识
        自身.人设=list(人设)
        自身.scopes=()

    def 授权网址(自身,请求):
        '重定向回中继回调，查询里带上选定的固定人设码'
        选定=请求['loginHint'] if 'loginHint' in 请求 and 请求['loginHint'] is not None else (自身.人设[0]['id'] if len(自身.人设)>0 else None)
        if 选定 is None:
            raise ValueError('mock identity provider has no selectable persona')
        部件=urlsplit(请求['redirectUri'])
        查询=dict(parse_qsl(部件.query,keep_blank_values=True))
        查询['code']=选定
        查询['state']=请求['state']
        return urlunsplit((部件.scheme,部件.netloc,部件.path,urlencode(查询),部件.fragment))

    def 交换(自身,请求):
        '把固定人设码解成与提供方无关的行动者'
        盒=期约()
        人设=None
        for 候选 in 自身.人设:
            if 候选['id']==请求['code']:
                人设=候选
                break
        if 人设 is None:
            盒.拒绝(ValueError('mock identity callback code is unknown'))
            return 盒
        租户=人设['tenantId'] if 'tenantId' in 人设 and 人设['tenantId'] is not None else 'mock'
        显示名=人设['displayName'] if 'displayName' in 人设 and 人设['displayName'] is not None else 人设['id']
        行动者={'providerId':自身.id,'subjectId':人设['id'],'tenantId':租户,'displayName':显示名}
        if 人设.get('avatarUrl') is not None:
            行动者['avatarUrl']=人设['avatarUrl']
        规范=规范化身份(行动者,'mock')
        if 规范 is None:
            盒.拒绝(ValueError('mock identity persona id must not be empty'))
            return 盒
        盒.解决(规范)
        return 盒
