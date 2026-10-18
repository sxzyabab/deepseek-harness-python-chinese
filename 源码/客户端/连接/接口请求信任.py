'每条 /api 请求的 Host 与来源围栏'
from .回环主机名 import 是否回环主机名#回环主机名
from .异常 import 连接错误#加载期拒绝畸形权威
from .rpc import 编码json#紧凑 JSON


class 权威网址:
    '解析后的主机、端口和 host。端口空字符串表示这个方案下没有写出非默认端口'
    def __init__(自身,主机名,端口,主机,协议):
        '记下四项'
        自身.hostname=主机名#主机名，IPv6 带方括号
        自身.port=端口#非默认端口，否则空
        自身.host=主机#host，含非默认端口
        自身.protocol=协议#http: 或 https:


def 取头(头表,名):
    '从 Headers 或字典读单个头。只接受字符串'
    if 头表 is None:#没有头
        return None#缺失
    if isinstance(头表,dict):#普通映射
        值=头表[名] if 名 in 头表 else None#按原名
    else:#Headers
        取值=getattr(头表,'get',None)#get
        if not callable(取值):#没有 get
            return None#读不到
        值=取值(名)#按名
        if 值 is None:#缺失
            return None#缺失
    if isinstance(值,str):#字符串
        return 值#原值
    return None#数组或其它类型不当成这个头


def 预处理(文本):
    '去掉制表和换行，再去掉两端的 C0 与空格'
    去掉=''.join(字符 for 字符 in 文本 if 字符 not in '\t\n\r')#制表和换行整段删除
    起=0#左
    止=len(去掉)#右
    while 起<止 and (去掉[起]==' ' or ord(去掉[起])<32):#左端
        起=起+1#收
    while 止>起 and (去掉[止-1]==' ' or ord(去掉[止-1])<32):#右端
        止=止-1#收
    return 去掉[起:止]#剩余


def 解析ipv4数(文本):
    '一段 IPv4 数字。0x 十六进制，前导 0 八进制，其余十进制'
    if 文本=='':#空段
        return None#不是数字
    if len(文本)>=2 and 文本[0]=='0' and 文本[1] in 'xX':#十六进制
        数字=文本[2:]#0x 后面
        if 数字=='' or any(字符 not in '0123456789abcdefABCDEF' for 字符 in 数字):#非法
            return None#失败
        值=int(数字,16)#十六进制
    elif len(文本)>=2 and 文本[0]=='0':#八进制
        if any(字符 not in '01234567' for 字符 in 文本):#含 8 或 9
            return None#失败
        值=int(文本,8)#八进制
    else:#十进制
        if any(字符 not in '0123456789' for 字符 in 文本):#不是十进制
            return None#失败
        值=int(文本,10)#十进制
    if 值>4294967295:#超过 32 位
        return None#失败
    return 值#数字


def 解析ipv4(文本):
    '四段 IPv4。任一段超过 255 则整段失败'
    段=文本.split('.')#按点
    if len(段)!=4:#只接受四段
        return None#失败
    数=[]#四段
    for 片 in 段:#逐段
        值=解析ipv4数(片)#解析
        if 值 is None or 值>255:#不是 0 到 255
            return None#失败
        数.append(值)#收下
    return 数#四段


def 是ipv4数(文本):
    '这一段能不能当 IPv4 数字。用来判断主机名是不是以数字结尾'
    return 解析ipv4数(文本) is not None#能解析


def 域名(文本):
    '普通域名。禁止主机名里的特殊字符，字母改小写'
    if 文本=='':#空
        return None#失败
    for 字符 in 文本:#逐个
        码=ord(字符)#码点
        if 字符 in ' #%/:<>?@[\\]^|' or 码<32 or 码==127:#禁止
            return None#失败
    return 文本.lower()#小写


def 解析主机名(文本):
    '以数字结尾则按 IPv4，否则按域名。IPv4 失败就不是域名'
    if 文本=='':#空
        return None#失败
    段=文本.split('.')#标签
    if 是ipv4数(段[-1]):#以数字结尾
        地址=解析ipv4(文本)#四段
        if 地址 is None:#看起来像 IPv4 但非法
            return None#失败
        return '.'.join(str(值) for 值 in 地址)#规范十进制
    return 域名(文本)#域名


