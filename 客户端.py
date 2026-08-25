#models.py
from __future__ import annotations#启用延迟注解求值，便于前向引用

from dataclasses import dataclass
from typing import TypeAlias as 类型别名
from pydantic import BaseModel

基本JSON值:类型别名=str|int|float|bool|None
JSON数据:类型别名=基本JSON值|dict[str,"JSON数据"]|list["JSON数据"]
JSON对象:类型别名=dict[str,JSON数据]

@dataclass(slots=True)
class 通知消息:
    method:str
    payload:JSON对象

@dataclass(slots=True)
class 入站请求:#JSON_RPC
    id:str|int
    method:str
    payload:JSON对象

class 服务器信息(BaseModel):
    name:str|None=None
    version:str|None=None

class 初始化响应(BaseModel):
    serverInfo:服务器信息|None=None


#client.py
from __future__ import annotations

import json,os,queue,subprocess,threading,time,uuid
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable,TypeVar
from pydantic import BaseModel
from .异常 import (JSON_RPC错误,传输层关闭错误)

ModelT=TypeVar("ModelT",bound=BaseModel)
NotificationFilter:类型别名=Callable[[通知消息],bool]

@dataclass(slots=True)#用slots数据类降低内存占用
class Harness配置:#启动本地DeepSeek Harness SDK运行时的配置
    "启动本地DeepSeek Harness SDK运行时的配置"#类文档说明用途
    runtime_bin:str|None=None#显式运行时可执行文件路径
    bridge_bin:str|None=None#兼容用的桥接可执行文件路径
    launch_args_override:tuple[str,...]|None=None#覆盖默认启动参数
    cwd:str|None=None#子进程工作目录
    env:dict[str,str]|None=None#额外合并进子进程的环境变量
    request_timeout_seconds:float|None=None#请求默认超时秒数
    shutdown_timeout_seconds:float|None=1.0#关闭时等待秒数


