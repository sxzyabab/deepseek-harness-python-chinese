"""DeepSeek 插件配置与完整请求局部解析。"""
from math import isfinite as 是否有限#有限数判断
from urllib.parse import urlparse as 解析网址
from ...依赖.schemastery import 字符串字段,整数字段,列表字段,枚举字段,常量字段,数字字段#配置字段
from ...凭据.凭据 import 凭证引用#凭证引用工厂
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from ..llm import 解析重试政策#政策解析
from .协议无关.默认值 import (
    默认流空闲超时毫秒,默认上下文窗口,默认最大令牌,默认最大内联请求图字节,
    默认图片卸载字节量子,默认内联图片卸载字节量子,默认图片卸载张数量子,
    默认文件过期秒,默认文件刷新边距秒,默认文件配额清理批,默认文件接口超时毫秒,
)#默认值
from .协议无关.模型目录 import 默认模型列表#默认目录
from .协议无关.请求定价 import 默认最大请求文件字节,默认每请求最大图片数,默认请求图最大字节#请求图默认
from .协议无关.类型 import 深求协议表#协议名

__all__=(#仅中文公开名
    '配置','公开基址','消息基址','解析适配器选项','深求配置错误',
    '默认接口密钥环境',
)#公开面结束

默认接口密钥环境='DEEPSEEK_API_KEY'#默认密钥环境变量
最大安全整数=9007199254740991#Number.MAX_SAFE_INTEGER
最小正数=5e-324#Number.MIN_VALUE
模型模态=('text','image')#目录允许的模态
公开基址='https://api.deepseek.com'#公开 API 默认
消息基址='https://api.deepseek.com/anthropic'#官方消息协议根
基址环境='DEEPSEEK_BASE_URL'#基址环境变量

class 深求配置错误(Exception):
    """llm-deepseek 配置校验失败。"""

目录模型={
    'id':字符串字段(可空=False),#必需id
    'name':字符串字段(),#可选名
    'description':字符串字段(),#可选描述
    'contextWindow':整数字段(最小=1),#正整数窗口
    'maxTokens':整数字段(最小=1),#正整数上限
}#目录条目模式
配置={
    'protocol':枚举字段(常量字段('chat-completions'),常量字段('messages')),#线路协议，默认 messages
    'apiKeyEnv':字符串字段(默认值=默认接口密钥环境),#密钥引用
    'baseURL':字符串字段(),#基址
    'thinking':枚举字段(常量字段('enabled'),常量字段('disabled')),#思考开关
    'reasoningEffort':枚举字段(常量字段('off'),常量字段('low'),常量字段('high'),常量字段('max')),#力度
    'maxTokens':整数字段(最小=1,最大=最大安全整数,默认值=默认最大令牌),#输出上限
    'defaultContextWindow':整数字段(最小=1,默认值=默认上下文窗口),#默认窗口
    'models':列表字段(目录模型),#建议目录
    'streamIdleTimeoutMs':数字字段(最小=最小正数,最大=定时器延迟上限毫秒,默认值=默认流空闲超时毫秒),#空闲超时
    'maxRequestFilesBytes':整数字段(最小=1,默认值=默认最大请求文件字节),#请求文件字节
    'maxInlineRequestImageBytes':整数字段(最小=1,默认值=默认最大内联请求图字节),#内联图字节
    'maxImagesPerRequest':整数字段(最小=1,默认值=默认每请求最大图片数),#每请求张数
    'imageOffloadByteQuantum':整数字段(最小=1,默认值=默认图片卸载字节量子),#卸载字节量子
    'inlineImageOffloadByteQuantum':整数字段(最小=1,默认值=默认内联图片卸载字节量子),#内联卸载字节量子
    'imageOffloadCountQuantum':整数字段(最小=1,默认值=默认图片卸载张数量子),#卸载张数量子
    'filesApiTimeoutMs':数字字段(最小=最小正数,最大=定时器延迟上限毫秒,默认值=默认文件接口超时毫秒),#Files 超时
    'fileExpiresAfterSeconds':整数字段(最小=3600,最大=2592000,默认值=默认文件过期秒),#文件过期
    'fileRefreshMarginSeconds':整数字段(最小=0,默认值=默认文件刷新边距秒),#刷新边距
    'fileQuotaCleanupBatch':整数字段(最小=1,最大=1000,默认值=默认文件配额清理批),#清理批
    'retryPolicy':'重试政策模式',#重试政策
}#配置运行时模式

