"""GitHub HTTP 鉴权、解析与 fire-and-forget 分发。

对齐上游 `webhook-github/src/handler.ts`。公开面仅中文名。
"""
import hashlib,hmac,json,time#签名、JSON与时间
from ...工具.值 import 快照json值#无损JSON快照
from ..webhook.标识构造 import Webhook来源标识,Webhook投递标识#webhook标识构造
from ..webhook import Webhook错误#运行时失败
from .正文 import WebhookHttp错误,读取有界utf8正文#正文读取

__all__=['创建GitHubWebhook事件分派']#仅中文公开名

def 必填头(请求,名):
    """要求唯一、非空的请求头。请求为 webServer 对象，头名为小写。"""
    头表=请求.headers#请求头
    if 名 not in 头表:#键不存在
        raise WebhookHttp错误(400,f'missing {名} header')#拒绝
    头字段值=头表[名]#头值
    if isinstance(头字段值,list):#多值
        if len(头字段值)!=1:#不唯一
            raise WebhookHttp错误(400,f'missing {名} header')#拒绝
        值=头字段值[0]#取唯一
    else:#单值
        值=头字段值#原值
    if 值 is None or str(值).strip()=='':#空
        raise WebhookHttp错误(400,f'missing {名} header')#拒绝
    return str(值)#返回

def 是否json内容类型(值):
    """Content-Type 是否为 JSON，且最多带一个 UTF-8 charset。"""
    if 值 is None:#缺席
        return False#不是
    if isinstance(值,list):#多值
        if len(值)==0:#空列表
            return False#不是
        值=值[0]#取首个
    部分=[段.strip() for 段 in str(值).split(';')]#分段
    if len(部分)==0 or 部分[0].lower()!='application/json':#不是JSON
        return False#不是
    if len(部分)==1:#无参数
        return True#纯JSON
    if len(部分)!=2:#参数过多
        return False#不是
    return 部分[1].lower() in ('charset=utf-8','charset="utf-8"')#UTF-8

def 发送响应(响应对象,状态码,消息=None):
    """恰好发送一次空响应或纯文本响应。"""
    if 消息 is None:#空响应
        响应对象.writeHead(状态码)#写头
        响应对象.end()#结束
        return#完成
    响应对象.writeHead(状态码,{'content-type':'text/plain; charset=utf-8'})#写头
    响应对象.end(消息)#写正文

def 解析载荷(正文):
    """把解析值转成适配器通用的已签名对象保证。"""
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

def 校验签名(密钥,正文,签名头):
    """校验 GitHub HMAC SHA256 签名。"""
    if not 签名头.startswith('sha256='):#前缀
        return False#失败
    期望=签名头[7:]#十六进制摘要
    实际=hmac.new(密钥.encode('utf-8'),正文.encode('utf-8'),hashlib.sha256).hexdigest()#计算
    return hmac.compare_digest(期望,实际)#常量时间比较

def 创建GitHubWebhook事件分派(上下文,配置):
    """创建一条精确路由的 GitHub 事件分派入口。配置为 dict。"""
    def 分派入口(请求,响应对象):
        """鉴权、解析，再 fire-and-forget 分发。"""
        try:#处理请求
            方法=请求.method#HTTP方法
            if 方法!='POST':#非POST
                响应对象.setHeader('allow','POST')#Allow
                raise WebhookHttp错误(405,'method not allowed')#拒绝
            头表=请求.headers#请求头
            内容类型=头表['content-type'] if 'content-type' in 头表 else None#Content-Type
            if not 是否json内容类型(内容类型):#非JSON
                raise WebhookHttp错误(415,'content type must be application/json')#拒绝
            正文=读取有界utf8正文(请求,配置['maxBodyBytes'])#读正文
            签名=必填头(请求,'x-hub-signature-256')#签名
            投递号=必填头(请求,'x-github-delivery')#投递id
            事件名=必填头(请求,'x-github-event')#事件名
            凭据=上下文.credentials.解析(配置['secretEnv'])#解析密钥
            if 凭据 is None or 凭据['value']=='':#密钥不可用
                raise WebhookHttp错误(503,'GitHub webhook secret is unavailable')#拒绝
            if not 校验签名(凭据['value'],正文,签名):#签名校验
                raise WebhookHttp错误(401,'invalid webhook signature')#拒绝
            载荷=解析载荷(正文)#解析载荷
            投递={#组装投递
                'kind':'github',#提供方
                'source':Webhook来源标识(配置['source']),#来源
                'deliveryId':Webhook投递标识(投递号),#投递号
                'event':{'name':事件名,'payload':载荷},#事件
                'receivedAt':int(time.time()*1000),#收到时刻
            }#投递结束
            try:#分发
                上下文.webhookRuntime.dispatch(投递)#fire-and-forget
            except Webhook错误:#运行时不可用
                上下文.日志.警告('webhook-github: dispatch unavailable')#记警告
                raise WebhookHttp错误(503,'webhook runtime is unavailable')#拒绝
            发送响应(响应对象,202)#接受
        except WebhookHttp错误 as 错误:#已知HTTP错误
            消息=错误.args[0] if len(错误.args)>0 else None#安全消息
            发送响应(响应对象,错误.status,消息)#写回
        except (TypeError,OSError,UnicodeDecodeError):#未知入口失败
            上下文.日志.警告('webhook-github: request failed')#记警告
            发送响应(响应对象,503,'webhook ingress is unavailable')#拒绝
    return 分派入口#返回分派入口
