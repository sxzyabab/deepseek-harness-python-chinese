"""构造一条已配置路由注册进适配器 Models 集合的 pi-ai Provider。

对齐上游 `llm-pi-ai/src/provider.ts`。公开面仅中文名；无英文别名。
"""
import pi_ai#外部依赖胶水（pi-ai SDK）
from .目录 import 目录提供方,配置错误#已安装目录提供方查找与本包异常

__all__=('受支持协议','线束密钥认证','路由认证','复用目录提供方','构建提供方')#仅中文公开名

协议表={
    #'openai-completions':pi_ai.openAICompletionsApi,#OpenAI Completions
    #'openai-responses':pi_ai.openAIResponsesApi,#OpenAI Responses
    #'anthropic-messages':pi_ai.anthropicMessagesApi,#Anthropic Messages
}#可手声明的协议表

def 受支持协议():
    """已配置路由可以点名的每条线路协议，按到达次数从多到少。"""
    return list(协议表.keys())#表的键顺序

def 线束密钥认证(名称):
    """给 harness 自己认证的路由用的 api-key 认证。"""
    def 解析(选项):
        """按次解析密钥覆盖。选项是流式调用 dict。"""
        if 'credential' not in 选项:#本次未带凭证
            return {'auth':{},'source':名称}#空认证头表示这次不附加 api-key
        凭证=选项['credential']#本次凭证 dict
        if 凭证 is None:#显式空凭证
            return {'auth':{},'source':名称}#不附加 api-key
        if 'key' not in 凭证:#凭证没有 key
            return {'auth':{},'source':名称}#不附加 api-key
        密钥=凭证['key']#密钥值
        认证头={} if 密钥 is None else {'apiKey':密钥}#有密钥才带上
        return {'auth':认证头,'source':名称}#解析结果；source 钉本路由展示名
    return {'name':名称,'resolve':解析}#认证对象

def 路由认证(规格,目录):
    """一条路由解析其凭证所经的认证。规格为 dict；目录为 SDK 提供方对象或 None。"""
    if 目录 is None:#手声明路由没有目录认证，只用 harness 密钥
        return {'apiKey':线束密钥认证(规格['displayName'])}#手声明：只用harness密钥
    目录认证=目录.auth#SDK 对象属性
    if 目录认证 is None:#目录没有认证块
        return {'apiKey':线束密钥认证(规格['displayName'])}#回落到 harness 密钥
    密钥方法=目录认证.apiKey#SDK 认证对象上的密钥方法；缺席则为 None
    if 密钥方法 is not None or not 规格['namesCredential']:#已有密钥方法，或不点名凭证，都保留目录认证，避免覆盖 OAuth 以外的方法
        return 目录认证#已有密钥方法或不点名凭证则保留
    合并=dict(vars(目录认证))#拷贝 SDK 认证对象字段，再补 harness 密钥方法
    合并['apiKey']=线束密钥认证(规格['displayName'])#加上harness密钥方法；仅 OAuth 的目录提供方走这条
    return 合并#仅OAuth的目录提供方

def 复用目录提供方(基,规格):
    """用本路由的模型与身份复用已安装目录提供方。基为 SDK 对象，规格为 dict。"""
    if 'baseURL' in 规格 and 规格['baseURL'] is not None:#配置显式写了端点（含空串，空串在配置入口已拒）
        基址=规格['baseURL']#配置端点优先
    else:#缺席才用目录端点
        基址=基.baseUrl#SDK 对象端点；可能仍为 None
    def 取模型():
        """本路由物化模型。"""
        return 规格['models']#已物化模型
    def 流(模型,上下文,选项):
        """委托目录提供方流。"""
        return 基.stream(模型,上下文,选项)#委托流
    def 简化流(模型,上下文,选项):
        """委托目录提供方简化流。"""
        return 基.streamSimple(模型,上下文,选项)#委托简化流
    提供方={
        'id':规格['provider'],#路由键
        'name':规格['displayName'],#展示名
        'auth':路由认证(规格,基),#解析后的认证
        'getModels':取模型,#本路由物化模型
        'stream':流,#委托流
        'streamSimple':简化流,#委托简化流
    }#复用后的提供方
    if 基址 is not None:#有端点才写 baseUrl，缺席则沿用目录提供方自己的端点
        提供方['baseUrl']=基址#有端点才带上，不把 None 写进提供方
    return 提供方#复用提供方

def 构建提供方(规格):
    """为一条已解析路由构建 pi-ai 提供方。规格为 dict。"""
    目录=目录提供方(规格['provider'])#已安装目录提供方；未运来为 None，下面走协议表
    if 目录 is not None and 'api' not in 规格:#已运来且没改协议，复用目录流实现，避免换一套线路
        return 复用目录提供方(目录,规格)#复用目录
    if 'api' not in 规格:#未运来又没点名协议
        工厂=None#没有工厂
    elif 规格['api'] not in 协议表:#点名了本构建没有的协议
        工厂=None#查不到
    else:#协议表认得
        工厂=协议表[规格['api']]#取出工厂
    if 工厂 is None:#点名了本构建没有的协议，或未运来又没点名，加载时失败
        协议名=规格['api'] if 'api' in 规格 else None#诊断用协议名
        raise 配置错误(
            'llm-pi-ai: provider "'+规格['provider']+'" names api "'+str(协议名)+'", which this build cannot serve;'
            +' supported protocols are '+', '.join(受支持协议()),
        )#无法服务
    构造={
        'id':规格['provider'],#路由键
        'name':规格['displayName'],#展示名
        'auth':路由认证(规格,目录),#解析后的认证；目录可能是 None
        'models':规格['models'],#已物化模型
        'api':工厂(),#惰性加载的协议实现
    }#从协议表构建
    if 'baseURL' in 规格 and 规格['baseURL'] is not None:#有端点才写进构造，缺席让 createProvider 用协议默认
        构造['baseUrl']=规格['baseURL']#有端点才带上，不把 None 传给 SDK
    return pi_ai.createProvider(构造)#建成提供方
