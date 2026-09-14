import threading#中止竞态线程
from concurrent.futures import Future as 原生结果#单次操作结果
from ...工具.超时 import 取超时,已中止,若已中止则抛出,等待中止#超时分类与中止入口
from ..语言服务器 import 语言服务器错误#本缝异常基类

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身.未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if 自身.未来.done() is False:#尚未结算
            自身.未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if 自身.未来.done() is False:#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身.未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身.未来.set_exception(语言服务器错误('任务被拒绝','LSP_INTERNAL'))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身.未来.result(timeout=超时)#取结果或抛错

def 中止错误(信号):
    """把中止信号转成可抛出的错误，并保留超时分类。"""
    超时=取超时(信号)#尝试取出超时分类
    if 超时 is not None:#有超时原因则原样返回
        return 超时#超时原因
    return 语言服务器错误('语言服务器查询已中止','LSP_ABORTED')#通用中止

def 可中止等待(工作,信号=None):
    """等待工作完成，同时允许查询信号放弃等待；底层工作仍保留自己的处理，并继续到其所有者定义的静止边界。工作是操作任务或已有同步值。"""
    if 信号 is None:#无信号则直接取结果
        if isinstance(工作,操作任务):#任务
            return 工作.等待()#等待
        return 工作#同步值
    if 已中止(信号):#已中止则立刻拒绝
        raise 中止错误(信号)#分类中止
    结果任务=操作任务()#竞态结果
    状态={'完成':False}#只结算一次
    锁=threading.Lock()#结算互斥

    def 结算成功(值):
        """工作先完成时兑现。"""
        with 锁:#互斥
            if 状态['完成']:#已结算
                return#忽略
            状态['完成']=True#标记
        结果任务.兑现(值)#兑现

    def 结算失败(错误):
        """失败或中止时拒绝。"""
        with 锁:#互斥
            if 状态['完成']:#已结算
                return#忽略
            状态['完成']=True#标记
        if isinstance(错误,BaseException):#已是异常
            结果任务.拒绝(错误)#拒绝
        else:#非异常
            结果任务.拒绝(语言服务器错误(str(错误),'LSP_INTERNAL'))#拒绝

    def 执行工作():
        """等待原工作并结算。"""
        try:#执行工作
            if isinstance(工作,操作任务):#任务
                值=工作.等待()#等待
            else:#同步值
                值=工作#原样
            结算成功(值)#成功
        except BaseException as 错误:#工作拒绝
            结算失败(错误)#失败

    def 转发中止():
        """信号中止时拒绝竞态。"""
        等待中止(信号)#阻塞到中止
        结算失败(中止错误(信号))#用分类中止拒绝

    工作线程=threading.Thread(target=执行工作)#执行工作
    工作线程.daemon=True#不挡住退出
    工作线程.start()#启动
    中止线程=threading.Thread(target=转发中止)#转发中止
    中止线程.daemon=True#不挡住退出
    中止线程.start()#启动
    return 结果任务.等待()#同步等待竞态
