"""DeepSeek 对话补全适配器：http.client 加服务推送。"""
import json,re,time#JSON、Retry-After 与时钟
from email.utils import parsedate_to_datetime as 解析日期时间#HTTP 日期
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接,HTTPException as 超文本异常#HTTP
from urllib.parse import urlparse as 解析网址
from ....llm import (
    归属头,#归属
    内容含图片,#含图
    大模型适配器,#基类
    大模型错误,#错误
    是否上下文窗口溢出,#溢出分类
    是否配额耗尽,#配额分类
    上下文窗口溢出码,#溢出码
    配额耗尽码,#配额码
    提供方请求标识,#请求 id
)#llm 词表
from .....工具.超时 import 空闲看门狗,取超时,中止控制器,合成信号#空闲看门狗与中止
from ...协议无关.文件仓 import 深求文件仓#文件仓
from ...协议无关.请求定价 import 深求图片请求定价,解析请求图目标#定价与目标
from ...协议无关.模型信息 import 目录模型信息,模型信息#模型信息
from ...协议无关.请求文件 import 文件解析失败,请求文件#Files
from ...协议无关.请求扩展 import 准备请求扩展#扩展
from .序列化 import 序列化请求,序列化带图请求#序列化
from .事件流 import 解析服务推送#SSE
from .翻译 import 翻译#翻译

__all__=('http错误码','对话补全适配器')#仅中文公开名

流空闲超时码='LLM_STREAM_IDLE_TIMEOUT'#空闲码
纯秒形=re.compile(r'^[0-9]+\Z',re.ASCII)#Retry-After 纯秒

def 收集图片引用(内容,引用表):
    """收集未卸载图片引用。"""
    for 块 in 内容:#逐块
        if 块.get('type')=='image' and 块.get('offloaded') is not True:#保留图
            引用表[块['attachment']['attachmentId']]=块['attachment']#记下
        elif 块.get('type')=='tool-result':#嵌套
            收集图片引用(块.get('content') or [],引用表)#递归

def 准备请求图(选项,附件,模型,信号):
    """为保留出现准备确定性请求版本。"""
    引用表={}#id→引用
    for 消息 in 选项['messages']:#逐条
        收集图片引用(消息.get('content') or [],引用表)#收集
    有序=list(引用表.values())#顺序
    结果={}#id→版本
    for 引用 in 有序:#逐张
        结果[引用['attachmentId']]=附件.读取图像请求(引用,解析请求图目标(模型,引用),信号)#准备
    return 结果#版本表

def 提供方重试等待毫秒(值):
    """解析 Retry-After 为建议等待毫秒。"""
    if 值 is None:#缺席
        return None#无
    if 纯秒形.match(值):#纯秒
        延迟=int(值)*1000#毫秒
        return 延迟 if 延迟>0 else None#正延迟
    try:#HTTP 日期
        时刻=解析日期时间(值)#解析
        延迟=int(时刻.timestamp()*1000)-int(time.time()*1000)#差值
        return 延迟 if 延迟>0 else None#正延迟
    except (TypeError,ValueError,OverflowError):#无法解析
        return None#无

def 请求标识(响应):
    """从响应头取出提供方请求 id。"""
    值=响应.getheader('x-request-id') or 响应.getheader('x-deepseek-request-id')#两候选
    if 值 is None or len(值)==0:#缺席
        return None#无
    return 提供方请求标识(值)#品牌

def http错误码(状态,错误=None):
    """把 HTTP 状态映射到稳定 LlmError 码。"""
    if 状态==401 or 状态==403:#认证
        return 'AUTH'#认证
    if 状态==413:#体过大
        return 'INVALID_REQUEST'#非法请求
    细节=' '.join(段 for 段 in ((错误 or {}).get('code'),(错误 or {}).get('type'),(错误 or {}).get('message')) if 段)#拼接
    if 是否配额耗尽(细节):#配额
        return 配额耗尽码#配额
    if 状态==429:#限流
        return 'RATE_LIMIT'#限流
    if 状态==400:#坏请求
        if 是否上下文窗口溢出(细节):#溢出
            return 上下文窗口溢出码#溢出
        return 'INVALID_REQUEST'#非法请求
    if 状态>=500:#服务端
        return 'SERVER'#服务端
    return 'HTTP_'+str(状态)#其余 HTTP

