import re
from .协议 import 平台认证错误,请求账号

__all__=['投影配置档','读账号细节']

钱包形态=re.compile(r'^-?\d+(?:\.\d+)?$',re.ASCII)

def 投影配置档(值):
    """投影平台用户数据，不保留凭证。"""
    if not isinstance(值,dict):
        raise 平台认证错误('protocol')
    标识=值.get('id')
    邮箱=值.get('email')
    手机=值.get('mobile') if 'mobile' in 值 else None
    手机号=值.get('mobile_number') if 'mobile_number' in 值 else None
    身份=值.get('id_profile') if 'id_profile' in 值 else None
    if not isinstance(邮箱,str):
        raise 平台认证错误('protocol')
    图片=None
    姓名=None
    if 身份 is not None:
        if not isinstance(身份,dict):
            raise 平台认证错误('protocol')
        姓名=身份.get('name')
        图片=身份.get('picture') if 'picture' in 身份 else None
        if 图片=='':
            图片=None
        if 姓名=='':
            姓名=None
    联系=手机 or 手机号 or 邮箱 or None
    return {
        'id':None if 标识 is None else 标识,
        'avatarUrl':图片 or None,
        'name':姓名 or None,
        'contact':联系,
    }

def 解析钱包表(值):
    """校验钱包列表。"""
    if not isinstance(值,list):
        raise 平台认证错误('protocol')
    结果=[]
    for 项 in 值:
        if not isinstance(项,dict):
            raise 平台认证错误('protocol')
        货币=项.get('currency')
        余额=项.get('balance')
        if 货币 not in ('CNY','USD') or not isinstance(余额,str) or 钱包形态.search(余额) is None:
            raise 平台认证错误('protocol')
        结果.append({'currency':货币,'balance':余额})
    return 结果

def 读账号细节(字段,来源,令牌,信号,头):
    """读配置档或钱包；失败永不变成零余额。"""
    if 字段=='profile':
        路径='/auth-api/v0/users/current'
        def 解析(值):
            """配置档。"""
            return {'status':'ready','value':投影配置档(值)}
    else:
        路径='/api/v0/users/get_user_summary'
        def 解析(值):
            """钱包。"""
            if not isinstance(值,dict):
                raise 平台认证错误('protocol')
            return {
                'status':'ready',
                'value':解析钱包表(值.get('normal_wallets')),
                'bonusWallets':解析钱包表(值.get('bonus_wallets')),
            }
    try:
        return 解析(请求账号(来源,路径,令牌,信号,头))
    except Exception:
        return {'status':'failed'}
