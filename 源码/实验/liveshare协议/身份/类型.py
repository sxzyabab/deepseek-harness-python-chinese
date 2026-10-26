'跨提供方标识一个人的提供方、租户和主体'
from typing import NotRequired,TypedDict

__all__=['身份三元组','身份行动者','身份授权请求','身份交换请求']

class 身份三元组(TypedDict):
    '提供方、租户和主体'
    providerId:str
    tenantId:str
    subjectId:str

class 身份行动者(身份三元组):
    '中继解析出的、与提供方无关的查看者身份'
    displayName:str
    avatarUrl:NotRequired[str]

class 身份授权请求(TypedDict):
    '构造提供方授权重定向需要的请求事实'
    state:str
    redirectUri:str
    scopes:list
    loginHint:NotRequired[str]

class 身份交换请求(TypedDict):
    '用提供方回调码交换身份需要的请求事实'
    code:str
    redirectUri:str
