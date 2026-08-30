"""浏览器客户端 RPC 的宿主 HTTP 桥。

对齐上游 `@deepseek-ai/dsh-client-connection`。公开面仅中文名。配置键英文字面量保持上游。
"""
from ...依赖 import schemastery#配置字段
列表字段=schemastery.列表字段#配置字段
字符串字段=schemastery.字符串字段#配置字段
自然数字段=schemastery.自然数字段#配置字段
from .接口路径 import 接口路径,复用事件路径,宿主事件路径#API 与事件路径常量
from .http桥 import 桥接,默认最大请求正文字节#HTTP 桥与默认正文上限
from .接口请求信任 import 断言受信任权威,是否受信任接口请求#权威校验与请求信任闸
from .rpc宿主 import 宿主连接服务#宿主连接服务
from .网页套接字下行 import 拒绝网页套接字升级,网页套接字下行#WebSocket 下行与拒绝升级
from .rpc import 连接权威_受信任宿主,连接权威_回环#再导出权威常量

__all__=[#仅中文公开名
    '名称',
    '注入',
    '配置',
    '应用',
    '宿主连接服务',
    '接口路径',
    '复用事件路径',
    '宿主事件路径',
    '连接权威_受信任宿主',
    '连接权威_回环',
]#公开面结束

名称='client-connection'#插件名
注入=['webServer']#只硬依赖 web 服务器
请求信封余量字节=1024*1024#信封余量 1MiB
配置={#连接插件配置
    'trustedHosts':列表字段(字符串字段(),默认值=[]),#默认无额外受信任 Host
    'maxRequestBodyBytes':自然数字段(最小=1,默认值=默认最大请求正文字节),#至少 1 字节，默认桥常量
}#配置模式结束

特权方法=set([#回环闸方法名
    'agentPreset.read',#读预设组合
    'agentPreset.copy',#复制预设
    'agentPreset.openDocument',#打开预设文档
    'agentPreset.remove',#删除预设
    'host.pickDirectory',#宿主选目录
    'host.openPath',#宿主打开路径
    'settings.describe',#描述设置
    'settings.openDocument',#打开设置文档
    'settings.update',#更新设置
    'settings.replace',#替换设置
    'settings.mutate',#变更设置
    'credentials.describe',#描述凭证
    'credentials.set',#设置凭证
    'credentials.unset',#清除凭证
    'llm.discoverModels',#发现模型（会让宿主发 GET）
])#特权方法结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 断言图像正文容量(上下文,最大请求正文字节):#正文上限必须装得下合计图像
    """有附件服务时核图像容量。"""
    附件=上下文.get('attachments')#可选附件服务
    if 附件 is None:#没有附件服务则不检查
        return#跳过
    图像上限=取字段(取字段(附件,'imageLimits'),'maxMessageImageBytes')#合计图像上限
    所需=int(图像上限*4/3)+请求信封余量字节#base64 膨胀后再加信封余量
    if 最大请求正文字节<所需:#配置上限不够
        raise Exception('client-connection maxRequestBodyBytes ('+str(最大请求正文字节)+') must be at least '+str(所需)+' for the configured aggregate image limit')#加载期大声失败

def 经网关fetch(网关,请求):#对齐上游 toFetchHandler(apiProxy).fetch
    """把请求交给网关的 fetch 面。"""
    from ...host.apiproxy import 转fetch处理#宿主网关 → fetch 面（对齐上游 toFetchHandler）
    return 转fetch处理(网关).fetch(请求)#派发

def 应用(上下文,配置值=None):#安装连接插件
    """把 API 网关挂到浏览器传输前缀下。"""
    受信任主机表=取字段(配置值,'trustedHosts',[]) if 配置值 is not None else []#受信任 Host，缺省空
    最大请求正文字节=取字段(配置值,'maxRequestBodyBytes',默认最大请求正文字节) if 配置值 is not None else 默认最大请求正文字节#正文上限
    for 条目 in 受信任主机表:#逐条校验权威形态
        断言受信任权威(条目)#畸形条目加载失败
    if 上下文.get('apiProxy') is not None:#有网关才核图像容量
        断言图像正文容量(上下文,最大请求正文字节)#核图像容量
    连接=宿主连接服务(上下文,受信任主机表)#宿主连接服务
    def 回退fetch(请求):#处理未命中 RPC 的 /api 请求
        """共享 fetch 回退。"""
        from urllib.parse import urlparse#取路径
        路径名=urlparse(取字段(请求,'url','')).path#取出路径
        方法名=None#方法名
        if 路径名.startswith(接口路径+'/'):#是否 /api/<method>
            方法名=路径名[len(接口路径)+1:]#切出方法名
        if 方法名 is not None and 方法名 in 特权方法 and (not 是否受信任接口请求(请求,[])):#特权方法钉回环
            return {'status':403,'headers':{},'body':b'forbidden'}#非回环拒绝
        if 取字段(请求,'method')=='GET' and (路径名==复用事件路径 or 路径名==宿主事件路径):#事件路径的普通 GET
            return {'status':426,'headers':{'connection':'Upgrade','upgrade':'websocket'},'body':b'upgrade required'}#要求升级为 WebSocket
        网关=上下文.get('apiProxy')#可选 API 网关
        if 网关 is None:#没有网关则 404
            return {'status':404,'headers':{},'body':b'not found'}#404
        return 经网关fetch(网关,请求)#交给网关 fetch 面
    共享处理=连接.createSharedFetchHandler(接口路径,{'fetch':回退fetch})#共享 fetch 回退
    def 路由处理(请求,响应):#每条 /api 请求
        """信任围栏后桥接。"""
        if not 是否受信任接口请求(请求,受信任主机表):#Host 不在回环也不在名单
            响应.writeHead(403)#禁止
            响应.end('forbidden')#正文
            return#不再桥接
        桥接(请求,响应,共享处理,最大请求正文字节)#Node HTTP → fetch 桥
    路由={'kind':'prefix','path':接口路径,'handler':路由处理}#HTTP 前缀路由
    上下文.effect(lambda:上下文.webServer.register(路由),'client-connection: /api route')#登记 /api 路由
    def 挂下行(网关上下文):#等 apiProxy 出现再挂 WebSocket 下行
        """登记 mux/host 下行。"""
        断言图像正文容量(网关上下文,最大请求正文字节)#网关在时再核一次图像容量
        下行=网页套接字下行(网关上下文.apiProxy)#事件下行
        def 登记下行(路径,处理):#登记一条带信任闸的升级路由
            """安装升级路由。"""
            def 升级处理(请求,套接字,头):#升级请求
                """信任闸后交给下行。"""
                if not 是否受信任接口请求(请求,受信任主机表):#未过信任围栏
                    拒绝网页套接字升级(套接字)#拒绝握手
                    return#不升级
                return 处理(请求,套接字,头)#交给 mux/host 下行
            return 网关上下文.webServer.registerUpgrade({'path':路径,'handler':升级处理})#登记 WebSocket 升级
        def 下行效应():#下行生命周期
            """登记两条升级并在拆除时关掉下行。"""
            拆复用=登记下行(复用事件路径,下行.handleMux)#复用事件通道
            拆宿主=登记下行(宿主事件路径,下行.handleHost)#宿主事件通道
            def 拆除():#拆除
                """取消升级并关下行。"""
                拆复用()#拆复用
                拆宿主()#拆宿主
                下行.close()#关掉下行
            return 拆除#拆除器
        网关上下文.effect(下行效应,'client-connection: WebSocket downlinks')#拆除时关掉下行
    上下文.inject(['apiProxy'],挂下行)#等 apiProxy 出现
