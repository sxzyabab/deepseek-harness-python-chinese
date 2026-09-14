import random,threading,time#抖动、后台循环、睡眠
from ..rpc import 连接错误,已中止#本包异常与中止

__all__=['连接配置缺省','连接控制器']#仅中文公开名

连接配置缺省={#配置缺省
    'backoffBaseMs':500,#首次退避 500ms
    'backoffFactor':2,#每次翻倍
    'backoffMaxMs':10_000,#上限 10s
    'streamOpenTimeoutMs':3_000,#等 onOpen 最多 3s
}#连接配置缺省结束

def 可取消睡眠(毫秒,信号):#可取消睡眠
    """到期或 abort 都返回。"""
    截止=time.monotonic()+毫秒/1000#到期时刻
    while time.monotonic()<截止:#未到期
        if 已中止(信号):#已取消
            return#结束
        time.sleep(min(0.05,(截止-time.monotonic())))#短睡

class 连接控制器:#浏览器连接控制器
    """打开两条流并保持迭代；丢失后按指数退避重连。"""
    def __init__(自身,接口客户端,汇=None,配置=None):#绑定 API、汇与配置
        """合并默认后的配置。"""
        自身.接口=接口客户端#底层 API 客户端
        自身.汇=汇 if 汇 is not None else {}#可选汇
        合并=dict(连接配置缺省)#拷默认
        if 配置 is not None:#有覆盖
            for 键,值 in 配置.items():#逐项
                if 值 is not None:#非空覆盖
                    合并[键]=值#写入
        自身.配置=合并#合并后
        自身.世代=0#当前世代序号
        自身.尝试=0#连续失败次数
        自身.当前=None#当前世代的取消器
        自身.运行中=False#循环是否在跑
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
        """停止循环并 abort 当前世代的流。"""
        自身.运行中=False#循环条件失败
        if 自身.当前 is not None:#有世代
            自身.当前.set()#取消当前世代
        自身.当前=None#丢掉取消器

    def _退避延迟(自身,尝试次数):#按失败次数算抖动退避
        """半到全之间抖动。"""
        基础=自身.配置['backoffBaseMs']#基础
        因子=自身.配置['backoffFactor']#因子
        上限=自身.配置['backoffMaxMs']#封顶
        帽=min(上限,基础*(因子**max(0,尝试次数-1)))#指数上限再封顶
        return 帽/2+random.random()*(帽/2)#抖动

    def _仍运行(自身):#当前是否仍该继续
        """经方法读取：停止会在等待之间翻转旗标。"""
        return 自身.运行中#每次重读

    def _世代仍活(自身,信号):#本世代是否仍有效
        """循环还在且本世代未 abort。"""
        return 自身._仍运行() and (not 已中止(信号))#双守卫

    def _循环(自身):#连接世代循环
        """直到停止。"""
        while 自身.运行中:#直到 stop
            自身.世代+=1#新世代号
            世代号=自身.世代#本世代
            取消=threading.Event()#本世代取消
            自身.当前=取消#供 stop 使用
            打开旗={'mux':False,'host':False}#两条流 onOpen
            失败事件=threading.Event()#任一流结束则本世代失败

            def 收敛():#流结束回调
                """仍是当前世代则 abort。"""
                if 世代号==自身.世代 and (not 已中止(取消)):#仍当前
                    取消.set()#abort
                失败事件.set()#让 loop 往下走退避

            def 记复用打开():#mux 已开
                """标旗。"""
                打开旗['mux']=True#开

            def 记宿主打开():#host 已开
                """标旗。"""
                打开旗['host']=True#开

            def 泵复用():#泵 mux
                """复用事件流。"""
                函=自身.汇['onMuxEnvelope'] if 'onMuxEnvelope' in 自身.汇 else None#汇
                自身._泵流(自身.接口.events.mux({},取消,记复用打开),函,收敛)#泵 mux

            def 泵宿主():#泵 host
                """宿主事件流。"""
                函=自身.汇['onHostEnvelope'] if 'onHostEnvelope' in 自身.汇 else None#汇
                自身._泵流(自身.接口.events.host({},取消,记宿主打开),函,收敛)#泵 host

            threading.Thread(target=泵复用,daemon=True).start()#后台 mux
            threading.Thread(target=泵宿主,daemon=True).start()#后台 host
            try:#严格就绪握手
                描述响应=自身.接口.host.describe({})#一元可达性
                超时毫秒=自身.配置['streamOpenTimeoutMs']#握手超时
                截止=time.monotonic()+超时毫秒/1000#到期
                while time.monotonic()<截止:#等流打开或超时
                    if 打开旗['mux'] and 打开旗['host']:#两条都开
                        break#就绪
                    if 已中止(取消):#已被 abort
                        break#退出等
                    time.sleep(0.01)#短睡
                描述结果=描述响应['result']#describe RPC 结果
                成功=描述结果['ok'] if 'ok' in 描述结果 else False#是否 ok
                if not 成功:#宿主描述失败
                    错误=描述结果['error'] if 'error' in 描述结果 else {}#错误
                    码=错误['code'] if 'code' in 错误 else '?'#码
                    消息=错误['message'] if 'message' in 错误 else '?'#消息
                    raise 连接错误(f'host.describe 失败: {码}: {消息}')#当成本世代失败
                if 已中止(取消):#握手期间已被 abort
                    raise 连接错误('就绪握手期间世代已中止')#失败
                自身.尝试=0#成功则清失败计数
                自身._发状态('connected')#通知 UI 已连接
                if 自身._世代仍活(取消):#世代仍活
                    值=描述结果['value'] if 'value' in 描述结果 else None#描述值
                    自身._调已连接(值)#把描述交给业务
            except Exception:#传输失败：当作世代失败，落到共用退避
                if not 已中止(取消):#尚未 abort
                    取消.set()#取消泵
            失败事件.wait()#等流泵结束
            if not 自身._仍运行():#stop 了就退出循环
                return#退出
            自身._发状态('reconnecting')#进入重连
            自身.尝试+=1#失败次数加一
            print(f'[web-runtime] 连接丢失，重试 #{自身.尝试}')#诊断日志
            可取消睡眠(自身._退避延迟(自身.尝试),threading.Event())#抖动睡眠

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

    def _泵流(自身,流,汇函数,结束回调):#把一条事件流泵到汇
        """迭代到结束；汇抛错不杀泵。"""
        try:#迭代流
            for 信封 in 流:#每帧
                载荷=信封['payload'] if 'payload' in 信封 else None#载荷
                类型=载荷['type'] if 载荷 is not None and 'type' in 载荷 else None#帧类型
                if 类型=='stream/error':#流错误帧结束泵
                    break#停
                if 汇函数 is not None:#有汇
                    自身._调汇(汇函数,信封)#交给业务
        except OSError:#流丢失：收敛到结束回调
            pass#吞掉，触发共用重连
        结束回调()#通知世代失败/结束

    def _调汇(自身,函数,参数):#安全调用汇
        """业务层抛错只记日志，从不影响泵或重连语义。"""
        try:#汇可能抛
            函数(参数)#执行
        except Exception as 错误:#只记日志
            print('[web-runtime] 连接汇抛错:',错误)#诊断
