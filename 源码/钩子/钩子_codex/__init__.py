"""在 harness 拦截点上桥接未经修改的 Codex 命令钩子。支持五个点（SessionStart、提示/工具前后、Stop）、仅正则匹配器、snake_case 载荷且不加末尾换行、没有钩子环境或命令替换、也没有工具前批准或改写路径；只兑现阻断判定。共用的执行与解析在 `dsh-hook-protocol`。"""
import json,os,time,threading#读配置、进程 cwd、墙钟与后台链
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from ...模型后端.llm import 创建用户消息#导入用户消息工厂
from ..钩子协议 import (
    追加钩子调用,#追加调用事件
    追加钩子结果,#追加结果事件
    创建分离运行,#创建分离运行跟踪器
    默认钩子超时毫秒,#默认超时
    默认stderr摘要最大字符,#stderr摘要默认上限
    匹配命中 as 匹配判定,#匹配判定
    合并钩子输出,#合并钩子输出
    跑钩子,#执行命令钩子
)#钩子协议库
from .配置 import 解析科德克斯配置#导入配置解析

名称='hooks-codex'#插件名
注入=['shell']#依赖 shell 服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
配置={#插件配置：Codex hooks.json 所在位置，以及载荷上的模型名
    'configPath':字符串字段(),#Codex hooks.json 路径；必填；进程级，加载时读一次
    'model':字符串字段(默认值=''),#盖在每份载荷上的模型名（Codex 每个事件都带 model）
    'defaultTimeoutMs':数字字段(默认值=默认钩子超时毫秒),#钩子自己没设超时时的默认超时毫秒（Codex 默认：600000）
    'stderrSummaryMaxChars':数字字段(默认值=默认stderr摘要最大字符),#hook/result 事件里持久 stderr 摘要的字符上限
}#配置模式结束
Config=配置#Cordis配置模式
插件来源={'kind':'plugin','plugin':'hooks-codex'}#本桥注入的每条上下文都盖上的来源
处理器计数=0#处理器计数，用于稳定 id

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

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺席#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 取墙钟毫秒():#对齐 performance.now
    """单调墙钟毫秒，供钩子时长计量。"""
    return time.perf_counter()*1000#单调毫秒

def 下一条处理器标识(钩子点):#生成下一条处理器 id
    """每个处理器的稳定 id，用来在日志里把调用/结果对上。"""
    global 处理器计数#共享计数
    处理器计数+=1#递增
    return 'codex:'+钩子点+':'+str(处理器计数)#方言、钩子点、序号

def 断言正整数(名字,值):#断言正整数
    """摘要上限约束的是持久事件字段——必须是正整数，否则切片会静默失常。"""
    if isinstance(值,bool) or (not isinstance(值,int)) or 值<1:#非正整数则失败
        raise TypeError('hooks-codex: '+名字+' must be a positive integer')#报告非法配置

def 最后轮次(智能体):#取最后打开轮次
    """智能体日志里最后一个打开轮次号；没有智能体则为 0。"""
    if 智能体 is None:#没有智能体
        return 0#零
    事件们=list(取字段(取字段(智能体,'session'),'events') or [])#事件拷贝
    for 事件 in reversed(事件们):#从后往前找轮次开始
        if 取字段(事件,'type')=='turn/start':#找到
            return 取字段(取字段(事件,'data'),'turn') or 0#用其轮次
    return 0#否则零

def 块们折文本(内容):#内容块折成纯文本
    """把内容块摊成钩子载荷携带的文本（常见情况）。"""
    文本们=[]#只留文本块
    for 块 in (内容 or []):#逐块
        if 取字段(块,'type')=='text':#文本块
            文本们.append(取字段(块,'text') or '')#收正文
    return ''.join(文本们)#拼接

