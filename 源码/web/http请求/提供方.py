"""ctx.web 的安全 HTTP(S) 检索：校验 URL、只跟随同源重定向、强制时间与体积上限、分类并解码文本，展示交给 tool-web。请求不携带浏览器 cookie 或环境凭证。未实现私有网络与 SSRF 防护；能碰到敏感内部目标的环境不要启用本提供方。"""
import threading#中止监视线程
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接#HTTP 客户端
from urllib.parse import urlunparse as 拼回网址#把解析结果拼回绝对串
from ..web import 网络错误#web 错误类型
from ...工具.超时 import 截止,取超时#截止期与超时原因
from .策略 import (
    校验抓取网址,#URL 卫生
    是否同源,#同源判定
    分类内容类型,#MIME 分类
    解析字符集,#抽出 charset
    字符集解码器,#解码标签
    解析重定向目标,#相对 Location
)#策略模块

线程=threading.Thread#工作线程
本地抓取提供方标识='http'#本提供方注册所用的稳定 id
HTTP抓取上限字段=('maxUrlLength','maxResponseBytes','maxBodyChars','timeoutMs','maxRedirects','userAgent')#已解析的提供方上限字段
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 信号已中止(信号):#英文 aborted 或中文 已中止
    """调用方信号是否已中止。"""
    if 信号 is None:#没有信号
        return False#未中止
    if getattr(信号,'aborted',False) is True:#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False) is True:#中文旗标
        return True#已中止
    return False#未中止

def 等待信号(信号):#阻塞到信号中止
    """阻塞到信号中止；优先走等待方法。"""
    等待=getattr(信号,'等待',None)#中文等待
    if 等待 is not None:#有中文
        等待()#阻塞
        return#完成
    等待英=getattr(信号,'wait',None)#英文等待
    if 等待英 is not None:#有英文
        等待英()#阻塞
        return#完成
    while not 信号已中止(信号):#无等待则轮询
        pass#忙等

def 网址绝对串(网址):#解析结果拼回绝对 URL 串
    """把 urlparse 结果拼回绝对 URL 字符串。"""
    return 拼回网址(网址)#拼回

def 是否重定向状态(状态):#是否重定向
    """带 Location 的 HTTP 重定向状态码。"""
    return 状态==301 or 状态==302 or 状态==303 or 状态==307 or 状态==308#常见 3xx

def 解析重定向(位置,基址):#解析下一跳
    """把（可能相对的）Location 相对当前 URL 解析。"""
    try:#相对或绝对 Location
        return 解析重定向目标(位置,基址)#相对 base 解析
    except Exception as 错误:#Location 非法
        raise 网络错误('invalid redirect Location "'+位置+'"','WEB_PROVIDER_ERROR',{'cause':错误})#包装成提供方错误

