from threading import Event as 事件#完成门
from queue import Empty as 空队列,Queue as 队列#跨线程一次结果
from ...基础设施.通用工具 import (
    中止信号,中止控制器,已中止,若已中止则抛出,启动守护线程,
)
from .异常 import 循环错误

def 包装中止错误(标识,原因):
    '把非异常原因收成创建中止错误'
    if isinstance(原因,BaseException):#已是异常
        return 原因#已是异常
    中止异常=循环错误('智能体 "'+str(标识)+'" 创建已中止')#包装文案
    中止异常.原因=原因#附加属性
    return 中止异常#包装错误

def 已决议队列(值=None):
    '立刻落定的 Queue(1)'
    结果队列=队列(1)#跨线程一次结果
    结果队列.put(('ok',值))#立刻成功
    return 结果队列#Queue(1)

def 放入成功(结果队列,值=None):
    '成功写入 Queue(1)'
    结果队列.put(('ok',值))#成功
    return 值#返回值

def 放入失败(结果队列,错误):
    '失败写入 Queue(1)；非异常则包成循环错误'
    if isinstance(错误,BaseException):#已是异常
        结果队列.put(('err',错误))#原样
        return
    包装=循环错误('任务被拒绝')#包装拒绝
    包装.原因=错误#附加信息
    结果队列.put(('err',包装))#包装失败

def 在线程执行(函数):
    '在工作线程执行，经 Queue(1) 交回结果；调用方 等待队列结果'
    结果队列=队列(1)#跨线程一次结果
    def 执行并放入():
        '执行函数并放入队列'
        try:
            放入成功(结果队列,函数())#成功
        except BaseException as 错误:
            放入失败(结果队列,错误)#失败原样
    启动守护线程(执行并放入)#工作线程
    return 结果队列#Queue(1)

def 等待队列结果(结果队列):
    '阻塞取出 Queue(1) 结果；失败原样抛'
    种类,载荷=结果队列.get()#阻塞取
    if 种类=='err':#失败
        raise 载荷#原样抛
    return 载荷#成功值

def 全部并发执行(函数列表):
    '扇出：每路一线程，join 后按原序取结果；一路失败则抛'
    结果表=[None]*len(函数列表)#按原序结果
    错误表=[None]*len(函数列表)#按原序错误
    def 跑一路(下标,函数):
        '执行一路并写入表'
        try:
            结果表[下标]=函数()#成功
        except BaseException as 错误:
            错误表[下标]=错误#记下
    线程表=[]#工作线程
    for 下标,函数 in enumerate(函数列表):#每路一线程
        工作=启动守护线程(跑一路,下标,函数)#工作线程
        线程表.append(工作)#登记
    for 工作 in 线程表:#扇出 join
        工作.join()#等到结束
    for 错误 in 错误表:#按原序检查
        if 错误 is not None:#有失败
            raise 错误#原样抛
    return 结果表#按原序结果

def 全部等待(队列列表):
    '等全部 Queue 落定；一路失败则抛'
    结果表=[None]*len(队列列表)#按原序结果
    错误表=[None]*len(队列列表)#按原序错误
    def 跑一路(下标,结果队列):
        '等待一路并写入表'
        try:
            结果表[下标]=等待队列结果(结果队列)#成功
        except BaseException as 错误:
            错误表[下标]=错误#记下
    线程表=[]#工作线程
    for 下标,结果队列 in enumerate(队列列表):#每路一线程
        工作=启动守护线程(跑一路,下标,结果队列)#工作线程
        线程表.append(工作)#登记
    for 工作 in 线程表:#扇出 join
        工作.join()#等到结束
    for 错误 in 错误表:#按原序检查
        if 错误 is not None:#有失败
            raise 错误#原样抛
    return 结果表#按原序结果

def 全部排空队列(队列列表):
    '并发等全部 Queue 落定，吞掉失败'
    def 等待并吞错(结果队列):
        '等待一路并吞错'
        try:
            等待队列结果(结果队列)#等待
        except BaseException:
            pass#排空不抛
    线程表=[]#工作线程
    for 结果队列 in 队列列表:#每路一线程
        工作=启动守护线程(等待并吞错,结果队列)#工作线程
        线程表.append(工作)#登记
    for 工作 in 线程表:#等全部结束
        工作.join()#等到结束

def 赛跑取值(队列列表):
    '最先落定的那路值胜出；失败原样抛'
    胜出=队列(1)#胜出路
    已取=事件()#只取一路
    def 等一路(结果队列):
        '等待一路并竞选'
        try:
            值=等待队列结果(结果队列)#等待
        except BaseException as 错误:
            if not 已取.is_set():#首路
                已取.set()#占住
                放入失败(胜出,错误)#失败胜出
            return
        if not 已取.is_set():#首路
            已取.set()#占住
            放入成功(胜出,值)#成功胜出
    for 结果队列 in 队列列表:#每路一线程
        启动守护线程(等一路,结果队列)#等待线程
    return 等待队列结果(胜出)#胜出值

def 启动可中止操作(操作,信号,标识,回收已放弃结果=None):
    """在线程跑操作；与中止信号赛跑，中止胜出则抛。
    操作是同步回调"""
    if 已中止(信号):#已经中止
        raise 包装中止错误(标识,信号.原因)#已经中止
    结果队列=队列(1)#跨线程一次结果
    已放弃=事件()#调用方已因中止放弃
    def 执行并放入():
        '执行函数并放入或回收'
        try:
            值=操作()#同步执行
        except BaseException as 错误:
            if 已放弃.is_set():#调用方已走
                return#不再投递
            放入失败(结果队列,错误)#失败
            return
        if 已放弃.is_set():#取消后仍跑完
            if 回收已放弃结果 is not None:#需要回收
                try:
                    回收已放弃结果(值)#兑现则拆除
                except BaseException:
                    pass#回收失败忽略
            return#不再投递
        放入成功(结果队列,值)#成功
    启动守护线程(执行并放入)#工作线程
    while True:#结果或中止
        if 已中止(信号):#中止胜出
            已放弃.set()#标记放弃
            raise 包装中止错误(标识,信号.原因)#抛中止
        try:
            种类,载荷=结果队列.get(timeout=0.05)#短等结果
        except 空队列:#尚无结果
            continue#再看中止
        if 种类=='err':#失败
            raise 载荷#原样抛
        return 载荷#成功值
