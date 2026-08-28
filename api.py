#api.py
from __future__ import annotations#启用延迟注解求值，便于前向引用

import uuid#导入uuid用于生成会话标识
from dataclasses import dataclass,field#导入数据类与字段工厂
from pathlib import Path#导入路径工具用于解析工作目录
from typing import Callable#导入可调用类型用于通知回调

from .客户端 import (Harness客户端,Harness配置,
JSON对象,通知消息)#导入底层客户端与其配置
from .异常 import SDK协议错误#导入协议错误类型

@dataclass(slots=True)#用slots数据类降低内存占用
class DeepSeekHarness配置:#启动本地DeepSeek Harness SDK运行时的配置
    """启动本地DeepSeek Harness SDK运行时的配置。

    运行时默认继承调用方环境，因此已有的DEEPSEEK_API_KEY与DEEPSEEK_BASE_URL会继续生效。
    使用环境变量可有意覆盖或注入子进程环境变量。
    """#说明环境继承与环境变量覆盖约定

    提供方:str="deepseek-official"#默认模型提供方名称
    模型:str="deepseek-v4-flash"#默认模型标识
    最大令牌数:int|None=None#可选的最大生成token数
    工作目录:str|None=None#会话工作目录，空则用当前目录
    运行时工作目录:str|None=None#运行时进程工作目录，空则与工作目录相同
    会话根目录:str|None=None#会话持久化根目录，会写入环境变量
    cordis:str|None=None#cordis配置路径，会写入环境变量
    环境变量:dict[str,str]=field(default_factory=dict)#额外注入的环境变量字典
    运行时二进制:str|None=None#显式指定的运行时可执行文件路径
    启动参数覆盖:tuple[str,...]|None=None#覆盖默认启动参数的元组
    请求超时秒数:float|None=None#请求超时秒数，空表示不超时
    关闭超时秒数:float|None=1.0#关闭子进程等待秒数
    基址:str|None=None#可选的DeepSeek API基址，注入环境变量
    密钥:str|None=None#可选的API密钥，注入环境变量


@dataclass(slots=True)#用slots数据类降低内存占用
class 运行结果:#单次agent轮次运行结果
    会话ID:str#本次使用的会话标识
    最终响应:str#从事件中提取的最终助手文本
    结束原因:str|None#最后一轮结束原因种类，可能为空
    事件列表:list[JSON对象]#本会话树内收集到的会话事件列表
    通知列表:list[通知消息]#本轮收到的全部通知列表
    会话根目录:str|None=None#配置中的会话根目录，便于调用方定位产物