def 解析ipv6(文本):
    '八个十六位段。允许一处 ::，末段可以是点分 IPv4'
    if 文本.count('::')>1:#两处压缩
        return None#失败
    有压缩='::' in 文本#是否压缩
    if 有压缩:#拆开两边
        左文,右文=文本.split('::',1)#左右
    else:#没有压缩
        左文,右文=文本,''#全部在左
    def 解析侧(侧,允许地址):
        '一侧的十六位段。点分地址只允许出现在这一侧的最后'
        if 侧=='':#空侧
            return []#没有段
        片=侧.split(':')#冒号
        结果=[]#段
        for 下标,片文 in enumerate(片):#逐段
            if 片文=='':#空段
                return None#失败
            if '.' in 片文:#点分 IPv4
                if not 允许地址 or 下标!=len(片)-1:#不是末段
                    return None#失败
                地址=解析ipv4(片文)#四段
                if 地址 is None:#非法
                    return None#失败
                结果.append((地址[0]<<8)|地址[1])#高 16 位
                结果.append((地址[2]<<8)|地址[3])#低 16 位
            else:#十六进制
                if len(片文)>4 or any(字符 not in '0123456789abcdefABCDEF' for 字符 in 片文):#非法
                    return None#失败
                结果.append(int(片文,16))#一段
        return 结果#段
    左侧=解析侧(左文, (not 有压缩) and ('.' in 左文))#左侧，无压缩时末段可以是地址
    if 左侧 is None:#左侧失败
        return None#失败
    右侧=解析侧(右文,'.' in 右文) if 有压缩 else []#右侧末段可以是地址
    if 右侧 is None:#右侧失败
        return None#失败
    if 有压缩:#补零
        缺少=8-len(左侧)-len(右侧)#要补的段数
        if 缺少<1:#没有可压缩的零
            return None#失败
        段=左侧+[0]*缺少+右侧#拼上
    else:#必须刚好八段
        段=左侧#左侧就是全部
        if len(段)!=8:#段数不对
            return None#失败
    if len(段)!=8:#仍不是八段
        return None#失败
    return 段#八段


def 序列化ipv6(段):
    '最长的一段零压成 ::。同样长时取左边。单个零不压'
    最好起=-1#起点
    最好长=0#长度
    下标=0#游标
    while 下标<8:#扫描
        if 段[下标]==0:#一段零
            起=下标#起点
            while 下标<8 and 段[下标]==0:#继续
                下标=下标+1#前进
            长=下标-起#这一段
            if 长>最好长:#更长
                最好长=长#记下
                最好起=起#记下
        else:#不是零
            下标=下标+1#前进
    def 十六(值):
        '小写，不补前导零'
        return format(值,'x')#十六进制
    if 最好长<2:#没有可压的
        return ':'.join(十六(值) for 值 in 段)#全写
    左=':'.join(十六(值) for 值 in 段[:最好起])#左边
    右=':'.join(十六(值) for 值 in 段[最好起+最好长:])#右边
    return 左+'::'+右#压上


def 解析端口(端口文,方案):
    '空表示没写。默认端口在这个方案下记成空字符串。非法返回 None'
    if 端口文 is None:#没写端口
        return ''#空
    if 端口文=='' or len(端口文)>5 or any(字符 not in '0123456789' for 字符 in 端口文):#悬空或非数字
        return None#失败
    值=int(端口文,10)#数值
    if 值>65535:#超出
        return None#失败
    默认=80 if 方案=='http:' else 443#这个方案的默认端口
    if 值==默认:#默认端口不出现在 host 里
        return ''#空
    return str(值)#去掉前导零


def 解析权威(条目,方案='http:'):
    '裸权威的 WHATWG 解析。失败为 None。路径、用户信息会被切掉，不在这里拒绝'
    文本=预处理(条目)#先整理空白
    if 文本=='':#空
        return None#失败
    文本=文本.replace('\\','/')#特殊方案把反斜杠当斜杠
    for 分隔 in '/?#':#路径、查询、片段
        位置=文本.find(分隔)#第一处
        if 位置!=-1:#有
            文本=文本[:位置]#只留权威
    if '@' in 文本:#用户信息
        文本=文本.rsplit('@',1)[1]#只留主机
    if 文本=='':#切完是空
        return None#失败
    端口文=None#还没看到端口
    if 文本.startswith('['):#IPv6
        右=文本.find(']')#右括号
        if 右<0:#没有
            return None#失败
        内部=文本[1:右]#括号内
        其余=文本[右+1:]#括号后
        if 其余=='':#没有端口
            端口文=None#没写
        elif 其余.startswith(':'):#端口
            端口文=其余[1:]#冒号后
        else:#括号后还有别的
            return None#失败
        段=解析ipv6(内部)#八段
        if 段 is None:#非法
            return None#失败
        主机名='['+序列化ipv6(段)+']'#带方括号的规范形
    else:#域名或 IPv4
        if ':' in 文本:#可能有端口
            主机文,端口文=文本.rsplit(':',1)#最后一处冒号
        else:#没有端口
            主机文=文本#整段
            端口文=None#没写
        if 主机文=='':#空主机
            return None#失败
        主机名=解析主机名(主机文)#规范主机名
        if 主机名 is None:#非法
            return None#失败
    端口=解析端口(端口文,方案)#这个方案下的端口
    if 端口 is None:#端口非法
        return None#失败
    主机=主机名 if 端口=='' else 主机名+':'+端口#host
    return 权威网址(主机名,端口,主机,方案)#解析结果