def 是否正整数(值):#入口正整数
    """排除 bool 的正整数。"""
    return not isinstance(值,bool) and isinstance(值,(int,float)) and 值==int(值) and 值>0#正整数

def 是否正安全整数(值):#入口正安全整数
    """排除 bool 的正安全整数。"""
    return 是否正整数(值) and abs(值)<=最大安全整数#正安全

def 解析模型目录(模型列表):#解析建议目录
    """解析、校验并拆离建议模型目录。条目为 dict。"""
    已见=set()#已见id
    结果=[]#拆离后的目录
    for 模型 in (模型列表 if 模型列表 is not None else 默认模型列表):#逐条
        if 'imageDetail' in 模型:#旧字段
            raise 深求配置错误('llm-deepseek: catalog model imageDetail is no longer supported; use imagePixelBudget')#旧字段
        if len(模型['id'])==0:#id空
            raise 深求配置错误('llm-deepseek: catalog model ids must be non-empty')#id不得空
        if 'name' in 模型 and 模型['name'] is not None and len(模型['name'])==0:#名给了但是空
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" has an empty name')#名非法
        if 'contextWindow' in 模型 and not 是否正整数(模型['contextWindow']):#窗口非法
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" contextWindow must be a positive integer')#窗口非法
        if 'maxTokens' in 模型 and not 是否正整数(模型['maxTokens']):#上限非法
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" maxTokens must be a positive integer')#上限非法
        模态=模型['inputModalities'] if 'inputModalities' in 模型 and 模型['inputModalities'] is not None else ['text']#模态
        if len(模态)==0:#空
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" inputModalities must not be empty')#不得空
        for 项 in 模态:#逐项
            if 项 not in 模型模态:#非法
                raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" inputModalities must contain only "text" and "image"')#非法
        if len(set(模态))!=len(模态):#重复
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" inputModalities must not contain duplicates')#重复
        有图='image' in 模态#是否视觉
        if not 有图 and (('imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None) or ('imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None)):#纯文本却带图限制
            raise 深求配置错误('llm-deepseek: text-only catalog model "'+模型['id']+'" cannot declare image request limits')#非法
        if 'imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None and 模型['imagePixelBudget']!='low' and not 是否正安全整数(模型['imagePixelBudget']):#像素预算非法
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" imagePixelBudget must be "low" or a positive safe integer')#非法
        if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None and not 是否正安全整数(模型['imageMaxBytes']):#字节非法
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" imageMaxBytes must be a positive safe integer')#非法
        更新模式=模型['systemPromptUpdate'] if 'systemPromptUpdate' in 模型 else None#可选系统提示词更新
        if 更新模式 is not None and 更新模式!='in-history':#非法模式
            raise 深求配置错误('llm-deepseek: catalog model "'+模型['id']+'" systemPromptUpdate must be "in-history" when present')#更新模式非法
        if 模型['id'] in 已见:#id重复
            raise 深求配置错误('llm-deepseek: duplicate catalog model "'+模型['id']+'"')#id重复
        已见.add(模型['id'])#记下已见
        条目={'id':模型['id'],'inputModalities':list(模态)}#拆离条目
        if 'name' in 模型:#有名
            条目['name']=模型['name']#有名才带上
        if 'description' in 模型:#有描述
            条目['description']=模型['description']#有描述才带上
        if 'contextWindow' in 模型:#有窗口
            条目['contextWindow']=模型['contextWindow']#有窗口才带上
        if 'maxTokens' in 模型:#有上限
            条目['maxTokens']=模型['maxTokens']#有上限才带上
        if 更新模式 is not None:#有更新模式
            条目['systemPromptUpdate']=更新模式#有更新模式才带上
        if 有图:#视觉
            if 'imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None:#有像素预算
                条目['imagePixelBudget']=模型['imagePixelBudget']#带上
            条目['imageMaxBytes']=模型['imageMaxBytes'] if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None else 默认请求图最大字节#默认字节
        结果.append(条目)#收下
    return 结果#已校验目录

