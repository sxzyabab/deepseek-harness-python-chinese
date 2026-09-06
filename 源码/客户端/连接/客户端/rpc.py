"""通用 Connection 一元 RPC 通道的浏览器调用方。

对齐上游 `connection/src/client/rpc.ts`。公开面仅中文名。
"""
import builtins,json,re#全局、JSON 与形态校验
import urllib.request as 请求库#标准库 fetch 形
from urllib.parse import urljoin#拼基址
from ....host.apiproxy.接口 import Rpc标识,服务端响应模式#RPC id 与响应模式
from ..rpc import 连接错误#本包异常
from .随机uuid import 随机uuid#浏览器 UUID

__all__=['创建网页连接rpc']#仅中文公开名

内部基址='http://dsh.internal'#无 location.origin 时的内部基址
通道规则=re.compile(r'^/[A-Za-z0-9._~-]+\Z')#通道：单段绝对路径
端点段规则=re.compile(r'^[A-Za-z0-9_$.-]+\Z')#端点每一段允许的字符

def 解析基址():#解析 fetch 基址
    """有真 origin 用它，不透明 origin 用内部基址。"""
    try:#宿主可选 location
        定位=builtins.location#页面
    except AttributeError:#非浏览器
        定位=None#无
    原点=定位.origin if 定位 is not None else None#origin
    if 原点 is not None and 原点!='null':#真 origin
        return 原点#用它
    return 内部基址#假权威

def 断言目标(通道,端点):#校验通道与端点
    """通道名与端点各段必须合法。"""
    段列表=端点.split('/')#端点按段切开
    目标=通道+'/'+端点#拼
    if not 通道规则.fullmatch(通道):#通道名非法
        raise 连接错误('connection: invalid RPC target '+json.dumps(目标,ensure_ascii=False,separators=(',',':'),allow_nan=False))#调用前失败
    for 段 in 段列表:#任一段
        if 段=='' or 段=='.' or 段=='..' or 端点段规则.fullmatch(段) is None:#空段、相对段或非法字符
            raise 连接错误('connection: invalid RPC target '+json.dumps(目标,ensure_ascii=False,separators=(',',':'),allow_nan=False))#调用前失败

class 网页连接rpc:#浏览器 RPC 调用方
    """拥有请求关联与响应信封校验的调用方。"""
    def call(自身,通道,端点,载荷,信号=None):#经 HTTP POST 发一元 RPC
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
        请求=请求库.Request(地址,data=json.dumps(消息,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'),headers={'content-type':'application/json'},method='POST')#构造
        try:#发
            with 请求库.urlopen(请求) as 响应:#POST
                状态=响应.status#HTTP 状态
                if 状态<200 or 状态>=300:#HTTP 层失败
                    raise 连接错误(f'transport failure for {通道}/{端点}: HTTP {状态}')#传输失败
                正文=响应.read().decode('utf-8')#读正文
        except 连接错误:#已是本层
            raise#原样
        except OSError as 错误:#传输失败
            raise 连接错误(f'transport failure for {通道}/{端点}: {错误}') from 错误#包一层
        完整=服务端响应模式.parse(json.loads(正文))#校验服务端响应信封
        回显=完整['rpcId']#关联 id
        if 回显!=rpc标识:#关联必须对上
            raise 连接错误(f'rpcId mismatch for {端点}: sent {rpc标识}, got {回显}')#对不上则失败
        return 完整['result']#交出业务结果

def 创建网页连接rpc():#浏览器 RPC 调用方
    """创建拥有请求关联与响应信封校验的调用方。"""
    return 网页连接rpc()#实例
