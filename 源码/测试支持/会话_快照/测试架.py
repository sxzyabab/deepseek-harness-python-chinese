"""ACP 快照套件共享子进程 harness。

对齐上游 `session-snapshot/src/harness.ts`。公开面仅中文名。
同步 + threading 轮询等待；无 asyncio。
"""
import hashlib,json,os,shutil,tempfile,time,threading#哈希、JSON、文件、临时与轮询
from .启动器 import 启动ACP测试智能体#启动器
from .工作区 import 捕获工作区快照#工作区快照

#上游 @deepseek-ai/dsh-http-proxy；包尚未迁完时内联
代理环境名=('http_proxy','HTTP_PROXY','https_proxy','HTTPS_PROXY','no_proxy','NO_PROXY','all_proxy','ALL_PROXY')

__all__=['快照溢出根','运行场景']#仅中文公开名

默认等待超时毫秒=10_000#默认等待超时
轮询间隔毫秒=10#轮询间隔
Error=Exception#错误别名

def 清代理环境():#清代理名
    """返回把全部代理环境名置为 None 的覆盖表。"""
    return {名:None for 名 in 代理环境名}#清代理

def 等待直到(谓词,超时毫秒=默认等待超时毫秒,间隔毫秒=轮询间隔毫秒):#轮询等待
    """对齐 vi.waitFor：超时前反复调用谓词直至不抛。"""
    截止=time.monotonic()+超时毫秒/1000#截止
    末次=None#末次错误
    while time.monotonic()<截止:#轮询
        try:#尝试
            谓词()#调用
            return#成功
        except Exception as 错误:#尚未
            末次=错误#记下
            time.sleep(间隔毫秒/1000)#间隔
    raise 末次 or Error('wait timed out')#超时

def 快照溢出根(夹具文件,平台=None):#溢出根
    """推导本场景拥有的一个稳定定长溢出根。"""
    if 平台 is None:#缺省
        平台=os.name#平台
    场景=os.path.basename(os.path.dirname(夹具文件))#场景名
    键=hashlib.sha256(场景.encode('utf-8')).hexdigest()[:9]#哈希键
    根='/t' if 平台=='nt' else '/tmp'#临时根
    return f'{根}/dsh-acp-snap-{键}'#溢出目录

def 收获会话日志(根):#收获会话日志
    """收获会话根下每个持久化 session.jsonl，主优先。"""
    日志们=[]#日志
    if not os.path.isdir(根):#无根
        return 日志们#空
    for 目录,子目录,文件们 in os.walk(根):#递归
        for 文件 in 文件们:#逐文件
            if 文件!='session.jsonl':#非会话
                continue#跳过
            路径=os.path.join(目录,文件)#路径
            with open(路径,'r',encoding='utf-8') as 句柄:#读
                内容=句柄.read()#内容
            首行=next((行 for 行 in 内容.split('\n') if 行.strip()!=''),'{}')#首行
            头=json.loads(首行)#头
            项={'id':头['id'] if isinstance(头.get('id'),str) else '','createdAt':头['createdAt'] if isinstance(头.get('createdAt'),(int,float)) else 0,'content':内容}#项
            if isinstance(头.get('parentSession'),str):#父会话
                项['parentSession']=头['parentSession']#写入
            日志们.append(项)#追加
    日志们.sort(key=lambda 项:(0 if 'parentSession' not in 项 else 1,项['createdAt'],项['id']))#主优先
    return 日志们#返回

def 最新回合已关闭(内容):#最新回合是否关闭
    """最新完整原始 JSONL 回合边界是否关闭。"""
    完整=内容[:内容.rfind('\n')+1] if '\n' in 内容 else 内容#完整前缀
    return 完整.rfind('\n{"type":"turn/end",')>完整.rfind('\n{"type":"turn/start",')#关闭晚于开始

