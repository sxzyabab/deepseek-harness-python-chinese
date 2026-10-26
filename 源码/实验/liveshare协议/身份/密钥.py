'一条身份三元组的规范访问控制键，以及每个适配器先做的规范化'
from urllib.parse import quote,unquote
import re

__all__=['身份键','键到身份','租户占位','规范化身份','要求身份租户']

组件安全="-_.!~*'()"
坏转义=re.compile(r'%(?![0-9A-Fa-f]{2})')

def 编码组件(文本):
    '与 encodeURIComponent 同一组不编码字符'
    return quote(文本,safe=组件安全)

def 解码组件(文本):
    '非法百分号转义时抛出，调用方把它当成无法解析'
    if 坏转义.search(文本) is not None:
        raise ValueError('bad escape')
    return unquote(文本)

def 身份键(身份):
    '分享访问控制里存放的规范键。调用方要先规范化'
    return ':'.join([
        编码组件(身份['providerId']),
        编码组件(身份['tenantId']),
        编码组件(身份['subjectId']),
    ])

def 键到身份(键):
    '解析身份键造出来的规范键。不是规范键时没有身份'
    段=键.split(':')
    if len(段)!=3:
        return None
    try:
        提供方,租户,主体=解码组件(段[0]),解码组件(段[1]),解码组件(段[2])
    except ValueError:
        return None
    if 提供方=='' or 租户=='' or 主体=='':
        return None
    return {'providerId':提供方,'tenantId':租户,'subjectId':主体}

租户占位='default'

def 规范化身份(身份,租户回落=None):
    '适配器产出的身份在进中继状态之前先规范化。提供方或主体为空时没有身份'
    if 租户回落 is None:
        租户回落=租户占位
    if 身份['providerId']=='' or 身份['subjectId']=='':
        return None
    if 身份['tenantId']!='':
        return 身份
    if 租户回落=='':
        return None
    结果=dict(身份)
    结果['tenantId']=租户回落
    return 结果

def 要求身份租户(身份):
    '提供方必须签发租户时，空租户不能通过'
    if 身份['providerId']=='' or 身份['tenantId']=='' or 身份['subjectId']=='':
        return None
    return 身份
