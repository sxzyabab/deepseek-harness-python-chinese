"""工作流 VM 钩子、子回调、普通并发上限与结果序列化。PTC 拥有进程隔离与取消。致命钩子与提供方失败经组合子传播；普通子失败与阶段错误变成每项 null。"""
import threading#槽位等待
from concurrent.futures import Future as 原生结果#单次操作结果
from ...内核.会话 import 会话标识#子 id 品牌
from ...内核.工具.json模式 import 断言对象json模式,json模式错误#对象 JSON 模式
from ..工作流 import 工作流错误,是否致命工作流错误#缝上错误
from .领域 import 从领域物化,物化错误,渲染抛出#跨领域 JSON

__all__=['任务','全部并发','全部结算','赛跑','工作流执行']#仅中文公开名

支持的智能体选项=frozenset(('label','phase','schema','provider','model'))#脚本可传的 agent() 选项
推迟的智能体选项=frozenset(('effort','isolation','agentType'))#拒绝文案里点名的推迟选项

class 任务:#单次操作的 Future 包装，只留 等待
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):#未决任务
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future
    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身._未来.set_exception(工作流错误(str(错误),'INVALID_ARGUMENT'))#包成工作流错误
    def 等待(自身,超时=None):#阻塞等到结算
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

def 全部并发(函数列表):#Promise.all
    """每路一线程，join 后按原序取结果；一路失败则抛。"""
    结果表=[None]*len(函数列表)#按原序结果
    错误表=[None]*len(函数列表)#按原序错误
    def 跑一路(下标,函数):#执行一路
        """执行一路并写入表。"""
        try:#执行
            结果表[下标]=函数()#成功
        except BaseException as 错误:#失败
            错误表[下标]=错误#记下
    线程表=[]#工作线程
    for 下标,函数 in enumerate(函数列表):#每路一线程
        工作=threading.Thread(target=跑一路,args=(下标,函数),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#扇出 join
        工作.join()#等到结束
    for 错误 in 错误表:#按原序检查
        if 错误 is not None:#有失败
            raise 错误#原样抛
    return 结果表#按原序结果

def 全部结算(任务列表):#Promise.allSettled
    """并发等全部任务落定，吞掉失败。"""
    def 等待并吞错(一项):#等待一路
        """等待一路并吞错。"""
        try:#等待
            一项.等待()#等到结算
        except BaseException:#排空不抛
            pass#吞掉
    线程表=[]#工作线程
    for 一项 in 任务列表:#每路一线程
        工作=threading.Thread(target=等待并吞错,args=(一项,),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#等全部结束
        工作.join()#等到结束

def 赛跑(函数列表):#Promise.race
    """先结算的一路获胜。"""
    完成=任务()#先到先得
    def 在线程执行(函数):#一路
        """跑一路并尝试结算。"""
        try:#执行
            完成.兑现(函数())#成功
        except BaseException as 错误:#失败
            完成.拒绝(错误)#拒绝
    for 函数 in 函数列表:#每路一线程
        工作=threading.Thread(target=在线线程执行,args=(函数,),daemon=True)#工作线程
        工作.start()#启动
    return 完成.等待()#先到

def 输出文本(块表):#子最终输出块压成文本
    """把子最终输出块里的 text 块拼成字符串。"""
    段列表=[]#文本段
    for 块 in 块表:#逐块
        if type(块) is dict and 块.get('type')=='text' and 'text' in 块:#文本块
            段列表.append(块['text'])#收下
    return ''.join(段列表)#拼接

def 默认标签(提示词):#无 label 时从提示词截
    """脚本没传 label 时，用提示词首行做短展示标签。"""
    换行=提示词.find('\n')#首行
    行=提示词 if 换行==-1 else 提示词[:换行]#首行
    if len(行)<=48:#够短
        return 行#原样
    return 行[:47]+'…'#截断

class 工作流执行:#隔离进程内的一次脚本执行
    """隔离进程内的一次脚本执行。宿主拥有取消与被丢弃子工作的清理。"""
    def __init__(自身,元数据,正文,参数,上限,观察器,子端口):#编译并注入钩子
        """编译脚本包装并注入 agent/parallel/pipeline/phase/log/args。上限是 dict。观察器与子端口是对象。"""
        自身._上限=上限#钩子上限
        自身._观察器=观察器#进度观察
        自身._子端口=子端口#子回调
        自身._已启动=0#从 1 计的 agent() 次数
        自身._活动槽=0#占用的并发槽
        自身._槽等待=[]#FIFO 等待
        自身._槽锁=threading.Lock()#槽位锁
        自身._当前阶段=None#当前 phase 标题
        环境={'__builtins__':__builtins__}#脚本全局
        def 流水线钩子(条目,*阶段):#pipeline 形参
            """把可变阶段收成列表交给流水线。"""
            return 自身.流水线(条目,阶段)#流水线
        环境['agent']=自身.智能体#agent 钩子
        环境['parallel']=自身.并行#parallel 钩子
        环境['pipeline']=流水线钩子#pipeline 钩子
        环境['phase']=自身.阶段#phase 钩子
        环境['log']=自身.日志#log 钩子
        环境['args']=参数#输入
        try:#编译包装
            源='def 脚本():\n'#函数头
            if 正文=='':#空体
                源+='    return None\n'#空
            else:#有体
                for 行 in 正文.split('\n'):#逐行
                    源+='    '+行+'\n'#缩进
            盒={}#局部
            exec(源,环境,盒)#编译进钩子全局
            自身._已编译=盒['脚本']#函数
        except SyntaxError as 错误:#解析失败
            raise 工作流错误('workflow script does not parse: '+str(错误),'SCRIPT_PARSE',{'cause':错误})#解析

    def 驱动(自身):#跑脚本并物化 JSON 返回值
        """跑脚本并物化 JSON 返回值。完成或错误结果；脚本失败永不拒绝。"""
        try:#执行
            原始=自身._已编译()#跑包装；钩子闭包走实例
            if 原始 is None:#无返回
                值=None#null
            else:#有返回
                值=自身.物化结果(原始)#物化
            return {'value':值,'stopReason':'completed','agentsStarted':自身._已启动}#完成
        except BaseException as 错误:#脚本失败
            return {'value':None,'stopReason':'error','error':渲染抛出(错误),'agentsStarted':自身._已启动}#错误

    def 物化结果(自身,原始):#返回值
        """物化脚本返回值；违规变成 RESULT_UNSERIALIZABLE。"""
        try:#物化
            return 从领域物化(原始,'workflow result')#物化
        except 物化错误 as 错误:#物化失败
            raise 工作流错误(
                "the workflow's return value is not plain JSON data — "+错误.原因+'. Return only JSON-serializable objects/arrays/scalars.',
                'RESULT_UNSERIALIZABLE',
                {'cause':错误},
            )#不可序列化

    def 取得槽(自身):#FIFO 取一个并发槽
        """取得一个并发槽；满则按 FIFO 等待。"""
        with 自身._槽锁:#互斥
            if 自身._活动槽<自身._上限['maxConcurrentAgents']:#有空位
                自身._活动槽+=1#占用
                return#立刻
            事件=threading.Event()#等待
            自身._槽等待.append(事件)#排队
        事件.wait()#等到唤醒

    def 释放槽(自身):#还槽并唤醒下一个
        """释放一个并发槽，FIFO 唤醒下一个等待者。"""
        下一个=None#待唤醒
        with 自身._槽锁:#互斥
            自身._活动槽-=1#还
            if len(自身._槽等待)>0:#有人等
                下一个=自身._槽等待.pop(0)#FIFO
                自身._活动槽+=1#占给下一个
        if 下一个 is not None:#唤醒
            下一个.set()#放行

    def 智能体(自身,原始提示,原始选项=None):#agent 钩子
        """agent(prompt, opts) 钩子。"""
        if type(原始提示) is not str or len(原始提示)==0:#必须非空串
            raise 工作流错误('agent() requires a non-empty prompt string','INVALID_ARGUMENT')#参数
        选项=自身.读智能体选项(原始选项)#选项
        if 自身._已启动>=自身._上限['maxTotalAgents']:#触顶
            raise 工作流错误(
                'this run reached its total agent cap ('+str(自身._上限['maxTotalAgents'])+') — a runaway-loop backstop; raise the applicable maxTotalAgents limit if the scale is intentional',
                'AGENT_CAP',
            )#上限
        自身._已启动+=1#计数
        序号=自身._已启动#从 1
        标签=选项['label'] if 'label' in 选项 else 默认标签(原始提示)#展示标签
        阶段=选项['phase'] if 'phase' in 选项 else 自身._当前阶段#阶段
        自身.取得槽()#占槽
        try:#启动到拆除
            try:#启动子
                请求={'prompt':原始提示}#提示词
                if 'schema' in 选项:#有模式
                    请求['schema']=选项['schema']#带上
                if 'provider' in 选项:#有提供方
                    请求['provider']=选项['provider']#带上
                if 'model' in 选项:#有模型
                    请求['model']=选项['model']#带上
                跑=自身._子端口.启动智能体(请求)#发布
            except BaseException as 错误:#启动失败
                raise 工作流错误('agent() could not start a child: '+渲染抛出(错误),'AGENT_START',{'cause':错误})#启动
            信息={'seq':序号,'label':标签,'childId':会话标识(跑.id)}#身份
            if 阶段 is not None:#有阶段
                信息['phase']=阶段#带上
            自身._观察器.智能体开始(信息)#开始
            try:#等结果并拆除
                try:#等子
                    结果=跑.result.等待()#子终态
                except BaseException as 错误:#基础设施
                    自身._观察器.智能体结束(dict(信息,outcome='failed'))#配对失败
                    raise 工作流错误('child agent run failed: '+渲染抛出(错误),'AGENT_RESULT',{'cause':错误})#致命
                if 结果['stopReason']=='completed':#完成
                    if 'schema' in 选项:#要结构化
                        if 'structured' not in 结果 or 结果['structured'] is None:#没给
                            自身._观察器.智能体结束(dict(信息,outcome='failed'))#失败
                            return None#null
                        自身._观察器.智能体结束(dict(信息,outcome='completed'))#完成
                        return 结果['structured']#结构化
                    自身._观察器.智能体结束(dict(信息,outcome='completed'))#完成
                    return 输出文本(结果['output'])#文本
                自身._观察器.智能体结束(dict(信息,outcome='failed'))#失败
                return None#null
            finally:#拆除
                跑.销毁()#拆除
        finally:#还槽
            自身.释放槽()#还

    def 读智能体选项(自身,原始选项):#物化并校验选项袋
        """从领域物化并校验 agent() 选项袋。"""
        if 原始选项 is None:#缺省
            return {}#空
        try:#物化
            选项=从领域物化(原始选项,'agent() options')#物化
        except 物化错误 as 错误:#不是 JSON
            raise 工作流错误('agent() options must be plain JSON data — '+错误.原因,'INVALID_ARGUMENT',{'cause':错误})#参数
        if type(选项) is not dict:#必须对象
            raise 工作流错误('agent() options must be an object','INVALID_ARGUMENT')#参数
        for 键 in 选项.keys():#未知键
            if 键 in 支持的智能体选项:#认识
                continue#下一项
            if 键 in 推迟的智能体选项:#推迟
                raise 工作流错误('agent() option "'+键+'" is deferred and not supported by this engine (supported: label, phase, schema, provider, model)','UNSUPPORTED_OPTION')#推迟
            raise 工作流错误('agent() option "'+键+'" is not recognized (supported: label, phase, schema, provider, model)','UNSUPPORTED_OPTION')#未知
        for 键 in ('label','phase','provider','model'):#必须字符串
            if 键 in 选项 and 选项[键] is not None and type(选项[键]) is not str:#类型
                raise 工作流错误('agent() option "'+键+'" must be a string','INVALID_ARGUMENT')#参数
        模式=None#可选 schema
        if 'schema' in 选项 and 选项['schema'] is not None:#有模式
            try:#子集
                断言对象json模式(选项['schema'])#断言
                模式=选项['schema']#收下
            except json模式错误 as 错误:#子集外
                raise 工作流错误('agent() schema is outside the supported subset — '+str(错误),'UNSUPPORTED_SCHEMA',{'cause':错误})#模式
        结果={}#规范化
        if 'label' in 选项 and 选项['label'] is not None:#标签
            结果['label']=选项['label']#带上
        if 'phase' in 选项 and 选项['phase'] is not None:#阶段
            结果['phase']=选项['phase']#带上
        if 'provider' in 选项 and 选项['provider'] is not None:#提供方
            结果['provider']=选项['provider']#带上
        if 'model' in 选项 and 选项['model'] is not None:#模型
            结果['model']=选项['model']#带上
        if 模式 is not None:#模式
            结果['schema']=模式#带上
        return 结果#选项

    def 并行(自身,原始块):#parallel 钩子
        """每块捕获 → null；致命错误传播。"""
        if type(原始块) is not list:#必须数组
            raise 工作流错误('parallel() requires an array of zero-argument functions','INVALID_ARGUMENT')#参数
        自身.断言条目上限(len(原始块),'parallel()')#上限
        块列表=[]#函数表
        下标=0#从 0
        while 下标<len(原始块):#逐项
            块=原始块[下标]#一项
            if not callable(块):#必须函数
                raise 工作流错误('parallel() item '+str(下标)+' is not a function','INVALID_ARGUMENT')#参数
            块列表.append(块)#收下
            下标+=1#推进
        def 跑一块(块):#一路
            """跑一块；致命再抛，普通变 null。"""
            try:#执行
                return 块()#结果
            except BaseException as 错误:#捕获
                if 是否致命工作流错误(错误):#致命
                    raise 错误#再抛
                return None#null
        函数列表=[]#并发函数
        for 块 in 块列表:#每块一路
            def 制作(一块):#钉住本块
                """钉住一块。"""
                def 在线程执行():#一路
                    """跑一块。"""
                    return 跑一块(一块)#执行
                return 在线程执行#函数
            函数列表.append(制作(块))#收下
        return 全部并发(函数列表)#并发

    def 流水线(自身,原始条目,原始阶段):#pipeline 钩子
        """每条目的阶段链，无跨阶段屏障。"""
        if type(原始条目) is not list:#必须数组
            raise 工作流错误('pipeline() requires an items array','INVALID_ARGUMENT')#参数
        自身.断言条目上限(len(原始条目),'pipeline()')#上限
        if len(原始阶段)==0:#至少一阶段
            raise 工作流错误('pipeline() requires at least one stage function','INVALID_ARGUMENT')#参数
        阶段表=[]#函数表
        下标=0#从 0
        while 下标<len(原始阶段):#逐阶段
            阶段=原始阶段[下标]#一项
            if not callable(阶段):#必须函数
                raise 工作流错误('pipeline() stage '+str(下标)+' is not a function','INVALID_ARGUMENT')#参数
            阶段表.append(阶段)#收下
            下标+=1#推进
        def 跑一条(条目,序号):#一条流水线
            """顺序跑阶段；致命再抛，普通变 null。"""
            值=条目#起点
            try:#阶段链
                for 阶段 in 阶段表:#逐阶段
                    值=阶段(值,条目,序号)#下一步
                return 值#结果
            except BaseException as 错误:#捕获
                if 是否致命工作流错误(错误):#致命
                    raise 错误#再抛
                return None#null
        函数列表=[]#并发函数
        号=0#从 0
        for 项 in 原始条目:#每条目一路
            def 制作(一条目,一号):#钉住本条
                """钉住一条。"""
                def 在线程执行():#一路
                    """跑一条流水线。"""
                    return 跑一条(一条目,一号)#执行
                return 在线程执行#函数
            函数列表.append(制作(项,号))#收下
            号+=1#推进
        return 全部并发(函数列表)#并发

    def 断言条目上限(自身,长度,钩子):#每调用上限
        """一次 parallel/pipeline 的条目上限。"""
        if 长度>自身._上限['maxItemsPerCall']:#越顶
            raise 工作流错误(
                钩子+' received '+str(长度)+' items — over the per-call cap ('+str(自身._上限['maxItemsPerCall'])+'); split the work or raise maxItemsPerCall in the engine config',
                'ITEM_CAP',
            )#上限

    def 阶段(自身,标题):#phase 钩子
        """设定后续 agent() 的当前标签并通知观察器。"""
        if type(标题) is not str or len(标题)==0:#必须非空串
            raise 工作流错误('phase() requires a non-empty title string','INVALID_ARGUMENT')#参数
        自身._当前阶段=标题#记下
        自身._观察器.阶段(标题)#通知

    def 日志(自身,消息):#log 钩子
        """向观察器叙述。"""
        if type(消息) is not str:#必须字符串
            raise 工作流错误('log() requires a message string','INVALID_ARGUMENT')#参数
        自身._观察器.日志(消息)#通知
