"""pi-ai 适配器的配置模式与提供方配置校验。

公开面仅中文名；无英文别名。
"""
import math#有限数判断
from .. import llm#语言模型服务
from ...依赖.schemastery import 字符串字段,整数字段,列表字段,复合类型字段,常量字段,字典字段,布尔字段,枚举字段,自然数字段,数字字段#配置字段
from ...凭据.凭据 import 凭证引用#凭证引用工厂
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from .目录 import 模态列表,解析路由模型,受支持思考格式,思考档位列表,配置错误,目录错误#目录词表与本包异常
from .提供方 import 构建提供方,受支持协议#提供方构建与受支持协议
from ...配置.配置 import json深度相等#深等比较

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

def 断言可服务(配置,先前=None):#拒绝新增或变更且无法服务的设置段
    """拒绝新增或变更且无法服务的提供方配置。未变的已存配置不阻塞编辑另一提供方。"""
    提供方表=配置['providers'] if 'providers' in 配置 else {}#当前
    先前表=(先前['providers'] if 先前 is not None and 'providers' in 先前 else {}) if 先前 is not None else {}#先前
    变更={}#仅变更
    for 提供方,配置项 in 提供方表.items():#筛变更
        旧=先前表[提供方] if 提供方 in 先前表 else None#旧值
        if not json深度相等(配置项,旧):#有变
            变更[提供方]=配置项#记下
    解析配置表(变更)#严格解析变更集

def 拒绝已删字段(提供方,来源):#拒绝已删除的预发布配置字段
    """拒绝已删除的预发布配置字段并点名其替换。来源为单条路由 dict。"""
    if 'provider' in 来源:#预发布曾把路由写在条目里，现已迁到 providers 字典键
        raise 配置错误('llm-pi-ai: provider "'+提供方+'" sets "provider", which moved to the providers dict key')#已迁到字典键
    if 'maxRetries' in 来源 or 'maxRetryDelayMs' in 来源:#旧重试字段已删除，应改用 dsh-llm-retry
        raise 配置错误(
            'llm-pi-ai: provider "'+提供方+'" sets maxRetries or maxRetryDelayMs, which were removed;'
            +' compose agent recovery with dsh-llm-retry',
        )#已删除

