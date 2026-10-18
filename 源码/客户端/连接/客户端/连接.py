'代际就绪、取消和持续恢复'
from ...模块.客户端.通告 import 取握手窗口
import random,threading,time#退避抖动与循环线程
from ..恢复流程配置 import 解析连接配置#补齐时序
from ..异常 import 连接错误#代际结束或超时
from ..rpc import 中止控制器,同步等待#这一代的信号，以及源返回的期约

手动重连=连接错误('connection: manual reconnect requested')#立即替换当前尝试
网络状态变更=连接错误('connection: browser network state changed')#在线状态变了


class 连接控制器:
    '打开已登记的代际源，丢失后按指数退避重连。汇抛错不停止循环'
    def __init__(自身,源,汇=None,配置=None):
        '先把时序补齐'
        自身.源=源#代际源
        自身.汇=汇 if 汇 is not None else {}#状态回调
        自身.配置=解析连接配置({} if 配置 is None else 配置)#完整时序
        自身.世代=0#代际号
        自身.尝试=0#重试次数
        自身.当前=None#这一代的中止
        自身._重试延迟=None#退避的中止
        自身.运行中=False#循环是否在跑
        自身._立即重试=False#手动重连
        自身._网络可用=True#浏览器是否在线
        自身.上次状态=None#上次发出的状态
        自身._线程=None#循环线程

    def 启动(自身):
        '已经在跑则忽略'
        if 自身.运行中:#已启动
            return#不重复
        自身.运行中=True#占上
        自身._线程=threading.Thread(target=自身._循环,daemon=True)#不挡住调用方
        自身._线程.start()#开始泵

    def 停止(自身):
        '停止循环并中止当前代际与退避'
        自身.运行中=False#停下
        if 自身.当前 is not None:#有一代
            自身.当前.abort()#中止
            自身.当前=None#清掉
        if 自身._重试延迟 is not None:#在退避
            自身._重试延迟.abort()#打断
            自身._重试延迟=None#清掉

    def 重连(自身):
        '重置重试并立刻替换当前一代或退避'
        if not 自身.运行中:#没在跑
            return#忽略
        自身.尝试=0#从头
        自身._立即重试=True#不等退避
        自身._发状态('connecting')#正在连接
        if not 自身._仍运行():#汇里可能已经停止
            return#结束
        if 自身.当前 is not None:#有一代
            自身.当前.abort(手动重连)#替换
        if 自身._重试延迟 is not None:#在退避
            自身._重试延迟.abort(手动重连)#打断睡眠

    def 设网络可用(自身,可用):
        '离线时挂起自动重试。网络回来后重新退避'
        if 自身._网络可用==可用:#没变
            return#忽略
        自身._网络可用=可用#记下
        自身.尝试=0#从头
        自身._立即重试=False#不是手动
        if not 自身.运行中:#没在跑
            return#只改标志
        自身._发状态('connecting' if 可用 else 'disconnected')#状态
        if not 自身._仍运行():#汇里可能已经停止
            return#结束
        if 自身.当前 is not None:#有一代
            自身.当前.abort(网络状态变更)#替换
        if 自身._重试延迟 is not None:#在退避或挂起
            自身._重试延迟.abort(网络状态变更)#打断

    def _仍运行(自身):
        '停止会在等待之间把标志翻掉'
        return 自身.运行中#当前标志

    def _世代仍活(自身,控制器):
        '循环还在，且这一代还没中止'
        return 自身._仍运行() and not 控制器.signal.aborted#两样都要

    def _警告(自身,文本):
        '打到页面控制台'
        取握手窗口().console.warn(文本)#警告

    def _错误(自身,文本,错误):
        '打到页面控制台'
        取握手窗口().console.error(文本,错误)#错误

    def _调汇(自身,函数):
        '业务层抛错只记日志'
        try:#隔离
            函数()#调用
        except Exception as 错误:#不杀死循环
            自身._错误('[connection] connection sink threw:',错误)#诊断

    def _发状态(自身,状态):
        '相同状态不重复发'
        if 自身.上次状态==状态:#没变
            return#跳过
        自身.上次状态=状态#记下

        def 通知():
            '交给 onStateChange'
            回调=自身.汇.get('onStateChange')#回调
            if 回调 is not None:#有
                回调(状态)#通知

        自身._调汇(通知)#隔离

    def _循环(自身):
        '直到停止。源在另一条线程里跑，这一条线程负责超时和退避'
        重试=False#第一次不退避
        while 自身._仍运行():#还在跑
            if not 自身._网络可用 and not 自身._立即重试:#离线且不是手动
                延迟=中止控制器()#挂起
                自身._重试延迟=延迟#记下
                自身._发状态('disconnected')#断开
                if not 延迟.signal.aborted:#还没被打断
                    延迟.signal._事件.wait()#等到中止
                if 自身._重试延迟 is 延迟:#还是这一次
                    自身._重试延迟=None#清掉
                if not 自身._仍运行():#停了
                    return#离开
                重试=True#醒来后按重试走
                continue#重新看网络
            手动尝试=False#这一次是不是手动
            if 重试:#丢失之后
                立即=自身._立即重试#先读
                自身._立即重试=False#用掉
                if 立即:#手动
                    自身.尝试=0#从头数
                手动尝试=立即#记下来
                自身.尝试=自身.尝试+1#这一次
                尝试次数=自身.尝试#局部
                自身._发状态('connecting')#正在连接
                if not 自身._仍运行():#停了
                    return#离开
                if 自身._立即重试 or (not 自身._网络可用 and not 立即):#退避前又被打断
                    continue#重来
                if not 立即:#自动重试才睡
                    延迟=中止控制器()#可打断的睡眠
                    自身._重试延迟=延迟#记下
                    帽=min(#半到全抖动用的帽
                        自身.配置['backoffMaxMs'],
                        自身.配置['backoffBaseMs']*(自身.配置['backoffFactor']**max(0,尝试次数-1)),
                    )#帽结束
                    毫秒=帽/2+random.random()*(帽/2)#半到全
                    睡完=threading.Event()#到期

                    def 睡醒(睡完=睡完):
                        '到期或中止都放开'
                        睡完.set()#放开

                    定时=threading.Timer(毫秒/1000,睡醒)#到期
                    定时.daemon=True#随进程
                    定时.start()#开始
                    延迟.signal.addEventListener('abort',睡醒,{'once':True})#中止
                    睡完.wait()#等到其中一个
                    定时.cancel()#不再响
                    延迟.signal.removeEventListener('abort',睡醒)#摘掉
                    if 自身._重试延迟 is 延迟:#还是这一次
                        自身._重试延迟=None#清掉
                    if not 自身._仍运行():#停了
                        return#离开
                    if 延迟.signal.aborted:#被打断
                        continue#重来
                自身._警告('[connection] connection lost, retry #'+str(尝试次数))#诊断

                def 请求重连():
                    '让消费者重开物理载体'
                    回调=自身.汇.get('onReconnectRequested')#回调
                    if 回调 is not None:#有
                        回调()#调用

                自身._调汇(请求重连)#隔离
                if not 自身._仍运行():#停了
                    return#离开
            世代=自身.世代+1#新的一代
            自身.世代=世代#记下
            控制器=中止控制器()#这一代
            自身.当前=控制器#记下
            就绪事件=threading.Event()#源报告就绪
            失败事件=threading.Event()#源结束
            叫醒=threading.Event()#超时等待
            就绪盒={}#宿主或错误
            源已就绪={'值':False}#是否已经 ready

            def 醒(叫醒=叫醒):
                '让等待看一眼新状态'
                叫醒.set()#放开

            def 报告就绪(宿主信息,世代=世代,控制器=控制器,源已就绪=源已就绪,就绪盒=就绪盒,就绪事件=就绪事件,醒=醒):
                '增量监听挂上之后只报告一次'
                if 源已就绪['值'] or 世代!=自身.世代 or not 自身._世代仍活(控制器):#过期
                    return#忽略
                源已就绪['值']=True#占上
                就绪盒['宿主']=宿主信息#记下
                就绪事件.set()#就绪
                醒()#叫醒

            def 跑源(控制器=控制器,报告就绪=报告就绪,源已就绪=源已就绪,就绪盒=就绪盒,就绪事件=就绪事件,失败事件=失败事件,醒=醒):
                '源结束或失败后通知循环。就绪之后的中止留给循环'
                try:#源自己的寿命
                    try:#正常结束或失败
                        结果=自身.源(控制器.signal,报告就绪)#打开
                        同步等待(结果)#期约则等到它结束
                        错误=连接错误('connection generation ended')#正常结束
                    except Exception as 捕到:#失败
                        错误=捕到#原错误
                    if not 源已就绪['值']:#还没就绪就结束了
                        就绪盒['错误']=错误#给竞赛
                        就绪事件.set()#放开竞赛
                finally:#无论成败都要放开循环
                    失败事件.set()#循环可以继续
                    醒()#叫醒竞赛

            控制器.signal.addEventListener('abort',醒,{'once':True})#中止也要叫醒
            threading.Thread(target=跑源,daemon=True).start()#源不堵这一条线程
            开始=time.monotonic()#起算
            已警告=False#慢握手只警告一次
            成功宿主=None#竞赛得到的宿主
            竞赛错误=None#竞赛得到的错误
            while 竞赛错误 is None and 成功宿主 is None:#还没分出胜负
                经过=(time.monotonic()-开始)*1000#已过毫秒
                if not 已警告 and 经过>=自身.配置['generationReadyWarnMs']:#到了警告
                    已警告=True#只一次
                    自身._警告('[connection] generation is still not ready after '+str(自身.配置['generationReadyWarnMs'])+'ms')#诊断
                if 控制器.signal.aborted:#这一代被中止
                    竞赛错误=连接错误('connection generation aborted')#握手中止
                    if isinstance(控制器.signal.reason,BaseException):#有原因
                        竞赛错误.__cause__=控制器.signal.reason#挂上
                    break#离开竞赛
                if 就绪事件.is_set():#源有结果
                    if '错误' in 就绪盒:#失败
                        竞赛错误=就绪盒['错误']#错误
                    else:#就绪
                        成功宿主=就绪盒['宿主']#宿主
                    break#离开竞赛
                if 失败事件.is_set():#源已经结束但没报告就绪
                    竞赛错误=就绪盒['错误'] if '错误' in 就绪盒 else 连接错误('connection generation ended')#结束
                    break#离开竞赛
                if 经过>=自身.配置['generationReadyTimeoutMs']:#硬截止
                    竞赛错误=连接错误('connection generation was not ready within '+str(自身.配置['generationReadyTimeoutMs'])+'ms')#超时
                    自身._警告('[connection] '+str(竞赛错误)+'; cancelling generation')#诊断
                    break#离开竞赛
                下一刻=自身.配置['generationReadyWarnMs'] if not 已警告 else 自身.配置['generationReadyTimeoutMs']#下一次要看的时刻
                叫醒.wait(max(0,(下一刻-经过)/1000))#睡到那一刻或被叫醒
                叫醒.clear()#这次用掉
            try:#握手结果
                if 竞赛错误 is not None:#没连上
                    raise 竞赛错误#交给下面的中止
                if 控制器.signal.aborted:#就绪竞争期间被中止
                    raise 连接错误('generation aborted during readiness handshake')#不算连上
                自身.尝试=0#连上就清掉重试
                自身._发状态('connected')#已连接
                if 自身._世代仍活(控制器):#汇没有把这一代停掉
                    宿主信息=成功宿主#闭包

                    def 通知已连接():
                        '交给 onConnected'
                        回调=自身.汇.get('onConnected')#回调
                        if 回调 is not None:#有
                            回调(宿主信息)#宿主事实

                    自身._调汇(通知已连接)#隔离
            except Exception as 错误:#握手失败
                if not 控制器.signal.aborted:#还没中止
                    控制器.abort(错误)#取消这一代
            失败事件.wait()#等到源结束
            if 世代==自身.世代 and 自身.当前 is 控制器 and not 控制器.signal.aborted:#源结束时中止信号
                控制器.abort()#没有额外原因
            if not 自身._仍运行():#停了
                return#离开
            if 手动尝试:#手动的这一次不累计
                自身.尝试=0#清掉
            重试=True#下一圈走退避
