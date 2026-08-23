"""循环用的中止、承诺赛跑与字段读取。"""
import threading#后台线程
from ..llm.类型 import 中止信号 as 基中止信号#基类取消通道
from ...依赖 import cordis#外部依赖胶水
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定

def 取(对象,名,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 名 in 对象:#自有键
            return 对象[名]#映射键
        return 缺省#缺席
    return getattr(对象,名,缺省)#对象属性

def 有自有(对象,名):#对齐 Object.hasOwn
    """对齐 Object.hasOwn。"""
    if 对象 is None:#空对象
        return False#空对象
    if isinstance(对象,dict):#映射
        return 名 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 名 in 字典#自有

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否整数(值):#对齐 JS Number.isInteger
    """对齐 JS Number.isInteger。"""
    if isinstance(值,bool):#布尔
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger。"""
    if not 是否整数(值):#非整数
        return False#非整数
    return abs(值)<=9007199254740991#53 位上限

def 已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#无信号
    if getattr(信号,'已中止',False):#中文旗标
        return True#已中止
    if getattr(信号,'aborted',False):#外来 Web 旗标
        return True#已中止
    return False#未中止

def 中止原因(信号):#取出中止原因
    """取出中止原因。"""
    if 信号 is None:#无信号
        return None#无信号
    原因=getattr(信号,'原因',None)#中文原因
    if 原因 is not None:#有中文原因
        return 原因#中文原因
    return getattr(信号,'reason',None)#外来 Web 原因

def 听中止(信号,回调):#登记一次性 abort 回调
    """登记一次性 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'加入监听'):#中文 API
        信号.加入监听('abort',回调,{'once':True})#中文 API
        return#已登记
    if hasattr(信号,'addEventListener'):#外来 Web API
        信号.addEventListener('abort',回调,{'once':True})#Web API

def 摘中止(信号,回调):#去掉 abort 回调
    """去掉 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'移除监听'):#中文 API
        信号.移除监听('abort',回调)#中文 API
        return#已摘掉
    if hasattr(信号,'removeEventListener'):#外来 Web API
        信号.removeEventListener('abort',回调)#Web API

def 抛若中止(信号):#已中止则抛出原因
    """已中止则抛出原因。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'抛若中止'):#中文 API
        信号.抛若中止()#中文 API
        return#已抛或仍活
    if hasattr(信号,'throwIfAborted'):#外来 Web API
        信号.throwIfAborted()#英文 API
        return#已抛或仍活
    if not 已中止(信号):#仍活着
        return#仍活着
    原因=中止原因(信号)#中止原因
    if isinstance(原因,BaseException):#已是异常
        raise 原因#原样抛
    错=Exception('aborted')#非异常则包装
    错.cause=原因#挂上原因
    raise 错#抛出

def 包中止错误(标识,原因):#把非异常原因收成创建中止错误
    """把非异常原因收成创建中止错误。"""
    if isinstance(原因,BaseException):#已是异常
        return 原因#已是异常
    错=Exception('agent "'+str(标识)+'" creation aborted')#包装文案
    错.cause=原因#TS 风格 cause
    return 错#包装错误

def 释放准备(准备):#释放一份会话准备
    """释放一份会话准备。"""
    if 准备 is None:#无准备
        return#无准备
    if hasattr(准备,'拆除'):#中文拆除
        准备.拆除()#中文拆除
        return#已释放
    if hasattr(准备,'dispose'):#外来拆除
        准备.dispose()#英文拆除

class 中止信号(基中止信号):#可监听的取消通道
    """可监听的取消通道。"""
    def __init__(自身,已中止旗=False):#创建一条取消通道
        """创建一条取消通道。"""
        super().__init__(已中止旗)#基类旗标
        自身.已中止=已中止旗#中止旗标
        自身.原因=None#中止原因
        自身._监听=[]#回调表
        自身._锁=threading.Lock()#并发锁

    def 触发(自身,原因=None):#标记中止并通知
        """标记中止并通知。"""
        with 自身._锁:#串行触发
            if 自身.已中止:#只触发一次
                return#已触发
            自身.已中止=True#标记
            自身.原因=原因#记下原因
            回调们=list(自身._监听)#拷贝
            自身._监听=[]#清空
        for 回调 in 回调们:#锁外通知
            回调()#通知

    def 加入监听(自身,事件名,回调,选项=None):#登记 abort 回调
        """登记 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#忽略其它
        立刻=False#是否已中止
        with 自身._锁:#串行登记
            if 自身.已中止:#已中止
                立刻=True#锁外调用
            else:#尚未中止
                自身._监听.append(回调)#登记
        if 立刻:#锁外立刻通知
            回调()#立刻通知

    def 移除监听(自身,事件名,回调):#去掉 abort 回调
        """去掉 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#忽略其它
        with 自身._锁:#串行删除
            自身._监听=[项 for 项 in 自身._监听 if 项 is not 回调]#按引用删除

    def 抛若中止(自身):#已中止则抛出原因
        """已中止则抛出原因。"""
        if not 自身.已中止:#仍活着
            return#仍活着
        原因=自身.原因#中止原因
        if isinstance(原因,BaseException):#已是异常
            raise 原因#原样抛
        错=Exception('aborted')#非异常则包装
        错.cause=原因#挂上原因
        raise 错#抛出

    @staticmethod
    def 任一(信号列表):#最先中止的那路胜出
        """最先中止的那路胜出。"""
        融合=中止控制器()#融合控制器
        for 信号 in 信号列表:#先扫已中止
            if 已中止(信号):#已中止
                融合.中止(中止原因(信号))#立刻胜出
                return 融合.信号#已中止的融合信号
        def 绑定(来源):#转发某一路中止
            """转发某一路中止。"""
            def 转发(*位置参数):#把来源原因交给融合控制器
                """把来源原因交给融合控制器。"""
                融合.中止(中止原因(来源))#转发原因
            return 转发#该路回调
        for 信号 in 信号列表:#挂监听
            听中止(信号,绑定(信号))#只听一次
        return 融合.信号#融合信号

