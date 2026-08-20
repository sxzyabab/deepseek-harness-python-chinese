"""本地 LSP 提供方在宿主 I/O、队列与协议阶段共用的取消辅助。"""
import threading#中止竞态线程
from timeout import 取超时,取已中止,取原因值,等待中止#超时分类与信号读写
from cordis.工具 import 承诺,是否thenable#承诺与可等待判定

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 中止错误(信号):#把中止信号转成可抛出的Error
    """构造携带信号 reason 的中止 Error，并保留超时分类。"""
    超时=取超时(信号)#尝试取出超时分类
    if 超时 is not None:#有超时原因则原样返回
        return 超时#超时原因
    原因=取原因值(信号)#取出信号上的任意reason
    if isinstance(原因,BaseException):#已是异常则直接使用
        return 原因#原样
    return Exception('LSP query aborted')#否则构造通用中止错误

def 若已中止则抛(信号=None):#已中止则立刻抛错
    """信号已经触发时，抛出该信号的已分类中止错误。"""
    if 信号 is not None and 取已中止(信号):#信号已触发
        raise 中止错误(信号)#抛出分类后的中止错误

def 可中止等待(工作,信号=None):#可被查询信号放弃等待的竞态
    """等待工作完成，同时允许查询信号放弃等待；底层工作仍保留自己的处理，并继续到其所有者定义的静止边界。"""
    if 信号 is None:#无信号则直接跑原工作
        return 解开(工作)#同步解开
    if 取已中止(信号):#已中止则立刻拒绝
        raise 中止错误(信号)#分类中止
    结果承诺=承诺()#竞态结果
    状态={'完成':False}#只结算一次
    锁=threading.Lock()#结算互斥

    def 结算成功(值):#工作先到
        """工作先完成时兑现。"""
        with 锁:#互斥
            if 状态['完成']:#已结算
                return#忽略
            状态['完成']=True#标记
        结果承诺.兑现(值)#兑现

    def 结算失败(错误):#失败先到
        """失败或中止时拒绝。"""
        with 锁:#互斥
            if 状态['完成']:#已结算
                return#忽略
            状态['完成']=True#标记
        结果承诺.拒绝(错误 if isinstance(错误,BaseException) else Exception(str(错误)))#拒绝

    def 跑工作():#后台等原工作
        """等待原工作并结算。"""
        try:#跑工作
            值=解开(工作)#等待
            结算成功(值)#成功
        except BaseException as 错误:#工作拒绝
            规范=错误 if isinstance(错误,BaseException) else Exception(str(错误))#规范成异常
            结算失败(规范)#失败

    def 盯中止():#后台等中止
        """信号中止时拒绝竞态。"""
        等待中止(信号)#阻塞到中止
        结算失败(中止错误(信号))#用分类中止拒绝

    threading.Thread(target=跑工作,daemon=True).start()#跑工作
    threading.Thread(target=盯中止,daemon=True).start()#盯中止
    return 结果承诺.等待()#交给调用方（同步等待竞态）
