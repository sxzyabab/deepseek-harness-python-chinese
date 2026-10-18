'占住 webserver 回退席，按 distIndex 发 SPA'
import errno,os,re,urllib.parse#路径、缺失码与路径解码
from . import 异常#本包没有异常类，导入以执行同目录顶层

__all__=['名称','依赖','配置','应用','提供静态','异常']#同目录公开名

名称='frontend-static'#插件名
依赖=['webServer','connection']#回退席与索引认证

class 配置模式:#插件配置
    'distIndex 是 dist 里 index.html 的路径，必填'
    def 校验数据(自身,数据=None):#归一配置
        '必须是对象，且 distIndex 是字符串；其余键保留'
        if not isinstance(数据,dict):#不是对象
            raise TypeError('frontend-static: 配置必须是对象')#拒绝
        if 'distIndex' not in 数据 or not isinstance(数据['distIndex'],str):#缺或类型不对
            raise TypeError('frontend-static: distIndex 必须是字符串')#拒绝
        return dict(数据)#浅拷贝，其余键保留

配置=配置模式()#供纤程校验
网页类型='text/html; charset=utf-8'#索引类型
媒体类型={#扩展名到 Content-Type
    '.html':网页类型,#页面
    '.js':'text/javascript; charset=utf-8',#脚本
    '.css':'text/css; charset=utf-8',#样式
    '.svg':'image/svg+xml',#矢量
    '.json':'application/json',#json
    '.map':'application/json',#源映射
    '.webmanifest':'application/manifest+json',#清单
    '.gz':'application/gzip',#打包的 VFS，不当成 Content-Encoding
}#媒体类型结束
缺失码={errno.ENOENT,errno.EISDIR,errno.ENOTDIR}#不存在、是目录、路径中段不是目录

def 提供静态(路径名,响应,dist根,dist索引,认证索引,渲染索引):#发一条 GET 或 HEAD
    '越出 dist 根是 403；不存在或不是文件是 404；索引先认证再渲染'
    #路径名以 / 开头。拼上分隔符再规范化，避免 Windows 把 / 当成盘符根
    拼接=dist根+os.sep+路径名#对应 path.join
    目标=os.path.abspath(os.path.normpath(拼接))#对应 resolve
    if 目标!=dist根 and not 目标.startswith(dist根+os.sep):#越出根
        响应.writeHead(403)#禁止
        响应.end()#空体
        return#停
    try:#读索引或文件
        if 目标==dist根 or 目标==dist索引:#根或配置的索引
            if not 认证索引():#认证失败时对方已经写了响应
                return#停
            正文=渲染索引()#注入并插入 base
            类型=网页类型#html
        else:#普通资源
            with open(目标,'rb') as 文件:#按字节读
                正文=文件.read()#正文
            扩展=os.path.splitext(目标)[1]#扩展名
            if 扩展 in 媒体类型:#已知类型
                类型=媒体类型[扩展]#表内
            else:#未知扩展
                类型='application/octet-stream'#原样字节
    except OSError as 错误:#文件系统失败
        码=getattr(错误,'errno',None)#系统码
        是缺失=码 in 缺失码#ENOENT、EISDIR、ENOTDIR
        if not 是缺失 and isinstance(错误,PermissionError):#Windows 打开目录
            是缺失=os.path.isdir(目标)#与 Node 的 EISDIR 相同，算缺失
        if not 是缺失:#其它失败
            raise#交给 webserver
        响应.writeHead(404)#未找到
        响应.end()#空体
        return#停
    响应.writeHead(200,{'content-type':类型})#成功
    响应.end(正文)#正文

def 应用(上下文,配置值):#占回退席
    'dist 根是 distIndex 所在目录'
    dist索引=配置值['distIndex']#配置原文，不另做绝对化
    dist根=os.path.dirname(dist索引)#所在目录
    if dist根=='':#纯文件名
        dist根='.'#Node 的 dirname 在这里是 .
    def 渲染索引():#读索引并注入，再插入 base
        'base 放在 head 开标签后，排在其余资源引用之前'
        with open(dist索引,'r',encoding='utf-8',errors='replace') as 文件:#Node 的 utf8 会替换非法字节
            原文=文件.read()#文本
        正文=上下文.webServer.renderIndex(原文)#结构化注入，再跑 tap
        return re.sub(r'(<head(?:\s[^>]*)?>)',r'\1<base href="./">',正文,count=1,flags=re.I)#只换第一处
    def 回退(请求,响应):#未命中具名路由
        '非 GET/HEAD 是 405'
        if 请求.method!='GET' and 请求.method!='HEAD':#方法不对
            响应.writeHead(405)#不允许
            响应.end()#空体
            return#停
        网址=请求.url if 请求.url else '/'#没有 url 时当作 /
        原始=urllib.parse.urlparse(网址).path#pathname，不含查询
        def 认证索引():#索引认证
            '失败时 connection 已经写了响应'
            return 上下文.connection.authorizeIndex(请求,响应)#是否可发索引
        提供静态(urllib.parse.unquote(原始),响应,dist根,dist索引,认证索引,渲染索引)#发文件
    def 占席():#登记回退
        '把回退席交给静态服务，拆除时让出'
        return 上下文.webServer.registerFallback(回退)#拆除器
    上下文.副作用(占席,'frontend-static: fallback seat')#卸载时让出席

name=名称#框架槽
inject=依赖#框架槽
Config=配置#框架槽
apply=应用#框架槽