def 规范权威(条目,解析):
    '没写端口时是 hostname，否则 hostname:port。默认端口改到另一个方案上仍算写了'
    if 解析.port!='':#这个方案下端口非默认
        端口=解析.port#就用它
    else:#可能没写，也可能是默认端口
        另一='https:' if 解析.protocol=='http:' else 'http:'#另一个特殊方案
        另一解析=解析权威(条目,另一)#再用原文字解析
        端口='' if 另一解析 is None else 另一解析.port#另一方案看到的端口
    if 端口=='':#两个方案都没有非默认端口
        return 解析.hostname#只有主机名
    return 解析.hostname+':'+端口#主机名加端口


def 断言受信任权威(条目):
    '配置的 trustedHosts 必须是规范形态的裸权威。会被改写的写法在加载时失败'
    解析=解析权威(条目)#按 http 解析
    if 解析 is not None and 规范权威(条目,解析)==条目.lower():#解析后与原文小写一致
        return#通过
    raise 连接错误('client-connection: trustedHosts entry '+编码json(条目)+' is not a bare host[:port] authority')#拒绝


def 是否远程权威(条目):
    '已通过断言的权威。解析不到或不是回环则为真'
    解析=解析权威(条目)#解析
    if 解析 is None:#解析不到
        return True#当成远程
    return not 是否回环主机名(解析.hostname)#不是回环


def 请求头表(请求):
    '对象用 headers，字典用同名键'
    if isinstance(请求,dict):#字典
        return 请求['headers']#头
    return 请求.headers#头


def 是否受信任接口请求(请求,受信任表,绑定主机=None,协议='http:'):
    'Host 必须是回环、绑定地址或受信任权威，浏览器标记必须同源'
    头表=请求头表(请求)#头
    主机文=取头(头表,'host')#Host
    if 主机文 is None:#没有 Host
        return False#拒绝
    主机解析=解析权威(主机文,协议)#按监听方案解析
    if 主机解析 is None:#解析不到
        return False#拒绝
    绑定相符=False#绑定地址
    if 绑定主机 is not None:#有绑定地址
        区=绑定主机.find('%')#区域标识
        地址=绑定主机 if 区<0 else 绑定主机[:区]#去掉区域
        待解析='['+地址+']' if ':' in 地址 else 地址#IPv6 加括号
        绑定解析=解析权威(待解析)#解析绑定地址
        绑定相符=绑定解析 is not None and 绑定解析.hostname==主机解析.hostname#只比主机名
    受信任=False#名单
    for 条目 in 受信任表:#逐条
        条目解析=解析权威(条目,协议)#按同一方案
        if 条目解析 is None:#这条解析不到
            continue#看下一条
        规范=规范权威(条目,条目解析)#规范形
        if 规范==条目解析.hostname:#没写端口，任意端口
            if 条目解析.hostname==主机解析.hostname:#主机名相同
                受信任=True#命中
                break#不用再看
        elif 条目解析.host==主机解析.host:#写了端口，必须整段相同
            受信任=True#命中
            break#不用再看
    if not 是否回环主机名(主机解析.hostname) and not 受信任 and not 绑定相符:#三种都不是
        return False#拒绝
    if 取头(头表,'sec-fetch-site')=='cross-site':#明确的跨站
        return False#拒绝
    来源=取头(头表,'origin')#Origin
    if 来源 is None:#没有 Origin
        return True#Host 围栏已经够了
    来源文本=预处理(来源)#同样去掉空白
    冒号=来源文本.find(':')#方案
    if 冒号<1 or not 来源文本.startswith('//',冒号+1):#不是绝对 URL
        return False#拒绝
    来源方案=来源文本[:冒号+1].lower()#含冒号
    if 来源方案=='https:':#https
        比较方案='https:'#用 https 比默认端口
    elif 来源方案=='http:':#http
        比较方案='http:'#用 http 比默认端口
    else:#其它方案或 null
        return False#拒绝
    来源权威=来源文本[冒号+3:]#双斜杠后面
    来源解析=解析权威(来源权威,比较方案)#解析来源权威
    主机再解析=解析权威(主机文,比较方案)#用来源的方案再解析 Host
    return 来源解析 is not None and 主机再解析 is not None and 来源解析.host==主机再解析.host#host 相同
