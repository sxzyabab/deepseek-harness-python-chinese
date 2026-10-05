'带稳定、可供程序路由的 code 与链式 cause 的 Harness 错误基类'
import re#正则
import math#有限数判定
from ...依赖.工具 import 聚合错误#聚合错误
from .调用配置 import 深冻结#冻结可序列化事实

__all__=(#仅中文公开名
    '上下文窗口溢出码','配额耗尽码','空响应码','非法凭证码','图片卸载必需码',
    '装备错误','是否上下文窗口溢出','是否配额耗尽','错误链','是否装备错误',
    '上下文窗口超出码','配额超出码','是否上下文窗口超出错误','是否配额超出错误',
    '语言模型错误','永不错误','重试政策错误',
)#公开面结束

上下文窗口溢出码='CONTEXT_WINDOW_EXCEEDED'#上下文溢出码
配额耗尽码='QUOTA'#配额耗尽码
空响应码='EMPTY_RESPONSE'#空响应码
非法凭证码='INVALID_CREDENTIAL'#非法凭证码
图片卸载必需码='IMAGE_OFFLOAD_REQUIRED'#图片卸载尚未满足码

结构化上下文溢出=re.compile(
    r'(?:^|[^a-z0-9])context[\s_-](?:length|window)[\s_-]'
    r'(?:exceed(?:ed|s)?|overflow(?:ed)?|limit[\s_-]exceeded)(?:$|[^a-z0-9])',
    re.I)#结构化溢出措辞
对上下文太大=re.compile(
    r'\b(?:request|prompt|input|messages?)\s+(?:is\s+|are\s+)?'
    r'too\s+(?:large|long)\s+for\s+(?:(?:this|the)\s+)?'
    r"(?:model(?:'s)?\s+)?context(?:\s+window)?\b",
    re.I)#对上下文来说太大
超出模型上下文=re.compile(
    r'\b(?:input|prompt|request|messages?)\b.{0,40}'
    r'\b(?:exceed(?:s|ed)?|overflows?|is\s+larger\s+than)\b.{0,40}'
    r"\b(?:the\s+)?(?:model(?:'s)?\s+)?context(?:\s+(?:length|window))?\b",
    re.I)#超出模型上下文
最大上下文长度=re.compile(
    r'\b(?:maximum|max)(?:\s+(?:allowed|supported))?\s+context\s+(?:length|window)\b',
    re.I)#max context length/window
对模型太长=re.compile(
    r'\b(?:input|prompt|request)\s+(?:is\s+)?too\s+(?:long|large)\s+for\s+(?:this|the)\s+model\b',
    re.I)#对模型来说太长/太大

class 装备错误(Exception):#所有 Harness 错误的基类
    '所有 Harness 错误的基类，携带稳定 code 与可选 cause'
    def __init__(自身,消息,码,选项=None):#记下稳定 code，并把 cause 链到本错误
        '记下稳定 code，并把 cause 链到本错误'
        super().__init__(消息)#交给 Exception
        自身.message=消息#可读消息
        自身.code=码#记下稳定 code
        自身.name='HarnessError'#基类名
        原因=None#默认无 cause
        if isinstance(选项,dict):#选项是映射
            原因=选项.get('cause')#从选项取出
        if 原因 is not None:#有 cause
            自身.cause=原因#TS 风格 cause
            自身.__cause__=原因#Python 异常链

def 是否上下文窗口溢出(细节):#识别上下文溢出措辞
    '识别 OpenAI 兼容提供方与库适配器使用的上下文溢出措辞'
    return bool(#任一措辞命中
        结构化上下文溢出.search(细节)#结构化溢出
        or 最大上下文长度.search(细节)#max context
        or 对上下文太大.search(细节)#对上下文太大
        or 对模型太长.search(细节)#对模型太长
        or 超出模型上下文.search(细节)#超出模型上下文
    )#任一措辞命中

def 是否配额耗尽(细节):#识别账户配额耗尽措辞
    '识别标识账户配额耗尽、而非瞬时请求速率限制的提供方措辞'
    return bool(#仅终止性配额措辞
        re.search(r'\binsufficient[\s_-]+(?:quota|balance|credits?)\b',细节,re.I)#insufficient
        or re.search(r'\b(?:quota|usage[\s_-]+limit)[\s_-]+(?:exceeded|exhausted|reached)\b',细节,re.I)#quota limit
        or re.search(r'\bexceed(?:ed|s)?[\s_-]+(?:(?:your|the)[\s_-]+)?(?:current[\s_-]+)?quota\b',细节,re.I)#exceed quota
        or re.search(r'\b(?:balance|credits?)[\s_-]+(?:exhausted|depleted)\b',细节,re.I)#balance exhausted
        or re.search(r'\bout[\s_-]+of[\s_-]+(?:credits?|budget)\b',细节,re.I)#out of credits
    )#仅终止性配额措辞

