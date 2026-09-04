"""原生 Node Runtime 通知上的 ConsoleBackend 实现。"""
#对齐上游 worker/realms/host/console.ts

from ......内核.智能体循环.辅助 import 解开#可等待则等待
from .桥接 import Host通知通道#通知通道

__all__=['Host控制台后端']#仅中文公开名

控制台类型=frozenset([#Console类型集
    'log','debug','info','error','warning','dir','dirxml','table','trace','clear',#常用
    'startGroup','startGroupCollapsed','endGroup','assert','profile','profileEnd','count','timeEnd',#分组等
])#CONSOLE_TYPES结束

class Host控制台后端:#Host Console后端
    """将原生 Runtime 通知转换为 realm 中立的 Console 事件。"""
    def __init__(自身,目标,运行时):#构造
        """装配通知通道。"""
        自身.目标=目标#会话
        自身.运行时=运行时#Runtime
        自身._事件=Host通知通道(#通道
            目标,#会话
            lambda 消息:消息.get('method') in ('Runtime.consoleAPICalled','Runtime.exceptionThrown'),#过滤
            自身._投影,#投影
        )#通道结束

    def _投影(自身,消息):#投影
        """按方法投影事件。"""
        if 消息.get('method')=='Runtime.consoleAPICalled':#Console
            return 自身._控制台事件(消息.get('params'))#Console
        return 自身._异常事件(消息.get('params'))#异常

    def 订阅(自身,监听):#订阅
        """订阅原生 Console 与异常事件。"""
        return 自身._事件.订阅(监听)#委托

    def 清空(自身):#清空
        """丢弃 Console 条目。"""
        解开(自身.目标.请求('Runtime.discardConsoleEntries',{}))#丢弃条目

    def 关闭(自身):#关闭
        """释放原生通知订阅。"""
        自身._事件.关闭()#关通道

    def _控制台事件(自身,参数):#Console事件
        """投影 consoleAPICalled。"""
        参数=参数 or {}#参数
        类型=参数.get('type')#类型
        参数列表=参数.get('args')#参数列表
        时间戳=参数.get('timestamp')#时间戳
        if 类型 not in 控制台类型 or not isinstance(参数列表,list) or not isinstance(时间戳,(int,float)):#无效
            return None#无
        参数对象=[]#参数对象
        for 值 in 参数列表:#扫
            参数对象.append(解开(自身.运行时.远程对象(值)))#转换
        事件={'type':类型,'arguments':参数对象,'timestamp':时间戳}#载荷
        if isinstance(参数.get('executionContextId'),(int,float)):#上下文
            事件['contextId']=参数['executionContextId']#写入
        栈=参数.get('stackTrace')#栈
        if isinstance(栈,dict):#有栈
            事件['stackTrace']=自身.运行时.栈跟踪(栈)#转换
        return {'type':'console-api','event':事件}#事件

    def _异常事件(自身,参数):#异常事件
        """投影 exceptionThrown。"""
        参数=参数 or {}#参数
        时间戳=参数.get('timestamp')#时间
        异常详情=参数.get('exceptionDetails')#异常详情
        if not isinstance(时间戳,(int,float)) or 异常详情 is None:#无效
            return None#无
        事件={'timestamp':时间戳,'details':解开(自身.运行时.异常详情(异常详情))}#载荷
        if isinstance(参数.get('executionContextId'),(int,float)):#上下文
            事件['contextId']=参数['executionContextId']#写入
        return {'type':'exception','event':事件}#事件
