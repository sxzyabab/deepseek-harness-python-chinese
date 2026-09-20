import json,os,time,threading#读配置、进程 cwd、单调时钟与后台链
from concurrent.futures import Future as 原生结果#单次操作结果
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from ...模型后端.llm import 创建用户消息#导入用户消息工厂
from ..钩子协议 import (
    追加钩子调用,#追加调用事件
    追加钩子结果,#追加结果事件
    创建分离运行,#创建分离运行跟踪器
    默认钩子超时毫秒,#默认超时
    默认stderr摘要最大字节,#stderr摘要默认上限
    匹配命中,#匹配判定
    合并钩子输出,#合并钩子输出
    执行钩子,#执行命令钩子
)#钩子协议库
from .配置 import 解析科德克斯配置#导入配置解析

名称='hooks-codex'#插件名
依赖=['shell']#依赖 shell 服务
配置={#插件配置：Codex hooks.json 所在位置，以及载荷上的模型名
    'configPath':字符串字段(),#Codex hooks.json 路径；必填；进程级，加载时读一次
    'model':字符串字段(默认值=''),#盖在每份载荷上的模型名（Codex 每个事件都带 model）
    'defaultTimeoutMs':数字字段(默认值=默认钩子超时毫秒),#钩子自己没设超时时的默认超时毫秒（Codex 默认：600000）
    'stderrSummaryMaxChars':数字字段(默认值=默认stderr摘要最大字节),#hook/result 事件里持久 stderr 摘要的字节上限
}#配置模式结束
插件来源={'kind':'plugin','plugin':'hooks-codex'}#本桥注入的每条上下文都盖上的来源
处理器计数=0#处理器计数，用于稳定 id

