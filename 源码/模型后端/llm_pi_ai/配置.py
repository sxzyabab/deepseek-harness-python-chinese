"""pi-ai 适配器的配置模式与提供方配置校验。

对齐上游 `llm-pi-ai/src/config.ts`。公开面仅中文名；无英文别名。
"""
import math#有限数判断
from .. import llm#语言模型服务
from ...依赖.schemastery import 字符串字段,整数字段,列表字段,复合类型字段,常量字段,字典字段,布尔字段,枚举字段,自然数字段,数字字段#配置字段
from ...凭据.凭据 import 凭证引用#凭证引用工厂
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from .目录 import 模态列表,解析路由模型,受支持思考格式,思考档位列表#目录词表
from .提供方 import 构建提供方,受支持协议#提供方构建与受支持协议

__all__=(#仅中文公开名
    '默认流空闲超时毫秒','默认上下文窗口','默认最大输出','默认输入',
    '思考预算模式','兼容配置模式','推理力度模式','模型字段','模型配置模式','模型覆盖模式',
    '路由配置模式','配置模式','断言可服务','拒绝已删字段','解析配置表',
)#公开面结束

默认流空闲超时毫秒=300000#默认空闲超时
默认上下文窗口=262144#默认窗口
默认最大输出=32768#默认输出上限
默认输入=('text',)#默认仅文本

思考预算模式={
    'minimal':数字字段(),#最小
    'low':数字字段(),#低
    'medium':数字字段(),#中
    'high':数字字段(),#高
}#思考预算模式

兼容配置模式={
    'thinkingFormat':枚举字段(*list(受支持思考格式)),#思考格式
    'supportsReasoningEffort':布尔字段(),#是否支持力度
}#兼容配置模式

推理力度模式=枚举字段(*list(思考档位列表))#档位到线路拼写

模型字段={
    'name':字符串字段(),#展示名
    'contextWindow':整数字段(最小=1),#正整数窗口
    'maxTokens':整数字段(最小=1),#正整数上限
    'input':列表字段(枚举字段(*list(模态列表))),#模态列表
    'reasoningEfforts':复合类型字段(常量字段(False),推理力度模式),#力度映射或关掉
    'compat':兼容配置模式,#兼容配置
}#模型字段模式

模型配置模式={
    'id':字符串字段(可空=False),#必需id
    **模型字段,#共用字段
}#模型配置模式

模型覆盖模式=模型字段#覆盖模式，无id字段

路由配置模式={
    'apiKeyEnv':字符串字段(),#密钥引用
    'displayName':字符串字段(),#展示名
    #'api':枚举字段(*list(受支持协议())),#协议
    'baseURL':字符串字段(),#基址
    #'models':字典字段(模型配置模式),#模型列表
    #'modelOverrides':字典字段(模型覆盖模式),#按id覆盖
    'compat':兼容配置模式,#兼容配置
    'defaultContextWindow':整数字段(最小=1,默认值=默认上下文窗口),#默认窗口
    'defaultMaxTokens':整数字段(最小=1,默认值=默认最大输出),#默认上限
    'defaultInput':列表字段(枚举字段(*list(模态列表)),默认值=list(默认输入)),#默认模态
    #'headers':字典字段(字符串字段()),#头
    'reasoning':枚举字段(*list(思考档位列表)),#思考档位
    'thinkingBudgets':思考预算模式,#思考预算
    'cacheRetention':枚举字段('none','short','long'),#缓存保留
    'transport':枚举字段('sse','websocket','websocket-cached','auto'),#传输
    'timeoutMs':自然数字段(),#超时
    'websocketConnectTimeoutMs':自然数字段(),#WebSocket超时
    'streamIdleTimeoutMs':数字字段(最小=5e-324,最大=定时器延迟上限毫秒,默认值=默认流空闲超时毫秒),#空闲超时
    #'retryPolicy':llm.重试政策模式,#重试政策
}#路由配置模式

配置模式={
    #'providers':字典字段(路由配置模式,默认值={}),#路由字典，默认空
}#插件配置模式；中文名，无英文 Config 别名

def 断言可服务(配置):#拒绝本适配器无法服务的设置段
    """拒绝本适配器无法服务的设置段。"""
    解析配置表(配置.get('providers') if isinstance(配置,dict) else None)#解析即校验

def 拒绝已删字段(提供方,来源):#拒绝已删除的预发布配置字段
    """拒绝已删除的预发布配置字段并点名其替换。"""
    if 'provider' in 来源:#预发布曾把路由写在条目里，现已迁到 providers 字典键
        raise Exception('llm-pi-ai: provider "'+提供方+'" sets "provider", which moved to the providers dict key')#已迁到字典键
    if 'maxRetries' in 来源 or 'maxRetryDelayMs' in 来源:#旧重试字段已删除，应改用 dsh-llm-retry
        raise Exception(
            'llm-pi-ai: provider "'+提供方+'" sets maxRetries or maxRetryDelayMs, which were removed;'
            +' compose agent recovery with dsh-llm-retry',
        )#已删除

