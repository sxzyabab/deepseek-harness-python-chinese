"""工具桥接：发现 MCP 工具，以确定性的服务器限定公开名注册到框架工具运行时，并在服务器工具列表变化时再同步。

对齐上游 `mcp-client/src/tools.ts`。公开面仅中文名。配置键、工具名与诊断英文字面量保持上游。
"""
import hashlib,json,re#身份哈希、旧结果序列化与非法名字符
from ...内核.工具 import 断言受支持json模式#受支持 JSON 模式断言
from .传输 import MCP错误#本包异常

__all__=['公开工具名','同步工具','MCP结果']#仅中文公开名

公开名最大长度=64#DeepSeek 函数名最大长度
非法名字符=re.compile(r'[^A-Za-z0-9_-]+')#非法公开名字符
哈希长度=12#有损归一化时追加的 SHA-256 十六进制字符数

def 编码(值):
    """按线协议锁死的 JSON 序列化。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON

def 公开工具名(服务器名,原始名):
    """`(serverName, rawName)` 的确定性纯函数：干净情形是原文 `mcp__<serverName>__<rawName>`。"""
    拼接='mcp__'+服务器名+'__'+原始名#拼接命名空间与原始名
    归一=非法名字符.sub('_',拼接,count=0)#非法字符全换成下划线
    if 归一==拼接 and len(归一.encode('utf-8'))<=公开名最大长度:#无需有损归一化则原样返回
        return 归一#干净名
    摘要=hashlib.sha256((服务器名+'\0'+原始名).encode('utf-8')).hexdigest()[:哈希长度]#身份哈希后缀
    前缀预算=公开名最大长度-哈希长度-1#截断预算
    前缀=归一.encode('utf-8')[:前缀预算].decode('utf-8','ignore')#按字节切在字符边界
    while len((前缀+'_'+摘要).encode('utf-8'))>公开名最大长度 and len(前缀)>0:#仍超长则再削
        前缀=前缀[:-1]#削一个码点
    return 前缀+'_'+摘要#截断后追加哈希

def 无缓存列工具(客户端,游标=None):
    """列出工具且不改动 SDK 每页输出校验器缓存。客户端为世代 dict。"""
    if 游标 is None:#无游标
        return 客户端['request']({'method':'tools/list'})#tools/list
    return 客户端['request']({'method':'tools/list','params':{'cursor':游标}})#带游标

def 无缓存调工具(客户端,原始名,参数,执行,选项):
    """调用工具且不让 SDK 预先校验桥接可能不支持的输出模式。"""
    return 客户端['request'](#发出 tools/call
        {'method':'tools/call','params':{'name':原始名,'arguments':参数}},#只用原始名
        {'signal':执行['signal'] if 'signal' in 执行 else None,'timeout':选项['toolCallTimeoutMs']},#中止与超时
    )#request 结束

def 同步工具(客户端,上下文,选项,上一代):
    """两阶段交换：先获取并构建下一代定义，成功后再拆除上一代并注册本代。"""
    定义表={}#下一代工具定义
    游标=None#分页游标
    while True:#循环拉取每一页
        响应=无缓存列工具(客户端,游标)#无缓存列出本页
        工具列表=响应['tools'] if 'tools' in 响应 else []#本页工具
        for 工具 in 工具列表:#遍历本页工具
            公开名=公开工具名(选项['serverName'],工具['name'])#推导公开名
            if 公开名 in 定义表:#同一公开名出现两次
                raise MCP错误('mcp-client('+选项['serverName']+'): server listed tool "'+工具['name']+'" more than once — invalid tool list')#服务器列表非法
            执行块=工具['execution'] if 'execution' in 工具 else None#执行块
            执行支持=执行块['taskSupport'] if 执行块 is not None and 'taskSupport' in 执行块 else None#任务式执行标记
            描述=工具['description'] if 'description' in 工具 and 工具['description'] is not None else ''#缺描述则空串
            输出模式=工具['outputSchema'] if 'outputSchema' in 工具 else None#输出模式
            定义表[公开名]={#登记本工具定义
                'name':公开名,#面向模型的公开名
                'description':描述,#描述
                'parameters':工具['inputSchema'] if 'inputSchema' in 工具 else None,#输入模式
                'output':构建输出(工具['name'],受支持输出模式(输出模式)),#输出模式与渲染
                'execute':创建执行器(客户端,工具['name'],执行支持=='required',选项),#执行器
            }#定义结束
        游标=响应['nextCursor'] if 'nextCursor' in 响应 else None#下一页游标
        if 游标 is None:#无游标则结束
            break#退出分页
    for 注销 in 上一代.values():#拆除上一代
        注销()#注销
    本代={}#本代 disposer
    try:#尝试注册本代
        for 公开名,定义 in 定义表.items():#逐个注册
            本代[公开名]=上下文.tools.登记(定义)#登记并可稍后注销
    except MCP错误 as 错误:#注册冲突或其他失败
        for 注销 in 本代.values():#回滚已注册项
            注销()#注销
        上下文.日志.错误('mcp-client('+选项['serverName']+'): tool registration failed, no tools registered: '+str(错误))#记录失败
        if 选项['registrationFailure']=='throw':#严格模式向上抛
            raise 错误#抛出
        return {}#包容模式返回空映射
    return 本代#返回本代 disposer

def 受支持输出模式(候选):
    """保留受支持的已声明模式；不受支持的 MCP 词表退回无模式。"""
    if 候选 is None:#未声明则无模式
        return None#无模式
    try:#尝试断言受支持
        断言受支持json模式(候选)#校验 JSON 模式词表
        return 候选#受支持则原样返回
    except TypeError:#不受支持的模式
        return None#退回无结构化模式

def 构建输出(原始名,结构化模式):
    """构建规范结果模式以及现有 Native 文本投影。"""
    def 渲染(_参数,值):
        """抽出文本成单个文本块。"""
        内容=值['content'] if 'content' in 值 else []#内容数组
        return [{'type':'text','text':抽出文本(内容,原始名)}]#抽出文本
    必填=['content']#内容始终必需
    if 结构化模式 is not None:#有结构化模式
        必填.append('structuredContent')#两者都必需
    return {#输出约定
        'schema':{#结果 JSON 模式
            'type':'object',#对象
            'properties':{#属性
                'content':{'type':'array','items':{}},#内容数组
                'structuredContent':结构化模式 if 结构化模式 is not None else {},#结构化内容或空对象
            },#properties 结束
            'required':必填,#必填字段
            'additionalProperties':False,#禁止额外属性
        },#schema 结束
        'render':渲染,#文本投影
    }#输出约定结束

def 创建执行器(客户端,原始名,要求任务式,选项):
    """闭包原始 MCP 工具名，发出无缓存的 tools/call，再把结果映射为框架内容。"""
    def 执行(参数,执行上下文):
        """调用 MCP 工具并把结果规范成 content/structuredContent。"""
        if 要求任务式:#本桥接不支持任务式执行
            raise MCP错误('Tool "'+原始名+'" requires task-based execution, which this bridge does not support')#拒绝任务式工具
        参数对象=参数 if isinstance(参数,dict) else {}#非对象则空对象
        结果=无缓存调工具(客户端,原始名,参数对象,执行上下文,选项)#无缓存调用
        内容=结果['content'] if 'content' in 结果 else None#内容数组
        if not isinstance(内容,list):#没有内容数组
            if 'toolResult' in 结果:#有旧字段则序列化
                文本=编码(结果['toolResult'])#旧结果转字符串
            else:#否则占位
                文本='(no output)'#占位
            if 'isError' in 结果 and 结果['isError'] is True:#错误则抛给运行时
                raise MCP错误(文本)#抛出
            规范={'content':[{'type':'text','text':文本}]}#无内容数组时的规范结果
            if 'structuredContent' in 结果 and 结果['structuredContent'] is not None:#有结构化内容则带上
                规范['structuredContent']=结果['structuredContent']#结构化内容
            return 规范#返回
        文本=抽出文本(内容,原始名)#抽出文本供错误信息
        if 'isError' in 结果 and 结果['isError'] is True:#服务器标记错误
            raise MCP错误(文本)#抛出抽出的文本
        规范={'content':内容}#成功结果
        if 'structuredContent' in 结果 and 结果['structuredContent'] is not None:#有结构化内容则带上
            规范['structuredContent']=结果['structuredContent']#结构化内容
        return 规范#返回
    return 执行#execute 闭包

def 抽出文本(mcp内容,工具名):
    """从 MCP 内容数组抽出文本成单个字符串。"""
    片段=[]#文本片段
    for 值 in mcp内容:#逐块处理
        if not isinstance(值,dict):#非对象块
            片段.append('[unsupported content type: unknown]')#未知类型占位
            continue#跳过后续分支
        类型=值['type'] if 'type' in 值 else None#块类型
        if 类型=='text':#文本块
            if 'text' in 值 and 值['text'] is not None:#有文本才追加
                片段.append(值['text'])#追加
        elif 类型=='image':#图像块
            类型名=值['mimeType'] if 'mimeType' in 值 and 值['mimeType'] is not None else 'unknown'#类型
            片段.append('[image: '+类型名+', content discarded]')#丢弃内容并占位
        elif 类型=='audio':#音频块
            类型名=值['mimeType'] if 'mimeType' in 值 and 值['mimeType'] is not None else 'unknown'#类型
            片段.append('[audio: '+类型名+', content discarded]')#丢弃内容并占位
        elif 类型 in ('resource','resource_link'):#资源块
            片段.append('[resource: content discarded]')#丢弃内容并占位
        else:#其余类型
            片段.append('[unsupported content type: '+str(类型)+']')#不受支持的类型占位
    if len(片段)==0:#无片段
        return '('+工具名+' returned no text content)'#报告无文本
    return '\n'.join(片段)#拼接

MCP结果=dict#规范 MCP 结果形状对照