class 钩子codex错误(Exception):
    """Codex 钩子桥包的异常基类。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身.原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身.原生结果.done():#尚未结算
            自身.原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身.原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身.原生结果.set_exception(错误)#原样拒绝
            else:
                包装=钩子codex错误('任务被拒绝')#包装拒绝
                包装.原因=错误#附加信息做成属性
                自身.原生结果.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身.原生结果.result(timeout=超时)#取结果或抛错

def 取单调纳秒():
    """单调时钟纳秒，供钩子时长计量。"""
    return time.perf_counter_ns()#单调纳秒

def 下一条处理器标识(钩子点):
    """每个处理器的稳定 id，用来在日志里把调用/结果对上。"""
    global 处理器计数#共享计数
    处理器计数+=1#递增
    return 'codex:'+钩子点+':'+str(处理器计数)#方言、钩子点、序号

def 断言正整数(名字,值):
    """摘要上限约束的是持久事件字段——必须是正整数，否则切片会静默失常。"""
    if isinstance(值,bool) or (not isinstance(值,int)) or 值<1:#非正整数则失败
        raise TypeError('hooks-codex: '+名字+' 必须是正整数')#报告非法配置

def 最后轮次(智能体):
    """智能体日志里最后一个打开轮次号；没有智能体则为 0。智能体是对象。"""
    if 智能体 is None:#没有智能体
        return 0#零
    for 事件 in reversed(list(智能体.session.events)):#从后往前找轮次开始
        if 事件['type']=='turn/start':#找到
            数据=事件['data']#载荷
            if 'turn' not in 数据 or 数据['turn'] is None:#无轮次
                return 0#零
            return 数据['turn']#用其轮次
    return 0#否则零

def 拼接块文本(内容):
    """把内容块摊成钩子载荷携带的文本（常见情况）。内容是块 dict 列表。"""
    文本列表=[]#只留文本块
    块列表=内容 if 内容 is not None else []#缺席当空列表
    for 块 in 块列表:#逐块
        if 块['type']=='text':#文本块
            文本列表.append(块['text'] if 'text' in 块 and 块['text'] is not None else '')#收正文；缺席当空串
    return ''.join(文本列表)#拼接

def 共用载荷(上下文,智能体,事件,模型):
    """每份 Codex 载荷上的公共字段（没有 turn_id）。智能体是对象或 None。"""
    if 智能体 is None:#没有智能体则空路径用 null
        文本记录路径=None#空路径用 null，保留 Codex string|null 形状
        会话号=''#空会话
        工作目录=os.getcwd()#进程 cwd
    else:
        头=智能体.session.header#会话头 dict
        会话号=头['id'] if 'id' in 头 and 头['id'] is not None else ''#会话 id；空串当无
        if 'cwd' in 头 and 头['cwd'] is not None and 头['cwd']!='':#空串 cwd 视为无，回落进程 cwd（原 ||）
            工作目录=头['cwd']#会话工作目录
        else:
            工作目录=os.getcwd()#进程 cwd
        定位=None#持久化定位
        持久化=上下文.获取服务('sessionPersistence',False)#可选会话持久化
        if 持久化 is not None:#有服务
            定位=持久化.定位(头)#定位文本记录，同步返回 dict 或 None
        if 定位 is not None and 'path' in 定位:#有路径键
            文本记录路径=定位['path']#路径或缺席（下游当 null）
        else:
            文本记录路径=None#显式 null
    return {#组装公共字段
        'session_id':会话号,#会话 id
        'transcript_path':文本记录路径,#文本记录路径或 null
        'cwd':工作目录,#工作目录
        'hook_event_name':事件,#钩子事件名
        'model':模型,#模型名
        'permission_mode':'default',#权限模式
    }#公共字段对象

def 轮次共用载荷(上下文,智能体,事件,模型):
    """公共字段加 turn_id，给轮次作用域事件（PreToolUse/PostToolUse/UserPromptSubmit/Stop）。"""
    载荷=共用载荷(上下文,智能体,事件,模型)#公共字段
    载荷['turn_id']=str(最后轮次(智能体))#加上当前打开轮次
    return 载荷#带轮次 id 的公共字段

def 命令参数(参数):
    """从工具调用的已解析参数 dict 里取出 command 字符串，否则 ''。"""
    if isinstance(参数,dict) and 'command' in 参数 and isinstance(参数['command'],str):#有 command 字符串
        return 参数['command']#命令串
    return ''#否则空串

def 工具前载荷(上下文,执行,模型):
    """PreToolUse 方言载荷；tool_name 与匹配主体一致，tool_input 保持 Codex 的 { command } 形状。执行是 dict。"""
    智能体=执行['agent'] if 'agent' in 执行 else None#智能体
    载荷=轮次共用载荷(上下文,智能体,'PreToolUse',模型)#带轮次公共字段
    载荷['tool_name']=执行['name']#真正的工具名
    载荷['tool_input']={'command':命令参数(执行['arguments'] if 'arguments' in 执行 else None)}#Codex shell 载荷形状
    载荷['tool_use_id']=执行['callId']#调用 id
    return 载荷#载荷

def 工具后载荷(上下文,执行,结果,模型):
    """PostToolUse 方言载荷；再加上工具响应文本。执行与结果都是 dict。"""
    智能体=执行['agent'] if 'agent' in 执行 else None#智能体
    载荷=轮次共用载荷(上下文,智能体,'PostToolUse',模型)#带轮次公共字段
    载荷['tool_name']=执行['name']#工具名
    载荷['tool_input']={'command':命令参数(执行['arguments'] if 'arguments' in 执行 else None)}#命令输入
    载荷['tool_use_id']=执行['callId']#调用 id
    载荷['tool_response']=拼接块文本(结果['content'] if 'content' in 结果 else None)#工具响应文本
    return 载荷#载荷

def 应用(上下文,配置值=None):
    """在 ctx 生命周期内登记 Codex 钩子桥监听器。读或解析失败只记日志，不登记任何钩子。配置值是 dict。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    if 'stderrSummaryMaxChars' in 配置值:#配置给了上限
        stderr摘要上限=配置值['stderrSummaryMaxChars']#摘要上限
    else:
        stderr摘要上限=默认stderr摘要最大字节#默认
    断言正整数('stderrSummaryMaxChars',stderr摘要上限)#上限必须是正整数
    if 'defaultTimeoutMs' in 配置值:#配置给了超时
        默认超时=配置值['defaultTimeoutMs']#默认超时
    else:
        默认超时=默认钩子超时毫秒#默认
    配置路径=配置值['configPath'] if 'configPath' in 配置值 else None#配置文件路径
    已解析={}#解析出的可跑配置
    try:
        with open(配置路径,'r',encoding='utf-8') as 文件:#同步读配置文件
            原始=json.loads(文件.read())#当 JSON
        解析结果=解析科德克斯配置(原始)#解析 Codex 配置
        已解析=解析结果['config']#留下可跑组
        for 跳过 in 解析结果['skipped']:#警告被跳过的钩子
            上下文.日志.警告('hooks-codex: skipping '+跳过['reason']+' on '+跳过['event']+' (only sync command hooks run)')#记录跳过
    except (OSError,json.JSONDecodeError,UnicodeDecodeError,SyntaxError,TypeError,ValueError) as 错误:
        上下文.日志.警告('hooks-codex: could not load hook config "'+str(配置路径)+'": '+str(错误)+' — no hooks registered')#记录加载失败
        return#不安装监听器
    if 'model' in 配置值 and 配置值['model'] is not None:#配置给了模型名
        模型=配置值['model']#载荷上的模型名
    else:
        模型=''#默认空串
    分离=创建分离运行()#分离运行跟踪器
    def 取得排空():
        """登记拆除时排空分离钩子运行。"""
        return 分离.排空#清理器即排空
    上下文.副作用(取得排空,'hooks-codex: drain detached hook runs')#拆除时排空分离运行

    def 执行钩子点(钩子点,匹配主体,载荷,选项):
        """跑并折合一个已配置的 Codex 钩子点。传入轮次时，在该未关闭轮次里记录钩子调用/结果对。分离生命周期点省略这对事件。选项是 dict。"""
        组列表=已解析[钩子点] if 钩子点 in 已解析 else []#该点的匹配组
        输出列表=[]#各条钩子的解码输出
        智能体=选项['agent'] if 'agent' in 选项 else None#可选智能体
        轮次=选项['turn'] if 'turn' in 选项 else None#可选轮次
        信号=选项['signal'] if 'signal' in 选项 else None#取消信号
        纯stdout当上下文=选项['plainStdoutAsContext'] is True if 'plainStdoutAsContext' in 选项 else False#干净纯 stdout 是否当作附加上下文
        工作目录=None#会话工作目录
        if 智能体 is not None:#有智能体才读会话头
            头=智能体.session.header#会话头
            if 'cwd' in 头:#有 cwd
                工作目录=头['cwd']#工作目录
        for 组 in 组列表:#逐个匹配组
            匹配器=组['matcher'] if 'matcher' in 组 else None#匹配模式
            if not 匹配命中(匹配器,匹配主体,'codex'):#Codex 始终把匹配器当正则；未命中则跳过
                continue#下一组
            for 钩子 in 组['hooks']:#逐条命令钩子
                处理器标识=下一条处理器标识(钩子点)#本条调用的稳定 id
                会话=智能体.session if 智能体 is not None else None#可选会话
                if 会话 is not None and 轮次 is not None:#有会话且在轮内才记调用事件
                    调用数据={#追加 hook/invoked
                        'turn':轮次,#轮次
                        'point':钩子点,#点
                        'dialect':'codex',#方言
                        'handlerId':处理器标识,#id
                    }#调用身份
                    if 匹配器 is not None:#有匹配模式才写入
                        调用数据['matcher']=匹配器#匹配器
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
                运行结果=执行钩子(上下文.shell,钩子,运行选项,取单调纳秒)#执行并计量
                输出=运行结果['output']#解码输出
                时长=运行结果['durationMs']#墙钟毫秒
                标准输出=输出['stdout'] if 'stdout' in 输出 else None#stdout 文本
                if (纯stdout当上下文 is True#允许纯 stdout 当上下文
                    and ('exitCode' in 输出 and 输出['exitCode']==0)#干净退出
                    and ('additionalContext' not in 输出 or 输出['additionalContext'] is None)#还没有结构化附加上下文
                    and isinstance(标准输出,str)#有 stdout
                    and len(标准输出)>0#非空
                    and not 标准输出.startswith('{')):#不像 JSON 对象
                    输出['additionalContext']=标准输出#把纯 stdout 当作附加上下文
                输出列表.append(输出)#收进待合并列表
                if 'systemMessage' in 输出 and 输出['systemMessage'] is not None:#发出了系统消息
                    上下文.日志.警告('hooks-codex: '+钩子点+' hook emitted a systemMessage, which is not yet surfaced (ignored)')#尚未展示，只警告
                if 会话 is not None and 轮次 is not None:#有会话且在轮内才记结果事件
                    追加钩子结果(会话,{#追加 hook/result
                        'turn':轮次,#轮次
                        'point':钩子点,#点
                        'handlerId':处理器标识,#id
                        'output':输出,#输出
                        'stderrSummaryMaxChars':stderr摘要上限,#摘要上限
                        'durationMs':时长,#时长
                    })#结果事件
        return 合并钩子输出(输出列表)#按最严格规则折合

    def 从合并取上下文(合并):
        """从钩子输出组装附加模型上下文；空则返回 None。合并是 dict。"""
        附加=合并['additionalContext'] if 'additionalContext' in 合并 else []#附加上下文列表
        if 附加 is None:#缺席
            return None#省略
        if len(附加)==0:#没有附加上下文
            return None#省略
        内容=[{'type':'text','text':文本} for 文本 in 附加]#每条做成文本块
        return 创建用户消息({'content':内容,'source':插件来源})#盖上本桥来源

    def 前置上下文(本桥,下游列表):
        """前置一条上下文，不压平来源字段或其他下游元数据。"""
        后列=下游列表 if 下游列表 is not None else []#缺席当空
        return [本桥]+list(后列)#本桥在前，下游原有在后

    def 智能体已创建监听(载荷,*位置参数):
        """智能体创建时跑 SessionStart 并等完。载荷是 dict。"""
        智能体=载荷['agent']#智能体
        来源=载荷['source']#会话来源
        创建信号=载荷['signal'] if 'signal' in 载荷 else None#创建边取消信号
        if 创建信号 is None:#没有创建信号
            拥有信号=分离.信号#只用拆除信号
        else:
            拥有信号=创建信号#创建信号与拆除信号任一取消
            if 分离.信号.is_set():#拆除已触发
                拥有信号.set()#一并取消
        def 任务():
            """跑 SessionStart 并注入。"""
            try:
                会话载荷=共用载荷(上下文,智能体,'SessionStart',模型)#公共字段
                会话载荷['source']=来源#加上来源
                合并=执行钩子点('SessionStart',来源,会话载荷,{#按来源匹配，纯 stdout 当上下文
                    'agent':智能体,#智能体
                    'plainStdoutAsContext':True,#纯 stdout 当上下文
                    'signal':拥有信号,#拥有取消信号
                })#跑 SessionStart
                上下文消息=从合并取上下文(合并)#折成用户消息
                if 上下文消息 is not None:#有上下文才注入
                    智能体.注入(上下文消息)#注入
            except Exception as 错误:
                上下文.日志.警告('hooks-codex: SessionStart hook failed: '+str(错误))#记录失败
        后台=操作任务()#本条创建边任务
        def 执行链():
            """执行并结算。"""
            try:
                任务()#执行
                后台.兑现(None)#成功
            except BaseException as 错误:
                后台.拒绝(错误)#拒绝
        threading.Thread(target=执行链,daemon=True).start()#启动
        分离.登记(后台)#纳入拆除排空
        后台.等待()#创建边等到跑完
    上下文.监听('agent/created',智能体已创建监听)#结束 created 监听

    def 预步骤监听(载荷,下一步,*位置参数):
        """UserPromptSubmit → PreStepDecision。Codex 支持拒绝，不支持改写或询问。载荷是 dict。"""
        消息列表=载荷['messages'] if 'messages' in 载荷 else []#步进消息
        if 消息列表 is None:#缺席
            消息列表=[]#空列表
        if len(消息列表)==0:#没有消息则直接委托
            return 下一步()#委托
        内容=[]#摊平全部内容块
        for 消息 in 消息列表:#逐条
            块列表=消息['content'] if 'content' in 消息 else []#内容块
            if 块列表 is None:#缺席
                块列表=[]#空
            内容.extend(list(块列表))#摊平
        智能体=载荷['agent'] if 'agent' in 载荷 else None#智能体
        提示载荷体=共用载荷(上下文,智能体,'UserPromptSubmit',模型)#公共字段
        提示载荷体['turn_id']=str(载荷['turn'] if 'turn' in 载荷 else None)#轮次 id
        提示载荷体['prompt']=拼接块文本(内容)#提示文本
        合并=执行钩子点('UserPromptSubmit','',提示载荷体,{#该事件无匹配主体
            'agent':智能体,#智能体
            'turn':载荷['turn'] if 'turn' in 载荷 else None,#轮次
            'plainStdoutAsContext':True,#纯 stdout 当上下文
            'signal':载荷['signal'] if 'signal' in 载荷 else None,#信号
        })#跑 UserPromptSubmit
        if 'decision' in 合并 and 合并['decision']=='deny':#拒绝则挡下这一步
            return {'kind':'reject'}#拒绝进入
        下游=下一步()#先委托后续监听器
        本桥=从合并取上下文(合并)#本桥上下文
        if 本桥 is None or 下游['kind']!='enter':#没有上下文或下游不是 enter
            return 下游#原样返回
        下游消息=下游['messages'] if 'messages' in 下游 else []#下游消息
        if 下游消息 is None:#缺席
            下游消息=[]#空
        return {#进入并带上本桥上下文
            'kind':'enter',#进入步进
            'messages':list(下游消息)+[本桥],#下游消息后面追加本桥上下文
        }#enter 判定
    上下文.监听('agent/pre-step',预步骤监听)#结束 pre-step 监听

    def 工具前监听(执行,下一步,*位置参数):
        """PreToolUse → PreToolDecision。Codex 只阻断（不兑现 allow/ask）。执行是 dict。"""
        智能体=执行['agent'] if 'agent' in 执行 else None#智能体
        轮次=最后轮次(智能体)#取当前打开轮次
        选项={'turn':轮次,'signal':执行['signal'] if 'signal' in 执行 else None}#运行选项
        if 智能体 is not None:#有智能体才传入
            选项['agent']=智能体#智能体
        合并=执行钩子点('PreToolUse',执行['name'],工具前载荷(上下文,执行,模型),选项)#按工具名匹配
        if 'decision' in 合并 and 合并['decision']=='deny':#拒绝则否认
            原因=合并['reason'] if 'reason' in 合并 and 合并['reason'] is not None and 合并['reason']!='' else '已被 PreToolUse 钩子阻断'#空串原因回落默认（原 ||）
            return {'kind':'deny','reason':原因}#否认
        return 下一步()#否则委托后续
    上下文.监听('tools/pre-execute',工具前监听)#结束 pre-execute 监听

    def 工具后监听(执行,结果,下一步,*位置参数):
        """PostToolUse → PostToolDecision（带反馈阻断，或附上上下文）。执行与结果都是 dict。"""
        智能体=执行['agent'] if 'agent' in 执行 else None#智能体
        轮次=最后轮次(智能体)#取当前打开轮次
        选项={'turn':轮次,'signal':执行['signal'] if 'signal' in 执行 else None}#运行选项
        if 智能体 is not None:#有智能体才传入
            选项['agent']=智能体#智能体
        合并=执行钩子点('PostToolUse',执行['name'],工具后载荷(上下文,执行,结果,模型),选项)#按工具名匹配
        上下文消息=从合并取上下文(合并)#附加上下文
        if 'decision' in 合并 and 合并['decision']=='deny':#拒绝则阻断工具结果
            原因=合并['reason'] if 'reason' in 合并 and 合并['reason'] is not None and 合并['reason']!='' else '已被 PostToolUse 钩子阻断'#空串原因回落默认（原 ||）
            判定={#阻断
                'kind':'block',#阻断
                'feedback':[{'type':'text','text':原因}],#反馈
            }#阻断判定
            if 上下文消息 is not None:#可选带上下文
                判定['additionalContexts']=[上下文消息]#附加上下文
            return 判定#阻断
        下游=下一步()#先委托后续监听器
        if 上下文消息 is None:#没有上下文则原样返回
            return 下游#原样
        下游上下文=下游['additionalContexts'] if 'additionalContexts' in 下游 else None#下游附加
        合并下游=dict(下游)#拷贝
        合并下游['additionalContexts']=前置上下文(上下文消息,下游上下文)#把本桥上下文前置进去
        return 合并下游#带上下文的下游判定
    上下文.监听('tools/post-execute',工具后监听)#结束 post-execute 监听

    def 轮次将停监听(载荷,*位置参数):
        """阻断型 Stop 钩子在停止边界转向，让状态机看到待处理输入再跑一步。载荷是 dict。"""
        智能体=载荷['agent']#智能体
        停止载荷体=轮次共用载荷(上下文,智能体,'Stop',模型)#带轮次公共字段
        停止载荷体['stop_hook_active']=False#循环守卫标志恒为假
        停止载荷体['last_assistant_message']=None#恒为 null
        合并=执行钩子点('Stop','',停止载荷体,{#该事件无匹配主体
            'agent':智能体,#智能体
            'turn':载荷['turn'] if 'turn' in 载荷 else None,#轮次
            'signal':载荷['signal'] if 'signal' in 载荷 else None,#信号
        })#跑 Stop
        if 'decision' in 合并 and 合并['decision']=='deny':#阻断型 Stop 强迫续跑
            文本=合并['reason'] if 'reason' in 合并 and 合并['reason'] is not None and 合并['reason']!='' else 'continue: 已被 Stop 钩子阻断'#空串原因回落默认（原 ||）
            智能体.转向(创建用户消息({'content':[{'type':'text','text':文本}],'source':插件来源}))#注入转向消息
    上下文.监听('agent/turn-stopping',轮次将停监听)#结束 turn-stopping 监听

__all__=['名称','依赖','应用','配置','钩子codex错误']#仅中文公开名
name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
