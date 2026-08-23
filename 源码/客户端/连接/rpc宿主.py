"""通用 Connection RPC 通道的宿主注册表与 HTTP 适配器。

对齐上游 `connection/src/rpc-host.ts`。公开面仅中文名。
"""
import json,re#JSON 与通道名校验
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
是否thenable=cordis.工具.是否thenable#可等待判定
from .http桥 import 桥接#HTTP 桥
from .接口请求信任 import 是否受信任接口请求#请求信任闸
from .接口路径 import 接口路径#/api 路径常量
from .rpc import 连接权威_回环#回环权威

__all__=['宿主连接服务']#仅中文公开名

通道规则=re.compile(r'^/[A-Za-z0-9._~-]+$')#独占通道：单段绝对路径
端点段规则=re.compile(r'^[A-Za-z0-9_$.-]+$')#端点每一段允许的字符
无效请求标识='invalid-request'#信封无效时的占位 rpcId

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 路径切端点(通道,路径名):#路径切相对端点
    """从绝对路径切出通道相对端点。"""
    前缀=通道+'/'#通道前缀
    if not 路径名.startswith(前缀):#不是该通道前缀
        return None#不当端点
    端点=路径名[len(前缀):]#去掉通道与斜杠
    段们=端点.split('/')#按段切开
    for 段 in 段们:#任一段非法则整条拒绝
        if 段=='' or 段=='.' or 段=='..' or 端点段规则.fullmatch(段) is None:#空段、相对段或非法字符
            return None#不当端点
    return 端点#合法相对端点

def 断言通道(通道):#独占通道名必须合法且不得占用 /api
    """拒绝 /api 与畸形通道名。"""
    if 通道规则.fullmatch(通道) is None or 通道=='/api':#畸形或保留名
        raise Exception('connection: invalid or reserved RPC channel '+json.dumps(通道,ensure_ascii=False))#加载/登记时失败

def 完整响应(rpc标识,结果):#成功或失败都写成 server-response
    """包成 server-response JSON 响应。"""
    体={'type':'server-response','rpcId':rpc标识,'result':结果}#标准信封
    return {'status':200,'headers':{'content-type':'application/json; charset=utf-8'},'body':json.dumps(体,ensure_ascii=False).encode('utf-8')}#JSON 响应

def 错误响应(rpc标识,错误):#失败结果包成 HTTP JSON
    """失败结果。"""
    return 完整响应(rpc标识,{'ok':False,'error':错误})#ok:false 加 error

def rpcFetch处理(通道,处理函数):#把 RPC handler 适配成 FetchHandler
    """解码信封并调 handler。"""
    def fetch(请求):#处理一条 POST
        """处理一条标准 Fetch 请求。"""
        网址=取字段(请求,'url','')#url
        try:#解析路径
            from urllib.parse import urlparse#解析
            路径名=urlparse(网址).path#路径
        except Exception:#畸形
            路径名='/'#回退
        端点=路径切端点(通道,路径名)#路径 → 端点
        if 取字段(请求,'method')!='POST' or 端点 is None:#只接受合法 POST 端点
            return {'status':404,'headers':{},'body':b'not found'}#其它 404
        头们=取字段(请求,'headers',{}) or {}#头
        内容类型=头们.get('content-type') or 头们.get('Content-Type') or ''#内容类型
        媒体=内容类型.split(';',1)[0].strip().lower()#去掉参数的媒体类型
        if 媒体!='application/json':#必须是 JSON
            return {'status':415,'headers':{},'body':b'content type must be application/json'}#不支持的媒体类型
        体字节=取字段(请求,'body',None)#正文
        try:#正文可能不是 JSON
            if 体字节 is None:#空
                体=None#空
            elif isinstance(体字节,(bytes,bytearray)):#字节
                体=json.loads(体字节.decode('utf-8'))#解析
            elif isinstance(体字节,str):#文本
                体=json.loads(体字节)#解析
            else:#已是对象
                体=体字节#原样
        except Exception:#JSON 语法错误
            return {'status':400,'headers':{},'body':b'body is not JSON'}#坏请求
        if not isinstance(体,dict):#信封须是对象
            return 错误响应(无效请求标识,{'code':'bad-request','message':'invalid client-request message','details':{'issues':[]}})#坏信封
        rpc标识=体.get('rpcId')#关联 id
        方法=体.get('method')#方法
        载荷=体.get('payload')#载荷
        if not isinstance(rpc标识,str) or not isinstance(方法,str):#字段不合格
            用标识=rpc标识 if isinstance(rpc标识,str) else 无效请求标识#尽量保住
            return 错误响应(用标识,{'code':'bad-request','message':'invalid client-request message','details':{'issues':[]}})#坏信封
        if 方法!=端点:#信封 method 必须与路径端点一致
            return 错误响应(rpc标识,{'code':'bad-request','message':'method '+json.dumps(方法,ensure_ascii=False)+' does not match endpoint '+json.dumps(端点,ensure_ascii=False),'details':{'issues':[]}})#不一致
        try:#调用业务 handler
            信号=取字段(请求,'signal')#取消信号
            结果=解开(处理函数(端点,载荷,信号))#带取消信号
            return 完整响应(rpc标识,结果)#包成 server-response
        except Exception as 错误:#handler 抛错
            return {'status':500,'headers':{},'body':('handler failure: '+str(错误)).encode('utf-8')}#内部错误
    return {'fetch':fetch}#处理器对象

