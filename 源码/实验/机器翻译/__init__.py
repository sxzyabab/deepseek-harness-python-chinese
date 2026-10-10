'匿名文本翻译，可选把与提供方无关的结果写进耐久会话'
import threading
from urllib.parse import urlsplit,urlunsplit
from ...依赖.cordis.服务 import 服务
from ...依赖.schemastery import 无数据
from ...依赖.工具 import 未传参
from ...工具.值 import 断言永不
from .异常 import 翻译错误
from .提供方 import 匿名配方,翻译文本
from .存储 import 翻译存储
from .深求 import 深求配方,可用付费提供方,用深求翻译
from .类型 import 中止控制器,码元数,合并信号,若已中止则抛出

__all__=['机器翻译','翻译错误']

提供方表=('google','bing','deepseek-account','deepseek-official')
默谷歌端点='https://translate.googleapis.com/translate_a/single'
默必应端点='https://edge.microsoft.com/translate/translatetext'
定时器上限=2147483647
端点消息='翻译端点必须是不带凭据、不带片段的 HTTP(S) 地址'

def 端点(值):
    '只接受不带用户信息、不带片段的 http 或 https 地址'
    if not isinstance(值,str) or len(值)==0:
        raise ValueError(端点消息)
    拆开=urlsplit(值)
    if 拆开.scheme not in ('http','https') or not 拆开.hostname or 拆开.username or 拆开.password or 拆开.fragment!='':
        raise ValueError(端点消息)
    主机=拆开.hostname.lower()
    if ':' in 主机:
        主机='['+主机+']'
    if 拆开.port is not None:
        默认端口=(拆开.scheme=='http' and 拆开.port==80) or (拆开.scheme=='https' and 拆开.port==443)
        if not 默认端口:
            主机=主机+':'+str(拆开.port)
    路径=拆开.path if len(拆开.path)>0 else '/'
    return urlunsplit((拆开.scheme,主机,路径,拆开.query,''))

def 取整数(配置值,键,默认,最小,最大=None):
    '缺省用默认；布尔和小数都拒绝'
    if 键 not in 配置值 or 配置值[键] is None:
        值=默认
    else:
        值=配置值[键]
    if isinstance(值,bool) or not isinstance(值,int) or 值<最小 or (最大 is not None and 值>最大):
        raise ValueError('翻译配置 '+键+' 超出允许范围')
    return 值

def 规范化配置(配置值):
    '补默认值并检查端点；模式校验返回的也是这份字典'
    if 配置值 is None:
        配置值={}
    if not isinstance(配置值,dict):
        raise ValueError('翻译配置必须是对象')
    if 'provider' not in 配置值 or 配置值['provider'] is None:
        提供方='bing'
    else:
        提供方=配置值['provider']
    if 提供方 not in 提供方表:
        raise ValueError('翻译提供方必须是 google、bing、deepseek-account 或 deepseek-official')
    谷歌=默谷歌端点 if 'googleEndpoint' not in 配置值 or 配置值['googleEndpoint'] is None else 配置值['googleEndpoint']
    必应=默必应端点 if 'bingEndpoint' not in 配置值 or 配置值['bingEndpoint'] is None else 配置值['bingEndpoint']
    return {
        'provider':提供方,
        'googleEndpoint':端点(谷歌),
        'bingEndpoint':端点(必应),
        'timeoutMs':取整数(配置值,'timeoutMs',10000,1,定时器上限),
        'maxTextChars':取整数(配置值,'maxTextChars',4000,2),
        'maxResponseBytes':取整数(配置值,'maxResponseBytes',1024*1024,1),
        'deepseekTimeoutMs':取整数(配置值,'deepseekTimeoutMs',60000,1,定时器上限),
        'deepseekMaxOutputTokens':取整数(配置值,'deepseekMaxOutputTokens',8192,1),
    }

class 配置模式:
    '机器翻译路由与上限'
    def 校验数据(自身,数据=未传参):
        '缺省配置展开成完整字典'
        if 数据 is 未传参 or 数据 is 无数据 or 数据 is None:
            数据={}
        return 规范化配置(数据)

配置=配置模式()
依赖=[]

