"""每次运行在 worker 侧的领域钩子、子 RPC、并发/上限、取消与结果序列化；它从不碰 Cordis。离开领域的脚本值在发消息前物化为普通 JSON。进入受信任的模型编写领域的值直接传入；只有 args 被克隆，以免脚本改写初始化数据。信任模型见 `./领域`。

致命工作流错误——坏的钩子参数、不受支持的模式/选项、上限、启动失败、取消——经组合子传播。只有子失败和普通阶段错误变成按条 null。每个返回的承诺都有拒绝消费方，因此被丢掉的脚本承诺杀不死 worker。从未结算的已取消脚本什么都不发；宿主在宽限内强制结算运行并终止线程。
"""
import copy,threading#克隆 args 与后台收容线程
from concurrent.futures import Future as _原生Future#单次操作结果
from ...内核.会话 import 会话标识#会话标识铸造
from ...内核.工具 import 断言对象json模式,json模式错误
from ..工作流 import 是否致命工作流错误,工作流错误#致命错误判定与工作流错误
from .领域 import 从领域物化,物化错误,渲染抛出#领域物化

受支持智能体选项=set(['label','phase','schema','provider','model'])#受支持的 agent 选项名
推迟智能体选项=set(['effort','isolation','agentType'])#推迟选项名

class 执行观察者:#执行观察者协议
    """执行通过这些观察者报告进度（会话把它们发给宿主）。"""
    def phase(自身,标题):#阶段标题
        """阶段标题。"""
        raise NotImplementedError('ExecutionObserver.phase')#由会话实现
    def log(自身,消息):#叙述日志
        """叙述日志。"""
        raise NotImplementedError('ExecutionObserver.log')#由会话实现
    def agentStart(自身,信息):#智能体开始
        """智能体开始。"""
        raise NotImplementedError('ExecutionObserver.agentStart')#由会话实现
    def agentEnd(自身,信息):#智能体结束
        """智能体结束。"""
        raise NotImplementedError('ExecutionObserver.agentEnd')#由会话实现

def 输出文本(块们):#抽取文本块并拼接
    """把子运行最终输出块压成文本（无 schema 时的 agent() 结果）。"""
    文本们=[]#收集文本
    for 块 in 块们:#遍历内容块
        类型=块.get('type') if isinstance(块,dict) else getattr(块,'type',None)#块类型
        if 类型=='text':#只留文本块
            文本=块.get('text') if isinstance(块,dict) else getattr(块,'text','')#取出文本
            文本们.append(文本 if isinstance(文本,str) else str(文本))#收入
    return ''.join(文本们)#拼成一段

def 默认标签(提示词):#从提示词取默认标签
    """脚本未传标签时，从提示词推导的短展示标签。"""
    换行=提示词.find('\n')#第一行换行位置
    行=提示词 if 换行==-1 else 提示词[0:换行]#取第一行
    return 行 if len(行)<=48 else 行[0:47]+'…'#超长则截断

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 收容承诺(承诺值):#挂上空操作拒绝消费方
    """挂上空操作拒绝消费方，但不改变调用方收到的东西。"""
    if not _是否thenable(承诺值):#非可等待
        return 承诺值#原样
    def 盯():#吞掉未处理拒绝
        """已消费：被丢掉的钩子任务不得浮成未处理拒绝。"""
        try:#等待
            _等待(承诺值)#等待结算
        except BaseException:#拒绝也算消费
            pass#吞掉
    线程=threading.Thread(target=盯)#后台观察
    线程.daemon=True#不挡住退出
    线程.start()#启动
    return 承诺值#原样返回给调用方

