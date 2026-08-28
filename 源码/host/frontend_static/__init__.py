"""经 webserver 兜底席位提供 SPA dist 服务。

对齐上游 `@deepseek-ai/dsh-host-frontend-static`。公开面仅中文名。越出 dist 根的遍历是 403，未命中回落到 index.html 且 HTTP 200。本包不提供默认导出。
"""
import os#路径
from urllib.parse import unquote#解码路径
from ...依赖.schemastery import 路径上节点,字符串字段#配置字段

__all__=['名称','注入','配置','应用','服务静态']#仅中文公开名

名称='frontend-static'#本插件名
注入=['webServer']#依赖 webServer
配置=路径上节点({#前端静态服务配置
    'distIndex':字符串字段(可空=False),#index.html 绝对路径
})#配置结束

MIME={#按扩展名的 Content-Type
    '.html':'text/html; charset=utf-8',#HTML
    '.js':'text/javascript; charset=utf-8',#脚本
    '.css':'text/css; charset=utf-8',#样式
    '.svg':'image/svg+xml',#矢量图
    '.json':'application/json',#JSON
    '.map':'application/json',#sourcemap
    '.webmanifest':'application/manifest+json',#Web 清单
}#MIME 结束

def 服务静态(路径名,响应,发行根,发行索引,渲染索引):#从 dist 根服务一次 GET/HEAD
    """写入响应后返回。越出 dist 根 403；未命中回落 index。"""
    目标=os.path.normpath(os.path.join(发行根,路径名.lstrip('/\\')))#接到 dist 根并规范化
    分隔=os.sep#平台分隔符
    if 目标!=发行根 and not 目标.startswith(发行根+分隔):#越出 dist 根
        响应.writeHead(403)#禁止遍历
        响应.end()#无正文
        return#不再读
    def 发索引():#200 返回经 tap 的 index.html
        """走 index 路径。"""
        正文=渲染索引()#跑 index tap
        响应.writeHead(200,{'content-type':MIME['.html']})#HTML
        响应.end(正文)#写出
    if 目标==发行根 or 目标==发行索引:#`/` 或显式 index
        发索引()#index
        return#不按文件读
    try:#按目标读文件
        with open(目标,'rb') as 文件:#命中 dist 内文件
            正文=文件.read()#字节
        扩展=os.path.splitext(目标)[1].lower()#扩展名
        响应.writeHead(200,{'content-type':MIME.get(扩展,'application/octet-stream')})#MIME 或 octet-stream
        响应.end(正文)#写出
    except OSError:#未命中
        发索引()#SPA 客户端路由

def 应用(上下文,配置值):#申领兜底席位并提供 dist
    """登记兜底处理器。"""
    发行索引=取字段(配置值,'distIndex')#index.html 绝对路径
    发行根=os.path.dirname(发行索引)#dist 根
    def 渲染索引():#读 index 再跑全部 index tap
        """注入 boot-manifest 等。"""
        with open(发行索引,'r',encoding='utf-8') as 文件:#读原文
            原文=文件.read()#正文
        return 上下文.webServer.applyIndexTaps(原文)#跑 tap
    def 兜底(请求,响应):#唯一兜底席位
        """非 GET/HEAD 是 405；其余按 dist 服务。"""
        方法=getattr(请求,'method',None) or 取字段(请求,'method')#HTTP 方法
        if 方法 not in ('GET','HEAD'):#兜底不处理写方法
            响应.writeHead(405)#方法不允许
            响应.end()#无正文
            return#不读 dist
        原始=getattr(请求,'url',None) or 取字段(请求,'url') or '/'#路径
        try:#解码
            from urllib.parse import urlsplit#取路径
            路径名=unquote(urlsplit(原始).path or '/')#解码路径
        except Exception:#坏 %-转义
            响应.writeHead(400)#畸形
            响应.end()#无正文
            return#结束
        服务静态(路径名,响应,发行根,发行索引,渲染索引)#按 dist 服务
    上下文.effect(lambda:上下文.webServer.registerFallback(兜底),'frontend-static: fallback seat')#申领席位

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性
