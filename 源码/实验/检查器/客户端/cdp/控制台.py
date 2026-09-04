"""每个活动 DevTools Runtime 会话共享的 Client Console 观测。

对齐上游 `client/cdp/console.ts`。公开面仅中文名。
"""
from .栈 import 捕获客户端控制台栈#捕获栈

__all__=['控制台桥能力','客户端控制台观察器']#仅中文公开名

方法映射=(#方法映射
    ('log','log'),('debug','debug'),('info','info'),('error','error'),('warn','warning'),#常用
    ('dir','dir'),('dirxml','dirxml'),('table','table'),('trace','trace'),('clear','clear'),#扩展
    ('group','startGroup'),('groupCollapsed','startGroupCollapsed'),('groupEnd','endGroup'),#组
    ('assert','assert'),('profile','profile'),('profileEnd','profileEnd'),('count','count'),('timeEnd','timeEnd'),#计时
)#映射结束

def 控制台桥能力():#Console桥能力
    """描述浏览器侧 Console 观测。"""
    return {'type':'client-console'}#能力

class 客户端控制台观察器:#Client Console观察器
    """包装 console 方法并向活动会话转发事件。"""
    def __init__(自身,运行时,接收器,解析脚本=None):#构造
        """保存运行时与接收器。"""
        自身.运行时=运行时#Runtime执行器
        自身.接收器=接收器#Console接收器
        自身.解析脚本=解析脚本 or (lambda _网址:None)#脚本键
        自身.会话们=set()#已启用会话
        自身.已关闭=False#是否关闭
        自身.原始={}#原方法

    def 启用(自身,会话标识):#启用会话
        """为一个 DevTools 会话开始 Console 观测。"""
        自身.会话们.add(会话标识)#登记

    def 禁用(自身,会话标识):#禁用会话
        """为一个 DevTools 会话停止 Console 观测。"""
        自身.会话们.discard(会话标识)#移除

    def 重置(自身):#重置
        """代数结束时清空会话并卸钩。"""
        自身.会话们.clear()#清空会话
        #浏览器侧卸钩由运行时绑定完成

    def 关闭(自身):#关闭
        """恢复 console 并清空会话。"""
        if 自身.已关闭:#幂等
            return#返回
        自身.已关闭=True#置位
        自身.重置()#重置

    def 转发(自身,类型,参数):#转发事件
        """向已启用会话转发。"""
        if 自身.已关闭 or len(自身.会话们)==0:#无会话
            return#返回
        import time#时间戳
        栈=捕获客户端控制台栈(自身.解析脚本)#栈
        时间戳=time.time()*1000#纪元毫秒
        for 会话标识 in list(自身.会话们):#逐会话
            事件=自身.运行时.控制台事件(会话标识,类型,参数,时间戳,栈)#序列化
            if 事件 is not None:#有事件
                自身.接收器(会话标识,事件)#投递
