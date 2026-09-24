"""DeepSeek 插件配置与完整请求局部解析。"""
from math import isfinite as 是否有限
from urllib.parse import urlparse as 解析网址
from ...依赖.schemastery import 字符串字段,整数字段,列表字段,枚举字段,常量字段,数字字段,复合类型字段
from ...凭据.凭据 import 凭证引用
from ...工具.超时 import 定时器延迟上限毫秒
from ..llm import 解析重试政策
from .默认值 import (
    默认流空闲超时毫秒,默认上下文窗口,默认最大令牌,默认最大内联请求图字节,
    默认图片卸载字节量子,默认内联图片卸载字节量子,默认图片卸载张数量子,
    默认文件过期秒,默认文件刷新边距秒,默认文件配额清理批,默认文件接口超时毫秒,
)
from .模型目录 import 默认模型列表
from .请求定价 import 默认最大请求文件字节,默认每请求最大图片数,默认请求图最大字节

__all__=(
    '配置','公开基址','消息基址','解析适配器选项','深求配置错误','默认接口密钥环境','朴素选项',
)

默认接口密钥环境='DEEPSEEK_API_KEY'
最大安全整数=9007199254740991
最小正数=5e-324
模型模态=('text','image')
公开基址='https://api.deepseek.com/anthropic'
消息基址=公开基址
基址环境='DEEPSEEK_BASE_URL'

class 深求配置错误(Exception):
    """llm-deepseek 配置校验失败。"""

目录模型={
    'id':字符串字段(可空=False),
    'name':字符串字段(),
    'description':字符串字段(),
    'contextWindow':整数字段(最小=1),
    'maxTokens':整数字段(最小=1),
    'inputModalities':列表字段(枚举字段(常量字段('text'),常量字段('image')),默认值=['text']),
    'imagePixelBudget':复合类型字段(整数字段(最小=1),常量字段('low')),
    'imageMaxBytes':整数字段(最小=1),
    'systemPromptUpdate':常量字段('in-history'),
}
配置={
    'apiKeyEnv':字符串字段(默认值=默认接口密钥环境),
    'baseURL':字符串字段(),
    'thinking':枚举字段(常量字段('enabled'),常量字段('disabled')),
    'reasoningEffort':枚举字段(常量字段('off'),常量字段('low'),常量字段('high'),常量字段('max')),
    'maxTokens':整数字段(最小=1,最大=最大安全整数,默认值=默认最大令牌),
    'defaultContextWindow':整数字段(最小=1,默认值=默认上下文窗口),
    'models':列表字段(目录模型),
    'streamIdleTimeoutMs':数字字段(最小=最小正数,最大=定时器延迟上限毫秒,默认值=默认流空闲超时毫秒),
    'maxRequestFilesBytes':整数字段(最小=1,默认值=默认最大请求文件字节),
    'maxInlineRequestImageBytes':整数字段(最小=1,默认值=默认最大内联请求图字节),
    'maxImagesPerRequest':整数字段(最小=1,默认值=默认每请求最大图片数),
    'imageOffloadByteQuantum':整数字段(最小=1,默认值=默认图片卸载字节量子),
    'inlineImageOffloadByteQuantum':整数字段(最小=1,默认值=默认内联图片卸载字节量子),
    'imageOffloadCountQuantum':整数字段(最小=1,默认值=默认图片卸载张数量子),
    'filesApiTimeoutMs':数字字段(最小=最小正数,最大=定时器延迟上限毫秒,默认值=默认文件接口超时毫秒),
    'fileExpiresAfterSeconds':整数字段(最小=3600,最大=2592000,默认值=默认文件过期秒),
    'fileRefreshMarginSeconds':整数字段(最小=0,默认值=默认文件刷新边距秒),
    'fileQuotaCleanupBatch':整数字段(最小=1,最大=1000,默认值=默认文件配额清理批),
    'retryPolicy':'重试政策模式',
}

def 朴素选项(配置值):
    """读出已校验配置后面的当前值。"""
    结果={}
    for 键,值 in 配置值.items():
        if hasattr(值,'get') and callable(值.get):
            结果[键]=值.get()
        else:
            结果[键]=值
    return 结果

def 是否正整数(值):
    """排除 bool 的正整数。"""
    return not isinstance(值,bool) and isinstance(值,(int,float)) and 值==int(值) and 值>0

def 是否正安全整数(值):
    """排除 bool 的正安全整数。"""
    return 是否正整数(值) and abs(值)<=最大安全整数

