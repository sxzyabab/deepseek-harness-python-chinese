"""工具注册表、模型呈现模式，以及预执行/守卫/环绕/后执行/结果管线。对齐上游 `@deepseek-ai/dsh-tools`。公开面仅中文名；Cordis 槽 `inject`/`Config`/`default` 为协议兼容，不入 `__all__`。"""
import json,math,threading,weakref
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
枚举字段=schemastery.枚举字段#配置字段
自然数字段=schemastery.自然数字段#配置字段
服务=cordis.服务#导入服务基类
from ..作用域 import 匿名条目,具名条目,作用域层集,获取作用域,作用域目标#导入作用域层与载体
from ...模型后端.llm import 装备错误 as 框架错误,断言永不,深冻结#导入框架错误、穷尽检查与深冻结
from ..会话 import 快照json值#导入无损 JSON 快照
from .json模式 import 断言受支持json模式,断言对象json模式,校验json模式值,json模式错误#导入统一 JSON Schema 校验
from .模式 import (
    定义工具,#定义工具
    值模式规格转json模式,#值模式编译
    参数模式规格转json模式,#参数模式编译
    校验参数,#校验参数
    工具参数错误,#参数错误
)
from .ts类型 import json模式转ts,渲染工具sdk#导入 TS SDK
from .python类型 import json模式转py,渲染工具sdkpy#导入 Python SDK
from .测试 import 定义内容工具夹具#导入测试夹具
from .类型 import 代码派发开始,代码派发落定,派发开始字段,派发落定字段#导入派发事件词汇
from .呈现 import (
    调用类别,#调用类别
    调用卡片,#待处理卡片
    结果卡片,#完成卡片
    搜索形态,#搜索形态
    网页种类,#网页种类
    文件位置字段,#文件位置
    文件差异字段,#文件 diff
    读取文件行字段,#读取行
    通用调用字段,#通用调用
    终端调用字段,#终端调用
    差异调用字段,#diff 调用
    通用结果字段,#通用结果
    终端结果字段,#终端结果
    差异结果字段,#diff 结果
    搜索行匹配字段,#搜索行
    搜索文件匹配字段,#搜索文件
    搜索匹配结果字段,#匹配结果
    搜索路径结果字段,#路径结果
    读取结果字段,#读取结果
    网页来源字段,#网页来源
    网页搜索结果字段,#网页搜索
    网页抓取结果字段,#网页抓取
)#导入呈现词汇

__all__=(
    '工具运行时','默认',
    '定义工具','值模式规格转json模式','参数模式规格转json模式','校验参数','工具参数错误',
    '断言受支持json模式','断言对象json模式','校验json模式值','json模式错误',
    '代码派发开始','代码派发落定','派发开始字段','派发落定字段',
    '代码运行失败错误','运行代码名','sdk段顺序','代码sdk语言',
    'json模式转ts','渲染工具sdk','json模式转py','渲染工具sdkpy',
    '定义内容工具夹具',
    '工具未找到错误','工具输出错误',
    '调用类别','调用卡片','结果卡片','搜索形态','网页种类',
    '文件位置字段','文件差异字段','读取文件行字段',
    '通用调用字段','终端调用字段','差异调用字段',
    '通用结果字段','终端结果字段','差异结果字段',
    '搜索行匹配字段','搜索文件匹配字段','搜索匹配结果字段','搜索路径结果字段',
    '读取结果字段','网页来源字段','网页搜索结果字段','网页抓取结果字段',
)#仅中文公开名；Cordis 槽 inject/Config/default 另见类与模块尾

调度器符号=object()#调度器符号
折叠段顺序=99#折叠段顺序
工具体后中止='ABORTED'#体后中止
工具体前中止='ABORTED_BEFORE_DISPATCH'#体前中止

from .代码模式 import (
    运行代码名,#传输名
    sdk段顺序,#SDK 段顺序
    创建运行代码工具,#构建传输
    代码运行失败错误,#运行失败
    代码sdk语言,#随附 SDK 语言
    解开,#等待承诺
    已中止,#是否中止
    中止原因,#中止原因
    听中止,#登记监听
    摘中止,#去掉监听
    中止控制器,#熔合控制器
)

仅代码指令='`'+运行代码名+'` is the only tool you can call directly — a tool call naming any other tool fails. Reach every tool the SDK declares below from inside the program.'#模型可见折叠规则
sdk渲染器={
    'typescript':渲染工具sdk,#TS SDK
    'python':渲染工具sdkpy,#Python SDK
}#语言→渲染器

class 可弱引用表(dict):
    """可被弱引用的工具执行或结果表。"""
    pass#字典子类可弱引用

def 取字段(对象,键,缺省=None):
    """从映射或对象读字段。"""
    if 对象 is None:
        return 缺省#空
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else 缺省#映射键
    return getattr(对象,键,缺省)#对象属性

def 有自有(对象,键):
    """对齐 Object.hasOwn。"""
    if isinstance(对象,dict):
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:
        return False#没有字典
    return 键 in 字典#自有

def 是否正有限(值):
    """超时预算必须为正有限数。"""
    if isinstance(值,bool):
        return False#布尔不是数字
    if isinstance(值,int):
        return 值>0#正整数
    if isinstance(值,float):
        return math.isfinite(值) and 值>0#正有限浮点
    return False#其余非法

def 是否可调用(值):
    """值是否可调用。"""
    return callable(值)#函数

def 错误消息(错误):
    """从任意抛出值尽力得到人类可读消息。"""
    try:
        if isinstance(错误,Exception):
            消息=getattr(错误,'message',None)#Error.message
            if isinstance(消息,str):
                return 消息#用它
            if 错误.args:
                return str(错误.args[0])#args
            return str(错误)#字符串化
        if isinstance(错误,dict) and isinstance(错误.get('message'),str):
            return 错误['message']#对象 message
        if hasattr(错误,'message') and isinstance(getattr(错误,'message',None),str):
            return 错误.message#属性 message
        return str(错误)#其余字符串化
    except Exception:
        return '<unprintable thrown value>'#不可打印

def 从内容取失败消息(内容):
    """从策略反馈导出一条失败消息，不改其已渲染块。"""
    文本列表=[]#拼文本
    for 块 in 内容:
        if 取字段(块,'type')=='text':
            文本列表.append(取字段(块,'text',''))#文本
        else:
            文本列表.append('['+str(取字段(块,'type'))+' content]')#类型占位
    文本='\n'.join(文本列表)#换行连接
    return 文本 if len(文本)>0 else 'tool result blocked by post-execute policy'#空则用默认句

