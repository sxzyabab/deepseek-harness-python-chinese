"""循环用的中止通道与任务赛跑。"""
import threading#后台线程
from concurrent.futures import Future as 原生结果#单次操作结果

class 循环错误(Exception):
    """内核智能体循环包的异常基类。"""

class 中止错误(循环错误):
    """取消通道已中止。"""
    def __init__(自身,消息='aborted',种类=None):
        """用消息与可选控制流种类构造。"""
        super().__init__(消息)#错误消息原样英文
        if 种类 is not None:#有控制流种类
            自身.kind=种类#按结构识别，不做类型嗅探

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():#尚未结算
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                包装=循环错误('task rejected')#包装拒绝
                包装.原因=错误#附加信息做成属性
                自身._原生结果.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。原因用异常对象承载，不对外挂第二字段。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止标志
        自身._异常=None#中止时抛出的异常
        if 已中止标志:#创建时已中止
            自身._事件.set()#置位
            自身._异常=中止错误()#默认中止异常

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#原因已是异常
            自身._异常=原因#用异常对象承载
        elif 原因 is not None:#非异常原因
            中止异常=中止错误()#包装
            中止异常.原因=原因#附加属性
            自身._异常=中止异常#记下
        else:#无原因
            自身._异常=中止错误()#默认
        自身._事件.set()#置位

    @staticmethod
    def 任一(信号列表):
        """最先中止的那路胜出。"""
        融合=中止控制器()#融合控制器
        for 信号 in 信号列表:#先扫已中止
            if 信号 is not None and 已中止(信号):#已中止
                融合.中止(信号._异常)#立刻胜出
                return 融合.信号#已中止的融合信号
        def 转发中止(来源):
            """等到来源置位后转发给融合控制器。"""
            来源._事件.wait()#阻塞到中止
            融合.中止(来源._异常)#转发异常
        for 信号 in 信号列表:#每路一线程
            if 信号 is None:#无信号
                continue#跳过
            工作=threading.Thread(target=转发中止,args=(信号,))#转发线程
            工作.daemon=True#不挡住退出
            工作.start()#启动
        return 融合.信号#融合信号

class 中止控制器:
    """发出中止的控制器。"""
    def __init__(自身):
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:#无信号
        return#无信号
    if not 信号._事件.is_set():#仍活着
        return#仍活着
    if 信号._异常 is not None:#有承载异常
        raise 信号._异常#抛出
    raise 中止错误()#默认中止

def 包装中止错误(标识,原因):
    """把非异常原因收成创建中止错误。"""
    if isinstance(原因,BaseException):#已是异常
        return 原因#已是异常
    中止异常=循环错误('agent "'+str(标识)+'" creation aborted')#包装文案
    中止异常.原因=原因#附加属性
    return 中止异常#包装错误

def 在线程执行(函数):
    """在工作线程执行并返回任务。回调翻译时已是同步函数。"""
    任务=操作任务()#本次任务
    def 执行并结算():
        """执行函数并结算。"""
        try:
            任务.兑现(函数())#兑现同步返回值
        except BaseException as 错误:
            任务.拒绝(错误)#拒绝
    工作=threading.Thread(target=执行并结算)#工作线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 任务#操作任务

def 赛跑(任务列表):
    """最先结算的那路胜出。列表项必须是操作任务。"""
    胜出=操作任务()#赛跑结果
    锁=threading.Lock()#只结算一次
    def 等待并胜出(任务):
        """等待一路并尝试胜出。"""
        try:
            值=任务.等待()#等待操作任务
            with 锁:#只结算一次
                胜出.兑现(值)#先到先赢
        except BaseException as 错误:
            with 锁:#只结算一次
                胜出.拒绝(错误)#先到先赢
    for 任务 in 任务列表:#每路一线程
        工作=threading.Thread(target=等待并胜出,args=(任务,))#等待线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
    return 胜出.等待()#阻塞取胜者

def 全部并发(任务列表):
    """并发等待全部，一路失败则抛。列表项必须是操作任务。"""
    槽表=[操作任务() for _ in 任务列表]#每路一槽
    def 等待并写入槽(任务,槽):
        """等待一路写入槽。"""
        try:
            槽.兑现(任务.等待())#兑现
        except BaseException as 错误:
            槽.拒绝(错误)#拒绝
    for 任务,槽 in zip(任务列表,槽表):#每路一线程
        工作=threading.Thread(target=等待并写入槽,args=(任务,槽))#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
    return [槽.等待() for 槽 in 槽表]#按原序取出

def 全部结算(任务列表):
    """并发等全部落定，吞掉失败。列表项必须是操作任务。"""
    def 等待并吞错(任务):
        """等待一路并吞错。"""
        try:
            任务.等待()#等待
        except BaseException:
            pass#排空不抛
    线程表=[]#工作线程
    for 任务 in 任务列表:#每路一线程
        工作=threading.Thread(target=等待并吞错,args=(任务,))#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#等全部结束
        工作.join()#等到结束

def 与中止赛跑(操作,信号,标识):
    """等待操作任务，或在信号中止时立刻抛出其原因。"""
    if 已中止(信号):#已中止
        raise 包装中止错误(标识,信号._异常)#立刻抛
    中止侧=操作任务()#中止时拒绝
    def 监听():
        """abort 时拒绝赛跑。"""
        信号._事件.wait()#等到中止
        中止侧.拒绝(包装中止错误(标识,信号._异常))#中止原因
    工作=threading.Thread(target=监听)#监听线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 赛跑([操作,中止侧])#操作或中止

def 启动可中止操作(操作,信号,标识,拆除被弃=None):
    """启动可中止操作，并在取消后到达的值上拆除它。操作是同步回调。"""
    if 已中止(信号):#已经中止
        raise 包装中止错误(标识,信号._异常)#已经中止
    未决=在线程执行(操作)#下一线程才启动
    try:
        return 与中止赛跑(未决,信号,标识)#等待结果
    except BaseException as 错误:
        if 已中止(信号) and 拆除被弃 is not None:#取消后仍可能兑现
            def 回收被弃结果():
                """兑现则拆除，拒绝则忽略。"""
                try:
                    拆除被弃(未决.等待())#兑现则拆除
                except BaseException:
                    pass#拒绝则忽略
            收线程=threading.Thread(target=回收被弃结果)#后台回收
            收线程.daemon=True#不挡住退出
            收线程.start()#启动
        raise 错误#原错上抛
