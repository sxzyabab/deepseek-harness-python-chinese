"""worker 侧的 `node:http`：`createServer` 返回其 `listen` 立即成功且无套接字的
Server，并保留捕获的请求监听器，以便隧道服务器可将合成请求喂入真实路由表。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/http.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
__all__=[#中文与Node面
    '请求监听器','当请求监听器','服务器响应','创建服务器','请求','获取','状态码表','假服务器',
    'requestListener','whenRequestListener','ServerResponse','createServer','request','get',
    'STATUS_CODES','Server','__esModule','default',
]#公开结束

虚拟端口=3080#虚拟端口；成为 webServer.port
_已捕获=None#已捕获监听器
_等待们=set()#等待兑现集合

def 请求监听器():#取已捕获监听器
    """webserver 的请求监听器，一旦 `[Service.init]` 安装完毕。"""
    return _已捕获#可能仍空

def 当请求监听器():#等待监听器
    """等待请求监听器；已有则立即，否则登记 Promise。"""
    承诺类=globals().get('Promise')#Promise
    if _已捕获 is not None:#已有
        if callable(承诺类) and hasattr(承诺类,'resolve'): return 承诺类.resolve(_已捕获)#立即
        return _已捕获#同步交回
    def 执行(resolve,reject):#登记等待
        """一旦捕获即以监听器兑现。"""
        _等待们.add(resolve)#登记
    return 承诺类(执行)#返回Promise

class 假服务器:#假HTTP服务器
    """假 Server：事件注册被存储且从不发射。"""

    def __init__(自身):#构造
        """空监听表。"""
        自身._监听们={}#事件监听表

    def 监听(自身,事件,监听器):#注册监听器
        """注册事件监听器（`upgrade`、`error`）；从不发射。"""
        集合=自身._监听们.get(事件) or set()#取或新建
        集合.add(监听器)#加入
        自身._监听们[事件]=集合#写回
        return 自身#链式

    def 一次(自身,事件,监听器):#一次性注册
        """on 的一次性注册对应物。"""
        return 自身.监听(事件,监听器)#同监听存储

    def 取消监听(自身,事件,监听器):#移除监听器
        """移除监听器。"""
        集合=自身._监听们.get(事件)#取集合
        if 集合 is not None: 集合.discard(监听器)#删一项
        return 自身#链式

    def 听端口(自身,*参数):#假绑定
        """绑定：立即成功。回调必须运行。"""
        回调=参数[-1] if 参数 else None#尾部回调
        if callable(回调):#有回调
            微任务=globals().get('queueMicrotask')#微任务
            if callable(微任务): 微任务(回调)#异步成功
            else: 回调()#同步
        return 自身#链式

    def 地址(自身):#报告地址
        """隧道合成的回环权威。"""
        return {'address':'127.0.0.1','family':'IPv4','port':虚拟端口}#回环权威

    def 关闭(自身,回调=None):#假关闭
        """关闭：无套接字可释放。"""
        if 回调 is not None:#有回调
            微任务=globals().get('queueMicrotask')#微任务
            if callable(微任务): 微任务(回调)#异步完成
            else: 回调()#同步
        return 自身#链式

    def 关闭全部连接(自身):#关闭全部连接
        """从未接受过连接。"""
        pass#无连接

    def 关闭空闲连接(自身):#关闭空闲连接
        """也不存在空闲连接。"""
        pass#无连接

    on=监听#Node面
    once=一次#Node面
    off=取消监听#Node面
    listen=听端口#Node面
    address=地址#Node面
    close=关闭#Node面
    closeAllConnections=关闭全部连接#Node面
    closeIdleConnections=关闭空闲连接#Node面

class 服务器响应:#空响应类标记
    """中间件特性检测时读取的构造器标记。"""
    pass#空类

def 创建服务器(监听器=None):#创建假服务器
    """创建假服务器并为其保留请求监听器供隧道使用。"""
    global _已捕获#_已捕获
    if 监听器 is not None:#有监听器
        _已捕获=监听器#捕获
        for resolve in list(_等待们): resolve(监听器)#唤醒等待者
        _等待们.clear()#清空等待集
    return 假服务器()#返回假服务器

def 请求(*位置参数,**关键字参数):#出站request不可用
    """出站 HTTP 在 worker 中只有一个载体：`fetch`。"""
    raise Exception('web-preview: node:http.request is not available in the worker host — use fetch')#引导用fetch

def 获取(*位置参数,**关键字参数):#出站get不可用
    """同 request。"""
    raise Exception('web-preview: node:http.get is not available in the worker host — use fetch')#引导用fetch

状态码表={#状态文本表
    200:'OK',204:'No Content',304:'Not Modified',400:'Bad Request',#一批
    403:'Forbidden',404:'Not Found',405:'Method Not Allowed',413:'Payload Too Large',#续
    415:'Unsupported Media Type',426:'Upgrade Required',500:'Internal Server Error',503:'Service Unavailable',#续
}#状态码表结束

#Node面英文别名
requestListener=请求监听器#取监听器
whenRequestListener=当请求监听器#等待监听器
ServerResponse=服务器响应#响应类
createServer=创建服务器#创建服务器
request=请求#出站request
get=获取#出站get
STATUS_CODES=状态码表#状态码
Server=假服务器#Server别名
__esModule=True#CJS互操作标记
default={'createServer':创建服务器,'request':请求,'get':获取,'STATUS_CODES':状态码表,'Server':假服务器,'ServerResponse':服务器响应}#默认导出
