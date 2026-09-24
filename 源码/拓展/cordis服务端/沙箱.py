import base64,re,sys,threading
from .门面规则 import 宿主运行器错误,沙箱定义工具,沙箱登记工具

__all__=[
    '创建沙箱','求值宿主代码','预检代码','解析失败消息','语法错误上下文',
]

#常量
标注词=re.compile(r'\bas\b',re.ASCII)
定时器重定向=(
    'Node 定时器不可用。请改用 cordis timer 服务：在插件上声明 inject: [\'timer\']，'
    '查 Host Service.listService 的精确重载后调用 ctx.超时 / ctx.间隔。'
    '这些调用是纤程副作用，停止时会自动拆除。'
)
节点接口重定向={
    'require':
        'Node 模块不可用。请改用 ctx 上的 cordis 服务——例如 inject: [\'fs\'] 处理文件，'
        '[\'web\'] 处理 HTTP，[\'bash\'] 处理进程；先用 cordis_inspect_query 查 Service.listService。',
    'setTimeout':定时器重定向,
    'setInterval':定时器重定向,
    'setImmediate':定时器重定向,
    'clearTimeout':定时器重定向,
    'clearInterval':定时器重定向,
    'fetch':
        '网络走 cordis web 服务：声明 inject: [\'web\'] 并调用 ctx.web'
        '（用 cordis_inspect_query 查 Host Service.listService 的方法）。',
}
语言内建={
    'None':None,'True':True,'False':False,
    'object':object,'type':type,
    'bool':bool,'int':int,'float':float,'str':str,'bytes':bytes,
    'list':list,'dict':dict,'tuple':tuple,'set':set,'frozenset':frozenset,
    'Exception':Exception,'BaseException':BaseException,
    'TypeError':TypeError,'ValueError':ValueError,'KeyError':KeyError,
    'IndexError':IndexError,'AttributeError':AttributeError,
    'RuntimeError':RuntimeError,'StopIteration':StopIteration,
    'SyntaxError':SyntaxError,
    'len':len,'range':range,'enumerate':enumerate,'zip':zip,
    'iter':iter,'next':next,'isinstance':isinstance,'issubclass':issubclass,
    'callable':callable,'hasattr':hasattr,'getattr':getattr,'setattr':setattr,
    'repr':repr,'abs':abs,'min':min,'max':max,'sum':sum,
    'map':map,'filter':filter,'sorted':sorted,'reversed':reversed,
    'any':any,'all':all,'round':round,'pow':pow,
    '__build_class__':__build_class__,
}

#工具
class 文本编码器:
    """沙箱内的 UTF-8 编码器，对应 TextEncoder。"""
    def encode(自身,文本):
        """编码为字节。"""
        if not isinstance(文本,str):
            文本=str(文本)
        return 文本.encode('utf-8')

class 文本解码器:
    """沙箱内的 UTF-8 解码器，对应 TextDecoder。"""
    def decode(自身,数据):
        """解码为字符串。"""
        if isinstance(数据,memoryview):
            数据=bytes(数据)
        return bytes(数据).decode('utf-8')

def 编码base64(文本):
    """utf-8 文本转 base64。"""
    return base64.b64encode(文本.encode('utf-8')).decode('ascii')

def 解码base64(文本):
    """base64 转 utf-8 文本。"""
    return base64.b64decode(文本).decode('utf-8')

def 标记控制台(标识):
    """带包 id 标签的直通控制台。"""
    前缀=f'[cordis:{标识}]'
    def 写(*参数):
        """写到标准输出。"""
        print(前缀,*参数)
    def 写错(*参数):
        """写到标准错误。"""
        print(前缀,*参数,file=sys.stderr)
    return {'log':写,'info':写,'warn':写,'debug':写,'error':写错}

def 节点接口陷阱():
    """调用即抛出重定向教学。"""
    陷阱={}
    for 名,重定向 in 节点接口重定向.items():
        def 拦截(_名=名,_文=重定向):
            """永不返回。"""
            raise 宿主运行器错误(f'动态包沙箱里没有 {_名} —— {_文}')
        陷阱[名]=拦截
    return 陷阱

