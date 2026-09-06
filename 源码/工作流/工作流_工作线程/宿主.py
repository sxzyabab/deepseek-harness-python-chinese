"""一次工作流运行的宿主侧。第一份 worker 结果、意外死亡、或取消宽限到期拥有结算权并关闭消息准入。待启动项共享一条中止信号；已发布的子运行共享幂等清理，静止等待两者，并对缺失的结束事件做合成。"""
import os,queue,tempfile,threading,time#平台、队列、临时目录、线程与宽限睡眠
from concurrent.futures import Future as 原生结果#单次操作结果
from ...模型后端.llm import 断言永不#穷尽检查
from ...内核.会话 import 快照json值#JSON 无损快照
from ...工具.超时 import 中止控制器,已中止#中止原语
from ..工作流 import 工作流错误#本包异常
from ..工作流.运行时类型 import 工作流运行#存活运行协议
from .领域 import 渲染抛出#抛出值渲染
from .协议 import 宿主到工作线程类型,工作线程到宿主类型#双向消息标签
from .会话 import 驱动工作线程会话#工作线程侧会话

class 操作任务:#单次操作的 Future 包装，只留 等待
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身.原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if 自身.原生结果.done() is False:#尚未结算
            自身.原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if 自身.原生结果.done() is False:#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身.原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身.原生结果.set_exception(工作流错误(str(错误),'AGENT_RESULT'))#包装拒绝

    def 等待(自身,超时=None):#阻塞等到结算
        """阻塞等到结算。"""
        return 自身.原生结果.result(timeout=超时)#取结果或抛错

class 队列端口:#同进程队列消息端口
    """把双向队列收成 MessagePort 形态，供会话与宿主共用。"""
    def __init__(自身,入队,出队,关闭标志):#绑定队列
        """绑定入队/出队与关闭标志。"""
        自身.入队=入队#收到的消息
        自身.出队=出队#发出的消息
        自身.关闭标志=关闭标志#关闭标志
        自身.处理=None#message 回调
        自身.泵=None#泵线程

    def postMessage(自身,消息):#投递一条消息
        """投递一条消息。消息是 dict。"""
        if 自身.关闭标志.is_set():#已关闭
            return#无处可投
        自身.出队.put(消息)#入出队

    def on(自身,事件,回调):#登记事件回调
        """登记 message 回调并启动泵。"""
        if 事件!='message':#只支持 message
            return#忽略
        自身.处理=回调#记住回调
        def 泵():#后台读入队
            """后台读入队直到关闭。"""
            while 自身.关闭标志.is_set() is False:#未关闭
                try:#带超时取消息
                    消息=自身.入队.get(timeout=0.05)#取一条
                except queue.Empty:#暂时没有
                    continue#再试
                if 消息 is None:#毒丸
                    break#结束
                if 自身.处理 is not None:#有回调
                    try:#分发
                        自身.处理(消息)#调用
                    except Exception:#回调可抛任意类型，泵必须活着
                        pass#收容
        自身.泵=threading.Thread(target=泵)#泵线程
        自身.泵.daemon=True#不挡住退出
        自身.泵.start()#启动

