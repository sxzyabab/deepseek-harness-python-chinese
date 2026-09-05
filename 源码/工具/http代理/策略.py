"""代理策略解析：本包与传输无关的纯半边。把启动环境收成一份代理策略，并回答给定网址是否走代理、走哪一个。

这里不引入 undici，因此在没有 Node 传输的运行时里仍可加载，与 dsh-web-fetch-http 的求值面一致。
"""
import re#拆分绕过列表
from urllib.parse import urlparse as 解析网址#对应 URL.parse
__all__=[#仅中文公开名
    '环境查找','环回绕过代理','策略环境名','代理环境名','代理策略','直连策略',
    '代理诊断','代理解析结果','是否受支持代理网址','是否环回主机','是否绕过代理',
    '解析代理策略','按网址取代理',
]#公开面结束

#环境查找面：实现 取(名称)->{'value':str}|None；启动器快照在结构上满足它。
环境查找=object#名义类型，调用方提供带 取 方法的对象

#合并进每一份策略绕过代理的 loopback 条目。若代理也承接 Harness 自己的 loopback 流量，会形成路由回环。
#::1 与 [::1] 都列出，因为解析字符串也会交给匹配器，而裸写的 ::1 可能被读成主机 : 端口 1。
环回绕过代理=('localhost','127.0.0.1','::1','[::1]')#强制绕过的 loopback 字面量

#各策略字段拥有的环境名，小写在前——undici 先读小写，因此两种大小写总是一起写入或一起清除。
策略环境名={#策略字段到环境名的映射
    'http代理':['http_proxy','HTTP_PROXY'],#http 代理名
    'https代理':['https_proxy','HTTPS_PROXY'],#https 代理名
    '绕过代理':['no_proxy','NO_PROXY'],#绕过列表名
}#策略环境名结束

#承载代理配置的全部环境名，含本包会解析但从不写回的 ALL_PROXY 兜底。
代理环境名=tuple(#全部代理相关环境名
    [名称 for 名称们 in 策略环境名.values() for 名称 in 名称们]+#策略字段对应的大小写名
    ['all_proxy','ALL_PROXY']#全协议兜底
)#代理环境名结束

支持协议=frozenset(['http:','https:'])#可接受的代理协议
袜子协议=frozenset(['socks:','socks4:','socks4a:','socks5:','socks5h:'])#SOCKS 族协议

#已解析的出站代理策略。纯数据、无方法：工作线程经结构化克隆接收它，两侧跑同一份策略。
#形如 {'http代理'?:str,'https代理'?:str,'绕过代理':str,'来源':'env'|'none'}
代理策略=dict#名义类型

直连策略={'绕过代理':'','来源':'none'}#什么都不代理的策略

#拒绝诊断：{'种类':'socks'|'invalid','来源':str,'消息':str}
代理诊断=dict#名义类型

#解析结果：{'策略':代理策略,'诊断':list}
代理解析结果=dict#名义类型

缺席候选={'种类':'缺席'}#无人填充的槽位

def 读环境(环境,小写名):#按 undici 优先序读环境名
    """按 undici 的优先序读一个环境名——小写优先、大写兜底——空白值视为未设置。

    空白要紧：undici 自己的链会让空的小写名盖住已填充的大写名。
    """
    for 名称 in (小写名,小写名.upper()):#小写再大写
        条目=环境.取(名称)#取胜出条目
        if 条目 is None:#本层未提供
            continue#试下一个名
        值=条目['value'].strip()#修剪
        if 值!='':#非空即胜出
            return {'value':值,'name':名称}#胜出值与名字
    return None#皆未设置

