import os,subprocess,threading,time#环境、子进程、线程与超时
from concurrent.futures import Future as 原生结果#单次操作结果
from collections import deque#有界 stderr 尾
from ..协议 import 换行JSONRPC传输,JSONRPC响应错误#传输与对端错误
from .拆除 import 拆除运行时进程#运行时进程拆除阶梯

__all__=[#仅中文公开名
    '传输已关闭错误','请求超时错误','SDK协议错误',
    '通知订阅','装备客户端','是否普通对象',
    '操作任务','中止信号','中止控制器','已中止',
]#公开面结束

标准错误尾上限=400#stderr 尾部最多保留行数
流落定毫秒=100#流落定等待毫秒

class SDK客户端错误(Exception):
    """本包异常基类。"""

class 传输已关闭错误(SDK客户端错误):
    """运行时子进程已消失或不可用。"""
    def __init__(自身,消息):
        """记下失败描述，含任何 stderr 尾部。"""
        super().__init__(消息)#交给基类
        自身.name='TransportClosedError'#固定错误名

class 请求超时错误(SDK客户端错误):
    """某次请求超过了 requestTimeoutMs。"""
    def __init__(自身,消息):
        """记下哪个方法超时。"""
        super().__init__(消息)#交给基类
        自身.name='RequestTimeoutError'#固定错误名

