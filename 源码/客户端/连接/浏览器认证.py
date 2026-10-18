'浏览器会话认证：启动令牌和签名饼干'
import base64,email.utils,hashlib,hmac,json,re,secrets,time,urllib.parse,weakref#签名、时间与进程令牌
from ...凭据.凭据 import 凭证键#记录键
from .连接协议 import 连接路径# /connect
from .接口请求信任 import 解析权威#听众用的权威解析
from .异常 import 连接错误#记录或寿命非法
from .rpc import 编码json,同步等待#饼干正文与可能的期约

认证记录键=凭证键('client-connection','browser-session')#持久签名密钥
一日毫秒=24*60*60*1000#一天
密钥字节数=32#密钥长度
令牌查询='token'#查询名
饼干前缀='dsh-auth-'#饼干名前缀
饼干版本=1#浏览器饼干
已存密钥版本=1#记录版本
网址64规则=re.compile(r'^[A-Za-z0-9_-]*\Z')#base64url
启动令牌表=weakref.WeakKeyDictionary()#进程拥有者到启动令牌
安全整数上限=9007199254740991#2^53-1


def 现在毫秒():
    '当前时间的毫秒数'
    return int(time.time()*1000)#毫秒


def 是否安全整数(值):
    'JavaScript 的安全整数。布尔值不算'
    return isinstance(值,int) and not isinstance(值,bool) and abs(值)<=安全整数上限#范围内


def 编码64网址(数据):
    'base64url，不带填充'
    文字=base64.b64encode(数据).decode('ascii')#普通 base64
    return 文字.replace('+','-').replace('/','_').rstrip('=')#网址安全


def 解码64网址(文字):
    '非规范的 base64url 返回 None'
    if 网址64规则.fullmatch(文字) is None or len(文字)%4==1:#字母或长度不对
        return None#拒绝
    填充='='*((4-len(文字)%4)%4)#补齐
    标准=文字.replace('-','+').replace('_','/')+填充#还原
    try:#解码
        原始=base64.b64decode(标准,validate=True)#严格
    except Exception:#不是合法 base64
        return None#拒绝
    if 编码64网址(原始)!=文字:#再编码必须一致
        return None#拒绝非规范
    return 原始#字节


def 取头(头表,名):
    'Headers 用 get，字典只收字符串'
    if 头表 is None:#没有
        return None#缺失
    if isinstance(头表,dict):#映射
        值=头表[名] if 名 in 头表 else None#原名
    else:#Headers
        取值=getattr(头表,'get',None)#get
        if not callable(取值):#没有
            return None#读不到
        值=取值(名)#按名
        if 值 is None:#缺失
            return None#缺失
    if isinstance(值,str):#字符串
        return 值#原值
    return None#其它类型


def 请求听众(头表,安全):
    'https 用 origin，http 只用 host。解析不到则为空'
    主机=取头(头表,'host')#Host
    if 主机 is None:#没有
        return None#空
    解析=解析权威(主机,'https:' if 安全 else 'http:')#按监听方案
    if 解析 is None:#解析不到
        return None#空
    if 安全:#带方案的 origin
        return 'https://'+解析.host#origin
    return 解析.host#不含方案


def 已存密钥(记录):
    '从 grant 记录取出 32 字节密钥。格式不对就抛'
    if 记录 is None:#没有记录
        return None#空
    载荷=记录.get('payload') if isinstance(记录,dict) else None#载荷
    if 记录.get('kind')!='grant' or not isinstance(载荷,dict) or 载荷.get('version')!=已存密钥版本:#格式
        raise 连接错误('client-connection: browser-session credential record has an unsupported format')#拒绝
    密钥文=载荷.get('secret')#密钥文本
    密钥=None#先当没有
    if isinstance(密钥文,str):#字符串
        解出=解码64网址(密钥文)#解码
        if 解出 is not None and len(解出)==密钥字节数:#长度对
            密钥=解出#收下
    if 密钥 is None:#解不出或长度不对
        raise 连接错误('client-connection: browser-session credential record has an invalid secret')#拒绝
    return 密钥#字节