class 工作线程:#对齐 node:worker_threads.Worker 的最小宿主面
    """拉起驱动工作线程会话的守护线程，并经队列交换协议消息。"""
    def __init__(自身,初始化):#按初始化拉起
        """按初始化拉起。初始化是 dict。"""
        自身.到工作线程=queue.Queue()#宿主→工作线程
        自身.到宿主=queue.Queue()#工作线程→宿主
        自身.关闭=threading.Event()#关闭标志
        自身.消息回调=None#message 回调
        自身.错误回调=None#error 回调
        自身.退出回调=None#exit 回调
        自身.初始化=初始化#保存初始化（工作线程使用）
        自身.线程=threading.Thread(target=自身.主循环)#工作线程
        自身.线程.daemon=True#不挡住退出
        自身.泵=threading.Thread(target=自身.宿主泵)#宿主侧读泵
        自身.泵.daemon=True#不挡住退出
        自身.线程.start()#启动工作线程
        自身.泵.start()#启动宿主泵

    def 主循环(自身):#工作线程主体
        """在工作线程跑会话。"""
        端口=队列端口(自身.到工作线程,自身.到宿主,自身.关闭)#工作线程侧端口
        码=0#退出码
        try:#跑会话
            驱动工作线程会话(端口,自身.初始化)#驱动会话
        except Exception as 错误:#工作线程失败，领域可抛任意类型
            码=1#非零退出
            if 自身.错误回调 is not None:#有错误回调
                try:#通知
                    自身.错误回调(错误)#回调
                except Exception:#回调可抛任意类型
                    pass#收容
        finally:#无论如何退出
            自身.关闭.set()#关闭
            自身.到宿主.put(None)#毒丸结束宿主泵
            if 自身.退出回调 is not None:#有退出回调
                try:#通知
                    自身.退出回调(码)#回调
                except Exception:#回调可抛任意类型
                    pass#收容

    def 宿主泵(自身):#宿主侧读工作线程消息
        """宿主侧读工作线程消息直到关闭。"""
        while True:#直到毒丸
            消息=自身.到宿主.get()#阻塞取
            if 消息 is None:#毒丸
                break#结束
            if 自身.消息回调 is not None:#有回调
                try:#分发
                    自身.消息回调(消息)#调用
                except Exception:#回调可抛任意类型
                    pass#收容

    def on(自身,事件,回调):#登记事件回调
        """登记 message/error/exit/messageerror 回调。"""
        if 事件=='message':#消息
            自身.消息回调=回调#记住
        elif 事件=='error':#错误
            自身.错误回调=回调#记住
        elif 事件=='exit':#退出
            自身.退出回调=回调#记住
        elif 事件=='messageerror':#反序列化失败
            pass#本端口只传普通 dict，无独立 messageerror 源

    def postMessage(自身,消息):#向工作线程投递
        """向工作线程投递一条消息。消息是 dict。"""
        if 自身.关闭.is_set():#已关闭
            raise 工作流错误('worker is gone','AGENT_START')#投递失败
        自身.到工作线程.put(消息)#入队

    def 终止(自身):#终止工作线程
        """终止工作线程（协作：关闭标志 + 毒丸）。"""
        自身.关闭.set()#关闭
        自身.到工作线程.put(None)#毒丸结束工作线程泵
        自身.到宿主.put(None)#毒丸结束宿主泵
        if 自身.线程.is_alive() and threading.current_thread() is not 自身.线程:#不能 join 自己
            自身.线程.join(timeout=1.0)#有界等待

def 工作线程启动环境(平台=None,tsconfig路径=None):#构造清洗后的 worker 环境
    """清洗后的 worker 环境：无环境凭证、无 loader 标志。Windows 必须显式注入临时目录。未构建形态还会转发 TSX_TSCONFIG_PATH。"""
    if 平台 is None:#默认当前平台
        平台=os.name#nt 或 posix
    环境={}#从空环境开始
    if 平台=='nt' or 平台=='win32':#Windows 必须显式注入临时目录
        临时=tempfile.gettempdir()#取宿主真实临时路径
        环境['TMP']=临时#写入 TMP
        环境['TEMP']=临时#写入 TEMP
    if tsconfig路径 is not None:#未构建时转发 tsconfig 钉
        环境['TSX_TSCONFIG_PATH']=tsconfig路径#写入
    return 环境#返回清洗后的环境

class 子记录:#已发布子运行记录
    """一条已发布的子运行及其共享的静止期销毁事务。"""
    def __init__(自身,运行):#绑定运行句柄
        """绑定运行句柄。"""
        自身.运行=运行#子智能体运行句柄
        自身.销毁事务=None#进行中的销毁任务

