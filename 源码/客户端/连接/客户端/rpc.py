import builtins,json,re#全局、JSON 与形态校验
import urllib.request as 请求库#标准库 fetch 形
from urllib.parse import urljoin as 拼接URL
from ..rpc import Rpc标识#RPC id
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

def 是否记录(值):
    """普通对象记录。"""
    return isinstance(值,dict)#dict

def 解析连接响应(值):
    """校验 server-response 信封并交出 rpcId 与业务结果。"""
    if not 是否记录(值) or ('type' not in 值) or 值['type']!='server-response' or ('rpcId' not in 值) or type(值['rpcId']) is not str:#信封
        raise TypeError('connection: invalid server-response envelope')#失败
    结果=值['result'] if 'result' in 值 else None#结果
    if not 是否记录(结果):#须对象
        raise TypeError('connection: invalid server-response result')#失败
    if ('ok' in 结果) and 结果['ok'] is True:#成功
        return {'rpcId':Rpc标识(值['rpcId']),'result':{'ok':True,'value':结果['value'] if 'value' in 结果 else None}}#成功槽
    if ('ok' not in 结果) or 结果['ok'] is not False or ('error' not in 结果) or (not 是否记录(结果['error'])):#失败槽
        raise TypeError('connection: invalid server-response result')#失败
    错误=结果['error']#错误
    if ('code' not in 错误) or type(错误['code']) is not str or ('message' not in 错误) or type(错误['message']) is not str or ('details' not in 错误) or (not 是否记录(错误['details'])):#失败形态
        raise TypeError('connection: invalid server-response failure')#失败
    return {'rpcId':Rpc标识(值['rpcId']),'result':{'ok':False,'error':{'code':错误['code'],'message':错误['message'],'details':错误['details']}}}#失败槽

class 网页响应:#标准库 POST 的响应面
    """对齐 fetch Response 的 ok/status/json。"""
    def __init__(自身,状态,正文):
        """记下状态与正文。"""
        自身.status=状态#HTTP 状态
        自身.ok=状态>=200 and 状态<300#成功
        自身._正文=正文#正文

    def json(自身):
        """解析 JSON 正文。"""
        return json.loads(自身._正文)#对象

def 默认发送(地址,初始化):
    """页面缺省 unary：标准库 POST。"""
    正文=初始化['body'] if 'body' in 初始化 else ''#正文
    头=初始化['headers'] if 'headers' in 初始化 else {}#头
    请求=请求库.Request(地址,data=正文.encode('utf-8') if type(正文) is str else 正文,headers=头,method=初始化['method'] if 'method' in 初始化 else 'POST')#构造
    try:#发
        with 请求库.urlopen(请求) as 响应:#POST
            return 网页响应(响应.status,响应.read().decode('utf-8'))#响应面
    except OSError as 错误:#传输失败
        raise 连接错误('transport failure: '+str(错误)) from 错误#包一层

class 网页连接rpc:#浏览器 RPC 调用方
    """拥有请求关联与响应信封校验的调用方。"""
    def __init__(自身,发送):
        """绑定 unary 发送。"""
        自身.发送=发送#fetch 形

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
        地址=拼接URL(解析基址().rstrip('/')+'/',通道.strip('/')+'/'+端点)
        初始化={#fetch init
            'method':'POST',#方法
            'headers':{'content-type':'application/json'},#头
            'body':json.dumps(消息,ensure_ascii=False,separators=(',',':'),allow_nan=False),#正文
        }#结束
        if 信号 is not None:#有中止
            初始化['signal']=信号#带上
        响应=自身.发送(地址,初始化)#发送
        if not 响应.ok:#HTTP 层失败
            raise 连接错误('transport failure for '+通道+'/'+端点+': HTTP '+str(响应.status))#传输失败
        完整=解析连接响应(响应.json())#校验服务端响应信封
        回显=完整['rpcId']#关联 id
        if 回显!=rpc标识:#关联必须对上
            raise 连接错误('rpcId mismatch for '+端点+': sent '+str(rpc标识)+', got '+str(回显))#对不上则失败
        return 完整['result']#交出业务结果

def 创建网页连接rpc(执行fetch=None,打开流=None):#浏览器 RPC 调用方
    """创建拥有请求关联与响应信封校验的调用方。可选覆盖 fetch 与 worker 流载体。"""
    调用方=网页连接rpc(执行fetch if 执行fetch is not None else 默认发送)#实例
    if 打开流 is not None:#worker 本地流
        def 打开(通道,端点,载荷,信号=None):#打开流
            """worker 本地 Gateway 流。"""
            断言目标(通道,端点)#形态
            if 通道!='/api':#通道必须是 /api
                raise 连接错误('connection: worker-local streams require the /api channel, got '+json.dumps(通道,ensure_ascii=False,separators=(',',':'),allow_nan=False))#抛
            return 打开流(端点,载荷,信号)#委托
        调用方.open=打开#挂上
    return 调用方#实例
