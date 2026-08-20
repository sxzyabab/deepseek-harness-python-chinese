"""DeepSeek 适配器：对对话补全端点做 HTTP+SSE，发出 harness 流块。

对齐上游 `llm-deepseek/src/adapter.ts`。公开面仅中文名；无英文别名。
"""
import json,re,time,threading#JSON、正则、时间与工作线程
from email.utils import parsedate_tz as 解析邮件日期,mktime_tz as 邮件时区戳#HTTP日期
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接#HTTP客户端
from math import isfinite as 是否有限#有限数判断
from urllib.parse import urlparse as 解析网址#拆URL
from llm import (
    归属头,#产品归属头
    上下文窗口超出码,#溢出码
    是否上下文窗口超出错误,#溢出分类
    是否配额超出错误,#配额分类
    大模型适配器,#适配器基类
    大模型错误,#LLM错误
    提供方请求标识,#请求id品牌
    配额超出码,#配额码
    推理力度标识,#力度id品牌
)#导入 llm 词表
from timeout import 空闲看门狗,取超时#空闲看门狗与超时判定
from .序列化 import 序列化请求#线路序列化
from .事件流 import 解析服务推送#服务推送事件解析
from .翻译 import 翻译#线路翻译

__all__=(#仅中文公开名
    '默认流空闲超时毫秒','默认上下文窗口','默认最大令牌',
    '深求适配器','中止信号','中止控制器','合成信号','模型信息',
)#公开面结束

编码=json.dumps#JSON编码
解码=json.loads#JSON解码
线程=threading.Thread#工作线程
事件=threading.Event#中止事件
完整匹配=re.fullmatch#整串数字匹配
取时间=time.time#纪元秒

默认流空闲超时毫秒=300000#默认空闲超时毫秒
默认上下文窗口=1000000#默认窗口
默认最大令牌=256000#默认输出上限
流空闲超时码='LLM_STREAM_IDLE_TIMEOUT'#空闲超时码
关闭力度=推理力度标识('off')#关闭力度
高度力度=推理力度标识('high')#高力度
最大力度=推理力度标识('max')#最大力度
完整力度列表=[
    {'id':关闭力度,'name':'Off'},#关闭
    {'id':高度力度,'name':'High'},#高
    {'id':最大力度,'name':'Max'},#最大
]#完整力度
仅关闭力度列表=[
    {'id':关闭力度,'name':'Off'},#关闭
]#仅关闭

class 中止信号:
    """对应中止信号协议，只通知不自己停工作。"""
    def __init__(自身,事件对象,取原因):
        """绑到共享事件与原因读取。"""
        自身._事件=事件对象#中止事件
        自身._取原因=取原因#读取原因
    @property
    def 已中止(自身):
        """是否已经中止。"""
        return 自身._事件.is_set()#事件已置位
    @property
    def 原因(自身):
        """中止原因。"""
        return 自身._取原因()#当前原因
    def 等待(自身):
        """阻塞直到中止。"""
        自身._事件.wait()#等待事件

class 中止控制器:
    """对应中止控制器。"""
    def __init__(自身):
        """创建一对控制器与信号。"""
        自身._事件=事件()#中止事件
        自身._原因=None#中止原因
        自身.信号=中止信号(自身._事件,自身._读原因)#对外信号
    def _读原因(自身):
        """读取当前中止原因。"""
        return 自身._原因#原因
    def 中止(自身,原因=None):
        """发出中止；重复调用忽略。"""
        if 自身._事件.is_set():#已中止
            return#已中止
        自身._原因=原因#记下原因
        自身._事件.set()#置位

def 合成信号(甲,乙):
    """先中止的一路获胜。"""
    控制器=中止控制器()#合成控制器
    def 转发(源):
        """源中止后转发到合成控制器。"""
        源.等待()#阻塞到源中止
        控制器.中止(源.原因)#转发原因
    for 源 in (甲,乙):#监视两路
        if 源.已中止:#已中止
            控制器.中止(源.原因)#已中止则立刻合成
            return 控制器.信号#合成信号
        线程(target=转发,args=(源,),daemon=True).start()#监视一路
    return 控制器.信号#融合信号

