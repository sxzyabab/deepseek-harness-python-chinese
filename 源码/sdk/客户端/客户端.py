"""面向 DeepSeek Harness SDK 运行时子进程的底层 JSON-RPC 客户端。

对齐上游 `sdk/client/src/client.ts`。公开面仅中文名。经子进程标准输入输出讲 sdk_protocol 线协议；设计对偶是仓库 python/sdk 的 HarnessClient。本客户端运行在任何 harness 上下文之外，因此直接 spawn，不走 subprocess 服务。
"""
import os,subprocess,threading,time#环境、子进程、线程与超时
from collections import deque#有界 stderr 尾
from cordis.工具 import 承诺,已兑现,是否thenable#承诺、立刻兑现与可等待
from sdk_protocol import 换行JSONRPC传输,JSONRPC响应错误#传输与对端错误
from .拆除 import 拆除运行时进程#运行时进程拆除阶梯

__all__=[#仅中文公开名
    '传输已关闭错误','请求超时错误','SDK协议错误',
    '通知订阅','装备客户端','是否普通对象',
]#公开面结束

标准错误尾上限=400#stderr 尾部最多保留行数
流落定毫秒=100#流落定等待毫秒

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否普通对象(值):#普通 JSON 对象谓词
    """当且仅当值是非 null、非数组对象时为真。"""
    return isinstance(值,dict)#排除 list 等

def 错误消息(错误):#取出错误消息
    """非 Exception 则字符串化。"""
    if isinstance(错误,BaseException):#异常
        return str(错误)#消息
    return str(错误)#兜底

class 传输已关闭错误(Exception):#传输已关闭或进程不可用
    """运行时子进程已消失或不可用。"""
    def __init__(自身,消息):#用描述构造
        """记下失败描述，含任何 stderr 尾部。"""
        super().__init__(消息)#交给 Exception
        自身.name='TransportClosedError'#固定错误名

class 请求超时错误(Exception):#请求超时
    """某次请求超过了 requestTimeoutMs。"""
    def __init__(自身,消息):#用描述构造
        """记下哪个方法超时。"""
        super().__init__(消息)#交给 Exception
        自身.name='RequestTimeoutError'#固定错误名

class SDK协议错误(Exception):#协议字段不符合约定
    """运行时给出了文档协议之外的应答。"""
    def __init__(自身,消息):#用描述构造
        """记下协议违规描述。"""
        super().__init__(消息)#交给 Exception
        自身.name='SdkProtocolError'#固定错误名

class 通知订阅:#公开通知订阅句柄
    """HarnessClient.subscribe 返回的客户端通知流。"""
    def __init__(自身,状态,卸订阅):#绑定状态与卸订阅回调
        """记下共享状态与卸订阅。"""
        自身.状态=状态#共享状态
        自身.卸订阅=卸订阅#从客户端表删除本订阅

    def 下一条(自身):#取下一条或挂起
        """等待下一条匹配的通知。"""
        if 自身.状态['queue']:#有存货
            return 自身.状态['queue'].pop(0)#立刻兑现
        if 自身.状态['failure'] is not None:#已失败
            raise 自身.状态['failure']#拒绝
        等待=承诺()#挂起
        自身.状态['waiters'].append(等待)#等后续 push
        return 解开(等待)#阻塞取

    def 试取(自身):#非阻塞取队列头
        """没有则为 None。"""
        if 自身.状态['queue']:#有存货
            return 自身.状态['queue'].pop(0)#取出
        return None#没有

    def 关闭(自身):#关闭订阅
        """已排队项丢弃，未完成等待者拒绝。"""
        自身.卸订阅()#从客户端表删除
        自身.状态['queue'].clear()#丢掉未取走的通知
        自身.失败(传输已关闭错误('notification subscription closed'))#拒绝未完成等待者

    def 失败(自身,错误):#标记终结失败
        """首次失败胜出；已入队通知仍可排空。"""
        if 自身.状态['failure'] is None:#只记下第一次
            自身.状态['failure']=错误#终结失败
        等待者=自身.状态['waiters']#取出
        自身.状态['waiters']=[]#清空
        for 一项 in 等待者:#拒绝并清空等待者
            一项.拒绝(自身.状态['failure'])#拒绝

    def 推送(自身,通知):#尝试投递一条通知
        """过滤器抛错只让本订阅失败。"""
        try:#过滤器抛错只影响本订阅
            过滤=自身.状态['filter']#可选谓词
            匹配=过滤 is None or 过滤(通知)#无过滤器则全部匹配
        except BaseException as 错误:#过滤器抛错
            自身.卸订阅()#卸下本订阅
            自身.失败(错误 if isinstance(错误,Exception) else Exception(str(错误)))#终结
            return#不再投递
        if not 匹配:#不匹配
            return#丢弃
        if 自身.状态['waiters']:#有人在等
            自身.状态['waiters'].pop(0).兑现(通知)#交给等待者
        else:#否则入队
            自身.状态['queue'].append(通知)#入队