class 宿主连接服务(服务):#提供 ctx.connection
    """宿主 Connection 服务，通道登记属于调用方光纤。"""

    def __init__(自身,上下文,受信任主机表):#绑定上下文与受信任 Host
        """在活动 HTTP 服务器上提供宿主半边。"""
        super().__init__(上下文,'connection')#服务名 connection
        自身.受信任主机表=list(受信任主机表)#部署权威
        自身.拦截器表={}#共享通道 → 拦截器

    @property#登记面
    def rpc(自身):#每次取都闭包当前 ctx
        """作用域落在读取本服务的 Context 上的通用通道注册表。"""
        拥有=自身.ctx#调用方光纤上下文
        return {#登记面
            'handle':lambda 通道,处理,选项:自身.登记(拥有,通道,处理,选项),#独占通道
            'intercept':lambda 通道,匹配,处理,选项:自身.登记拦截器(拥有,通道,匹配,处理,选项),#共享通道拦截
        }#结束返回

    def createSharedFetchHandler(自身,通道,回退):#组合共享通道
        """由拦截器与回退组成一条共享通道的 Fetch 处理器。"""
        def fetch(请求):#按路径选拦截器或回退
            """每条请求恰好选一个目标。"""
            try:#解析路径
                from urllib.parse import urlparse#解析
                路径名=urlparse(取字段(请求,'url','')).path#路径
            except Exception:#畸形
                路径名='/'#回退
            端点=路径切端点(通道,路径名)#切出相对端点
            拦截器=自身.拦截器表.get(通道)#该通道的拦截器
            if 端点 is None or 拦截器 is None or not 拦截器['matches'](端点):#未声称
                return 回退.fetch(请求)#走回退
            if 取字段(拦截器['options'],'authority')==连接权威_回环 and (not 是否受信任接口请求(请求,[])):#拦截器钉回环
                return {'status':403,'headers':{},'body':b'forbidden'}#非回环 403
            return 拦截器['fetchHandler'].fetch(请求)#交给拦截器
        return {'fetch':fetch}#处理器

    def 登记(自身,拥有,通道,处理函数,选项):#登记一条独占 RPC 通道
        """登记绝对通道前缀及其信任政策。"""
        断言通道(通道)#拒绝 /api 与畸形通道名
        权威=取字段(选项,'authority')#信任级别
        受信任= [] if 权威==连接权威_回环 else 自身.受信任主机表#回环则空名单
        fetch处理=rpcFetch处理(通道,处理函数)#解码信封并调 handler
        def 路由处理(请求,响应):#每条该前缀请求
            """信任闸后桥接。"""
            if not 是否受信任接口请求(请求,受信任):#未过信任围栏
                响应.writeHead(403)#禁止
                响应.end('forbidden')#正文
                return#不桥接
            桥接(请求,响应,fetch处理)#Node HTTP → fetch
        路由={'kind':'prefix','path':通道,'handler':路由处理}#HTTP 前缀路由
        return 拥有.effect(lambda:拥有.webServer.register(路由),'client-connection: '+通道+' rpc channel')#登记归调用方光纤

    def 登记拦截器(自身,拥有,通道,匹配,处理函数,选项):#在共享通道上登记拦截器
        """在共享 /api 通道的回退之前拦截所拥有的端点。"""
        if 通道!=接口路径:#只允许保留的共享通道
            raise Exception('connection: invalid shared RPC channel '+json.dumps(通道,ensure_ascii=False))#其它通道名失败
        拦截器={#组装拦截器
            'matches':匹配,#所有权谓词
            'fetchHandler':rpcFetch处理(通道,处理函数),#解码并调 handler
            'options':选项,#信任政策
        }#结束拦截器
        def 效应():#归调用方光纤
            """写入表；拆除时删除。"""
            if 通道 in 自身.拦截器表:#同一通道只能有一个拦截器
                raise Exception('connection: shared RPC channel '+json.dumps(通道,ensure_ascii=False)+' already has an interceptor')#重复登记失败
            自身.拦截器表[通道]=拦截器#写入表
            def 拆除():#拆除
                """从表删除。"""
                自身.拦截器表.pop(通道,None)#删除
            return 拆除#拆除器
        return 拥有.effect(效应,'client-connection: '+通道+' rpc interceptor')#effect 名
