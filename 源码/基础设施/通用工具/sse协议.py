'Server-Sent Events（text/event-stream）的编码与增量解码'
from codecs import getincrementaldecoder as 取增量解码器#按块解码UTF-8
from re import compile as 编译正则#行终止符：CRLF、CR、LF 三种

__all__=['sse消息','编码sse事件','编码sse注释','sse解码器']#仅中文公开名

行终止模式=编译正则(r'\r\n|\r|\n')#SSE 规范允许的三种行终止

class sse消息:
    '一条完整的 SSE 事件'
    __slots__=('事件名','标识','数据')
    def __init__(自身,事件名:str,标识:str,数据:str):
        '事件名缺省为 message；标识是最近一次见到的 id 字段（没有则为空串）；多行数据以换行连接'
        自身.事件名=事件名
        自身.标识=标识
        自身.数据=数据

    def __repr__(自身)->str:
        '便于调试的文本形式'
        return f'sse消息(事件名={自身.事件名!r},标识={自身.标识!r},数据={自身.数据!r})'

def 编码sse事件(数据:str,事件名:str=None,标识:str=None)->str:
    '编码一条事件；数据含换行时拆成多行 data 字段。返回以空行结尾的文本'
    行列表=[]
    if 事件名 is not None:
        行列表.append(f'event: {事件名}')
    if 标识 is not None:
        行列表.append(f'id: {标识}')
    for 数据行 in 行终止模式.split(数据):
        行列表.append(f'data: {数据行}')
    return '\n'.join(行列表)+'\n\n'

def 编码sse注释(文本:str='')->str:
    '编码一条注释帧，常用于建立连接后的握手或保活'
    return f': {文本}\n\n'

class sse解码器:
    '增量解码 SSE 流：喂入任意分块的字节或文本，取回此刻已完整的事件。流结束时未以空行结尾的事件按规范丢弃'
    def __init__(自身):
        '创建空解码器'
        自身._解码器=取增量解码器('utf-8')()
        自身._残余=''
        自身._上块以回车结尾=False
        自身._事件名=''
        自身._数据行列表=[]
        自身._最近标识=''

    def 推入(自身,数据:str|bytes)->list:
        '追加一块数据，按顺序返回已完整的事件（sse消息）列表'
        if isinstance(数据,(bytes,bytearray)):
            数据=自身._解码器.decode(bytes(数据))
        if 自身._上块以回车结尾 and 数据.startswith('\n'):#上一块结尾的回车与这一块开头的换行是同一个 CRLF
            数据=数据[1:]
        自身._上块以回车结尾=数据.endswith('\r')
        分段列表=行终止模式.split(自身._残余+数据)
        自身._残余=分段列表.pop()
        消息列表=[]
        for 行 in 分段列表:
            if 行=='':#空行：派发事件
                if len(自身._数据行列表)>0:
                    消息列表.append(sse消息(自身._事件名 or 'message',自身._最近标识,'\n'.join(自身._数据行列表)))
                自身._事件名=''
                自身._数据行列表=[]
                continue
            if 行.startswith(':'):#注释
                continue
            字段,冒号,取值=行.partition(':')
            if 冒号!='' and 取值.startswith(' '):
                取值=取值[1:]
            if 字段=='event':
                自身._事件名=取值
            elif 字段=='data':
                自身._数据行列表.append(取值)
            elif 字段=='id' and '\0' not in 取值:
                自身._最近标识=取值
        return 消息列表
