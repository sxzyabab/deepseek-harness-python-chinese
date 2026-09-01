"""GitHub HTTP authentication, parsing, and fire-and-forget dispatch. 对齐上游 `webhook-github/src/handler.ts`。"""
import hashlib,hmac,json#签名与JSON
from ...工具.值 import 快照json值#无损JSON快照
from ..webhook.品牌 import Webhook来源标识,Webhook投递标识#webhook品牌
from .正文 import WebhookHttp错误,读取有界utf8正文#正文读取

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        if callable(getattr(值,'wait',None)):#Future风格
            return 值.wait()#等待
        return 值.等待()#thenable
    return 值#同步值

def 必填头(请求,名):#读取唯一非空头
    """Require one unambiguous non-empty request header."""
    头们=取字段(取字段(请求,'headers',{}),名) or 取字段(请求,'headers',{}).get(名.lower())#头值
    if isinstance(头们,list):#多值
        if len(头们)!=1:#不唯一
            raise WebhookHttp错误(400,f'missing {名} header')#拒绝
        值=头们[0]#取唯一
    else:#单值
        值=头们#原值
    if 值 is None or str(值).strip()=='':#空
        raise WebhookHttp错误(400,f'missing {名} header')#拒绝
    return str(值)#返回

def 是否json内容类型(值):#是否application/json
    """Whether Content-Type names JSON with at most one UTF-8 charset parameter."""
    if 值 is None:#缺席
        return False#不是
    if isinstance(值,list):#多值
        值=值[0] if len(值)>0 else None#取首个
    if 值 is None:#仍缺席
        return False#不是
    部分=[段.strip() for 段 in str(值).split(';')]#分段
    if len(部分)==0 or 部分[0].lower()!='application/json':#不是JSON
        return False#不是
    if len(部分)==1:#无参数
        return True#纯JSON
    if len(部分)!=2:#参数过多
        return False#不是
    return 部分[1].lower() in ('charset=utf-8','charset="utf-8"')#UTF-8

def 响应(响应对象,状态码,消息=None):#发送响应
    """Send one empty or plain-text response exactly once."""
    if 消息 is None:#空响应
        if hasattr(响应对象,'writeHead'):#Node风格
            响应对象.writeHead(状态码)#写头
            响应对象.end()#结束
        return#完成
    if hasattr(响应对象,'writeHead'):#Node风格
        响应对象.writeHead(状态码,{'content-type':'text/plain; charset=utf-8'})#写头
        响应对象.end(消息)#写正文

def 解析载荷(正文):#解析JSON对象
    """Convert a parsed value into the adapter's generic signed-object guarantee."""
    try:#解析JSON
        已解析=json.loads(正文)#JSON.parse
    except json.JSONDecodeError:#非法JSON
        raise WebhookHttp错误(400,'request body is not valid JSON')#拒绝
    if 已解析 is None or not isinstance(已解析,dict):#必须是对象
        raise WebhookHttp错误(400,'GitHub webhook payload must be a JSON object')#拒绝
    快照=快照json值(已解析)#无损快照
    if 快照 is None:#不能快照
        raise WebhookHttp错误(400,'GitHub webhook payload is not lossless JSON')#拒绝
    return 快照#返回对象

def 校验签名(密钥,正文,签名头):#校验Hub签名
    """Verify GitHub HMAC SHA256 signature."""
    if not 签名头.startswith('sha256='):#前缀
        return False#失败
    期望=签名头[7:]#十六进制摘要
    实际=hmac.new(密钥.encode('utf-8'),正文.encode('utf-8'),hashlib.sha256).hexdigest()#计算
    return hmac.compare_digest(期望,实际)#常量时间比较

def 创建GitHubWebhook处理器(上下文,配置):#创建处理器
    """Create one exact-route GitHub handler."""
    async def 处理器(请求,响应):#HTTP入口
        """Authenticate, parse, and fire-and-forget dispatch."""
        try:#处理请求
            方法=取字段(请求,'method','GET')#HTTP方法
            if 方法!='POST':#非POST
                if hasattr(响应,'setHeader'):#Node风格
                    响应.setHeader('allow','POST')#Allow
                raise WebhookHttp错误(405,'method not allowed')#拒绝
            内容类型=取字段(取字段(请求,'headers',{}),'content-type')#Content-Type
            if not 是否json内容类型(内容类型):#非JSON
                raise WebhookHttp错误(415,'content type must be application/json')#拒绝
            正文=await 读取有界utf8正文(请求,取字段(配置,'maxBodyBytes'))#读正文
            签名=必填头(请求,'x-hub-signature-256')#签名
            投递号=必填头(请求,'x-github-delivery')#投递id
            事件名=必填头(请求,'x-github-event')#事件名
            凭据=解开(上下文.credentials.resolve(取字段(配置,'secretEnv')))#解析密钥
            if 凭据 is None or 取字段(凭据,'value','')=='':#密钥不可用
                raise WebhookHttp错误(503,'GitHub webhook secret is unavailable')#拒绝
            if not 校验签名(取字段(凭据,'value'),正文,签名):#签名校验
                raise WebhookHttp错误(401,'invalid webhook signature')#拒绝
            载荷=解析载荷(正文)#解析载荷
            投递={
                'kind':'github',
                'source':Webhook来源标识(取字段(配置,'source')),
                'deliveryId':Webhook投递标识(投递号),
                'event':{'name':事件名,'payload':载荷},
                'receivedAt':int(__import__('time').time()*1000),
            }#组装投递
            try:#分发
                上下文.webhookRuntime.dispatch(投递)#fire-and-forget
            except Exception:#运行时不可用
                上下文.logger.warn('webhook-github: dispatch unavailable')#记警告
                raise WebhookHttp错误(503,'webhook runtime is unavailable')#拒绝
            响应(响应,202)#接受
        except WebhookHttp错误 as 错误:#已知HTTP错误
            响应(响应,错误.status,错误.args[0] if len(错误.args)>0 else None)#安全消息
        except Exception:#未知错误
            上下文.logger.warn('webhook-github: request failed')#记警告
            响应(响应,503,'webhook ingress is unavailable')#拒绝
    return 处理器#返回处理器
