"""一个终端所有者的窗口保持与保守空闲回收。

对齐上游 `terminal-controller/src/retention.ts`。公开面仅中文名。
"""
import threading#观察与定时
import time#单调时钟
from ...工具.超时 import 中止控制器,若已中止则抛出,合成信号#中止
from .类型 import 远程错误#不可用

__all__=['终端保持']#仅中文公开名

class 终端保持:
    """恰好一个所有者编排保持、观察与可重试进程清理。"""

    def __init__(自身,策略,观察,终止,失败汇):
        """记下策略与回调。策略为 dict。"""
        自身._策略=策略#时序
        自身._观察=观察#inspect
        自身._终止=终止#terminate
        自身._失败汇=失败汇#failed
        自身._寿命=中止控制器()#寿命
        自身._保持者=set()#持有者 id
        自身._纪元=0#纪元
        自身._定时器=None#Timer
        自身._观察中=None#观察任务标志
        自身._空闲=None#空闲 dict
        自身._关闭中=False#关闭中
        自身._已拆除=False#已拆除
        自身._清理=None#清理任务
        自身._锁=threading.Lock()#互斥
        自身._调度(0)#即调度

    def retain(自身,信号):
        """为一条物理 Remote 流保持终端。"""
        若已中止则抛出(信号)#已取消
        if 自身._关闭中 or 自身._已拆除:#不可用
            raise 远程错误('terminal/unavailable','Terminal is closing or unavailable',{})#拒绝
        持有者=object()#持有者
        结束=threading.Event()#结束门
        合成=合成信号([信号,自身._寿命.信号])#合成
        def 释放():
            """释放持有。"""
            with 自身._锁:#互斥
                if 持有者 not in 自身._保持者:#已释
                    return#结束
                自身._保持者.discard(持有者)#移除
            自身.作废()#作废
            结束.set()#唤醒
            自身._调度(0)#调度
        with 自身._锁:#登记
            自身._保持者.add(持有者)#加入
        自身.作废()#作废空闲
        自身._取消定时()#清定时
        try:
            yield {'type':'retained'}#确认
            while not 结束.is_set():#等待结束
                事件=getattr(合成,'事件',None)#中止事件
                if 事件 is not None and 事件.is_set():#已中止
                    break#停
                结束.wait(0.05)#短等
        finally:
            释放()#释放

    def 作废(自身):
        """接受输入前作废未完成的空闲观察。"""
        自身._纪元+=1#纪元
        自身._空闲=None#清空

    def close(自身):
        """启动或加入清理。"""
        with 自身._锁:#互斥
            if 自身._清理 is not None:#共享
                return 自身._清理#任务
            自身._关闭中=True#标记
            自身.作废()#作废
            自身._寿命.中止(远程错误('gateway/internal','Terminal closed',{}))#中止寿命
            自身._取消定时()#清定时
            def 跑清理():
                """执行终止。"""
                try:
                    自身._终止()#终止
                except BaseException as 错误:
                    with 自身._锁:#允许重试
                        自身._清理=None#清空
                    自身._调度(自身._策略['cleanupRetryMs'])#重试
                    raise 错误#上抛
            任务=threading.Thread(target=跑清理)#线程
            任务.daemon=True#守护
            自身._清理=任务#记下
            任务.start()#启动
            return 任务#任务

    def dispose(自身):
        """停止定时器与流并等待最终清理。"""
        自身._已拆除=True#标记
        自身._取消定时()#清定时
        自身.close()#关闭

    def _取消定时(自身):
        """清定时器。"""
        定时=自身._定时器#取出
        自身._定时器=None#清空
        if 定时 is not None:#有
            定时.cancel()#取消

    def _调度(自身,延迟毫秒):
        """调度观察或重试关闭。"""
        with 自身._锁:#互斥
            if 自身._已拆除 or 自身._定时器 is not None:#已有
                return#结束
            if (not 自身._关闭中) and (len(自身._保持者)>0 or 自身._策略['unattendedTimeoutMs']==0):#有持有或禁用
                return#结束
            def 到点():
                """到期回调。"""
                自身._定时器=None#清空
                if 自身._关闭中:#重试关闭
                    try:
                        自身.close()#关闭
                    except BaseException as 错误:
                        自身._失败汇(错误)#报告
                    return#结束
                自身._观察空闲()#观察
            定时=threading.Timer(max(延迟毫秒,0)/1000.0,到点)#定时
            定时.daemon=True#守护
            自身._定时器=定时#记下
            定时.start()#启动

    def _观察空闲(自身):
        """观察空闲并可能回收。"""
        if 自身._观察中 is not None:#进行中
            return#结束
        纪元=自身._纪元#纪元
        自身._观察中=True#标记
        def 跑():
            """后台观察。"""
            try:
                try:
                    活动=自身._观察()#观察
                except BaseException:
                    活动={'state':'unknown','revision':0}#未知
                if 自身._已拆除 or 自身._关闭中 or len(自身._保持者)>0 or 纪元!=自身._纪元:#过期
                    return#结束
                现在=time.monotonic()*1000#单调毫秒
                if 活动.get('state')!='idle':#非空闲
                    自身._空闲=None#清空
                    return#结束
                修订=活动.get('revision',0)#修订
                空闲=自身._空闲#当前
                轮询=自身._策略['activityPollIntervalMs']#轮询
                if 空闲 is None or 空闲.get('revision')!=修订 or 现在-空闲['observedAt']>轮询*2:#新空闲
                    自身._空闲={'since':现在,'observedAt':现在,'revision':修订}#记下
                else:#刷新
                    空闲['observedAt']=现在#刷新
                if 现在-自身._空闲['since']>=自身._策略['unattendedTimeoutMs']:#超时
                    自身.close()#回收
            except BaseException as 错误:
                自身._失败汇(错误)#报告
            finally:
                自身._观察中=None#清空
                if not 自身._关闭中:#再调度
                    自身._调度(自身._策略['activityPollIntervalMs'])#调度
        线=threading.Thread(target=跑)#线程
        线.daemon=True#守护
        线.start()#启动