def 公共载荷(上下文,智能体,事件,模型):#Codex 载荷公共字段（没有 turn_id）
    """每份 Codex 载荷上的公共字段（没有 turn_id）。"""
    if 智能体 is None:#没有智能体则空路径用 null
        文本记录路径=None#空路径用 null，保留 Codex string|null 形状
    else:#有智能体
        定位=None#持久化定位
        持久化=上下文.get('sessionPersistence')#可选会话持久化
        if 持久化 is not None:#有服务
            定位=解开(持久化.定位(取字段(取字段(智能体,'session'),'header')))#定位文本记录
        文本记录路径=取字段(定位,'path')#路径或缺席（下游当 null）
        if 文本记录路径 is None:#没有定位到
            文本记录路径=None#显式 null
    return {#组装公共字段
        'session_id':取字段(取字段(取字段(智能体,'session'),'header'),'id') or '',#会话 id
        'transcript_path':文本记录路径,#文本记录路径或 null
        'cwd':取字段(取字段(取字段(智能体,'session'),'header'),'cwd') or os.getcwd(),#工作目录
        'hook_event_name':事件,#钩子事件名
        'model':模型,#模型名
        'permission_mode':'default',#权限模式
    }#公共字段对象

def 轮次公共载荷(上下文,智能体,事件,模型):#公共字段加 turn_id
    """公共字段加 turn_id，给轮次作用域事件（PreToolUse/PostToolUse/UserPromptSubmit/Stop）。"""
    载荷=公共载荷(上下文,智能体,事件,模型)#公共字段
    载荷['turn_id']=str(最后轮次(智能体))#加上当前打开轮次
    return 载荷#带轮次 id 的公共字段

def 命令参数(参数):#从工具调用已解析参数里取出 command 字符串
    """从工具调用的已解析参数里取出 command 字符串，否则 ''。"""
    if isinstance(参数,dict) and 'command' in 参数:#有 command 键
        命令=参数['command']#取出 command 值
        if isinstance(命令,str):#是字符串才用
            return 命令#命令串
    elif 参数 is not None and hasattr(参数,'command'):#对象属性
        命令=getattr(参数,'command',None)#取出
        if isinstance(命令,str):#是字符串才用
            return 命令#命令串
    return ''#否则空串

def 工具前载荷(上下文,执行,模型):#PreToolUse 载荷
    """PreToolUse 方言载荷；tool_name 与匹配主体一致，tool_input 保持 Codex 的 { command } 形状。"""
    载荷=轮次公共载荷(上下文,取字段(执行,'agent'),'PreToolUse',模型)#带轮次公共字段
    载荷['tool_name']=取字段(执行,'name')#真正的工具名
    载荷['tool_input']={'command':命令参数(取字段(执行,'arguments'))}#Codex shell 载荷形状
    载荷['tool_use_id']=取字段(执行,'callId')#调用 id
    return 载荷#载荷

def 工具后载荷(上下文,执行,结果,模型):#PostToolUse 载荷
    """PostToolUse 方言载荷；再加上工具响应文本。"""
    载荷=轮次公共载荷(上下文,取字段(执行,'agent'),'PostToolUse',模型)#带轮次公共字段
    载荷['tool_name']=取字段(执行,'name')#工具名
    载荷['tool_input']={'command':命令参数(取字段(执行,'arguments'))}#命令输入
    载荷['tool_use_id']=取字段(执行,'callId')#调用 id
    载荷['tool_response']=块们折文本(取字段(结果,'content'))#工具响应文本
    return 载荷#载荷