def 物化呈现(候选):
    """快照并冻结一份耐久工具结果投影，或拒绝有损数据。"""
    脱离=快照json值(候选)#脱离
    if 脱离 is None:
        raise TypeError('tool result must be losslessly JSON-serializable')#必须无损
    return 深冻结(脱离)#冻结

def 错误信息(错误):
    """抛出的 HarnessError 的结构化 name/code，否则 None。"""
    try:
        if isinstance(错误,框架错误):
            return {'name':错误.name,'code':错误.code}#框架错误才有
        return None#其余无
    except Exception:
        return None#探测抛错

def 解析并行上限(值):
    """在所属配置边界解析 run_code 重叠上限。"""
    上限=10 if 值 is None else 值#默认 10
    if isinstance(上限,bool):
        是整数=False#布尔不是数字
    elif isinstance(上限,int):
        是整数=True#整数
    elif isinstance(上限,float) and 上限.is_integer():
        是整数=True#整值浮点，对齐 Number.isInteger
    else:
        是整数=False#其余非法
    if (not 是整数) or 上限<1:
        raise Exception('maxParallelSubCalls must be a positive integer')#必须正整数
    return 上限#已校验上限

class 工具未找到错误(框架错误):
    """模型请求未注册工具时抛出。"""
    def __init__(自身,工具名,可达路径=None):
        """用名字与可选替代路径构造。"""
        if 可达路径 is None:
            消息='unknown tool "'+工具名+'"'#裸未知
        else:
            消息='unknown tool "'+工具名+'": '+可达路径#带路径
        super().__init__(消息,'UNKNOWN_TOOL')#错误码
        自身.name='ToolNotFoundError'#类名

class 工具输出错误(框架错误):
    """工具函数体或后策略值违反其声明输出时抛出。"""
    def __init__(自身,工具名,违规列表):
        """用违规构造；公开属性仅 违规列表。"""
        super().__init__('tool "'+工具名+'" returned invalid output: '+'; '.join(违规列表),'INVALID_TOOL_OUTPUT')#拼消息
        自身.name='ToolOutputError'#错误名槽
        自身.违规列表=违规列表#违规诊断列表

def 投影失败(工具名,投影器,错误):
    """把一次投影器异常转成规范的非法输出失败。"""
    return 工具输出错误(工具名,['output.'+投影器+' failed: '+错误消息(错误)])#包成输出错误

def 快照投影(工具名,投影器,候选):
    """在后续耐久结果物化之前快照一次投影器结果。"""
    try:
        脱离=快照json值(候选)#脱离
        if 脱离 is None:
            raise 工具输出错误(工具名,['output.'+投影器+' returned non-lossless JSON'])#非无损 JSON
        return 脱离#已脱离投影
    except 工具输出错误:
        raise#已是输出错误则原样抛
    except Exception as 错误:
        raise 投影失败(工具名,投影器,错误)#其它异常转输出错误

def 快照工具值(工具名,候选):
    """把一次函数体或策略值快照进规范非法输出失败类。"""
    try:
        脱离=快照json值(候选)#脱离
        if 脱离 is None:
            raise 工具输出错误(工具名,['value is not lossless JSON'])#非无损
        return 脱离#规范值
    except 工具输出错误:
        raise#已是输出错误
    except Exception as 错误:
        raise 工具输出错误(工具名,['value snapshot failed: '+错误消息(错误)])#快照失败

def 铸造执行令牌():
    """铸造同进程关联令牌。"""
    return object()#唯一身份

def 工具错误结果(错误):
    """任意抛出值→失败结果。"""
    信息=错误信息(错误)#结构化信息
    消息=错误消息(错误)#人类可读消息
    失败={'message':消息}#细节
    if 信息 is not None:
        失败['info']=信息#结构化
    return {
        'content':[{'type':'text','text':'Error: '+消息}],#Native 信封
        'isError':True,#失败
        'error':失败,#细节
    }#失败结果

def 工具体后中止结果(先前=None):
    """函数体已调用后取消取代成功时的规范结果。"""
    推迟=取字段(先前,'additionalContexts') or []#保留已推迟上下文
    结果={
        'content':[{'type':'text','text':'Error: tool call aborted'}],#模型可见
        'isError':True,#失败
        'error':{
            'message':'tool call aborted',#消息
            'info':{'name':'AbortError','code':工具体后中止},#体后码
        },#结构化
    }#中止失败
    if len(推迟)>0:
        结果['additionalContexts']=推迟#可选上下文
    return 结果#返回

def 工具体前中止结果(先前=None):
    """取消阻止工具函数体调用时的规范结果。"""
    推迟=取字段(先前,'additionalContexts') or []#保留已推迟上下文
    结果={
        'content':[{'type':'text','text':'Error: tool call aborted before dispatch'}],#模型可见
        'isError':True,#失败
        'error':{
            'message':'tool call aborted before dispatch',#消息
            'info':{'name':'AbortError','code':工具体前中止},#体前码
        },#结构化
    }#中止失败
    if len(推迟)>0:
        结果['additionalContexts']=推迟#可选上下文
    return 结果#返回

def 熔合工具信号(调用方,包装器):
    """熔合调用方与包装器取消，不嵌套 AbortSignal.any。"""
    if 调用方 is 包装器:
        def 空拆除():
            """同一信号无需熔合。"""
            return#无事
        return {'signal':调用方,'dispose':空拆除}#同一信号
    控制器=中止控制器()#熔合控制器
    监听中=False#是否已挂监听
    def 拆除():
        """拆除监听。"""
        nonlocal 监听中#修改外层
        if not 监听中:
            return#未挂则无事
        监听中=False#标记已拆
        摘中止(调用方,从调用方中止)#拆调用方
        摘中止(包装器,从包装器中止)#拆包装器
    def 从源中止(来源):
        """从某源中止。"""
        控制器.中止(中止原因(来源))#中止熔合
        拆除()#拆监听
    def 从调用方中止(*位置参数):
        """调用方中止。"""
        从源中止(调用方)#转发
    def 从包装器中止(*位置参数):
        """包装器中止。"""
        从源中止(包装器)#转发
    if 已中止(包装器):
        从包装器中止()#包装器已中止
    elif 已中止(调用方):
        从调用方中止()#调用方已中止
    else:
        监听中=True#已挂
        听中止(调用方,从调用方中止)#听调用方一次
        听中止(包装器,从包装器中止)#听包装器一次
    return {'signal':控制器.信号,'dispose':拆除}#熔合信号与拆除