def 令牌相符(实际,期望):
    '长度相同才做恒定时间比较'
    实际字节=实际.encode('utf-8')#实际
    期望字节=期望.encode('utf-8')#期望
    if len(实际字节)!=len(期望字节):#长度不同
        return False#不相符
    return hmac.compare_digest(实际字节,期望字节)#恒定时间


def 饼干名(听众):
    '听众的 sha256，再编码成饼干名'
    摘要=hashlib.sha256(听众.encode('utf-8')).digest()#摘要
    return 饼干前缀+编码64网址(摘要)#名字


def 会话饼干(名字,值,到期毫秒,最大秒,安全):
    '固定的会话属性。https 再加 Secure'
    到期=email.utils.formatdate(到期毫秒/1000,usegmt=True)#UTC 日期
    属性=名字+'='+值+'; Max-Age='+str(最大秒)+'; Path=/; Expires='+到期+'; HttpOnly; SameSite=Strict'#属性
    if 安全:#监听的是 TLS
        return 属性+'; Secure'#再加
    return 属性#到此为止


def 签名(密钥,正文):
    '对 base64 正文做 sha256 HMAC'
    return hmac.new(密钥,正文.encode('utf-8'),hashlib.sha256).digest()#摘要


def 编码饼干(载荷,密钥):
    'v版本.正文.签名'
    正文=编码64网址(编码json(载荷).encode('utf-8'))#正文
    return 'v'+str(载荷['version'])+'.'+正文+'.'+编码64网址(签名(密钥,正文))#三段


