"""Web 路由登记插件：一个 HTTP 服务器加上 `webServer` 服务。

对齐上游 `@deepseek-ai/dsh-host-webserver`。公开面仅中文名。HTTP 与 upgrade 路由表、index 变换 tap、以及无路由申领时的唯一兜底席位。本包默认导出服务类。配置键与诊断英文字面量保持上游。
"""
import socket,threading#监听套接字与请求线程
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer#HTTP 处理
from urllib.parse import urlsplit#取路径
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
枚举字段=schemastery.枚举字段#配置字段
自然数字段=schemastery.自然数字段#配置字段
服务=cordis.服务#服务基类

__all__=['网页服务器','网页路由种类','配置']#仅中文公开名

网页路由种类=('exact','prefix')#精确或前缀
配置={#listen 用的主机与端口
    'host':枚举字段('127.0.0.1','0.0.0.0',可空=False),#仅环回或全部接口
    'port':自然数字段(最大=65535,可空=False),#含 0 的自然数
}#配置结束

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

class 网页服务器(服务):#HTTP 路由登记与监听
    """浏览器 HTTP 载体服务。激活后立刻监听。具名路由必须互异；未申领时兜底 404。"""
    Config=配置#Cordis 配置
    配置=配置#中文别名
    inject=[]#无额外注入
    注入=[]#中文别名

    def __init__(自身,上下文,配置值):#按上下文与已校验配置构造
        """登记为 ctx.webServer。"""
        super().__init__(上下文,'webServer')#服务名
        自身.配置值=配置值#已校验配置
        自身.精确={}#精确路径表
        自身.前缀={}#前缀路径表
        自身.升级={}#精确 upgrade 表
        自身.已升级套接字=set()#已升级套接字
        自身.索引变换们=[]#index.html 变换
        自身.兜底=None#唯一兜底席位
        自身.服务器=None#listen 后才有
        自身.已监听端口=None#实际绑定端口
        自身._锁=threading.Lock()#路由表互斥

    @property#实际绑定端口
    def port(自身):#正在监听的端口
        """config.port 为 0 时是 OS 分配值。"""
        return 自身.已监听端口#listen 成功后才有

    @property#绑定主机
    def host(自身):#配置的绑定主机
        """环回或全部接口字面量。"""
        return 取字段(自身.配置值,'host')#配置封闭联合

    def register(自身,路由):#登记一条具名 HTTP 路由
        """重复的 (kind, path) 会抛。返回拆除器。"""
        种类=取字段(路由,'kind')#exact 或 prefix
        路径=取字段(路由,'path')#登记路径
        表=自身.精确 if 种类=='exact' else 自身.前缀#目标表
        with 自身._锁:#互斥
            if 路径 in 表:#已有主人
                raise Exception('webserver: duplicate '+种类+' route "'+路径+'"')#组合错误
            表[路径]=路由#占住
        def 拆除():#移除该路由
            """卸载时释放。"""
            with 自身._锁:#互斥
                表.pop(路径,None)#删除
        return 拆除#disposer

    def registerUpgrade(自身,路由):#登记精确 upgrade 路由
        """重复路径会抛。返回拆除器。"""
        路径=取字段(路由,'path')#精确路径
        with 自身._锁:#互斥
            if 路径 in 自身.升级:#已有主人
                raise Exception('webserver: duplicate upgrade route "'+路径+'"')#冲突
            自身.升级[路径]=路由#占住
        def 拆除():#移除
            """卸载时释放。"""
            with 自身._锁:#互斥
                自身.升级.pop(路径,None)#删除
        return 拆除#disposer

    def registerFallback(自身,处理器):#申领唯一兜底席位
        """第二次登记会抛。返回拆除器。"""
        with 自身._锁:#互斥
            if 自身.兜底 is not None:#已有主人
                raise Exception('webserver: fallback already registered')#无法组合
            自身.兜底=处理器#占住
        def 拆除():#释放席位
            """卸载时释放。"""
            with 自身._锁:#互斥
                自身.兜底=None#清空
        return 拆除#disposer

    def tapIndex(自身,变换):#登记 index.html 变换
        """按登记顺序应用。返回拆除器。"""
        自身.索引变换们.append(变换)#追加
        def 拆除():#按引用移除
            """允许同一函数只卸一次。"""
            try:#找这一次
                自身.索引变换们.remove(变换)#摘掉
            except ValueError:#已不在
                return#忽略
        return 拆除#disposer

    def applyIndexTaps(自身,网页):#顺序应用全部 index tap
        """按登记顺序把 index.html 正文跑过已登记的 tap。"""
        出=网页#从原文开始
        for 变换 in 自身.索引变换们:#流水线
            出=变换(出)#应用
        return 出#变换后正文

    def 匹配(自身,路径名):#先精确，再最长前缀
        """精确表未命中后，前缀表里最长前缀获胜。"""
        with 自身._锁:#互斥读
            if 路径名 in 自身.精确:#精确命中
                return 自身.精确[路径名]#精确优先
            最佳=None#当前最长前缀
            for 前缀,路由 in 自身.前缀.items():#扫描
                if 路径名!=前缀 and not 路径名.startswith(前缀+'/'):#不是该前缀
                    continue#跳过
                if 最佳 is None or len(前缀)>len(取字段(最佳,'path')):#更长者
                    最佳=路由#更新
            return 最佳#可能仍无

    def _初始化(自身):#激活时立刻 listen（光纤在依赖就绪后调用）
        """监听；套接字绑定后返回（失败 = FAILED fiber）。"""
        拥有=自身#闭包服务
        class 处理器(BaseHTTPRequestHandler):#把请求交给路由表
            """按路径匹配具名路由或兜底。"""
            def log_message(自身2,格式,*参数):#静默
                """本包从不打印。"""
                return#外壳才打 URL
            def do_GET(自身2):#GET
                """处理 GET。"""
                自身2._派发()#统一派发
            def do_HEAD(自身2):#HEAD
                """处理 HEAD。"""
                自身2._派发()#统一派发
            def do_POST(自身2):#POST
                """处理 POST。"""
                自身2._派发()#统一派发
            def do_PUT(自身2):#PUT
                """处理 PUT。"""
                自身2._派发()#统一派发
            def do_DELETE(自身2):#DELETE
                """处理 DELETE。"""
                自身2._派发()#统一派发
            def do_OPTIONS(自身2):#OPTIONS
                """处理 OPTIONS。"""
                自身2._派发()#统一派发
            def do_PATCH(自身2):#PATCH
                """处理 PATCH。"""
                自身2._派发()#统一派发
            def _派发(自身2):#匹配并调用
                """畸形请求收成 400，绝不退出进程。"""
                try:#单次请求
                    原始=urlsplit(自身2.path).path or '/'#取出路径
                    路由=拥有.匹配(原始)#先精确后前缀
                    if 路由 is not None:#具名命中
                        解开(取字段(路由,'handler')(自身2.请求包装(),自身2.响应包装()))#交给路由
                        return#不再兜底
                    兜底=拥有.兜底#可能尚未登记
                    if 兜底 is None:#无主人
                        自身2.send_response(404)#未申领
                        自身2.end_headers()#无正文
                        return#结束
                    解开(兜底(自身2.请求包装(),自身2.响应包装()))#交给兜底
                except BaseException as 错误:#单次失败
                    拥有.ctx.logger.warn(错误 if isinstance(错误,Exception) else Exception(str(错误)))#记警告
                    try:#尽量 400
                        自身2.send_response(400)#畸形
                        自身2.end_headers()#无正文
                    except BaseException:#已无法写
                        return#放弃
            def 请求包装(自身2):#最小请求面
                """对齐 node IncomingMessage 的 method/url。"""
                return _请求(自身2.command,自身2.path)#方法与路径
            def 响应包装(自身2):#最小响应面
                """对齐 node ServerResponse 的 writeHead/end。"""
                return _响应(自身2)#包装处理器
        主机=取字段(自身.配置值,'host')#绑定主机
        端口=取字段(自身.配置值,'port')#配置端口
        try:#绑定
            自身.服务器=ThreadingHTTPServer((主机,端口),处理器)#创建服务器
        except OSError as 错误:#绑定失败
            raise 错误#拒绝 init
        自身.已监听端口=自身.服务器.server_address[1]#实际端口
        线程=threading.Thread(target=自身.服务器.serve_forever,daemon=True)#后台服务
        线程.start()#开始接受
        def 拆除():#关服务器
            """拆除：关服务器。"""
            if 自身.服务器 is not None:#仍活着
                自身.服务器.shutdown()#停止接受
                自身.服务器.server_close()#关套接字
        自身.ctx.effect(lambda:拆除,'webServer.listen')#拆除 effect
        return#init 成功

