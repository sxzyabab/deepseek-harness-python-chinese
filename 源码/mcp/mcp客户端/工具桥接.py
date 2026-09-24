"""工具桥接：发现 MCP 工具，以确定性的服务器限定公开名注册到框架工具运行时，并在服务器工具列表变化时再同步。

配置键、工具名与诊断英文字面量按线协议原样保留。
"""
import base64,hashlib,json,re,weakref
from ...内核.工具 import 断言受支持json模式
from ...附件.附件 import 是否图像准入错误
from ...模型后端.llm import 已中止
from .传输 import MCP错误

__all__=['公开工具名','同步工具','MCP结果','创建mcp工具定义']

公开名最大长度=64
非法名字符=re.compile(r'[^A-Za-z0-9_-]+',re.ASCII)
哈希长度=12
图像媒体类型=('image/png','image/jpeg','image/webp','image/gif')
规范base64=re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\Z')

def 编码(值):
    """按线协议锁死的 JSON 序列化。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)

def 公开工具名(服务器名,原始名):
    """由服务器名与原始工具名生成确定性公开名；干净时为 mcp__<server>__<raw>。"""
    拼接='mcp__'+服务器名+'__'+原始名
    归一=非法名字符.sub('_',拼接,count=0)
    if 归一==拼接 and len(归一)<=公开名最大长度:
        return 归一
    摘要=hashlib.sha256((服务器名+'\0'+原始名).encode('utf-8')).hexdigest()[:哈希长度]
    前缀预算=公开名最大长度-哈希长度-1
    return 归一[:前缀预算]+'_'+摘要

def 无缓存列工具(客户端,游标=None):
    """列出工具且不改动 SDK 每页输出校验器缓存。客户端为世代 dict。"""
    if 游标 is None:
        return 客户端['request']({'method':'tools/list'})
    return 客户端['request']({'method':'tools/list','params':{'cursor':游标}})

def 无缓存调工具(客户端,原始名,参数,执行,选项):
    """调用工具且不让 SDK 预先校验桥接可能不支持的输出模式。"""
    return 客户端['request'](
        {'method':'tools/call','params':{'name':原始名,'arguments':参数}},
        {'signal':执行['signal'] if 'signal' in 执行 else None,'timeout':选项['toolCallTimeoutMs']},
    )

def 服务器声明工具(客户端):
    """远程：capabilities.tools 缺席则不同步工具表。"""
    会话=客户端['session'] if isinstance(客户端,dict) and 'session' in 客户端 else None
    if 会话 is None:
        return True
    取能力=getattr(会话,'get_server_capabilities',None)
    if 取能力 is None:
        return True
    能力=取能力()
    if 能力 is None:
        return False
    工具能力=能力['tools'] if isinstance(能力,dict) and 'tools' in 能力 else getattr(能力,'tools',None)
    return 工具能力 is not None

def 同步工具(客户端,上下文,选项,上一代):
    """两阶段交换：先获取并构建下一代定义，成功后再拆除上一代并注册本代。"""
    定义表={}
    if not 服务器声明工具(客户端):
        for 注销 in 上一代.values():
            注销()
        return {}
    已见游标=set()
    游标=None
    while True:
        响应=无缓存列工具(客户端,游标)
        工具列表=响应['tools'] if 'tools' in 响应 else []
        for 工具 in 工具列表:
            公开名=公开工具名(选项['serverName'],工具['name'])
            if 公开名 in 定义表:
                raise MCP错误('mcp-client('+选项['serverName']+'): server listed tool "'+工具['name']+'" more than once — invalid tool list')
            执行块=工具['execution'] if 'execution' in 工具 else None
            执行支持=执行块['taskSupport'] if 执行块 is not None and 'taskSupport' in 执行块 else None
            描述=工具['description'] if 'description' in 工具 and 工具['description'] is not None else ''
            原始名=工具['name']
            def 调(参数,执行上下文,原始=原始名):
                """用原始名发出 tools/call。"""
                return 无缓存调工具(客户端,原始,参数,执行上下文,选项)
            定义表[公开名]=创建mcp工具定义(上下文,{
                'name':公开名,
                'rawName':原始名,
                'description':描述,
                'inputSchema':工具['inputSchema'] if 'inputSchema' in 工具 else None,
                'outputSchema':工具['outputSchema'] if 'outputSchema' in 工具 else None,
                'taskRequired':执行支持=='required',
                'call':调,
            })
        游标=响应['nextCursor'] if 'nextCursor' in 响应 else None
        if 游标 is not None:
            if 游标 in 已见游标:
                raise MCP错误('mcp-client('+选项['serverName']+'): server repeated a tools/list continuation cursor — invalid tool list')
            已见游标.add(游标)
        if 游标 is None:
            break
    for 注销 in 上一代.values():
        注销()
    本代={}
    try:
        for 公开名,定义 in 定义表.items():
            本代[公开名]=上下文.tools.登记(定义)
    except Exception as 错误:
        for 注销 in 本代.values():
            注销()
        上下文.日志.错误('mcp-client('+选项['serverName']+'): tool registration failed, no tools registered: '+str(错误))
        if 选项['registrationFailure']=='throw':
            raise 错误
        return {}
    return 本代

def 受支持输出模式(候选):
    """保留受支持的已声明模式；不受支持的 MCP 词表退回无模式。"""
    if 候选 is None:
        return None
    try:
        断言受支持json模式(候选)
        return 候选
    except Exception:
        return None

def 构建输出(原始名,结构化模式):
    """构建规范结果模式以及现有 Native 文本投影。"""
    def 渲染(_参数,值):
        """抽出文本成单个文本块。"""
        内容=值['content'] if 'content' in 值 else []
        return [{'type':'text','text':抽出文本(内容,原始名)}]
    必填=['content']
    if 结构化模式 is not None:
        必填.append('structuredContent')
    return {
        'schema':{
            'type':'object',
            'properties':{
                'content':{'type':'array','items':{}},
                'structuredContent':结构化模式 if 结构化模式 is not None else {},
            },
            'required':必填,
            'additionalProperties':False,
        },
        'render':渲染,
    }

def 创建mcp工具定义(上下文,选项):
    """把上游 MCP 工具接到规范值与耐久图像内容。登记、寿命、期限与传输由调用方持有。选项为 dict。"""
    投影表=weakref.WeakKeyDictionary()
    最终器=创建内容最终器(投影表)
    return {
        'name':选项['name'],
        'description':选项['description'],
        'parameters':选项['inputSchema'],
        'output':构建输出(选项['rawName'],受支持输出模式(选项['outputSchema'] if 'outputSchema' in 选项 else None)),
        'execute':创建执行器(上下文,选项,投影表),
        'projectContent':最终器,
        'finalizeContent':最终器,
    }

def 创建内容最终器(投影表):
    """仅在执行值与回退内容仍是本代投影时替换为图像富化内容。"""
    def 最终内容(执行,结果):
        """规范结果上的内容投影。执行与结果为 dict。"""
        try:
            投影=投影表.pop(执行,None)
        except TypeError:
            return None
        if 投影 is None:
            return None
        if 'isError' in 结果 and 结果['isError'] is True:
            return None
        if 'value' not in 结果 or 结果['value']!=投影['value']:
            return None
        if 'content' not in 结果 or 结果['content']!=投影['fallback']:
            return None
        return 投影['content']
    return 最终内容

def 创建执行器(上下文,选项,投影表):
    """调用方持有的原始结果回调，再准备规范内容。"""
    原始名=选项['rawName']
    要求任务式=选项['taskRequired'] if 'taskRequired' in 选项 else False
    def 执行(参数,执行上下文):
        """调用 MCP 工具并把结果规范成 content/structuredContent。"""
        if 要求任务式:
            raise MCP错误('Tool "'+原始名+'" requires task-based execution, which this bridge does not support')
        参数对象=参数 if isinstance(参数,dict) else {}
        结果=选项['call'](参数对象,执行上下文)
        内容=结果['content'] if 'content' in 结果 else None
        if not isinstance(内容,list):
            if 'toolResult' in 结果:
                文本=编码(结果['toolResult'])
            else:
                文本='(no output)'
            if 'isError' in 结果 and 结果['isError'] is True:
                raise MCP错误(文本)
            规范={'content':[{'type':'text','text':文本}]}
            if 'structuredContent' in 结果 and 结果['structuredContent'] is not None:
                规范['structuredContent']=结果['structuredContent']
            return 规范
        文本=抽出文本(内容,原始名)
        if 'isError' in 结果 and 结果['isError'] is True:
            raise MCP错误(文本)
        规范={'content':内容}
        if 'structuredContent' in 结果 and 结果['structuredContent'] is not None:
            规范['structuredContent']=结果['structuredContent']
        if 含图像(内容):
            回退=[{'type':'text','text':抽出文本(内容,原始名)}]
            投影表[执行上下文]={'value':规范,'fallback':回退,'content':准备图像投影(上下文,执行上下文,内容,原始名)}
        return 规范
    return 执行

def 含图像(内容):
    """未信任的 MCP 内容数组是否含声明的图像块。"""
    for 值 in 内容:
        if isinstance(值,dict) and 'type' in 值 and 值['type']=='image':
            return True
    return False

def 解码图像(块):
    """解码一帧投影图像，不接受 base64 别名。块为 dict。"""
    媒体=块['mimeType'] if 'mimeType' in 块 else None
    if 媒体 not in 图像媒体类型:
        raise MCP错误('the declared media type is not PNG, JPEG, WebP, or GIF')
    数据=块['data'] if 'data' in 块 else None
    if not isinstance(数据,str) or 规范base64.match(数据) is None:
        raise MCP错误('the image data is not canonical base64')
    字节=base64.b64decode(数据,validate=True)
    if base64.b64encode(字节).decode('ascii')!=数据:
        raise MCP错误('the image data is not canonical base64')
    return {'data':字节,'mediaType':媒体}

def 解析图像准入(上下文,执行):
    """解析当前模型路由与耐久存储；需正向图像能力证明。"""
    附件=上下文.获取服务('attachments')
    if 附件 is None:
        raise MCP错误('no attachment store is mounted')
    智能体=执行['agent'] if 'agent' in 执行 else None
    头=智能体.session.请求头() if 智能体 is not None else None
    路由=头['config'] if 头 is not None and 'config' in 头 else None
    提供方=None
    模型=None
    if 路由 is not None:
        提供方=路由['provider'] if 'provider' in 路由 else None
        模型=路由['model'] if 'model' in 路由 else None
    if 提供方 is None and 智能体 is not None:
        提供方=智能体.options['provider'] if 'provider' in 智能体.options else None
    if 模型 is None and 智能体 is not None:
        模型=智能体.options['model'] if 'model' in 智能体.options else None
    语言模型=上下文.获取服务('llm')
    if 提供方 is None or 模型 is None or 语言模型 is None:
        raise MCP错误('the current model route could not be resolved')
    try:
        信息=语言模型.解析模型信息(提供方,模型,执行['signal'] if 'signal' in 执行 else None)
    except Exception:
        raise MCP错误('the current model route could not be verified')
    模态=信息['inputModalities'] if 'inputModalities' in 信息 else None
    if 模态 is None or 'image' not in 模态:
        raise MCP错误('model "'+str(模型)+'" does not declare image input')
    if 已中止(执行['signal'] if 'signal' in 执行 else None):
        raise MCP错误('the tool call was canceled before image storage')
    return 附件

def 图像诊断(块,原因):
    """未准入图像块的稳定诊断文本。块为 dict。"""
    媒体=块['mimeType'] if 'mimeType' in 块 and 块['mimeType'] is not None else 'unknown media type'
    return '[image unavailable: '+str(媒体)+'; '+原因+'; raw image data remains available to programmatic callers]'

def 准备图像投影(上下文,执行,内容,工具名):
    """解码、预检并耐久保存一次 MCP 结果的有序图像批次。任一拒绝则全部图像投影为文本。"""
    已解码=[]
    校验错误={}
    图像下标=[]
    for 下标,值 in enumerate(内容):
        if not isinstance(值,dict) or 'type' not in 值 or 值['type']!='image':
            continue
        图像下标.append(下标)
        try:
            已解码.append(解码图像(值))
        except MCP错误 as 错误:
            校验错误[下标]=str(错误)
    if len(校验错误)>0:
        def 无效图(块,下标):
            """校验失败时每张图都投影为文本。"""
            原因=校验错误[下标] if 下标 in 校验错误 else 'another image in the same result was invalid'
            return {'type':'text','text':图像诊断(块,原因)}
        return 投影内容(内容,工具名,无效图)
    try:
        附件=解析图像准入(上下文,执行)
    except MCP错误 as 错误:
        原因=str(错误)
        def 无准入(块,_下标):
            """路由或存储未就绪时全部图像投影为文本。"""
            return {'type':'text','text':图像诊断(块,原因)}
        return 投影内容(内容,工具名,无准入)
    try:
        引用表=附件.保存图像批次(已解码)
        按下标={}
        for 偏移,下标 in enumerate(图像下标):
            按下标[下标]=引用表[偏移]
        def 已保存(_块,下标):
            """按原位插入耐久图像引用。"""
            return {'type':'image','attachment':按下标[下标]}
        return 投影内容(内容,工具名,已保存)
    except Exception as 错误:
        if 是否图像准入错误(错误):
            原因='image admission rejected the result: '+str(错误)
        else:
            原因='durable image storage rejected the result'
        def 存储拒绝(块,_下标):
            """耐久存储拒绝时全部图像投影为文本。"""
            return {'type':'text','text':图像诊断(块,原因)}
        return 投影内容(内容,工具名,存储拒绝)

def 抽出文本(mcp内容,工具名):
    """从 MCP 内容数组抽出文本成单个字符串。"""
    内容=投影内容(mcp内容,工具名)
    return '\n'.join(块['text'] for 块 in 内容)

def 默认图像投影(块,_下标):
    """未准入到耐久模型上下文的图像占位。"""
    return {'type':'text','text':图像诊断(块,'this result was not admitted to durable model context')}

def 投影内容(mcp内容,工具名,图像=默认图像投影):
    """把有序 MCP 块投影到核心内容词表。文本游程按换行合并；图像在原位切开。"""
    已投影=[]
    文本=[]
    def 冲文本():
        """把未冲刷的文本游程收成一块。"""
        if len(文本)==0:
            return
        已投影.append({'type':'text','text':'\n'.join(文本)})
        文本.clear()
    for 下标,值 in enumerate(mcp内容):
        if not isinstance(值,dict):
            文本.append('[unsupported MCP content block: expected an object]')
            continue
        类型=值['type'] if 'type' in 值 else None
        if 类型=='text':
            if 'text' in 值 and 值['text'] is not None:
                文本.append(值['text'])
        elif 类型=='image':
            冲文本()
            已投影.append(图像(值,下标))
        elif 类型=='resource_link':
            if 'name' not in 值 or 值['name'] is None or 'uri' not in 值 or 值['uri'] is None:
                文本.append('[resource link unavailable: the MCP block is missing its name or URI]')
            else:
                文本.append('Resource link: '+str(值['name'])+' ('+str(值['uri'])+')')
        elif 类型=='audio':
            媒体=值['mimeType'] if 'mimeType' in 值 and 值['mimeType'] is not None else 'unknown media type'
            文本.append('[audio result unsupported: '+str(媒体)+'; raw audio data remains available to programmatic callers]')
        elif 类型=='resource':
            文本.append('[embedded resource unsupported; raw resource data remains available to programmatic callers]')
        else:
            文本.append('[unsupported MCP content type: '+str(类型)+']')
    冲文本()
    if len(已投影)>0:
        return 已投影
    return [{'type':'text','text':'('+工具名+' returned no model-visible content)'}]

MCP结果=dict