class 装备客户端:#SDK 运行时客户端
    """经子进程标准输入输出对接 DeepSeek Harness SDK 运行时的 JSON-RPC 客户端。"""
    def __init__(自身,选项):#保存启动选项
        """记下启动规格、完整子进程环境与超时。"""
        自身.选项=选项#启动选项
        自身.子进程=None#已拉起的子进程
        自身.传输=None#绑在子进程 stdio 上的传输
        自身.标准错误尾=deque(maxlen=标准错误尾上限)#保留的 stderr 尾部行
        自身.订阅们={}#活动通知订阅
        自身.会话父们={}#子会话 → 父会话，用于树过滤
        自身.订阅序号=0#订阅 id 序号
        自身.退出码=None#子进程退出码；未退出则为特殊哨兵
        自身._已退出=False#是否已见 exit
        自身.拉起错误=None#spawn 失败错误
        自身.流落定=承诺()#stderr 关闭与 exit 都发生后兑现
        自身.流落定.兑现(None)#初始已落定（尚未 start）
        自身.关闭任务=None#close 去重任务
        自身.锁=threading.Lock()#订阅表互斥

    def 启动(自身):#确保子进程与传输已启动
        """进程仍活着时幂等；关闭之后拒绝复用。"""
        if 自身.关闭任务 is not None:#已关闭
            raise 传输已关闭错误('DeepSeek Harness runtime client is closed')#不能再 start
        if 自身.子进程 is not None:#已有子进程
            return#幂等返回
        命令=取字段(自身.选项,'command')#运行时命令
        参数=list(取字段(自身.选项,'args') or [])#可选命令参数
        工作目录=取字段(自身.选项,'cwd')#可选工作目录
        环境=取字段(自身.选项,'env')#可选完整子进程环境
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
        自身.流落定=承诺()#新的落定承诺
        def 或许落定():#两旗都立起才兑现
            """通知等待流落定的人。"""
            if 落定旗['stderr'] and 落定旗['exited']:#都齐
                自身.流落定.兑现(None)#兑现
        def 盯退出():#进程退出
            """记下退出码并让订阅失败。"""
            码=子.wait()#等待退出
            自身.退出码=码#记下退出码
            自身._已退出=True#标记已退出
            落定旗['exited']=True#标记已退出
            或许落定()#尝试兑现落定
            自身._失败订阅们(自身._关闭错误('DeepSeek Harness runtime exited'))#让订阅失败
            if 自身.传输 is not None:#有传输
                自身.传输.关闭()#关闭传输
        threading.Thread(target=盯退出,daemon=True).start()#盯 exit
        def 读标准错误():#追加 stderr 块
            """有界尾部。"""
            try:#读 stderr
                while True:#直到 EOF
                    块=子.stderr.read(4096)#一块
                    if not 块:#EOF
                        break#结束
                    文本=块.decode('utf-8',errors='replace') if isinstance(块,bytes) else 块#解码
                    for 行 in 文本.splitlines():#按行
                        if 行:#非空
                            自身.标准错误尾.append(行)#写入尾部
            except BaseException:#管道错误
                pass#忽略
            落定旗['stderr']=True#标记 stderr 已关
            或许落定()#尝试兑现落定
        threading.Thread(target=读标准错误,daemon=True).start()#读 stderr
        传输=换行JSONRPC传输(子.stdout,子.stdin)#stdout 入、stdin 出
        def 派发通知(方法,参数):#把通知交给订阅
            """扇出到所有订阅。"""
            自身._派发通知({'method':方法,'params':参数})#统一形状
        传输.当通知(派发通知)#挂通知
        传输.启动()#开始读帧
        自身.传输=传输#记下传输

    def 初始化(自身,参数):#握手
        """执行进程级握手。"""
        结果=解开(自身.请求('initialize',dict(参数)))#发 initialize
        信息=取字段(结果,'serverInfo') if 是否普通对象(结果) else None#serverInfo
        if (not 是否普通对象(信息)
            or not isinstance(取字段(信息,'name'),str)
            or not isinstance(取字段(信息,'version'),str)):#缺少身份
            raise SDK协议错误('initialize returned no server identity: '+str(结果))#协议错误
        return {'serverInfo':{'name':信息['name'],'version':信息['version']}}#只交出线稳定字段

    def 提示(自身,会话号,内容块们):#发一条用户提示
        """排队一条提示并返回其持久收件箱身份。"""
        结果=解开(自身.请求('session/prompt',{'sessionId':会话号,'contentBlocks':内容块们}))#发
        if (not 是否普通对象(结果)) or not isinstance(取字段(结果,'messageId'),str):#缺 messageId
            raise SDK协议错误('session/prompt returned no message id: '+str(结果))#协议错误
        return 结果['messageId']#交出消息 id

    def 请求(自身,方法,参数=None,超时毫秒=None):#底层请求
        """发送 JSON-RPC 请求并等待结果。"""
        自身.启动()#惰性确保子进程已启动
        if 自身._已退出 or 自身.拉起错误 is not None:#已经退出或 spawn 失败
            自身._落定流()#等 stderr/exit 落定以便拼诊断
            raise 自身._关闭错误('DeepSeek Harness runtime is not running')#带退出码与 stderr 尾部
        传输=自身.传输#取出传输
        if 传输 is None:#start 后仍无传输
            raise 传输已关闭错误('DeepSeek Harness runtime is not running')#关闭
        超时=超时毫秒 if 超时毫秒 is not None else 取字段(自身.选项,'requestTimeoutMs')#单次超时或选项默认
        try:#向传输发请求
            if 超时 is None:#无超时则一直等
                return 解开(传输.请求(方法,参数 if 参数 is not None else {}))#一直等
            放弃=承诺()#超时用的放弃标记（用线程模拟 AbortSignal）
            class 信号:#简易中止信号
                """对齐 AbortSignal 的最小面。"""
                def __init__(自身信号):#初始未中止
                    """记下状态。"""
                    自身信号.aborted=False#未中止
                    自身信号.reason=None#原因
                    自身信号._监听=[]#abort 监听
                def addEventListener(自身信号,名,回调,选项=None):#听 abort
                    """只支持 abort。"""
                    if 名=='abort':#abort
                        自身信号._监听.append(回调)#登记
                def removeEventListener(自身信号,名,回调):#卸监听
                    """卸 abort。"""
                    if 回调 in 自身信号._监听:#在表中
                        自身信号._监听.remove(回调)#卸掉
                def 中止(自身信号,原因):#触发中止
                    """通知监听。"""
                    自身信号.aborted=True#已中止
                    自身信号.reason=原因#原因
                    for 回 in list(自身信号._监听):#逐个
                        回()#回调
            放弃信号=信号()#新建
            def 到期():#到期后 abort
                """带方法名与毫秒数。"""
                time.sleep(超时/1000.0)#等待
                放弃信号.中止(请求超时错误(方法+' timed out after '+str(超时)+'ms waiting for the DeepSeek Harness runtime'))#abort
            threading.Thread(target=到期,daemon=True).start()#定时
            return 解开(传输.请求(方法,参数 if 参数 is not None else {},放弃信号))#带信号发请求
        except (JSONRPC响应错误,请求超时错误):#这两类原样抛出
            raise#原样
        except BaseException as 错误:#传输级失败
            自身._落定流()#等流落定
            raise 自身._关闭错误(错误消息(错误))#包成传输已关闭错误

    def 订阅(自身,过滤=None):#新建通知订阅
        """订阅服务端通知。"""
        标识=str(自身.订阅序号)#分配订阅 id
        自身.订阅序号+=1#递增
        状态={'queue':[],'waiters':[],'filter':过滤,'failure':None}#空队列、无失败
        def 卸下():#卸下时从表删除
            """删除本订阅。"""
            with 自身.锁:#互斥
                自身.订阅们.pop(标识,None)#删除
        订阅=通知订阅(状态,卸下)#构造句柄
        if 自身.关闭任务 is not None or 自身._已退出 or 自身.拉起错误 is not None:#客户端已关或进程已死
            订阅.失败(自身._关闭错误('DeepSeek Harness runtime closed'))#生来失败
            return 订阅#仍返回句柄
        with 自身.锁:#互斥
            自身.订阅们[标识]=订阅#登记活动订阅
        return 订阅#交给调用方

    def 订阅会话树(自身,会话号):#按会话树过滤通知
        """订阅一个会话以及从 subagent.started 系谱边发现的后代。"""
        def 过滤(通知):#谓词：与根或其后代相关
            """树过滤。"""
            参数=取字段(通知,'params') or {}#通知载荷
            方法=取字段(通知,'method')#方法名
            if 方法=='subagent.started' or 方法=='subagent.finished':#子智能体生命周期
                父号=取字段(参数,'parentSessionId')#父会话 id
                if isinstance(父号,str) and 自身._是后代(父号,会话号):#父在树内
                    return True#匹配
                return 取字段(参数,'childSessionId')==会话号#或子会话本身就是根
            相关号=取字段(参数,'sessionId')#普通会话类通知的 sessionId
            return isinstance(相关号,str) and 自身._是后代(相关号,会话号)#该会话是根或其后代
        return 自身.订阅(过滤)#过滤后的订阅

    def 关闭(自身):#关闭客户端与子进程
        """先协议 shutdown，再走拆除阶梯。幂等。"""
        if 自身.关闭任务 is None:#首次调用才真正关闭
            自身.关闭任务=已兑现(自身._执行关闭())#记忆
        return 自身.关闭任务#后续共用同一承诺

    def _执行关闭(自身):#实际关闭序列
        """完整拆除。"""
        子=自身.子进程#取出子进程
        if 子 is None:#从未 start
            return#无事可做
        try:#先尽量走协议 shutdown
            解开(自身.请求('shutdown',None,取字段(自身.选项,'shutdownTimeoutMs') or 1000))#默认 1 秒
        except BaseException as 错误:#shutdown 失败只记诊断
            自身.标准错误尾.append('shutdown request failed: '+错误消息(错误))#写入 stderr 尾部
        拆除运行时进程(子,{#走 EOF → SIGTERM → SIGKILL
            'disposeEofGraceMs':取字段(自身.选项,'disposeEofGraceMs') or 6000,#EOF 宽限默认 6 秒
            'disposeGraceMs':取字段(自身.选项,'disposeGraceMs') or 3000,#SIGTERM 宽限默认 3 秒
        })#拆除阶梯结束
        if 自身.传输 is not None:#有传输
            自身.传输.关闭()#关掉传输
        自身._失败订阅们(自身._关闭错误('DeepSeek Harness runtime closed'))#让剩余订阅失败

    def _派发通知(自身,通知):#把一条通知扇出到所有订阅
        """先记下子智能体系谱。"""
        自身._记录会话关系(通知)#先记下
        with 自身.锁:#互斥
            列表=list(自身.订阅们.values())#快照
        for 订阅 in 列表:#逐个 push
            订阅.推送(通知)#过滤器各自决定

    def _记录会话关系(自身,通知):#从 started 通知记下父子边
        """只关心启动边。"""
        if 取字段(通知,'method')!='subagent.started':#不是启动
            return#忽略
        参数=取字段(通知,'params') or {}#载荷
        父号=取字段(参数,'parentSessionId')#父会话
        子号=取字段(参数,'childSessionId')#子会话
        if isinstance(父号,str) and 父号!='' and isinstance(子号,str) and 子号!='' and 父号!=子号:#有效边
            自身.会话父们[子号]=父号#登记子 → 父

    def _是后代(自身,会话号,根会话号):#sessionId 是否为根或其后代（含自身）
        """沿父链上走，防环。"""
        已见=set()#防环
        当前=会话号#沿父链上走
        while 当前 not in 已见:#未见过的节点继续
            if 当前==根会话号:#走到根
                return True#在树内
            已见.add(当前)#记下已走
            父=自身.会话父们.get(当前)#查父
            if 父 is None:#到顶仍不是根
                return False#不在树内
            当前=父#继续向上
        return False#环防护

    def _失败订阅们(自身,错误):#让所有订阅以同一错误失败
        """首次失败胜出。"""
        with 自身.锁:#互斥
            列表=list(自身.订阅们.values())#快照
        for 订阅 in 列表:#逐个
            订阅.失败(错误)#失败

    def _落定流(自身):#等待流落定，但有上限
        """落定或超时先到先得。"""
        截止=time.time()+流落定毫秒/1000.0#截止
        while time.time()<截止:#未超时
            if 自身.流落定._已定:#已落定
                break#停
            time.sleep(0.01)#小睡
        return#结束

    def _关闭错误(自身,原因):#拼带进程上下文的关闭错误
        """多段用换行拼。"""
        段们=[原因]#先放原因
        if 自身.拉起错误 is not None:#有 spawn 错误
            段们.append('spawn error: '+错误消息(自身.拉起错误))#附上
        if 自身._已退出:#有退出码
            段们.append('exit code: '+str(自身.退出码))#附上
        if 自身.标准错误尾:#有 stderr 尾
            段们.append('stderr tail:\n'+'\n'.join(自身.标准错误尾))#附上
        return 传输已关闭错误('\n'.join(段们))#多段拼
