"""Inspector Worker 的失败遏制与关闭协调。

对齐上游 `host/bridge/lifecycle.ts`。公开面仅中文名。
"""
import threading#超时与事件
from ...共享.桥接.控制编解码 import 解析检查器工作者控制#控制帧解析

__all__=['检查器工作者生命周期']#仅中文公开名

class 检查器工作者生命周期:#Worker生命周期
    """跟踪 Worker 终止，且不移除用于遏制运行时错误的监听器。"""
    def __init__(自身,工作者):#绑定Worker
        """绑定 Worker 监听。"""
        自身.工作者=工作者#Worker
        自身.退出事件=threading.Event()#退出结算
        自身.失败事件=threading.Event()#失败结算
        自身.失败=None#首个失败
        自身.退出码值=None#退出码
        自身.运行中=False#是否已标记运行
        自身.期望退出=False#是否所有者请求退出
        自身.已通知=False#是否已通知意外退出
        自身.意外退出回调=None#意外退出回调
        def 错误(错误值):#错误监听
            """错误监听。"""
            if 自身.失败 is None:#保留首错
                自身.失败=错误值#首错
            自身.失败事件.set()#结算失败
            自身.通知意外退出()#尝试通知
        def 退出(码):#退出监听
            """退出监听。"""
            自身.退出码值=码#记录码
            自身.退出事件.set()#结算退出
            自身.通知意外退出()#尝试通知
        工作者.on('error',错误)#错误监听
        工作者.once('exit',退出)#退出监听

    @property
    def 退出码(自身):#退出码访问器
        """exit 事件已触发后的 Worker 退出码。"""
        return 自身.退出码值#返回

    def 等待就绪(自身,超时毫秒):#等待就绪
        """在观察启动失败与退出的同时等待已校验的 ready 帧。"""
        结果={'ready':None,'error':None}#结果
        完成=threading.Event()#完成事件
        def 收消息(值):#处理消息
            """处理消息。"""
            try:#解析
                控制=解析检查器工作者控制(值)#校验解码
            except Exception as 错误:#解析失败
                结果['error']=错误 if isinstance(错误,Exception) else Exception(str(错误))#拒绝
                完成.set()#结束
                return#结束
            if 控制['type']=='ready':#就绪
                结果['ready']=控制#就绪
                完成.set()#结束
            elif 控制['type']=='failure':#失败帧
                结果['error']=Exception(f'inspector Worker failed: {控制["message"]}')#失败
                完成.set()#结束
        自身.工作者.on('message',收消息)#挂监听
        定时器=threading.Timer(超时毫秒/1000,lambda:(结果.__setitem__('error',Exception(f'inspector Worker did not become ready within {超时毫秒}ms')),完成.set()))#超时
        定时器.daemon=True#守护
        定时器.start()#启动
        while not 完成.is_set():#竞速
            if 自身.失败事件.wait(0.05):#失败
                结果['error']=自身.失败#失败
                break#结束
            if 自身.退出事件.wait(0.05):#提前退出
                结果['error']=Exception(f'inspector Worker exited before readiness (code {自身.退出码值})')#拒绝
                break#结束
        定时器.cancel()#清定时器
        try:#卸监听
            自身.工作者.off('message',收消息)#卸监听
        except Exception:#忽略
            pass#忽略
        if 结果['error'] is not None:#失败
            raise 结果['error']#抛出
        return 结果['ready']#就绪

    def 标记运行(自身,监听器):#标记运行
        """开始通过一个受遏制的回调报告意外运行时退出。"""
        自身.运行中=True#置运行
        自身.意外退出回调=监听器#保存回调
        自身.通知意外退出()#补通知

    def 期望退出(自身):#期望退出
        """将后续 Worker 终止标为所有者请求。"""
        自身.期望退出标志=True#置位
        自身.期望退出=True#置位

    def 终止(自身):#强制终止
        """在失败初始化期间终止 Worker。"""
        自身.期望退出()#标记期望
        if 自身.退出码值 is None:#未退出则终止
            自身.工作者.terminate()#终止

    def 停止(自身,超时毫秒):#优雅停止
        """请求优雅关闭，并在截止后强制终止。"""
        自身.期望退出()#标记期望
        if 自身.退出码值 is not None:#已退出
            return#返回
        自身.工作者.postMessage({'type':'shutdown'})#发关闭
        if 自身.退出事件.wait(超时毫秒/1000):#已退出
            return#优雅完成
        自身.工作者.terminate()#强制终止
        raise Exception(f'inspector Worker did not stop within {超时毫秒}ms and was terminated')#报告

    def 通知意外退出(自身):#通知意外退出
        """通知意外退出。"""
        if not 自身.运行中 or 自身.期望退出 or 自身.已通知 or 自身.退出码值 is None:#条件不足
            return#返回
        自身.已通知=True#只通知一次
        if 自身.意外退出回调 is not None:#回调
            自身.意外退出回调(自身.失败 or Exception(f'inspector Worker exited unexpectedly with code {自身.退出码值}'))#回调