class SDK协议错误(SDK客户端错误):
    """运行时给出了文档协议之外的应答。"""
    def __init__(自身,消息):
        """记下协议违规描述。"""
        super().__init__(消息)#交给基类
        自身.name='SdkProtocolError'#固定错误名

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身._未来.set_exception(SDK客户端错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止旗标
        自身._异常=None#中止时抛出的异常
        if 已中止标志:#创建时已中止
            自身._事件.set()#置位
            自身._异常=SDK客户端错误('请求已中止')#默认

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#已是异常
            自身._异常=原因#承载
        elif 原因 is not None:#非异常
            自身._异常=SDK客户端错误(str(原因))#包装
        else:#无原因
            自身._异常=SDK客户端错误('请求已中止')#默认
        自身._事件.set()#置位

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
    return 信号._事件.is_set()#Event 置位

def 是否普通对象(值):
    """当且仅当值是非 null、非数组对象时为真。"""
    return isinstance(值,dict)#排除 list 等

def 错误消息(错误):
    """取出错误消息。"""
    return str(错误)#字符串化

def 选项字段(选项,键,缺省=None):
    """从启动选项 dict 读键；缺席为缺省。"""
    if 键 in 选项:#自有键
        return 选项[键]#取值
    return 缺省#缺席

class 通知订阅:
    """HarnessClient.subscribe 返回的客户端通知流。"""
    def __init__(自身,状态,卸订阅):
        """记下共享状态与卸订阅。"""
        自身.状态=状态#共享状态
        自身.卸订阅=卸订阅#从客户端表删除本订阅

    def 下一条(自身):
        """等待下一条匹配的通知。"""
        if len(自身.状态['queue'])>0:#有存货
            return 自身.状态['queue'].pop(0)#立刻兑现
        if 自身.状态['failure'] is not None:#已失败
            raise 自身.状态['failure']#拒绝
        等待=操作任务()#挂起
        自身.状态['waiters'].append(等待)#等后续 push
        return 等待.等待()#阻塞取

    def 关闭(自身):
        """已排队项丢弃，未完成等待者拒绝。"""
        自身.卸订阅()#从客户端表删除
        自身.状态['queue'].clear()#丢掉未取走的通知
        自身.失败(传输已关闭错误('通知订阅已关闭'))#拒绝未完成等待者

    def 失败(自身,错误):
        """首次失败胜出；已入队通知仍可排空。"""
        if 自身.状态['failure'] is None:#只记下第一次
            自身.状态['failure']=错误#终结失败
        等待者=自身.状态['waiters']#取出
        自身.状态['waiters']=[]#清空
        for 一项 in 等待者:#拒绝并清空等待者
            一项.拒绝(自身.状态['failure'])#拒绝

    def 推送(自身,通知):
        """过滤器抛错只让本订阅失败。"""
        try:
            过滤=自身.状态['filter']#可选判断
            匹配=过滤 is None or 过滤(通知)#无过滤器则全部匹配
        except BaseException as 错误:
            自身.卸订阅()#卸下本订阅
            if isinstance(错误,BaseException):#已是异常
                自身.失败(错误)#原样终结
            else:#非异常
                自身.失败(SDK客户端错误(str(错误)))#包装终结
            return#不再投递
        if not 匹配:#不匹配
            return#丢弃
        if len(自身.状态['waiters'])>0:#有人在等
            自身.状态['waiters'].pop(0).兑现(通知)#交给等待者
        else:#否则入队
            自身.状态['queue'].append(通知)#入队

class 装备客户端:
    """经子进程标准输入输出对接 DeepSeek Harness SDK 运行时的 JSON-RPC 客户端。"""
    def __init__(自身,选项):
        """记下启动规格、完整子进程环境与超时。"""
        自身.选项=选项#启动选项 dict
        自身.子进程=None#已拉起的子进程
        自身.传输=None#绑在子进程 stdio 上的传输
        自身.标准错误尾=deque(maxlen=标准错误尾上限)#保留的 stderr 尾部行
        自身.订阅表={}#活动通知订阅
        自身.会话父表={}#子会话 → 父会话，用于树过滤
        自身.订阅序号=0#订阅 id 序号
        自身.退出码=None#子进程退出码；未退出则为特殊哨兵
        自身._已退出=False#是否已见 exit
        自身.拉起错误=None#spawn 失败错误
        自身.流落定=操作任务()#stderr 关闭与 exit 都发生后兑现
        自身.流落定.兑现(None)#初始已落定（尚未 start）
        自身.关闭任务=None#close 去重任务
        自身.锁=threading.Lock()#订阅表互斥

    def 启动(自身):
        """进程仍活着时幂等；关闭之后拒绝复用。"""
        if 自身.关闭任务 is not None:#已关闭
            raise 传输已关闭错误('DeepSeek Harness 运行时客户端已关闭')#不能再 start
        if 自身.子进程 is not None:#已有子进程
            return#幂等返回
        命令=选项字段(自身.选项,'command')#运行时命令
        原始参数=选项字段(自身.选项,'args')#可选命令参数
        参数=list(原始参数) if 原始参数 is not None else []#缺席为空列表
        工作目录=选项字段(自身.选项,'cwd')#可选工作目录
        环境=选项字段(自身.选项,'env')#可选完整子进程环境
        if 环境 is None:#缺省继承当前进程
            环境=os.environ.copy()#继承
        子=subprocess.Popen(#按选项 spawn 运行时
            [命令,*参数],#命令行
            cwd=工作目录,#工作目录
            env=环境,#环境
            stdin=subprocess.PIPE,#管道 stdin
            stdout=subprocess.PIPE,#管道 stdout
            stderr=subprocess.PIPE,#管道 stderr
            bufsize=0,#无缓冲
        )#spawn 结束
        自身.子进程=子#记下子进程
        落定旗={'stderr':False,'exited':False}#两旗
        自身.流落定=操作任务()#新的落定任务
        def 或许落定():
            """通知等待流落定的人。"""
            if 落定旗['stderr'] and 落定旗['exited']:#都齐
                自身.流落定.兑现(None)#兑现
        def 监视退出():
            """记下退出码并让订阅失败。"""
            码=子.wait()#等待退出
            自身.退出码=码#记下退出码
            自身._已退出=True#标记已退出
            落定旗['exited']=True#标记已退出
            或许落定()#尝试兑现落定
            自身.令订阅失败(自身._关闭错误('DeepSeek Harness 运行时已退出'))#让订阅失败
            if 自身.传输 is not None:#有传输
                自身.传输.关闭()#关闭传输
        threading.Thread(target=监视退出,daemon=True).start()#监视 exit
        def 读标准错误():
            """追加 stderr 块到有界尾部。"""
            try:
                while True:#直到 EOF
                    块=子.stderr.read(4096)#一块
                    if not 块:#EOF
                        break
                    if isinstance(块,bytes):#字节块
                        文本=块.decode('utf-8',errors='replace')#解码
                    else:#已是文本
                        文本=块#原样
                    for 行 in 文本.splitlines():#按行
                        if 行!='':#非空
                            自身.标准错误尾.append(行)#写入尾部
            except OSError:
                pass#管道错误忽略
            落定旗['stderr']=True#标记 stderr 已关
            或许落定()#尝试兑现落定
        threading.Thread(target=读标准错误,daemon=True).start()#读 stderr
        传输=换行JSONRPC传输(子.stdout,子.stdin)#stdout 入、stdin 出
        def 派发通知(方法,参数):
            """把通知交给订阅。"""
            自身._派发通知({'method':方法,'params':参数})#统一形状
        传输.当通知(派发通知)#挂通知
        传输.启动()#开始读帧
        自身.传输=传输#记下传输

    def 初始化(自身,参数):
        """执行进程级握手。"""
        结果=自身.请求('initialize',dict(参数))#发 initialize
        信息=结果['serverInfo'] if 是否普通对象(结果) and 'serverInfo' in 结果 else None#serverInfo
        if (not 是否普通对象(信息)
            or 'name' not in 信息
            or 'version' not in 信息
            or not isinstance(信息['name'],str)
            or not isinstance(信息['version'],str)):#缺少身份
            raise SDK协议错误('initialize 未返回服务器身份：'+str(结果))#协议错误
        return {'serverInfo':{'name':信息['name'],'version':信息['version']}}#只交出线稳定字段

    def 提示(自身,会话号,内容块列表):
        """排队一条提示并返回其持久收件箱身份。"""
        结果=自身.请求('session/prompt',{'sessionId':会话号,'contentBlocks':内容块列表})#发
        if (not 是否普通对象(结果)) or 'messageId' not in 结果 or not isinstance(结果['messageId'],str):#缺 messageId
            raise SDK协议错误('session/prompt 未返回消息 id：'+str(结果))#协议错误
        return 结果['messageId']#交出消息 id

    def 请求(自身,方法,参数=None,超时毫秒=None):
        """发送 JSON-RPC 请求并等待结果。"""
        自身.启动()#惰性确保子进程已启动
        if 自身._已退出 or 自身.拉起错误 is not None:#已经退出或 spawn 失败
            自身._落定流()#等 stderr/exit 落定以便拼诊断
            raise 自身._关闭错误('DeepSeek Harness 运行时未在运行')#带退出码与 stderr 尾部
        传输=自身.传输#取出传输
        if 传输 is None:#start 后仍无传输
            raise 传输已关闭错误('DeepSeek Harness 运行时未在运行')#关闭
        if 超时毫秒 is not None:#调用方给了单次超时
            超时=超时毫秒#用单次
        elif 'requestTimeoutMs' in 自身.选项:#选项默认
            超时=自身.选项['requestTimeoutMs']#用选项
        else:#都没有
            超时=None#一直等
        try:
            载荷=参数 if 参数 is not None else {}#缺 params 则空对象
            if 超时 is None:#无超时则一直等
                return 传输.请求(方法,载荷)#同步等
            控制器=中止控制器()#超时用的中止
            def 到期():
                """到期后 abort，带方法名与毫秒数。"""
                time.sleep(超时/1000.0)#等待
                控制器.中止(请求超时错误(方法+' 等待 DeepSeek Harness 运行时超时，已过 '+str(超时)+'ms'))#中止
            threading.Thread(target=到期,daemon=True).start()#定时
            return 传输.请求(方法,载荷,控制器.信号)#带信号发请求
        except JSONRPC响应错误:
            raise#原样
        except 请求超时错误:
            raise#原样
        except BaseException as 错误:
            自身._落定流()#等流落定
            raise 自身._关闭错误(错误消息(错误))#包成传输已关闭错误

    def 订阅(自身,过滤=None):
        """订阅服务端通知。"""
        标识=str(自身.订阅序号)#分配订阅 id
        自身.订阅序号+=1#递增
        状态={'queue':[],'waiters':[],'filter':过滤,'failure':None}#空队列、无失败
        def 卸下():
            """删除本订阅。"""
            with 自身.锁:#互斥
                自身.订阅表.pop(标识,None)#删除
        订阅=通知订阅(状态,卸下)#构造句柄
        if 自身.关闭任务 is not None or 自身._已退出 or 自身.拉起错误 is not None:#客户端已关或进程已死
            订阅.失败(自身._关闭错误('DeepSeek Harness 运行时已关闭'))#生来失败
            return 订阅#仍返回句柄
        with 自身.锁:#互斥
            自身.订阅表[标识]=订阅#登记活动订阅
        return 订阅#交给调用方

    def 订阅会话树(自身,会话号):
        """订阅一个会话以及从 subagent.started 系谱边发现的后代。"""
        def 过滤(通知):
            """树过滤。"""
            原始参数=通知['params'] if 'params' in 通知 else None#通知载荷
            参数=原始参数 if isinstance(原始参数,dict) else {}#非对象则空对象
            方法=通知['method'] if 'method' in 通知 else None#方法名
            if 方法=='subagent.started' or 方法=='subagent.finished':#子智能体生命周期
                父号=参数['parentSessionId'] if 'parentSessionId' in 参数 else None#父会话 id
                if isinstance(父号,str) and 自身._是后代(父号,会话号):#父在树内
                    return True#匹配
                子号=参数['childSessionId'] if 'childSessionId' in 参数 else None#子会话
                return 子号==会话号#或子会话本身就是根
            相关号=参数['sessionId'] if 'sessionId' in 参数 else None#普通会话类通知的 sessionId
            return isinstance(相关号,str) and 自身._是后代(相关号,会话号)#该会话是根或其后代
        return 自身.订阅(过滤)#过滤后的订阅

    def 关闭(自身):
        """先协议 shutdown，再走拆除阶梯。幂等。同步返回。"""
        if 自身.关闭任务 is None:#首次调用才真正关闭
            自身._执行关闭()#实际关闭
            自身.关闭任务=True#记忆已关
        return#无返回值

    def _执行关闭(自身):
        """完整拆除。"""
        子=自身.子进程#取出子进程
        if 子 is None:#从未 start
            return#无事可做
        if 'shutdownTimeoutMs' in 自身.选项 and 自身.选项['shutdownTimeoutMs'] is not None:#调用方给了宽限
            关超时=自身.选项['shutdownTimeoutMs']#用选项
        else:#缺席
            关超时=1000#默认 1 秒
        try:
            自身.请求('shutdown',None,关超时)#先尽量走协议 shutdown
        except BaseException as 错误:
            自身.标准错误尾.append('shutdown 请求失败：'+错误消息(错误))#写入 stderr 尾部
        if 'disposeEofGraceMs' in 自身.选项 and 自身.选项['disposeEofGraceMs'] is not None:#EOF 宽限
            eof宽限=自身.选项['disposeEofGraceMs']#用选项
        else:#缺席
            eof宽限=6000#默认 6 秒
        if 'disposeGraceMs' in 自身.选项 and 自身.选项['disposeGraceMs'] is not None:#SIGTERM 宽限
            杀宽限=自身.选项['disposeGraceMs']#用选项
        else:#缺席
            杀宽限=3000#默认 3 秒
        拆除运行时进程(子,{#走 EOF → SIGTERM → SIGKILL
            'disposeEofGraceMs':eof宽限,#EOF 宽限
            'disposeGraceMs':杀宽限,#SIGTERM 宽限
        })#拆除阶梯结束
        if 自身.传输 is not None:#有传输
            自身.传输.关闭()#关掉传输
        自身.令订阅失败(自身._关闭错误('DeepSeek Harness 运行时已关闭'))#让剩余订阅失败

    def _派发通知(自身,通知):
        """先记下子智能体系谱。"""
        自身._记录会话关系(通知)#先记下
        with 自身.锁:#互斥
            列表=list(自身.订阅表.values())#快照
        for 订阅 in 列表:#逐个 push
            订阅.推送(通知)#过滤器各自决定

    def _记录会话关系(自身,通知):
        """只关心启动边。"""
        方法=通知['method'] if 'method' in 通知 else None#方法名
        if 方法!='subagent.started':#不是启动
            return#忽略
        原始参数=通知['params'] if 'params' in 通知 else None#载荷
        参数=原始参数 if isinstance(原始参数,dict) else {}#非对象则空对象
        父号=参数['parentSessionId'] if 'parentSessionId' in 参数 else None#父会话
        子号=参数['childSessionId'] if 'childSessionId' in 参数 else None#子会话
        if isinstance(父号,str) and 父号!='' and isinstance(子号,str) and 子号!='' and 父号!=子号:#有效边
            自身.会话父表[子号]=父号#登记子 → 父

    def _是后代(自身,会话号,根会话号):
        """沿父链上走，防环。"""
        已见=set()#防环
        当前=会话号#沿父链上走
        while 当前 not in 已见:#未见过的节点继续
            if 当前==根会话号:#走到根
                return True#在树内
            已见.add(当前)#记下已走
            父=自身.会话父表[当前] if 当前 in 自身.会话父表 else None#查父
            if 父 is None:#到顶仍不是根
                return False#不在树内
            当前=父#继续向上
        return False#环防护

    def 令订阅失败(自身,错误):
        """首次失败胜出。"""
        with 自身.锁:#互斥
            列表=list(自身.订阅表.values())#快照
        for 订阅 in 列表:#逐个
            订阅.失败(错误)

    def _落定流(自身):
        """落定或超时先到先得。"""
        截止=time.time()+流落定毫秒/1000.0#截止
        while time.time()<截止:#未超时
            if 自身.流落定._未来.done():#已落定
                break#停
            time.sleep(0.01)#小睡
        return

    def _关闭错误(自身,原因):
        """多段用换行拼。"""
        段列表=[原因]#先放原因
        if 自身.拉起错误 is not None:#有 spawn 错误
            段列表.append('拉起错误：'+错误消息(自身.拉起错误))#附上
        if 自身._已退出:#有退出码
            段列表.append('退出码：'+str(自身.退出码))#附上
        if len(自身.标准错误尾)>0:#有 stderr 尾
            段列表.append('标准错误尾部：\n'+'\n'.join(自身.标准错误尾))#附上
        return 传输已关闭错误('\n'.join(段列表))#多段拼