def 解析配置表(提供方表,校验='strict'):#校验并拆离按路由键控的配置映射
    """解析标量默认并物化每路由可服务模型。校验为 strict 或 deferred。"""
    if isinstance(提供方表,list):#旧数组形态已废除，必须是按路由键控的字典
        raise 配置错误('llm-pi-ai: providers is now a dict keyed by provider route, not an array of profiles')#必须是字典
    if 提供方表 is None:#缺席当空表；空 dict 仍按空表迭代，不走 or 以免与 JS 真值分叉
        条目列表=[]#没有路由
    else:#已给字典
        条目列表=list(提供方表.items())#路由条目
    已校验={}#已校验结果
    for 提供方,来源 in 条目列表:#逐条路由：先拒旧字段，再拆离并物化目录与提供方
        拒绝已删字段(提供方,来源)#拒绝旧字段
        if len(提供方)==0:#路由键不得空
            raise 配置错误('llm-pi-ai: provider names must be non-empty')#键不得空
        if 'baseURL' in 来源 and 来源['baseURL'] is not None and len(来源['baseURL'])==0:#写了基址就不能是空串；?? 不吞缺席
            raise 配置错误('llm-pi-ai: provider "'+提供方+'" has an empty baseURL')#基址非法
        if 'displayName' in 来源 and 来源['displayName'] is not None and len(来源['displayName'])==0:#写了展示名就不能是空串
            raise 配置错误('llm-pi-ai: provider "'+提供方+'" has an empty displayName')#展示名非法
        if 'streamIdleTimeoutMs' in 来源 and 来源['streamIdleTimeoutMs'] is not None:#??：显式 0 不得被默认值吞掉，交给下面校验拒绝
            空闲超时=来源['streamIdleTimeoutMs']#配置超时
        else:#缺席用默认
            空闲超时=默认流空闲超时毫秒#空闲超时或默认
        if (not math.isfinite(空闲超时)) or 空闲超时<=0 or 空闲超时>定时器延迟上限毫秒:#空闲超时必须正有限且不超过定时器上限
            raise 配置错误(
                'llm-pi-ai: provider "'+提供方+'" streamIdleTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒),
            )#空闲超时非法
        if 'defaultInput' in 来源 and 来源['defaultInput'] is not None:#??：空列表不得被默认模态吞掉，交给下面校验拒绝
            默认模态=list(来源['defaultInput'])#拆离默认模态
        else:#缺席用默认
            默认模态=list(默认输入)#默认仅文本
        if len(默认模态)==0:#默认输入必须至少一种模态
            raise 配置错误('llm-pi-ai: provider "'+提供方+'" defaultInput must name at least one modality')#至少一种模态
        if 'displayName' in 来源 and 来源['displayName'] is not None:#??：空串已在上面拒绝，这里只处理缺席
            展示名=来源['displayName']#展示名
        else:#缺席落到路由键
            展示名=提供方#展示名或键
        目录请求={'provider':提供方,'defaultInput':默认模态}#路由目录请求
        if 'defaultContextWindow' in 来源 and 来源['defaultContextWindow'] is not None:#??：显式 0 交给目录正整数校验
            目录请求['defaultContextWindow']=来源['defaultContextWindow']#配置窗口
        else:#缺席用默认
            目录请求['defaultContextWindow']=默认上下文窗口#默认窗口
        if 'defaultMaxTokens' in 来源 and 来源['defaultMaxTokens'] is not None:#??：显式 0 交给目录正整数校验，不得 or 成默认
            目录请求['defaultMaxTokens']=来源['defaultMaxTokens']#配置上限
        else:#缺席用默认
            目录请求['defaultMaxTokens']=默认最大输出#默认上限
        if 'api' in 来源 and 来源['api'] is not None:#有协议才交给目录物化，缺席则继承已安装目录
            目录请求['api']=来源['api']#有协议才带上
        if 'baseURL' in 来源 and 来源['baseURL'] is not None:#有基址才带上
            目录请求['baseURL']=来源['baseURL']#有基址才带上
        if 'models' in 来源 and 来源['models'] is not None:#有 models 列表则整份替换目录
            目录请求['models']=来源['models']#有列表才带上
        if 'modelOverrides' in 来源 and 来源['modelOverrides'] is not None:#有按 id 覆盖才带上
            目录请求['modelOverrides']=来源['modelOverrides']#有覆盖才带上
        if 'compat' in 来源 and 来源['compat'] is not None:#有路由级兼容开关才带上
            目录请求['compat']=来源['compat']#有兼容才带上
        目录=None#可选目录
        派爱提供方=None#可选提供者
        目录错误文=None#可选诊断
        try:#物化目录与提供方
            目录=解析路由模型(目录请求,校验)#物化本路由模型
            if len(目录['modelErrors'])>0:#有模型诊断
                目录错误文=next(iter(目录['modelErrors'].values()))#首个
            提供方规格={'provider':提供方,'displayName':展示名,'models':目录['models'],'namesCredential':('apiKeyEnv' in 来源 and 来源['apiKeyEnv'] is not None)}#提供方规格
            if 'api' in 来源 and 来源['api'] is not None:#规格同样只在点名协议时带 api
                提供方规格['api']=来源['api']#有协议才带上
            if 'baseURL' in 来源 and 来源['baseURL'] is not None:#规格只在点名基址时带 baseURL
                提供方规格['baseURL']=来源['baseURL']#有基址才带上
            派爱提供方=构建提供方(提供方规格)#建成提供方
        except 目录错误 as 错误:#目录失败
            if 校验=='strict':#严格
                raise 错误#抛出
            目录错误文=str(错误) if 目录错误文 is None else 目录错误文#收住
        其余=dict(来源)#拆出来源
        密钥引用=其余.pop('apiKeyEnv',None)#待品牌化引用
        其余.pop('retryPolicy',None)#待解析政策
        其余.pop('models',None)#已物化
        其余.pop('displayName',None)#已解析展示名
        已解析={**其余,'provider':提供方,'displayName':展示名,'streamIdleTimeoutMs':空闲超时}#已校验配置
        if 密钥引用 is not None:#有引用才品牌化；省略则交还 pi-ai 环境发现
            已解析['apiKeyEnv']=凭证引用(密钥引用)#有引用才品牌化
        if 'retryPolicy' in 来源:#点名了政策才传入；缺席让解析器走默认
            已解析['retryPolicy']=llm.解析重试政策(来源['retryPolicy'],'llm-pi-ai: provider "'+提供方+'" retryPolicy')#解析政策
        else:#缺席
            已解析['retryPolicy']=llm.解析重试政策(None,'llm-pi-ai: provider "'+提供方+'" retryPolicy')#解析缺席政策
        if 'headers' in 其余 and 其余['headers'] is not None:#有部署头则拆离一份，避免与来源共享可变字典
            已解析['headers']=dict(其余['headers'])#拆离头
        if 'thinkingBudgets' in 其余 and 其余['thinkingBudgets'] is not None:#有思考预算则拆离一份
            已解析['thinkingBudgets']=dict(其余['thinkingBudgets'])#拆离预算
        已解析['configuredMaxTokens']=目录['configuredMaxTokens'] if 目录 is not None else {}#配置的按次上限
        已解析['modelErrors']=目录['modelErrors'] if 目录 is not None else {}#模型错误
        if 派爱提供方 is not None:#可服务
            已解析['piProvider']=派爱提供方#建成提供方
        if 目录错误文 is not None:#有诊断
            已解析['catalogError']=目录错误文#目录错误
        已校验[提供方]=已解析#写入
    return 已校验#已校验映射
