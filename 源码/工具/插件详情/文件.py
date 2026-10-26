'插件详情文档的只读文件来源：本地包目录，以及公共文件 CDN 上已发布的 npm 版本。来源在调用之间不保留状态'
import os,stat#本地路径与文件种类
import re#README 名称
import urllib.error#网络失败
import urllib.request#同步 HTTP
from urllib.parse import quote,urljoin,urlparse#路径编码与重定向
from typing import Literal,TypedDict#读到的记录

__all__=[#仅中文公开名
    '详情失败','找到的文件','详情文件','自述文件名表','拼接路径','自述文件名','按名读自述','本地文件',
    '远程文件选项','取到正文成功','取到正文失败','取到正文','请求正文','npm文件来源','npm文件来源顺序','编码路径','npm文件',
]#公开面结束

自述模式=re.compile(r'^readme(?:\.md|\.markdown)?\Z',re.ASCII|re.IGNORECASE)#任意大小写的 README、README.md、README.markdown
最大重定向=3#同一源内跟随的重定向次数

class 不处理状态(urllib.request.HTTPErrorProcessor):#任意状态码原样交回
    '把任意状态码的响应原样交回，不跟随、不抛'
    def http_response(自身,请求对象,响应):#http
        '原样交回'
        return 响应#调用方自己看状态
    https_response=http_response#https 同样原样交回

不跟随=urllib.request.build_opener(不处理状态)#不自动跳转

class 详情失败(Exception):#不得回退的读取
    '不得回退的读取：来源存在但拒绝、失败或超过上限'
    def __init__(自身,种类,消息):#记下种类与诊断
        '记下失败种类与诊断。种类是 too-large、network、denied、git-unavailable、invalid'
        super().__init__(消息)#诊断给调用方
        自身.name='DetailFailure'#错误名原样
        自身.reason=种类#机器比对的种类

class 找到的文件(TypedDict):#按名称找到的一个文件
    '按名称找到的一个文件'
    path:str#相对源根、以 / 分隔的路径
    bytes:bytes#文件字节

class 详情文件:#一个根下的文件
    '一个根下的文件。相对路径以 / 分隔，不以 / 开头，不含 . 或 .. 段'
    def __init__(自身,键,读取,自述):#记下身份与两个读取函数
        '记下内容身份与读取函数。相同键的两个来源读到相同字节'
        自身.键=键#内容身份
        自身.读取实现=读取#读一个普通文件
        自身.自述实现=自述#读目录 README

    def 读取(自身,路径,最大字节,信号):#读一个普通文件
        '读一个普通文件。不存在时没有返回；来源失败或超过最大字节时抛详情失败'
        return 自身.读取实现(路径,最大字节,信号)#交给来源

    def 读自述(自身,目录,最大字节,信号):#读目录 README
        '读目录的 README。没有时没有返回；来源失败或超过最大字节时抛详情失败'
        return 自身.自述实现(目录,最大字节,信号)#交给来源

自述文件名表=('README.md','readme.md','Readme.md','README.markdown','README')#不能列目录时按这个顺序试

def 拼接路径(目录,名称):#目录加文件名
    '把目录和文件名拼成相对根的路径。目录为空表示根'
    if 目录=='':#根
        return 名称#不再加斜杠
    return 目录+'/'+名称#相对根

def 等级(名称):#名单中的次序
    '按自述文件名表的顺序分级，不在表里的排在后面'
    if 名称 in 自述文件名表:#精确命中名单
        return 自述文件名表.index(名称)#越靠前越优先
    return len(自述文件名表)#其余排在后面

def 自述排序键(名称):#排序键
    '先按名单顺序，再按名称'
    return (等级(名称),名称)#稳定的先后

def 自述文件名(名称表):#从目录项里挑 README
    '按自述文件名表的顺序，再按名称，从目录项里挑 README'
    候选=[]#命中模式的名字
    for 名称 in 名称表:#逐个目录项
        if 自述模式.search(名称) is not None:#是 README
            候选.append(名称)#收下
    候选.sort(key=自述排序键)#名单优先，然后按名称
    if len(候选)==0:#没有
        return None#没有 README
    return 候选[0]#最优先的一个