def 解析适配器选项(原始配置,环境=None):#解析连接事实
    """从原始配置到已校验连接事实的那一次显式解析步骤。配置为 dict。"""
    协议=原始配置['protocol'] if 'protocol' in 原始配置 and 原始配置['protocol'] is not None else 'messages'#默认消息
    if 协议 not in 深求协议表:#非法
        raise 深求配置错误('llm-deepseek: protocol must be chat-completions or messages')#非法协议
    思考=原始配置['thinking'] if 'thinking' in 原始配置 else None#思考开关
    力度=原始配置['reasoningEffort'] if 'reasoningEffort' in 原始配置 else None#力度
    if 思考=='disabled' and 力度 is not None and 力度!='off':#禁用思考却给了非off力度
        raise 深求配置错误('llm-deepseek: only reasoningEffort "off" can be configured when thinking is disabled')#禁用思考时只能off
    if 'defaultContextWindow' in 原始配置 and not 是否正整数(原始配置['defaultContextWindow']):#窗口非法
        raise 深求配置错误('llm-deepseek: defaultContextWindow must be a positive integer')#窗口非法
    if 'maxTokens' in 原始配置 and not 是否正安全整数(原始配置['maxTokens']):#上限非法
        raise 深求配置错误('llm-deepseek: maxTokens must be a positive safe integer')#上限非法
    空闲超时=原始配置['streamIdleTimeoutMs'] if 'streamIdleTimeoutMs' in 原始配置 else 默认流空闲超时毫秒#空闲超时或默认
    if not 是否有限(空闲超时) or 空闲超时<=0 or 空闲超时>定时器延迟上限毫秒:#空闲超时非法
        raise 深求配置错误('llm-deepseek: streamIdleTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#空闲超时非法
    请求文件字节=原始配置['maxRequestFilesBytes'] if 'maxRequestFilesBytes' in 原始配置 else 默认最大请求文件字节#文件字节
    if not 是否正安全整数(请求文件字节):#非法
        raise 深求配置错误('llm-deepseek: maxRequestFilesBytes must be a positive safe integer')#非法
    内联图字节=原始配置['maxInlineRequestImageBytes'] if 'maxInlineRequestImageBytes' in 原始配置 else 默认最大内联请求图字节#内联
    if not 是否正安全整数(内联图字节):#非法
        raise 深求配置错误('llm-deepseek: maxInlineRequestImageBytes must be a positive safe integer')#非法
    每请求张数=原始配置['maxImagesPerRequest'] if 'maxImagesPerRequest' in 原始配置 else 默认每请求最大图片数#张数
    if not 是否正安全整数(每请求张数):#非法
        raise 深求配置错误('llm-deepseek: maxImagesPerRequest must be a positive safe integer')#非法
    卸载字节量子=原始配置['imageOffloadByteQuantum'] if 'imageOffloadByteQuantum' in 原始配置 else 默认图片卸载字节量子#量子
    if not 是否正安全整数(卸载字节量子):#非法
        raise 深求配置错误('llm-deepseek: imageOffloadByteQuantum must be a positive safe integer')#非法
    if 卸载字节量子>请求文件字节:#超上限
        raise 深求配置错误('llm-deepseek: imageOffloadByteQuantum must not exceed maxRequestFilesBytes')#超上限
    内联卸载字节量子=原始配置['inlineImageOffloadByteQuantum'] if 'inlineImageOffloadByteQuantum' in 原始配置 else 默认内联图片卸载字节量子#内联量子
    if not 是否正安全整数(内联卸载字节量子):#非法
        raise 深求配置错误('llm-deepseek: inlineImageOffloadByteQuantum must be a positive safe integer')#非法
    if 内联卸载字节量子>内联图字节:#超上限
        raise 深求配置错误('llm-deepseek: inlineImageOffloadByteQuantum must not exceed maxInlineRequestImageBytes')#超上限
    卸载张数量子=原始配置['imageOffloadCountQuantum'] if 'imageOffloadCountQuantum' in 原始配置 else 默认图片卸载张数量子#张数量子
    if not 是否正安全整数(卸载张数量子):#非法
        raise 深求配置错误('llm-deepseek: imageOffloadCountQuantum must be a positive safe integer')#非法
    if 卸载张数量子>每请求张数:#超上限
        raise 深求配置错误('llm-deepseek: imageOffloadCountQuantum must not exceed maxImagesPerRequest')#超上限
    文件超时=原始配置['filesApiTimeoutMs'] if 'filesApiTimeoutMs' in 原始配置 else 默认文件接口超时毫秒#Files 超时
    if not 是否有限(文件超时) or 文件超时<=0 or 文件超时>定时器延迟上限毫秒:#非法
        raise 深求配置错误('llm-deepseek: filesApiTimeoutMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#非法
    过期秒=原始配置['fileExpiresAfterSeconds'] if 'fileExpiresAfterSeconds' in 原始配置 else 默认文件过期秒#过期
    if not 是否正安全整数(过期秒) or 过期秒<3600 or 过期秒>2592000:#非法
        raise 深求配置错误('llm-deepseek: fileExpiresAfterSeconds must be an integer from 3600 through 2592000')#非法
    刷新边距=原始配置['fileRefreshMarginSeconds'] if 'fileRefreshMarginSeconds' in 原始配置 else 默认文件刷新边距秒#边距
    if isinstance(刷新边距,bool) or not isinstance(刷新边距,(int,float)) or 刷新边距!=int(刷新边距) or 刷新边距<0 or 刷新边距>=过期秒:#非法
        raise 深求配置错误('llm-deepseek: fileRefreshMarginSeconds must be a non-negative integer below fileExpiresAfterSeconds')#非法
    清理批=原始配置['fileQuotaCleanupBatch'] if 'fileQuotaCleanupBatch' in 原始配置 else 默认文件配额清理批#清理批
    if not 是否正安全整数(清理批) or 清理批>1000:#非法
        raise 深求配置错误('llm-deepseek: fileQuotaCleanupBatch must be an integer from 1 through 1000')#非法
    if 'baseURL' in 原始配置 and 原始配置['baseURL'] is not None:#配置基址
        基址=原始配置['baseURL']#配置基址
    else:#回落环境或公开
        环境项=环境.取(基址环境) if 环境 is not None else None#受信环境
        if 环境项 is not None:#有环境项
            基址=环境项['value']#环境基址
        else:#按协议默认
            基址=消息基址 if 协议=='messages' else 公开基址#协议默认
    if 协议=='messages':#消息根约束
            解析=解析网址(基址)
        if 解析.scheme not in ('http','https') or 解析.username or 解析.password or 解析.query or 解析.fragment:#非法
            raise 深求配置错误('llm-deepseek: Messages baseURL must be an HTTP(S) root without credentials, query, or fragment')#非法根
    return {
        'protocol':协议,#协议
        'apiKeyEnv':凭证引用(原始配置['apiKeyEnv'] if 'apiKeyEnv' in 原始配置 else 默认接口密钥环境),#凭证引用
        'baseURL':基址,#基址
        'defaults':{
            'thinking':思考,#开关
            'reasoningEffort':力度,#力度
        },#思考默认
        'maxTokens':原始配置['maxTokens'] if 'maxTokens' in 原始配置 else 默认最大令牌,#输出上限
        'defaultContextWindow':原始配置['defaultContextWindow'] if 'defaultContextWindow' in 原始配置 else 默认上下文窗口,#默认窗口
        'models':解析模型目录(原始配置['models'] if 'models' in 原始配置 else None),#目录
        'streamIdleTimeoutMs':空闲超时,#空闲超时
        'maxRequestFilesBytes':请求文件字节,#文件字节
        'maxInlineRequestImageBytes':内联图字节,#内联字节
        'maxImagesPerRequest':每请求张数,#张数
        'imageOffloadByteQuantum':卸载字节量子,#卸载字节量子
        'inlineImageOffloadByteQuantum':内联卸载字节量子,#内联卸载字节量子
        'imageOffloadCountQuantum':卸载张数量子,#卸载张数量子
        'filesApiTimeoutMs':文件超时,#Files 超时
        'filePolicy':{
            'expiresAfterSeconds':过期秒,#过期
            'refreshMarginSeconds':刷新边距,#刷新边距
            'quotaCleanupBatch':清理批,#清理批
        },#文件政策
        'retryPolicy':解析重试政策(原始配置['retryPolicy'] if 'retryPolicy' in 原始配置 else None,'llm-deepseek: retryPolicy'),#解析政策
    }#已校验事实
