"""经已组合文件系统 provider，对已认证的 GET/HEAD /api/file 读出有界文件响应。

路径与 MIME 不限制访问；连接服务在本处理器之前完成认证。
响应为连接包惯用的字典形态（status/headers/body）。
"""
import mimetypes#按扩展名查 MIME
import os#绝对路径判定
from urllib.parse import parse_qs as 解析查询串,urlparse as 解析网址
from ...文件系统.文件系统 import 文件系统错误#文件系统错误

__all__=['会话媒体引用']#仅中文公开名

基础响应头={#基础响应头
    'Cache-Control':'private, no-store',#禁止共享缓存
    'X-Content-Type-Options':'nosniff',#禁止嗅探
    # HTML/SVG 可能直接在已认证 API 源打开。
    'Content-Security-Policy':"sandbox; default-src 'none'",#沙箱 CSP
}#基础响应头结束

错误状态表={#错误码到 HTTP
    'FS_NOT_FOUND':404,
    'FS_NOT_REGULAR_FILE':403,
    'FS_PERMISSION_DENIED':403,
    'FS_SANDBOX_DENIED':403,
    'FS_TOO_LARGE':413,
    'FS_ABORTED':499,
}#错误状态表结束

def _失败(请求,状态,文本):
    """失败响应；HEAD 无体。"""
    方法=请求['method'] if 'method' in 请求 else 'GET'#方法
    正文=None if 方法=='HEAD' else 文本.encode('utf-8')#体
    return {'status':状态,'headers':dict(基础响应头),'body':正文}

def 提供文件(请求,文件系统,最大字节):
    """解析 path、读元数据或有界字节并回响应。请求为 dict。"""
    网址=请求['url'] if 'url' in 请求 else ''#url
    参数=解析查询串(解析网址(网址).query)
    路径列表=参数['path'] if 'path' in 参数 else []#path
    路径=路径列表[0] if len(路径列表)>0 else None#首值
    if 路径 is None or 路径=='':#缺路径
        return _失败(请求,400,'missing path')#缺路径
    if '\0' in 路径 or not os.path.isabs(路径):#须绝对路径
        return _失败(请求,400,'absolute path required')#须绝对路径
    信号=请求['signal'] if 'signal' in 请求 else None#中止
    方法=请求['method'] if 'method' in 请求 else 'GET'#方法
    try:
        目标=文件系统.解析(路径,{'signal':信号} if 信号 is not None else None)#解析目标
        媒体类型=mimetypes.guess_type(目标['displayPath'])[0] or 'application/octet-stream'#媒体类型
        头=dict(基础响应头)#响应头
        头['Content-Type']=媒体类型#类型
        if 方法=='HEAD':#仅元数据
            信息=文件系统.状态(目标,信号)#stat
            if 信息 is None:#不存在
                return _失败(请求,404,'not found')#不存在
            if 信息['type']!='file':#非普通文件
                return _失败(请求,403,'not a regular file')#非普通文件
            if 'size' in 信息 and 信息['size'] is not None:#已知大小
                if 信息['size']>最大字节:#超限
                    return _失败(请求,413,'file exceeds byte limit')#超限
                头['Content-Length']=str(信息['size'])#长度
            return {'status':200,'headers':头,'body':None}#HEAD 无体
        字节=文件系统.读字节(目标,信号,最大字节)#读字节
        字节=bytes(字节)#切片拷贝
        头['Content-Length']=str(len(字节))#长度
        return {'status':200,'headers':头,'body':字节}#返回体
    except 文件系统错误 as 错误:
        状态=错误状态表[错误.code] if 错误.code in 错误状态表 else 500#映射
        return _失败(请求,状态,错误.code)#映射失败

依赖=['connection','fs','attachments']

def 应用(上下文,配置=None):
    """挂载已认证 GET|HEAD /api/file。"""
    最大字节=上下文.attachments.imageLimits['maxImageBytes']#字节上限
    def 登记():
        """登记 fetch 路由。"""
        def 处理(请求):
            """转交提供文件。"""
            return 提供文件(请求,上下文.fs,最大字节)#处理器
        return 上下文.connection.fetch.register({#登记
            'path':'/api/file',#文件 API
            'methods':['GET','HEAD'],#方法
            'requestBody':'buffered',#缓冲请求体
            'fetch':处理,#处理器
        })
    上下文.副作用(登记,'session-controller: /api/file')#效果名

class _会话媒体引用插件:
    """文件展示贡献。连接服务负责认证；ctx.fs 提供执行世界的路径、读取与访问策略。"""
    pass

会话媒体引用=_会话媒体引用插件()#对象插件（非类），Cordis 读 apply
会话媒体引用.inject=依赖
会话媒体引用.apply=应用
