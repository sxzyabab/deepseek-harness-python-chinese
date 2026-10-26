'Search 与 Fetch API 共用的鉴权和拒绝重定向的传输'
import json
import threading
from http.client import HTTPConnection as 明文连接
from http.client import HTTPSConnection as 安全连接
from http.client import HTTPException as HTTP异常
from urllib.parse import urlparse as 解析网址
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from ...凭据.凭据 import 凭证引用
from ...工具.启动环境 import 取启动环境
from ..web.异常 import 网络错误

__all__=[
    '深度求索网页认证','有深度求索网页凭据','是记录','无效响应',
    '派发深度求索网页','凭据就绪',
]

账号提供方='deepseek-account'
用户代理='deepseek-harness/0.0.1'
线程=threading.Thread


def 已中止(信号):
    '调用方 Event 是否已置位。缺席视为未中止'
    if 信号 is None:
        return False
    return 信号.is_set()


def 等待信号(信号):
    '阻塞到 threading.Event 置位'
    信号.wait()


def 搜索已取消(信号=None,回退=None):
    '提供方稳定的取消错误。原因留在 cause 上'
    原因=回退
    if 信号 is not None and 已中止(信号):
        原因=getattr(信号,'reason',回退)
    if 原因 is None:
        return 网络错误('DeepSeek web request aborted','WEB_ABORTED')
    return 网络错误('DeepSeek web request aborted','WEB_ABORTED',{'cause':原因})


def 若已中止则抛出(信号=None):
    '调用方已经中止时抛出稳定取消错误'
    if 已中止(信号):
        raise 搜索已取消(信号)


def 是中止错误(错误):
    '套接字被取消线程拆掉时，按 AbortError 记'
    return getattr(错误,'name',None)=='AbortError'


def 是记录(值):
    '可读的 JSON 对象。数组不算'
    return isinstance(值,dict)


def 无效响应():
    '上游 JSON 不合约定。不把响应正文写进错误'
    return 网络错误('DeepSeek returned an invalid response body','WEB_PROVIDER_ERROR')


def 深度求索网页认证(上下文,配置):
    '为一次操作解析凭据来源，不把密钥留在提供方上'
    密钥环境=凭证引用(配置['apiKeyEnv'])
    字面量=配置.get('apiKey')
    字面量密钥=字面量 if isinstance(字面量,str) and len(字面量)>0 else None

    def 解析账号令牌(端点):
        '账号路由才向账号服务要这一端点的令牌'
        智能体=上下文.获取服务('agents')
        发起方=None if 智能体 is None else 智能体.当前发起方()
        会话=None if 发起方 is None else 发起方.session
        请求上下文=None if 会话 is None else 会话.请求上下文()
        提供方=None if 请求上下文 is None else 请求上下文.get('provider')
        if 提供方!=账号提供方:
            return None
        账号=上下文.获取服务('deepseekAccount')
        if 账号 is None:
            return None
        return 账号.解析令牌(端点)

    def 解析密钥():
        '有凭证服务就走凭证。否则环境就是整个凭证平面'
        凭证=上下文.获取服务('credentials')
        if 凭证 is not None:
            命中=凭证.解析(密钥环境)
            if 命中 is None:
                return None
            return 命中.get('value')
        环境项=取启动环境(上下文).取(密钥环境)
        if 环境项 is not None and isinstance(环境项.get('value'),str) and len(环境项['value'])>0:
            return 环境项['value']
        return None

    认证={'resolveAccountToken':解析账号令牌,'resolveApiKey':解析密钥,'apiKeyEnv':密钥环境}
    if 字面量密钥 is not None:
        认证['apiKey']=字面量密钥
    return 认证