class 工作流执行:#worker 侧一次脚本执行
    """worker 内一次活着的脚本执行。由会话按次构造；drive() 恰好调用一次且永不拒绝——每次失败都变成带非 completed 停止原因的工作流结果。宿主拥有取消，以及任何被丢掉的子工作的清理。"""
    def __init__(自身,元数据,正文,参数,上限,观察者,子端口):#按次构造一次执行
        """按次构造一次执行。"""
        自身.limits=上限#本次运行上限
        自身.上限=上限#中文别名
        自身.observer=观察者#进度观察者
        自身.观察者=观察者#中文别名
        自身.children=子端口#子 RPC 端口
        自身.子端口=子端口#中文别名
        自身.started=0#已启动智能体计数
        自身.已启动=0#中文别名
        自身.activeSlots=0#当前占用的并发槽
        自身.占用槽=0#中文别名
        自身.slotWaiters=[]#排队等槽的人
        自身.等槽者=自身.slotWaiters#中文别名
        自身.cancelReason=None#取消原因，先到者获胜
        自身.取消原因=None#中文别名
        自身.cancelError=None#对应的 CANCELLED 错误
        自身.取消错误=None#中文别名
        自身.currentPhase=None#当前阶段标题
        自身.当前阶段=None#中文别名
        自身._槽锁=threading.Lock()#并发槽锁
        # 先编译：正文语法错误必须在任何领域状态存在之前从构造函数抛出。
        # 宿主用同一包装预先解析，因此在同一引擎版本下生产路径到不了这次抛错——
        # 会话仍防御性地把它映射成错误结果。
        自身._元数据名=元数据.get('name') if isinstance(元数据,dict) else getattr(元数据,'name','workflow')#工作流名
        try:#编译包装后的正文
            自身._已编译=编译脚本正文(正文,自身._元数据名)#按 worker 包装编译
        except 工作流错误:#已是工作流错误
            raise#原样抛出
        except Exception as 错误:#包装编译失败
            raise 工作流错误('workflow script does not parse: '+str(错误),'SCRIPT_PARSE',{'cause':错误})#映射为 SCRIPT_PARSE
        自身._参数=copy.deepcopy(参数) if 参数 is not None else None#克隆 args，以免脚本改写初始化数据
        自身._上下文={#注入脚本全局
            'agent':lambda 提示,选项=None: 解开(收容承诺(自身._智能体(提示,选项))),#agent 钩子（同步等待）
            'parallel':lambda 形参: 解开(收容承诺(自身._并行(形参))),#parallel 钩子
            'pipeline':自身._管道入口,#pipeline 钩子
            'phase':lambda 标题: 自身._阶段(标题),#phase 钩子
            'log':lambda 消息: 自身._日志(消息),#log 钩子
            'args':自身._参数,#脚本输入
        }#结束全局表

    def _管道入口(自身,条目,*阶段们):#pipeline 变参入口
        """pipeline(items, ...stages) 钩子入口。"""
        return 解开(收容承诺(自身._管道(条目,list(阶段们))))#同步等待

    def 是否已取消(自身):#查询是否已取消
        """运行是否已被取消。这是方法，不是内联属性读取：cancel() 会并发改写 cancelReason。"""
        return 自身.cancelReason is not None#有取消原因即为已取消

    def 若已取消则抛(自身):#已取消则抛 CANCELLED
        """共享的钩子入口守卫：cancel 之后，每个钩子在下一次调用时抛 CANCELLED。"""
        if 自身.是否已取消():#已取消
            raise 自身.取取消错误()#抛规范错误

    def 取消(自身,原因):#取消本次执行
        """取消本次运行：正在等的 agent() 槽拒绝，此后每次钩子调用都抛 CANCELLED。幂等；第一条原因获胜。"""
        if 自身.cancelReason is not None:#已取消则忽略
            return#幂等
        自身.cancelReason=原因#先到的原因获胜
        自身.取消原因=原因#中文别名
        自身.cancelError=工作流错误('workflow run cancelled: '+自身.cancelReason,'CANCELLED')#构造规范取消错误
        自身.取消错误=自身.cancelError#中文别名
        with 自身._槽锁:#拒绝所有排队等槽的人
            等待们=list(自身.slotWaiters)#快照
            自身.slotWaiters.clear()#清空
        for 等待 in 等待们:#逐个拒绝
            等待['reject'](自身.取取消错误())#拒绝

    def 驱动(自身):#驱动脚本直到结算
        """把脚本跑到结算。兑现——永不拒绝——为本次运行的工作流结果。"""
        try:#执行正文并物化返回值
            if 自身.是否已取消():#启动前已取消则不跑
                raise 自身.取取消错误()#抛取消
            原始=跑已编译脚本(自身._已编译,自身._上下文,自身.limits.get('syncTimeoutMs',5000))#跑脚本
            原始=解开(收容承诺(已兑现值(原始)))#等待脚本承诺并收容拒绝
            if 自身.是否已取消():#结算后发现已取消
                raise 自身.取取消错误()#抛取消
            值=None if 原始 is None else 自身.物化结果(原始)#None 当成 null，其余物化
            return {'value':值,'stopReason':'completed','agentsStarted':自身.started}#干净完成
        except Exception as 错误:#脚本失败或取消
            if 自身.是否已取消():#已取消
                取消错=自身.取取消错误()#规范取消错误
                取消消息=str(取消错) if str(取消错) else 'workflow run cancelled'#错误消息
                return {'value':None,'stopReason':'cancelled','error':取消消息,'agentsStarted':自身.started}#报取消
            return {'value':None,'stopReason':'error','error':渲染抛出(错误),'agentsStarted':自身.started}#报错误

    def 取取消错误(自身):#取出规范取消错误
        """cancel() 在任何调用方能观察到已取消之前就武装 cancelError；回退只护住类型。"""
        if 自身.cancelError is not None:#已武装
            return 自身.cancelError#返回已武装错误
        return 工作流错误('workflow run cancelled','CANCELLED')#类型回退

    def 物化结果(自身,原始):#物化脚本返回值
        """物化脚本返回值；违规变成 RESULT_UNSERIALIZABLE。"""
        try:#尝试按领域规则物化
            return 从领域物化(原始,'workflow result')#把返回值收成普通 JSON
        except 物化错误 as 错误:#物化失败
            raise 工作流错误(#返回值不是普通 JSON
                "the workflow's return value is not plain JSON data — "+str(错误)+'. Return only JSON-serializable objects/arrays/scalars.',#说明只接受可序列化值
                'RESULT_UNSERIALIZABLE',#不可序列化错误码
                {'cause':错误},#保留原因
            )#结束抛错
        except Exception as 错误:#非物化错误
            if not isinstance(错误,物化错误):#防御臂
                raise#原样抛出
            raise#不可达

    def 取槽(自身):#取得一个并发槽
        """取得一个并发槽（FIFO）。取消会拒绝排队等待者。"""
        with 自身._槽锁:#检查空槽
            if 自身.activeSlots<自身.limits['maxConcurrentAgents']:#还有空槽
                自身.activeSlots+=1#立即占用
                自身.占用槽=自身.activeSlots#同步中文
                完成=操作任务()#立刻兑现
                完成.兑现(None)#无需排队
                return 完成#返回
            等待=操作任务()#排队等释放
            自身.slotWaiters.append({#登记等待者
                'resolve':lambda: 自身._唤醒取槽(等待),#轮到时占用槽
                'reject':等待.拒绝,#取消时拒绝
            })#结束等待者
            return 等待#返回排队承诺

    def _唤醒取槽(自身,等待):#轮到时占用槽
        """轮到时占用槽并唤醒等待者。"""
        自身.activeSlots+=1#占用一个槽
        自身.占用槽=自身.activeSlots#同步中文
        等待.兑现(None)#唤醒等待者

    def 放槽(自身):#释放一个并发槽
        """释放一个并发槽。"""
        下一个=None#下一个等待者
        with 自身._槽锁:#减占用
            自身.activeSlots-=1#减占用
            自身.占用槽=自身.activeSlots#同步中文
            if len(自身.slotWaiters)>0:#有人排队
                下一个=自身.slotWaiters.pop(0)#取出下一个等待者
        if 下一个 is not None:#有人排队则唤醒
            下一个['resolve']()#唤醒

    def _智能体(自身,原始提示,原始选项):#跑一个子智能体直到完成
        """agent(prompt, opts) 钩子。返回承诺。"""
        结果=操作任务()#钩子结果任务
        def 跑():#在后台跑，避免嵌套死锁
            """跑 agent 钩子主体。"""
            try:#主体
                自身.若已取消则抛()#入口取消守卫
                if not isinstance(原始提示,str) or len(原始提示)==0:#提示不是非空字符串
                    raise 工作流错误('agent() requires a non-empty prompt string','INVALID_ARGUMENT')#参数无效
                选项=自身.读智能体选项(原始选项)#读取并校验选项袋
                if 自身.started>=自身.limits['maxTotalAgents']:#已达总数上限
                    raise 工作流错误(#失控循环挡板
                        'this run reached its total agent cap ('+str(自身.limits['maxTotalAgents'])+') — a runaway-loop backstop; raise the applicable maxTotalAgents limit if the scale is intentional',#说明已达上限
                        'AGENT_CAP',#上限错误码
                    )#结束抛错
                自身.started+=1#计入一次启动
                自身.已启动=自身.started#同步中文
                序号=自身.started#本次成员序号
                标签=选项.get('label') if 选项.get('label') is not None else 默认标签(原始提示)#展示标签
                阶段=选项.get('phase') if 选项.get('phase') is not None else 自身.currentPhase#所属阶段
                解开(自身.取槽())#取得并发槽
                try:#在持有槽期间跑子运行
                    自身.若已取消则抛()#取得后取消守卫
                    try:#向宿主请求启动子运行
                        启动请求={'prompt':原始提示}#经子端口启动
                        if 选项.get('schema') is not None:#有模式才传入
                            启动请求['schema']=选项['schema']#写入模式
                        if 选项.get('provider') is not None:#有提供方覆盖才传入
                            启动请求['provider']=选项['provider']#写入提供方
                        if 选项.get('model') is not None:#有模型覆盖才传入
                            启动请求['model']=选项['model']#写入模型
                        启动=自身.children.startAgent(启动请求) if hasattr(自身.children,'startAgent') else 自身.children.启动子(启动请求)#启动
                        运行=解开(启动)#等待已发布句柄
                    except Exception as 错误:#启动失败
                        if 自身.是否已取消():#取消竞速则报取消
                            raise 自身.取取消错误()#报取消
                        raise 工作流错误('agent() could not start a child: '+渲染抛出(错误),'AGENT_START',{'cause':错误})#否则报启动失败
                    if 自身.是否已取消():#启动后发现已取消
                        解开(运行.dispose() if hasattr(运行,'dispose') else 运行.销毁())#立即销毁子运行
                        raise 自身.取取消错误()#报取消
                    信息={'seq':序号,'label':标签,'childId':会话标识(取字段(运行,'id'))}#组装开始信息
                    if 阶段 is not None:#有阶段
                        信息['phase']=阶段#写入阶段
                    自身.observer.agentStart(信息)#报告智能体开始
                    try:#等待子运行结算并配对结束
                        try:#等待子结果
                            子结果=解开(取字段(运行,'result'))#等待子运行兑现
                        except Exception as 错误:#子结果拒绝
                            if 自身.是否已取消():#拒绝时已取消
                                自身.observer.agentEnd({**信息,'outcome':'cancelled'})#配对为取消
                                raise 自身.取取消错误()#报取消
                            自身.observer.agentEnd({**信息,'outcome':'failed'})#配对为失败
                            raise 工作流错误('child agent run failed: '+渲染抛出(错误),'AGENT_RESULT',{'cause':错误})#致命的结果故障
                        停止原因=子结果.get('stopReason') if isinstance(子结果,dict) else getattr(子结果,'stopReason',None)#停止原因
                        if 停止原因=='completed':#子运行干净完成
                            if 选项.get('schema') is not None:#要了结构化输出
                                结构化=子结果.get('structured') if isinstance(子结果,dict) else getattr(子结果,'structured',None)#结构化值
                                if 结构化 is None:#缺少结构化值
                                    自身.observer.agentEnd({**信息,'outcome':'failed'})#配对为失败
                                    结果.兑现(None)#按条 null
                                    return#结束
                                自身.observer.agentEnd({**信息,'outcome':'completed'})#配对为完成
                                结果.兑现(结构化)#返回结构化对象
                                return#结束
                            输出=子结果.get('output') if isinstance(子结果,dict) else getattr(子结果,'output',[])#输出块
                            自身.observer.agentEnd({**信息,'outcome':'completed'})#配对为完成
                            结果.兑现(输出文本(输出 or []))#返回拼接文本
                            return#结束
                        if 自身.是否已取消():#运行已取消
                            自身.observer.agentEnd({**信息,'outcome':'cancelled'})#配对为取消
                            raise 自身.取取消错误()#杀死脚本
                        自身.observer.agentEnd({**信息,'outcome':'failed'})#配对为失败
                        结果.兑现(None)#按条 null
                    finally:#无论结局都销毁子运行
                        解开(运行.dispose() if hasattr(运行,'dispose') else 运行.销毁())#等待子销毁
                finally:#无论成败都放槽
                    自身.放槽()#释放并发槽
            except Exception as 错误:#钩子失败
                结果.拒绝(错误)#拒绝承诺
        线程=threading.Thread(target=跑)#后台跑钩子
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 结果#返回承诺

    def 读智能体选项(自身,原始选项):#读取 agent 选项
        """从领域物化并校验 agent() 选项袋。"""
        if 原始选项 is None:#未传选项
            return {}#空选项
        try:#把领域值收成普通 JSON
            选项=从领域物化(原始选项,'agent() options')#物化选项袋
        except 物化错误 as 错误:#物化失败
            raise 工作流错误('agent() options must be plain JSON data — '+str(错误),'INVALID_ARGUMENT',{'cause':错误})#选项必须是普通 JSON
        if not isinstance(选项,dict):#不是普通对象
            raise 工作流错误('agent() options must be an object','INVALID_ARGUMENT')#必须是对象
        for 键 in 选项.keys():#检查每个键
            if 键 in 受支持智能体选项:#受支持则继续
                continue#继续
            if 键 in 推迟智能体选项:#推迟选项
                raise 工作流错误('agent() option "'+键+'" is deferred and not supported by this engine (supported: label, phase, schema, provider, model)','UNSUPPORTED_OPTION')#点名推迟选项
            raise 工作流错误('agent() option "'+键+'" is not recognized (supported: label, phase, schema, provider, model)','UNSUPPORTED_OPTION')#未知选项
        for 键 in ('label','phase','provider','model'):#这四个必须是字符串
            if 键 in 选项 and 选项[键] is not None and not isinstance(选项[键],str):#出现了非字符串
                raise 工作流错误('agent() option "'+键+'" must be a string','INVALID_ARGUMENT')#类型无效
        模式值=None#可选结构化模式
        if 'schema' in 选项 and 选项['schema'] is not None:#传了 schema
            try:#校验受支持子集
                断言对象json模式(选项['schema'])#断言对象根模式
                模式值=选项['schema']#保存已校验模式
            except JsonSchemaError as 错误:#模式校验失败
                raise 工作流错误('agent() schema is outside the supported subset — '+str(错误),'UNSUPPORTED_SCHEMA',{'cause':错误})#超出受支持子集
            except Exception as 错误:#非模式错误
                if not isinstance(错误,JsonSchemaError):#防御臂
                    raise#原样抛出
                raise#不可达
        结果={}#组装已校验选项
        if 'label' in 选项 and 选项['label'] is not None:#可选标签
            结果['label']=选项['label']#写入
        if 'phase' in 选项 and 选项['phase'] is not None:#可选阶段
            结果['phase']=选项['phase']#写入
        if 'provider' in 选项 and 选项['provider'] is not None:#可选提供方
            结果['provider']=选项['provider']#写入
        if 'model' in 选项 and 选项['model'] is not None:#可选模型
            结果['model']=选项['model']#写入
        if 模式值 is not None:#可选模式
            结果['schema']=模式值#写入
        return 结果#结束返回

    def _并行(自身,原始形参):#并发跑零参函数
        """parallel(thunks) 钩子：每个 thunk 被捕获则变成 null；致命错误传播。"""
        结果=操作任务()#钩子结果
        def 跑():#主体
            """跑 parallel 主体。"""
            try:#主体
                自身.若已取消则抛()#入口取消守卫
                if not isinstance(原始形参,list):#不是数组
                    raise 工作流错误('parallel() requires an array of zero-argument functions','INVALID_ARGUMENT')#必须是函数数组
                自身.断言条目上限(len(原始形参),'parallel()')#检查每调用条目上限
                形参们=[]#校成函数列表
                for 索引,形参 in enumerate(原始形参):#校验
                    if not callable(形参):#该项不是函数
                        raise 工作流错误('parallel() item '+str(索引)+' is not a function','INVALID_ARGUMENT')#指出哪一项
                    形参们.append(形参)#收入
                输出=[]#结果列表
                for 形参 in 形参们:#顺序等待（语义上可并发；Python 端口用顺序保确定性）
                    try:#跑一个 thunk
                        输出.append(解开(形参()))#兑现其返回值
                    except Exception as 错误:#thunk 抛错
                        if 是否致命工作流错误(错误):#致命错误杀死脚本
                            raise#再抛
                        输出.append(None)#普通错误变成 null
                结果.兑现(输出)#返回全部
            except Exception as 错误:#钩子失败
                结果.拒绝(错误)#拒绝
        线程=threading.Thread(target=跑)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 结果#返回承诺

    def _管道(自身,原始条目,原始阶段):#按条跑多阶段
        """pipeline(items, ...stages) 钩子：按条的阶段链，没有跨阶段屏障。"""
        结果=操作任务()#钩子结果
        def 跑():#主体
            """跑 pipeline 主体。"""
            try:#主体
                自身.若已取消则抛()#入口取消守卫
                if not isinstance(原始条目,list):#条目不是数组
                    raise 工作流错误('pipeline() requires an items array','INVALID_ARGUMENT')#必须是条目数组
                自身.断言条目上限(len(原始条目),'pipeline()')#检查每调用条目上限
                if len(原始阶段)==0:#没有阶段
                    raise 工作流错误('pipeline() requires at least one stage function','INVALID_ARGUMENT')#至少要一个阶段
                阶段们=[]#校成阶段函数列表
                for 索引,阶段 in enumerate(原始阶段):#校验
                    if not callable(阶段):#该项不是函数
                        raise 工作流错误('pipeline() stage '+str(索引)+' is not a function','INVALID_ARGUMENT')#指出哪一阶段
                    阶段们.append(阶段)#收入
                输出=[]#结果列表
                for 索引,条目 in enumerate(原始条目):#每条独立跑完全部分阶段
                    值=条目#当前阶段输入，起步为条目本身
                    try:#按顺序跑阶段
                        for 阶段 in 阶段们:#逐个阶段
                            值=解开(阶段(值,条目,索引))#本阶段输出成为下一阶段输入
                        输出.append(值)#该条的最终值
                    except Exception as 错误:#某阶段抛错
                        if 是否致命工作流错误(错误):#致命错误杀死脚本
                            raise#再抛
                        输出.append(None)#该条溶解为 null
                结果.兑现(输出)#返回全部
            except Exception as 错误:#钩子失败
                结果.拒绝(错误)#拒绝
        线程=threading.Thread(target=跑)#后台
        线程.daemon=True#不挡住退出
        线程.start()#启动
        return 结果#返回承诺

    def 断言条目上限(自身,长度,钩子):#检查组合子条目上限
        """检查组合子条目上限。"""
        if 长度>自身.limits['maxItemsPerCall']:#超过每调用上限
            raise 工作流错误(#条目过多
                钩子+' received '+str(长度)+' items — over the per-call cap ('+str(自身.limits['maxItemsPerCall'])+'); split the work or raise maxItemsPerCall in the engine config',#说明超限
                'ITEM_CAP',#条目上限错误码
            )#结束抛错

    def _阶段(自身,标题):#开始一个进度阶段
        """phase(title) 钩子：为随后的 agent() 调用设置当前标签并通知观察者。"""
        自身.若已取消则抛()#入口取消守卫
        if not isinstance(标题,str) or len(标题)==0:#标题不是非空字符串
            raise 工作流错误('phase() requires a non-empty title string','INVALID_ARGUMENT')#参数无效
        自身.currentPhase=标题#记下当前阶段
        自身.当前阶段=标题#中文别名
        自身.observer.phase(标题)#通知观察者

    def _日志(自身,消息):#发出一条叙述
        """log(message) 钩子：向观察者叙述。"""
        自身.若已取消则抛()#入口取消守卫
        if not isinstance(消息,str):#消息不是字符串
            raise 工作流错误('log() requires a message string','INVALID_ARGUMENT')#参数无效
        自身.observer.log(消息)#转发给观察者

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 已兑现值(值):#把任意值包成已兑现任务
    """把任意值包成已兑现任务。"""
    if _是否thenable(值):#已是可等待
        return 值#原样
    完成=操作任务()#新任务
    完成.兑现(值)#立刻成功
    return 完成#已完成