def 接受代理网址(候选,诊断们):#校验并分类一个候选网址
    """校验一个候选代理网址。返回已接受 / 已拒绝 / 缺席。"""
    if 候选 is None:#无人提供
        return 缺席候选#缺席
    解析结果=解析网址(候选['value'])#对应 URL.parse
    协议=(解析结果.scheme+':') if 解析结果.scheme else ''#带冒号的协议
    if 协议=='':#无法解析出协议
        诊断们.append({#追加无效诊断
            '种类':'invalid',#种类为无效
            '来源':候选['name'],#来源变量名
            '消息':候选['name']+' is not a valid URL; connecting directly',#英文诊断字面量不翻译
        })#诊断结束
        return {'种类':'已拒绝'}#记为被拒
    if 协议 in 袜子协议:#SOCKS 族
        诊断们.append({#追加 SOCKS 诊断
            '种类':'socks',#种类为 socks
            '来源':候选['name'],#来源变量名
            '消息':候选['name']+' names a SOCKS proxy, which is not supported; connecting directly for that scheme — set an http:// or https:// proxy URL instead',#英文诊断字面量不翻译
        })#诊断结束
        return {'种类':'已拒绝'}#记为被拒
    if 协议 not in 支持协议:#不受支持的协议
        诊断们.append({#追加无效协议诊断
            '种类':'invalid',#种类为无效
            '来源':候选['name'],#来源变量名
            '消息':候选['name']+' uses the unsupported '+协议+'// scheme; connecting directly for that scheme — set an http:// or https:// proxy URL instead',#英文诊断字面量不翻译
        })#诊断结束
        return {'种类':'已拒绝'}#记为被拒
    return {'种类':'已接受','值':候选['value']}#接受该值

def 是否受支持代理网址(值):#是否为本包可接受的代理网址
    """代理网址是否为本包接受：可解析，且协议为 http: 或 https:。与接受代理网址同一检验，但不产诊断。"""
    解析结果=解析网址(值)#解析网址
    协议=(解析结果.scheme+':') if 解析结果.scheme else ''#带冒号的协议
    return 协议 in 支持协议#可解析且协议受支持

def 解析协议槽(本槽,*兜底们):#解析单协议代理
    """从一个协议自己的槽位解析代理，再走兜底——但仅当该协议自己的槽位为空。被拒槽位让该协议保持直连。"""
    if 本槽['种类']=='已接受':#本槽已接受
        return 本槽['值']#本槽值
    if 本槽['种类']=='已拒绝':#本槽被拒则直连
        return None#直连
    for 值 in 兜底们:#缺席则按兜底取首个有值项
        if 值 is not None:#有值
            return 值#采用兜底
    return None#皆无

def 合并环回(绕过代理):#合并 loopback 绕过
    """把环回绕过代理合并进绕过列表，保留调用方条目与顺序。已含 * 的列表会绕过一切，原样返回。"""
    条目们=[条目.strip() for 条目 in re.split(r'[,\s]+',绕过代理 or '') if 条目.strip()!='']#拆成非空条目
    if '*' in 条目们:#* 已绕过全部
        return '*'#原样
    已有=set(条目.lower() for 条目 in 条目们)#已有条目小写集合
    追加=[条目 for 条目 in 环回绕过代理 if 条目.lower() not in 已有]#缺失的 loopback
    return ','.join(条目们+追加)#追加缺失的 loopback

def 拆主机端口(条目):#拆主机与端口
    """把一个绕过条目拆成主机与可选端口。

    裸 IPv6 字面量含多个冒号且无端口，因此只有单冒号条目才拆；方括号字面量的端口取自括号之后。
    """
    if 条目.startswith('['):#方括号 IPv6
        右括号=条目.find(']')#找右括号
        if 右括号!=-1:#括号成对
            剩余=条目[右括号+1:]#括号后剩余
            主机=条目[1:右括号]#括号内主机
            if 剩余.startswith(':'):#有端口
                return {'host':主机,'port':剩余[1:]}#主机与端口
            return {'host':主机}#无端口
    冒号=条目.find(':')#首个冒号
    if 冒号!=-1 and 条目.find(':',冒号+1)==-1:#恰好一个冒号
        return {'host':条目[:冒号],'port':条目[冒号+1:]}#主机与端口
    return {'host':条目}#无端口

八位组=r'(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)'#合法 IPv4 八位组
环回Ipv4=re.compile(r'^127\.'+八位组+r'\.'+八位组+r'\.'+八位组+r'$')#整个 127.0.0.0/8 段

def 是否环回主机(主机名):#是否为本机 loopback 主机
    """主机是否点名本机。只匹配四个字面量会让 127.0.0.2 与其余 127/8 仍走代理。"""
    主机=re.sub(r'^\[|\]$','',主机名)#去方括号
    主机=re.sub(r'\.$','',主机).lower()#去尾点并小写
    if 主机=='localhost' or 主机.endswith('.localhost'):#localhost 族
        return True#环回
    if 主机=='::1' or 主机=='::' or 主机=='0.0.0.0':#IPv6 环回与未指定
        return True#环回
    #IPv4 映射的 IPv6：::ffff:127.0.0.1 与 ::ffff:7f00:1 是同一地址。
    映射匹配=re.match(r'^::ffff:([0-9a-f]{1,4}):[0-9a-f]{1,4}$',主机)#十六进制映射
    if 映射匹配 is not None:#十六进制映射高 16 位
        return (int(映射匹配.group(1),16)>>8)==127#高字节为 127 则 loopback
    待测=主机[7:] if 主机.startswith('::ffff:') else 主机#点分或 127 段
    return 环回Ipv4.match(待测) is not None#点分或 127 段