def 解析配置表(提供方们):#校验并拆离按路由键控的配置映射
    """校验配置并返回拆离的、按路由键控、适合按请求读取的映射。"""
    if isinstance(提供方们,list):#旧数组形态已废除，必须是按路由键控的字典
        raise Exception('llm-pi-ai: providers is now a dict keyed by provider route, not an array of profiles')#必须是字典
    条目们=list((提供方们 or {}).items())#路由条目，缺省空
    已校验={}#已校验结果
    for 提供方,来源 in 条目们:#逐条路由：先拒旧字段，再拆离并物化目录与提供方
        拒绝已删字段(提供方,来源)#拒绝旧字段
        if len(提供方)==0:#路由键不得空
            raise Exception('llm-pi-ai: provider names must be non-empty')#键不得空
        if 来源.get('baseURL') is not None and len(来源['baseURL'])==0:#写了基址就不能是空串
            raise Exception('llm-pi-ai: provider "'+提供方+'" has an empty baseURL')#基址非法
        if 来源.get('displayName') is not None and len(来源['displayName'])==0:#写了展示名就不能是空串
            raise Exception('llm-pi-ai: provider "'+提供方+'" has an empty displayName')#展示名非法
        空闲超时=来源['streamIdleTimeoutMs'] if 来源.get('streamIdleTimeoutMs') is not None else 默认流空闲超时毫秒#空闲超时或默认
        if (not math.isfinite(空闲超时)) or 空闲超时<=0 or 空闲超时>定时器延迟上限毫秒:#空闲超时必须正有限且不超过定时器上限
            raise Exception(
                'llm-pi-ai: provider "'+提供方+'" streamIdleTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒),
            )#空闲超时非法
        默认模态=list(来源['defaultInput'] if 来源.get('defaultInput') is not None else 默认输入)#拆离默认模态
        if len(默认模态)==0:#默认输入必须至少一种模态
            raise Exception('llm-pi-ai: provider "'+提供方+'" defaultInput must name at least one modality')#至少一种模态
        展示名=来源['displayName'] if 来源.get('displayName') is not None else 提供方#展示名或键
        目录请求={'provider':提供方,'defaultInput':默认模态}#路由目录请求
        目录请求['defaultContextWindow']=来源['defaultContextWindow'] if 来源.get('defaultContextWindow') is not None else 默认上下文窗口#默认窗口
        目录请求['defaultMaxTokens']=来源['defaultMaxTokens'] if 来源.get('defaultMaxTokens') is not None else 默认最大输出#默认上限
        if 来源.get('api') is not None:#有协议才交给目录物化，缺席则继承已安装目录
            目录请求['api']=来源['api']#有协议才带上
        if 来源.get('baseURL') is not None:#有基址才带上
            目录请求['baseURL']=来源['baseURL']#有基址才带上
        if 来源.get('models') is not None:#有 models 列表则整份替换目录
            目录请求['models']=来源['models']#有列表才带上
        if 来源.get('modelOverrides') is not None:#有按 id 覆盖才带上
            目录请求['modelOverrides']=来源['modelOverrides']#有覆盖才带上
        if 来源.get('compat') is not None:#有路由级兼容开关才带上
            目录请求['compat']=来源['compat']#有兼容才带上
        目录=解析路由模型(目录请求)#物化本路由模型
        其余=dict(来源)#拆出来源
        密钥引用=其余.pop('apiKeyEnv',None)#待品牌化引用
        其余.pop('retryPolicy',None)#待解析政策
        其余.pop('models',None)#已物化
        其余.pop('displayName',None)#已解析展示名
        已解析={**其余,'provider':提供方,'displayName':展示名,'streamIdleTimeoutMs':空闲超时}#已校验配置
        if 密钥引用 is not None:#有引用才品牌化；省略则交还 pi-ai 环境发现
            已解析['apiKeyEnv']=凭证引用(密钥引用)#有引用才品牌化
        已解析['retryPolicy']=llm.解析重试政策(来源.get('retryPolicy'),'llm-pi-ai: provider "'+提供方+'" retryPolicy')#解析政策
        if 其余.get('headers') is not None:#有部署头则拆离一份，避免与来源共享可变字典
            已解析['headers']=dict(其余['headers'])#拆离头
        if 其余.get('thinkingBudgets') is not None:#有思考预算则拆离一份
            已解析['thinkingBudgets']=dict(其余['thinkingBudgets'])#拆离预算
        已解析['configuredMaxTokens']=目录['configuredMaxTokens']#配置的按次上限
        提供方规格={'provider':提供方,'displayName':展示名,'models':目录['models'],'namesCredential':密钥引用 is not None}#提供方规格
        if 来源.get('api') is not None:#规格同样只在点名协议时带 api
            提供方规格['api']=来源['api']#有协议才带上
        if 来源.get('baseURL') is not None:#规格只在点名基址时带 baseURL
            提供方规格['baseURL']=来源['baseURL']#有基址才带上
        已解析['piProvider']=构建提供方(提供方规格)#建成提供方
        已校验[提供方]=已解析#写入
    return 已校验#已校验映射