def 按名读自述(读取,目录,最大字节,信号,名称表=None):#不能列目录时按名称试
    '读名称表里第一个存在的 README。读取抛出的详情失败原样抛出'
    if 名称表 is None:#默认名单
        名称表=自述文件名表#固定顺序
    for 名称 in 名称表:#按顺序试
        路径=拼接路径(目录,名称)#相对根
        字节=读取(路径,最大字节,信号)#读这一个
        if 字节 is not None:#存在
            return {'path':路径,'bytes':字节}#第一个存在的
    return None#都不存在

def 过大(标签,最大字节):#超过上限
    '超过字节上限。种类 too-large 原样，诊断给调用方'
    return 详情失败('too-large',f'{标签}超过{最大字节}字节')#不回退

def 若已中止则抛出(信号):#中止优先于网络失败
    '信号已置位则抛出其上的原因。信号是带 is_set 与原因的事件'
    if 信号 is None or not 信号.is_set():#无信号或仍活着
        return#继续
    if 信号.原因 is not None:#有承载原因
        raise 信号.原因#原样抛出
    raise RuntimeError('The operation was aborted')#无原因时的英文诊断

def 错误文本(错误):#失败文本
    '取出失败文本'
    return str(错误)#异常消息或普通值

def 取源(文本):#比较重定向是否还在原来的源
    'http(s) 的源；其他方案是 null'
    部分=urlparse(文本)#拆开
    方案=部分.scheme.lower()#方案小写
    if 方案 not in ('http','https'):#file、javascript 等
        return 'null'#不透明源
    try:
        主机=部分.hostname#主机
    except ValueError:
        return 'null'#坏主机
    if not 主机:#没有主机
        return 'null'#不透明源
    主机=主机.lower()#主机小写
    try:
        端口=部分.port#端口
    except ValueError:
        return 'null'#坏端口
    if 端口 is not None and not ((方案=='http' and 端口==80) or (方案=='https' and 端口==443)):#非默认端口
        return 方案+'://'+主机+':'+str(端口)#带端口
    return 方案+'://'+主机#默认端口不写

def 能解析(位置,基址):#Location 能否构成绝对网址
    '位置相对基址能否构成绝对网址'
    try:
        绝对=urljoin(基址,位置)#拼绝对网址
    except ValueError:
        return False#拼不出来
    部分=urlparse(绝对)#拆开
    if 部分.scheme=='':#仍然相对
        return False#不能当绝对网址
    if 部分.scheme.lower() in ('http','https'):#需要主机
        try:
            主机=部分.hostname#主机
        except ValueError:
            return False#坏主机
        return bool(主机)#有主机才算
    return True#其他方案可解析

def 本地文件(根,修订):#本地包目录
    '本地包目录里的文件。真实位置离开该目录的路径按不存在读。修订进内容键，重装后视为另一份文件'
    键='local:'+根+'@'+修订#内容身份

    def 读取(路径,最大字节,信号=None):#读一个普通文件
        '读一个普通文件；离开目录、缺失或不可读时没有返回'
        try:
            if not os.path.exists(根):#包目录不存在
                return None#没有这个文件
            基=os.path.realpath(根)#包目录的真实位置
            拼接=os.path.join(基,*路径.split('/'))#按 / 段接上
            if not os.path.exists(拼接):#缺失或断链
                return None#包没有提供
            文件=os.path.realpath(拼接)#跟随到真实文件
            内部=os.path.relpath(文件,基)#相对包目录
            if 内部=='.' or 内部=='..' or 内部.startswith('..'+os.sep) or os.path.isabs(内部):#离开目录
                return None#按不存在
            信息=os.lstat(文件)#真实目标的元数据
            if not stat.S_ISREG(信息.st_mode):#不是普通文件
                return None#目录和设备都不读
            if 信息.st_size>最大字节:#声明的大小已超
                raise 过大(路径,最大字节)#不读
        except 详情失败:
            raise#上限是失败，不是缺失
        except (OSError,ValueError):
            return None#缺失、无权限，或 Windows 上跨盘相对路径
        with open(文件,'rb') as 句柄:#读字节
            字节=句柄.read()#整文件
        if len(字节)>最大字节:#读的时候变大了
            raise 过大(路径,最大字节)#仍然拒绝
        return 字节#文件字节

    def 读自述(目录,最大字节,信号):#列出目录再挑 README
        '列出目录里的普通文件和符号链接，再按名称读 README'
        try:
            分段=[] if 目录=='' else 目录.split('/')#根没有段
            列表目录=根 if len(分段)==0 else os.path.join(根,*分段)#要列的目录
            名称表=[]#文件与链接的名字
            with os.scandir(列表目录) as 扫描:#不跟随链接
                for 条目 in 扫描:#逐项
                    if 条目.is_file(follow_symlinks=False) or 条目.is_symlink():#普通文件或链接
                        名称表.append(条目.name)#只留名字
        except OSError:
            return None#目录不存在或不可读
        名称=自述文件名(名称表)#挑一个 README
        if 名称 is None:#没有
            return None#无 README
        路径=拼接路径(目录,名称)#相对根
        字节=读取(路径,最大字节,信号)#再走真实路径检查
        if 字节 is None:#链接跑到目录外，或不是普通文件
            return None#按没有
        return {'path':路径,'bytes':字节}#找到的 README

    return 详情文件(键,读取,读自述)#这一份来源