class 浏览器认证:
    '进程启动令牌和持久签名饼干。密钥在激活时载入，请求认证是同步的'
    def __init__(自身,进程拥有者,密钥,最大天数):
        '同一进程拥有者共用一个启动令牌'
        已有=启动令牌表.get(进程拥有者)#已有令牌
        if 已有 is None:#还没有
            已有=编码64网址(secrets.token_bytes(密钥字节数))#新的
            启动令牌表[进程拥有者]=已有#记下
        自身._启动令牌=已有#启动令牌
        自身._密钥=密钥#签名密钥
        自身._最大寿命毫秒=最大天数*一日毫秒#饼干寿命
        现在=现在毫秒()#现在
        if not 是否安全整数(自身._最大寿命毫秒) or not 是否安全整数(现在+自身._最大寿命毫秒):#超出安全整数
            raise 连接错误('client-connection: cookieMaxAgeDays exceeds the safe timestamp range')#拒绝

    @classmethod
    def 创建(类,进程拥有者,凭证,最大天数):
        '没有记录就生成签名密钥。已有记录只校验，不覆盖'
        生成={'version':已存密钥版本,'secret':编码64网址(secrets.token_bytes(密钥字节数))}#新密钥

        def 变更(当前):
            '已有记录保持不动。没有则写入 grant'
            if 当前 is not None:#已有
                已存密钥(当前)#格式不对就抛
                return None#不改
            return {'kind':'grant','payload':生成}#新建

        记录=凭证.修改记录(认证记录键,变更)#读改写
        if hasattr(记录,'then'):#仍是期约
            记录=同步等待(记录)#等到记录
        密钥=已存密钥(记录)#取出
        if 密钥 is None:#没有创建出来
            raise 连接错误('client-connection: browser-session credential record was not created')#拒绝
        return 类(进程拥有者,密钥,最大天数)#实例

    def 已认证网址(自身,基址):
        '把本进程的启动令牌放进调用方的应用网址'
        拆=urllib.parse.urlsplit(基址)#拆开
        原查询=urllib.parse.parse_qsl(拆.query,keep_blank_values=True)#原查询
        新查询=[]#替换后的
        已放=False#是否已经放过 token
        for 键,值 in 原查询:#逐项
            if 键==令牌查询:#原有 token
                if not 已放:#只留一个
                    新查询.append((令牌查询,自身._启动令牌))#换成进程令牌
                    已放=True#已放
            else:#其它参数
                新查询.append((键,值))#原样
        if not 已放:#原来没有
            新查询.append((令牌查询,自身._启动令牌))#追加
        return urllib.parse.urlunsplit((拆.scheme,拆.netloc,拆.path,urllib.parse.urlencode(新查询),拆.fragment))#拼回

    def 授权索引(自身,请求,响应,安全=False):
        '根查询里的合法令牌换成饼干并重定向。合法饼干才允许发送索引'
        原始=请求.url if getattr(请求,'url',None) else '/'#没有 url 当根
        绝对=urllib.parse.urljoin('http://dsh.invalid',原始)#补上基址
        拆=urllib.parse.urlsplit(绝对)#拆开
        查询=urllib.parse.parse_qs(拆.query,keep_blank_values=True)#查询
        令牌表=查询.get(令牌查询,[])#全部 token
        if len(令牌表)>0:#带了令牌
            听众=请求听众(请求.headers,安全)#听众
            if 请求.method=='GET' and 拆.path=='/' and len(令牌表)==1 and 听众 is not None and 令牌相符(''.join(令牌表),自身._启动令牌):#唯一合法令牌
                发出=现在毫秒()#现在
                到期=发出+自身._最大寿命毫秒#到期
                值=编码饼干({'version':饼干版本,'authority':听众,'issuedAt':发出,'expiresAt':到期},自身._密钥)#饼干
                响应.writeHead(303,{#重定向
                    'cache-control':'no-store',#不缓存
                    'location':'./',#去掉查询
                    'referrer-policy':'no-referrer',#不带引用
                    'set-cookie':会话饼干(饼干名(听众),值,到期,自身._最大寿命毫秒//1000,安全),#饼干
                })#头结束
                响应.end()#无正文
                return False#调用方不要再发索引
            if 请求.method=='GET' and 拆.path=='/' and 自身.是否已认证(请求,安全):#令牌无效但饼干有效
                响应.writeHead(303,{#只去掉查询
                    'cache-control':'no-store',#不缓存
                    'location':'./',#干净地址
                    'referrer-policy':'no-referrer',#不带引用
                })#头结束
                响应.end()#无正文
                return False#调用方不要再发索引
            自身._写未授权(请求,响应)#同一个 401
            return False#拒绝
        if 自身.是否已认证(请求,安全):#没有令牌，饼干有效
            return True#可以发索引
        自身._写未授权(请求,响应)#401
        return False#拒绝

    def 授权连接(自身,请求,响应,安全,发布):
        '用启动令牌换成独立的接口操作方。没写 interactions 则为 none'
        原始=请求.url if getattr(请求,'url',None) else '/'#没有 url 当根
        绝对=urllib.parse.urljoin('http://dsh.invalid',原始)#补上基址
        拆=urllib.parse.urlsplit(绝对)#拆开
        查询=urllib.parse.parse_qs(拆.query,keep_blank_values=True)#查询
        声明表=查询.get('interactions',[])#全部声明
        交互=声明表[0] if len(声明表)>0 else 'none'#默认 none
        if len(声明表)>1 or (交互!='answer' and 交互!='none'):#写了多次或不是那两个值
            响应.writeHead(400,{#坏请求
                'cache-control':'no-store',#不缓存
                'content-type':'text/plain; charset=utf-8',#纯文本
            })#头结束
            响应.end('interactions must be declared once as answer or none\n')#说明
            return#结束
        令牌表=查询.get(令牌查询,[])#令牌
        听众=请求听众(请求.headers,安全)#听众
        if 请求.method!='GET' or 拆.path!=连接路径 or len(令牌表)!=1 or 听众 is None or not 令牌相符(''.join(令牌表),自身._启动令牌):#不是一次合法交换
            自身._写未授权(请求,响应)#401
            return#结束
        发出=现在毫秒()#现在
        到期=发出+自身._最大寿命毫秒#到期
        标识=发布(交互)#先创建操作方
        值=编码饼干({'version':2,'authority':听众,'id':标识,'issuedAt':发出,'expiresAt':到期},自身._密钥)#接口饼干
        响应.writeHead(302,{#转到复用通道
            'cache-control':'no-store',#不缓存
            'location':'./api/remote.mux',#复用通道
            'referrer-policy':'no-referrer',#不带引用
            'set-cookie':会话饼干(饼干名(听众),值,到期,自身._最大寿命毫秒//1000,安全),#饼干
        })#头结束
        响应.end()#无正文

    def 是否已认证(自身,请求,安全=False):
        '未过期、且是本激活密钥签的浏览器饼干'
        载荷=自身.鉴别(请求,安全)#解出
        return 载荷 is not None and 载荷['version']==饼干版本#只认浏览器版本

    def 鉴别接口(自身,请求,安全=False):
        '接口饼干里的操作方标识。浏览器饼干、过期和无效都为空'
        载荷=自身.鉴别(请求,安全)#解出
        if 载荷 is not None and 载荷['version']==2:#接口版本
            return 载荷['id']#标识
        return None#不是

    def 鉴别(自身,请求,安全):
        '验签、听众、时间和寿命。失败为空'
        头表=请求.headers if not isinstance(请求,dict) else 请求['headers']#头
        听众=请求听众(头表,安全)#听众
        饼干头=取头(头表,'cookie')#Cookie
        if 听众 is None or 饼干头 is None:#缺一
            return None#失败
        名字=饼干名(听众)#这个听众的名字
        值=None#饼干值
        for 段 in 饼干头.split(';'):#按段
            位置=段.find('=')#等号
            if 位置<0 or 段[:位置].strip()!=名字:#不是这一张
                continue#下一
            值=段[位置+1:].strip()#值
            break#找到
        if 值 is None:#没有这张饼干
            return None#失败
        段表=值.split('.')#三段
        if len(段表)!=3:#不是三段
            return None#失败
        版本字,正文,签名文=段表#拆开
        if 版本字!='v1' and 版本字!='v2':#版本字
            return None#失败
        if 正文 is None or 签名文 is None:#缺段
            return None#失败
        实际签名=解码64网址(签名文)#签名
        if 实际签名 is None:#签名不是 base64url
            return None#失败
        期望签名=签名(自身._密钥,正文)#重算
        if len(实际签名)!=len(期望签名) or not hmac.compare_digest(实际签名,期望签名):#签名不符
            return None#失败
        try:#正文
            正文字节=解码64网址(正文)#正文
            if 正文字节 is None:#不是 base64url
                return None#失败
            解出=json.loads(正文字节.decode('utf-8'))#对象
        except Exception:#不是 JSON
            return None#失败
        if not isinstance(解出,dict):#不是对象
            return None#失败
        if 解出.get('version')!=饼干版本 and 解出.get('version')!=2:#版本
            return None#失败
        if 版本字!='v'+str(解出['version']):#版本字和字段不一致
            return None#失败
        if not isinstance(解出.get('authority'),str):#听众
            return None#失败
        if not 是否安全整数(解出.get('issuedAt')) or not 是否安全整数(解出.get('expiresAt')):#时间
            return None#失败
        载荷={'authority':解出['authority'],'issuedAt':解出['issuedAt'],'expiresAt':解出['expiresAt']}#公共字段
        if 解出['version']==饼干版本:#浏览器
            载荷['version']=饼干版本#版本 1
        else:#接口
            if not isinstance(解出.get('id'),str) or 解出['id']=='':#标识
                return None#失败
            载荷['version']=2#版本 2
            载荷['id']=解出['id']#标识
        if 载荷['authority']!=听众:#听众不符
            return None#失败
        现在=现在毫秒()#现在
        if 载荷['issuedAt']>现在 or 载荷['expiresAt']<=现在 or 载荷['expiresAt']<=载荷['issuedAt']:#时间不对
            return None#失败
        if 载荷['expiresAt']-载荷['issuedAt']>自身._最大寿命毫秒:#寿命超过配置
            return None#失败
        return 载荷#通过

    def _写未授权(自身,请求,响应):
        '索引和连接失败用同一句。HEAD 不写正文'
        响应.writeHead(401,{#401
            'cache-control':'no-store',#不缓存
            'content-type':'text/plain; charset=utf-8',#纯文本
        })#头结束
        if 请求.method=='HEAD':#没有正文
            响应.end()#空
        else:#其它方法
            响应.end('dsh web authentication required; reopen the URL printed by dsh web.\n')#原文
