"""通用 Connection 一元 RPC 通道的浏览器调用方。

对齐上游 `connection/src/client/rpc.ts`。公开面仅中文名。
"""
import json,re#JSON 与形态校验
from urllib.parse import urljoin#拼基址
from apiproxy.接口 import Rpc标识,服务端响应模式#RPC id 与响应模式
from .随机uuid import 随机uuid#浏览器 UUID

__all__=['创建网页连接rpc']#仅中文公开名

内部基址='http://dsh.internal'#无 location.origin 时的内部基址
通道规则=re.compile(r'^/[A-Za-z0-9._~-]+$')#通道：单段绝对路径
端点段规则=re.compile(r'^[A-Za-z0-9_$.-]+$')#端点每一段允许的字符

def 解析基址():#解析 fetch 基址
    """有真 origin 用它，不透明 origin 用内部基址。"""
    try:#浏览器才有 location
        import builtins#取全局
        定位=getattr(builtins,'location',None)#可能缺
        if 定位 is None:#再试 globals
            定位=globals().get('location')#页内
        原点=getattr(定位,'origin',None) if 定位 is not None else None#origin
        if 原点 is not None and 原点!='null':#真 origin
            return 原点#用它
    except Exception:#非浏览器
        pass#落到内部基址
    return 内部基址#假权威

def 断言目标(通道,端点):#校验通道与端点
    """通道名与端点各段必须合法。"""
    段们=端点.split('/')#端点按段切开
    if not 通道规则.fullmatch(通道):#通道名非法
        raise Exception('connection: invalid RPC target '+json.dumps(通道+'/'+端点))#调用前失败
    for 段 in 段们:#任一段
        if 段=='' or 段=='.' or 段=='..' or 端点段规则.fullmatch(段) is None:#空段、相对段或非法字符
            raise Exception('connection: invalid RPC target '+json.dumps(通道+'/'+端点))#调用前失败

def 创建网页连接rpc():#浏览器 RPC 调用方
    """创建拥有请求关联与响应信封校验的调用方。"""
    def 调用(通道,端点,载荷,信号=None):#经 HTTP POST 发一元 RPC
        """断言目标后 POST，校验回显 rpcId，交出业务结果。"""
        断言目标(通道,端点)#通道与端点形态必须合法
        rpc标识=Rpc标识(随机uuid())#本请求关联 id
        消息={#客户端请求信封
            'type':'client-request',#判别标签
            'rpcId':rpc标识,#关联 id
            'method':端点,#信封 method 必须等于路径端点
            'payload':载荷,#通道拥有的载荷
        }#结束信封
        地址=urljoin(解析基址().rstrip('/')+'/',通道.strip('/')+'/'+端点)#通道/端点
        选项={#fetch 选项
            'method':'POST',#一元 RPC 用 POST
            'headers':{'content-type':'application/json'},#JSON 正文
            'body':json.dumps(消息,ensure_ascii=False),#序列化信封
        }#结束选项
        if 信号 is not None:#有取消信号才带上
            选项['signal']=信号#取消
        import urllib.request as 请求库#标准库 fetch 形
        请求=请求库.Request(地址,data=选项['body'].encode('utf-8'),headers=选项['headers'],method='POST')#构造
        try:#发
            with 请求库.urlopen(请求) as 响应:#POST
                if getattr(响应,'status',200)<200 or getattr(响应,'status',200)>=300:#HTTP 层失败
                    raise Exception(f'transport failure for {通道}/{端点}: HTTP {getattr(响应,"status",0)}')#传输失败
                正文=响应.read().decode('utf-8')#读正文
        except Exception as 错误:#传输失败
            if 'transport failure' in str(错误):#已是本层
                raise#原样
            raise Exception(f'transport failure for {通道}/{端点}: {错误}') from 错误#包一层
        完整=服务端响应模式.parse(json.loads(正文))#校验服务端响应信封
        回显=完整['rpcId'] if isinstance(完整,dict) else 完整.rpcId#关联 id
        if 回显!=rpc标识:#关联必须对上
            raise Exception(f'rpcId mismatch for {端点}: sent {rpc标识}, got {回显}')#对不上则失败
        return 完整['result'] if isinstance(完整,dict) else 完整.result#交出业务结果
    return type('网页连接rpc',(),{'call':staticmethod(调用)})()#调用方
