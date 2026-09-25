"""GitHub HTTP 鉴权、解析与即发即弃分发。"""
import hashlib,hmac,json,time#签名、JSON 与时间
from ...工具.值 import 快照json值#无损 JSON 快照
from ..webhook.标识构造 import Webhook来源标识,Webhook投递标识
from ..webhook import Webhook错误#运行时失败
from .正文 import WebhookHttp错误,读取有界utf8正文

__all__=['创建GitHubWebhook事件分派']

def 必填头(请求,名):
    """要求唯一、非空的请求头。请求为 webServer 对象，头名为小写。"""
    头表=请求.headers
    if 名 not in 头表:
        raise WebhookHttp错误(400,f'missing {名} header')
    头字段值=头表[名]
    if isinstance(头字段值,list):
        if len(头字段值)!=1:
            raise WebhookHttp错误(400,f'missing {名} header')
        值=头字段值[0]
    else:
        值=头字段值
    if 值 is None or str(值).strip()=='':
        raise WebhookHttp错误(400,f'missing {名} header')
    return str(值)

def 是否json内容类型(值):
    """Content-Type 是否为 JSON，且最多带一个 UTF-8 charset。"""
    if 值 is None:
        return False
    if isinstance(值,list):
        if len(值)==0:
            return False
        值=值[0]
    部分=[段.strip() for 段 in str(值).split(';')]
    if len(部分)==0 or 部分[0].lower()!='application/json':
        return False
    if len(部分)==1:
        return True
    if len(部分)!=2:
        return False
    return 部分[1].lower() in ('charset=utf-8','charset="utf-8"')

def 发送响应(响应对象,状态码,消息=None):
    """恰好发送一次空响应或纯文本响应。"""
    if 消息 is None:
        响应对象.writeHead(状态码)
        响应对象.end()
        return
    响应对象.writeHead(状态码,{'content-type':'text/plain; charset=utf-8'})
    响应对象.end(消息)

def 解析载荷(正文):
    """把正文解析为可无损快照的 JSON 对象。"""
    try:
        已解析=json.loads(正文)
    except json.JSONDecodeError:
        raise WebhookHttp错误(400,'request body is not valid JSON')
    if 已解析 is None or not isinstance(已解析,dict):
        raise WebhookHttp错误(400,'GitHub webhook payload must be a JSON object')
    快照=快照json值(已解析)
    if 快照 is None:
        raise WebhookHttp错误(400,'GitHub webhook payload is not lossless JSON')
    return 快照

def 校验签名(密钥,正文,签名头):
    """校验 GitHub HMAC-SHA256 签名头（sha256=…）。"""
    if not 签名头.startswith('sha256='):
        return False
    期望=签名头[7:]
    实际=hmac.new(密钥.encode('utf-8'),正文.encode('utf-8'),hashlib.sha256).hexdigest()
    return hmac.compare_digest(期望,实际)

def 创建GitHubWebhook事件分派(上下文,配置):
    """创建一条精确路由的 GitHub 事件分派入口。配置为 dict。"""
    def 分派入口(请求,响应对象):
        """鉴权并解析后立即分发；不等待规则结算。"""
        try:
            方法=请求.method
            if 方法!='POST':
                响应对象.setHeader('allow','POST')
                raise WebhookHttp错误(405,'method not allowed')
            头表=请求.headers
            内容类型=头表['content-type'] if 'content-type' in 头表 else None
            if not 是否json内容类型(内容类型):
                raise WebhookHttp错误(415,'content type must be application/json')
            正文=读取有界utf8正文(请求,配置['maxBodyBytes'])
            签名=必填头(请求,'x-hub-signature-256')
            投递号=必填头(请求,'x-github-delivery')
            事件名=必填头(请求,'x-github-event')
            凭据=上下文.credentials.解析(配置['secretEnv'])
            if 凭据 is None or 凭据['value']=='':
                raise WebhookHttp错误(503,'GitHub webhook secret is unavailable')
            if not 校验签名(凭据['value'],正文,签名):
                raise WebhookHttp错误(401,'invalid webhook signature')
            载荷=解析载荷(正文)
            投递={
                'kind':'github',
                'source':Webhook来源标识(配置['source']),
                'deliveryId':Webhook投递标识(投递号),
                'event':{'name':事件名,'payload':载荷},
                'receivedAt':int(time.time()*1000),#纪元毫秒
            }
            try:
                上下文.webhookRuntime.dispatch(投递)#即发即弃，不等规则返回
            except Webhook错误:
                上下文.日志.警告('webhook-github: dispatch unavailable')
                raise WebhookHttp错误(503,'webhook runtime is unavailable')
            发送响应(响应对象,202)
        except WebhookHttp错误 as 错误:
            消息=错误.args[0] if len(错误.args)>0 else None#可回写的安全消息
            发送响应(响应对象,错误.status,消息)
        except (TypeError,OSError,UnicodeDecodeError):
            上下文.日志.警告('webhook-github: request failed')
            发送响应(响应对象,503,'webhook ingress is unavailable')
    return 分派入口
