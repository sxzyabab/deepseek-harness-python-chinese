'node HTTP 与 fetch 形态处理函数之间的桥'
import json,threading,urllib.parse#正文、排空等待与内部基址
from .rpc import 中止控制器,同步等待#断开即中止，处理函数可以返回期约

默认最大请求正文字节=300*1024*1024#300 MiB，覆盖默认图像上限的 base64 膨胀


class 头映射:
    '小写头名。get 与 entries 对齐 Fetch Headers'
    def __init__(自身,原始=None):
        '只收下字符串值'
        自身._表={}#小写名到值
        if isinstance(原始,dict):#字典
            for 键,值 in 原始.items():#逐个
                if isinstance(键,str) and isinstance(值,str):#字符串
                    自身._表[键.lower()]=值#收下

    def get(自身,名):
        '按名读取，大小写不敏感'
        if not isinstance(名,str):#不是字符串
            return None#没有
        return 自身._表.get(名.lower())#值或 None

    def set(自身,名,值):
        '写入一个头'
        自身._表[名.lower()]=值#收下

    def entries(自身):
        '全部头'
        return list(自身._表.items())#列表


class 桥网址:
    '桥里用到的 pathname 与 href'
    def __init__(自身,文本):
        '空路径当成 /'
        拆=urllib.parse.urlsplit(文本)#拆开
        自身.href=文本#绝对地址
        自身.pathname=拆.path if 拆.path else '/'#路径
        自身.protocol=(拆.scheme+':') if 拆.scheme else ''#方案


class 连接请求:
    'fetch Request 里桥和 RPC 会用到的字段'
    def __init__(自身,网址文本,方法,头,正文,信号):
        '记下方法、绝对地址、头、正文和中止信号'
        自身.url=网址文本#绝对地址
        自身.method=方法#方法
        自身.headers=头 if hasattr(头,'get') and not isinstance(头,dict) else 头映射(头)#头
        自身._正文=正文#字节或空
        自身.signal=信号#中止

    def json(自身):
        '把正文解析成 JSON。不是 JSON 就抛'
        正文=自身._正文#正文
        if isinstance(正文,str):#文本
            return json.loads(正文)#对象
        if isinstance(正文,(bytes,bytearray)):#字节
            return json.loads(bytes(正文).decode('utf-8'))#对象
        if 正文 is None:#没有正文
            raise ValueError('body is not JSON')#拒绝
        return 正文#已经是对象


class 连接响应:
    'fetch Response 里桥会写回去的状态、头和正文块'
    def __init__(自身,正文=b'',状态=200,头=None):
        '字符串按 utf-8。正文为 None 时 body 为空'
        自身.status=状态#状态
        自身.ok=状态>=200 and 状态<300#2xx
        自身.headers=头 if hasattr(头,'entries') and not isinstance(头,dict) else 头映射(头)#头
        if 正文 is None:#明确没有正文
            自身.body=None#空
            自身._正文=b''#空字节
        else:#有正文
            if isinstance(正文,str):#文本
                正文=正文.encode('utf-8')#编码
                if 自身.headers.get('content-type') is None:#没写类型
                    自身.headers.set('content-type','text/plain;charset=UTF-8')#默认纯文本
            elif not isinstance(正文,(bytes,bytearray)):#其它
                正文=bytes(正文)#收成字节
            自身._正文=bytes(正文)#一份
            自身.body=[自身._正文]#一块，避免按字节迭代


def 读取正文字节(请求):
    '网页服务器按 Content-Length 读。没有这个方法则按块迭代'
    if hasattr(请求,'readBody'):#当前网页服务器
        数据=请求.readBody()#按声明长度
        if isinstance(数据,str):#文本
            return 数据.encode('utf-8')#字节
        return bytes(数据)#字节
    块=[]#分块
    for 片 in 请求:#逐块
        if isinstance(片,str):#文本
            片=片.encode('utf-8')#编码
        块.append(bytes(片))#收下
    return b''.join(块)#合并