def 翻译中止或网络(错误,信号):#把原始错误收成网络错误
    """把抛出的 fetch/流错误翻译成网络错误，按截止期信号分类而不是按抛出值分类。取超时(信号,'WEB_FETCH_TIMEOUT') 找回我们的原因表示本超时触发；其它中止是 WEB_ABORTED；信号未中止却抛错则是传输/网络失败。"""
    超时=取超时(信号,'WEB_FETCH_TIMEOUT')#是否本提供方超时
    if 超时 is not None:#本超时
        return 网络错误('web fetch timed out','WEB_FETCH_TIMEOUT',{'cause':超时})#本超时
    if 信号已中止(信号):#其它中止
        return 网络错误('web fetch aborted','WEB_ABORTED',{'cause':错误})#其它中止
    return 网络错误('web fetch failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败

def 取消响应正文(响应包装):#丢掉正文以免漏套接字
    """取消可能仍在流的正文，以免漏套接字。"""
    if 响应包装 is None:#无响应
        return#空操作
    try:#关掉响应与连接
        原始=取字段(响应包装,'原始')#http 响应
        连接=取字段(响应包装,'连接')#底层连接
        if 原始 is not None:#有响应
            原始.close()#关响应
        if 连接 is not None:#有连接
            连接.close()#关连接
    except Exception:#清理失败
        pass#尽力清理

class HTTP抓取提供方:#匿名的公开 HTTP(S) 抓取提供方
    """匿名的公开 HTTP(S) 抓取提供方。"""
    def __init__(自身,上限):#保存已解析上限
        """收下已解析上限（插件的 schemastery Config 提供默认值）。"""
        自身.上限=上限#已解析上限
        自身.id=本地抓取提供方标识#注册 id
        自身.标识=本地抓取提供方标识#中文别名

    def 可用(自身):#是否可用
        """无需检查凭证——匿名公开抓取器始终可用。"""
        return True#始终可用

    available=可用#协议字段

    def 抓取(自身,请求,信号=None):#执行一次抓取
        """执行一次抓取；用信号接受取消。"""
        if 信号已中止(信号):#调用方已取消
            raise 网络错误('web fetch aborted','WEB_ABORTED')#已取消
        句柄=截止(信号,自身.上限['timeoutMs'],'WEB_FETCH_TIMEOUT')#一个信号同时停请求和读正文
        try:#跟随重定向并读最终响应
            return 自身.跟随并读取(取字段(请求,'url'),句柄.信号)#跟随并读取
        finally:#无论成败都清定时器
            句柄.释放()#清除截止定时器

    fetch=抓取#协议字段

    def 跟随并读取(自身,起始网址,信号):#重定向循环
        """跟随同源重定向直到跳数上限，然后读最终响应。"""
        当前=校验抓取网址(起始网址,自身.上限['maxUrlLength'])#校验并规范化起始 URL
        已跟随=0#已跟随跳数
        while True:#直到返回或抛错
            响应=自身.请求一次(当前,信号)#发一次 GET，不自动跟随
            if 是否重定向状态(响应['status']):#重定向状态
                if 已跟随>=自身.上限['maxRedirects']:#先执行重定向预算，再解析或校验下一跳
                    取消响应正文(响应)#丢掉正文以免漏套接字
                    raise 网络错误('exceeded the maximum of '+str(自身.上限['maxRedirects'])+' redirects','WEB_REDIRECT_BLOCKED')#超过跳数上限
                位置=响应['headers'].get('location')#读 Location
                if 位置 is None:#重定向状态却没有 Location，不是可用资源
                    取消响应正文(响应)#抛错前取消可能仍在流的正文，以免漏套接字
                    raise 网络错误('redirect response (HTTP '+str(响应['status'])+') without a Location header','WEB_PROVIDER_ERROR')#缺少 Location
                目标串=解析重定向(位置,当前)#相对 Location 相对当前 URL 解析
                try:#校验下一跳
                    已校验=校验抓取网址(目标串,自身.上限['maxUrlLength'])#长度与协议校验
                    if not 是否同源(已校验,当前):#跨源不自动跟随
                        raise 网络错误(
                            'cross-origin redirect to '+已校验.scheme+'://'+已校验.netloc+' is not followed automatically; retry against that URL directly',#跨源提示，字面量不改
                            'WEB_REDIRECT_BLOCKED',#重定向被拦
                        )#网络错误结束
                except Exception as 错误:#校验失败
                    取消响应正文(响应)#取消正文
                    raise 错误#原样抛出
                取消响应正文(响应)#不读重定向正文
                当前=已校验#改当前 URL
                已跟随=已跟随+1#跳数加一
                continue#发下一跳
            return 自身.读正文(响应,当前,信号)#读最终正文

    def 请求一次(自身,网址,信号):#单次 GET
        """发一次 GET，不自动跟随重定向。"""
        try:#发请求
            主机=网址.hostname#主机名
            端口=网址.port#显式端口或 None
            if 网址.scheme=='https':#HTTPS
                客户端=安全连接(主机,端口)#安全连接
            else:#HTTP
                客户端=明文连接(主机,端口)#明文连接
            if 信号 is not None:#有取消信号
                def 监视中止():#信号中止时关掉套接字
                    """信号中止时关掉套接字。"""
                    等待信号(信号)#阻塞到中止
                    客户端.close()#拆传输
                线程(target=监视中止,daemon=True).start()#监视中止
                if 信号已中止(信号):#已经中止则立刻关掉
                    客户端.close()#关掉
                    raise 翻译中止或网络(Exception('aborted'),信号)#分类成网络错误
            路径=网址.path if 网址.path else '/'#路径
            if 网址.query:#有查询串
                路径=路径+'?'+网址.query#拼上
            头={#UA 与可接受类型
                'user-agent':自身.上限['userAgent'],#UA
                'accept':'text/html,application/xhtml+xml,text/*;q=0.9,application/json;q=0.8',#可接受类型
            }#头结束
            客户端.request('GET',路径,headers=头)#只 GET；http.client 不自动跟随
            原始=客户端.getresponse()#上游响应
            头映射={}#小写头名映射
            for 键,值 in 原始.getheaders():#遍历响应头
                头映射[键.lower()]=值#小写键
            return {'status':原始.status,'headers':头映射,'原始':原始,'连接':客户端}#响应包装
        except 网络错误:#已是网络错误
            raise#原样抛
        except Exception as 错误:#网络或中止
            raise 翻译中止或网络(错误,信号)#分类成网络错误

    def 读正文(自身,响应,最终网址,信号):#处理最终响应
        """读取、按字节封顶、分类并解码最终响应正文。"""
        内容类型=响应['headers'].get('content-type')#读 Content-Type
        种类=分类内容类型(内容类型)#html / text / 不支持
        if 种类 is None:#不支持的类型
            取消响应正文(响应)#丢掉流
            文案='unknown' if 内容类型 is None else 内容类型#缺头当 unknown
            raise 网络错误('unsupported content type "'+文案+'"','WEB_UNSUPPORTED_CONTENT_TYPE')#类型错误
        try:#按 charset 建解码标签
            编码标签=字符集解码器(解析字符集(内容类型))#未知 charset 会抛
        except Exception as 错误:#charset 不支持
            取消响应正文(响应)#取消正文
            raise 错误#原样抛出
        有界=自身.有界读取(响应,信号)#按字节上限读
        字节=有界['bytes']#有界字节
        按字节截断=有界['truncatedByBytes']#字节截断标记
        解码文=字节.decode(编码标签,'replace')#解码成字符串（对齐 TextDecoder 替换）
        按字符截断=len(解码文)>自身.上限['maxBodyChars']#是否超字符上限
        内容=解码文[:自身.上限['maxBodyChars']] if 按字符截断 else 解码文#超则切开
        正文={'kind':种类,'content':内容}#按 kind 装箱
        return {#抓取结果
            'url':网址绝对串(最终网址),#最终 URL
            'statusCode':响应['status'],#HTTP 状态码
            'body':正文,#解码后正文
            'truncated':按字节截断 or 按字符截断,#字节或字符任一截断
        }#结果结束

    def 有界读取(自身,响应,信号):#有界读取
        """把响应流读到 maxResponseBytes。Content-Length 超过上限立即以 WEB_FETCH_TOO_LARGE 拒绝；流增长超过上限则截短（truncatedByBytes）而不是拒绝，这样少报长度的服务器仍能给出有界可用正文。"""
        声明=响应['headers'].get('content-length')#声明长度
        if 声明 is not None:#有 Content-Length
            try:#转成数字
                长度=float(声明)#数字
            except Exception:#非数字
                长度=None#忽略声明
            if 长度 is not None and 长度==长度 and 长度>自身.上限['maxResponseBytes']:#有限且声明就已超上限
                取消响应正文(响应)#不读正文
                raise 网络错误('response exceeds the maximum of '+str(自身.上限['maxResponseBytes'])+' bytes','WEB_FETCH_TOO_LARGE')#过大
        原始=响应['原始']#http 响应
        if 原始 is None:#无流则空正文
            return {'bytes':b'','truncatedByBytes':False}#空正文
        块们=[]#已收块
        合计=0#已收字节
        按字节截断=False#是否因上限截过
        try:#读到结束或上限
            while True:#直到 break
                剩余=自身.上限['maxResponseBytes']-合计#还能收多少
                if 剩余<=0:#已满上限
                    按字节截断=True#丢掉后续
                    break#停止读取
                try:#下一块
                    块=原始.read(65536 if 剩余>65536 else 剩余)#按剩余容量读
                except Exception as 错误:#读中途故障
                    raise 翻译中止或网络(错误,信号)#分类成网络错误
                if 块 is None or len(块)==0:#流结束
                    break#结束
                if len(块)>剩余:#只有被丢掉的字节才算截断
                    块们.append(块[:剩余])#只留剩余容量
                    合计=合计+剩余#记满上限
                    按字节截断=True#丢掉了后续字节
                    break#停止读取
                块们.append(块)#整块收下
                合计=合计+len(块)#累加
        finally:#无论成败都关掉
            取消响应正文(响应)#尽力清理
        return {'bytes':b''.join(块们),'truncatedByBytes':按字节截断}#有界字节与截断标记