class Harness客户端:#通过标准输入输出与DeepSeek Harness SDK运行时通信的同步JSON-RPC客户端
    """通过标准输入输出与DeepSeek Harness SDK运行时通信的同步JSON-RPC客户端。"""#类文档说明传输方式

    def __init__(self,config:Harness配置|None=None)->None:#用可选配置构造客户端
        self.config=config or Harness配置()#保存配置，缺省用空配置
        self._proc:subprocess.Popen[str]|None=None#运行时子进程句柄，未启动为None
        self._lock=threading.Lock()#保护共享表结构的互斥锁
        self._write_lock=threading.Lock()#保护stdin写入的互斥锁
        self._responses:dict[str,queue.Queue[JSON数据|BaseException]]={}#请求id到响应等待队列
        self._notifications:queue.Queue[通知消息|BaseException]=queue.Queue()#未订阅投递时的全局通知队列
        self._notification_subscribers:dict[#订阅id到(队列, 可选过滤器)
            str,tuple[queue.Queue[通知消息|BaseException],NotificationFilter|None]
        ]={}#活跃通知订阅表
        self._session_parents:dict[str,str]={}#子会话到父会话的映射，用于会话树过滤
        self._requests:queue.Queue[入站请求|BaseException]=queue.Queue()#运行时发来的入站请求队列
        self._stderr_lines:deque[str]=deque(maxlen=400)#有界stderr尾部缓冲，供诊断
        self._reader_thread:threading.Thread|None=None#stdout读取线程
        self._stderr_thread:threading.Thread|None=None#stderr读取线程

    def __enter__(self)->"Harness客户端":#进入上下文时启动
        self.启动()#启动子进程与后台线程
        return self#返回自身

    def __exit__(self,_exc_type,_exc,_tb)->None:#退出上下文时关闭
        self.关闭()#回收子进程并唤醒等待者

    def 启动(self)->None:#启动运行时子进程，幂等
        if self._proc is not None:#已启动则直接返回
            return#避免重复拉起
        with self._lock:#加锁清会话亲子表
            self._session_parents.clear()#新进程从空会话树开始
        启动参数=list(self.config.launch_args_override or self.默认启动参数())#解析最终启动参数
        环境变量=os.environ.copy()#继承当前进程环境
        if self.config.env:#若配置了额外环境变量
            环境变量.update(self.config.env)#合并覆盖到子进程环境
        self.注入捆绑默认配置(环境变量)#捆绑启动且无配置时注入默认cordis
        self._proc=subprocess.Popen(#拉起运行时子进程
            启动参数,#启动参数列表
            stdin=subprocess.PIPE,#管道标准输入供写JSON-RPC
            stdout=subprocess.PIPE,#管道标准输出供读JSON-RPC
            stderr=subprocess.PIPE,#管道标准错误供诊断缓冲
            text=True,#文本模式读写
            encoding="utf-8",#统一UTF-8编码
            cwd=None if self.config.cwd is None else str(Path(self.config.cwd).resolve()),#解析工作目录
            env=环境变量,#传入组装环境
            bufsize=1,#行缓冲，便于按行NDJSON
        )#Popen结束
        self.启动读取线程()#启动stdout读取线程
        self.启动错误读取线程()#启动stderr读取线程

    def 关闭(self)->None:#关闭运行时并清理等待者
        进程=self._proc#取出当前子进程引用
        if 进程 is None:#未启动则无需关闭
            return#直接返回
        try:#尝试发送协议层shutdown
            self.请求("shutdown",None,response_model=关闭响应,timeout_seconds=self.config.shutdown_timeout_seconds)#请求优雅关闭
        except Exception as 错误:#shutdown失败只记诊断，不中断关闭流程
            self._stderr_lines.append(f"shutdown request failed: {错误}")#记录shutdown失败信息
        if 进程.stdin:#若stdin仍可用
            try:#尝试关闭stdin促使对端退出
                进程.stdin.close()#关闭标准输入
            except Exception as 错误:#关闭失败只记诊断
                self._stderr_lines.append(f"stdin close failed: {错误}")#记录stdin关闭失败
        if 进程.poll() is None:#进程仍在运行
            try:#发送SIGTERM/terminate
                进程.terminate()#请求终止
            except ProcessLookupError:#进程已消失则忽略
                pass#吞掉查找失败
        try:#等待进程在超时内退出
            进程.wait(timeout=self.config.shutdown_timeout_seconds)#带超时等待
        except subprocess.TimeoutExpired:#超时则强杀
            进程.kill()#强制杀死
            进程.wait()#再等到真正退出
        self._proc=None#清空进程句柄
        self.失败等待者(self.运行时关闭错误("DeepSeek Harness runtime closed"))#唤醒所有等待者为关闭错误
        if self._reader_thread and self._reader_thread.is_alive():#读取线程仍活着
            self._reader_thread.join(timeout=0.5)#短暂等待其结束
        if self._stderr_thread and self._stderr_thread.is_alive():#stderr线程仍活着
            self._stderr_thread.join(timeout=0.5)#短暂等待其结束

    def 初始化(#向运行时发送initialize并返回响应
        self,#当前客户端
        *,#之后参数仅关键字
        cwd:str,#会话工作目录
        provider:str,#模型提供方
        model:str,#模型名
        max_tokens:int|None=None,#可选最大token
    )->初始化响应:#返回校验后的初始化响应
        载荷:JSON对象={#组装initialize参数
            "cwd":str(Path(cwd).resolve()),#绝对工作目录
            "provider":provider,#提供方
            "model":model,#模型
        }#基础载荷结束
        if max_tokens is not None:#若指定了max_tokens
            载荷["maxTokens"]=max_tokens#写入驼峰字段
        try:#initialize失败时关闭进程再抛出
            return self.请求("initialize",载荷,response_model=初始化响应)#发请求并校验
        except BaseException:#任意失败都先关闭
            self.关闭()#回收半初始化状态
            raise#原样抛出

    def session_prompt(#发送session/prompt并返回messageId
        self,#当前客户端
        session_id:str,#目标会话id
        content_blocks:list[JSON对象],#内容块列表
        *,#之后参数仅关键字
        on_notification:Callable[[通知消息],None]|None=None,#可选通知回调
        notification_subscription:"通知订阅|None"=None,#可选已有订阅
    )->str:#返回服务端分配的消息id
        载荷:JSON对象={"sessionId":session_id,"contentBlocks":content_blocks}#组装提示载荷
        响应结果=self.请求(#发session/prompt请求
            "session/prompt",#方法名
            载荷,#参数
            response_model=_SessionPromptResponse,#响应模型
            on_notification=on_notification,#透传回调
            notification_filter=self._notification_belongs_to_session_tree(session_id),#按会话树过滤
            notification_subscription=notification_subscription,#透传已有订阅
        )#request结束
        return 响应结果.messageId#返回消息id字符串

    def 请求(#发送带响应的JSON-RPC请求并校验为指定模型
        self,#当前客户端
        method:str,#方法名
        params:JSON对象|None,#参数对象，可为None
        *,#之后参数仅关键字
        response_model:type[ModelT],#期望的响应模型类
        timeout_seconds:float|None=None,#可选覆盖超时
        on_notification:Callable[[通知消息],None]|None=None,#可选通知回调
        notification_filter:NotificationFilter|None=None,#可选临时订阅过滤器
        notification_subscription:"通知订阅|None"=None,#可选已有订阅
    )->ModelT:#返回校验后的响应模型实例
        结果=self.原始请求(#先取原始JSON结果
            method,#方法名
            params,#参数
            timeout_seconds=timeout_seconds,#超时
            on_notification=on_notification,#回调
            notification_filter=notification_filter,#过滤器
            notification_subscription=notification_subscription,#订阅
        )#原始请求结束
        if not isinstance(结果,dict):#响应必须是JSON对象
            raise TypeError(f"{method} response must be a JSON object")#类型错误
        return response_model.model_validate(结果)#用Pydantic校验并返回

    def 通知(self,method:str,params:JSON对象|None=None)->None:#发送无响应的JSON-RPC通知
        消息:JSON对象={"jsonrpc":"2.0","method":method}#组装通知信封
        if params is not None:#若有参数
            消息["params"]=params#写入params
        self.写消息(消息)#写入stdin

    def 下一个通知(self)->通知消息:#从全局通知队列取下一条
        项=self._notifications.get()#阻塞取出
        if isinstance(项,BaseException):#队列里可能是失败异常
            raise 项#抛出传输/运行时错误
        return 项#返回通知

    def 订阅通知(#创建带可选过滤器的通知订阅
        self,#当前客户端
        notification_filter:NotificationFilter|None=None,#可选过滤器
    )->"通知订阅":#返回可上下文管理的订阅对象
        订阅标识=str(uuid.uuid4())#生成订阅id
        通知队列:queue.Queue[通知消息|BaseException]=queue.Queue()#该订阅的私有队列
        with self._lock:#加锁登记订阅
            self._notification_subscribers[订阅标识]=(通知队列,notification_filter)#写入订阅表
        return 通知订阅(self,订阅标识,通知队列)#包装为订阅对象

    def 订阅会话通知(self,session_id:str)->"通知订阅":#订阅某会话及其子会话通知
        """订阅某会话以及从子智能体生命周期边发现的后代会话通知。"""#说明会话树语义
        return self.订阅通知(self._notification_belongs_to_session_tree(session_id))#用会话树过滤器订阅

    def 下一个请求(self)->入站请求:#取下一条运行时入站请求
        项=self._requests.get()#阻塞取出
        if isinstance(项,BaseException):#可能是关闭异常
            raise 项#抛出错误
        return 项#返回入站请求

    def 响应(self,request_id:str|int,result:JSON数据)->None:#对入站请求写成功结果
        self.写消息({"jsonrpc":"2.0","id":request_id,"result":result})#写结果响应

    def 响应错误(#对入站请求写错误响应
        self,#当前客户端
        request_id:str|int,#对应请求id
        *,#之后参数仅关键字
        code:int,#错误码
        message:str,#错误消息
        data:JSON数据|None=None,#可选错误数据
    )->None:#无返回值
        错误:JSON对象={"code":code,"message":message}#组装错误对象
        if data is not None:#若有附加数据
            错误["data"]=data#写入data字段
        self.写消息({"jsonrpc":"2.0","id":request_id,"error":错误})#写错误响应

    def 原始请求(#发送请求并等待原始JSON结果，期间可排空通知
        self,#当前客户端
        method:str,#方法名
        params:JSON对象|None=None,#参数
        *,#之后参数仅关键字
        timeout_seconds:float|None=None,#可选超时覆盖
        on_notification:Callable[[通知消息],None]|None=None,#可选通知回调
        notification_filter:NotificationFilter|None=None,#临时订阅过滤器
        notification_subscription:"通知订阅|None"=None,#已有订阅
    )->JSON数据:#返回原始result值
        请求标识=str(uuid.uuid4())#生成本次请求id
        等待者:queue.Queue[JSON数据|BaseException]=queue.Queue(maxsize=1)#单槽响应等待队列
        临时订阅:通知订阅|None=None#本请求临时创建的订阅
        订阅=notification_subscription#优先使用调用方订阅
        with self._lock:#加锁登记waiter
            self._responses[请求标识]=等待者#挂到响应表
        if on_notification is not None and 订阅 is None:#需要回调但未给订阅
            临时订阅=self.订阅通知(notification_filter)#创建临时订阅
            订阅=临时订阅#后续用临时订阅排空
        try:#写请求，失败则清理waiter与临时订阅
            消息:JSON对象={"jsonrpc":"2.0","id":请求标识,"method":method}#组装请求信封
            if params is not None:#若有参数
                消息["params"]=params#写入params
            self.写消息(消息)#发到stdin
        except BaseException:#写入失败
            with self._lock:#加锁移除waiter
                self._responses.pop(请求标识,None)#避免泄漏
            if 临时订阅 is not None:#若建了临时订阅
                临时订阅.关闭()#立刻退订
            raise#原样抛出
        超时=self.config.request_timeout_seconds if timeout_seconds is None else timeout_seconds#解析有效超时
        截止=None if 超时 is None else time.monotonic()+超时#计算截止时间
        try:#循环等待响应，期间可选排空通知
            while True:#直到拿到waiter中的项
                if on_notification is not None and 订阅 is not None:#有回调则先排空
                    订阅.清空(on_notification)#非阻塞消费已到通知
                等待超时=None#默认无限等待
                if on_notification is not None:#有回调时用短轮询以便继续排空
                    等待超时=0.05#50毫秒轮询间隔
                if 截止 is not None:#设置了超时
                    剩余=截止-time.monotonic()#剩余时间
                    if 剩余<=0:#已超时
                        with self._lock:#移除waiter
                            self._responses.pop(请求标识,None)#避免迟到响应入队
                        诊断=self.运行时诊断()#收集诊断信息
                        后缀=f"\n{诊断}" if 诊断 else ""#附加诊断后缀
                        raise TimeoutError(#抛出带方法名的超时
                            f"{method} timed out waiting for DeepSeek Harness runtime{后缀}"
                        )#超时错误结束
                    等待超时=剩余 if 等待超时 is None else min(等待超时,剩余)#取更小等待上限
                try:#尝试从waiter取响应
                    项=等待者.get(timeout=等待超时)#可能阻塞到超时
                    if on_notification is not None and 订阅 is not None:#响应到达后再排空一次
                        订阅.清空(on_notification)#避免尾部通知滞留
                    break#拿到结果跳出循环
                except queue.Empty:#本轮未等到响应
                    continue#继续循环并再次排空通知
        except BaseException:#等待阶段失败
            with self._lock:#清理waiter
                self._responses.pop(请求标识,None)#移除登记
            if 临时订阅 is not None:#关闭临时订阅
                临时订阅.关闭()#退订
            raise#原样抛出
        finally:#无论成败，临时订阅都要关闭
            if 临时订阅 is not None:#有临时订阅
                临时订阅.关闭()#保证退订
        if isinstance(项,BaseException):#响应槽里是异常
            raise 项#抛给调用方
        return 项#返回原始JSON结果

    def 写消息(self,message:JSON对象)->None:#把一条JSON对象写成NDJSON行到stdin
        进程=self._proc#取当前进程
        if 进程 is None or 进程.stdin is None:#未运行或无stdin
            raise 传输层关闭错误("DeepSeek Harness runtime is not running")#传输已关闭
        try:#序列化并写入
            载荷=json.dumps(message,separators=(",",":"))+"\n"#紧凑JSON加换行
            with self._write_lock:#串行化写入
                进程.stdin.write(载荷)#写一行
                进程.stdin.flush()#立刻刷出
        except Exception as 错误:#写失败包装为传输关闭
            raise self.运行时关闭错误("Failed to write to DeepSeek Harness runtime") from 错误#附带诊断

    def 启动读取线程(self)->None:#启动stdout读取守护线程
        self._reader_thread=threading.Thread(target=self.读取循环,name="dsh-runtime-reader",daemon=True)#创建读取线程
        self._reader_thread.start()#启动线程

    def 启动错误读取线程(self)->None:#启动stderr读取守护线程
        self._stderr_thread=threading.Thread(target=self.错误读取循环,name="dsh-runtime-stderr",daemon=True)#创建stderr线程
        self._stderr_thread.start()#启动线程

    def 读取循环(self)->None:#持续读取stdout行并分发消息
        进程=self._proc#取进程引用
        if 进程 is None or 进程.stdout is None:#无stdout则退出
            return#无法读取
        try:#按行读直到流结束或异常
            for 行 in 进程.stdout:#迭代每一行NDJSON
                if not 行.strip():#跳过空行
                    continue#下一行
                try:#尝试解析JSON
                    消息=json.loads(行)#反序列化
                except json.JSONDecodeError:#非法JSON忽略
                    continue#继续读下一行
                self.处理消息(消息)#分发到响应/请求/通知路径
        except BaseException as 错误:#读取循环异常
            self.失败等待者(错误)#让等待者失败
        finally:#无论正常或异常结束都通知关闭
            self.失败等待者(self.运行时关闭错误("DeepSeek Harness runtime stdout closed"))#stdout关闭错误

    def 错误读取循环(self)->None:#持续把stderr行写入有界缓冲
        进程=self._proc#取进程引用
        if 进程 is None or 进程.stderr is None:#无stderr则退出
            return#无法读取
        for 行 in 进程.stderr:#逐行读取stderr
            self._stderr_lines.append(行.rstrip())#去掉行尾空白后入队

    def 处理消息(self,message:object)->None:#根据JSON-RPC信封类型分发消息
        if not isinstance(message,dict):#非对象忽略
            return#直接返回
        消息标识=message.get("id")#取可选id
        方法=message.get("method")#取可选method
        if isinstance(消息标识,(str,int)) and isinstance(方法,str):#有id且有method：入站请求
            参数=message.get("params")#取参数
            self._requests.put(入站请求(id=消息标识,method=方法,payload=参数 if isinstance(参数,dict) else {}))#入队入站请求
            return#处理完毕
        if isinstance(消息标识,(str,int)):#仅有id：响应
            with self._lock:#加锁取出waiter
                等待者=self._responses.pop(str(消息标识),None)#按字符串id查找
            if 等待者 is None:#没有对应等待者
                return#丢弃迟到/未知响应
            if isinstance(message.get("error"),dict):#错误响应
                错误对象=message["error"]#取出错误对象
                等待者.put(JSON_RPC错误(_int_or_none(错误对象.get("code")),str(错误对象.get("message","JSON-RPC error")),错误对象.get("data")))#放入JSON-RPC错误
            else:#成功响应
                等待者.put(message.get("result"))#放入result字段
            return#处理完毕
        if isinstance(方法,str):#仅有method：通知
            参数=message.get("params")#取参数
            通知项=通知消息(method=方法,payload=参数 if isinstance(参数,dict) else {})#构造通知
            with self._lock:#加锁记录会话关系并快照订阅者
                self.记录会话关系(通知项)#从subagent通知更新亲子表
                订阅者们=list(self._notification_subscribers.items())#快照订阅列表
            已投递=False#是否至少投递给一个订阅
            for 订阅标识,(订阅者,谓词) in 订阅者们:#遍历每个订阅
                try:#评估过滤器
                    匹配=谓词 is None or 谓词(通知项)#无过滤器或谓词为真
                except BaseException as 错误:#过滤器抛错则移除该订阅并投递异常
                    with self._lock:#加锁确认并移除
                        当前=self._notification_subscribers.get(订阅标识)#再取当前登记
                        if 当前 is not None and 当前[0] is 订阅者:#仍是同一队列
                            self._notification_subscribers.pop(订阅标识,None)#退订坏订阅
                    订阅者.put(错误)#把异常放入订阅队列
                    continue#处理下一个订阅
                if 匹配:#匹配则投递
                    订阅者.put(通知项)#放入订阅队列
                    已投递=True#标记已投递
            if not 已投递:#没有任何订阅接收
                self._notifications.put(通知项)#落入全局通知队列

    def 失败等待者(self,exc:BaseException)->None:#让所有响应与订阅等待者收到同一异常
        with self._lock:#加锁快照并清空表
            等待者们=list(self._responses.values())#快照响应等待队列
            self._responses.clear()#清空响应表
            订阅者们=list(self._notification_subscribers.values())#快照订阅
            self._notification_subscribers.clear()#清空订阅表
        for 等待者 in 等待者们:#唤醒每个响应等待者
            等待者.put(exc)#放入异常
        for 订阅者,_谓词 in 订阅者们:#唤醒每个订阅队列
            订阅者.put(exc)#放入异常
        self._notifications.put(exc)#全局通知队列也放入异常
        self._requests.put(exc)#入站请求队列也放入异常

    def 运行时关闭错误(self,reason:str)->传输层关闭错误:#构造带诊断信息的传输关闭错误
        诊断=self.运行时诊断()#收集可用诊断
        return 传输层关闭错误(f"{reason}\n{诊断}" if 诊断 else reason)#有诊断则拼到消息后

    def 运行时诊断(self)->str:#返回子进程状态与stderr尾部，供失败诊断
        """返回传输失败与超时时可用的子进程状态信息。"""#说明用途
        进程=self._proc#取进程引用
        if (#进程已退出但stderr线程可能还在刷尾部
            进程 is not None#有进程
            and 进程.poll() is not None#已退出
            and self._stderr_thread is not None#有stderr线程
            and self._stderr_thread.is_alive()#线程仍活着
            and threading.current_thread() is not self._stderr_thread#避免自join
        ):#条件满足则短暂等待stderr刷完
            self._stderr_thread.join(timeout=0.1)#最多等0.1秒

        部分:list[str]=[]#诊断片段列表
        if 进程 is not None:#有进程句柄
            退出码=进程.poll()#取退出码，未退出为None
            if 退出码 is not None:#已退出
                部分.append(f"exit code: {退出码}")#记录退出码
        if self._stderr_lines:#有stderr缓冲
            部分.append("stderr tail:\n"+"\n".join(self._stderr_lines))#拼接stderr尾部
        return "\n".join(部分)#合并为单字符串

    def 默认启动参数(self)->tuple[str,...]:#解析默认启动参数元组
        if self.config.runtime_bin is not None:#显式runtime优先
            return (self.config.runtime_bin,)#单元素可执行路径
        if self.config.bridge_bin is not None:#其次兼容bridge
            return (self.config.bridge_bin,)#单元素桥接路径
        try:#尝试从捆绑运行时包解析
            from .runtime import resolve_bundled_launch_args#导入捆绑启动解析
        except ImportError as 错误:#未安装运行时包
            raise FileNotFoundError(#提示安装或显式配置
                "Unable to locate the bundled DeepSeek Harness SDK runtime. "
                "Install deepseek-harness-runtime-bin or set Harness配置.runtime_bin."
            ) from 错误#保留导入错误链
        return resolve_bundled_launch_args()#返回捆绑启动argv

    def 注入捆绑默认配置(self,env:dict[str,str])->None:#捆绑启动且无配置时注入默认cordis路径
        """为无非空配置的捆绑启动注入默认配置。

        两种捆绑载体都要求显式配置。显式runtime、启动参数与配置通道保持不动。
        """#说明何时注入、何时不动
        使用捆绑运行时=(#判定是否走捆绑默认启动路径
            self.config.launch_args_override is None#未覆盖启动参数
            and self.config.runtime_bin is None#未指定runtime
            and self.config.bridge_bin is None#未指定bridge
        )#捆绑判定结束
        if not 使用捆绑运行时 or env.get("DSH_CORDIS_CONFIG"):#非捆绑或已有配置则跳过
            return#不注入
        #默认启动参数已导入该包，否则会抛出安装缺失错误
        from .runtime import bundled_default_config_path#导入默认配置路径解析

        env["DSH_CORDIS_CONFIG"]=str(bundled_default_config_path())#写入默认cordis绝对路径

    def 取消订阅通知(self,subscription_id:str)->None:#按订阅id退订
        with self._lock:#加锁
            self._notification_subscribers.pop(subscription_id,None)#移除订阅项

    def 记录会话关系(self,notification:通知消息)->None:#在已持锁前提下记录子智能体会话亲子关系
        if notification.method!="subagent.started":#只关心子智能体启动通知
            return#其他通知忽略
        父标识=notification.payload.get("parentSessionId")#取父会话id
        子标识=notification.payload.get("childSessionId")#取子会话id
        if (#两边都是非空字符串且不相同
            isinstance(父标识,str)#父id是字符串
            and 父标识#父id非空
            and isinstance(子标识,str)#子id是字符串
            and 子标识#子id非空
            and 父标识!=子标识#避免自环
        ):#条件成立则记录
            self._session_parents[子标识]=父标识#子指向父

    def _notification_belongs_to_session_tree(self,session_id:str)->NotificationFilter:#构造“属于该会话树”的过滤器
        def 属于(通知项:通知消息)->bool:#闭包：判断单条通知是否属于根会话树
            载荷=通知项.payload#取载荷
            if 通知项.method in {"subagent.started","subagent.finished"}:#子智能体生命周期通知
                父标识=载荷.get("parentSessionId")#取父会话
                if (#父会话是根或其后代则匹配
                    isinstance(父标识,str)#父id是字符串
                    and self.会话是否后代(父标识,session_id)#父在根树内
                ):#匹配
                    return True#属于该树
                return 载荷.get("childSessionId")==session_id#或子会话就是根
            相关标识=载荷.get("sessionId")#普通通知看sessionId
            return (#sessionId是根或其后代
                isinstance(相关标识,str)#必须是字符串
                and self.会话是否后代(相关标识,session_id)#在会话树内
            )#返回是否匹配

        return 属于#返回闭包过滤器

    def 会话是否后代(self,session_id:str,root_session_id:str)->bool:#判断session是否等于根或沿亲子链上溯到根
        当前=session_id#从当前会话开始上溯
        已访问:set[str]=set()#已访问集合，防止环
        while 当前 not in 已访问:#尚未形成环
            if 当前==root_session_id:#命中根
                return True#是后代（含自身）
            已访问.add(当前)#标记已访问
            父=self._session_parents.get(当前)#查父会话
            if 父 is None:#没有父则到顶
                return False#不在该树
            当前=父#继续上溯
        return False#检测到环，视为不匹配