def 桥接(请求,响应,接口处理,对等体,最大请求正文字节=None):
    '把一条 HTTP 请求桥到 fetch 形态的处理函数。客户端断开会中止'
    if 最大请求正文字节 is None:#没传
        最大请求正文字节=默认最大请求正文字节#默认上限
    中止=中止控制器()#断开即中止

    def 连接关闭():
        '响应还没正常结束，就中止这次处理'
        if not 响应.writableEnded:#不是正常 end
            中止.abort()#中止

    响应.on('close',连接关闭)#挂在响应上，不挂在请求上
    原始=请求.url if getattr(请求,'url',None) else '/'#没有 url 当根
    绝对=urllib.parse.urljoin('http://dsh.internal',原始)#内部基址
    网址=桥网址(绝对)#路径
    方法=请求.method if getattr(请求,'method',None) else 'GET'#方法
    头={}#只留字符串头
    原始头=请求.headers#头
    if isinstance(原始头,dict):#字典
        for 键,值 in 原始头.items():#逐个
            if isinstance(值,str):#字符串
                头[键]=值#收下
    取模式=接口处理['requestBodyMode'] if isinstance(接口处理,dict) else 接口处理.requestBodyMode#正文模式
    正文模式=取模式({'method':方法,'url':网址})#先问模式，再读正文
    已读=False#是否已经把 node 正文读完
    if 正文模式=='buffered':#有上限的缓冲
        声明=原始头.get('content-length') if isinstance(原始头,dict) else None#声明长度
        if isinstance(声明,str):#字符串长度
            try:#转数字
                声明长度=float(声明)#数字
            except ValueError:#不是数字
                声明长度=float('nan')#不当成超限
            if 声明长度==声明长度 and 声明长度>最大请求正文字节:#超过上限
                响应.writeHead(413,{'connection':'close'})#太大
                响应.end()#结束
                请求.destroy()#关掉请求
                return#不再处理
        数据=读取正文字节(请求)#读完
        已读=True#已读
        if len(数据)>最大请求正文字节:#实际超过
            响应.writeHead(413,{'connection':'close'})#太大
            响应.end()#结束
            请求.destroy()#关掉
            return#不再处理
        连接请求对象=连接请求(绝对,方法,头,数据 if len(数据)>0 else None,中止.signal)#请求
    else:#流式。当前服务器没有背压流，这里一次读完且不套总上限
        数据=读取正文字节(请求)#读完
        已读=True#已读
        连接请求对象=连接请求(绝对,方法,头,数据 if len(数据)>0 else None,中止.signal)#请求
    取响应=接口处理['fetch'] if isinstance(接口处理,dict) else 接口处理.fetch#处理
    结果=同步等待(取响应(连接请求对象,对等体))#同步等到响应
    请求未读=正文模式=='streaming' and not 已读 and not getattr(请求,'readableEnded',False)#处理函数没读完
    结果头=结果.headers#响应头
    if hasattr(结果头,'entries'):#Headers
        头对=dict(结果头.entries())#成对
    elif isinstance(结果头,dict):#字典
        头对=dict(结果头)#拷贝
    else:#没有
        头对={}#空
    if 请求未读:#还没读完请求
        头对['connection']='close'#关掉连接
    响应.writeHead(结果.status,头对)#状态和头
    if 结果.body is None:#没有正文
        响应.end()#结束
        if 请求未读:#请求还开着
            请求.destroy()#关掉
        return#完成
    正文流=结果.body#正文
    if isinstance(正文流,(bytes,bytearray)):#一整块
        正文流=[bytes(正文流)]#当成一块
    for 块 in 正文流:#逐块
        if 中止.signal.aborted:#已经断开
            continue#只排空，不再写
        写下=响应.write(块)#写一块
        if 写下 is False and not getattr(响应,'destroyed',False):#套接字缓冲满了
            等到=threading.Event()#排空门闩

            def 排空完成():
                'drain 或 close 都放开'
                if hasattr(响应,'off'):#能摘
                    响应.off('drain',排空完成)#摘掉
                    响应.off('close',排空完成)#摘掉
                等到.set()#放开

            登记=响应.once if hasattr(响应,'once') else 响应.on#没有 once 就用 on
            登记('drain',排空完成)#缓冲空了
            登记('close',排空完成)#或者断开
            等到.wait()#等到其中一个
    响应.end()#写完
    if 请求未读:#请求还开着
        请求.destroy()#关掉