def 解析模型目录(模型列表):
    """解析、校验并拆离建议模型目录。"""
    已见=set()
    结果=[]
    for 模型 in (模型列表 if 模型列表 is not None else 默认模型列表):
        if 'imageDetail' in 模型:
            raise 深求配置错误('llm-deepseek: catalog model imageDetail is no longer supported; use imagePixelBudget')
        if len(模型['id'])==0:
            raise 深求配置错误('llm-deepseek: catalog model ids must be non-empty')
        if 'name' in 模型 and 模型['name'] is not None and len(模型['name'])==0:
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" has an empty name')
        if 'contextWindow' in 模型 and not 是否正整数(模型['contextWindow']):
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" contextWindow must be a positive integer')
        if 'maxTokens' in 模型 and not 是否正整数(模型['maxTokens']):
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" maxTokens must be a positive integer')
        模态=模型['inputModalities'] if 'inputModalities' in 模型 and 模型['inputModalities'] is not None else ['text']
        if len(模态)==0:
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" inputModalities must not be empty')
        for 项 in 模态:
            if 项 not in 模型模态:
                raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" inputModalities must contain only "text" and "image"')
        if len(set(模态))!=len(模态):
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" inputModalities must not contain duplicates')
        有图='image' in 模态
        if not 有图 and (('imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None) or ('imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None)):
            raise 深求配置错误('llm-deepseek: text-only catalog model "'+模型['id']+'" cannot declare image request limits')
        if 'imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None and 模型['imagePixelBudget']!='low' and not 是否正安全整数(模型['imagePixelBudget']):
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" imagePixelBudget must be "low" or a positive safe integer')
        if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None and not 是否正安全整数(模型['imageMaxBytes']):
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" imageMaxBytes must be a positive safe integer')
        更新模式=模型['systemPromptUpdate'] if 'systemPromptUpdate' in 模型 else None
        if 更新模式 is not None and 更新模式!='in-history':
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" systemPromptUpdate must be "in-history" when present')
        if 模型['id'] in 已见:
            raise 深求配置错误('llm-deepseek: duplicate catalog model "'+模型['id']+'"')
        已见.add(模型['id'])
        条目={'id':模型['id'],'inputModalities':list(模态)}
        if 'name' in 模型:
            条目['name']=模型['name']
        if 'description' in 模型:
            条目['description']=模型['description']
        if 'contextWindow' in 模型:
            条目['contextWindow']=模型['contextWindow']
        if 'maxTokens' in 模型:
            条目['maxTokens']=模型['maxTokens']
        if 更新模式 is not None:
            条目['systemPromptUpdate']=更新模式
        if 有图:
            if 'imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None:
                条目['imagePixelBudget']=模型['imagePixelBudget']
            条目['imageMaxBytes']=模型['imageMaxBytes'] if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None else 默认请求图最大字节
        结果.append(条目)
    return 结果

