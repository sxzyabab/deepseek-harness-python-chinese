import math,random,threading,time#有限判定、抖动、后台循环、睡眠
from ..rpc import 连接错误,已中止#本包异常与中止

__all__=['连接配置缺省','解析连接配置','连接控制器']#仅中文公开名

定时器上限毫秒=2_147_483_647#有符号 32 位定时器上限
连接配置缺省={#配置缺省
    'backoffBaseMs':500,#首次退避 500ms
    'backoffFactor':2,#每次翻倍
    'backoffMaxMs':10_000,#上限 10s
    'generationReadyWarnMs':3_000,#握手过慢警告
    'generationReadyTimeoutMs':15_000,#就绪硬截止
}#连接配置缺省结束

def 解析连接配置(配置=None):
    """校验恢复输入并补齐时序默认值。"""
    输入={} if 配置 is None else 配置#缺省空
    if type(输入) is not dict:#须为对象
        raise TypeError('connection recovery config must be an object')#入口失败
    结果=dict(连接配置缺省)#拷默认
    for 键 in 连接配置缺省:#逐字段
        if 键 not in 输入:#省略
            continue#默认
        值=输入[键]#覆盖
        if 键=='backoffFactor':#因子
            if type(值) is bool or not isinstance(值,(int,float)):#须数字
                raise TypeError('connection recovery backoffFactor must be a number')#失败
            if 值<1:#至少 1
                raise ValueError('connection recovery backoffFactor must be at least 1')#失败
            结果[键]=float(值)#写入
            continue#下一项
        if type(值) is bool or type(值) is not int or 值<1 or 值>定时器上限毫秒:#自然数
            raise ValueError('connection recovery '+键+' must be a natural number within the timer limit')#失败
        结果[键]=值#写入
    if not math.isfinite(结果['backoffFactor']):#因子须有限
        raise ValueError('connection recovery backoffFactor must be finite')#失败
    return 结果#完整配置

def 可取消睡眠(毫秒,信号):#可取消睡眠
    """到期或 abort 都返回。"""
    截止=time.monotonic()+毫秒/1000#到期时刻
    while time.monotonic()<截止:#未到期
        if 已中止(信号):#已取消
            return#结束
        time.sleep(min(0.05,(截止-time.monotonic())))#短睡

def 等待中止(信号):
    """等到信号置位。"""
    if 已中止(信号):#已中止
        return#结束
    信号.wait()#阻塞

def 等待就绪(就绪事件,就绪宿主,就绪错误,源丢失事件,源丢失错误,配置,信号):
    """就绪与源丢失赛跑，附警告与硬截止。"""
    警告毫秒=配置['generationReadyWarnMs']#警告
    超时毫秒=配置['generationReadyTimeoutMs']#硬截止
    开始=time.monotonic()#起点
    警告截止=开始+警告毫秒/1000#警告时刻
    超时截止=开始+超时毫秒/1000#超时时刻
    已警告=False#是否已报
    while True:#直到结局
        if 已中止(信号):#世代取消
            raise 连接错误('connection generation aborted')#失败
        if 就绪事件.is_set():#就绪或就绪失败
            if 就绪宿主['v'] is not None:#有宿主
                return 就绪宿主['v']#交出
            错=就绪错误['v']#失败
            raise 错 if 错 is not None else 连接错误('connection generation ended')#抛
        if 源丢失事件.is_set():#源先结束
            错=源丢失错误['v']#失败
            raise 错 if 错 is not None else 连接错误('connection generation ended')#抛
        现在=time.monotonic()#此刻
        if 现在>=超时截止:#硬截止
            消息='connection generation was not ready within '+str(超时毫秒)+'ms'#文案
            print('[connection] '+消息+'; cancelling generation')#诊断
            raise 连接错误(消息)#取消世代
        if not 已警告 and 现在>=警告截止:#过慢
            print('[connection] generation is still not ready after '+str(警告毫秒)+'ms')#警告
            已警告=True#只报一次
        就绪事件.wait(timeout=min(0.05,超时截止-现在))#短等