class 远程文件选项(TypedDict):#远程来源的截止与寿命
    '远程文件来源的请求设置'
    timeoutMs:int#单次读取的截止毫秒
    lifetime:object#比单次读取更长的寿命信号，带 is_set 与原因

class 取到正文成功(TypedDict):#2xx 正文
    '2xx 响应的正文'
    ok:Literal[True]#成功
    bytes:bytes#正文

class 取到正文失败(TypedDict):#非 2xx
    '非 2xx 的状态，含转到其他源的重定向'
    ok:Literal[False]#没有正文
    status:int#状态码

取到正文=取到正文成功|取到正文失败#一次 HTTP 答案

def 请求正文(网址,最大字节,信号,选项):#有界 GET
    """GET 一个网址，只跟随同一源内的重定向，正文不超过最大字节。
    没有响应或正文失败是 network；超过最大字节是 too-large。
    中止在每次请求前检查，套接字超时对应该次读取的截止"""
    若已中止则抛出(信号)#调用方已经中止
    若已中止则抛出(选项['lifetime'])#服务已经停
    超时秒=选项['timeoutMs']/1000#urllib 用秒
    目标=网址#当前跳
    响应=None#最近一次响应
    跳=0#已经跟随的次数
    while True:#至少请求一次
        若已中止则抛出(信号)#这一跳之前再查
        若已中止则抛出(选项['lifetime'])#寿命同样再查
        请求=urllib.request.Request(目标,method='GET')#GET
        try:
            响应=不跟随.open(请求,timeout=超时秒)#不自动跳转
        except Exception as 错误:
            若已中止则抛出(信号)#中止不是网络失败
            若已中止则抛出(选项['lifetime'])#寿命中止同样
            raise 详情失败('network',f'无法请求 {目标}: {错误文本(错误)}') from 错误#网络失败
        位置=响应.headers.get('Location') if 300<=响应.status<400 else None#重定向位置
        绝对=urljoin(目标,位置) if 位置 is not None else ''#相对位置拼到当前跳
        if 位置 is None or not 能解析(位置,目标) or 取源(绝对)!=取源(网址) or 跳==最大重定向:#不再跟随
            break#用这一次响应
        响应.close()#丢掉这一跳的正文
        目标=绝对#下一跳仍须在最初的源里
        跳+=1#计数
    答案=响应#循环至少跑过一次
    if not (200<=答案.status<300):#非 2xx，含转到其他源的 3xx
        状态=答案.status#状态码
        答案.close()#不读正文
        return {'ok':False,'status':状态}#交给调用方
    声明=答案.headers.get('Content-Length')#声明的长度
    try:
        长度=int(声明) if 声明 else 0#缺席或空当 0
    except ValueError:
        长度=0#无法解析的长度不当成超限
    if 长度>最大字节:#声明已超
        答案.close()#不读
        raise 过大(网址,最大字节)#too-large
    块组=[]#正文块
    大小=0#已读字节
    try:
        while True:#按块读，超限就停
            块=答案.read(8192)#一块
            if not 块:#读完
                break#结束
            大小+=len(块)#累计
            if 大小>最大字节:#正文超限
                raise 过大(网址,最大字节)#too-large
            块组.append(块)#收下
    except 详情失败:
        raise#上限原样抛出
    except Exception as 错误:
        raise 详情失败('network',f'无法读取 {网址}: {错误文本(错误)}') from 错误#正文失败
    finally:
        答案.close()#无论成败都关掉
    return {'ok':True,'bytes':b''.join(块组)}#2xx 正文