class 机器翻译(服务):
    '显式路由、取消和卸干净之后才退出'
    def __init__(自身,上下文,配置值=None):
        '登记 translator，并在卸载时中止寿命'
        super().__init__(上下文,'translator')
        自身.上下文=上下文
        自身.配置=规范化配置({} if 配置值 is None else 配置值)
        自身.存储=翻译存储(上下文)
        自身.寿命=中止控制器()
        自身.在途=[]
        自身.在途锁=threading.Lock()

        def 登记寿命():
            '交出卸载时中止并等待其他线程的拆除器'
            def 拆():
                '中止后来的调用；不等待正在跑拆除器的那条线程'
                自身.寿命.中止(RuntimeError('翻译服务已拆除'))
                本线程=threading.get_ident()
                with 自身.在途锁:
                    待等=list(自身.在途)
                for 门,线程 in 待等:
                    if 线程!=本线程:
                        门.wait()
            return 拆

        上下文.副作用(登记寿命)

    @property
    def 最大文本字符(自身):
        '单次请求接受的 UTF-16 码元上限'
        return 自身.配置['maxTextChars']

    def 可用提供方(自身,信号=None):
        '不发推理；匿名选择后面跟着目前合格的付费路由'
        合并=自身.合成(信号)

        def 工作():
            '在服务在途表里做发现'
            return 可用付费提供方(自身.上下文,自身.配置,合并)

        return 自身.进入(工作)

    def 解析(自身,请求):
        '只补提供方和源语言，不发送文本'
        若已中止则抛出(自身.寿命.信号)
        自身.断言文本上限(请求['text'])
        if 'provider' in 请求 and 请求['provider'] is not None:
            提供方=请求['provider']
        else:
            提供方=自身.配置['provider']
        if 'sourceLanguage' in 请求 and 请求['sourceLanguage'] is not None:
            来源=请求['sourceLanguage']
        else:
            来源='auto'
        基础={'text':请求['text'],'targetLanguage':请求['targetLanguage'],'sourceLanguage':来源}
        有会话='sessionId' in 请求 and 请求['sessionId'] is not None
        if 提供方=='google' or 提供方=='bing':
            if 有会话:
                基础['sessionId']=请求['sessionId']
            基础['provider']=提供方
            return 基础
        if 提供方=='deepseek-account' or 提供方=='deepseek-official':
            if not 有会话:
                raise 翻译错误('TRANSLATION_SESSION_REQUIRED','付费翻译需要一份耐久会话')
            基础['provider']=提供方
            基础['sessionId']=请求['sessionId']
            return 基础
        return 断言永不(提供方)

    def 翻译(自身,规格,信号=None):
        '按已解析规格翻译；带会话时先落耐久再返回'
        自身.断言文本上限(规格['text'])
        合并=自身.合成(信号)
        if 规格['provider']=='google' or 规格['provider']=='bing':
            配方=匿名配方(规格['provider'],自身.配置)
        else:
            配方=深求配方(自身.配置)
        身份={
            'provider':规格['provider'],
            'text':规格['text'],
            'sourceLanguage':规格['sourceLanguage'],
            'targetLanguage':规格['targetLanguage'],
            'recipe':配方,
        }

        def 在会话(标识):
            '未命中缓存才真正调用提供方'
            def 操作(日志):
                '付费走原生模型，匿名端点先记请求再翻译'
                if 规格['provider']=='deepseek-account' or 规格['provider']=='deepseek-official':
                    return 用深求翻译(自身.上下文,规格,自身.配置,合并,日志,身份)
                if 规格['provider']=='google' or 规格['provider']=='bing':
                    序号=日志['请求'](身份)
                    若已中止则抛出(合并)
                    文本=翻译文本(规格,自身.配置,合并)
                    若已中止则抛出(合并)
                    日志['结果'](序号,文本)
                    return 文本
                return 断言永不(规格['provider'])

            return 自身.存储.运行(标识,身份,合并,操作)

        def 工作():
            '无会话的匿名请求直接发出；付费始终进会话'
            if 规格['provider']=='google' or 规格['provider']=='bing':
                if 'sessionId' not in 规格 or 规格['sessionId'] is None:
                    return 翻译文本(规格,自身.配置,合并)
                return 在会话(规格['sessionId'])
            if 规格['provider']=='deepseek-account' or 规格['provider']=='deepseek-official':
                return 在会话(规格.get('sessionId'))
            return 断言永不(规格['provider'])

        return 自身.进入(工作)

    def 合成(自身,调用方=None):
        '寿命已中止则立刻失败；否则和调用方信号合成'
        若已中止则抛出(自身.寿命.信号)
        if 调用方 is None:
            信号=自身.寿命.信号
        else:
            信号=合并信号(调用方,自身.寿命.信号)
        若已中止则抛出(信号)
        return 信号

    def 进入(自身,工作):
        '记下这条线程，卸载时可以等它结束'
        门=threading.Event()
        记录=(门,threading.get_ident())
        with 自身.在途锁:
            自身.在途.append(记录)
        try:
            return 工作()
        finally:
            with 自身.在途锁:
                if 记录 in 自身.在途:
                    自身.在途.remove(记录)
            门.set()

    def 断言文本上限(自身,文本):
        '超过配置的 UTF-16 码元数就拒绝'
        上限=自身.配置['maxTextChars']
        if 码元数(文本)>上限:
            raise 翻译错误('TRANSLATION_TEXT_LIMIT','翻译文本超过 '+str(上限)+' 个 UTF-16 码元')

def 应用(上下文,配置值=None):
    '挂上机器翻译服务'
    return 机器翻译(上下文,配置值)

name='translator'
inject=依赖
apply=应用
Config=配置
default=机器翻译
