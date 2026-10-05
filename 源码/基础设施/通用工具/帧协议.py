'字节流上的三种成帧方式：长度前缀、Content-Length 头（LSP/MCP 风格）、换行分隔（NDJSON）'
from codecs import getincrementaldecoder as 取增量解码器#按块解码UTF-8，字符被切开也不出错
from .序列化编码 import 紧凑json编码#NDJSON 行的 JSON 编码

__all__=[
    '帧协议错误','编码长度前缀帧','长度前缀帧解码器',
    '编码内容长度帧','内容长度帧解码器','编码ndjson行','换行帧解码器',
]#仅中文公开名

头体分隔=b'\r\n\r\n'#Content-Length 帧里头部与正文之间的分隔

class 帧协议错误(ValueError):
    '收到的字节不符合帧格式，或帧超过上限；流已不可再解析'

def 编码长度前缀帧(载荷:bytes,长度字节数:int=4)->bytes:
    '帧 = 大端无符号长度（默认4字节） + 载荷'
    return len(载荷).to_bytes(长度字节数,'big')+载荷

class 长度前缀帧解码器:
    '增量解码长度前缀帧：喂入任意分块的字节，取回此刻已完整的载荷'
    def __init__(自身,最大帧字节:int,长度字节数:int=4):
        '最大帧字节限制单个载荷，超过即判为协议错误'
        自身._最大帧字节=最大帧字节
        自身._长度字节数=长度字节数
        自身._缓冲=bytearray()

    @property
    def 未消费字节数(自身)->int:
        '缓冲里尚未凑成完整帧的字节数；流结束时不为0说明帧被截断'
        return len(自身._缓冲)

    def 推入(自身,数据:bytes)->list:
        '追加一块数据，按顺序返回已完整的载荷列表；长度超限抛帧协议错误'
        自身._缓冲.extend(数据)
        载荷列表=[]
        头长=自身._长度字节数
        while len(自身._缓冲)>=头长:
            载荷长度=int.from_bytes(自身._缓冲[:头长],'big')
            if 载荷长度>自身._最大帧字节:
                raise 帧协议错误(f'帧长度 {载荷长度} 超过上限 {自身._最大帧字节}')
            if len(自身._缓冲)<头长+载荷长度:
                break
            载荷列表.append(bytes(自身._缓冲[头长:头长+载荷长度]))
            del 自身._缓冲[:头长+载荷长度]
        return 载荷列表

def 编码内容长度帧(正文:bytes)->bytes:
    '帧 = "Content-Length: N" + 空行 + 正文（N 为正文字节数）'
    return b'Content-Length: '+str(len(正文)).encode('ascii')+头体分隔+正文

class 内容长度帧解码器:
    '增量解码 Content-Length 帧：只认 Content-Length 头（不区分大小写），忽略其它头'
    def __init__(自身,最大正文字节:int,最大头字节:int=65536):
        '正文或头部超过上限即判为协议错误，防止无限增长'
        自身._最大正文字节=最大正文字节
        自身._最大头字节=最大头字节
        自身._缓冲=bytearray()

    def 推入(自身,数据:bytes)->list:
        '追加一块数据，按顺序返回已完整的正文（bytes）列表'
        自身._缓冲.extend(数据)
        正文列表=[]
        while True:
            分隔位置=自身._缓冲.find(头体分隔)
            if 分隔位置<0:
                if len(自身._缓冲)>自身._最大头字节:
                    raise 帧协议错误(f'头部超过 {自身._最大头字节} 字节仍未结束')
                break
            if 分隔位置>自身._最大头字节:
                raise 帧协议错误(f'头部超过 {自身._最大头字节} 字节')
            头文本=bytes(自身._缓冲[:分隔位置]).decode('ascii','replace')
            正文长度=None
            for 行 in 头文本.split('\r\n'):
                名称,冒号,取值=行.partition(':')
                if 冒号=='' or 名称.strip().lower()!='content-length':
                    continue
                取值=取值.strip()
                if not (取值.isascii() and 取值.isdigit()):
                    raise 帧协议错误(f'无效的 Content-Length 头：{行!r}')
                正文长度=int(取值)
                break
            if 正文长度 is None:
                raise 帧协议错误('头部缺少 Content-Length')
            if 正文长度>自身._最大正文字节:
                raise 帧协议错误(f'正文长度 {正文长度} 超过上限 {自身._最大正文字节}')
            正文起点=分隔位置+len(头体分隔)
            if len(自身._缓冲)<正文起点+正文长度:
                break
            正文列表.append(bytes(自身._缓冲[正文起点:正文起点+正文长度]))
            del 自身._缓冲[:正文起点+正文长度]
        return 正文列表

def 编码ndjson行(值)->str:
    '把值编码为一行紧凑 JSON 加换行'
    return 紧凑json编码(值)+'\n'

class 换行帧解码器:
    '增量解码换行分隔的文本帧（NDJSON 等）：空行与行首尾空白（含 \\r）被丢弃，多字节字符被分块切开也能正确还原'
    def __init__(自身):
        '创建空解码器'
        自身._解码器=取增量解码器('utf-8')()
        自身._残余=''

    def 推入(自身,数据:str|bytes)->list:
        '追加一块文本或字节，按顺序返回已完整的非空行'
        if isinstance(数据,(bytes,bytearray)):
            数据=自身._解码器.decode(bytes(数据))
        分段列表=(自身._残余+数据).split('\n')
        自身._残余=分段列表.pop()
        整行列表=[]
        for 分段 in 分段列表:
            行=分段.strip()
            if 行!='':
                整行列表.append(行)
        return 整行列表

    def 结束(自身)->list:
        '流结束时调用：返回末尾没有换行的那一行（若非空），并清空解码器'
        残余=(自身._残余+自身._解码器.decode(b'',True)).strip()
        自身._残余=''
        return [残余] if 残余!='' else []