npm文件来源=('jsdelivr','unpkg','npmmirror')#全部 npm 文件 CDN，默认顺序

def npm文件来源顺序(已配置,优先=None):#按调用方偏好重排已配置的 CDN
    '已配置且被偏好的 CDN 按偏好顺序在前，然后是其余已配置的 CDN。没配置的偏好不会被询问'
    if 优先 is None:#没有偏好
        优先=()#保持配置顺序
    靠前=[]#又配置又偏好的
    for 来源 in 已配置:#配置顺序
        if 来源 in 优先:#在偏好里
            靠前.append(来源)#先收集
    def 优先键(来源):#偏好名单中的位置
        '偏好名单中的位置'
        return 优先.index(来源)#越靠前越先问
    靠前.sort(key=优先键)#按偏好顺序
    其余=[]#配置了但没被提前的
    for 来源 in 已配置:#仍按配置顺序
        if 来源 not in 靠前:#不在靠前
            其余.append(来源)#接在后面
    return 靠前+其余#先问到后问

def 编码路径(路径):#URL 路径段
    '把以 / 分隔的路径逐段做百分号编码'
    段表=[]#编码后的段
    for 段 in 路径.split('/'):#逐段
        段表.append(quote(段,safe="-_.!~*'()"))#与 encodeURIComponent 同一组不编码字符
    return '/'.join(段表)#再用 / 接回

def jsdelivr网址(名称,版本,路径):#jsDelivr
    'jsDelivr 上该文件的网址'
    return 'https://cdn.jsdelivr.net/npm/'+名称+'@'+版本+'/'+编码路径(路径)#包名与版本不编码

def unpkg网址(名称,版本,路径):#unpkg
    'unpkg 上该文件的网址'
    return 'https://unpkg.com/'+名称+'@'+版本+'/'+编码路径(路径)#包名与版本不编码

def npmmirror网址(名称,版本,路径):#npmmirror
    'npmmirror 上该文件的网址'
    return 'https://registry.npmmirror.com/'+名称+'/'+版本+'/files/'+编码路径(路径)#版本在路径里

npm网址={#来源名到网址
    'jsdelivr':jsdelivr网址,
    'unpkg':unpkg网址,
    'npmmirror':npmmirror网址,
}#三个 CDN

def npm文件(名称,版本,来源表,选项):#已发布的 npm 版本
    '按给定顺序从公共文件 CDN 读一个已发布版本。404 表示包里没有该文件；网络失败或其他状态再问下一个'
    键='npm:'+名称+'@'+版本#内容身份

    def 读取(路径,最大字节,信号):#问遍 CDN
        '404 表示包里没有该文件；网络失败或其他状态再问下一个 CDN'
        失败列表=[]#非 404 的失败
        for 来源 in 来源表:#按顺序
            网址=npm网址[来源](名称,版本,路径)#这个 CDN
            try:
                正文=请求正文(网址,最大字节,信号,选项)#有界 GET
            except 详情失败 as 错误:
                if 错误.reason!='network':#too-large 等不换 CDN
                    raise#原样
                失败列表.append(str(错误))#记下网络失败
                continue#问下一个
            if 正文['ok']:#2xx
                return 正文['bytes']#文件字节
            if 正文['status']==404:#包里没有
                return None#不是失败
            失败列表.append(网址+': HTTP '+str(正文['status']))#其他状态问下一个
        raise 详情失败('network','; '.join(失败列表))#全部 CDN 都没给出文件

    def 读自述(目录,最大字节,信号):#不能列目录
        '不能列目录时按固定名称试 README'
        return 按名读自述(读取,目录,最大字节,信号)#默认名单

    return 详情文件(键,读取,读自述)#这一份来源