def 应用(上下文,配置值=None):#安装 Codex 钩子桥
    """在 ctx 生命周期内登记 Codex 钩子桥监听器。读或解析失败只记日志，不登记任何钩子。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    stderr摘要上限=取字段(配置值,'stderrSummaryMaxChars')#摘要上限
    if stderr摘要上限 is None:#未给
        stderr摘要上限=默认stderr摘要最大字符#默认
    断言正整数('stderrSummaryMaxChars',stderr摘要上限)#上限必须是正整数
    默认超时=取字段(配置值,'defaultTimeoutMs')#默认超时
    if 默认超时 is None:#未给
        默认超时=默认钩子超时毫秒#默认
    配置路径=取字段(配置值,'configPath')#配置文件路径
    已解析={}#解析出的可跑配置
    try:#读取并解析配置文件
        with open(配置路径,'r',encoding='utf-8') as 文件:#同步读配置文件
            原始=json.loads(文件.read())#当 JSON
        解析结果=解析科德克斯配置(原始)#解析 Codex 配置
        已解析=解析结果['config']#留下可跑组
        for 跳过 in 解析结果['skipped']:#警告被跳过的钩子
            上下文.logger.warn('hooks-codex: skipping '+取字段(跳过,'reason')+' on '+取字段(跳过,'event')+' (only sync command hooks run)')#记录跳过
    except Exception as 错误:#读或解析失败则不登记钩子
        上下文.logger.warn('hooks-codex: could not load hook config "'+str(配置路径)+'": '+str(错误)+' — no hooks registered')#记录加载失败
        return#不安装监听器
    模型=取字段(配置值,'model')#载荷上的模型名
    if 模型 is None:#未给
        模型=''#默认空串
    分离=创建分离运行()#分离运行跟踪器
    上下文.effect(lambda:分离.drain,'hooks-codex: drain detached hook runs')#拆除时排空分离运行

    def 跑点(钩子点,匹配主体,载荷,选项):#跑一个钩子点上的全部命中命令
        """跑并折合一个已配置的 Codex 钩子点。传入轮次时，在该未关闭轮次里记录钩子调用/结果对。分离生命周期点省略这对事件。"""
        组们=已解析.get(钩子点) or []#该点的匹配组
        输出们=[]#各条钩子的解码输出
        智能体=取字段(选项,'agent')#可选智能体
        轮次=取字段(选项,'turn')#可选轮次
        信号=取字段(选项,'signal')#取消信号
        纯stdout当上下文=取字段(选项,'plainStdoutAsContext') is True#干净纯 stdout 是否当作附加上下文
        工作目录=取字段(取字段(取字段(智能体,'session'),'header'),'cwd')#会话工作目录
        for 组 in 组们:#逐个匹配组
            if not 匹配判定(取字段(组,'matcher'),匹配主体,'codex'):#Codex 始终把匹配器当正则；未命中则跳过
                continue#下一组
            for 钩子 in (取字段(组,'hooks') or []):#逐条命令钩子
                处理器标识=下一条处理器标识(钩子点)#本条调用的稳定 id
                会话=取字段(智能体,'session')#可选会话
                if 会话 is not None and 轮次 is not None:#有会话且在轮内才记调用事件
                    调用数据={#追加 hook/invoked
                        'turn':轮次,#轮次
                        'point':钩子点,#点
                        'dialect':'codex',#方言
                        'handlerId':处理器标识,#id
                    }#调用身份
                    if 取字段(组,'matcher') is not None:#有匹配模式才写入
                        调用数据['matcher']=取字段(组,'matcher')#匹配器
                    追加钩子调用(会话,调用数据)#追加
                运行选项={#执行这条命令钩子
                    'payload':载荷,#stdin 载荷
                    'defaultTimeoutMs':默认超时,#默认超时
                    'signal':信号,#取消信号
                    'trailingNewline':False,#Codex 写 stdin 不加末尾换行
                    'expectedEventName':钩子点,#用当前钩子点守卫专属字段
                }#运行选项
                if 工作目录 is not None:#有工作目录才传入
                    运行选项['cwd']=工作目录#工作目录
                运行结果=解开(跑钩子(上下文.shell,钩子,运行选项,取墙钟毫秒))#执行并计量
                输出=取字段(运行结果,'output')#解码输出
                时长=取字段(运行结果,'durationMs')#墙钟毫秒
                if (纯stdout当上下文#允许纯 stdout 当上下文
                    and 取字段(输出,'exitCode')==0#干净退出
                    and 取字段(输出,'additionalContext') is None#还没有结构化附加上下文
                    and isinstance(取字段(输出,'stdout'),str)#有 stdout
                    and len(取字段(输出,'stdout'))>0#非空
                    and not 取字段(输出,'stdout').startswith('{')):#不像 JSON 对象
                    if isinstance(输出,dict):#映射则可写
                        输出['additionalContext']=取字段(输出,'stdout')#把纯 stdout 当作附加上下文
                    else:#对象属性
                        setattr(输出,'additionalContext',取字段(输出,'stdout'))#写入属性
                输出们.append(输出)#收进待合并列表
                if 取字段(输出,'systemMessage') is not None:#发出了系统消息
                    上下文.logger.warn('hooks-codex: '+钩子点+' hook emitted a systemMessage, which is not yet surfaced (ignored)')#尚未展示，只警告
                if 会话 is not None and 轮次 is not None:#有会话且在轮内才记结果事件
                    追加钩子结果(会话,{#追加 hook/result
                        'turn':轮次,#轮次
                        'point':钩子点,#点
                        'handlerId':处理器标识,#id
                        'output':输出,#输出
                        'stderrSummaryMaxChars':stderr摘要上限,#摘要上限
                        'durationMs':时长,#时长
                    })#结果事件
        return 合并钩子输出(输出们)#按最严格规则折合

    def 从合并取上下文(合并):#折成用户消息上下文
        """从钩子输出组装附加模型上下文；空则返回 None。"""
        附加=取字段(合并,'additionalContext') or []#附加上下文列表
        if len(附加)==0:#没有附加上下文
            return None#缺席
        内容=[{'type':'text','text':文本} for 文本 in 附加]#每条做成文本块
        return 创建用户消息({'content':内容,'source':插件来源})#盖上本桥来源

    def 前置上下文(本桥,下游们):#把本桥上下文放前面
        """前置一条上下文，不压平来源字段或其他下游元数据。"""
        return [本桥]+list(下游们 or [])#本桥在前，下游原有在后

    def 会话开始监听(载荷,*剩余):#会话开始时跑 SessionStart
        """SessionStart 在分离钩子兑现时注入纯 stdout；慢钩子可能赶不上第一次请求。"""
        智能体=取字段(载荷,'agent')#智能体
        来源=取字段(载荷,'source')#会话来源
        def 任务():#分离链
            try:#兑现后注入上下文
                会话载荷=公共载荷(上下文,智能体,'SessionStart',模型)#公共字段
                会话载荷['source']=来源#加上来源
                合并=解开(跑点('SessionStart',来源,会话载荷,{#按来源匹配，纯 stdout 当上下文，分离跟踪
                    'agent':智能体,#智能体
                    'plainStdoutAsContext':True,#纯 stdout 当上下文
                    'signal':取字段(分离,'signal'),#分离取消信号
                }))#跑 SessionStart
                上下文消息=从合并取上下文(合并)#折成用户消息
                if 上下文消息 is not None:#有上下文才注入
                    解开(智能体.inject(上下文消息))#注入
            except Exception as 错误:#分离失败只警告
                上下文.logger.warn('hooks-codex: SessionStart hook failed: '+str(错误))#记录失败
        后台=操作任务()#分离链任务
        def 跑():#后台跑分离链
            try:#跑任务
                任务()#跑分离链
                后台.兑现(None)#成功
            except BaseException as 错误:#失败
                后台.拒绝(错误)#拒绝
        threading.Thread(target=跑,daemon=True).start()#启动
        分离.track(后台)#登记分离链
    上下文.on('agent/session-start',会话开始监听)#结束 session-start 监听

    def 预步骤监听(载荷,下一步,*剩余):#步进前跑 UserPromptSubmit
        """UserPromptSubmit → PreStepDecision。Codex 支持拒绝，不支持改写或询问。"""
        消息们=取字段(载荷,'messages') or []#步进消息
        if len(消息们)==0:#没有消息则直接委托
            return 解开(下一步())#委托
        内容=[]#摊平全部内容块
        for 消息 in 消息们:#逐条
            内容.extend(list(取字段(消息,'content') or []))#摊平
        提示载荷体=公共载荷(上下文,取字段(载荷,'agent'),'UserPromptSubmit',模型)#公共字段
        提示载荷体['turn_id']=str(取字段(载荷,'turn'))#轮次 id
        提示载荷体['prompt']=块们折文本(内容)#提示文本
        合并=解开(跑点('UserPromptSubmit','',提示载荷体,{#该事件无匹配主体
            'agent':取字段(载荷,'agent'),#智能体
            'turn':取字段(载荷,'turn'),#轮次
            'plainStdoutAsContext':True,#纯 stdout 当上下文
            'signal':取字段(载荷,'signal'),#信号
        }))#跑 UserPromptSubmit
        if 取字段(合并,'decision')=='deny':#拒绝则挡下这一步
            return {'kind':'reject'}#拒绝进入
        下游=解开(下一步())#先委托后续监听器
        本桥=从合并取上下文(合并)#本桥上下文
        if 本桥 is None or 取字段(下游,'kind')!='enter':#没有上下文或下游不是 enter
            return 下游#原样返回
        return {#进入并带上本桥上下文
            'kind':'enter',#进入步进
            'messages':list(取字段(下游,'messages') or [])+[本桥],#下游消息后面追加本桥上下文
        }#enter 判定
    上下文.on('agent/pre-step',预步骤监听)#结束 pre-step 监听

    def 工具前监听(执行,下一步,*剩余):#工具执行前跑 PreToolUse
        """PreToolUse → PreToolDecision。Codex 只阻断（不兑现 allow/ask）。"""
        轮次=最后轮次(取字段(执行,'agent'))#取当前打开轮次
        选项={'turn':轮次,'signal':取字段(执行,'signal')}#运行选项
        if 取字段(执行,'agent') is not None:#有智能体才传入
            选项['agent']=取字段(执行,'agent')#智能体
        合并=解开(跑点('PreToolUse',取字段(执行,'name'),工具前载荷(上下文,执行,模型),选项))#按工具名匹配
        if 取字段(合并,'decision')=='deny':#拒绝则否认
            return {'kind':'deny','reason':取字段(合并,'reason') or 'blocked by PreToolUse hook'}#否认
        return 解开(下一步())#否则委托后续
    上下文.on('tools/pre-execute',工具前监听)#结束 pre-execute 监听

    def 工具后监听(执行,结果,下一步,*剩余):#工具执行后跑 PostToolUse
        """PostToolUse → PostToolDecision（带反馈阻断，或附上上下文）。"""
        轮次=最后轮次(取字段(执行,'agent'))#取当前打开轮次
        选项={'turn':轮次,'signal':取字段(执行,'signal')}#运行选项
        if 取字段(执行,'agent') is not None:#有智能体才传入
            选项['agent']=取字段(执行,'agent')#智能体
        合并=解开(跑点('PostToolUse',取字段(执行,'name'),工具后载荷(上下文,执行,结果,模型),选项))#按工具名匹配
        上下文消息=从合并取上下文(合并)#附加上下文
        if 取字段(合并,'decision')=='deny':#拒绝则阻断工具结果
            判定={#阻断
                'kind':'block',#阻断
                'feedback':[{'type':'text','text':取字段(合并,'reason') or 'blocked by PostToolUse hook'}],#反馈
            }#阻断判定
            if 上下文消息 is not None:#可选带上下文
                判定['additionalContexts']=[上下文消息]#附加上下文
            return 判定#阻断
        下游=解开(下一步())#先委托后续监听器
        if 上下文消息 is None:#没有上下文则原样返回
            return 下游#原样
        if 取字段(下游,'kind')=='block':#下游已经阻断
            合并下游=dict(下游)#拷贝
            合并下游['additionalContexts']=前置上下文(上下文消息,取字段(下游,'additionalContexts'))#把本桥上下文前置进去
            return 合并下游#带上下文的阻断
        合并下游=dict(下游)#非阻断判定也前置上下文
        合并下游['additionalContexts']=前置上下文(上下文消息,取字段(下游,'additionalContexts'))#前置本桥上下文
        return 合并下游#带上下文的下游判定
    上下文.on('tools/post-execute',工具后监听)#结束 post-execute 监听

    def 轮次将停监听(载荷,*剩余):#轮次将停时跑 Stop
        """阻断型 Stop 钩子在停止边界转向，让状态机看到待处理输入再跑一步。"""
        智能体=取字段(载荷,'agent')#智能体
        停止载荷体=轮次公共载荷(上下文,智能体,'Stop',模型)#带轮次公共字段
        停止载荷体['stop_hook_active']=False#循环守卫标志恒为假
        停止载荷体['last_assistant_message']=None#恒为 null
        合并=解开(跑点('Stop','',停止载荷体,{#该事件无匹配主体
            'agent':智能体,#智能体
            'turn':取字段(载荷,'turn'),#轮次
            'signal':取字段(载荷,'signal'),#信号
        }))#跑 Stop
        if 取字段(合并,'decision')=='deny':#阻断型 Stop 强迫续跑
            文本=取字段(合并,'reason') or 'continue: blocked by Stop hook'#转向文本
            解开(智能体.steer(创建用户消息({'content':[{'type':'text','text':文本}],'source':插件来源})))#注入转向消息
    上下文.on('agent/turn-stopping',轮次将停监听)#结束 turn-stopping 监听

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出

__all__=['名称','注入','应用','配置','Config','name','inject','apply','默认','default']#公开面