class 通知订阅:#客户端通知订阅的上下文管理包装
    def __init__(#保存客户端、订阅id与私有队列
        self,#当前订阅
        client:Harness客户端,#所属客户端
        subscription_id:str,#订阅标识
        notifications:queue.Queue[通知消息|BaseException],#私有通知队列
    )->None:#无返回值
        self._client=client#所属客户端
        self._subscription_id=subscription_id#订阅id
        self._notifications=notifications#私有队列
        self._closed=False#是否已关闭

    def __enter__(self)->"通知订阅":#进入上下文返回自身
        return self#供with使用

    def __exit__(self,_exc_type,_exc,_tb)->None:#退出上下文时关闭
        self.关闭()#退订

    def 关闭(self)->None:#幂等退订
        if self._closed:#已关闭则跳过
            return#直接返回
        self._closed=True#标记已关闭
        self._client.取消订阅通知(self._subscription_id)#从客户端移除订阅

    def 下一个(self)->通知消息:#阻塞取下一条匹配通知
        项=self._notifications.get()#从私有队列取出
        if isinstance(项,BaseException):#可能是失败异常
            raise 项#抛出
        return 项#返回通知

    def 清空(self,on_notification:Callable[[通知消息],None])->None:#非阻塞排空当前已到通知
        while True:#直到队列空
            try:#尝试立刻取一条
                项=self._notifications.get_nowait()#非阻塞get
            except queue.Empty:#空则结束
                return#排空完成
            if isinstance(项,BaseException):#队列里是异常
                raise 项#抛出
            on_notification(项)#交给回调处理


class _SessionPromptResponse(BaseModel):#session/prompt响应模型
    messageId:str#服务端返回的消息id


class 关闭响应(BaseModel):#shutdown响应模型，无字段
    pass#空模型仅用于校验对象存在


def _int_or_none(value:object)->int|None:#把值收窄为int或None
    return value if isinstance(value,int) else None#非int一律当None
