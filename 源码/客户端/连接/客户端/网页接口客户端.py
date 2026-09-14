import builtins,json,time#全局、JSON、短等
import urllib.request as 请求库#标准库
from urllib.parse import urljoin,urlparse,urlunparse#拼基址与改协议
from ....host.apiproxy.接口.事件模式 import 宿主帧模式,复用帧模式#宿主/复用帧模式
from ....host.apiproxy.接口.rpc模式 import 服务端请求模式#服务端请求模式
from ..接口路径 import 宿主事件路径,复用事件路径#两条事件路径
from ..rpc import 连接错误,已中止#本包异常与中止
from .接口 import 抽象接口客户端#抽象 API 客户端

__all__=['网页接口客户端']#仅中文公开名

class 网页接口客户端(抽象接口客户端):#真实浏览器 API 客户端
    """浏览器平台子类：一元/应答用 fetch；mux/host 用仅下行 WebSocket。"""
    def doFetch(自身,输入,初始化=None):#一元请求走浏览器 fetch
        """标准 fetch 切面；无浏览器时用 urllib。"""
        初始化=初始化 if 初始化 is not None else {}#选项
        取=builtins.fetch if hasattr(builtins,'fetch') else None#可能有
        if callable(取):#有 fetch
            return 取(输入,初始化)#标准 fetch
        方法=初始化['method'] if 'method' in 初始化 else 'GET'#方法
        头=初始化['headers'] if 'headers' in 初始化 and 初始化['headers'] is not None else {}#头
        正文=初始化['body'] if 'body' in 初始化 else None#正文
        数据=正文.encode('utf-8') if isinstance(正文,str) else 正文#字节
        请求=请求库.Request(str(输入),data=数据,headers=头,method=方法)#构造
        响应=请求库.urlopen(请求)#发出
        return 响应#原始响应

    def openMux(自身,_载荷,信号,打开回调=None):#打开复用事件下行
        """读 mux 路径。"""
        return 自身._读网页套接字(复用事件路径,信号,复用帧模式,打开回调)#读 mux

    def openHost(自身,_载荷,信号,打开回调=None):#打开宿主事件下行
        """读 host 路径。"""
        return 自身._读网页套接字(宿主事件路径,信号,宿主帧模式,打开回调)#读 host

    def _读网页套接字(自身,路径,信号,帧模式,打开回调=None):#把一条仅下行 WebSocket 变成迭代
        """产出 RPC 信封；畸形帧丢掉。"""
        基=自身.resolveBase()#基址
        解析=urlparse(urljoin(基.rstrip('/')+'/',路径.lstrip('/')))#相对当前页解析
        协议='wss' if 解析.scheme=='https' else 'ws'#HTTP→WS，HTTPS→WSS
        地址=urlunparse((协议,解析.netloc,解析.path,解析.params,解析.query,解析.fragment))#套接字 URL
        收件箱=[]#已到未取的项
        结束旗={'done':False}#流结束
        套接字={'v':None}#稍后赋值

        def 入队(项):#入队
            """放入收件箱。"""
            收件箱.append(项)#放入

        def 处理打开(_事件=None):#套接字打开
            """打开回调。"""
            if callable(打开回调):#有回调
                打开回调()#通知

        def 处理消息(事件):#一条文本帧
            """线边界：畸形帧丢掉。"""
            try:#解析
                数据=事件 if isinstance(事件,str) else 事件.data#文本
                if not isinstance(数据,str):#不接受二进制
                    raise 连接错误('二进制 WebSocket 帧')#错
                完整=服务端请求模式.parse(json.loads(数据))#先当 JSON 再当 server-request
                载荷=完整['payload']#载荷
                帧=帧模式.parse(载荷)#再校验载荷变体
                rpc标识=完整['rpcId']#关联
            except (连接错误,json.JSONDecodeError,UnicodeDecodeError,KeyError,TypeError,ValueError) as 错误:#解析或模式失败
                print(f'[client-connection] 丢弃畸形 WebSocket 帧 {路径}:',错误)#大声丢掉
                return#本帧忽略
            自身.onEnvelope(完整)#让抽象客户端看见信封
            入队({'kind':'frame','envelope':{'rpcId':rpc标识,'payload':帧}})#入队给迭代器

        def 处理关闭(_事件=None):#套接字关则结束流
            """入队 end。"""
            入队({'kind':'end'})#结束
            结束旗['done']=True#标记

        def 处理中止(_事件=None):#取消时关掉仍活着的套接字
            """连接中或已开才 close。"""
            活=套接字['v']#当前
            if 活 is None:#尚未造
                return#完
            态=活.readyState#默认当开
            if 态 in (0,1) or 态 in ('CONNECTING','OPEN'):#连接中或已开
                活.close()#关

        try:#优先浏览器 WebSocket
            构造=builtins.WebSocket if hasattr(builtins,'WebSocket') else None#可能有
            if callable(构造):#有 WebSocket
                活=构造(地址)#打开
                套接字['v']=活#记下
                活.addEventListener('open',处理打开)#听打开
                活.addEventListener('message',处理消息)#听消息
                活.addEventListener('close',处理关闭)#听关闭
                if 已中止(信号):#已经取消则立刻关
                    处理中止()#关
            else:#无浏览器套接字：空流并立刻 onOpen，避免卡住握手
                if callable(打开回调):#有回调
                    打开回调()#视为已开
                入队({'kind':'end'})#结束
        except OSError as 错误:#打开失败
            print(f'[client-connection] WebSocket 打开失败 {路径}:',错误)#诊断
            if callable(打开回调):#仍通知打开超时路径
                打开回调()#避免永久卡住
            入队({'kind':'end'})#结束

        def 生成():#产出信封
            """直到 end。"""
            try:#把收件箱交给调用方
                while (not 结束旗['done']) or len(收件箱)>0:#直到排空且结束
                    while len(收件箱)>0:#先排空已到的
                        项=收件箱.pop(0)#取出队头
                        if 项['kind']=='end':#流结束
                            return#停
                        yield 项['envelope']#交出一帧
                    if 结束旗['done']:#已结束且空
                        return#停
                    if 已中止(信号):#取消
                        处理中止()#关
                        return#停
                    time.sleep(0.01)#等下一帧
            finally:#迭代结束或取消
                处理中止()#确保套接字关掉

        return 生成()#异步迭代的同步形