class 连接控制器:#浏览器连接控制器
    """打开已登记代际源并在丢失后按指数退避重连。"""
    def __init__(自身,源,汇=None,配置=None):#绑定源、汇与配置
        """合并默认后的配置。"""
        自身.源=源#代际源
        自身.汇=汇 if 汇 is not None else {}#可选汇
        自身.配置=解析连接配置(配置)#完整时序
        自身.世代=0#当前世代序号
        自身.尝试=0#连续失败次数
        自身.当前=None#当前世代的取消器
        自身._重试延迟=None#退避取消器
        自身.运行中=False#循环是否在跑
        自身._立即重试=False#手动立即重试
        自身._网络可用=True#浏览器网络
        自身.上次状态=None#上次已发出的状态
        自身._线程=None#后台循环线程

    def 启动(自身):#幂等开始连接/泵/重连循环
        """已在跑则忽略。"""
        if 自身.运行中:#已在跑
            return#忽略
        自身.运行中=True#标记运行
        自身._线程=threading.Thread(target=自身._循环,name='connection-loop',daemon=True)#后台跑
        自身._线程.start()#启动

    def 停止(自身):#停泵
        """停止循环并 abort 当前世代与退避。"""
        自身.运行中=False#循环条件失败
        if 自身.当前 is not None:#有世代
            自身.当前.set()#取消当前世代
        自身.当前=None#丢掉取消器
        if 自身._重试延迟 is not None:#有退避
            自身._重试延迟.set()#取消退避
        自身._重试延迟=None#丢掉

    def 重连(自身):#立即替换当前世代
        """重置重试进程并立即替换当前尝试。"""
        if not 自身.运行中:#未跑
            return#忽略
        自身.尝试=0#清失败计数
        自身._立即重试=True#立即
        自身._发状态('connecting')#进入连接中
        if not 自身._仍运行():#汇可能同步停
            return#停
        if 自身.当前 is not None:#有世代
            自身.当前.set()#abort
        if 自身._重试延迟 is not None:#有退避
            自身._重试延迟.set()#abort

    def 设网络可用(自身,可用):#浏览器网络可用性
        """离线挂起自动重试；网络回来后重启退避。"""
        if 自身._网络可用==可用:#未变
            return#忽略
        自身._网络可用=可用#记下
        自身.尝试=0#清失败计数
        自身._立即重试=False#非手动
        if not 自身.运行中:#未跑
            return#忽略
        自身._发状态('connecting' if 可用 else 'disconnected')#状态
        if not 自身._仍运行():#汇可能同步停
            return#停
        if 自身.当前 is not None:#有世代
            自身.当前.set()#abort
        if 自身._重试延迟 is not None:#有退避
            自身._重试延迟.set()#abort

    def _退避帽(自身,尝试次数):#指数上限再封顶
        """半到全抖动所用帽。"""
        基础=自身.配置['backoffBaseMs']#基础
        因子=自身.配置['backoffFactor']#因子
        上限=自身.配置['backoffMaxMs']#封顶
        return min(上限,基础*(因子**max(0,尝试次数-1)))#帽

    def _退避延迟(自身,尝试次数):#按失败次数算抖动退避
        """半到全之间抖动。"""
        帽=自身._退避帽(尝试次数)#帽
        return 帽/2+random.random()*(帽/2)#抖动

    def _重试被打断(自身,立即):#重读可变重试输入
        """立即重试或离线挂起。"""
        return 自身._立即重试 or ((not 自身._网络可用) and (not 立即))#打断

    def _仍运行(自身):#当前是否仍该继续
        """经方法读取：停止会在等待之间翻转旗标。"""
        return 自身.运行中#每次重读

    def _世代仍活(自身,信号):#本世代是否仍有效
        """循环还在且本世代未 abort。"""
        return 自身._仍运行() and (not 已中止(信号))#双守卫

    def _循环(自身):#连接世代循环
        """直到停止。"""
        重试=False#首次不退避
        while 自身.运行中:#直到 stop
            if (not 自身._网络可用) and (not 自身._立即重试):#离线挂起
                延迟取消=threading.Event()#退避取消
                自身._重试延迟=延迟取消#供 stop/重连
                自身._发状态('disconnected')#断开
                等待中止(延迟取消)#等到网络或停
                if 自身._重试延迟 is 延迟取消:#仍是本次
                    自身._重试延迟=None#清
                if not 自身._仍运行():#停
                    return#退出
                重试=True#下一圈当重试
                continue#再判网络
            手动尝试=False#是否手动立刻
            if 重试:#丢失后的下一圈
                立即=自身._立即重试#快照
                自身._立即重试=False#清
                if 立即:#手动
                    自身.尝试=0#清计数
                手动尝试=立即#记下
                自身.尝试+=1#失败次数
                尝试次数=自身.尝试#本圈
                自身._发状态('connecting')#连接中
                if not 自身._仍运行():#停
                    return#退出
                if 自身._重试被打断(立即):#被新输入打断
                    continue#再判
                if not 立即:#自动退避
                    延迟取消=threading.Event()#退避取消
                    自身._重试延迟=延迟取消#供 abort
                    可取消睡眠(自身._退避延迟(尝试次数),延迟取消)#抖动睡眠
                    if 自身._重试延迟 is 延迟取消:#仍是本次
                        自身._重试延迟=None#清
                    if not 自身._仍运行():#停
                        return#退出
                    if 已中止(延迟取消):#退避被 abort
                        continue#再判
                print('[connection] connection lost, retry #'+str(尝试次数))#诊断
                函=自身.汇['onReconnectRequested'] if 'onReconnectRequested' in 自身.汇 else None#汇
                if 函 is not None:#有
                    自身._调汇无参(函)#隔离
                if not 自身._仍运行():#停
                    return#退出
            自身.世代+=1#新世代号
            世代号=自身.世代#本世代
            取消=threading.Event()#本世代取消
            自身.当前=取消#供 stop 使用
            源已就绪=False#一次性就绪
            就绪宿主={'v':None}#宿主盒
            就绪错误={'v':None}#就绪失败
            就绪事件=threading.Event()#就绪或失败
            源丢失错误={'v':None}#源结束错误
            源丢失事件=threading.Event()#源结束
            源结束=threading.Event()#线程落定

            def 报告就绪(宿主):
                """代际源一次性报告就绪。"""
                nonlocal 源已就绪#写旗
                if 源已就绪 or 世代号!=自身.世代 or (not 自身._世代仍活(取消)):#过期
                    return#忽略
                源已就绪=True#一次性
                就绪宿主['v']=宿主#记下
                就绪事件.set()#唤醒

            def 跑源():
                """阻塞跑代际源直至结束。"""
                try:#源结算
                    自身.源(取消,报告就绪)#阻塞
                    错误=连接错误('connection generation ended')#正常结束亦失败就绪
                    if not 源已就绪:#未就绪
                        就绪错误['v']=错误#失败就绪
                        就绪事件.set()#唤醒
                    源丢失错误['v']=错误#源丢失
                    源丢失事件.set()#唤醒赛跑
                except Exception as 错误:#源失败
                    if not 源已就绪:#未就绪
                        就绪错误['v']=错误#失败就绪
                        就绪事件.set()#唤醒
                    源丢失错误['v']=错误#源丢失
                    源丢失事件.set()#唤醒赛跑
                if 世代号==自身.世代 and (not 已中止(取消)):#仍当前
                    取消.set()#abort
                源结束.set()#线程落定

            threading.Thread(target=跑源,name='connection-generation',daemon=True).start()#后台源
            try:#就绪握手
                宿主=等待就绪(就绪事件,就绪宿主,就绪错误,源丢失事件,源丢失错误,自身.配置,取消)#赛跑
                if 已中止(取消):#握手期间已被 abort
                    raise 连接错误('generation aborted during readiness handshake')#失败
                自身.尝试=0#成功则清失败计数
                自身._发状态('connected')#通知 UI 已连接
                if 自身._世代仍活(取消):#世代仍活
                    自身._调已连接(宿主)#把宿主交给业务
            except Exception:#传输失败：当作世代失败
                if not 已中止(取消):#尚未 abort
                    取消.set()#取消源
            源结束.wait()#等源线程落定
            if not 自身._仍运行():#stop 了就退出循环
                return#退出
            if 手动尝试:#手动重连不计连续失败
                自身.尝试=0#清
            重试=True#下一圈退避

    def _发状态(自身,状态):#去重的状态发出
        """只在变化时通知。"""
        if 自身.上次状态==状态:#相同则跳过
            return#跳过
        自身.上次状态=状态#记下
        函=自身.汇['onStateChange'] if 'onStateChange' in 自身.汇 else None#汇
        if 函 is not None:#有
            自身._调汇(函,状态)#隔离汇抛错

    def _调已连接(自身,值):#通知已连接
        """汇抛错不杀泵。"""
        函=自身.汇['onConnected'] if 'onConnected' in 自身.汇 else None#汇
        if 函 is not None:#有
            自身._调汇(函,值)#隔离

    def _调汇(自身,函数,参数):#安全调用汇
        """业务层抛错只记日志，从不影响泵或重连语义。"""
        try:#汇可能抛
            函数(参数)#执行
        except Exception as 错误:#只记日志
            print('[connection] connection sink threw:',错误)#诊断

    def _调汇无参(自身,函数):#无参汇
        """业务层抛错只记日志。"""
        try:#汇可能抛
            函数()#执行
        except Exception as 错误:#只记日志
            print('[connection] connection sink threw:',错误)#诊断