def 最新标题跟在回合结束后(内容):#标题是否跟在回合结束后
    """最新完整标题是否出现在最新完整回合结束之后。"""
    完整=内容[:内容.rfind('\n')+1] if '\n' in 内容 else 内容#完整前缀
    回合结束=完整.rfind('\n{"type":"turn/end",')#回合结束
    return 回合结束>=0 and 完整.rfind('\n{"type":"session/title",')>回合结束#标题更晚

def 最新事件跟在回合结束后(内容,类型):#事件是否跟在回合结束后
    """type 的完整记录是否出现在最新完整回合结束之后。"""
    完整=内容[:内容.rfind('\n')+1] if '\n' in 内容 else 内容#完整前缀
    回合结束=完整.rfind('\n{"type":"turn/end",')#回合结束
    return 回合结束>=0 and 完整.rfind(f'\n{{"type":"{类型}",')>回合结束#事件更晚

def 最新打开回合(内容):#最新打开回合号
    """返回最新打开回合号。"""
    完整=内容[:内容.rfind('\n')+1] if '\n' in 内容 else 内容#完整前缀
    开始=完整.rfind('\n{"type":"turn/start",')#开始
    if 开始<=完整.rfind('\n{"type":"turn/end",'):#已关闭
        return None#无打开
    结束=完整.find('\n',开始+1)#行结束
    记录=json.loads(完整[开始+1:结束 if 结束>=0 else None])#记录
    回合=(记录.get('data') or {}).get('turn')#回合
    if not isinstance(回合,int) or isinstance(回合,bool) or 回合<1:#非法
        raise Error('snapshot-harness: invalid persisted turn/start record')#非法
    return 回合#返回

def 有关闭回合(内容,回合):#是否含关闭回合
    """原始会话日志是否含请求的关闭回合。"""
    for 行 in 内容.split('\n'):#逐行
        if not 行:#空
            continue#跳过
        事件=json.loads(行)#解析
        if 事件.get('type')=='turn/end' and (事件.get('data') or {}).get('turn')==回合:#命中
            return True#有
    return False#无

def 描述符后有请求头(内容):#描述符后是否有请求头
    """子日志是否在自有描述符事件后含模型工作。"""
    行们=[行 for 行 in 内容.split('\n') if 行]#非空行
    事件们=[json.loads(行) for 行 in 行们]#事件
    描述符=-1#索引
    for 索引,事件 in enumerate(事件们):#查找
        if 事件.get('type')=='subagent/descriptor':#描述符
            描述符=索引#记下
    return 描述符>=0 and any(事件.get('type')=='request/header' for 事件 in 事件们[描述符+1:])#其后有头