def 包装宿主源(代码):
    """把宿主半源码收成可 exec 的函数体，对应 async 包装。"""
    行=['def __宿主半():']
    if 代码=='':
        行.append('    pass')
    else:
        for 源行 in 代码.split('\n'):
            行.append('    '+源行)
    行.append('__结果=__宿主半()')
    return '\n'.join(行)

#
def 语法错误上下文(错误):
    """语法失败时带出问题行与插入符。"""
    if not isinstance(错误,SyntaxError):
        return str(错误)
    段=[]
    if 错误.text:
        段.append(错误.text.rstrip('\n'))
        if 错误.offset:
            段.append(' '*(max(错误.offset,1)-1)+'^')
    段.append(f'SyntaxError: {错误.msg}')
    return '\n'.join(段)

def 解析失败消息(半,上下文):
    """define 预检与运行时求值共用的教学文本。"""
    行=上下文.split('\n')
    问题行=行[0] if len(行)>0 else ''
    if 标注词.search(问题行) is not None:
        return (
            f'动态包 `{半}` 无法解析：\n{上下文}\n'
            '沙箱运行的是普通 Python，不是 TypeScript。去掉类型标注：\n'
            "  ✗ { type: 'text' as const, text: x }\n"
            "  ✓ { type: 'text', text: x }"
        )
    return (
        f'动态包 `{半}` 无法解析：\n{上下文}\n'
        '注意：它作为函数体运行（行号相对 1 行包装偏移）。'
        '检查括号与缩进——用 `});` 结束返回的插件对象会关掉从未打开的调用；'
        '普通 `return { … }` 以 `}` 结束（可选 `;`），不要 `)`。'
    )

def 预检代码(代码,半):
    """只编译不运行，把无法解析的源码挡在登记之外。"""
    包装=包装宿主源(代码)
    try:
        compile(包装,f'cordis-dyn-{半}.py','exec')
    except SyntaxError as 错误:
        raise 宿主运行器错误(解析失败消息(半,语法错误上下文(错误)))

def 创建沙箱(标识,额外=None):
    """一份宿主半求值用的干净全局。"""
    if 额外 is None:
        额外={}
    沙箱={
        **节点接口陷阱(),
        'console':标记控制台(标识),
        'harness':{'defineTool':沙箱定义工具,'registerTool':沙箱登记工具,**额外},
        'btoa':编码base64,
        'atob':解码base64,
        'TextEncoder':文本编码器,
        'TextDecoder':文本解码器,
        '__name__':'沙箱',
        '__builtins__':dict(语言内建),
    }
    return 沙箱

def 求值宿主代码(沙箱,代码,标识,超时毫秒):
    """在沙箱里把宿主半当函数体求值；超时只约束同步部分。"""
    包装=包装宿主源(代码)
    文件名=f'cordis-dyn-{标识}.py'
    try:
        已编译=compile(包装,文件名,'exec')
    except SyntaxError as 错误:
        raise 宿主运行器错误(解析失败消息('code.host',语法错误上下文(错误)))
    盒={'结果':None,'错误':None}
    def 跑():
        """在独立线程里 exec。"""
        try:
            exec(已编译,沙箱)
            盒['结果']=沙箱.get('__结果')
        except BaseException as 错误:
            盒['错误']=错误
    线程=threading.Thread(target=跑)
    线程.start()
    秒=超时毫秒/1000 if 超时毫秒 is not None else None
    线程.join(秒)
    if 线程.is_alive():
        raise 宿主运行器错误(f'宿主半同步求值超过 {超时毫秒} 毫秒')
    错误=盒['错误']
    if 错误 is not None:
        if isinstance(错误,SyntaxError):
            raise 宿主运行器错误(解析失败消息('code.host',语法错误上下文(错误)))
        raise 错误
    return 盒['结果']
