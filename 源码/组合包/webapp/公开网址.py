'本组合包 publicUrl 配置与命令行启动共用的公开 HTTP(S) 根解析'
import ipaddress,re,urllib.parse
from .异常 import 网页错误#公告根被拒绝

六版地址=ipaddress.IPv6Address#IPv6
解析网址=urllib.parse.urlparse#拆开网址

class 网址:
    '解析后的公告根，href 以斜杠结尾'
    def __init__(自身,链接):
        '记下规范链接'
        自身.href=链接#规范链接

def 解析公开网址(值,标签='publicUrl'):
    '解析公告用的公开 HTTP(S) 根。拒绝 WHATWG 会单独收下的危险写法，路径收成以 / 结尾'
    #空白和控制字符先于协议检查
    if re.search(r'[\x00-\x20\x7f]',值) is not None:#含空白或控制字符
        raise 网页错误(标签+' 不能包含 ASCII 空白或控制字符')#拒绝
    if re.match(r'^https?://',值,re.IGNORECASE) is None:#不是绝对 http(s)
        raise 网页错误(标签+' 必须是形如 http(s)://主机[/前缀] 的绝对 http 或 https 网址')#拒绝
    if ('?' in 值) or ('#' in 值):#查询或片段
        raise 网页错误(标签+' 不能包含查询或片段（? 或 #）')#拒绝
    #用户信息在第一个路径斜杠前的原始权威里；空权威（https://、https:///ui）也在这里失败
    正文=值[值.find('://')+3:]#协议之后
    拆分=re.split(r'[/\\]',正文,maxsplit=1)#斜杠或反斜杠切开
    权威=拆分[0] if len(拆分)>0 else ''#权威
    if 权威=='':#没有主机
        raise 网页错误(标签+' 必须在 http:// 或 https:// 之后写主机')#拒绝
    if '@' in 权威:#含凭据
        raise 网页错误(标签+' 不能包含凭据（@ 前的用户名或密码，含空用户）')#拒绝
    #反斜杠按 WHATWG 当成路径分隔，再解析主机与端口
    结果=解析网址(值.replace('\\','/'))#规范化后再拆
    网络位置=结果.netloc#权威
    if ('[' in 网络位置) and (']' not in 网络位置):#方括号没关上
        raise 网页错误(标签+' 必须是绝对的 http 或 https 网址')#拒绝
    主机名=结果.hostname#主机
    if 主机名 is None or 主机名=='':#解析不到主机
        raise 网页错误(标签+' 必须是绝对的 http 或 https 网址')#拒绝
    try:#端口越界在这里失败
        端口数=结果.port#端口
    except ValueError:#端口不是可用数字
        raise 网页错误(标签+' 必须是绝对的 http 或 https 网址')#拒绝
    if ':' in 主机名:#IPv6
        try:#压缩写法
            主机文本='['+六版地址(主机名).compressed+']'#带方括号
        except ValueError:#不是 IPv6
            raise 网页错误(标签+' 必须是绝对的 http 或 https 网址')#拒绝
    else:#域名或 IPv4，hostname 已经小写
        主机文本=主机名#主机
    方案=结果.scheme#小写协议
    if 端口数 is not None and ((方案=='http' and 端口数==80) or (方案=='https' and 端口数==443)):#默认端口不写进 href
        端口数=None#省略
    路径=结果.path#路径
    if 路径=='':#WHATWG 至少是 /
        路径='/'#根
    if not 路径.endswith('/'):#补尾斜杠
        路径=路径+'/'#以斜杠结尾
    链接=方案+'://'+主机文本#协议与主机
    if 端口数 is not None:#非默认端口
        链接=链接+':'+str(端口数)#端口
    链接=链接+路径#路径
    return 网址(链接)#公告根