def 运行步骤(客户端,步骤,工作目录,等更新,取会话标识,设会话标识,等回合开始,等回合结束,等子回合结束,等目标阶段,等收件箱,等标题,等事件后):#驱动一步
    """经客户端连接驱动一步输入。"""
    操作=步骤.get('op')#操作
    if 操作=='initialize':#初始化
        客户端['initialize']({'protocolVersion':1,'clientCapabilities':{}})#初始化
        return#结束
    if 操作=='newSession':#新建会话
        结果=客户端['newSession']({'cwd':工作目录,'mcpServers':[]})#新建
        设会话标识(结果['sessionId'])#记下
        return#结束
    if 操作=='newSessionExpectError':#期望错误
        try:#应拒绝
            参数={'cwd':工作目录,'mcpServers':[]}#参数
            if 'additionalDirectories' in 步骤:#附加目录
                参数['additionalDirectories']=步骤['additionalDirectories']#写入
            客户端['newSession'](参数)#新建
            raise Error('snapshot-harness: expected session/new to be rejected but it succeeded')#意外成功
        except Error:#期望拒绝
            if 'expected session/new' in str(sys_exc()):#意外成功再抛
                raise#再抛
            return#期望拒绝
    if 操作=='prompt':#提示
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: prompt before newSession')#未建
        客户端['prompt']({'sessionId':标识,'prompt':[{'type':'text','text':步骤['text']}]})#提示
        return#结束
    if 操作=='promptContent':#内容块提示
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: promptContent before newSession')#未建
        客户端['prompt']({'sessionId':标识,'prompt':步骤['content']})#提示
        return#结束
    if 操作=='promptAndWaitForAgentMessage':#提示并等助手
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: promptAndWaitForAgentMessage before newSession')#未建
        等待文本=步骤['waitForText']#等待文本
        def 匹配(更新):#匹配更新
            """精确文本块。"""
            return 更新.get('sessionUpdate')=='agent_message_chunk' and 更新.get('content',{}).get('type')=='text' and 更新.get('content',{}).get('text')==等待文本#匹配
        完成=threading.Thread(target=lambda:等更新(匹配),daemon=True)#武装等待
        完成.start()#启动
        客户端['prompt']({'sessionId':标识,'prompt':[{'type':'text','text':步骤['text']}]})#提示
        完成.join()#等更新
        return#结束
    if 操作=='promptExpectError':#提示期望错误
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: promptExpectError before newSession')#未建
        try:#应失败
            客户端['prompt']({'sessionId':标识,'prompt':[{'type':'text','text':步骤['text']}]})#提示
            raise Error('snapshot-harness: expected the prompt to fail but it succeeded')#意外成功
        except Error:#期望失败
            if 'expected the prompt' in str(sys_exc()):#意外
                raise#再抛
            return#期望
    if 操作=='promptAndCancel':#提示并取消
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: promptAndCancel before newSession')#未建
        结果盒={}#结果
        def 派发():#后台提示
            """不阻塞取消路径。"""
            try:#提示
                结果盒['ok']=客户端['prompt']({'sessionId':标识,'prompt':[{'type':'text','text':步骤['text']}]})#提示
            except Exception as 错误:#失败
                结果盒['error']=错误#记下
        线程=threading.Thread(target=派发,daemon=True)#线程
        线程.start()#启动
        if 步骤.get('waitForFile') is not None:#等文件
            等待工作区文件(工作目录,步骤['waitForFile']['path'],步骤['waitForFile'].get('timeoutMs'))#等文件
        else:#等回合开始
            等回合开始(标识)#等回合开始
        客户端['cancel']({'sessionId':标识})#取消
        线程.join()#等提示结算
        return#结束
    if 操作=='waitForFile':#等文件
        等待工作区文件(工作目录,步骤['path'],步骤.get('timeoutMs'))#等文件
        return#结束
    if 操作=='waitForTurnEnd':#等回合结束
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: waitForTurnEnd before newSession')#未建
        等回合结束(标识,步骤.get('timeoutMs'))#等
        return#结束
    if 操作=='waitForSubagentTurnEnd':#等子回合结束
        等子回合结束(步骤.get('child') or 1,步骤.get('timeoutMs'),步骤.get('minimumTurn'))#等
        return#结束
    if 操作=='waitForGoalPhase':#等目标阶段
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: waitForGoalPhase before newSession')#未建
        等目标阶段(标识,步骤['phase'],步骤.get('timeoutMs'))#等
        return#结束
    if 操作=='waitForInboxMessage':#等收件箱
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: waitForInboxMessage before newSession')#未建
        等收件箱(标识,步骤['text'],步骤.get('timeoutMs'))#等
        return#结束
    if 操作=='waitForTitleAfterTurnEnd':#等标题
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: waitForTitleAfterTurnEnd before newSession')#未建
        等标题(标识,步骤.get('timeoutMs'))#等
        return#结束
    if 操作=='waitForEventAfterTurnEnd':#等事件
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: waitForEventAfterTurnEnd before newSession')#未建
        等事件后(标识,步骤['type'],步骤.get('timeoutMs'))#等
        return#结束
    if 操作=='waitForTurnStart':#等回合开始
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: waitForTurnStart before newSession')#未建
        等回合开始(标识,步骤.get('timeoutMs'),步骤.get('minimumTurn'))#等
        return#结束
    if 操作=='cancel':#取消
        标识=取会话标识()#会话
        if 标识 is None:#未建
            raise Error('snapshot-harness: cancel before newSession')#未建
        if 步骤.get('waitForFile') is not None:#等文件
            等待工作区文件(工作目录,步骤['waitForFile']['path'],步骤['waitForFile'].get('timeoutMs'))#等
        客户端['cancel']({'sessionId':标识})#取消
        return#结束
    raise Error(f'snapshot-harness: unknown input op {步骤!r}')#未知操作

