"""realm 迁移期间仅 Host 原生 CDP 方法的显式适配器。"""
#对齐上游 worker/cdp/domains/native.ts

from ..协议 import 响应cdp请求#协议工具

__all__=['Host原生域会话']#仅中文公开名

原生域名集合=frozenset(['Runtime','Profiler','HeapProfiler','Schema'])#原生域名集合

class Host原生域会话:#Host原生域会话
    """通过与传输无关的会话转发一个显式 Host 原生域。"""
    def __init__(自身,传输,目标):#构造
        """订阅通知并保留传输。"""
        自身.传输=传输#传输
        自身.目标=目标#后端
        自身._取消订阅=目标.订阅(自身._转发通知)#订阅通知

    def _转发通知(自身,消息):#转发通知
        """过滤后转发原生通知。"""
        方法=消息.get('method','')#方法
        if not 自身.拥有(方法):#不拥有
            return#跳过
        if 方法 in ('Runtime.consoleAPICalled','Runtime.exceptionThrown'):#别处处理
            return#跳过
        自身.传输.发送(消息)#转发通知

    def 处理(自身,请求):#处理请求
        """执行一条 Host 原生 CDP 请求并发送其关联结果。"""
        if not 自身.拥有(请求['method']):#不拥有
            return False#未拥有
        响应cdp请求(自身.传输,请求,lambda:自身.目标.请求(请求['method'],请求['params']))#响应
        return True#已拥有

    def 拥有(自身,方法):#是否拥有域
        """测试本适配器是否拥有某个 CDP 方法。"""
        点=方法.find('.')#点位置
        if 点<0:#无点
            return False#不拥有
        return 方法[:点] in 原生域名集合#域名前缀

    def 关闭(自身):#关闭
        """停止向本 DevTools 连接转发原生通知。"""
        自身._取消订阅()#取消订阅