def 是否绕过代理(绕过代理,网址):#网址是否被绕过列表免除
    """判断绕过列表是否免除某个网址。条目写主机并连同子域名匹配；可带 :port；* 绕过一切。不匹配 CIDR。

    网址为 urllib.parse 解析结果（scheme / hostname / port）。
    """
    原始主机=网址.hostname or ''#主机名
    主机=re.sub(r'^\[|\]$','',原始主机)#去方括号
    主机=re.sub(r'\.$','',主机).lower()#去尾点并小写
    if 网址.port is not None:#显式端口
        端口=str(网址.port)#数字端口
    elif 网址.scheme=='https':#缺省 https
        端口='443'#https 缺省
    else:#缺省 http
        端口='80'#http 缺省
    for 原始 in re.split(r'[,\s]+',绕过代理):#逐条匹配
        条目=原始.strip().lower()#修剪并小写
        if 条目=='':#跳过空条目
            continue#下一条
        if 条目=='*':#* 绕过全部
            return True#免除
        拆分=拆主机端口(条目)#拆主机端口
        if 拆分.get('port') is not None and 拆分['port']!=端口:#端口不符
            continue#跳过
        候选=re.sub(r'^\*\.?','',拆分['host'])#去掉前缀通配
        候选=re.sub(r'\.$','',候选)#去掉尾点
        if 候选=='':#空主机跳过
            continue#下一条
        if 主机==候选 or 主机.endswith('.'+候选):#精确或子域匹配
            return True#免除
    return False#未匹配

def 解析代理策略(环境):#从环境解析策略
    """为本进程解析出站代理策略。

    协议自己的变量胜出，然后是 ALL_PROXY，再然后——仅对 HTTPS——是 HTTP 代理，与 undici 对齐。
    """
    诊断们=[]#诊断收集器
    全协议=接受代理网址(读环境(环境,'all_proxy'),诊断们)#全协议兜底候选
    全协议值=全协议['值'] if 全协议['种类']=='已接受' else None#可用的 ALL_PROXY 值
    环境Http=接受代理网址(读环境(环境,'http_proxy'),诊断们)#http 槽候选
    环境Https=接受代理网址(读环境(环境,'https_proxy'),诊断们)#https 槽候选
    http代理=解析协议槽(环境Http,全协议值)#解析 http 代理
    #HTTPS 最后回退到 HTTP 代理，与 undici 对齐——但绝不越过用户为 HTTPS 点名却被本包拒绝的值。
    https代理=解析协议槽(环境Https,全协议值,http代理)#解析 https 代理
    if http代理 is None and https代理 is None:#两边皆无则直连
        return {'策略':dict(直连策略),'诊断':诊断们}#直连
    绕过条目=读环境(环境,'no_proxy')#绕过列表原始值
    策略={'绕过代理':合并环回(绕过条目['value'] if 绕过条目 is not None else None),'来源':'env'}#环境策略
    if http代理 is not None:#有 http 才写入
        策略['http代理']=http代理#写入 http
    if https代理 is not None:#有 https 才写入
        策略['https代理']=https代理#写入 https
    return {'策略':策略,'诊断':诊断们}#解析结果

def 按网址取代理(策略,网址):#按策略解析单网址代理
    """在一份策略下解析某个网址走哪个代理。

    网址为 urllib.parse 解析结果。直连则为 None。
    """
    if 网址.scheme=='https':#https 源
        代理=策略.get('https代理')#https 代理
    elif 网址.scheme=='http':#http 源
        代理=策略.get('http代理')#http 代理
    else:#其它协议
        代理=None#无代理
    if 代理 is None:#该协议无代理
        return None#直连
    if 是否环回主机(网址.hostname or ''):#本机永远直连
        return None#直连
    return None if 是否绕过代理(策略['绕过代理'],网址) else 代理#绕过则直连，否则走代理