def sys_exc():#取当前异常
    """返回当前异常实例。"""
    return __import__('sys').exc_info()[1]#当前异常

def 等待工作区文件(工作目录,路径,超时毫秒=None):#等 cwd 相对标记
    """等待证明外部动作到达就绪的 cwd 相对标记。"""
    if 超时毫秒 is None:#缺省
        超时毫秒=默认等待超时毫秒#默认
    目标=os.path.join(工作目录,路径)#目标
    def 检查():#检查存在
        """文件必须出现。"""
        if not os.path.exists(目标):#未出现
            raise Error(f'snapshot-harness: workspace file "{路径}" did not appear within {超时毫秒}ms')#未出现
    等待直到(检查,超时毫秒)#等待

def 运行场景(输入,选项):#运行场景
    """对新鲜 spawn 的子进程端到端运行场景。"""
    父=选项.get('workspaceParent') or tempfile.gettempdir()#父目录
    工作目录=tempfile.mkdtemp(prefix='acp-snap-cwd-',dir=父)#生成 cwd
    别名=list({os.path.realpath(工作目录)})#cwd 别名
    会话根=tempfile.mkdtemp(prefix='acp-snap-sessions-')#会话根
    溢出根=快照溢出根(选项['fixtureFile'])#溢出根
    已启动=None#已启动
    会话标识=None#会话 id
    会话日志=[]#会话日志
    结果=None#结果
    失败=None#失败
    try:#主路径
        if 选项.get('workspaceDir') and os.path.exists(选项['workspaceDir']):#播种工作区
            for 名 in os.listdir(选项['workspaceDir']):#拷贝
                源=os.path.join(选项['workspaceDir'],名)#源
                目标=os.path.join(工作目录,名)#目标
                if os.path.isdir(源):#目录
                    shutil.copytree(源,目标)#递归拷
                else:#文件
                    shutil.copy2(源,目标)#拷文件
        准备=选项.get('prepareWorkspace')#准备
        if 准备 is not None:#有准备
            准备(工作目录)#运行
        忽略根=['.agents','.dsh','.dsh-profile-patches','.dsh-snapshot-stream-ready']#忽略根
        初始工作区=捕获工作区快照(工作目录,{'ignoredRootEntries':忽略根})#初始
        环境={#环境
            **(选项.get('env') or {}),#场景环境
            **清代理环境(),#清代理
            'DSH_SNAPSHOT':选项['mode'],#模式
            'DSH_SNAPSHOT_FILE':选项['fixtureFile'],#fixture
            'DSH_SNAPSHOT_SESSIONS_ROOT':会话根,#会话根
            'DSH_SNAPSHOT_SPILL_ROOT':溢出根,#溢出根
            'DSH_HOME':os.path.join(工作目录,'.dsh'),#home
            'DSH_AGENTS_HOME':os.path.join(工作目录,'.agents'),#agents
        }#环境结束
        if 选项.get('overrideFile'):#覆盖
            环境['DSH_SNAPSHOT_OVERRIDE']=选项['overrideFile']#写入
        if 选项.get('childFiles'):#子文件
            环境['DSH_SNAPSHOT_CHILD_FILES']=os.pathsep.join(选项['childFiles'])#写入
        权限队列=list(输入.get('permissionAnswers') or [])#权限队列
        脚本错误=[None]#脚本错误
        def 请求权限(参数):#权限回调
            """FIFO 消费权限答案。"""
            if not 权限队列:#耗尽
                return {'outcome':{'outcome':'cancelled'}}#取消
            答案=权限队列.pop(0)#取答案
            选项们=参数.get('options') or []#选项
            命中=next((项 for 项 in 选项们 if 项.get('kind')==答案.get('kind')),None)#按 kind
            if 命中 is None:#脚本 bug
                脚本错误[0]=Error(#捕获
                    f"snapshot-harness: scripted permission answer {答案.get('kind')} not among "
                    +f"the offered options [{', '.join(项.get('kind','') for 项 in 选项们)}]",
                )#脚本 bug
                return {'outcome':{'outcome':'cancelled'}}#取消
            return {'outcome':{'outcome':'selected','optionId':命中.get('optionId')}}#选中
        启动选项={'agent':选项['agent'],'cwd':工作目录,'env':环境,'requestPermission':请求权限}#启动选项
        if 选项.get('configPath'):#覆盖配置
            启动选项['configPath']=选项['configPath']#写入
        已启动=启动ACP测试智能体(启动选项)#启动
        客户端=已启动['client']#客户端
        def 设标识(标识):#设会话 id
            """写入会话标识。"""
            nonlocal 会话标识#可变
            会话标识=标识#写入
        def 等回合开始(标识,超时=None,最小=None):#等回合开始
            """等待持久化打开回合。"""
            def 检查():#检查
                """打开回合就绪。"""
                日志=next((项 for 项 in 收获会话日志(会话根) if 项['id']==标识),None)#日志
                打开=None if 日志 is None else 最新打开回合(日志['content'])#打开回合
                if 打开 is None or (最小 is not None and 打开<最小):#未就绪
                    细节='turn/start' if 最小 is None else f'turn/start at or beyond turn {最小}'#细节
                    raise Error(f'snapshot-harness: session "{标识}" did not persist {细节} within {超时 or 默认等待超时毫秒}ms')#未就绪
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        def 等回合结束(标识,超时=None):#等回合结束
            """等待关闭回合。"""
            def 检查():#检查
                """关闭回合就绪。"""
                日志=next((项 for 项 in 收获会话日志(会话根) if 项['id']==标识),None)#日志
                if 日志 is None or not 最新回合已关闭(日志['content']):#未关闭
                    raise Error(f'snapshot-harness: session "{标识}" did not persist turn/end within {超时 or 默认等待超时毫秒}ms')#未关闭
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        def 等子回合结束(子,超时=None,最小=1):#等子回合结束
            """等待第 N 个子会话关闭回合。"""
            def 检查():#检查
                """子回合关闭。"""
                日志们=收获会话日志(会话根)#日志
                日志=日志们[子] if 子<len(日志们) else None#子日志
                if 日志 is None or not 最新回合已关闭(日志['content']) or not 描述符后有请求头(日志['content']) or not 有关闭回合(日志['content'],最小 or 1):#未就绪
                    raise Error(f'snapshot-harness: subagent child #{子} did not persist closed turn {最小 or 1} within {超时 or 默认等待超时毫秒}ms')#未就绪
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        def 等目标阶段(标识,阶段,超时=None):#等目标阶段
            """等待目标阶段。"""
            def 检查():#检查
                """阶段到达。"""
                内容=next((项['content'] for 项 in 收获会话日志(会话根) if 项['id']==标识),None)#内容
                命中=False#命中
                if 内容:#有内容
                    for 行 in 内容.split('\n'):#逐行
                        if not 行:#空
                            continue#跳过
                        事件=json.loads(行)#解析
                        if 事件.get('type')=='goal/change' and ((事件.get('data') or {}).get('goal') or {}).get('phase')==阶段:#命中
                            命中=True#命中
                            break#停
                if not 命中:#未命中
                    raise Error(f'snapshot-harness: session "{标识}" did not persist goal phase "{阶段}" within {超时 or 默认等待超时毫秒}ms')#未命中
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        def 等收件箱(标识,文本,超时=None):#等收件箱
            """等待收件箱文本。"""
            def 检查():#检查
                """收件箱含文本。"""
                日志=next((项 for 项 in 收获会话日志(会话根) if 项['id']==标识),None)#日志
                命中=False#命中
                if 日志:#有日志
                    for 行 in 日志['content'].split('\n'):#逐行
                        if not 行:#空
                            continue#跳过
                        记录=json.loads(行)#解析
                        if 记录.get('type')!='agent/inbox/spliced':#非拼接
                            continue#跳过
                        for 消息 in (记录.get('data') or {}).get('inserted') or []:#插入
                            for 块 in 消息.get('content') or []:#块
                                if 块.get('type')=='text' and isinstance(块.get('text'),str) and 文本 in 块['text']:#命中
                                    命中=True#命中
                if not 命中:#未命中
                    raise Error(f'snapshot-harness: session "{标识}" did not persist expected inbox message within {超时 or 默认等待超时毫秒}ms')#未命中
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        def 等标题(标识,超时=None):#等标题
            """等待标题跟在回合结束后。"""
            def 检查():#检查
                """标题就绪。"""
                日志=next((项 for 项 in 收获会话日志(会话根) if 项['id']==标识),None)#日志
                if 日志 is None or not 最新标题跟在回合结束后(日志['content']):#未就绪
                    raise Error(f'snapshot-harness: session "{标识}" did not persist session/title after turn/end within {超时 or 默认等待超时毫秒}ms')#未就绪
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        def 等事件后(标识,类型,超时=None):#等事件后
            """等待事件跟在回合结束后。"""
            def 检查():#检查
                """事件就绪。"""
                日志=next((项 for 项 in 收获会话日志(会话根) if 项['id']==标识),None)#日志
                if 日志 is None or not 最新事件跟在回合结束后(日志['content'],类型):#未就绪
                    raise Error(f'snapshot-harness: session "{标识}" did not persist {类型} after turn/end within {超时 or 默认等待超时毫秒}ms')#未就绪
            等待直到(检查,超时 or 默认等待超时毫秒)#等待
        for 步骤 in 输入.get('steps') or []:#逐步
            运行步骤(#驱动一步
                客户端,步骤,工作目录,已启动['waitForUpdate'],
                lambda:会话标识,设标识,等回合开始,等回合结束,等子回合结束,等目标阶段,等收件箱,等标题,等事件后,
            )#步骤结束
            if 脚本错误[0] is not None:#脚本 bug
                raise 脚本错误[0]#失败
        已启动['close']()#关闭
        会话日志=收获会话日志(会话根)#收获
        最终工作区=捕获工作区快照(工作目录,{'ignoredRootEntries':忽略根})#最终
        结果={#结果
            'rawStdout':已启动['rawStdout'](),#stdout
            'stderr':已启动['stderr'](),#stderr
            'cwd':工作目录,#cwd
            'cwdAliases':别名,#别名
            'initialWorkspace':初始工作区,#初始
            'finalWorkspace':最终工作区,#最终
            'sessionLogs':会话日志,#日志
        }#结果结束
        if 会话标识 is not None:#有会话
            结果['sessionId']=会话标识#写入
    except Exception as 错误:#失败
        标准错=已启动['stderr']() if 已启动 else ''#stderr
        失败=Error(f'snapshot-harness: scenario failed: {错误}\nagent stderr:\n{标准错}') if 标准错 else 错误#包装
    finally:#清理
        if 已启动 is not None:#有进程
            try:#杀
                已启动['close']('SIGKILL')#强制
            except Exception:#忽略
                pass#忽略
        for 路径 in (工作目录,会话根,溢出根):#清理路径
            shutil.rmtree(路径,ignore_errors=True)#移除
    if 失败 is not None:#失败
        raise 失败#再抛
    return 结果#返回

runScenario=运行场景#上游名
snapshotSpillRoot=快照溢出根#上游名
