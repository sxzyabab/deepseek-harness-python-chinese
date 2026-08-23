"""连接监督器：拥有一个插件实例的 MCP 客户端/传输世代，使框架工具注册表与存活世代保持同步；连接断开时按有界指数退避重启已配置的服务器。

对齐上游 `mcp-client/src/connection.ts`。公开面仅中文名。配置键与诊断英文字面量保持上游。
"""
import math,threading,time#有限判定、定时器与时间戳
from ..超时 import 定时器延迟上限毫秒#定时器延迟上限
from ...依赖 import cordis#外部依赖胶水
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定
from .传输 import 创建传输#传输工厂
from .工具 import 同步工具#工具同步

__all__=['重连默认值','解析重连策略','启动连接']#仅中文公开名

重连默认值={#冻结语义的重连默认值
    'enabled':True,#默认启用重连
    'initialDelayMs':500,#默认初始延迟 500 毫秒
    'maxDelayMs':30000,#默认上限与稳定窗口 30000 毫秒
    'maxAttempts':10,#默认最多 10 次
}#重连默认值结束

世代关闭超时毫秒=5000#世代关闭等待上限

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析重连策略(配置,路径):#解析并校验重连策略
    """从原始重连配置到监督器实际运行策略的唯一切确解析步骤。"""
    if 配置 is not None:#调用方给出了重连配置
        for 键 in (配置.keys() if isinstance(配置,dict) else dir(配置)):#遍历调用方给出的键
            if isinstance(配置,dict):#映射
                if 键 not in 重连默认值:#未知键则拒绝
                    raise Exception(路径+'.'+键+' is not a reconnect option')#未知键
            elif not 键.startswith('_') and 键 in ('enabled','initialDelayMs','maxDelayMs','maxAttempts'):#对象属性
                pass#已知键
    启用=取字段(配置,'enabled')#是否启用
    if 启用 is None:#缺省
        启用=重连默认值['enabled']#默认
    初始=取字段(配置,'initialDelayMs')#初始延迟
    if 初始 is None:#缺省
        初始=重连默认值['initialDelayMs']#默认
    上限=取字段(配置,'maxDelayMs')#延迟上限
    if 上限 is None:#缺省
        上限=重连默认值['maxDelayMs']#默认
    次数=取字段(配置,'maxAttempts')#最大尝试次数
    if 次数 is None:#缺省
        次数=重连默认值['maxAttempts']#默认
    if isinstance(初始,bool) or not isinstance(初始,(int,float)) or not math.isfinite(初始) or 初始<=0 or 初始>定时器延迟上限毫秒:#初始延迟非法
        raise Exception(路径+'.initialDelayMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#拒绝
    if isinstance(上限,bool) or not isinstance(上限,(int,float)) or not math.isfinite(上限) or 上限<=0 or 上限>定时器延迟上限毫秒:#延迟上限非法
        raise Exception(路径+'.maxDelayMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#拒绝
    if 初始>上限:#初始延迟超过上限
        raise Exception(路径+'.initialDelayMs must be less than or equal to maxDelayMs')#拒绝颠倒的延迟对
    if isinstance(次数,bool) or not isinstance(次数,int) or 次数<1:#尝试次数非法
        raise Exception(路径+'.maxAttempts must be a positive integer')#拒绝非正整数
    return {'enabled':启用,'initialDelayMs':初始,'maxDelayMs':上限,'maxAttempts':次数}#已解析策略

def 启动连接(上下文,配置,策略):#启动受监督连接
    """为一台 MCP 服务器启动受监督连接，并按重连策略保持存活。"""
    标签='mcp-client('+取字段(配置,'serverName')+')'#日志前缀
    选项={#普通同步用桥接选项
        'registrationFailure':'contain',#冲突时包容
        'serverName':取字段(配置,'serverName'),#服务器命名空间
        'toolCallTimeoutMs':取字段(配置,'toolCallTimeoutMs'),#工具调用超时
    }#选项结束
    if 取字段(配置,'failOnStartupError'):#启动同步选项
        启动选项=dict(选项)#拷贝
        启动选项['registrationFailure']='throw'#致命启动则冲突时抛出
    else:#否则沿用包容选项
        启动选项=选项#包容
    状态={#监督器可变状态
        'disposed':False,#是否已拆除
        'client':None,#当前 MCP 客户端
        'clientClosed':None,#当前世代关闭承诺
        'disposers':{},#当前工具 disposer
        'reconnectTimer':None,#已武装的重连定时器
        'failedAttempts':0,#连续失败计数
        'connectedAt':None,#连接成功时间戳
        'firstAttemptError':None,#初次失败原因
        'syncChain':已兑现链(),#同步串行链
        'settling':None,#进行中的连接尝试
    }#状态结束
    就绪=承诺()#初次尝试结算承诺

    def 仍是当前(世代):#是否仍是当前世代
        """一个世代仅在它仍是存活插件上的当前世代时才可行动。"""
        return (not 状态['disposed']) and 状态['client'] is 世代#仍是当前

    def 排队同步(世代,同步选项=None):#排队一次工具同步
        """序列化每一次同步工具调用。"""
        if 同步选项 is None:#缺省用普通选项
            同步选项=选项#普通选项
        链尾=状态['syncChain']#当前链尾
        本次=承诺()#本次运行
        def 接到链尾(_值=None):#接到链尾
            """世代仍当前才交换工具。"""
            try:#同步
                if not 仍是当前(世代):#世代已过时则跳过
                    本次.兑现(None)#跳过
                    return#结束
                状态['disposers']=同步工具(世代,上下文,同步选项,状态['disposers'])#交换工具世代
                本次.兑现(None)#成功
            except BaseException as 错误:#失败
                本次.拒绝(错误)#交给调用方
        def 吞掉(_错误=None):#吞掉失败以免断链
            """链尾必须挺过失败的同步。"""
            接到链尾()#继续跑本次
        新链=承诺()#新链尾
        def 结算链(_=None):#结算新链
            """无论成败都放行链。"""
            新链.兑现(None)#放行
        状态['syncChain']=新链#挂上新链尾
        try:#接旧链
            链尾.then(接到链尾,吞掉)#接到链尾
        except BaseException:#同步链 then 失败
            接到链尾()#直接跑
        本次.then(结算链,结算链)#结算链尾
        return 本次#把本次运行交给调用方

    def 世代断开(世代):#当前世代断开
        """每个世代一次断开判定。"""
        if not 仍是当前(世代):#过时信号忽略
            return#忽略
        状态['client']=None#清除当前客户端
        状态['clientClosed']=None#清除关闭承诺
        安排重连()#安排重连

    def 等待关闭(关闭承诺):#限时等待关闭
        """等待传输拥有的关闭信号，不让损坏的传输永远卡住拆除。"""
        结果=承诺()#超时或关闭二者先到
        def 超时():#超时则失败关闭
            """超时则失败关闭。"""
            结果.兑现(False)#失败关闭
        定时=threading.Timer(世代关闭超时毫秒/1000,超时)#超时定时器
        定时.daemon=True#不独自撑住进程
        定时.start()#启动
        def 已关闭(_=None):#关闭信号到达
            """取消超时并报告正常关闭。"""
            定时.cancel()#取消超时
            结果.兑现(True)#正常关闭
        try:#等待关闭承诺
            关闭承诺.then(已关闭,已关闭)#关闭或失败都算观察到
        except BaseException:#then 失败
            已关闭()#按已关闭处理
        return 解开(结果)#阻塞等到结果

    def 安排重连():#按策略安排下一次连接尝试
        """按策略安排下一次连接尝试。"""
        曾连通=状态['connectedAt'] is not None#是否曾建立过连接
        if not 策略['enabled']:#重连已关闭
            if 曾连通:#曾连通后丢失
                消息='connection lost and reconnect is disabled — registered tools will fail until an HMR reload or Host restart'#曾连通
            else:#从未连通
                消息='connection failed and reconnect is disabled — no tools were registered; reload the plugin or restart the Host to connect'#从未连通
            上下文.logger.error(标签+': '+消息)#记录致命停机
            return#不再尝试
        if 状态['connectedAt'] is not None and (time.time()*1000-状态['connectedAt'])>=策略['maxDelayMs']:#稳定存活则重置预算
            状态['failedAttempts']=0#重置
        状态['connectedAt']=None#离开连通状态
        状态['failedAttempts']+=1#计入本次失败
        if 状态['failedAttempts']>策略['maxAttempts']:#预算耗尽
            def 放弃拆除(_=None):#接到同步链尾再拆除
                """注销全部工具。"""
                for 注销 in 状态['disposers'].values():#注销全部工具
                    注销()#注销
                状态['disposers']={}#清空 disposer
            状态['syncChain'].then(放弃拆除,放弃拆除)#接到同步链尾
            上下文.logger.error(标签+': giving up after '+str(策略['maxAttempts'])+' consecutive failed reconnect attempts — tools unregistered; reload the plugin or restart the Host to reconnect')#记录放弃
            return#停止重连
        延迟=min(策略['maxDelayMs'],策略['initialDelayMs']*(2**(状态['failedAttempts']-1)))#指数退避并封顶
        动作='connection lost; reconnecting' if 曾连通 else 'connection failed; retrying'#日志动词
        上下文.logger.warn(标签+': '+动作+' in '+str(延迟)+'ms (attempt '+str(状态['failedAttempts'])+'/'+str(策略['maxAttempts'])+')')#预告下次尝试
        def 到期():#到期后发起下一代
            """非启动路径的连接尝试。"""
            状态['reconnectTimer']=None#定时器已触发
            状态['settling']=连接世代(False)#非启动路径
        定时=threading.Timer(延迟/1000,到期)#延迟毫秒
        定时.daemon=True#允许进程在等待期间退出
        状态['reconnectTimer']=定时#记下
        定时.start()#武装

    def 连接世代(启动):#尝试建立一代连接
        """一次连接尝试：全新传输 + 客户端，连接，然后排队初次工具同步。"""
        from mcp import ClientSession#MCP 客户端会话
        传输=创建传输(配置)#按配置创建传输
        关闭=承诺()#本代关闭栅栏
        尝试已结算=False#本次尝试是否已结算
        已观察关闭=False#是否已观察到关闭
        世代容器={'session':None,'cm':None}#会话与上下文管理器
        状态['client']=世代容器#设为当前世代
        状态['clientClosed']=关闭#配对关闭承诺
        try:#连接并初次同步
            if 传输['kind']=='stdio':#stdio
                上下文管理器=传输['factory'](传输['params'])#stdio_client
            else:#HTTP
                上下文管理器=传输['factory'](传输['url'],headers=传输['headers'])#streamablehttp_client
            读写=解开(上下文管理器.__aenter__()) if hasattr(上下文管理器,'__aenter__') else 上下文管理器.__enter__()#进入传输
            读,写=读写[0],读写[1]#读写流
            会话=ClientSession(读,写)#构造本代客户端
            解开(会话.initialize())#初始化
            世代容器['session']=会话#记下会话
            世代容器['cm']=上下文管理器#记下管理器
            世代容器['request']=会话.request if hasattr(会话,'request') else (lambda 载荷,选项=None:会话.call_tool(取字段(取字段(载荷,'params'),'name'),取字段(取字段(载荷,'params'),'arguments')) if 取字段(载荷,'method')=='tools/call' else 会话.list_tools())#请求面
            解开(排队同步(世代容器,启动选项 if 启动 else 选项))#排队初次同步
        except BaseException as 错误:#连接或同步失败
            if 状态['firstAttemptError'] is None:#只记下第一次错误
                状态['firstAttemptError']=错误#初次失败
            if 仍是当前(世代容器):#仍是当前则记警告
                上下文.logger.warn(标签+': connection attempt failed: '+str(错误))#记警告
            try:#尽力关闭
                关闭世代(世代容器)#关闭
            except BaseException:#传输已消失
                pass#忽略
            已安静=已观察关闭 or 解开(等待关闭(关闭))#等待关闭或超时
            尝试已结算=True#标记尝试已结算
            if not 仍是当前(世代容器):#已不是当前则退出
                return#退出
            if not 已安静:#关闭超时
                状态['client']=None#放弃当前客户端
                状态['clientClosed']=None#放弃关闭承诺
                上下文.logger.error(标签+': failed generation did not close within '+str(世代关闭超时毫秒)+'ms — reconnect stopped to avoid overlapping server processes; reload the plugin or restart the Host to retry')#停止重连
                return#不再重连
            世代断开(世代容器)#正常转入断开以重连
            return#结束失败路径
        尝试已结算=True#成功路径结算尝试
        if not 仍是当前(世代容器):#已不是当前则退出
            return#退出
        状态['connectedAt']=time.time()*1000#记下连通时刻
        if 状态['failedAttempts']>0:#重连成功则记信息
            上下文.logger.info(标签+': reconnected and re-synced tools (attempt '+str(状态['failedAttempts'])+'/'+str(策略['maxAttempts'])+')')#重连成功

    def 关闭世代(世代容器):#关闭一代
        """尽力关闭会话与传输。"""
        会话=取字段(世代容器,'session')#会话
        管理器=取字段(世代容器,'cm')#上下文管理器
        if 会话 is not None and hasattr(会话,'close'):#有关闭面
            解开(会话.close())#关闭会话
        if 管理器 is not None:#有管理器
            if hasattr(管理器,'__aexit__'):#异步退出
                解开(管理器.__aexit__(None,None,None))#退出
            elif hasattr(管理器,'__exit__'):#同步退出
                管理器.__exit__(None,None,None)#退出
        关闭=状态['clientClosed']#关闭栅栏
        if 关闭 is not None:#有栅栏
            关闭.兑现(None)#放行

    状态['settling']=连接世代#先记下函数；下面立刻跑启动尝试
    def 跑启动():#立刻发起启动尝试
        """插件激活时的那一次尝试。"""
        try:#连接
            连接世代(True)#启动路径
        finally:#无论成败结算就绪
            if 状态['client'] is not None:#初次成功则无错误
                就绪.兑现({})#成功
            else:#失败则带上真实错误
                错误=状态['firstAttemptError'] or Exception(标签+': initial connection failed')#真实错误
                就绪.兑现({'error':错误})#带错误
    threading.Thread(target=跑启动,daemon=True).start()#后台启动，避免阻塞 apply 登记 effect

    def 拆除():#拆除监督器
        """停止重连，关闭存活客户端，等待静默，然后注销本服务器仍拥有的全部工具。"""
        状态['disposed']=True#标记已拆除
        定时=状态['reconnectTimer']#已武装定时器
        if 定时 is not None:#有定时器
            定时.cancel()#取消待发重连
            状态['reconnectTimer']=None#清除
        当前=状态['client']#捕获当前客户端
        当前关闭=状态['clientClosed']#捕获当前关闭承诺
        状态['client']=None#放弃当前所有权
        状态['clientClosed']=None#放弃关闭承诺引用
        if 当前 is not None:#仍有存活世代
            try:#尽力关闭
                关闭世代(当前)#关闭
            except BaseException:#传输已消失
                pass#忽略
            if 当前关闭 is not None and not 解开(等待关闭(当前关闭)):#关闭超时
                上下文.logger.error(标签+': generation did not close within '+str(世代关闭超时毫秒)+'ms during disposal — server shutdown may be incomplete')#拆除时关闭不完整
        解开(状态['syncChain'])#等待同步链排空
        for 注销 in 状态['disposers'].values():#注销全部工具
            注销()#注销
        状态['disposers']={}#清空 disposer

    return {'ready':就绪,'dispose':拆除}#句柄

def 已兑现链():#立刻兑现的链起点
    """同步串行链起点。"""
    已兑现=cordis.工具.已兑现#立刻兑现
    return 已兑现(None)#已完成