def 凭据就绪(上下文,配置,路由):
    '账号令牌优先，然后才是字面密钥或已配置的引用。读失败回答假'
    if 路由==账号提供方:
        账号=上下文.获取服务('deepseekAccount')
        if 账号 is not None:
            try:
                令牌=账号.解析令牌(配置['baseURL'])
            except Exception as 读不到授予:
                读不到授予=None
                return False
            if isinstance(令牌,str) and len(令牌)>0:
                return True
    字面量=配置.get('apiKey')
    if isinstance(字面量,str) and len(字面量)>0:
        return True
    密钥环境=凭证引用(配置['apiKeyEnv'])
    凭证=上下文.获取服务('credentials')
    if 凭证 is None:
        环境项=取启动环境(上下文).取(密钥环境)
        return 环境项 is not None and isinstance(环境项.get('value'),str) and len(环境项['value'])>0
    try:
        return 凭证.描述(密钥环境)['configured'] is True
    except Exception as 读不到存储:
        读不到存储=None
        return False


def 有深度求索网页凭据(认证):
    '只看有没有来源，不解析密钥'
    字面量=认证.get('apiKey')
    字面长度=len(字面量) if isinstance(字面量,str) else 0
    return 字面长度>0 or 认证.get('resolveApiKey') is not None or 认证.get('resolveAccountToken') is not None


def 账号被拒(消息):
    '账号令牌被拒时，指引重新登录，而不是改端点'
    return 网络错误(
        消息+'\n\nDeepSeek rejected the account sign-in used for this web request. '
        +'Guide the user to sign in to DeepSeek again; the endpoint does not need changing.',
        'WEB_PROVIDER_ERROR',
    )


def 端点错误(指引,端点,消息,原因=None):
    '派发开始之后的失败带上端点和设置位置'
    正文=(
        消息+'\n\nThe web request used endpoint '+紧凑json编码(端点)+'. '
        +指引['subject']+' endpoint configuration is separate from chat. If that endpoint is not intended, '
        +'guide the user to Plugins > Built-in plugin settings > '+指引['page']+', where they can '
        +'change and save '+指引['label']+'. If that settings page is unavailable, the user can set '
        +指引['plugin']+'.'+指引['field']+' to a trusted DeepSeek endpoint. Only the user should choose or change the endpoint.'
    )
    if 原因 is None:
        return 网络错误(正文,'WEB_PROVIDER_ERROR')
    return 网络错误(正文,'WEB_PROVIDER_ERROR',{'cause':原因})


def 解析凭据(解析,信号):
    '已经取消的搜索不再解析。解析失败记成提供方错误'
    若已中止则抛出(信号)
    try:
        return 解析()
    except 网络错误:
        raise
    except Exception as 错误:
        if 已中止(信号) or 是中止错误(错误):
            raise 搜索已取消(信号,错误)
        raise 网络错误(
            'DeepSeek web credential resolution failed: '+str(错误),
            'WEB_PROVIDER_ERROR',
            {'cause':错误},
        )


def 解析接口密钥(选项,插件,信号):
    '解析这一次的 API 密钥，不留在提供方上'
    若已中止则抛出(信号)
    字面量=选项.get('apiKey')
    if isinstance(字面量,str) and len(字面量)>0:
        return 字面量
    解析=选项.get('resolveApiKey')
    已解析=None if 解析 is None else 解析凭据(解析,信号)
    if isinstance(已解析,str) and len(已解析)>0:
        return 已解析
    引用=选项.get('apiKeyEnv')
    if 引用 is None:
        引用='DEEPSEEK_API_KEY'
    raise 网络错误(
        'DeepSeek web access has no API key for "'+str(引用)+'"; store it through the credentials service'
        +' (the web Models page writes it), export it in the launching environment, or set a literal'
        +' "apiKey" in the '+插件+' config; a conversation using a DeepSeek Account model'
        +' searches with the account sign-in instead',
        'WEB_PROVIDER_CREDENTIAL_MISSING',
    )