def 错误链(值):#渲染抛出值与 cause 链
    '把抛出值连同完整 cause 链与聚合成员渲染出来'
    路径=set()#当前递归路径上的对象 id
    def 渲染(当前):#递归渲染一个节点
        '递归渲染一个节点'
        编号=id(当前)#对象身份
        if 编号 in 路径:#环
            return '<circular cause>'#环则停
        路径.add(编号)#进入路径
        try:#渲染本节点
            if not isinstance(当前,Exception):#非异常
                if isinstance(当前,dict) and 'message' in 当前:#映射带 message
                    描述=当前['message']#自有 message
                    if isinstance(描述,str):#字符串消息
                        return 描述#用该消息
                elif hasattr(当前,'__dict__') and 'message' in 当前.__dict__:#实例带 message
                    描述=当前.__dict__['message']#自有数据值
                    if isinstance(描述,str):#字符串消息
                        return 描述#用该消息
                return str(当前)#其余转字符串
            消息=getattr(当前,'message',None)#Error.message
            if not isinstance(消息,str):#无 message
                消息=当前.args[0] if 当前.args and isinstance(当前.args[0],str) else ''#无 message 则看 args
            if 消息=='':#空消息
                消息=getattr(当前,'name',type(当前).__name__)#空消息则用 name
            成员=''#默认无聚合成员
            if isinstance(当前,聚合错误) and len(当前.errors)>0:#有聚合成员
                成员=' ['+'; '.join(渲染(项) for 项 in 当前.errors)+']'#括号连接成员
            原因=getattr(当前,'cause',None)#TS 风格 cause
            if 原因 is None:#无 TS cause
                原因=getattr(当前,'__cause__',None)#Python 异常链
            if 原因 is None:#无 cause
                原因文本=''#空
            else:#有 cause
                原因文本=渲染(原因)#递归渲染 cause
            if 原因文本=='' or 原因文本==消息:#重复或空
                原因段=''#重复则跳过
            else:#追加 cause
                原因段=': '+原因文本#追加 cause
            return str(消息)+成员+原因段#拼出本节点
        except Exception:#本节点不可渲染
            return '<unrenderable value>'#本节点不可渲染
        finally:#退出路径
            路径.discard(编号)#退出当前递归路径
    return 渲染(值)#从最外层开始

def 是否装备错误(值):#收窄为装备错误实例
    '把任意抛出值收窄为装备错误实例'
    return isinstance(值,装备错误)#按类身份判定

上下文窗口超出码=上下文窗口溢出码#消费方别名
配额超出码=配额耗尽码#消费方别名
是否上下文窗口超出错误=是否上下文窗口溢出#消费方别名
是否配额超出错误=是否配额耗尽#消费方别名

class 语言模型错误(装备错误):#LLM 相关失败的有类型错误
    'LLM 相关失败的有类型错误'
    def __init__(自身,消息,码,选项=None):#校验可序列化事实并冻结 failure
        '校验可序列化事实并冻结 failure'
        if not isinstance(消息,str) or len(消息)==0:#消息非法
            raise 装备错误('LlmError message must be a non-empty string','INVALID_ERROR')#消息必须非空
        if not isinstance(码,str) or len(码)==0:#code 非法
            raise 装备错误('LlmError code must be a non-empty string','INVALID_ERROR')#code 必须非空
        if 选项 is None:#无选项
            选项={}#无选项
        if 'status' in 选项:#有 HTTP 状态
            状态=选项['status']#HTTP 状态
            是整数=isinstance(状态,(int,float)) and not isinstance(状态,bool) and math.isfinite(状态) and 状态==int(状态)#合法整数
            if not 是整数 or 状态<100 or 状态>599:#状态越界
                raise 装备错误('LlmError status must be an integer from 100 through 599','INVALID_ERROR')#状态越界
        if 'providerRetryAfterMs' in 选项:#有建议等待
            等待=选项['providerRetryAfterMs']#建议等待
            if not (isinstance(等待,(int,float)) and not isinstance(等待,bool) and math.isfinite(等待) and 等待>0):#等待非法
                raise 装备错误('LlmError providerRetryAfterMs must be a positive finite number','INVALID_ERROR')#等待非法
        if 'requestId' in 选项:#有请求 id
            请求=选项['requestId']#请求 id
            if not isinstance(请求,str) or len(请求)==0:#请求 id 非法
                raise 装备错误('LlmError requestId must be a non-empty string','INVALID_ERROR')#请求 id 非法
        if 'offloadImages' in 选项:#有还需卸载张数
            卸载=选项['offloadImages']#还需卸载张数
            是正安全=isinstance(卸载,(int,float)) and not isinstance(卸载,bool) and 卸载==int(卸载) and 卸载>0#正安全整数
            if not 是正安全:#张数非法
                raise 装备错误('LlmError offloadImages must be a positive safe integer','INVALID_ERROR')#张数非法
        装备错误.__init__(自身,消息,码,选项)#交给装备错误
        自身.name='LlmError'#固定类名
        事实={'message':消息,'code':码}#可序列化事实
        if 'status' in 选项:#有状态才写入
            事实['status']=选项['status']#有状态才带上
        if 'providerRetryAfterMs' in 选项:#有等待才写入
            事实['providerRetryAfterMs']=选项['providerRetryAfterMs']#有等待才带上
        if 'requestId' in 选项:#有请求 id 才写入
            事实['requestId']=选项['requestId']#有请求 id 才带上
        if 'offloadImages' in 选项:#有还需卸载张数
            事实['offloadImages']=选项['offloadImages']#有张数才带上
        自身.failure=深冻结(事实)#冻结可序列化事实

class 永不错误(Exception):
    '封闭联合穷尽失败'

class 重试政策错误(Exception):
    '重试政策配置校验失败'