class 中止控制器:#发出中止的控制器
    """发出中止的控制器。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 在线程跑(函数):#在工作线程执行并返回承诺
    """在工作线程执行并返回承诺。"""
    任务=承诺()#本次数
    def 跑():#执行函数并结算
        """执行函数并结算。"""
        try:#执行
            任务.兑现(解开(函数()))#兑现
        except BaseException as 错误:#失败
            任务.拒绝(错误)#拒绝
    工作=threading.Thread(target=跑)#工作线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 任务#承诺

def 赛跑(任务列表):#最先结算的那路胜出
    """最先结算的那路胜出。"""
    胜出=承诺()#赛跑结果
    锁=threading.Lock()#只结算一次
    def 盯(任务):#等待一路并尝试胜出
        """等待一路并尝试胜出。"""
        try:#等待
            值=解开(任务)#等待
            with 锁:#只结算一次
                胜出.兑现(值)#先到先赢
        except BaseException as 错误:#失败
            with 锁:#只结算一次
                胜出.拒绝(错误)#先到先赢
    for 任务 in 任务列表:#每路一线程
        工作=threading.Thread(target=盯,args=(任务,))#盯梢线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
    return 胜出.等待()#阻塞取胜者

def 全部并发(任务列表):#并发等待全部，一路失败则抛
    """并发等待全部，一路失败则抛。"""
    槽们=[承诺() for _ in 任务列表]#每路一槽
    def 盯(任务,槽):#等待一路写入槽
        """等待一路写入槽。"""
        try:#等待
            槽.兑现(解开(任务))#兑现
        except BaseException as 错误:#失败
            槽.拒绝(错误)#拒绝
    for 任务,槽 in zip(任务列表,槽们):#每路一线程
        工作=threading.Thread(target=盯,args=(任务,槽))#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
    return [槽.等待() for 槽 in 槽们]#按原序取出

def 全部结算(任务列表):#并发等全部落定，吞掉失败
    """并发等全部落定，吞掉失败。"""
    def 盯(任务):#等待一路并吞错
        """等待一路并吞错。"""
        try:#等待
            解开(任务)#等待
        except BaseException:#失败
            pass#排空不抛
    线程们=[]#工作线程
    for 任务 in 任务列表:#每路一线程
        工作=threading.Thread(target=盯,args=(任务,))#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        线程们.append(工作)#登记
    for 工作 in 线程们:#等全部结束
        工作.join()#等到结束

def 与中止赛跑(操作,信号,标识):#等待操作，或在信号中止时立刻抛出其原因
    """等待操作，或在信号中止时立刻抛出其原因。"""
    if 已中止(信号):#已中止
        raise 包中止错误(标识,中止原因(信号))#立刻抛
    中止侧=承诺()#中止时拒绝
    def 监听():#abort 时拒绝赛跑
        """abort 时拒绝赛跑。"""
        中止侧.拒绝(包中止错误(标识,中止原因(信号)))#中止原因
    听中止(信号,监听)#只听一次
    try:#赛跑
        return 赛跑([操作,中止侧])#操作或中止
    finally:#摘监听
        摘中止(信号,监听)#摘掉监听

def 与中止赛跑调用(操作,信号,标识,释放被弃=None):#启动可中止操作，并在取消后到达的值上释放它
    """启动可中止操作，并在取消后到达的值上释放它。"""
    if 已中止(信号):#已经中止
        raise 包中止错误(标识,中止原因(信号))#已经中止
    未决=在线程跑(操作)#下一线程才启动
    try:#等待结果
        return 与中止赛跑(未决,信号,标识)#等待结果
    except BaseException as 错误:#取消或失败
        if 已中止(信号) and 释放被弃 is not None:#取消后仍可能兑现
            def 收被弃():#兑现则释放，拒绝则忽略
                """兑现则释放，拒绝则忽略。"""
                try:#等待被弃值
                    释放被弃(未决.等待())#兑现则释放
                except BaseException:#拒绝
                    pass#拒绝则忽略
            收线程=threading.Thread(target=收被弃)#后台收
            收线程.daemon=True#不挡住退出
            收线程.start()#启动
        raise 错误#原错上抛

def 已兑现(值=None):#立刻兑现的承诺
    """立刻兑现的承诺。"""
    任务=承诺()#新承诺
    任务.兑现(值)#立刻成功
    return 任务#已完成