def 模型信息(提供方,模型):
    """目录条目转模型信息。"""
    信息={
        'provider':提供方,#提供方
        'id':模型['id'],#模型id
        'name':模型['name'] if 模型.get('name') is not None else 模型['id'],#展示名或id
        'inputModalities':['text'],#本线路纯文本
    }#拆离信息
    if 模型.get('description') is not None:#有描述
        信息['description']=模型['description']#有描述才带上
    return 信息#模型信息

def 解析提供方重试等待(值):
    """解析 Retry-After 头为毫秒。"""
    if 值 is None:#没有头
        return None#没有头
    if 完整匹配(r'\d+',值):#纯秒数
        延迟=int(值)*1000#秒换毫秒
        return 延迟 if 是否有限(延迟) and 延迟>0 else None#正有限才用
    解析=解析邮件日期(值)#HTTP日期
    if 解析 is None:#无法解析
        return None#无法解析
    延迟=邮件时区戳(解析)*1000-取时间()*1000#日期减现在
    return 延迟 if 是否有限(延迟) and 延迟>0 else None#正有限才用

def 取请求标识(响应):
    """取出提供方请求id。"""
    值=响应.getheader('x-request-id')#第一处头名
    if 值 is None:#没有
        值=响应.getheader('x-deepseek-request-id')#第二处头名
    if 值 is None or len(值)==0:#空则没有
        return None#空则没有
    return 提供方请求标识(值)#品牌化

def 映射超文本错误码(状态,错误=None):
    """把超文本状态映射成稳定的大模型错误码。"""
    if 状态==401 or 状态==403:#认证失败
        return 'AUTH'#认证失败
    片段=[]#诊断文本
    if 错误 is not None:#有提供方错误体
        for 项 in (错误.get('code'),错误.get('type'),错误.get('message')):#逐字段
            if 项:#非空
                片段.append(项)#非空才收
    详情=' '.join(片段)#拼诊断
    if 是否配额超出错误(详情):#配额措辞
        return 配额超出码#配额耗尽
    if 状态==429:#速率限制
        return 'RATE_LIMIT'#速率限制
    if 状态==400:#坏请求
        if 是否上下文窗口超出错误(详情):#溢出措辞
            return 上下文窗口超出码#上下文溢出
        return 'INVALID_REQUEST'#其余400
    if 状态>=500:#服务端
        return 'SERVER'#服务端错误
    return f'HTTP_{状态}'#其余用状态号

