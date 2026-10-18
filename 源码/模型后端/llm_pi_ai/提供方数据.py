'已安装提供方的配置面默认值。不执行认证'
from .提供方数据_生成 import 提供方数据

__all__=('提供方默认',)

缺席=object()#区分没有 oauth 和 oauth 值为 None

def 读(主体,键):
    'dict 用键，对象用属性。缺则 None'
    if isinstance(主体,dict):
        if 键 not in 主体:
            return None
        return 主体[键]
    return getattr(主体,键,None)

def 有授权(认证):
    'oauth 在即可。值为 None 也算在，缺属性则不算。认证本身缺了要抛'
    if 认证 is None:
        raise AttributeError('oauth')
    if isinstance(认证,dict):
        return 'oauth' in 认证
    return getattr(认证,'oauth',缺席) is not 缺席

def 提供方默认(提供方):
    '返回生成的展示元数据，不执行认证。目录里没有的提供方仍可配置，只在端点是不含占位符的固定公开地址时给出 defaultBaseURL'
    标识=读(提供方,'id')
    基址=读(提供方,'baseUrl')
    if 标识 not in 提供方数据:
        if isinstance(基址,str) and 基址!='' and '{' not in 基址:
            return {'defaultBaseURL':基址}
        return {}
    数据=提供方数据[标识]
    端点={}
    for 键,值 in 数据.items():
        if 键!='env':
            端点[键]=值
    端点['nativeAuth']={'env':数据['env'],'oauth':有授权(读(提供方,'auth'))}
    return 端点
