"""本地 HTTP(S) 抓取提供方的 URL 校验与内容类型分类——纯的、不碰网络的一半。提供方的 fetch() 把这些与传输（跟随重定向、字节上限、解码）组合起来。"""
import re#抽出 charset 参数
from urllib.parse import urlparse as 解析网址,urljoin as 拼接网址#解析与相对 Location
from ..web import 网络错误#web 错误类型

可抓取种类=('html','text')#本提供方会解码的正文种类
def 校验抓取网址(输入,最大网址长度):#校验并解析请求 URL
    """对照提供方在任何网络访问前强制的基本传输卫生校验请求 URL：只允许 http(s)、不许内嵌凭证、长度有界。返回解析后的网址对象。否则抛网络错误。SSRF / 私有网络拦截推迟。"""
    if len(输入)>最大网址长度:#超过长度上限
        raise 网络错误('URL exceeds the maximum length of '+str(最大网址长度),'WEB_INVALID_URL')#过长
    try:#解析绝对 URL
        网址=解析网址(输入)#失败则畸形
    except Exception as 错误:#非法 URL
        raise 网络错误('invalid URL: '+输入,'WEB_INVALID_URL',{'cause':错误})#包装成 WEB_INVALID_URL
    if 网址.scheme not in ('http','https') or 网址.netloc=='':#协议不是 http(s) 或缺少主机
        协议=网址.scheme+':' if 网址.scheme else ''#对齐 URL.protocol 字面量
        if 网址.scheme not in ('http','https'):#协议不合格
            raise 网络错误('unsupported URL scheme "'+协议+'" (only http and https are allowed)','WEB_INVALID_URL')#不支持的协议
        raise 网络错误('invalid URL: '+输入,'WEB_INVALID_URL')#缺主机当非法 URL
    if (网址.username is not None and len(网址.username)>0) or (网址.password is not None and len(网址.password)>0):#内嵌用户名或密码
        raise 网络错误('credentials in URLs are not allowed','WEB_BLOCKED_URL')#禁止凭证 URL
    return 网址#卫生检查通过

def 是否同源(甲,乙):#是否同源
    """两个 URL 在协议、主机名、端口都相同时为同源。跨源重定向会被拒绝，使每个新源都需要一次新的工具调用（从而一次新的提供方/权限决定）。"""
    甲端口='' if 甲.port is None else str(甲.port)#对齐 URL.port 缺省空串
    乙端口='' if 乙.port is None else str(乙.port)#对齐 URL.port 缺省空串
    return 甲.scheme==乙.scheme and 甲.hostname==乙.hostname and 甲端口==乙端口#协议、主机、端口都相同

def 分类内容类型(内容类型):#按 MIME 分类
    """把响应 Content-Type 分类成可解码正文种类；不支持的（例如二进制）为 None。text/html 与 application/xhtml+xml 是 html；其它 text/* 加上几种结构化文本是 text。"""
    原文='' if 内容类型 is None else 内容类型#响应没有该头时为空
    媒体类型=re.sub(r';.*$','',原文,flags=re.S).strip().lower()#去掉参数、去空白、小写
    if 媒体类型=='text/html' or 媒体类型=='application/xhtml+xml':#HTML
        return 'html'#html 种类
    if 媒体类型.startswith('text/'):#其它 text/*
        return 'text'#纯文本
    if 媒体类型=='application/json' or 媒体类型=='application/xml' or 媒体类型.endswith('+json') or 媒体类型.endswith('+xml'):#结构化文本
        return 'text'#当文本解码
    return None#二进制或不认识

def 解析字符集(内容类型):#抽出 charset
    """从响应 Content-Type 抽出 charset 参数并小写；缺席则为 None。提供方把这个标签交给解码器，使非 UTF-8 响应按其声明编码解码，而不是悄悄变成替换字符。"""
    原文='' if 内容类型 is None else 内容类型#无头则空串
    命中=re.search(r';\s*charset\s*=\s*"?([^";]+)"?',原文,flags=re.I)#匹配 charset= 参数
    if 命中 is None:#未声明
        return None#缺席
    return 命中.group(1).strip().lower()#去空白并小写

def 字符集解码器(字符集):#按 charset 建解码标签
    """按声明的 charset 返回解码用标签；未声明则用 utf-8。标签存在但编解码器不认识时抛网络错误 WEB_UNSUPPORTED_CONTENT_TYPE——大声失败优于返回乱码。"""
    if 字符集 is None:#未声明则 UTF-8
        return 'utf-8'#默认编码
    try:#按标签探测
        ''.encode(字符集)#不认识的标签会抛
        return 字符集#声明编码
    except Exception as 错误:#未知 charset
        raise 网络错误('unsupported charset "'+字符集+'"','WEB_UNSUPPORTED_CONTENT_TYPE',{'cause':错误})#不支持的内容类型

def 解析重定向目标(位置,基址):#相对 Location 相对基址解析
    """把（可能相对的）Location 相对当前 URL 解析成绝对串。"""
    基串=基址.geturl() if hasattr(基址,'geturl') else str(基址)#当前绝对 URL 串
    return 拼接网址(基串,位置)#相对基址解析