class 深求适配器(大模型适配器):
    """深求线路适配器。一个实例服务它被注册时的每个模型名。"""
    def __init__(自身,配置):
        """保存插件拥有的操作局部解析钩子。"""
        自身.配置=配置#插件钩子

    def 提供方信息(自身,提供方):
        """提供方展示。"""
        return {'id':提供方,'name':'DeepSeek'}#固定展示名（线路字面量）

    def 提供方重试政策(自身,提供方):
        """提供方政策。"""
        return 自身.配置['选项']()['retryPolicy']#按操作读取已解析政策

    def 列出模型(自身,提供方):
        """建议目录。"""
        结果=[]#模型列表
        for 模型 in 自身.配置['选项']()['models']:#当前快照
            结果.append(模型信息(提供方,模型))#映射当前快照
        return 结果#建议目录

    def 解析模型(自身,提供方,模型,信号=None):
        """解析精确模型。"""
        连接=自身.配置['选项']()#当前连接事实
        条目=None#目录条目
        for 项 in 连接['models']:#逐条
            if 项['id']==模型:#命中
                条目=项#命中目录
                break#找到即停
        if 条目 is not None and 条目.get('contextWindow') is not None:#条目有窗口
            窗口=条目['contextWindow']#条目窗口
        else:#回落默认
            窗口=连接['defaultContextWindow']#默认窗口
        if 条目 is None:#未编目
            信息={'provider':提供方,'id':模型,'name':模型,'inputModalities':['text']}#未编目仍声明纯文本
        else:#有目录
            信息=模型信息(提供方,条目)#目录条目
        信息['context']={'contextWindow':窗口}#窗口
        if 条目 is not None and 条目.get('maxTokens') is not None:#条目上限
            信息['defaultMaxTokens']=条目['maxTokens']#条目上限
        else:#配置上限
            信息['defaultMaxTokens']=连接['maxTokens']#配置上限
        if 连接['defaults'].get('thinking')=='disabled':#部署关掉思考
            信息['reasoning']={
                'efforts':仅关闭力度列表,#只有off
                'defaultEffort':关闭力度,#默认关闭
            }#仅关闭力度
        else:#完整力度
            默认力度配置=连接['defaults'].get('reasoningEffort')#配置力度
            if 默认力度配置=='off':#关闭
                默认力度=关闭力度#关闭
            elif 默认力度配置=='max':#最大
                默认力度=最大力度#最大
            else:#其余默认high
                默认力度=高度力度#其余默认high
            信息['reasoning']={
                'efforts':完整力度列表,#off/high/max
                'defaultEffort':默认力度,#默认力度
            }#完整力度
        return 信息#已解析信息

    def 流式(自身,选项):
        """流式调用。连接事实与凭证在此冻结并撑过整次请求。"""
        连接=自身.配置['选项']()#本次连接事实
        接口密钥=自身.配置['解析接口密钥'](连接)#从本快照解析密钥
        用户标识=自身.配置['解析用户标识']()#匿名用户id
        消费方=中止控制器()#消费方中止
        if 选项.get('signal') is None:#调用方未给信号
            上游=消费方.信号#只用消费方
        else:#融合
            上游=合成信号(选项['signal'],消费方.信号)#融合调用方与消费方
        看门狗=空闲看门狗(上游,连接['streamIdleTimeoutMs'],流空闲超时码)#空闲看门狗
        def 注释活动(注释):
            """服务推送注释当作传输活动。"""
            看门狗.脉冲()#再武装空闲计时
        迭代器=自身.请求(选项,看门狗.信号,连接,接口密钥,用户标识,注释活动)#打开上游请求
        已耗尽=False#是否正常耗尽
        try:#消费上游
            while True:#直到done
                结果=看门狗.下一步(迭代器)#带空闲监视的下一步
                if 结果['done']:#上游结束
                    已耗尽=True#正常耗尽
                    return#结束生成器
                yield 结果['value']#让出一块
        except Exception as 错误:#读取或打开失败
            if 取超时(看门狗.信号,流空闲超时码) is not None:#空闲超时
                超时文案=f'DeepSeek stream idle timeout after {连接["streamIdleTimeoutMs"]}ms'#超时文案（诊断字面量）
                raise 大模型错误(超时文案,'TIMEOUT') from 错误#空闲超时
            调用方信号=选项.get('signal')#调用方信号
            if 调用方信号 is not None and 调用方信号.已中止:#调用方中止
                raise 大模型错误('DeepSeek request aborted by caller','ABORTED') from 错误#中止
            if isinstance(错误,大模型错误):#已是大模型错误
                raise 错误#已是LLM错误则原样
            传输文案=f'DeepSeek API stream from {连接["baseURL"]} failed'#传输文案（诊断字面量）
            raise 大模型错误(传输文案,'TRANSPORT') from 错误#其余当传输
        finally:#生成器结束
            消费方.中止('DeepSeek stream consumer stopped')#中止消费方
            if not 已耗尽:#尚未耗尽
                try:#通知上游取消
                    迭代器.close()#关闭迭代器
                except Exception:#吞掉拆除期中止
                    pass#吞掉拆除期中止；消费方控制器已拥有终止
            看门狗.释放()#释放看门狗定时器

    def 请求(自身,选项,信号,连接,接口密钥,用户标识,注释回调):
        """一次上游超文本加服务推送。"""
        体=序列化请求(选项,连接['defaults'])#序列化请求体
        载荷=编码(体,ensure_ascii=False,separators=(',',':'))#JSON正文
        正文=载荷.encode('utf-8')#UTF-8字节
        头={
            'authorization':'Bearer '+接口密钥,#bearer
            'content-type':'application/json',#JSON
            'accept':'text/event-stream',#服务推送
        }#请求头
        头.update(归属头())#产品归属
        头['x-deepseek-harness-user-id']=str(用户标识)#匿名用户
        if 选项.get('sessionId') is not None:#有会话
            头['x-deepseek-harness-session-id']=str(选项['sessionId'])#会话id
        if 选项.get('purpose')=='compaction':#压缩用途
            头['x-deepseek-harness-compact']='1'#压缩标记
        网址=连接['baseURL']+'/chat/completions'#对话补全
        解析=解析网址(网址)#拆主机路径
        try:#打开连接
            if 解析.scheme=='https':#安全
                客户端=安全连接(解析.hostname,解析.port)#HTTPS
            else:#明文
                客户端=明文连接(解析.hostname,解析.port)#HTTP
            def 监视中止():
                """信号中止时关掉套接字。"""
                信号.等待()#阻塞到中止
                客户端.close()#拆传输
            线程(target=监视中止,daemon=True).start()#监视中止
            if 信号.已中止:#已经中止
                客户端.close()#已经中止则立刻关掉
                原因=信号.原因#中止原因
                if isinstance(原因,BaseException):#原样异常
                    raise 原因#原样抛出
                raise RuntimeError(原因 or 'aborted')#包装中止
            路径=解析.path or '/'#路径
            if 解析.query:#有查询串
                路径=路径+'?'+解析.query#查询串
            客户端.request('POST',路径,body=正文,headers=头)#发出POST
            响应=客户端.getresponse()#上游响应
        except Exception as 错误:#连接失败
            if 信号.已中止:#已中止
                raise 错误#已中止则原样抛，让外层分类
            传输文案=f'DeepSeek API request to {连接["baseURL"]} failed'#传输文案（诊断字面量）
            raise 大模型错误(传输文案,'TRANSPORT') from 错误#传输失败
        if not (200<=响应.status<300):#非成功
            消息=f'DeepSeek API error (HTTP {响应.status})'#默认消息（诊断字面量）
            提供方错误=None#可选提供方错误
            try:#读错误体
                解析错误=解码(响应.read())#按线路错误查看
                提供方错误=解析错误.get('error')#错误对象
                if 提供方错误 and 提供方错误.get('message'):#有消息
                    消息=提供方错误['message']#有消息则用
            except Exception:#只吞错误体解析
                pass#只吞错误体解析：HTTP状态仍标识失败，畸形网关JSON不得盖住它
            等待=解析提供方重试等待(响应.getheader('retry-after'))#可选等待
            标识=取请求标识(响应)#可选请求id
            选项事实={'status':响应.status}#带状态事实
            if 等待 is not None:#有等待
                选项事实['providerRetryAfterMs']=等待#有等待才带上
            if 标识 is not None:#有请求id
                选项事实['requestId']=标识#有请求id才带上
            raise 大模型错误(消息,映射超文本错误码(响应.status,提供方错误),选项事实)#超文本错误
        长度=响应.getheader('content-length')#正文长度
        if 长度=='0':#空正文
            raise 大模型错误('DeepSeek API returned no response body','EMPTY_RESPONSE')#空响应
        for 块 in 翻译(解析服务推送(响应,注释回调)):#解析再翻译
            yield 块#服务推送解析再翻译