class 工具层:
    """一个作用域的完整工具注册表贡献。"""
    def __init__(自身,作用域):
        """按作用域建层。"""
        def 重复错误(名):
            """重复注册诊断。"""
            if 作用域 is None:
                return Exception('tool "'+名+'" is already registered (for a per-agent variant, register through that agent\'s `agent.ctx` instead)')#全局重复
            return Exception('tool "'+名+'" is already registered in this scope')#作用域内重复
        自身.工具=具名条目(重复错误)#具名工具
        自身.限制=匿名条目()#限制
        自身.守卫=匿名条目()#守卫
        自身.模式=None#作用域呈现
    def 是否空(自身):
        """本聚合层里每张贡献表是否都空。"""
        return 自身.工具.是否空() and 自身.限制.是否空() and 自身.守卫.是否空() and 自身.模式 is None#三表皆空且无呈现
    def 接纳(自身,名):
        """本层每条已编译限制是否都接纳一个全局工具名。"""
        for 过滤器 in 自身.限制.诸值():
            白名单=过滤器.get('allow')#白名单集
            黑名单=过滤器.get('deny')#黑名单集
            if (白名单 is not None and 名 not in 白名单) or (黑名单 is not None and 名 in 黑名单):
                return False#不在白名单或在黑名单
        return True#全部接纳
    def 守卫原因(自身,执行):
        """本层在线守卫注册的第一条单调拒绝。"""
        for 守卫 in 自身.守卫.诸值():
            原因=守卫(执行)#求值
            if 原因 is not None:
                return 原因#第一条拒绝
        return None#无拒绝

