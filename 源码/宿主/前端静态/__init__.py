'占住 webserver 回退席，按 distIndex 发 SPA'
import errno,os,re,urllib.parse#路径、缺失码与路径解码
from ...依赖.schemastery import 字符串字段#配置字段

__all__=['名称','依赖','配置','应用','提供静态']#仅中文公开名

名称='frontend-static'#插件名
依赖=['webServer','connection']#回退席与索引认证
配置={#插件配置
    'distIndex':字符串字段(),#dist 里 index.html 的绝对路径
}#配置结束
网页类型='text/html; charset=utf-8'#索引类型
媒体类型={#扩展名
    '.html':网页类型,#页面
    '.js':'text/javascript; charset=utf-8',#脚本
    '.css':'text/css; charset=utf-8',#样式
    '.svg':'image/svg+xml',#矢量
    '.json':'application/json',#json
    '.map':'application/json',#源映射
    '.webmanifest':'application/manifest+json',#清单
    '.gz':'application/gzip',#打包的 VFS，不当成 Content-Encoding
}#结束
缺失码={errno.ENOENT,errno.EISDIR,errno.ENOTDIR}#不存在或不是文件

def 提供静态(路径名,响应,dist根,dist索引,认证索引,渲染索引):#发一条 GET/HEAD
    '越出 dist 根是 403；缺失是 404；索引先认证再渲染'
    相对=路径名.lstrip('/').replace('/',os.sep)#相对 dist
    目标=os.path.abspath(os.path.normpath(os.path.join(dist根,相对)))#绝对
    if 目标!=dist根 and not 目标.startswith(dist根+os.sep):#越界
        响应.writeHead(403)#禁止
        响应.end()#结束
        return#停
    try:#读
        if 目标==dist根 or 目标==dist索引:#索引
            if not 认证索引():#认证失败时对方已经写了响应
                return#停
            正文=渲染索引()#注入后的 HTML
            类型=网页类型#html
        else:#普通资源
            with open(目标,'rb') as 文件:#读
                正文=文件.read()#字节
            扩展=os.path.splitext(目标)[1]#扩展名
            类型=媒体类型[扩展] if 扩展 in 媒体类型 else 'application/octet-stream'#类型
    except OSError as 错误:#文件系统
        if getattr(错误,'errno',None) not in 缺失码:#不是缺失
            raise#交给 webserver
        响应.writeHead(404)#未找到
        响应.end()#结束
        return#停
    响应.writeHead(200,{'content-type':类型})#成功
    响应.end(正文)#正文

def 应用(上下文,配置值):#占回退席
    'dist 根是 distIndex 的目录'
    dist索引=os.path.abspath(配置值['distIndex'])#索引绝对路径
    dist根=os.path.dirname(dist索引)#dist 根
    def 渲染索引():#读索引并注入，再插入 base
        'base 放在 head 开标签后，排在其余资源引用之前'
        with open(dist索引,'r',encoding='utf-8') as 文件:#读
            正文=上下文.webServer.renderIndex(文件.read())#注入
        return re.sub(r'(<head(?:\s[^>]*)?>)',r'\1<base href="./">',正文,count=1,flags=re.I)#base
    def 回退(请求,响应):#未命中具名路由
        '非 GET/HEAD 是 405'
        if 请求.method!='GET' and 请求.method!='HEAD':#方法不对
            响应.writeHead(405)#不允许
            响应.end()#结束
            return#停
        原始=urllib.parse.urlparse(请求.url if 请求.url else '/').path#路径
        提供静态(#发文件
            urllib.parse.unquote(原始),响应,dist根,dist索引,#目标
            lambda:上下文.connection.authorizeIndex(请求,响应),渲染索引,#认证与渲染
        )#结束
    def 占席():#登记回退
        '把回退席交给静态服务'
        return 上下文.webServer.registerFallback(回退)#登记
    上下文.副作用(占席,'frontend-static: fallback seat')#拆除时让出

name=名称#框架槽
inject=依赖#框架槽
Config=配置#框架槽
apply=应用#框架槽