class _请求:#最小请求包装
    """对齐上游 handler 所见的 req.method / req.url。"""
    def __init__(自身,方法,网址):#记下
        """方法与路径。"""
        自身.method=方法#HTTP 方法
        自身.url=网址#路径含查询

class _响应:#最小响应包装
    """对齐 writeHead / end / destroy。"""
    def __init__(自身,处理器):#绑到底层处理器
        """记下 BaseHTTPRequestHandler。"""
        自身._处理器=处理器#底层
        自身._已写头=False#是否已 writeHead
    def writeHead(自身,状态,头们=None):#写响应头
        """写入状态码与可选头。"""
        自身._处理器.send_response(状态)#状态
        if 头们:#有头
            for 键,值 in 头们.items():#逐个
                自身._处理器.send_header(键,值)#头
        自身._处理器.end_headers()#结束头
        自身._已写头=True#记下
    def end(自身,正文=None):#结束响应
        """写出可选正文。"""
        if not 自身._已写头:#尚未写头
            自身.writeHead(200)#默认 200
        if 正文 is None:#无正文
            return#结束
        if isinstance(正文,str):#文本
            自身._处理器.wfile.write(正文.encode('utf-8'))#编码写出
        else:#字节
            自身._处理器.wfile.write(正文)#原样写出
    def destroy(自身):#拆掉连接
        """关闭底层连接。"""
        try:#尽量关
            自身._处理器.connection.close()#拆套接字
        except BaseException:#忽略
            return#已拆

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性