class 工具运行时(服务):
    """工具注册表与执行管线。"""
    注入=['systemPrompt']#依赖系统提示词
    inject=注入#Cordis 依赖声明槽
    配置={
        'mode':枚举字段('native','code','both',默认值='native'),#呈现默认 native
        'maxParallelSubCalls':自然数字段(最小=1,默认值=10),#并行上限默认 10
    }#Loader 配置模式
    Config=配置#Cordis Config 槽

    def __init__(自身,ctx,配置=None):
        """构造运行时。"""
        super().__init__(ctx,'tools')#登记 tools 服务
        if 配置 is None:
            配置={}#缺省空配置
        呈现=取字段(配置,'mode')#配置呈现
        自身.默认模式='native' if 呈现 is None else 呈现#部署默认
        自身.最大并行子调用=解析并行上限(取字段(配置,'maxParallelSubCalls'))#校验上限
        自身.推迟上下文=weakref.WeakKeyDictionary()#推迟上下文
        自身.终止执行=weakref.WeakSet()#终止本轮集合
        自身.取消状态=weakref.WeakKeyDictionary()#取消状态
        自身.内容最终器=weakref.WeakKeyDictionary()#最终化器
        自身.规范结果=weakref.WeakKeyDictionary()#规范结果表
        def 建层(作用域):
            """建一层。"""
            return 工具层(作用域)#建层
        def 层变():
            """层变则通知。"""
            自身.ctx.emit('tools/change')#通知
        自身.层集=作用域层集(建层,层变)#作用域层
        自身.代码传输=None#run_code 传输
        自身._调度器={
            'prepare':自身.准备调度执行,#准备
            'dispatch':自身.派发调度执行,#派发
            'finalize':自身.最终化调度执行,#最终化
            'finish':自身.收尾调度执行,#收尾
        }#调度器入口
        def 提供线模式(上下文):
            """按作用域提供线模式。"""
            return 自身.接线模式(取字段(上下文,'scope'))#按作用域
        自身.ctx.systemPrompt.tools(提供线模式)#按作用域提供线模式
        if 自身.默认模式!='native':
            自身.ctx.systemPrompt.section(自身.折叠段())#折叠段
            自身.ctx.systemPrompt.section(自身.sdk段())#SDK 段

    def __getitem__(自身,键):
        """符号键控的调度器视图。"""
        if 键 is 调度器符号:
            return 自身._调度器#调度器
        raise KeyError(键)#未知键

    def 折叠段(自身):
        """code 执行器折叠的提示词陈述。"""
        def 文本(上下文):
            """仅 code 才有文案。"""
            return 仅代码指令 if 自身.解析呈现(取字段(上下文,'scope'))=='code' else ''#仅 code
        return {'name':'tools:code-only','order':折叠段顺序,'text':文本}#段登记

    def sdk段(自身):
        """生成 SDK 提示词段。"""
        def 文本(上下文):
            """按作用域渲染。"""
            呈现=自身.解析呈现(取字段(上下文,'scope'))#有效呈现
            if 呈现=='native':
                return ''#原生则空
            运行时=自身.要求代码运行时(呈现)#必需运行时
            语言=取字段(运行时,'language')#语言
            渲染=sdk渲染器.get(语言)#查渲染器
            if 渲染 is None:
                raise Exception('dsh-tools: no SDK renderer for '+str(语言))#无渲染器
            return 渲染(自身.sdk模式(取字段(上下文,'scope')))#渲染 SDK
        return {'name':'tools:sdk','order':sdk段顺序,'text':文本}#段登记

    def 解析呈现(自身,作用域=None):
        """一个作用域的智能体看见的呈现。"""
        层列表=自身.层集.链上层(作用域)#祖先到自身
        下标=len(层列表)-1#从近到远
        while 下标>=0:
            模式值=层列表[下标].模式#该层声明
            if 模式值 is not None:
                return 模式值#最近声明
            下标-=1#前进
        return 自身.默认模式#部署默认

    def 要求代码传输(自身):
        """保留的 run_code 传输，第一次需要时构建。"""
        if 自身.代码传输 is None:
            def 要求运行时():
                """组装/执行时必需。"""
                return 自身.要求代码运行时(自身.默认模式)#必需
            def 窥探运行时():
                """窥探运行时。"""
                return 自身.ctx.get('codeRuntime')#可选服务
            def 整形日志(派发):
                """整形日志。"""
                return 自身.整形派发日志(派发)#委托
            自身.代码传输=创建运行代码工具(自身,{
                'requireRuntime':要求运行时,#必需
                'peekRuntime':窥探运行时,#窥探
                'maxParallel':自身.最大并行子调用,#并行上限
                'shapeDispatchLog':整形日志,#整形日志
            })#惰性构建
        return 自身.代码传输#共享实例

    def 呈现为(自身,模式值):
        """用 mode 而不是部署默认来呈现调用作用域的工具。"""
        上下文=自身.ctx#当前上下文
        if 获取作用域(上下文) is None:
            raise Exception('tools.presentAs() requires a scoped context (agent.ctx): a context-global presentation is the `mode` config field on the tools row')#必须作用域上下文
        def 执行体():
            """组合 effect。"""
            def 写入层(层):
                """装入层。"""
                if 层.模式 is not None:
                    raise Exception('tools.presentAs("'+模式值+'") conflicts with "'+层.模式+'" already declared for this scope; one composition selects one presentation')#一作用域一种呈现
                层.模式=模式值#写入
                def 清掉():
                    """拆除时清掉。"""
                    层.模式=None#清掉
                return 清掉#拆除器
            yield 自身.层集.副作用(上下文,写入层,{'标签':'tools.presentAs()'})#写入本层 mode
            if 模式值!='native':
                yield 上下文.systemPrompt.section(自身.折叠段())#折叠段
                yield 上下文.systemPrompt.section(自身.sdk段())#SDK 段
        return 上下文.effect(执行体,'tools.presentAs()')#拆除器

    def 接线模式(自身,作用域=None):
        """为一个作用域构建线模式与提示词顺序校验用的名字。"""
        视图=自身.视图(作用域)#作用域视图
        呈现=自身.解析呈现(作用域)#有效呈现
        if 呈现=='native':
            模式列表=[自身.投影模式(定义,False) for 定义 in 视图['visible'].values()]#不脱离参数
            return {'schemas':模式列表,'knownNames':list(视图['knownNames'])}#已知名含限制前
        自身.要求代码运行时(呈现)#必需运行时与渲染器
        模式列表=[自身.投影模式(定义,False) for 定义 in 视图['visible'].values()]#含传输
        if 呈现=='code':
            return {
                'schemas':[项 for 项 in 模式列表 if 项['name']==运行代码名],#仅 run_code
                'knownNames':[运行代码名],#顺序校验只认传输
            }#折叠到 run_code
        return {'schemas':模式列表,'knownNames':list(视图['knownNames'])+[运行代码名]}#both：全部加传输

    def 要求代码运行时(自身,呈现):
        """解析代码运行时，否则抛出可操作的错误配置。"""
        运行时=自身.ctx.get('codeRuntime')#可选服务
        if 运行时 is None:
            raise Exception('dsh-tools: mode "'+呈现+'" requires a code runtime — load a ctx.codeRuntime implementation (e.g. @deepseek-ai/dsh-code-runtime-worker-thread) or set tools mode to "native"')#可操作错误
        语言=取字段(运行时,'language')#语言
        if 语言 not in sdk渲染器:
            已知=', '.join(json.dumps(名) for 名 in sdk渲染器.keys())#已知语言
            raise Exception('dsh-tools: no SDK renderer registered for runtime language '+json.dumps(语言)+' (known: '+已知+')')#未知语言
        return 运行时#已校验运行时

    def 登记(自身,定义):
        """全局或在调用智能体作用域注册。"""
        名=定义['name']#工具名
        输出=取字段(定义,'output')#输出约定
        if 输出 is None or (not isinstance(输出,dict)) or (not 是否可调用(取字段(输出,'render'))) or (取字段(输出,'presentationMeta') is not None and not 是否可调用(输出['presentationMeta'])):
            raise TypeError('tool "'+名+'" must declare output { schema, render, presentationMeta? }')#必须声明输出
        断言受支持json模式(输出['schema'])#输出模式必须是子集
        超时=取字段(定义,'timeoutMs')#超时
        if 超时 is not None and not 是否正有限(超时):
            raise TypeError('tool "'+名+'" timeoutMs must be a positive finite number')#必须正有限
        if 名==运行代码名:
            raise Exception('tool name "'+运行代码名+'" is reserved for the Code Mode presentation transport and cannot be registered or shadowed')#不得注册或遮蔽
        def 插入(层):
            """插入定义。"""
            return 层.工具.插入(名,定义)#插入
        return 自身.层集.副作用(自身.ctx,插入,{'标签':'tools.register()'})#写入当前作用域层

    def 限制(自身,过滤器):
        """为调用智能体作用域限制全局工具。"""
        作用域=获取作用域(自身.ctx)#当前作用域
        if 作用域 is None:
            raise Exception('tools.restrict() requires a scoped context (agent.ctx): a context-global restriction would mask every agent — deny the tool for the intended agent instead')#必须作用域上下文
        白名单=取字段(过滤器,'allow')#白名单
        黑名单=取字段(过滤器,'deny')#黑名单
        if 白名单 is None and 黑名单 is None:
            raise Exception('tools.restrict({}) is a no-op: pass `allow` and/or `deny` (an empty filter is almost always a materialized-empty-config bug)')#空过滤器几乎总是物化空配置缺陷
        已编译={}#编译成集
        if 白名单 is not None:
            已编译['allow']=set(白名单)#白名单集
        if 黑名单 is not None:
            已编译['deny']=set(黑名单)#黑名单集
        点名=list(白名单 or [])+list(黑名单 or [])#全部点名
        if 运行代码名 in 点名:
            raise Exception('tools.restrict() cannot name reserved Code Mode presentation transport "'+运行代码名+'"; restrict end-capability tools instead')#不得限制传输
        已知=自身.视图(作用域)['restrictableNames']#可限制的全局名
        未知=[名 for 名 in 点名 if 名 not in 已知]#未知名
        if len(未知)>0:
            词='s' if len(未知)>1 else ''#复数
            已知文本=', '.join(sorted(已知)) or '(none)'#已知或空
            raise Exception('tools.restrict() names unknown global tool'+词+' '+', '.join('"'+名+'"' for 名 in 未知)+'; known global tools: '+已知文本)#列出未知与已知
        def 追加(层):
            """追加限制。"""
            return 层.限制.追加(已编译)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'tools.restrict()'})#写入本层限制

    def 守卫(自身,守卫函数):
        """在可扩展的 tools/pre-execute 瀑布之后登记一条单调守卫。"""
        def 追加(层):
            """追加守卫。"""
            return 层.守卫.追加(守卫函数)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'tools.guard()','通知':False})#守卫不发 tools/change

    def 求守卫原因(自身,执行):
        """全局然后作用域链守卫层的第一条单调拒绝。"""
        全局原因=自身.层集.全局.守卫原因(执行)#先全局
        if 全局原因 is not None:
            return 全局原因#全局拒绝
        if 取字段(执行,'agent') is None:
            return None#无智能体则无作用域链
        for 层 in 自身.层集.链上层(执行['agent']):
            原因=层.守卫原因(执行)#本层守卫
            if 原因 is not None:
                return 原因#第一条拒绝
        return None#无拒绝

    def 视图(自身,作用域=None):
        """一次层遍历解析一个作用域需要的每项注册表事实。"""
        层列表=自身.层集.链上层(作用域)#链
        自己的=自身.层集.窥视(作用域)#自己的层
        继承={}#从全局起步
        for 名,定义 in 自身.层集.全局.工具.诸条目():
            继承[名]=定义#全局
        for 层 in 层列表:
            if 层 is 自己的:
                continue#自己的稍后
            for 名,定义 in 层.工具.诸条目():
                继承[名]=定义#较近遮蔽
        可见={}#可见
        已知名=set()#限制前已知
        可限制名=set()#可限制
        for 名,定义 in 继承.items():
            已知名.add(名)#已知
            可限制名.add(名)#可限制
            if all(层.接纳(名) for 层 in 层列表):
                可见[名]=定义#链上全部接纳才可见
        if 自己的 is not None:
            for 名,定义 in 自己的.工具.诸条目():
                已知名.add(名)#已知（但不进 restrictable）
                可见[名]=定义#可见且遮蔽
        if 自身.解析呈现(作用域)!='native':
            可见[运行代码名]=自身.要求代码传输()#追加 run_code
        return {'visible':可见,'knownNames':已知名,'restrictableNames':可限制名}#完整视图

    def 获取(自身,名,作用域=None):
        """按一个作用域看见的样子查找工具。"""
        return 自身.视图(作用域)['visible'].get(名)#可见表

    def 解析可执行(自身,名,作用域,嵌套):
        """解析一次调用可以执行的定义。"""
        工具=自身.获取(名,作用域)#可见定义
        if 工具 is None:
            return None#不可见
        if 自身.是否折叠(名,作用域,嵌套):
            return None#被折叠
        return 工具#可执行

    def 诸模式(自身,作用域=None):
        """把可见定义投影到白名单的面向模型模式字段。"""
        return [自身.投影模式(定义,True) for 定义 in 自身.视图(作用域)['visible'].values()]#脱离参数

    def sdk模式(自身,作用域=None):
        """把可见可调用工具投影到生成的 Code Mode SDK 约定。"""
        结果=[]#SDK 模式
        for 定义 in 自身.视图(作用域)['visible'].values():
            if 定义['name']==运行代码名:
                continue#排除传输自身
            输出=快照json值(定义['output']['schema'])#输出模式快照
            if 输出 is None:
                raise Exception('tool "'+定义['name']+'" output schema must be lossless JSON before SDK projection')#必须无损
            项=自身.投影模式(定义,True)#模型字段
            项['output']=输出#规范输出模式
            结果.append(项)#收下
        return 结果#SDK 模式

    def 投影模式(自身,定义,脱离参数):
        """把一个定义投影到面向模型的模式字段。"""
        名=定义['name']#名
        描述=定义['description']#描述
        参数=定义['parameters']#参数
        脱离=快照json值(参数) if 脱离参数 else 参数#可选脱离
        if 脱离 is None:
            raise Exception('tool "'+名+'" parameters must be lossless JSON before schema projection')#必须无损
        return {'name':名,'description':描述,'parameters':脱离}#模型模式

    def 执行模式(自身,执行输入):
        """经调用方可见工具定义给待处理调用分类。"""
        工具=自身.解析可执行(执行输入['name'],取字段(执行输入,'agent'),取字段(执行输入,'parent') is not None)#可执行定义
        if 工具 is None or not 取字段(工具,'isConcurrencySafe'):
            return {'kind':'exclusive'}#无分类器则独占
        try:
            并发安全=工具['isConcurrencySafe'](执行输入['arguments'])#求值
            return {'kind':'parallel'} if 并发安全 is True else {'kind':'exclusive'}#只有 true 才并行
        except Exception:
            return {'kind':'exclusive'}#失败关闭

    def 整形派发日志(自身,派发):
        """对一次已落定子派发跑 tools/code-dispatch-log 瀑布。"""
        def 默认内容():
            """默认原样内容。"""
            return 派发['content']#原样
        try:
            return 解开(自身.ctx.waterfall(作用域目标(自身,取字段(派发,'agent')),'tools/code-dispatch-log',派发,默认内容))#按智能体过滤
        except Exception as 错误:
            自身.ctx.logger.warn('tools: code-dispatch-log listener failed for '+派发['name']+': '+错误消息(错误)+'; logging the original settled content')#记警告
            return 派发['content']#回落原始内容

    def 是否折叠(自身,名,作用域,嵌套):
        """code 模式折叠是否拒绝模型直接调用。"""
        return (not 嵌套) and 自身.解析呈现(作用域)=='code' and 名!=运行代码名#非嵌套且 code 且不是传输

    def 执行(自身,执行输入):
        """经预策略、守卫、环绕派发、后策略、内容最终化与最终通知执行。"""
        def 下一步(已准备):
            """准备后跑完。"""
            return 自身.跑完已准备(已准备)#跑完
        return 自身.准备执行(执行输入,下一步)#准备后跑完

    def 跑完已准备(自身,已准备):
        """跑完已准备执行。"""
        种类=已准备['kind']#按准备种类
        if 种类=='dispatch':
            已派发=自身.派发调度执行(已准备['exec'])#环绕+体
            if 已派发['kind']=='post-result':
                return 自身.最终化调度执行(已准备['exec'],已派发['result'])#后执行+收尾
            return 自身.收尾调度执行(已准备['exec'],已派发['result'])#跳过后执行
        if 种类=='post-result':
            return 自身.最终化调度执行(已准备['exec'],已准备['result'])#后执行+收尾
        if 种类=='final-result':
            return 自身.收尾调度执行(已准备['exec'],已准备['result'])#只收尾
        return 断言永不(已准备,'scheduled tool preparation')#未覆盖种类

    def 铸造执行(自身,执行输入):
        """铸造执行对象。"""
        推迟列表=[]#本执行推迟的上下文
        令牌=铸造执行令牌()#关联令牌
        调用号=执行输入['callId']#本次调用 id
        根调用号=取字段(执行输入,'rootCallId')#根调用
        if 根调用号 is None:
            根调用号=调用号#根即自身
        名=执行输入['name']#工具名
        智能体=取字段(执行输入,'agent')#智能体
        父=取字段(执行输入,'parent')#父令牌
        信号=执行输入['signal']#调用方信号
        可见=自身.获取(名,智能体)#可见定义
        已折叠=可见 is not None and 自身.是否折叠(名,智能体,父 is not None)#可见但被折叠
        执行盒=[None]#铸造后的执行对象
        def 推迟上下文(上下文块):
            """推迟上下文。"""
            推迟列表.append(上下文块)#收下
        def 终止本轮():
            """终止本轮。"""
            if 执行盒[0] is not None:
                自身.终止执行.add(执行盒[0])#记入集合
        基础=可弱引用表({
            'token':令牌,#令牌
            'callId':调用号,#调用 id
            'rootCallId':根调用号,#根
            'name':名,#名
            'signal':信号,#信号
            'deferContext':推迟上下文,#推迟
            'concludeTurn':终止本轮,#终止
        })#共享字段
        if 智能体 is not None:
            基础['agent']=智能体#有智能体才带
        if 父 is not None:
            基础['parent']=父#有父才带
        捕获最终器=None#开始时快照
        if 可见 is not None and 取字段(可见,'finalizeContent') is not None:
            捕获最终器=可见['finalizeContent']#快照回调
        def 最终器():
            """按折叠/中止决定是否保留。"""
            return None if 已折叠 and not 已中止(信号) else 捕获最终器#折叠且未中止则丢掉
        try:
            脱离=快照json值(执行输入['arguments'])#脱离
            if 脱离 is None:
                raise TypeError('tool execution arguments must be losslessly JSON-serializable')#必须无损
            执行=可弱引用表(基础)#拷贝基础
            执行['arguments']=深冻结(脱离)#冻结参数
            执行盒[0]=执行#供终止本轮键控
            自身.推迟上下文[执行]=推迟列表#挂推迟表
            自身.内容最终器[执行]=最终器()#挂最终化器
            自身.取消状态[执行]={'callerSignal':信号,'bodyInvoked':False}#挂取消状态
            if 已折叠:
                if 已中止(信号):
                    return {'kind':'final-result','exec':执行,'result':工具体前中止结果()}#体前中止
                return {
                    'kind':'final-result',#跳过策略
                    'exec':执行,#已铸造执行
                    'result':工具错误结果(工具未找到错误(
                        名,#工具名
                        'only `'+运行代码名+'` is callable directly — call `'+名+'` from inside a `'+运行代码名+'` program instead',#替代路径
                    )),#未知工具但带路径
                }#折叠拒绝
            return {'kind':'ready','exec':执行}#进入策略管线
        except Exception as 错误:
            执行=可弱引用表(基础)#参数未脱离
            执行['arguments']=None#未脱离
            执行盒[0]=执行#供终止本轮键控
            自身.内容最终器[执行]=最终器()#仍可能走最终化器
            return {'kind':'final-result','exec':执行,'result':工具错误结果(错误)}#物化错误

    def 准备调度执行(自身,输入):
        """为调度器跑有序预执行与单调守卫阶段。"""
        def 原样(已准备):
            """准备后原样返回。"""
            return 已准备#原样
        return 自身.准备执行(输入,原样)#准备后原样返回

    def 准备执行(自身,输入,下一步):
        """铸造并跑预策略。"""
        已造=自身.铸造执行(输入)#铸造
        if 已造['kind']!='ready':
            return 下一步(已造)#已是最终/后结果
        执行=已造['exec']#可变执行
        if 自身.调用方已取消(执行):
            return 下一步({'kind':'final-result','exec':执行,'result':工具体前中止结果()})#体前中止
        try:
            载体=作用域目标(自身,取字段(执行,'agent'))#作用域载体
            def 默认允许():
                """默认允许。"""
                return {'kind':'allow'}#允许
            门=解开(自身.ctx.waterfall(载体,'tools/pre-execute',执行,默认允许))#预执行瀑布
            if 门['kind']=='ask':
                询问决议=自身.服务询问(执行,门)#走审批接缝
            else:
                询问决议={'decision':门,'approvalCancelled':False}#允许或拒绝
            决策=询问决议['decision']#最终允许/拒绝
            if 自身.调用方已取消(执行) and 询问决议['approvalCancelled']:
                return 下一步({'kind':'post-result','exec':执行,'result':工具体前中止结果()})#仍走后执行
            if 决策['kind']=='allow':
                拒绝原因=自身.求守卫原因(执行)#单调守卫
            else:
                拒绝原因=决策['reason']#策略拒绝原因
            if 拒绝原因 is not None:
                return 下一步({
                    'kind':'post-result',#还要后执行
                    'exec':执行,#执行
                    'result':自身.物化最终结果({
                        'content':[{'type':'text','text':'Error: '+拒绝原因}],#模型可见错误
                        'isError':True,#失败
                        'error':{'message':拒绝原因},#失败细节
                    }),#物化拒绝
                })#后执行仍能看见拒绝
            if 自身.调用方已取消(执行):
                return 下一步({'kind':'post-result','exec':执行,'result':工具体前中止结果()})#体前中止，仍走后执行
            return 下一步({'kind':'dispatch','exec':执行})#进入派发
        except Exception as 错误:
            return 下一步({'kind':'final-result','exec':执行,'result':工具错误结果(错误)})#跳过后执行

    def 调用方已取消(自身,执行):
        """原始调用方信号当前是否已中止。"""
        状态=自身.取消状态.get(执行)#取消状态
        if 状态 is None:
            raise Exception('tool registry scheduler invariant violated: missing cancellation state')#调度器不变量
        return 已中止(状态['callerSignal'])#原始信号

    def 取消结果(自身,执行,先前=None):
        """按工具函数体是否已开始选出的规范取消结局。"""
        状态=自身.取消状态.get(执行)#取消状态
        if 状态 is None:
            raise Exception('tool registry scheduler invariant violated: missing cancellation state')#调度器不变量
        if 状态['bodyInvoked']:
            return 工具体后中止结果(先前)#体后中止
        return 工具体前中止结果(先前)#体前中止

    def 派发函数体(自身,执行):
        """用熔回任何环绕包装器替换的原始调用方信号派发已注册函数体。"""
        状态=自身.取消状态.get(执行)#取消状态
        if 状态 is None:
            raise Exception('tool registry scheduler invariant violated: missing cancellation state')#调度器不变量
        包装器信号=执行['signal']#包装器信号
        熔合=熔合工具信号(状态['callerSignal'],包装器信号)#熔合调用方与包装器
        信号=熔合['signal']#熔合后信号
        if 已中止(信号):
            熔合['dispose']()#拆除监听
            return 工具体前中止结果()#体前中止
        执行['signal']=信号#函数体看见熔合信号
        try:
            工具=自身.解析可执行(执行['name'],取字段(执行,'agent'),取字段(执行,'parent') is not None)#可执行定义
            if not 工具:
                raise 工具未找到错误(执行['name'])#不可见或被折叠
            状态['bodyInvoked']=True#此后取消走 ABORTED
            返回值=解开(工具['execute'](执行['arguments'],执行))#跑函数体
            结果=自身.创建成功结果(执行,工具,返回值)#校验并渲染
            return 工具体后中止结果(结果) if 已中止(信号) else 结果#成功被中止取代
        except Exception as 错误:
            return 工具错误结果(错误)#失败结果
        finally:
            熔合['dispose']()#拆除熔合监听
            执行['signal']=包装器信号#还给包装器

    def 派发调度执行(自身,执行):
        """跑环绕派发与工具函数体。"""
        try:
            载体=作用域目标(自身,取字段(执行,'agent'))#作用域载体
            def 最内层():
                """最内层跑体。"""
                return 自身.派发函数体(执行)#跑体
            结果=解开(自身.ctx.waterfall(载体,'tools/execute',执行,最内层))#环绕执行瀑布
            已归一=自身.归一派发结果(执行,结果)#经输出约定归一
            推迟=自身.推迟上下文.get(执行)#体推迟的上下文
            if 推迟 is None:
                raise Exception('tool registry scheduler invariant violated: unprepared execution')#未准备
            if len(推迟)==0:
                带推迟=已归一#原样
            else:
                合并=dict(已归一)#拷贝
                合并['additionalContexts']=list(推迟)+list(已归一.get('additionalContexts') or [])#体的在前，包装器的在后
                带推迟=自身.标记规范(执行,合并)#并入推迟上下文
            if 自身.调用方已取消(执行) and not 带推迟['isError']:
                最终=自身.取消结果(执行,带推迟)#按体是否已调用选码
            else:
                最终=带推迟#原样
            return {'kind':'post-result','result':最终}#还要后执行
        except Exception as 错误:
            return {'kind':'final-result','result':工具错误结果(错误)}#跳过后执行

    def 最终化调度执行(自身,执行,结果):
        """跑有序后执行，再应用定义拥有的内容最终化。"""
        try:
            后结果=自身.后执行(执行,结果)#后策略
            if 自身.调用方已取消(执行) and not 后结果['isError']:
                候选=自身.取消结果(执行,后结果)#按体是否已调用选码
            else:
                候选=后结果#原样
            return 自身.收尾调度执行(执行,候选)#收尾
        except Exception as 错误:
            return 自身.收尾调度执行(执行,工具错误结果(错误))#仍收尾

    def 收尾调度执行(自身,执行,结果):
        """物化候选，应用定义拥有的内容最终化，再物化并通知权威结果。"""
        try:
            已物化=自身.物化最终结果(结果)#快照冻结
        except Exception as 错误:
            已物化=自身.物化最终结果(工具错误结果(错误))#改成错误再物化
        try:
            最终=自身.物化最终结果(自身.应用最终内容(执行,已物化))#应用最终内容再物化
        except Exception as 错误:
            最终=自身.物化最终结果(工具错误结果(错误))#改成错误
        自身.通知结果(执行,最终)#通知观察者
        return 最终#权威结果

    def 应用最终内容(自身,执行,结果):
        """应用已快照的工具自有内容变换。"""
        最终化=自身.内容最终器.get(执行)#开始时快照
        if 最终化 is None:
            return 结果#无变换
        内容=最终化(执行,结果)#调用（不得抛）
        if 内容 is None:
            return 结果#undefined 保留
        替换=dict(结果)#拷贝
        替换['content']=内容#替换内容
        return 替换#新结果

    def 通知结果(自身,执行,结果):
        """通知观察者，不把变更或错误通道暴露进结局。"""
        深冻结(执行)#冻结执行
        工具名=执行['name']#日志用身份
        调用号=执行['callId']#调用 id
        def 报告失败(错误):
            """收住观察者失败。"""
            自身.ctx.logger.warn('tool "'+工具名+'" ('+str(调用号)+'): tools/result observer failed: '+错误消息(错误))#记警告
        参数=[作用域目标(自身,取字段(执行,'agent')),'tools/result',执行,结果]#载体、事件、载荷
        回调们=list(自身.ctx.events.dispatch('emit',参数))#取出 emit 回调
        for 回调 in 回调们:
            try:
                返回=回调(执行,结果)#调用观察者
                if 是否thenable(返回):
                    def 盯住(任务=返回):
                        """收住返回 Promise 拒绝。"""
                        try:
                            任务.等待()#等待
                        except Exception as 错误:
                            报告失败(错误)#记警告
                    线程=threading.Thread(target=盯住)#后台观察
                    线程.daemon=True#不挡住退出
                    线程.start()#启动
            except Exception as 错误:
                报告失败(错误)#记警告

    def 服务询问(自身,执行,询问):
        """经审批接缝把 ask 决策解析成允许/拒绝。"""
        审批=自身.ctx.get('approval')#可选审批服务
        if 审批 is None:
            return {
                'decision':{'kind':'deny','reason':取字段(询问,'reason') or ('tool "'+执行['name']+'" requires approval (not yet supported)')},#缺审批通道
                'approvalCancelled':False,#不是取消
            }#降级拒绝
        if 取字段(执行,'agent') is None:
            return {
                'decision':{'kind':'deny','reason':'tool "'+执行['name']+'" requires approval, but the call has no agent to route it through'},#无处路由
                'approvalCancelled':False,#不是取消
            }#降级拒绝
        请求={
            'agent':执行['agent'],#路由智能体
            'toolName':执行['name'],#工具名
            'callId':执行['callId'],#调用 id
            'signal':执行['signal'],#取消信号
        }#审批请求
        if 取字段(询问,'reason') is not None:
            请求['reason']=询问['reason']#可选原因
        结局=解开(审批.request(请求))#请求一次审批
        if 结局=='allowed-once':
            return {'decision':{'kind':'allow'},'approvalCancelled':False}#允许一次
        if 结局=='rejected':
            return {'decision':{'kind':'deny','reason':'the user rejected tool "'+执行['name']+'"'},'approvalCancelled':False}#人的不
        if 结局=='cancelled':
            return {'decision':{'kind':'deny','reason':'approval for tool "'+执行['name']+'" was cancelled'},'approvalCancelled':True}#取消
        if 结局=='unavailable':
            return {'decision':{'kind':'deny','reason':'tool "'+执行['name']+'" requires approval, but no approval channel is available'},'approvalCancelled':False}#无通道
        return 断言永不(结局,'ApprovalOutcome')#穷尽

    def 后执行(自身,执行,结果):
        """对已派发 result 跑 tools/post-execute 瀑布并应用其决策。"""
        def 默认接受():
            """默认接受。"""
            return {'kind':'accept'}#接受
        决策=解开(自身.ctx.waterfall(作用域目标(自身,取字段(执行,'agent')),'tools/post-execute',执行,结果,默认接受))#后执行瀑布
        决策上下文=决策.get('additionalContexts') or []#决策附带上下文
        if 决策['kind']=='block':
            消息=从内容取失败消息(决策['feedback'])#从反馈取消息
            失败={
                'content':决策['feedback'],#纠正内容
                'isError':True,#失败
                'error':{'message':消息},#失败细节
            }#规范失败
            if len(决策上下文)>0:
                失败['additionalContexts']=决策上下文#只带挡住决策的上下文
            return 自身.标记规范(执行,失败)#挡住
        if 有自有(决策,'content') and 有自有(决策,'value'):
            raise TypeError('tools/post-execute accept decision cannot replace both value and content')#不得同时替换
        附加=list(结果.get('additionalContexts') or [])+list(决策上下文)#体的加决策的
        if 有自有(决策,'value'):
            if 结果['isError']:
                raise TypeError('tools/post-execute cannot replace the value of a failed result')#失败不能换值
            工具=自身.解析可执行(执行['name'],取字段(执行,'agent'),取字段(执行,'parent') is not None)#可执行定义
            if 工具 is None:
                raise 工具未找到错误(执行['name'])#不可见
            替换=自身.创建成功结果(执行,工具,决策['value'])#按输出约定重投影
            合并=dict(替换)#新成功
            if len(附加)>0:
                合并['additionalContexts']=附加#合并上下文
            return 自身.标记规范(执行,合并)#规范成功
        接受=dict(结果)#原结果
        if 决策.get('content') is not None:
            接受['content']=决策['content']#可选换内容
        if len(附加)>0:
            接受['additionalContexts']=附加#合并上下文
        return 自身.标记规范(执行,接受)#接受，可选换内容

    def 标记规范(自身,执行,结果):
        """把一份注册表已归一结果只标成其所属派发的规范结果。"""
        if type(结果) is dict:
            结果=可弱引用表(结果)#普通字典不可作弱键
        自身.规范结果[结果]=执行['token']#按令牌键控
        return 结果#原对象

    def 创建成功结果(自身,执行,工具,候选):
        """快照、校验、渲染，并可选投影一次成功函数体值。"""
        脱离=快照工具值(工具['name'],候选)#脱离规范值
        违规=校验json模式值(工具['output']['schema'],脱离,'value')#按输出模式校验
        if len(违规)>0:
            raise 工具输出错误(工具['name'],违规)#非法输出
        值=深冻结(脱离)#冻结值
        try:
            已渲染=工具['output']['render'](执行['arguments'],值)#纯投影
        except Exception as 错误:
            raise 投影失败(工具['name'],'render',错误)#转输出错误
        内容=快照投影(工具['name'],'render',已渲染)#快照内容
        元数据=None#呈现元数据
        if 取字段(执行,'parent') is None and 取字段(工具['output'],'presentationMeta') is not None:
            try:
                已投影=工具['output']['presentationMeta'](执行['arguments'],值)#纯投影
            except Exception as 错误:
                raise 投影失败(工具['name'],'presentationMeta',错误)#转输出错误
            元数据=快照投影(工具['name'],'presentationMeta',已投影)#快照元数据
        终止=执行 in 自身.终止执行#是否终止本轮
        成功={
            'isError':False,#成功
            'value':值,#规范值
            'content':内容,#内容
        }#物化并标记
        if 元数据 is not None:
            成功['meta']=元数据#可选元数据
        if 终止:
            成功['concludesTurn']=True#可选终止
        return 自身.标记规范(执行,自身.物化最终结果(成功))#断言成功

    def 归一派发结果(自身,执行,结果):
        """经所属输出约定归一环绕派发包装器写出的结果。"""
        if 自身.规范结果.get(结果) is 执行['token']:
            return 结果#已是本派发规范结果
        if 结果['isError']:
            失败={
                'isError':True,#失败
                'error':结果['error'],#失败细节
                'content':结果['content'],#内容
            }#拷贝字段
            if 有自有(结果,'meta'):
                失败['meta']=结果['meta']#可选元数据
            if 有自有(结果,'additionalContexts'):
                失败['additionalContexts']=结果['additionalContexts']#可选上下文
            return 自身.标记规范(执行,失败)#标记为本派发
        工具=自身.解析可执行(执行['name'],取字段(执行,'agent'),取字段(执行,'parent') is not None)#可执行定义
        if 工具 is None:
            raise 工具未找到错误(执行['name'])#不可见
        已归一=自身.创建成功结果(执行,工具,结果['value'])#按输出约定重投影
        合并=dict(已归一)#新成功
        if 有自有(结果,'additionalContexts'):
            合并['additionalContexts']=结果['additionalContexts']#保留包装器上下文
        return 自身.标记规范(执行,合并)#标记

    def 物化最终结果(自身,结果):
        """在 tools/result 之前把权威提交结局物化一次。"""
        呈现={'content':结果['content']}#耐久呈现字段
        if 有自有(结果,'meta'):
            呈现['meta']=结果['meta']#可选元数据
        if 有自有(结果,'additionalContexts'):
            呈现['additionalContexts']=结果['additionalContexts']#可选上下文
        if 结果['isError']:
            失败={'isError':True,'error':结果['error']}#失败不含 value
            失败.update(呈现)#呈现字段
            return 物化呈现(失败)#快照冻结失败
        成功={'isError':False}#成功
        成功.update(呈现)#呈现字段
        if 结果.get('concludesTurn') is True:
            成功['concludesTurn']=True#可选终止
        脱离=物化呈现(成功)#成功呈现（不含 value）
        合并=dict(脱离)#拷贝
        合并['value']=结果['value']#再并入执行局部 value
        return 深冻结(合并)#冻结

默认=工具运行时#默认导出运行时
default=工具运行时#Cordis 默认导出槽（不入 __all__）