class DeepSeekHarness:#可复用的同步SDK，用于跑DeepSeek Harness智能体轮次
    """可复用的同步SDK，用于跑DeepSeek Harness智能体轮次。

    运行时子进程惰性启动，并由此实例在多次run调用间持有。
    请用上下文管理器使用本实例，或结束后显式调用关闭，以确保子进程被回收。
    """#说明生命周期所有权约定

    def __init__(self,config:DeepSeekHarness配置|None=None,**kwargs:object)->None:#用配置对象或关键字参数构造
        if config is not None and kwargs:#禁止同时传配置对象与关键字
            raise TypeError("pass either DeepSeekHarness配置 or keyword options, not both")#明确二选一错误
        self.config=config or DeepSeekHarness配置(**kwargs)#保存最终配置实例
        工作目录=str(Path(self.config.工作目录 or Path.cwd()).resolve())#解析绝对会话工作目录
        运行时工作目录=str(Path(self.config.运行时工作目录).resolve()) if self.config.运行时工作目录 is not None else 工作目录#解析运行时工作目录
        self._cwd=工作目录#保存会话cwd供initialize使用
        进程环境变量=dict(self.config.环境变量)#复制额外环境变量，避免改动调用方字典
        if self.config.会话根目录 is not None:#若配置了会话根目录
            进程环境变量["DSH_SESSION_ROOT"]=self.config.会话根目录#注入会话根目录环境变量
        if self.config.cordis is not None:#若配置了cordis路径
            进程环境变量["DSH_CORDIS_CONFIG"]=self.config.cordis#注入cordis配置环境变量
        进程环境变量["DSH_CWD"]=工作目录#始终注入会话工作目录
        if self.config.基址 is not None:#若配置了API基址
            进程环境变量["DEEPSEEK_BASE_URL"]=self.config.基址#注入基址环境变量
        if self.config.密钥 is not None:#若配置了API密钥
            进程环境变量["DEEPSEEK_API_KEY"]=self.config.密钥#注入密钥环境变量

        self._client=Harness客户端(#创建并持有底层JSON-RPC客户端
            Harness配置(#把高层配置映射为客户端启动配置
                运行时二进制=self.config.运行时二进制,#透传运行时二进制
                启动参数覆盖=self.config.启动参数覆盖,#透传启动参数覆盖
                工作目录=运行时工作目录,#使用运行时工作目录
                环境变量=进程环境变量,#传入组装好的环境变量
                请求超时秒数=self.config.请求超时秒数,#透传请求超时
                关闭超时秒数=self.config.关闭超时秒数,#透传关闭超时
            )#Harness配置构造结束
        )#Harness客户端构造结束
        self._initialized=False#标记尚未完成initialize

    def __enter__(self)->"DeepSeekHarness":#进入上下文时启动运行时
        self.启动()#确保已启动并完成初始化
        return self#返回自身供with绑定

    def __exit__(self,_exc_type,_exc,_tb)->None:#退出上下文时关闭运行时
        self.关闭()#回收子进程并复位初始化标记

    @property#只读属性暴露底层客户端
    def 客户端(self)->Harness客户端:#返回持有的Harness客户端
        return self._client#直接返回内部客户端实例

    def 启动(self)->None:#启动运行时并完成initialize，幂等
        if self._initialized:#已初始化则直接返回
            return#避免重复initialize
        self._client.启动()#启动底层子进程与读写线程
        self._client.初始化(#向运行时发送initialize
            cwd=self._cwd,#传入会话工作目录
            provider=self.config.提供方,#传入提供方
            model=self.config.模型,#传入模型名
            max_tokens=self.config.最大令牌数,#传入可选max_tokens
        )#initialize调用结束
        self._initialized=True#标记已完成初始化

    def 关闭(self)->None:#关闭底层客户端并复位状态
        self._client.关闭()#请求shutdown并回收子进程
        self._initialized=False#允许之后再次启动

    def 创建会话(self,session_id:str|None=None)->"Session":#创建并确保已启动的会话对象
        self.启动()#惰性启动与初始化
        return Session(self,session_id or f"session-{uuid.uuid4().hex}")#用给定或随机会话id构造Session

    def 运行(#在临时会话上跑一轮输入并返回结果
        self,#当前Harness实例
        input:str|list[JSON对象],#用户输入：纯文本或内容块列表
        *,#之后参数仅关键字传递
        session_id:str|None=None,#可选会话id，空则新建
        on_notification:Callable[[通知消息],None]|None=None,#可选通知回调
    )->运行结果:#返回聚合后的运行结果
        return self.创建会话(session_id).运行(input,on_notification=on_notification)#创建会话并委托运行


class Session:#绑定到某个Harness与会话id的运行句柄
    def __init__(self,harness:DeepSeekHarness,session_id:str)->None:#保存所属Harness与会话id
        self.harness=harness#所属的DeepSeekHarness实例
        self.id=session_id#本会话标识

    def 运行(#在本会话上发送提示并等到空闲后返回结果
        self,#当前Session实例
        input:str|list[JSON对象],#用户输入：纯文本或内容块列表
        *,#之后参数仅关键字传递
        on_notification:Callable[[通知消息],None]|None=None,#可选通知回调
    )->运行结果:#返回本轮运行结果
        内容块=规范输入(input)#把输入规范成内容块列表
        通知列表:list[通知消息]=[]#收集本轮全部通知
        事件列表:list[JSON对象]=[]#收集本会话相关会话事件

        def 收集(通知项:通知消息)->None:#处理一条通知：归档并可选转发给调用方
            通知列表.append(通知项)#始终归档通知
            if on_notification is not None:#若调用方提供了回调
                on_notification(通知项)#转发给调用方
            if (#仅当通知是本会话的session.event时抽取事件
                通知项.方法=="session.event"#方法为会话事件
                and 通知项.载荷.get("sessionId")==self.id#且会话id匹配
            ):#条件成立则尝试抽取event字段
                事件=通知项.载荷.get("event")#取出事件对象
                if isinstance(事件,dict):#事件必须是对象才记录
                    事件列表.append(事件)#追加到事件列表

        with self.harness.客户端.订阅会话通知(self.id) as 订阅:#订阅本会话树通知
            消息标识=self.harness.客户端.session_prompt(#发送session/prompt并拿到消息id
                self.id,#目标会话id
                内容块,#规范化后的内容块
                notification_subscription=订阅,#复用已有订阅避免漏通知
            )#session_prompt调用结束

            已接收=False#是否已看到对应收件箱回执
            while True:#持续消费通知直到会话空闲
                通知项=订阅.下一个()#阻塞取下一条订阅通知
                if not 已接收:#尚未确认收件箱回执前
                    if not 是否收件箱回执(通知项,self.id,消息标识):#非本消息回执则跳过
                        continue#继续等待回执
                    已接收=True#标记已收到回执，之后开始正式收集
                收集(通知项)#归档并抽取事件
                if (#会话状态变为idle表示本轮结束
                    通知项.方法=="session.status"#状态通知
                    and 通知项.载荷.get("sessionId")==self.id#会话匹配
                    and 通知项.载荷.get("status")=="idle"#状态为空闲
                ):#满足则退出循环
                    break#结束等待

        return 运行结果(#组装并返回运行结果
            会话ID=self.id,#本会话id
            最终响应=最终响应(事件列表),#从事件提取最终文本
            结束原因=结束原因(事件列表),#从事件提取结束原因
            事件列表=事件列表,#收集到的事件列表
            通知列表=通知列表,#收集到的通知列表
            会话根目录=self.harness.config.会话根目录,#透传会话根目录配置
        )#运行结果构造结束