def 空扩展准备(请求):
    """无插件贡献时的空扩展。"""
    def 接纳():#空接纳
        """无贡献可提交。"""
        return None#空
    return {'fields':{},'accept':接纳}#空扩展

class 对话补全适配器(大模型适配器):
    """面向 DeepSeek 对话补全端点的传输适配器。"""
    def __init__(自身,配置):
        """记下插件钩子并解析文件仓。"""
        自身.配置=配置#钩子
        解析文件=配置.get('解析文件仓') if isinstance(配置,dict) else None#可选仓
        自身.文件仓=解析文件() if 解析文件 is not None else 深求文件仓()#解析或新建

    def 提供方简介(自身,提供方):
        """提供方展示。"""
        return {'id':提供方,'name':'DeepSeek'}#展示

    def 提供方重试政策(自身,提供方):
        """提供方政策。"""
        return 自身.配置['选项']()['retryPolicy']#政策

    def 图片请求定价(自身,提供方,模型):
        """图请求定价。"""
        附件钩子=自身.配置.get('解析附件')#附件
        访问钩子=自身.配置.get('解析图片访问')#访问
        def 解析访问(引用):#访问
            """把附件仓上的当前路径桥进执行世界。"""
            if 附件钩子 is None or 访问钩子 is None:#无
                return None#无
            附件=附件钩子()#仓
            if 附件 is None:#无仓
                return None#无
            return 访问钩子(附件,引用)#访问
        解析=解析访问 if 附件钩子 is not None else None#可选
        return 深求图片请求定价(自身.配置['选项'](),模型,解析)#定价

    def 列出模型(自身,提供方):
        """建议目录。"""
        return [目录模型信息(提供方,模型) for 模型 in 自身.配置['选项']()['models']]#目录

    def 解析模型(自身,提供方,模型,信号=None):
        """解析精确模型。"""
        return 模型信息(自身.配置['选项'](),提供方,模型)#能力

    def 准备调用(自身,提供方,模型,信号=None):
        """把元数据与派发绑到同一代。"""
        连接=自身.配置['选项']()#本代
        def 流(选项):#派发
            """用冻结连接流式调用。"""
            return 自身.带连接流式(选项,连接)#流
        return {'model':模型信息(连接,提供方,模型),'stream':流}#已准备

    def 流式(自身,选项):
        """流式调用。"""
        return 自身.带连接流式(选项,自身.配置['选项']())#当前代

    def 带连接流式(自身,选项,连接):
        """用一代已校验连接消费流。"""
        含图=any(内容含图片(消息.get('content') or []) for 消息 in 选项['messages'])#含图
        附件=None#附件仓
        if 含图:#需要视觉
            模型=None#目录
            for 条目 in 连接['models']:#逐条
                if 条目['id']==选项['model']:#命中
                    模型=条目#记下
                    break#停
            模态=模型.get('inputModalities') if 模型 is not None else None#模态
            if 模态 is None or 'image' not in 模态:#非视觉
                raise 大模型错误('DeepSeek model "'+str(选项['model'])+'" does not accept image input.','UNSUPPORTED_CONTENT')#不接受图
            解析附件=自身.配置.get('解析附件')#钩子
            附件=解析附件() if 解析附件 is not None else None#仓
            if 附件 is None:#无仓
                raise 大模型错误('DeepSeek image conversion requires the durable attachment service.','UNSUPPORTED_CONTENT')#需要附件
        接口密钥=自身.配置['解析接口密钥'](连接)#密钥
        用户标识=自身.配置['解析用户标识']()#用户
        消费者=中止控制器()#消费方中止
        上游=选项.get('signal')#调用方
        信号=消费者.信号 if 上游 is None else 合成信号(上游,消费者.信号)#融合
        看门狗=空闲看门狗(信号,连接['streamIdleTimeoutMs'],流空闲超时码)#空闲
        def 活动():#传输活动
            """无值时重置空闲计时。"""
            看门狗.脉冲()#脉冲
        迭代器=自身.请求(选项,看门狗.信号,连接,接口密钥,用户标识,附件,活动)#请求
        耗尽=False#是否自然结束
        try:#消费
            while True:#逐步
                结果=看门狗.下一步(迭代器)#下一步
                if 结果['done']:#结束
                    耗尽=True#记下
                    return
                yield 结果['value']#让出
        except Exception as 错误:#失败
            if 取超时(看门狗.信号,流空闲超时码) is not None:#空闲超时
                raise 大模型错误('DeepSeek stream idle timeout after '+str(连接['streamIdleTimeoutMs'])+'ms','TIMEOUT',{'cause':错误}) from 错误#超时
            if 上游 is not None and 上游.is_set():#调用方中止
                raise 大模型错误('DeepSeek request aborted by caller','ABORTED',{'cause':错误}) from 错误#中止
            if isinstance(错误,大模型错误):#已是 LLM 错误
                raise 错误#原样
            raise 大模型错误('DeepSeek API stream from '+连接['baseURL']+' failed','TRANSPORT',{'cause':错误}) from 错误#传输
        finally:#收尾
            消费者.中止('DeepSeek stream consumer stopped')#停消费
            看门狗.释放()#释放看门狗
            if not 耗尽:#未耗尽
                try:#关闭生成器
                    迭代器.close()#关闭
                except Exception:#拆除失败
                    pass#消费方已拥有终止

    def 请求(自身,选项,信号,连接,接口密钥,用户标识,附件,活动):
        """发对话补全请求并翻译服务推送。"""
        头=dict(归属头())#归属
        头['authorization']='Bearer '+接口密钥#密钥
        头['content-type']='application/json'#JSON
        头['accept']='text/event-stream'#SSE
        头['x-deepseek-harness-user-id']=str(用户标识)#用户
        if 选项.get('sessionId') is not None:#有会话
            头['x-deepseek-harness-session-id']=str(选项['sessionId'])#会话
        if 选项.get('purpose')=='compaction':#压缩
            头['x-deepseek-harness-compact']='1'#压缩
        文件连接={'baseURL':连接['baseURL'],'apiKey':接口密钥,'protocol':连接['protocol']}#文件连接
        模型=None#目录
        for 条目 in 连接['models']:#逐条
            if 条目['id']==选项['model']:#命中
                模型=条目#记下
                break#停
        解析图片访问=None#访问
        if 附件 is not None:#有仓
            访问钩子=自身.配置.get('解析图片访问')#钩子
            if 访问钩子 is not None:#有钩子
                def 解析访问(引用):#访问
                    """当前执行世界路径。"""
                    return 访问钩子(附件,引用)#桥
                解析图片访问=解析访问#记下
        请求图={}#版本表
        if 附件 is not None and 模型 is not None:#可准备
            请求图=准备请求图(选项,附件,模型,信号)#准备
        表示='file'#先文件
        请求文件对象=请求文件(自身.文件仓,文件连接,连接['filePolicy'],连接['filesApiTimeoutMs'],信号,活动)#Files
        准备=自身.配置.get('准备扩展')#扩展钩子
        if 准备 is None:#无
            准备=空扩展准备#空
        while True:#尝试
            请求文件对象.开始尝试()#重置出现
            if 附件 is None:#纯文本
                体=序列化请求(选项,连接['defaults'])#文本
            elif 表示=='base64':#内联
                图选项={
                    'representation':{'kind':'base64'},#内联
                    'requestImages':请求图,#版本
                    'maxRequestImageBytes':连接['maxInlineRequestImageBytes'],#内联上限
                    'maxImagesPerRequest':连接['maxImagesPerRequest'],#张数
                    'byteQuantum':连接['inlineImageOffloadByteQuantum'],#内联量子
                    'countQuantum':连接['imageOffloadCountQuantum'],#张数量子
                }#图选项
                if 解析图片访问 is not None:#有访问
                    图选项['resolveImageAccess']=解析图片访问#访问
                体=序列化带图请求(选项,图选项,连接['defaults'])#带图
            else:#文件 id
                def 解析文件标识(版本,块,位置):#解析 id
                    """在独立上传截止下解析一张保留图。"""
                    return 请求文件对象.解析(版本,位置)#id
                图选项={
                    'representation':{'kind':'file','resolveFileId':解析文件标识},#文件
                    'requestImages':请求图,#版本
                    'maxRequestImageBytes':连接['maxRequestFilesBytes'],#文件上限
                    'maxImagesPerRequest':连接['maxImagesPerRequest'],#张数
                    'byteQuantum':连接['imageOffloadByteQuantum'],#字节量子
                    'countQuantum':连接['imageOffloadCountQuantum'],#张数量子
                }#图选项
                if 解析图片访问 is not None:#有访问
                    图选项['resolveImageAccess']=解析图片访问#访问
                try:#序列化
                    体=序列化带图请求(选项,图选项,连接['defaults'])#带图
                except 文件解析失败:#上传失败
                    表示='base64'#回落内联
                    continue#再试
            扩展选项={'signal':信号}#扩展身份
            if 选项.get('sessionId') is not None:#有会话
                扩展选项['sessionId']=str(选项['sessionId'])#会话
            if 选项.get('purpose') is not None:#有用途
                扩展选项['purpose']=选项['purpose']#用途
            扩展=准备请求扩展(体,扩展选项,准备)#合并
            网址=连接['baseURL'].rstrip('/')+'/chat/completions'#端点
            解析=解析网址(网址)
            载荷=扩展['payload']#JSON 串
            if isinstance(载荷,str):#文本
                载荷=载荷.encode('utf-8')#字节
            try:#传输
                if 解析.scheme=='https':#安全
                    客户端=安全连接(解析.hostname,解析.port)#HTTPS
                else:#明文
                    客户端=明文连接(解析.hostname,解析.port)#HTTP
                请求路径=解析.path+(('?'+解析.query) if 解析.query else '')#路径
                if not 请求路径:#空
                    请求路径='/'#根
                客户端.request('POST',请求路径,body=载荷,headers=头)#发
                响应=客户端.getresponse()
            except (OSError,超文本异常,RuntimeError) as 错误:#传输失败
                if 信号 is not None and 信号.is_set():#中止
                    raise 错误#原样
                raise 大模型错误('DeepSeek API request to '+连接['baseURL']+' failed','TRANSPORT',{'cause':错误}) from 错误#传输
            if 响应.status<200 or 响应.status>=300:#非成功
                原文=响应.read()#体
                客户端.close()#关
                文本=原文.decode('utf-8',errors='replace')#文本
                消息='DeepSeek API error (HTTP '+str(响应.status)+')'#默认
                提供方错误=None#可选
                try:#解析
                    解析体=json.loads(文本)#JSON
                    提供方错误=(解析体 or {}).get('error') if isinstance(解析体,dict) else None#error
                    if isinstance(提供方错误,dict) and 提供方错误.get('message'):#有消息
                        消息=提供方错误['message']#覆盖
                except (json.JSONDecodeError,TypeError,ValueError,UnicodeDecodeError):#畸形
                    pass#状态仍够
                细节=' '.join(段 for 段 in (
                    提供方错误.get('code') if isinstance(提供方错误,dict) else None,
                    提供方错误.get('type') if isinstance(提供方错误,dict) else None,
                    提供方错误.get('message') if isinstance(提供方错误,dict) else None,
                ) if isinstance(段,str))#细节
                if 请求文件对象.重试(细节):#陈旧 id
                    continue#再发
                消息=请求文件对象.错误消息(响应.status,消息,细节)#诊断
                等待=提供方重试等待毫秒(响应.getheader('retry-after'))#等待
                标识=请求标识(响应)#请求 id
                选项体={'cause':Exception(文本 if len(文本)>0 else 'DeepSeek HTTP '+str(响应.status)),'status':响应.status}#事实
                if 等待 is not None:#有等待
                    选项体['providerRetryAfterMs']=等待#等待
                if 标识 is not None:#有 id
                    选项体['requestId']=标识#id
                raise 大模型错误(消息,http错误码(响应.status,提供方错误 if isinstance(提供方错误,dict) else None),选项体)#抛出
            扩展['accept']()#接纳
            try:#翻译流
                yield from 翻译(解析服务推送(响应,活动))#翻译
            finally:#关连接
                客户端.close()#关
            return#成功