def 编译脚本正文(正文,名称):#按 worker 包装编译脚本
    """用与宿主侧相同的包装编译脚本正文；语法错误抛 SCRIPT_PARSE。"""
    包装='def __workflow_body__():\n'+缩进(正文)+'\n__workflow_result__=__workflow_body__()\n'#包装成可执行函数
    try:#编译
        return compile(包装,'workflow:'+名称,'exec')#编译为代码对象
    except SyntaxError as 错误:#语法错误
        raise 工作流错误('workflow script does not parse: '+str(错误),'SCRIPT_PARSE',{'cause':错误})#映射为 SCRIPT_PARSE

def 缩进(正文):#给正文每行加一层缩进
    """给正文每行加一层缩进。"""
    行们=正文.splitlines() or ['']#至少一行
    return '\n'.join('    '+行 for 行 in 行们)+('\n' if 正文.endswith('\n') else '')#缩进

def 跑已编译脚本(已编译,上下文,超时毫秒):#在领域上下文中跑已编译脚本
    """在领域上下文中跑已编译脚本；syncTimeoutMs 在 Python 端口作协作超时提示（真正强制终止由宿主宽限负责）。"""
    本地=dict(上下文)#可写领域
    本地['__name__']='workflow'#模块名
    exec(已编译,本地,本地)#执行包装
    return 本地.get('__workflow_result__')#取出返回值