def 解析适配器选项(原始配置,环境=None):
    """从原始配置到已校验连接事实的那一次显式解析步骤。"""
    if 'protocol' in 原始配置:
        raise 深求配置错误('llm-deepseek: protocol is not configurable; remove it and use a Messages-compatible baseURL')
    思考=原始配置['thinking'] if 'thinking' in 原始配置 else None
    力度=原始配置['reasoningEffort'] if 'reasoningEffort' in 原始配置 else None
    if 思考=='disabled' and 力度 is not None and 力度!='off':
        raise 深求配置错误('llm-deepseek: only reasoningEffort "off" can be configured when thinking is disabled')
    if 'defaultContextWindow' in 原始配置 and not 是否正整数(原始配置['defaultContextWindow']):
        raise 深求配置错误('llm-deepseek: defaultContextWindow must be a positive integer')
    if 'maxTokens' in 原始配置 and not 是否正安全整数(原始配置['maxTokens']):
        raise 深求配置错误('llm-deepseek: maxTokens must be a positive safe integer')
    空闲超时=原始配置['streamIdleTimeoutMs'] if 'streamIdleTimeoutMs' in 原始配置 else 默认流空闲超时毫秒
    if not 是否有限(空闲超时) or 空闲超时<=0 or 空闲超时>定时器延迟上限毫秒:
        raise 深求配置错误('llm-deepseek: streamIdleTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))
    请求文件字节=原始配置['maxRequestFilesBytes'] if 'maxRequestFilesBytes' in 原始配置 else 默认最大请求文件字节
    if not 是否正安全整数(请求文件字节):
        raise 深求配置错误('llm-deepseek: maxRequestFilesBytes must be a positive safe integer')
    内联图字节=原始配置['maxInlineRequestImageBytes'] if 'maxInlineRequestImageBytes' in 原始配置 else 默认最大内联请求图字节
    if not 是否正安全整数(内联图字节):
        raise 深求配置错误('llm-deepseek: maxInlineRequestImageBytes must be a positive safe integer')
    每请求张数=原始配置['maxImagesPerRequest'] if 'maxImagesPerRequest' in 原始配置 else 默认每请求最大图片数
    if not 是否正安全整数(每请求张数):
        raise 深求配置错误('llm-deepseek: maxImagesPerRequest must be a positive safe integer')
    卸载字节量子=原始配置['imageOffloadByteQuantum'] if 'imageOffloadByteQuantum' in 原始配置 else 默认图片卸载字节量子
    if not 是否正安全整数(卸载字节量子):
        raise 深求配置错误('llm-deepseek: imageOffloadByteQuantum must be a positive safe integer')
    if 卸载字节量子>请求文件字节:
        raise 深求配置错误('llm-deepseek: imageOffloadByteQuantum must not exceed maxRequestFilesBytes')
    内联卸载字节量子=原始配置['inlineImageOffloadByteQuantum'] if 'inlineImageOffloadByteQuantum' in 原始配置 else 默认内联图片卸载字节量子
    if not 是否正安全整数(内联卸载字节量子):
        raise 深求配置错误('llm-deepseek: inlineImageOffloadByteQuantum must be a positive safe integer')
    if 内联卸载字节量子>内联图字节:
        raise 深求配置错误('llm-deepseek: inlineImageOffloadByteQuantum must not exceed maxInlineRequestImageBytes')
    卸载张数量子=原始配置['imageOffloadCountQuantum'] if 'imageOffloadCountQuantum' in 原始配置 else 默认图片卸载张数量子
    if not 是否正安全整数(卸载张数量子):
        raise 深求配置错误('llm-deepseek: imageOffloadCountQuantum must be a positive safe integer')
    if 卸载张数量子>每请求张数:
        raise 深求配置错误('llm-deepseek: imageOffloadCountQuantum must not exceed maxImagesPerRequest')
    文件超时=原始配置['filesApiTimeoutMs'] if 'filesApiTimeoutMs' in 原始配置 else 默认文件接口超时毫秒
    if not 是否有限(文件超时) or 文件超时<=0 or 文件超时>定时器延迟上限毫秒:
        raise 深求配置错误('llm-deepseek: filesApiTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))
    过期秒=原始配置['fileExpiresAfterSeconds'] if 'fileExpiresAfterSeconds' in 原始配置 else 默认文件过期秒
    if not 是否正安全整数(过期秒) or 过期秒<3600 or 过期秒>2592000:
        raise 深求配置错误('llm-deepseek: fileExpiresAfterSeconds must be an integer from 3600 through 2592000')
    刷新边距=原始配置['fileRefreshMarginSeconds'] if 'fileRefreshMarginSeconds' in 原始配置 else 默认文件刷新边距秒
    if isinstance(刷新边距,bool) or not isinstance(刷新边距,(int,float)) or 刷新边距!=int(刷新边距) or 刷新边距<0 or 刷新边距>=过期秒:
        raise 深求配置错误('llm-deepseek: fileRefreshMarginSeconds must be a non-negative integer below fileExpiresAfterSeconds')
    清理批=原始配置['fileQuotaCleanupBatch'] if 'fileQuotaCleanupBatch' in 原始配置 else 默认文件配额清理批
    if not 是否正安全整数(清理批) or 清理批>1000:
        raise 深求配置错误('llm-deepseek: fileQuotaCleanupBatch must be an integer from 1 through 1000')
    if 'baseURL' in 原始配置 and 原始配置['baseURL'] is not None:
        基址=原始配置['baseURL']
    else:
        环境项=环境.取(基址环境) if 环境 is not None else None
        if 环境项 is not None:
            基址=环境项['value']
        else:
            基址=公开基址
    解析=解析网址(基址)
    if 解析.scheme not in ('http','https') or 解析.username or 解析.password or 解析.query or 解析.fragment:
        raise 深求配置错误('llm-deepseek: Messages baseURL must be an HTTP(S) root without credentials, query, or fragment')
    return {
        'apiKeyEnv':凭证引用(原始配置['apiKeyEnv'] if 'apiKeyEnv' in 原始配置 else 默认接口密钥环境),
        'baseURL':基址,
        'defaults':{
            'thinking':思考,
            'reasoningEffort':力度,
        },
        'maxTokens':原始配置['maxTokens'] if 'maxTokens' in 原始配置 else 默认最大令牌,
        'defaultContextWindow':原始配置['defaultContextWindow'] if 'defaultContextWindow' in 原始配置 else 默认上下文窗口,
        'models':解析模型目录(原始配置['models'] if 'models' in 原始配置 else None),
        'streamIdleTimeoutMs':空闲超时,
        'maxRequestFilesBytes':请求文件字节,
        'maxInlineRequestImageBytes':内联图字节,
        'maxImagesPerRequest':每请求张数,
        'imageOffloadByteQuantum':卸载字节量子,
        'inlineImageOffloadByteQuantum':内联卸载字节量子,
        'imageOffloadCountQuantum':卸载张数量子,
        'filesApiTimeoutMs':文件超时,
        'filePolicy':{
            'expiresAfterSeconds':过期秒,
            'refreshMarginSeconds':刷新边距,
            'quotaCleanupBatch':清理批,
        },
        'retryPolicy':解析重试政策(原始配置['retryPolicy'] if 'retryPolicy' in 原始配置 else None,'llm-deepseek: retryPolicy'),
    }
