__all__=('查找策略失败','远程错误','协议消息错误')

def 去掉绝对路径(文本):
    '失败说明里去掉盘符路径、根路径和家目录路径'
    留下=[]
    for 词 in str(文本).split():
        统一=词.strip('\'"').replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    return ' '.join(留下).strip()

def _说明(消息,兜底):
    '说明去掉绝对路径；掏空则用兜底'
    干净=去掉绝对路径(消息)
    if 干净=='':
        return 兜底
    return 干净

class 查找策略失败(Exception):
    '查找策略拒绝。带类型的载荷在 failure 上，说明文不包含被拒绝的身份'
    def __init__(自身,失败载荷):
        '包装一次适配器失败'
        super().__init__('查找策略拒绝了所请求的身份')
        自身.name='TypertLookupFailure'
        自身.failure=失败载荷

class 远程错误(Exception):
    '一次远程调用失败。判别看 code，不看异常类型'
    def __init__(自身,code,message,details,原因=None):
        'code、message、details 会过线路；原因只留在本进程。说明去掉绝对路径'
        干净=_说明(message,str(code))
        super().__init__(干净)
        自身.name='RemoteError'
        自身.code=code
        自身.message=干净
        自身.details=details
        自身.isDSHRemoteError=True
        if 原因 is not None:
            自身.__cause__=原因

class 协议消息错误(Exception):
    '协议拒绝。只带一条给人看的说明'
    def __init__(自身,消息=''):
        '说明去掉绝对路径'
        super().__init__(_说明(消息,'协议消息错误'))