def 是否收件箱回执(notification:通知消息,session_id:str,message_id:str)->bool:#判断通知是否为本消息的收件箱回执
    if notification.方法!="session.event" or notification.载荷.get("sessionId")!=session_id:#方法或会话不匹配则否
        return False#不是回执
    事件=notification.载荷.get("event")#取出事件体
    if not isinstance(事件,dict) or 事件.get("type")!="agent/inbox/spliced":#必须是收件箱拼接事件
        return False#不是回执
    数据=事件.get("data")#取出事件数据
    已插入=数据.get("inserted") if isinstance(数据,dict) else None#取出插入的消息列表
    return isinstance(已插入,list) and any(#插入列表中是否含目标消息id
        isinstance(消息,dict) and 消息.get("id")==message_id for 消息 in 已插入
    )#任一匹配即为回执


def 规范输入(input:str|list[JSON对象])->list[JSON对象]:#把字符串或内容块列表规范为内容块列表
    if isinstance(input,str):#纯文本输入
        return [{"type":"text","text":input}]#包成单个text内容块
    return input#已经是内容块列表则原样返回


def 最终响应(events:list[JSON对象])->str:#从事件列表提取最后一条助手文本回复
    for 事件 in reversed(events):#从新到旧扫描事件
        if 事件.get("type")!="assistant/message":#只关心助手消息事件
            continue#跳过其他类型
        数据=事件.get("data")#取出事件数据
        if not isinstance(数据,dict):#数据必须是对象
            continue#跳过畸形事件
        消息=数据.get("message")#尝试取嵌套message字段
        内容所有者=消息 if isinstance(消息,dict) else 数据#有message用message，否则用data
        内容=内容所有者.get("content")#取内容块列表
        if not isinstance(内容,list):#内容必须是列表
            continue#跳过畸形内容
        部分:list[str]=[]#收集文本片段
        for 块 in 内容:#遍历每个内容块
            if isinstance(块,dict) and 块.get("type")=="text":#只拼接text块
                部分.append(str(块.get("text") or ""))#缺失文本当空串
        return "".join(部分)#返回拼接后的最终回复
    return ""#没有助手消息则返回空串


def 结束原因(events:list[JSON对象])->str|None:#返回最近一次轮次结束的原因种类
    """返回最近一次轮次结束的原因种类。

    输入必须包含某次自有运行区间内的根会话事件。

    Raises:
        SDK协议错误: 最近的turn/end没有字符串形式的reason.kind。
    """#说明输入前提与协议错误条件
    for 事件 in reversed(events):#从新到旧扫描事件
        if 事件.get("type")!="turn/end":#只关心轮次结束事件
            continue#跳过其他类型
        数据=事件.get("data")#取出事件数据
        原因=数据.get("reason") if isinstance(数据,dict) else None#取出reason对象
        种类=原因.get("kind") if isinstance(原因,dict) else None#取出原因种类
        if not isinstance(种类,str):#协议要求kind必须是字符串
            raise SDK协议错误("turn/end event requires a string data.reason.kind")#协议违规
        return 种类#返回找到的结束原因
    return None#没有turn/end则返回空