class 工作线程运行(工作流运行):#宿主侧一次工作流运行
    """一次活着的 worker 引擎运行——能力缝的工作流运行，由 start() 直接返回。拥有工作线程、子运行登记表和结果结算；结果永不拒绝。"""
    def __init__(自身,上下文,子智能体,标识,元数据,父智能体,初始化,提供方,销毁宽限毫秒,观察者,信号):#构造一次宿主侧运行
        """构造一次宿主侧运行。"""
        自身.上下文=上下文#插件上下文
        自身.子智能体=子智能体#子智能体运行时
        自身.id=标识#运行标识（载荷键字面量）
        自身.meta=元数据#工作流身份（载荷键字面量）
        自身.父=父智能体#父智能体
        自身.提供方=提供方#子智能体提供方名
        自身.销毁宽限毫秒=销毁宽限毫秒#销毁宽限毫秒
        自身.观察者=观察者#执行观察者
        自身.结果=操作任务()#运行结果任务
        自身.已结算=False#是否已经结算
        自身.终态已占=False#终态是否已被占用
        自身.工作线程死亡已见=False#是否已观察到 worker 死亡
        自身.取消原因=None#取消原因，先到者获胜
        自身.宽限线程=None#取消宽限线程
        自身.工作线程已退出=False#线程是否已退出
        自身.宿主已启动=0#宿主已接受的启动子次数
        自身.子运行表={}#已发布子运行表
        自身.待启动=set()#进行中的启动子事务
        自身.活智能体={}#未配对的开始账本
        自身.静止等待者=[]#等待子运行静止的回调
        自身.控制器=中止控制器()#共享中止控制器
        自身.已销毁任务=None#公开销毁事务
        自身.锁=threading.Lock()#状态锁
        自身.工作线程=工作线程(初始化)#拉起工作线程
        自身.工作线程.on('message',自身.收消息)#分发 worker 消息
        自身.工作线程.on('error',自身.工作线程错误)#错误视为死亡
        自身.工作线程.on('exit',自身.退出)#线程退出
        if 信号 is not None and 已中止(信号):#启动时信号已中止
            自身.取消('workflow start signal already aborted')#立即取消
        elif 信号 is not None:#有尚未中止的外部信号
            def 监视外部中止():#外部中止
                """外部中止后取消运行。"""
                信号.等待()#阻塞到中止
                自身.取消('workflow signal aborted')#再取消运行
            线程=threading.Thread(target=监视外部中止)#监视中止
            线程.daemon=True#不挡住退出
            线程.start()#启动

    def 工作线程错误(自身,错误):#工作线程 error 回调
        """错误视为死亡。"""
        自身.工作线程死亡('workflow worker failed: '+渲染抛出(错误),False)#按错误结算死亡

    def 退出(自身,码):#线程退出
        """标记线程已不在并按退出码结算死亡。"""
        自身.工作线程已退出=True#标记线程已不在
        自身.工作线程死亡('workflow worker exited before the run settled (exit code '+str(码)+')',True)#按退出码结算死亡

    def 取消(自身,原因=None):#取消本次运行
        """取消本次运行：告知 worker，中止每个子启动共用的必需信号，并启动宽限定时器。幂等；第一条原因获胜。"""
        with 自身.锁:#检查可否取消
            if 自身.已结算 or 自身.终态已占 or 自身.取消原因 is not None:#已结算、已占终态或已取消则忽略
                return#忽略
            自身.取消原因=原因 if 原因 is not None else 'workflow cancelled'#先到的原因获胜
        自身.投递(宿主到工作线程类型.取消,{'reason':自身.取消原因})#通知 worker 取消
        自身.中止子运行(自身.取消原因)#中止共享子信号
        def 宽限到期():#宽限到期后强制收尾
            """宽限到期后强制收尾。"""
            time.sleep(自身.销毁宽限毫秒/1000.0)#按配置宽限
            with 自身.锁:#占用终态
                自身.终态已占=True#占用终态
            自身.结束搁浅智能体()#合成缺失的结束事件
            自身.结算结果(自身.取消结果(自身.宿主已启动))#强制结算为取消
            自身.工作线程.终止()#终止工作线程
        宽限=threading.Thread(target=宽限到期)#宽限线程
        宽限.daemon=True#不阻止进程退出
        自身.宽限线程=宽限#记住
        宽限.start()#启动

    def 销毁(自身):#销毁本次运行
        """取消 + 有界结算 + 终止。幂等；每条路径都安全。"""
        if 自身.已销毁任务 is not None:#已有销毁事务则加入
            自身.已销毁任务.等待()#等待同一份
            return#结束
        公开=操作任务()#公开销毁的结算器
        自身.已销毁任务=公开#对外暴露同一份事务
        def 主体():#销毁事务主体
            """销毁事务主体。"""
            try:#主体
                自身.取消('workflow disposed')#走取消路径
                自身.收割子运行('workflow disposed')#立即收割已登记子运行
                截止=time.time()+自身.销毁宽限毫秒/1000.0#宽限截止
                while time.time()<截止:#结果静止与宽限竞速
                    if 自身.已结算 and 自身.已静止():#已结算且静止
                        break#结束等待
                    time.sleep(0.02)#短睡
                自身.工作线程.终止()#无条件终止线程
                自身.收割子运行('workflow disposed')#终止后再收割残留
                公开.兑现(None)#销毁成功
            except Exception as 错误:#销毁失败
                公开.拒绝(错误)#拒绝
        线程=threading.Thread(target=主体)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        公开.等待()#同步等到销毁结束

    def 投递(自身,类型,载荷):#向 worker 发消息
        """向 worker 投递一条消息（载荷按标签查表），容忍线程已经不在。"""
        if 自身.工作线程已退出 or 自身.工作线程死亡已见:#线程已不在或死亡后不再投递
            return#忽略
        try:#尝试投递
            消息={'type':类型}#标签
            消息.update(载荷)#附带载荷
            自身.工作线程.postMessage(消息)#发送
        except Exception as 错误:#投递抛错
            自身.上下文.日志.警告('workflow-worker-thread: postMessage failed: '+渲染抛出(错误))#记录投递失败

    def 收消息(自身,消息):#分发一条 worker 消息
        """分发一条 worker 消息。消息是 dict。"""
        if 自身.工作线程死亡已见:#死亡后拒绝准入
            return#忽略
        类型=消息['type']#消息类型
        if 类型==工作线程到宿主类型.就绪:#worker 已就绪
            自身.投递(宿主到工作线程类型.开始,{})#允许脚本开始
            return#结束就绪分支
        if 类型==工作线程到宿主类型.阶段:#阶段叙述
            if 自身.取消原因 is None:#未取消才转发阶段
                自身.观察者.阶段(消息['title'])#转发
            return#结束阶段分支
        if 类型==工作线程到宿主类型.日志:#日志叙述
            if 自身.取消原因 is None:#未取消才转发日志
                自身.观察者.日志(消息['message'])#转发
            return#结束日志分支
        if 类型==工作线程到宿主类型.智能体开始:#智能体开始
            信息=消息['info']#开始信息
            自身.活智能体[信息['seq']]=信息#记入未配对账本
            自身.观察者.智能体开始(信息)#转发给观察者
            return#结束开始分支
        if 类型==工作线程到宿主类型.智能体结束:#智能体结束
            自身.结束智能体(消息['info'])#经配对门转发结束
            return#结束结束分支
        if 类型==工作线程到宿主类型.子启动:#请求启动子运行
            自身.子启动(消息['callId'],消息['request'])#处理启动子请求
            return#结束启动子分支
        if 类型==工作线程到宿主类型.子销毁:#请求销毁子运行
            自身.子销毁(消息['callId'])#处理销毁请求
            return#结束销毁分支
        if 类型==工作线程到宿主类型.结果:#脚本结果
            自身.收结果(消息['result'])#处理运行结果
            return#结束结果分支
        断言永不(消息,'worker-to-host message')#未知消息类型失败

    def 子准入失败(自身):#查询子准入失败原因
        """一份就绪的提供方结果为何不再允许进入 worker。"""
        if 自身.取消原因 is not None:#运行已取消
            return {'reason':自身.取消原因,'rendered':'workflow run cancelled: '+自身.取消原因}#返回取消原因
        if 自身.工作线程死亡已见:#worker 已死亡
            return {'reason':'workflow worker gone','rendered':'workflow worker is no longer available'}#返回 worker 不可用
        if 自身.终态已占:#终态已被占用
            return {'reason':'workflow settled','rendered':'workflow run already settled'}#返回已结算
        return None#仍允许准入

    def 子启动(自身,调用号,请求):#处理一条启动子请求
        """处理一条启动子请求。请求是 dict。"""
        初始失败=自身.子准入失败()#先查当前准入
        if 初始失败 is not None:#终态边界之后拒绝
            自身.投递(宿主到工作线程类型.子启动错误,{'callId':调用号,'rendered':初始失败['rendered']})#回报启动失败
            return#不再启动
        自身.宿主已启动+=1#计入已接受的启动子
        任务=操作任务()#启动提供方事务
        自身.待启动.add(任务)#登记进行中的启动
        def 后台启动():#后台启动
            """启动并发布一个子运行。"""
            try:#启动
                自身.真正启动子(调用号,请求)#启动
                任务.兑现(None)#成功
            except Exception as 错误:#失败
                任务.拒绝(错误)#拒绝
            finally:#退休事务
                自身.待启动.discard(任务)#从进行中集合删除
                自身.通知静止()#可能释放静止等待者
        线程=threading.Thread(target=后台启动)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动

    def 真正启动子(自身,调用号,请求):#启动并发布一个子运行
        """等待一次提供方拥有的启动事务，并只在仍被准入时发布。请求是 dict。"""
        try:#调用提供方启动
            启动参数={#按提供方名启动子智能体
                'prompt':[{'type':'text','text':请求['prompt']}],#把提示打成文本块
                'parent':自身.父,#归属父智能体
                'signal':自身.控制器.信号,#带上本运行的共享中止
            }#结束基础参数
            if 'schema' in 请求 and 请求['schema'] is not None:#有模式才传入
                启动参数['outputSchema']=请求['schema']#写入模式
            if ('provider' in 请求 and 请求['provider'] is not None) or ('model' in 请求 and 请求['model'] is not None):#有覆盖才组装 agentOptions
                选项={}#智能体选项
                if 'provider' in 请求 and 请求['provider'] is not None:#可选提供方覆盖
                    选项['provider']=请求['provider']#写入
                if 'model' in 请求 and 请求['model'] is not None:#可选模型覆盖
                    选项['model']=请求['model']#写入
                启动参数['agentOptions']=选项#写入选项
            运行=自身.子智能体.启动(自身.提供方,启动参数)#调用启动
        except Exception as 错误:#提供方启动失败
            失败=自身.子准入失败()#启动期间可能已关闭准入
            自身.投递(宿主到工作线程类型.子启动错误,{#回报启动失败
                'callId':调用号,#对应的调用标识
                'rendered':失败['rendered'] if 失败 is not None else 渲染抛出(错误),#优先报准入失败，否则报抛出值
            })#结束失败消息
            return#不发布
        失败=自身.子准入失败()#启动完成后再次检查准入
        if 失败 is not None:#期间关闭了准入
            自身.投递(宿主到工作线程类型.子启动错误,{'callId':调用号,'rendered':失败['rendered']})#回报不再准入
            try:#丢掉已经拉起的子运行
                运行.销毁()#立即销毁
            except Exception as 错误:#销毁失败
                自身.上下文.日志.警告('workflow-worker-thread: refused child dispose failed: '+渲染抛出(错误))#记录拒绝后的销毁失败
            return#不发布
        记录=子记录(运行)#组装已发布记录
        自身.子运行表[调用号]=记录#登记到子运行表
        def 转发():#把子结果编成稍后投递
            """把子结果编成稍后投递。"""
            try:#等待子结果
                结果=运行.result.等待()#子运行兑现；result 是缝载荷键
                try:#快照必须能无损跨线程
                    快照对象={'output':结果['output'],'stopReason':结果['stopReason']}#把子结果打成 JSON 快照
                    if 'structured' in 结果:#有结构化才带上
                        快照对象['structured']=结果['structured']#写入
                    快照=快照json值(快照对象)#无损快照
                    if 快照 is None:#无法无损序列化则失败
                        raise TypeError('child result is not losslessly JSON-serializable')#失败
                    自身.投递(宿主到工作线程类型.子已结算,{'callId':调用号,'result':快照})#投递结算
                except (TypeError,ValueError) as 错误:#快照或序列化失败
                    已渲染='workflow child result could not cross the worker boundary: '+渲染抛出(错误)#跨界失败文案
                    自身.投递(宿主到工作线程类型.子失败,{'callId':调用号,'rendered':已渲染})#投递失败
            except Exception as 错误:#子运行拒绝
                自身.投递(宿主到工作线程类型.子失败,{'callId':调用号,'rendered':渲染抛出(错误)})#投递失败
        自身.投递(宿主到工作线程类型.子已启动,{'callId':调用号,'childId':运行.id})#先发布子句柄
        线程=threading.Thread(target=转发)#再投递结算或失败
        线程.daemon=True#不挡住退出
        线程.start()#启动

    def 子销毁(自身,调用号):#处理 worker 的销毁 RPC
        """处理 worker 的销毁 RPC。"""
        记录=自身.子运行表[调用号] if 调用号 in 自身.子运行表 else None#查找已发布记录
        if 记录 is None:#宿主侧已经销毁
            自身.投递(宿主到工作线程类型.子已销毁,{'callId':调用号})#仍回确认
            return#结束
        def 确认():#销毁后再确认
            """销毁后再确认。"""
            自身.销毁子(调用号,记录)#销毁
            自身.投递(宿主到工作线程类型.子已销毁,{'callId':调用号})#确认
        线程=threading.Thread(target=确认)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动

    def 销毁子(自身,调用号,记录):#销毁或加入已有销毁
        """启动（或加入）一个已登记子运行的销毁；登记条目在结算时离开。"""
        if 记录.销毁事务 is not None:#已有事务则加入
            记录.销毁事务.等待()#等待同一份
            return#结束
        事务=操作任务()#新销毁事务
        记录.销毁事务=事务#记住
        def 后台销毁():#后台销毁
            """调用子运行销毁并离表。"""
            try:#销毁
                记录.运行.销毁()#调用子运行销毁
            except Exception as 错误:#收容销毁拒绝
                自身.上下文.日志.警告('workflow-worker-thread: child dispose failed: '+渲染抛出(错误))#记录销毁失败
            自身.子运行表.pop(调用号,None)#从登记表删除
            自身.通知静止()#可能释放静止等待者
            事务.兑现(None)#兑现
        线程=threading.Thread(target=后台销毁)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        事务.等待()#同步等到该子销毁

    def 已静止(自身):#是否已静止
        """待启动与已发布子运行是否都已结束。"""
        return len(自身.子运行表)==0 and len(自身.待启动)==0#已静止；判 length

    def 通知静止(自身):#检查并释放静止等待者
        """只在待启动与已发布子运行都结束后才释放等待者。"""
        if 自身.已静止() is False:#仍有工作则继续等
            return#继续等
        等待列表=list(自身.静止等待者)#快照
        自身.静止等待者.clear()#清空
        for 等待 in 等待列表:#唤醒全部等待者
            等待()#唤醒

    def 收割子运行(自身,原因):#收割全部已登记子运行
        """中止并销毁每个已登记子运行；销毁被收容，不等待。"""
        自身.中止子运行(自身.取消原因 if 自身.取消原因 is not None else 原因)#中止共享信号
        for 调用号,记录 in list(自身.子运行表.items()):#快照后遍历
            线程=threading.Thread(target=自身.销毁子,args=(调用号,记录))#启动或加入销毁，不等待收割循环
            线程.daemon=True#不挡住退出
            线程.start()#启动

    def 中止子运行(自身,原因):#中止共享子信号
        """中止待启动与已发布子运行共用的那一条规范信号。"""
        if 已中止(自身.控制器.信号) is False:#尚未中止才 abort
            自身.控制器.中止(工作流错误(str(原因),'CANCELLED') if 原因 is not None else None)#原因用异常对象承载

    def 收结果(自身,结果):#处理 worker 送来的运行结果
        """处理 worker 送来的运行结果。结果是 dict。"""
        if 自身.终态已占:#终态已被占用则忽略
            return#忽略
        取消已请求=自身.取消原因 is not None#记录到达时是否已请求取消
        自身.终态已占=True#占用终态
        自身.收割子运行('workflow settled')#开始清理子运行
        if 取消已请求 is False:#到达时没有外部取消
            自身.结算结果(结果)#采用 worker 结果
            return#结束
        停止原因=结果['stopReason']#停止原因
        if 停止原因!='cancelled':#脚本在取消穿越线程边界时结算
            已开始=结果['agentsStarted'] if 'agentsStarted' in 结果 else 0#智能体计数
            自身.结算结果(自身.取消结果(已开始))#改报取消
            return#结束
        自身.结算结果(结果)#worker 自己已经报取消

    def 工作线程死亡(自身,消息,是否退出):#处理 worker 死亡
        """处理 error/messageerror/exit 信号；exit 还做最后一次销毁清扫。"""
        if 自身.工作线程死亡已见 is False:#第一份死亡信号
            自身.工作线程死亡已见=True#关闭消息准入
            结局已占=自身.终态已占#死亡到达前终态是否已被占用
            取消已请求=自身.取消原因 is not None#死亡到达前是否已请求取消
            if 结局已占 is False:#死亡作为终态源时占住
                自身.终态已占=True#占住
            if len(自身.子运行表)>0 or len(自身.待启动)>0:#有残留则收割；判 length
                自身.收割子运行('workflow worker gone')#收割
            自身.结束搁浅智能体()#合成缺失的结束事件
            if 结局已占 is False:#死亡赢得终态
                if 取消已请求:#死亡前已请求取消
                    自身.结算结果(自身.取消结果(自身.宿主已启动))#报取消
                else:#死亡前未取消
                    自身.结算结果({'value':None,'stopReason':'error','error':消息,'agentsStarted':自身.宿主已启动})#报错误
        if 是否退出 is False:#非 exit 不做物理清扫
            return#结束
        for 调用号,记录 in list(自身.子运行表.items()):#对残留子运行启动销毁
            线程=threading.Thread(target=自身.销毁子,args=(调用号,记录))#启动销毁
            线程.daemon=True#不挡住退出
            线程.start()#启动
        自身.结束搁浅智能体()#exit 清扫时再合成一次

    def 结束智能体(自身,结束):#经配对门转发一次结束
        """唯一的智能体结束发射门：仅当其开始仍在账本里未配对时才转发 end。结束是 dict。"""
        序号=结束['seq']#取出序号
        if 序号 not in 自身.活智能体:#已经配对或不在账本则忽略
            return#忽略
        自身.活智能体.pop(序号,None)#配对离表
        自身.观察者.智能体结束(结束)#转发给观察者

    def 结束搁浅智能体(自身):#合成所有搁浅开始的结束
        """为每个已开始但未配对的智能体合成缺失的 agent-end，结局为 cancelled。"""
        for 信息 in list(自身.活智能体.values()):#快照后遍历未配对账本
            自身.结束智能体({**信息,'outcome':'cancelled'})#按取消结局合成结束

    def 取消结果(自身,已开始):#组装取消结局
        """组装取消结局。"""
        原因=自身.取消原因 if 自身.取消原因 is not None else 'workflow cancelled'#取取消原因
        return {'value':None,'stopReason':'cancelled','error':'workflow run cancelled: '+原因,'agentsStarted':已开始}#返回取消结果

    def 结算结果(自身,结果):#结算运行结果
        """第一次结算获胜。结果是 dict。"""
        if 自身.已结算:#已经结算则忽略
            return#忽略
        自身.终态已占=True#占住终态
        自身.已结算=True#标记已结算
        自身.结果.兑现(结果)#兑现结果任务