def 认证头(选项,请求,信号):
    '有账号令牌就只用它。否则用 API 密钥'
    解析账号=选项.get('resolveAccountToken')
    令牌=None if 解析账号 is None else 解析凭据(lambda: 解析账号(请求['endpoint']),信号)
    if isinstance(令牌,str) and len(令牌)>0:
        return {'kind':'account','headers':{'x-dsh-auth-token':令牌}}
    密钥=解析接口密钥(选项,请求['guidance']['plugin'],信号)
    头={'authorization':'Bearer '+密钥}
    附加=请求.get('apiKeyHeaders')
    if 附加 is not None:
        头.update(附加(密钥))
    return {'kind':'api-key','headers':头}


def 读错误详情(原文):
    '从错误 JSON 里取出说明。没有就返回空'
    解析=json.loads(原文)
    if not 是记录(解析):
        return ''
    错误字段=解析.get('error')
    if isinstance(错误字段,str):
        详情=错误字段
    elif 是记录(错误字段):
        详情=错误字段.get('message')
    else:
        详情=解析.get('message')
    if isinstance(详情,str) and len(详情)>0:
        return ': '+详情
    return ''


def 派发深度求索网页(选项,请求,信号=None):
    '用同一份设置和凭据派发一次。重定向不跟随'
    端点=请求['endpoint']
    认证=认证头(选项,请求,信号)
    若已中止则抛出(信号)
    记录=请求.get('recordRequest')
    if 记录 is not None:
        记录(端点)
    若已中止则抛出(信号)
    头=dict(认证['headers'])
    if isinstance(请求.get('headers'),dict):
        头.update(请求['headers'])
    头['content-type']='application/json'
    头['accept']='application/json'
    头['user-agent']=用户代理
    拆开=解析网址(端点)
    路径=拆开.path if len(拆开.path)>0 else '/'
    if len(拆开.query)>0:
        路径=路径+'?'+拆开.query
    if 拆开.scheme=='https':
        客户端=安全连接(拆开.hostname,拆开.port)
    else:
        客户端=明文连接(拆开.hostname,拆开.port)
    if 信号 is not None:
        def 监视中止():
            '信号中止时关掉套接字'
            等待信号(信号)
            客户端.close()
        线程(target=监视中止,daemon=True).start()
        if 已中止(信号):
            客户端.close()
            raise 搜索已取消(信号)
    载荷=紧凑json编码(请求['body']).encode('utf-8')
    try:
        客户端.request('POST',路径,body=载荷,headers=头)
        响应=客户端.getresponse()
    except 网络错误:
        raise
    except (OSError,HTTP异常,TimeoutError) as 错误:
        if 已中止(信号) or 是中止错误(错误):
            raise 搜索已取消(信号,错误)
        raise 端点错误(请求['guidance'],端点,'DeepSeek web request failed: '+str(错误),错误)
    状态=响应.status
    if 状态<200 or 状态>=300:
        消息='DeepSeek API error (HTTP '+str(状态)+')'
        try:
            原文=响应.read().decode('utf-8')
            消息=消息+读错误详情(原文)
        except 网络错误:
            raise
        except Exception as 错误:
            if 已中止(信号) or 是中止错误(错误):
                raise 搜索已取消(信号,错误)
        finally:
            响应.close()
            客户端.close()
        if 状态==401 and 认证['kind']=='account':
            raise 账号被拒(消息)
        raise 端点错误(请求['guidance'],端点,消息)
    try:
        原文=响应.read().decode('utf-8')
        载荷值=json.loads(原文)
        若已中止则抛出(信号)
        return 请求['decode'](载荷值)
    except 网络错误:
        raise
    except Exception as 错误:
        if 已中止(信号) or 是中止错误(错误):
            raise 搜索已取消(信号,错误)
        if isinstance(错误,网络错误):
            消息=错误.args[0] if len(错误.args)>0 else str(错误)
        else:
            消息='DeepSeek returned an unprocessable response body: '+str(错误)
        raise 端点错误(请求['guidance'],端点,消息,错误)
    finally:
        响应.close()
        客户端.close()
