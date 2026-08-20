"""无服务器的独立 UI 开发假宿主。

对齐上游 `connection/src/client/fixture.ts` 的 FixtureApiClient / createFixtureFaces /
createFixtureWorld 主体。样本常量与甲日志来自 `.夹具样本` / `.夹具历史`。
真实约定：一元调用吃 RpcRequest、回 RpcResponse（回显 rpcId）；流产出自造帧 rpcId；
根 respond 吃 ClientResponse、回 RpcReceipt。公开面仅中文名；协议键保持英文。
"""
import functools,re,threading,time#偏函数、切片、定时器、延迟
from urllib.parse import parse_qs#读查询
from .接口 import 抽象接口客户端,Rpc标识,会话搜索结果上限#抽象客户端、rpcId、检索上限
from .随机uuid import 随机uuid#造 uuid
from .夹具历史 import 造文本块,造用户消息,造助手消息,构造甲日志#消息工厂与甲日志
from .夹具样本 import (#样本与投影/检索
    markdown样本,夹具图像数据,夹具图像引用,夹具模型分组,夹具用量,
    权限预设表,视图为,折计划,折表面,权限选择于,投影值于,投影帧于,分页于,
    日志引用附件,检索事件文本,检索令牌跨度,短语匹配,检索摘录,比较检索候选,
    回扫目标,最近请求上下文,
)#结束样本导入

__all__=[#仅中文公开名与上游别名
    '夹具接口客户端',
    '创建夹具双面',
    '创建夹具接口',
    'FixtureApiClient',
    'createFixtureFaces',
    'createFixtureApi',
]#公开面结束

def 造rpc请求(载荷):#自造一元请求
    """假载体像真载体一样自造 rpcId。"""
    return {'rpcId':Rpc标识(随机uuid()),'payload':载荷}#新 id + 原载荷

def 会话标识(字面):#品牌断言 SessionId
    """把字面量标成会话 id。"""
    return 字面#fixture 自造 id

def 工作区标识(字面):#品牌断言 WorkspaceId
    """把字面量标成工作区 id。"""
    return 字面#fixture 自造 id

def 取已中止(信号):#读 aborted
    """映射或对象。"""
    if 信号 is None:#无
        return False#未
    if isinstance(信号,dict):#映射
        return bool(信号.get('aborted'))#旗
    return bool(getattr(信号,'aborted',False))#属性

def 挂中止(信号,回调):#登记 abort 监听
    """有 addEventListener 则挂；否则无操作。"""
    if 信号 is None:#无
        return#完
    函=getattr(信号,'addEventListener',None)#可能有
    if callable(函):#事件面
        函('abort',回调)#挂一次语义由调用方保证

def 摘中止(信号,回调):#摘 abort 监听
    """有 removeEventListener 则摘。"""
    if 信号 is None:#无
        return#完
    函=getattr(信号,'removeEventListener',None)#可能有
    if callable(函):#事件面
        函('abort',回调)#摘

def 面对象(**方法们):#造属性面
    """把可调用表挂成属性对象。"""
    return type('夹具面',(),方法们)()#匿名面

class 夹具收件箱:#内存收件箱（FrameQueue 模式）
    """一流连接：push 入队；drain 吐帧直至 abort/breakNow。"""

    def __init__(自身):#空箱
        """初始化待吐信封。"""
        自身._收件箱=[]#待吐信封
        自身._打断=False#已被 breakNow

    def push(自身,信封):#入队
        """推一帧。"""
        自身._收件箱.append(信封)#收下

    def breakNow(自身):#强制结束
        """模拟断连。"""
        自身._打断=True#标记

    def 仍活(自身,信号):#活着？
        """breakNow/abort 会跨 yield 翻转，不得粘住循环条件。"""
        return not 取已中止(信号) and not 自身._打断#两边都未结束

    def drain(自身,信号):#抽出收件箱
        """同步生成器：吐帧直至 abort 或 breakNow。"""
        def 唤醒(_事件=None):#abort 也唤醒轮询
            """空操作：轮询侧会再读旗。"""
            return None#无
        挂中止(信号,唤醒)#循环外只挂一次
        try:#泵到死
            while 自身.仍活(信号):#仍活
                while 自身._收件箱:#抽干
                    yield 自身._收件箱.pop(0)#交出队头
                if not 自身.仍活(信号):#抽完后再看
                    break#停
                time.sleep(0.01)#等下一推或打断
        finally:#无论因何退出
            摘中止(信号,唤醒)#摘监听

def 自定位读夹具选项():#读 URL 分支
    """浏览器查询映射；非浏览器则空。"""
    try:#取 location
        import builtins#全局
        页面=getattr(builtins,'location',None)#可能缺
    except Exception:#无
        页面=None#无
    if 页面 is None:#非浏览器
        return {}#空选项
    查询=getattr(页面,'search','') or ''#查询串
    if 查询.startswith('?'):#带问号
        查询=查询[1:]#去掉
    参数=parse_qs(查询)#解析
    def 取一(键):#单值
        """取首个查询值。"""
        值们=参数.get(键) or []#列表
        return 值们[0] if 值们 else None#首或无
    帧序=取一('fixtureFrames')#帧序开关
    return {#各开关
        'empty':取一('fixture')=='empty',#空图
        'rejectPrompt':取一('fixturePrompt')=='reject',#拒 prompt
        'failWorkspaceAttach':取一('fixtureAttach')=='fail',#挂接失败
        'dropSessionCreateResponse':取一('fixtureSessionCreate')=='drop-response',#丢响应
        'createFrameOrder':'workspace-first' if 帧序=='workspace-first' else 'session-first',#帧序
    }#结束返回

def 创建夹具接口(选项=None):#只取旧 API 面
    """丢 rpc 面。"""
    return 造夹具世界(选项 or {}).api#旧面

def 创建夹具双面(选项=None):#双面入口
    """造两张 fixture 面，同一内存状态图。"""
    return 造夹具世界(选项 or {})#同一世界

createFixtureApi=创建夹具接口#上游名
createFixtureFaces=创建夹具双面#上游名

def 造夹具世界(选项):#内存假宿主
    """fx-alpha 带历史与回放；fx-beta 是子会话。返回 {api, rpc}。"""
    空图=bool(选项.get('empty'))#空图分支
    拒提示=bool(选项.get('rejectPrompt'))#拒 prompt
    挂接失败=bool(选项.get('failWorkspaceAttach'))#挂接失败
    丢创建响应=bool(选项.get('dropSessionCreateResponse'))#丢响应
    帧序=选项.get('createFrameOrder') or 'session-first'#帧序
    此刻=time.time()*1000#毫秒墙钟
    会话们=[] if 空图 else [#三会话或空
        {'sessionId':会话标识('fx-alpha'),'updatedAt':此刻,'running':True,'blank':False,'cwd':'/tmp/fixture'},#主会话
        {'sessionId':会话标识('fx-beta'),'updatedAt':此刻-60_000,'running':False,'blank':False,'parentSessionId':会话标识('fx-alpha'),'cwd':'/tmp/fixture'},#子会话
        {'sessionId':会话标识('fx-gamma'),'updatedAt':此刻-120_000,'running':False,'blank':False,'cwd':'/tmp/fixture'},#心跳翻转
    ]#结束会话们
    日志图={会话标识('fx-alpha'):构造甲日志()} if not 空图 else {}#仅 alpha 预填
    模型选择={会话['sessionId']:{'provider':'deepseek-official','model':'deepseek-v4-flash'} for 会话 in 会话们}#每会话默认
    附件图={str(夹具图像引用['attachmentId']):{'attachment':dict(夹具图像引用),'data':夹具图像数据}}#样本图
    凭证图={'DEEPSEEK_API_KEY':True}#已配置集合
    预设图={#三份预设
        'standard':{'trust':'system','content':"- id: tool-bash\n  name: '@deepseek-ai/dsh-tool-bash'\n"},
        'minimal':{'trust':'system','content':"- id: tool-web-search\n  name: '@deepseek-ai/dsh-tool-web-search'\n"},
        'my-agent':{'trust':'user','content':"- id: tool-read\n  name: '@deepseek-ai/dsh-tool-read'\n"},
    }#结束预设图
    默认预设=['standard']#可变盒：默认预设 id
    下一轮={会话标识('fx-alpha'):75}#alpha 下一轮从 75
    下一会话=[1]#自造会话序号
    下一rpc=[1]#自造 rpcId 序号
    已挂接=[0 if 空图 else 1]#describe 用的已挂接计数
    纪元=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime(time.time()-300))#固定创建/更新
    工作区们=[] if 空图 else [{#单工作区或空
        'workspaceId':工作区标识('fx-ws-fixture'),
        'path':'/tmp/fixture','title':'fixture',
        'sessionIds':[会话标识('fx-alpha'),会话标识('fx-beta'),会话标识('fx-gamma')],
        'createdAt':纪元,'updatedAt':纪元,
    }]#结束工作区们
    下一工作区=[1]#自造工作区序号
    已归档=[]#归档 id
    夹具家='/home/fixture'#家
    目录树={#显式子名
        '/':['home'],'/home':['fixture'],
        夹具家:['Documents','Downloads','.config'],
        f'{夹具家}/Documents':[
            'project','deepseek-iOS','deepseek-android','deepseek-platform',
            'deepseek-web','deepseek-harness','deepseek-app','deepseek-landing-blog',
        ],
    }#结束目录树

    def 列子(路径):#列子；未知为 None
        """父认得则空叶，否则不存在。"""
        if 路径 in 目录树:#已物化
            return list(目录树[路径])#拷贝
        斜=路径.rfind('/')#末斜杠
        父='/' if 斜<=0 else 路径[:斜] or '/'#父路径
        名=路径[斜+1:]#末段
        父们=目录树.get(父)#父节点
        return [] if 父们 is not None and 名 in 父们 else None#空叶或无

    def 面包屑(路径):#面包屑
        """根起累计路径。"""
        屑=[{'name':'/','path':'/','hidden':False}]#根
        累计=''#累计
        for 段 in [部 for 部 in 路径.split('/') if 部]:#非空段
            累计+=f'/{段}'#往下
            屑.append({'name':段,'path':累计,'hidden':False})#一段
        return 屑#整条

    def 铸造rpc():#自造帧 rpcId
        """稳定序号。"""
        号=下一rpc[0]#当前
        下一rpc[0]=号+1#前进
        return Rpc标识(f'fx-rpc-{号}')#品牌

    未决审批rpc=铸造rpc()#审批信封 id
    未决审批标识='fx-approval-1'#审批业务 id
    审批未决=[True]#未答
    未决提问rpc=铸造rpc()#提问信封 id
    提问未决=[True]#提问未答
    夹具提问=[#常驻提问（文案勿改）
        {'id':'harness-profile','header':'偏好','question':'你现在更想招哪类 Agent/Harness 候选人？','options':[
            {'label':'工程落地型 (Recommended)','description':'更看重能直接做 runtime、tool executor、sandbox、trace 和线上问题排查。'},
            {'label':'研究潜力型','description':'更看重 Agent 理解、训练评测思路和长期成长空间。'},
            {'label':'均衡型','description':'同时要求工程能力和 Agent 认知，但可能筛选门槛更高。'},
        ]},
        {'id':'work-mode','header':'方式','question':'你希望候选人优先展示哪种工作方式？','options':[
            {'label':'先做小型原型 (Recommended)','description':'用可运行结果尽快验证关键假设。'},
            {'label':'先写完整设计','description':'先收敛边界、协议和风险，再开始实现。'},
        ]},
        {'id':'signals','header':'信号','question':'哪些面试信号最重要？','detail':'按当前招聘目标选择；跳过则视为不设偏好。','multiSelect':True,'options':[
            {'label':'系统设计'},{'label':'代码质量'},{'label':'Agent 产品判断'},
        ]},
    ]#结束夹具提问
    mux连接们=set()#打开的 mux 收件箱
    宿主连接们=set()#打开的 host 收件箱

    def 广播mux(帧):#广播 mux 帧
        """每连接一封新 rpcId。"""
        for 连接 in list(mux连接们):#拷贝
            连接.push({'rpcId':铸造rpc(),'payload':帧})#推

    def 广播宿主(帧):#广播宿主帧
        """每连接一封新 rpcId。"""
        for 连接 in list(宿主连接们):#拷贝
            连接.push({'rpcId':铸造rpc(),'payload':帧})#推

    def 成功(请求,值):#成功响应
        """回显调用方 rpcId。"""
        return {'rpcId':请求['rpcId'],'result':{'ok':True,'value':值}}#成功信封

    def 失败(请求,错误):#失败响应
        """回显调用方 rpcId。"""
        return {'rpcId':请求['rpcId'],'result':{'ok':False,'error':错误}}#失败信封

    def 摘要于(标识):#按 id 找摘要
        """会话目录查找。"""
        for 项 in 会话们:#扫
            if 项['sessionId']==标识:#命中
                return 项#摘要
        return None#未知

    def 要求会话(请求):#会话必须存在
        """未知则错误响应，存在则 None。"""
        if 摘要于(请求['payload']['sessionId']) is not None:#存在
            return None#放行
        标识=请求['payload']['sessionId']#id
        return 失败(请求,{'code':'session-not-found','message':f'no session {标识}','details':{'sessionId':标识}})#未知

    def 设运行中(标识,运行中):#翻转 running 并广播
        """未知或未变则跳过。"""
        摘要=摘要于(标识)#摘要
        if 摘要 is None or 摘要['running']==运行中:#未知或未变
            return#跳过
        摘要['running']=运行中#写入
        广播宿主({'type':'host/session-status','sessionId':标识,'running':运行中})#宿主状态帧

    def 日志于(标识):#取或建日志
        """可变数组。"""
        日志=日志图.get(标识)#已有
        if 日志 is None:#尚无
            日志=[]#空
            日志图[标识]=日志#挂上
        return 日志#可变

    def 追加(标识,条目):#追加事件并直播
        """编 seq/time，emitMux，推投影帧。"""
        日志=日志于(标识)#目标
        事件={'seq':len(日志),'time':time.time()*1000,**条目}#编序号
        日志.append(事件)#持久
        视图=视图为(事件,日志)#可无
        if 视图 is None:#无视图
            广播mux({'type':'session/event','sessionId':标识,'event':事件})#纯事件
        else:#带视图
            广播mux({'type':'session/event','sessionId':标识,'event':事件,'view':视图})#带视图
        for 帧 in 投影帧于(标识,日志,事件):#投影帧
            广播mux(帧)#推

    def 追加目标变更(标识,变更):#写目标
        """追加 goal/change 并回扫。"""
        日志=日志于(标识)#折前同一数组
        追加(标识,{'type':'goal/change','data':变更})#追加
        return 回扫目标(日志)#刚写过

    def 目标失败(消息):#内部失败
        """RpcResult 失败体。"""
        return {'ok':False,'error':{'code':'internal','message':消息,'details':{}}}#失败

    def 要求目标会话(标识):#Remote 侧会话守卫
        """未知会话错误。"""
        if 摘要于(标识) is not None:#存在
            return None#放行
        return {'ok':False,'error':{'code':'session-not-found','message':f'no session {标识}','details':{'sessionId':标识}}}#未知

    def 目标视图(投影):#投影 → Remote 视图
        """active 即武装。"""
        目标=投影['goal']#本体
        return {#视图
            **目标,
            'roundsStarted':投影['roundsStarted'],
            'createdAt':投影['createdAt'],
            'updatedAt':投影['updatedAt'],
            'activation':'armed' if 目标.get('phase')=='active' else 'disarmed',
        }#结束视图

    def 解析目标(标识,引用):#CAS 读
        """当前投影或失败。"""
        缺=要求目标会话(标识)#会话
        if 缺 is not None:#未知
            return 缺#失败
        当前=回扫目标(日志于(标识))#现投影
        if 当前 is None or 当前['goal'].get('id')!=引用.get('id') or 当前['goal'].get('revision')!=引用.get('revision'):#对不上
            return 目标失败('stale or missing goal revision')#过期
        return {'ok':True,'value':当前}#命中

    def 变更目标(标识,引用,下一函):#CAS 写
        """由当前算出下一本体；None 表示非法转移。"""
        已解析=解析目标(标识,引用)#读
        if not 已解析.get('ok'):#失败
            return 已解析#原样
        当前=已解析['value']#当前
        目标=下一函(当前)#下一本体
        if 目标 is None:#非法
            return 目标失败(f"invalid goal transition from \"{当前['goal'].get('phase')}\"")#转移失败
        操作='edit'#同阶段
        if 目标.get('phase')!=当前['goal'].get('phase'):#阶段变
            相=目标.get('phase')#新阶段
            操作='pause' if 相=='paused' else 'resume' if 相=='active' else 'complete'#选 operation
        投影=追加目标变更(标识,{#按阶段选
            'kind':'goal/change','version':1,'operation':操作,
            'goal':目标,'roundsStarted':当前['roundsStarted'],
            'createdAt':当前['createdAt'],'updatedAt':time.time()*1000,
        })#结束追加
        return {'ok':True,'value':目标视图(投影)}#新视图

    def 映射目标结果(结果,映射):#映射成功值
        """失败原样。"""
        if 结果.get('ok'):#成功
            return {'ok':True,'value':映射(结果['value'])}#映射
        return 结果#失败

    def 目标引用结果(结果):#视图 → 引用应答
        """品牌 id 回引用。"""
        def 映引用(视):#视图 → 引用
            """抽出 id/revision。"""
            return {'ref':{'id':视['id'],'revision':视['revision']}}#引用
        return 映射目标结果(结果,映引用)#引用

    def 旧目标响应(请求,结果):#旧 API 信封
        """回填 rpcId。"""
        return {'rpcId':请求['rpcId'],'result':结果}#信封

    def 列命令(标识):#列命令
        """五条 fixture 命令。"""
        缺=要求目标会话(标识)#守卫
        if 缺 is not None:#未知
            return 缺#失败
        return {'ok':True,'value':[#五条（描述文案勿改）
            {'name':'compact','description':'fixture：压缩当前会话上下文'},
            {'name':'echo','description':'fixture：回显参数','input':{'hint':'text to echo'}},
            {'name':'goal','description':'set or view the goal for a long-running task','input':{'hint':'<objective>'}},
            {'name':'permission','description':'Switch the permission preset (sandbox mode + approval policy)','input':{'hint':'<preset>'}},
            {'name':'plan','description':'Enter or leave plan mode','input':{'hint':'[off|message]'}},
        ]}#结束成功

    def 执行命令(标识,行):#执行一行
        """镜像宿主解析器切分。"""
        缺=要求目标会话(标识)#守卫
        if 缺 is not None:#未知
            return 缺#失败
        匹配=re.match(r'^/(\S+)((?:\s.*)?)$',(行 or '').strip())#切 /name args
        名=匹配.group(1) if 匹配 else None#命令名
        参数=匹配.group(2) if 匹配 else ''#含前导空白
        if 名=='permission':#权限预设
            预设=(参数 or '').strip()#预设名或空
            命令标识=f'fx-cmd-{len(日志于(标识))}'#按日志长度造 id
            追加(标识,{'type':'command/run','data':{'commandId':命令标识,'name':名,'args':参数,'source':{'kind':'user'}}})#开跑
            规格=权限预设表.get(预设)#查表
            if 预设=='':#查询当前
                当前=权限选择于(日志于(标识))['currentValue']#当前值
                结果={'kind':'success','text':f"current preset {当前} (available: {', '.join(权限预设表.keys())})"}#列出
            elif 规格 is None:#未知预设
                结果={'kind':'error','text':f"unknown preset \"{预设}\" (available: {', '.join(权限预设表.keys())})"}#错误
            else:#切换
                if 权限选择于(日志于(标识))['currentValue']!=预设:#点名
                    追加(标识,{'type':'permission/preset','data':{'preset':预设}})#预设
                追加(标识,{'type':'sandbox/mode','data':{'mode':规格['sandbox']}})#沙箱
                追加(标识,{'type':'approval/policy','data':{'policy':规格['approval']}})#审批
                结果={'kind':'success','text':f'preset {预设}'}#成功文案
            追加(标识,{'type':'command/done','data':{'commandId':命令标识,**结果}})#收
            return {'ok':True,'value':{'commandId':命令标识,'result':结果}}#回执行
        if 名=='goal':#目标命令
            命令标识=f'fx-cmd-{len(日志于(标识))}'#造 id
            追加(标识,{'type':'command/run','data':{'commandId':命令标识,'name':名,'args':参数,'source':{'kind':'user'}}})#开跑
            目标文本=(参数 or '').strip()#目标文本
            当前=回扫目标(日志于(标识))#现投影
            if 目标文本=='':#查看
                文案='No goal is set. Usage: /goal <objective>' if 当前 is None else f"Current goal: {当前['goal']['objective']}"#无或有
            elif 当前 is not None and 当前['goal'].get('phase')!='complete':#已有未完成
                文案=f"A goal already exists ({当前['goal']['objective']}). Clear it first."#拒绝
            else:#创建
                造出=追加目标变更(标识,{#create
                    'kind':'goal/change','version':1,'operation':'create',
                    'goal':{'id':f'fx-goal-{len(日志于(标识))}','revision':1,'objective':目标文本,'phase':'active','maxGoalRounds':256},
                    'roundsStarted':0,'createdAt':time.time()*1000,'updatedAt':time.time()*1000,
                })#结束 create
                文案=f"Goal created: {造出['goal']['objective']}"#成功
            结果={'kind':'success','text':文案}#命令结果
            追加(标识,{'type':'command/done','data':{'commandId':命令标识,**结果}})#收
            return {'ok':True,'value':{'commandId':命令标识,'result':结果}}#回执行
        运行中=摘要于(标识) is not None and 摘要于(标识)['running'] is True#是否在跑
        结局={#其余命令回显
            'compact':'fixture：已压缩（假动作）',
            'echo':(参数 or '').strip(),
            'plan':(
                ('Leaving plan mode (applies from the next step).' if 运行中 else 'Plan mode off.')
                if (参数 or '').strip()=='off'
                else ('Entering plan mode (applies from the next step). Use /plan off to leave.' if 运行中 else 'Plan mode on. Use /plan off to leave.')
            ),
        }#结束结局
        文案=结局.get(名) if 名 is not None else None#查表
        if 名 is None or 文案 is None:#未知命令当无操作
            return {'ok':True,'value':None}#无操作
        命令标识=f'fx-cmd-{len(日志于(标识))}'#造 id
        追加(标识,{'type':'command/run','data':{'commandId':命令标识,'name':名,'args':参数,'source':{'kind':'user'}}})#开跑
        if 名=='plan' and not 运行中:#空闲时立刻提交计划
            计划=折计划(日志于(标识))#折
            if 计划['wanted'] is not None and 计划['wanted']!=计划['active']:#有未决
                追加(标识,{'type':'plan/mode','data':{'active':计划['wanted']}})#提交
        结果={'kind':'success'} if 文案=='' else {'kind':'success','text':文案}#空回显不加 text
        追加(标识,{'type':'command/done','data':{'commandId':命令标识,**结果}})#收
        return {'ok':True,'value':{'commandId':命令标识,'result':结果}}#回执行

    def 创建目标(标识,请求体):#规范 create
        """已有未完成则拒绝。"""
        缺=要求目标会话(标识)#守卫
        if 缺 is not None:#未知
            return 缺#失败
        当前=回扫目标(日志于(标识))#现投影
        if 当前 is not None and 当前['goal'].get('phase')!='complete':#已有未完成
            return 目标失败(f"goal \"{当前['goal']['id']}\" already exists")#拒绝
        现在=time.time()*1000#时间戳
        投影=追加目标变更(标识,{#create
            'kind':'goal/change','version':1,'operation':'create',
            'goal':{
                'id':f'fx-goal-{len(日志于(标识))}','revision':1,
                'objective':请求体['objective'],'phase':'active',
                'maxGoalRounds':请求体.get('maxGoalRounds',256),
            },
            'roundsStarted':0,'createdAt':现在,'updatedAt':现在,
        })#结束追加
        return {'ok':True,'value':{'ref':{'id':投影['goal']['id'],'revision':投影['goal']['revision']}}}#回引用

    def 编辑目标(标识,引用,请求体):#规范 edit
        """CAS 编辑。"""
        def 下一(当前):#下一本体
            """升修订并可选改字段。"""
            目标=dict(当前['goal'])#拷
            目标['revision']=当前['goal']['revision']+1#升修订
            if 'objective' in 请求体 and 请求体['objective'] is not None:#可选目标
                目标['objective']=请求体['objective']#改
            if 'maxGoalRounds' in 请求体 and 请求体['maxGoalRounds'] is not None:#可选上限
                目标['maxGoalRounds']=请求体['maxGoalRounds']#改
            return 目标#下一
        return 变更目标(标识,引用,下一)#CAS

    def 暂停目标(标识,引用):#规范 pause
        """仅 active → paused。"""
        def 下一(当前):#下一本体
            """非法则 None。"""
            if 当前['goal'].get('phase')!='active':#非法
                return None#拒绝
            return {**当前['goal'],'revision':当前['goal']['revision']+1,'phase':'paused'}#暂停
        return 变更目标(标识,引用,下一)#CAS

    def 恢复目标(标识,引用):#规范 resume
        """paused/blocked/active → active。"""
        def 下一(当前):#下一本体
            """非法则 None。"""
            if 当前['goal'].get('phase') not in ('paused','blocked','active'):#非法
                return None#拒绝
            return {**当前['goal'],'revision':当前['goal']['revision']+1,'phase':'active'}#恢复
        return 变更目标(标识,引用,下一)#CAS

    def 完成目标(标识,引用):#规范 complete
        """非 complete → complete。"""
        def 下一(当前):#下一本体
            """已完成则非法。"""
            if 当前['goal'].get('phase')=='complete':#已完成
                return None#拒绝
            return {**当前['goal'],'revision':当前['goal']['revision']+1,'phase':'complete'}#完成
        return 变更目标(标识,引用,下一)#CAS

    def 清除目标(标识,引用):#规范 clear
        """CAS 清除。"""
        已解析=解析目标(标识,引用)#CAS
        if not 已解析.get('ok'):#过期或缺失
            return 已解析#失败
        当前=已解析['value']#当前
        墓碑={'id':当前['goal']['id'],'revision':当前['goal']['revision']+1}#墓碑
        追加目标变更(标识,{'kind':'goal/change','version':1,'operation':'clear','cleared':墓碑,'clearedAt':time.time()*1000})#clear
        return {'ok':True,'value':墓碑}#回墓碑

    回放们={}#每会话最多一条在飞回放
    历史延迟毫秒=[0]#传输延迟
    下一次历史失败=[False]#一次性失败
    流打断们=set()#breakNow 集合
    重试剧本={}#sessionId → {turn, stepStarted}
    推理压测=[None]#可选压测泵状态

    def 开回复(标识,轮次,回复正文):#打字机回放
        """分块打字机（80ms/帧）→ 定稿 → turn/end。"""
        步=0#单步
        追加(标识,{'type':'step/start','data':{'turn':轮次,'step':步}})#开步
        追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':步,'chunk':{'type':'block-start','index':0,'blockType':'text'}}})#开块
        码点=list(回复正文 or '')#按码点
        片们=[''.join(码点[下标:下标+6]) for 下标 in range(0,len(码点),6)] or [回复正文 or '']#每片最多 6
        已发=[0]#已发片数
        定时器盒={'timer':None}#可变定时器

        def 定稿(已中断):#定稿
            """写 block-end + assistant/message + step/end + turn/end。"""
            回放们.pop(标识,None)#摘句柄
            完成=''.join(片们[:已发[0]])#已发出正文
            追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':步,'chunk':{'type':'block-end','index':0,'block':{'type':'text','text':完成}}}})#关块
            正文=f'{完成}（已中断）' if 已中断 else 完成#中断标记
            追加(标识,{'type':'assistant/message','surfaceOp':'append','data':{
                'turn':轮次,'step':步,'message':造助手消息(造文本块(正文)),'usage':夹具用量(轮次,步),
            }})#定稿
            追加(标识,{'type':'step/end','data':{'turn':轮次,'step':步}})#收步
            追加(标识,{'type':'turn/end','data':{'turn':轮次,'reason':{'kind':'cancelled' if 已中断 else 'completed'}}})#收轮
            设运行中(标识,False)#停跑

        def 滴答():#发一片
            """下一片或定稿。"""
            if 已发[0]>=len(片们):#发完
                定稿(False)#正常定稿
                return#停
            片=片们[已发[0]]#下一片
            已发[0]+=1#前进
            追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':步,'chunk':{'type':'text-delta','index':0,'text':片}}})#delta
            定时器=threading.Timer(0.08,滴答)#下一拍
            定时器.daemon=True#守护
            定时器.start()#启动
            定时器盒['timer']=定时器#记下
            回放们[标识]={'timer':定时器,'finish':定稿}#句柄

        首定时=threading.Timer(0.08,滴答)#启动
        首定时.daemon=True#守护
        首定时.start()#开
        定时器盒['timer']=首定时#记下
        回放们[标识]={'timer':首定时,'finish':定稿}#句柄

    def 时序钩_设历史延迟(毫秒):#设传输延迟
        """毫秒。"""
        历史延迟毫秒[0]=毫秒#写入

    def 时序钩_下一次历史失败():#一次性失败
        """下一发 history 抛错。"""
        下一次历史失败[0]=True#旗

    def 时序钩_追加用户(标识字面,消息):#直播用户消息
        """走 append。"""
        追加(会话标识(标识字面),{'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块(消息))})#追加

    def 时序钩_追加标题(标识字面,标题):#直播标题
        """经正常原始事件路径。"""
        标识=会话标识(标识字面)#品牌
        日志=日志于(标识)#现日志
        消息序号=[事件['seq'] for 事件 in 日志 if isinstance(事件,dict) and 事件.get('type')=='user/message']#用户 seq
        追加(标识,{'type':'session/title','data':{'title':标题,'messageSeqs':消息序号,'source':{'kind':'provider','provider':'fixture'}}})#标题

    def 时序钩_开推理压测(标识字面,块数,每间隔块数,间隔毫秒):#压测泵
        """外部节奏推理流；返回完成标记。"""
        if not isinstance(块数,int) or 块数<1:#块数非法
            raise Exception('fixture: reasoning chunk count must be a positive safe integer')#错误串勿改
        if not isinstance(每间隔块数,int) or 每间隔块数<1:#每间隔非法
            raise Exception('fixture: reasoning chunks per interval must be a positive safe integer')#勿改
        if not isinstance(间隔毫秒,int) or 间隔毫秒<1:#间隔非法
            raise Exception('fixture: reasoning interval must be a positive safe integer')#勿改
        活动=推理压测[0]#现泵
        if 活动 is not None and 活动.get('emitting') is True:#已在泵
            raise Exception('fixture: reasoning chunk storm already running')#勿改
        标识=会话标识(标识字面)#品牌
        日志=日志于(标识)#日志
        轮次=下一轮.get(标识,0)#候选轮
        for 事件 in 日志:#按已有 turn 抬高
            数据=事件.get('data') if isinstance(事件,dict) else None#data
            候选=数据.get('turn') if isinstance(数据,dict) else None#turn
            if isinstance(候选,(int,float)):#数字
                轮次=max(轮次,int(候选)+1)#下一轮
        下一轮[标识]=轮次+1#占住
        标记=f'REASONING_STRESS_COMPLETE:{轮次}:{块数}'#完成哨兵
        状态={#泵状态
            'sessionId':标识字面,'chunkCount':块数,'chunksPerInterval':每间隔块数,
            'intervalMs':间隔毫秒,'emitted':0,'marker':标记,'emitting':True,
        }#结束状态
        推理压测[0]=状态#挂上
        设运行中(标识,True)#开跑
        追加(标识,{'type':'turn/start','data':{'turn':轮次,'trigger':{'kind':'message','source':{'kind':'user'}}}})#开轮
        追加(标识,{'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块(f'Reasoning chunk stress: {块数} chunks.'))})#用户
        追加(标识,{'type':'step/start','data':{'turn':轮次,'step':0}})#开步
        追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':0,'chunk':{'type':'block-start','index':0,'blockType':'reasoning'}}})#开块
        起点=[time.time()*1000]#泵起点

        def 泵():#按墙钟补块
            """补发到应付数量。"""
            已过=int((time.time()*1000-起点[0])//间隔毫秒)+1#已过间隔
            应付=max(状态['emitted']+每间隔块数,已过*每间隔块数)#应付到
            止=min(应付,块数)#不超过总数
            for 下标 in range(状态['emitted'],止):#补发
                块文=f'\n{标记}' if 下标==块数-1 else ('推理\n' if 下标%64==63 else '推理')#末块带标记
                追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':0,'chunk':{'type':'reasoning-delta','index':0,'text':块文}}})#delta
            状态['emitted']=止#已发
            if 止<块数:#未完
                定时=threading.Timer(间隔毫秒/1000,泵)#下一拍
                定时.daemon=True#守护
                定时.start()#开
            else:#完
                状态['emitting']=False#停泵

        首=threading.Timer(0,泵)#尽快开泵
        首.daemon=True#守护
        首.start()#开
        return 标记#给探针

    def 时序钩_推理压测状态():#探针只读
        """浅拷，避免改到活动泵。"""
        活动=推理压测[0]#现
        return None if 活动 is None else dict(活动)#浅拷

    def 时序钩_开模型重试(标识字面):#开重试剧本
        """半截回复保持可见直到 llm/retry。"""
        标识=会话标识(标识字面)#品牌
        轮次=下一轮.get(标识,0)#下一轮
        下一轮[标识]=轮次+1#占住
        重试剧本[标识]={'turn':轮次,'stepStarted':True}#记下
        设运行中(标识,True)#开跑
        追加(标识,{'type':'turn/start','data':{'turn':轮次}})#开轮
        追加(标识,{'type':'user/message','surfaceOp':'append','data':{'content':造文本块('请重试这个请求'),'source':{'kind':'user'}}})#用户
        追加(标识,{'type':'step/start','data':{'turn':轮次,'step':1}})#开步
        追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':1,'chunk':{'type':'block-start','index':0,'blockType':'text'}}})#开块
        追加(标识,{'type':'assistant/chunk','data':{'turn':轮次,'step':1,'chunk':{'type':'text-delta','index':0,'text':'应撤回的半截回复'}}})#半截

    def 时序钩_排模型重试(标识字面,重试=1,延迟毫秒=450):#排重试
        """记录一次重试决定。"""
        标识=会话标识(标识字面)#品牌
        剧本=重试剧本.get(标识)#剧本
        if 剧本 is None:#未 begin
            raise Exception(f'fixture: no model retry scenario for {标识字面}')#错误
        if not 剧本['stepStarted']:#需要再开一块半截
            追加(标识,{'type':'assistant/chunk','data':{'turn':剧本['turn'],'step':1,'chunk':{'type':'block-start','index':0,'blockType':'text'}}})#开块
            追加(标识,{'type':'assistant/chunk','data':{'turn':剧本['turn'],'step':1,'chunk':{'type':'text-delta','index':0,'text':f'第 {重试} 次应撤回的回复'}}})#半截
            剧本['stepStarted']=True#已开
        失败体={'code':'TRANSPORT','message':'连接被重置'}#失败体（文案勿改）
        追加(标识,{'type':'llm/retry','data':{
            'turn':剧本['turn'],'step':1,'provider':'fixture','mode':'normal','policyKey':'fixture-normal',
            'retry':重试,'maxRetries':2,'delayMs':延迟毫秒,'failure':失败体,
        }})#retry
        剧本['stepStarted']=False#下次再开块

    def 时序钩_退避中取消(标识字面,延迟毫秒=450):#退避中取消
        """记录重试后取消源轮。"""
        标识=会话标识(标识字面)#品牌
        剧本=重试剧本.get(标识)#剧本
        if 剧本 is None:#未 begin
            raise Exception(f'fixture: no model retry scenario for {标识字面}')#错误
        失败体={'code':'TRANSPORT','message':'连接被重置'}#失败体
        追加(标识,{'type':'llm/retry','data':{
            'turn':剧本['turn'],'step':1,'provider':'fixture','mode':'normal','policyKey':'fixture-normal',
            'retry':1,'maxRetries':2,'delayMs':延迟毫秒,'failure':失败体,
        }})#retry
        追加(标识,{'type':'step/end','data':{'turn':剧本['turn'],'step':1}})#收步
        追加(标识,{'type':'turn/end','data':{'turn':剧本['turn'],'reason':{'kind':'aborted','reason':{'kind':'user'}}}})#用户中止
        重试剧本.pop(标识,None)#清剧本
        设运行中(标识,False)#停跑

    def 时序钩_完成模型重试(标识字面):#完成重试
        """用定稿回复结束。"""
        标识=会话标识(标识字面)#品牌
        剧本=重试剧本.pop(标识,None)#清
        if 剧本 is None:#未 begin
            raise Exception(f'fixture: no model retry scenario for {标识字面}')#错误
        追加(标识,{'type':'assistant/chunk','data':{'turn':剧本['turn'],'step':1,'chunk':{'type':'block-start','index':0,'blockType':'text'}}})#开块
        追加(标识,{'type':'assistant/message','surfaceOp':'append','data':{
            'turn':剧本['turn'],'step':1,'message':造助手消息(造文本块('重试后的完整回复')),
        }})#定稿
        追加(标识,{'type':'step/end','data':{'turn':剧本['turn'],'step':1}})#收步
        追加(标识,{'type':'turn/end','data':{'turn':剧本['turn'],'reason':{'kind':'completed'}}})#收轮
        设运行中(标识,False)#停跑

    def 时序钩_静默追加(标识字面,消息):#静默追加
        """只追加日志、不 mux 发射。"""
        标识=会话标识(标识字面)#品牌
        日志=日志于(标识)#日志
        日志.append({'type':'user/message','surfaceOp':'append','seq':len(日志),'time':time.time()*1000,'data':造用户消息(造文本块(消息))})#不广播

    def 时序钩_断流():#断流
        """结束每个打开的流生成器。"""
        for 打断 in list(流打断们):#拷贝后打断
            打断()#breakNow

    时序钩=面对象(#挂到 builtins.__fxTiming
        setHistoryDelay=staticmethod(时序钩_设历史延迟),
        failNextHistory=staticmethod(时序钩_下一次历史失败),
        appendUser=staticmethod(时序钩_追加用户),
        appendTitle=staticmethod(时序钩_追加标题),
        startReasoningChunkStorm=staticmethod(时序钩_开推理压测),
        reasoningChunkStormState=staticmethod(时序钩_推理压测状态),
        beginModelRetry=staticmethod(时序钩_开模型重试),
        scheduleModelRetry=staticmethod(时序钩_排模型重试),
        cancelModelRetryDuringBackoff=staticmethod(时序钩_退避中取消),
        completeModelRetry=staticmethod(时序钩_完成模型重试),
        appendSilent=staticmethod(时序钩_静默追加),
        breakStreams=staticmethod(时序钩_断流),
    )#结束时序钩
    try:#浏览器后门
        import builtins as 内建#全局
        setattr(内建,'__fxTiming',时序钩)#挂上
    except Exception:#非浏览器
        pass#忽略

    def 列会话(请求):#按更新倒序
        """会话目录。"""
        def 更新键(项):#排序键
            """updatedAt。"""
            return 项['updatedAt']#时刻
        项们=sorted(会话们,key=更新键,reverse=True)#倒序
        return 成功(请求,{'items':[dict(项) for 项 in 项们]})#拷贝

    def 检索会话(请求,信号):#会话检索
        """表面短语匹配分页。"""
        if 取已中止(信号):#已取消
            return 失败(请求,{'code':'cancelled','message':'fixture session search was aborted','details':{}})#取消
        查询=[令牌['value'] for 令牌 in 检索令牌跨度(请求['payload'].get('query') or '')['tokens']]#查询 token
        候选们=[]#跨会话
        for 摘要 in 会话们:#每会话一条最佳
            日志=日志图.get(摘要['sessionId']) or []#日志
            当前=set(折表面(日志)['nodes'])#当前表面
            本会话=[]#候选
            for 事件 in 日志:#表面事件
                if not isinstance(事件,dict) or 事件.get('seq') not in 当前:#非当前
                    continue#跳过
                事件正文=检索事件文本(事件)#检索正文
                文档=检索令牌跨度(事件正文)#切 token
                命中=短语匹配(文档['tokens'],查询)#短语
                if 命中['count']==0:#未命中
                    continue#跳过
                本会话.append({#候选
                    'sessionId':摘要['sessionId'],'seq':事件['seq'],'time':事件.get('time',0),
                    'text':文档['text'],'matchCount':命中['count'],
                    'matchStart':命中['start'],'matchEnd':命中['end'],
                    'documentLength':len(list(事件正文)),
                })#结束候选
            if 本会话:#有命中
                本会话.sort(key=functools.cmp_to_key(比较检索候选))#该会话排序
                候选们.append(本会话[0])#最佳
        候选们.sort(key=functools.cmp_to_key(比较检索候选))#跨会话排序
        上限=会话搜索结果上限#截断
        return 成功(请求,{#分页
            'items':[{
                'sessionId':命中['sessionId'],
                'snippet':检索摘录(命中['text'],命中['matchStart'],命中['matchEnd']),
            } for 命中 in 候选们[:上限]],
            'hasMore':len(候选们)>上限,
        })#结束成功

    def 创建会话(请求):#创建或幂等挂接
        """工作区挂接与帧序分支。"""
        载荷=请求['payload']#载荷
        工作区标识值=载荷.get('workspaceId')#可选
        工作区=None if 工作区标识值 is None else next((区 for 区 in 工作区们 if 区['workspaceId']==工作区标识值),None)#按 id
        if 工作区标识值 is not None and 工作区 is None:#id 有但找不到
            return 失败(请求,{'code':'workspace-not-found','message':f'no workspace {工作区标识值}','details':{'workspaceId':工作区标识值}})#缺失
        工作目录=(工作区 or {}).get('path') or 载荷.get('cwd') or '/tmp/fixture'#cwd
        请求标识=载荷.get('sessionId')#可选已有 id

        def 挂工作区(会话标识值):#挂到工作区头
            """无目标或已挂则跳过。"""
            if 工作区 is None or 会话标识值 in 工作区['sessionIds']:#无或已挂
                return#跳过
            工作区['sessionIds']=[会话标识值,*工作区['sessionIds']]#插到最前
            工作区['updatedAt']=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())#刷新
            广播宿主({'type':'host/workspace-changed','workspace':dict(工作区)})#广播

        def 挂接失败回执(会话标识值,工作区标识值2):#挂接失败
            """拒绝挂接。"""
            return 失败(请求,{'code':'workspace-attach-failed','message':f'fixture rejected Workspace attachment for {会话标识值}','details':{'sessionId':会话标识值,'workspaceId':工作区标识值2}})#失败

        if 请求标识 is not None:#幂等挂接
            已有=摘要于(请求标识)#查摘要
            if 已有 is not None:#已存在
                if 已有.get('cwd')!=工作目录:#cwd 冲突
                    细节={'sessionId':请求标识,'requestedCwd':工作目录}#细节
                    if 已有.get('cwd') is not None:#有现 cwd
                        细节['existingCwd']=已有['cwd']#补
                    return 失败(请求,{'code':'session-conflict','message':f"session {请求标识} already uses {已有.get('cwd') or 'no cwd'}",'details':细节})#冲突
                if 工作区 is not None and 请求标识 not in 工作区['sessionIds']:#尚未挂上
                    if 挂接失败:#演失败
                        return 挂接失败回执(请求标识,工作区['workspaceId'])#拒
                    挂工作区(请求标识)#挂上
                return 成功(请求,{'sessionId':请求标识})#幂等成功
        新标识=请求标识 if 请求标识 is not None else 会话标识(f'fx-{下一会话[0]}')#新 id
        if 请求标识 is None:#自造
            下一会话[0]+=1#前进
        建成={'sessionId':新标识,'updatedAt':time.time()*1000,'running':False,'blank':True,'cwd':工作目录}#新摘要
        会话们.append(建成)#登记
        模型选择[新标识]={'provider':'deepseek-official','model':'deepseek-v4-flash'}#默认模型
        已挂接[0]+=1#已挂计数

        def 发会话帧():#发 session-added
            """创建时 blank 恒为 true。"""
            广播宿主({'type':'host/session-added','sessionId':建成['sessionId'],'blank':True,'cwd':工作目录})#创建帧

        if 工作区 is not None and 挂接失败:#先发帧再拒挂
            发会话帧()#已发布
            return 挂接失败回执(建成['sessionId'],工作区['workspaceId'])#拒挂
        if 工作区 is not None and 帧序=='workspace-first':#先工作区后会话
            挂工作区(建成['sessionId'])#先挂
            发会话帧()#后发帧
        else:#默认先会话后工作区
            发会话帧()#先发帧
            if 工作区 is not None:#再挂
                挂工作区(建成['sessionId'])#挂
        if 丢创建响应:#发布后丢响应
            raise Exception('fixture: dropped session.create response after publication')#勿改
        return 成功(请求,{'sessionId':建成['sessionId']})#回新 id

    def 重命名会话(请求):#改会话标题
        """压空白后追加 session/title。"""
        缺=要求会话(请求)#必须存在
        if 缺 is not None:#未知
            return 缺#失败
        标识=请求['payload']['sessionId']#id
        标题=请求['payload']['title']#标题
        规范=re.sub(r'\s+',' ',(标题 or '').strip())#压空白
        if 规范=='':#无可见字符
            return 失败(请求,{'code':'title-invalid','message':'session title must contain visible characters','details':{'sessionId':标识}})#非法
        追加(标识,{'type':'session/title','data':{'title':规范,'messageSeqs':[],'source':{'kind':'user'}}})#标题事件
        末=日志于(标识)[-1]#刚追加
        return 成功(请求,{'title':规范,'seq':末['seq']})#回标题与 seq

    def 分叉会话(请求):#在已完成轮边界分叉
        """拷前缀日志并挂工作区。"""
        载荷=请求['payload']#载荷
        标识=载荷['sessionId']#源
        锚点=载荷.get('atSeq')#可选锚
        源=摘要于(标识)#源摘要
        if 源 is None:#未知
            return 失败(请求,{'code':'session-not-found','message':f'no session {标识}','details':{'sessionId':标识}})#缺失
        日志=日志图.get(标识) or []#源日志
        末序号=日志[-1]['seq'] if 日志 else -1#末 seq
        锚定边界=None if 锚点 is None else next((事件 for 事件 in 日志 if 事件.get('type')=='turn/end' and 事件.get('seq')>=锚点),None)#含 atSeq
        if 锚定边界 is not None:#优先锚点
            边界=锚定边界#用
        elif 锚点 is None or 锚点>末序号:#未点名或超出现有
            边界=next((事件 for 事件 in reversed(日志) if 事件.get('type')=='turn/end'),None)#最后一轮
        else:#点名落在未完成轮内
            边界=None#不可分
        if 边界 is None:#没有可切的轮边界
            消息=(
                f'session {标识} has not completed the turn containing event {锚点}'
                if 锚点 is not None and 锚点<=末序号
                else f'session {标识} has no completed turn'
            )#文案
            return 失败(请求,{'code':'fork-unavailable','message':消息,'details':{'sessionId':标识}})#不可分
        切=边界['seq']+1#切点
        while 切<len(日志) and 日志[切].get('type')!='turn/start':#跳到下一轮起点
            切+=1#前进
        子={'sessionId':会话标识(f'fx-{下一会话[0]}'),'updatedAt':time.time()*1000,'running':False,'blank':False,'parentSessionId':标识}#子摘要
        下一会话[0]+=1#前进
        if 源.get('cwd') is not None:#继承 cwd
            子['cwd']=源['cwd']#拷
        日志图[子['sessionId']]=list(日志[:切])#拷前缀
        会话们.append(子)#登记
        帧={'type':'host/session-added','sessionId':子['sessionId'],'blank':False,'parentSessionId':标识}#子会话帧
        if 源.get('cwd') is not None:#带 cwd
            帧['cwd']=源['cwd']#拷
        广播宿主(帧)#发
        工作区=next((区 for 区 in 工作区们 if 标识 in 区['sessionIds']),None)#源所在
        if 工作区 is not None:#挂子会话
            工作区['sessionIds']=[子['sessionId'],*工作区['sessionIds']]#插到最前
            工作区['updatedAt']=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())#刷新
            广播宿主({'type':'host/workspace-changed','workspace':dict(工作区)})#广播
        return 成功(请求,{'sessionId':子['sessionId']})#回子 id

    def 会话历史(请求):#分页历史
        """请求时拍快照，过完传输延迟再交付。"""
        标识=请求['payload']['sessionId']#id
        日志=日志图.get(标识) or []#日志
        页=分页于(日志,请求['payload'].get('beforeSeq'),请求['payload'].get('maxMessages') or 50)#切页
        投影=None#可选
        if 请求['payload'].get('beforeSeq') is None:#尾页才带
            投影={'asOfSeq':len(日志)-1,'values':投影值于(日志)}#整包
        注定失败=下一次历史失败[0]#本拍
        下一次历史失败[0]=False#一次性
        延迟=历史延迟毫秒[0]#传输延迟
        if 延迟>0:#等延迟
            time.sleep(延迟/1000)#秒
        if 注定失败:#演失败
            raise Exception('fixture: simulated history transport failure')#勿改
        值=dict(页)#页
        if 投影 is not None:#带投影
            值['projections']=投影#投影
        return 成功(请求,值)#页 + 可选投影

    def 会话模型(请求):#列模型
        """当前选择与分组目录。"""
        标识=请求['payload']['sessionId']#id
        当前=模型选择.get(标识) or {'provider':'deepseek-official','model':'deepseek-v4-flash'}#默认
        return 成功(请求,{'current':当前,'routable':True,'groups':夹具模型分组(),'failures':[]})#目录

    def 选模型(请求):#记下选择
        """新选择。"""
        载荷=请求['payload']#载荷
        选中={'provider':载荷['provider'],'model':载荷['model']}#新选择
        if 载荷.get('reasoningEffort') is not None:#可选等级
            选中['reasoningEffort']=载荷['reasoningEffort']#挂上
        模型选择[载荷['sessionId']]=选中#记下
        return 成功(请求,{'selected':选中})#回选择

    def 提示会话(请求):#接受用户消息并开回放
        """steer 或新轮 + 打字机。"""
        载荷=请求['payload']#载荷
        标识=载荷['sessionId']#id
        模式=载荷.get('mode')#模式
        内容=载荷.get('content') or []#内容块
        摘要=摘要于(标识)#摘要
        if 摘要 is None:#未知
            return 失败(请求,{'code':'session-not-found','message':f'no session {标识}','details':{'sessionId':标识}})#缺失
        if 拒提示:#演拒绝
            return 失败(请求,{'code':'agent-busy','message':'fixture: prompt rejected before acceptance','details':{'reason':'fixture-prompt-rejection'}})#拒绝
        摘要['updatedAt']=time.time()*1000#刷新
        摘要['blank']=False#已有内容
        用户文本=''.join(块.get('text','') if isinstance(块,dict) and 块.get('type')=='text' else '' for 块 in 内容)#拼文本
        落库=[]#落库内容
        for 块 in 内容:#逐块
            if not isinstance(块,dict):#非映射
                continue#跳过
            if 块.get('type')=='text':#文本原样
                落库.append(块)#收下
                continue#下一块
            数据=块.get('data') or ''#base64
            填充=2 if 数据.endswith('==') else (1 if 数据.endswith('=') else 0)#扣填充
            附件={#图片改引用
                'attachmentId':f'fixture:{随机uuid()}','mediaType':块.get('mediaType'),
                'bytes':max(1,len(数据)*3//4-填充),'width':160,'height':90,
            }#结束附件
            if 块.get('name') is not None:#可选文件名
                附件['name']=块['name']#挂上
            附件图[str(附件['attachmentId'])]={'attachment':附件,'data':数据}#记下字节
            落库.append({'type':'image','attachment':附件})#引用块
        if 模式=='steer' and 标识 in 回放们:#转向进行中的回放
            追加(标识,{'type':'user/message','surfaceOp':'append','data':造用户消息(落库)})#当前轮内
            return 成功(请求,{'accepted':True})#接受、不新开轮
        轮次=下一轮.get(标识,0)#下一轮号
        下一轮[标识]=轮次+1#预占
        设运行中(标识,True)#开跑
        追加(标识,{'type':'turn/start','data':{'turn':轮次}})#开轮
        计划=折计划(日志于(标识))#折计划
        if 计划['wanted'] is not None and 计划['wanted']!=计划['active']:#有未决
            追加(标识,{'type':'plan/mode','data':{'active':计划['wanted']}})#提交
        追加(标识,{'type':'user/message','surfaceOp':'append','data':造用户消息(落库)})#用户消息
        选择=模型选择.get(标识) or {'provider':'deepseek','model':'deepseek-v4-flash'}#当前路由
        if (最近请求上下文(日志于(标识)) or {}).get('model')!=选择.get('model'):#模型变了才记
            追加(标识,{'type':'request/context','data':{'provider':选择['provider'],'model':选择['model'],'contextWindow':128_000}})#容量
        if 用户文本=='render markdown':#Markdown 样本
            回复=markdown样本#固定正文
        elif 用户文本=='report model':#回显当前模型
            选=模型选择.get(标识)#已选
            回复=f"当前模型：{(选 or {}).get('provider','unknown')}/{(选 or {}).get('model','unknown')}"#提供方/模型
            if 选 is not None and 选.get('reasoningEffort') is not None:#可选等级
                回复+=f" · 推理等级：{选['reasoningEffort']}"#等级
        else:#默认回声
            回复=f'回声：{用户文本}。这是 fixture 的流式回复，用于验证打字机增长与定稿切换。'#回声
        开回复(标识,轮次,回复)#开打字机
        return 成功(请求,{'accepted':True})#接受

    def 读附件(请求):#按会话授权读附件
        """必须被本会话引用。"""
        存=附件图.get(str(请求['payload']['attachmentId']))#按 id
        if 存 is None:#没有
            return 失败(请求,{'code':'attachment-error','message':'fixture attachment missing','details':{'reason':'ATTACHMENT_NOT_FOUND'}})#缺失
        if not 日志引用附件(日志图.get(请求['payload']['sessionId']) or [],str(请求['payload']['attachmentId'])):#未引用
            return 失败(请求,{'code':'attachment-error','message':'fixture attachment is not referenced by this session','details':{'reason':'ATTACHMENT_NOT_REFERENCED'}})#越权
        return 成功(请求,存)#回附件

    def 更新队列(请求):#fixture 无队列项
        """恒失败。"""
        return 失败(请求,{'code':'queue-item-not-found','message':'fixture has no pending queue item','details':{'itemId':请求['payload'].get('itemId')}})#无

    def 取消会话(请求):#停回放或翻 running
        """有回放则中断定稿。"""
        标识=请求['payload']['sessionId']#id
        回放=回放们.get(标识)#进行中
        if 回放 is not None:#有回放
            定时=回放.get('timer')#定时器
            if 定时 is not None:#可停
                定时.cancel()#停下一拍
            回放['finish'](True)#中断定稿
        else:#无回放
            设运行中(标识,False)#只翻 running
        return 成功(请求,{'accepted':True})#接受

    def 列子智能体(请求):#空列表
        """stub。"""
        return 成功(请求,{'entries':[],'parentAvailable':True})#空

    def 子历史(请求):#子会话分页
        """切页。"""
        日志=日志图.get(请求['payload']['childSessionId']) or []#子日志
        return 成功(请求,分页于(日志,请求['payload'].get('beforeSeq'),请求['payload'].get('maxMessages') or 50))#页

    def 子提示(请求):#假消息 id
        """接受。"""
        return 成功(请求,{'messageId':f"fixture-message-{请求['payload']['childSessionId']}"})#假 id

    def 子中断(请求):#空操作接受
        """接受。"""
        return 成功(请求,{'accepted':True})#接受

    def 描述宿主(请求):#宿主画像
        """版本与挂接计数。"""
        return 成功(请求,{'version':'0.0.0-fixture','cwd':'/tmp/fixture','attachedSessions':已挂接[0],'canOpenPath':True})#描述

    def 选目录(请求):#确定性选中
        """无密钥车道。"""
        return 成功(请求,{'path':f'{夹具家}/Documents/project'})#路径

    def 列目录(请求):#列目录
        """fixture 树。"""
        目标=请求['payload'].get('path') or 夹具家#缺省家
        子们=列子(目标)#子名
        if 子们 is None:#不在树上
            return 失败(请求,{'code':'directory-unreadable','message':f'cannot list {目标}: not in the fixture tree','details':{'path':目标}})#不可读
        条目=[{'name':名,'path':f'/{名}' if 目标=='/' else f'{目标}/{名}','hidden':名.startswith('.')} for 名 in sorted(子们)]#条目
        return 成功(请求,{'path':目标,'home':夹具家,'crumbs':面包屑(目标),'entries':条目,'truncated':False})#目录页

    def 建目录(请求):#建子目录
        """登记到目录树。"""
        父=请求['payload']['path']#父路径
        名=请求['payload']['name']#子名
        子们=列子(父)#现有
        if 子们 is None:#父不在树上
            return 失败(请求,{'code':'directory-create-failed','message':f'missing parent {父}','details':{'path':父}})#失败
        目标=f'/{名}' if 父=='/' else f'{父}/{名}'#子路径
        if 名 in 子们:#已有同名
            return 失败(请求,{'code':'directory-exists','message':f'{目标} already exists','details':{'path':目标}})#冲突
        目录树[父]=[*子们,名]#登记子名
        目录树[目标]=[]#空目录
        return 成功(请求,{'path':目标})#回路径

    def 打开路径(请求):#空操作成功
        """opened true。"""
        return 成功(请求,{'opened':True})#成功

    def 列工作区(请求):#列工作区
        """拷贝视图。"""
        return 成功(请求,{'items':[dict(区) for 区 in 工作区们],'archivedSessionIds':list(已归档)})#列表

    def 建工作区(请求):#按 path 幂等创建
        """同路径则已有。"""
        路径=请求['payload']['path']#路径
        已有=next((区 for 区 in 工作区们 if 区['path']==路径),None)#同路径
        if 已有 is not None:#已有
            return 成功(请求,{'workspace':dict(已有),'created':False})#已有
        现在=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())#时间戳
        末段=([部 for 部 in 路径.split('/') if 部] or [路径])[-1]#末段名
        建成={'workspaceId':工作区标识(f'fx-ws-{下一工作区[0]}'),'path':路径,'title':末段,'sessionIds':[],'createdAt':现在,'updatedAt':现在}#新
        下一工作区[0]+=1#前进
        工作区们.insert(0,建成)#插到最前
        广播宿主({'type':'host/workspace-changed','workspace':dict(建成)})#广播
        return 成功(请求,{'workspace':dict(建成),'created':True})#新造

    def 改工作区名(请求):#改工作区标题
        """重名冲突。"""
        载荷=请求['payload']#载荷
        工作区=next((区 for 区 in 工作区们 if 区['workspaceId']==载荷['workspaceId']),None)#按 id
        if 工作区 is None:#找不到
            return 失败(请求,{'code':'workspace-not-found','message':f"no workspace {载荷['workspaceId']}",'details':{'workspaceId':载荷['workspaceId']}})#缺失
        修剪=(载荷.get('title') or '').strip()#去两端
        if 修剪!=工作区['title']:#真有改
            if any(区['workspaceId']!=载荷['workspaceId'] and 区['title']==修剪 for 区 in 工作区们):#重名
                return 失败(请求,{'code':'workspace-name-conflict','message':f"workspace name '{修剪}' is already in use",'details':{'name':修剪}})#冲突
            工作区['title']=修剪#改标题
            工作区['updatedAt']=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())#刷新
            广播宿主({'type':'host/workspace-changed','workspace':dict(工作区)})#广播
        return 成功(请求,{'workspace':dict(工作区)})#回视图

    def 删工作区(请求):#删工作区
        """摘掉并广播移除。"""
        标识=请求['payload']['workspaceId']#id
        下标=next((号 for 号,区 in enumerate(工作区们) if 区['workspaceId']==标识),-1)#下标
        if 下标==-1:#找不到
            return 失败(请求,{'code':'workspace-not-found','message':f'no workspace {标识}','details':{'workspaceId':标识}})#缺失
        工作区们.pop(下标)#摘掉
        广播宿主({'type':'host/workspace-removed','workspaceId':标识})#广播
        return 成功(请求,{'deleted':True})#已删

    def 插入工作区前(请求):#重排工作区
        """源插到锚前；未点名锚则接到尾。"""
        载荷=请求['payload']#载荷
        源标识=载荷['workspaceId']#源
        锚标识=载荷.get('beforeWorkspaceId')#锚
        源下标=next((号 for 号,区 in enumerate(工作区们) if 区['workspaceId']==源标识),-1)#源
        锚下标=len(工作区们) if 锚标识 is None else next((号 for 号,区 in enumerate(工作区们) if 区['workspaceId']==锚标识),-1)#锚
        缺=源标识 if 源下标==-1 else (锚标识 if 锚下标==-1 else None)#缺谁
        if 缺 is not None:#源或锚找不到
            return 失败(请求,{'code':'workspace-not-found','message':f'no workspace {缺}','details':{'workspaceId':缺}})#缺失
        if 锚标识!=源标识:#不是插到自己前面
            先前=[区['workspaceId'] for 区 in 工作区们]#改前序
            工作区=工作区们.pop(源下标)#摘出
            插入点=len(工作区们) if 锚标识 is None else next(号 for 号,区 in enumerate(工作区们) if 区['workspaceId']==锚标识)#锚现位
            工作区们.insert(插入点,工作区)#插入
            if any(区['workspaceId']!=先前[号] for 号,区 in enumerate(工作区们)):#序真变了
                广播宿主({'type':'host/workspace-order-changed','workspaceIds':[区['workspaceId'] for 区 in 工作区们]})#顺序帧
        return 成功(请求,{'workspaceIds':[区['workspaceId'] for 区 in 工作区们]})#回现序

    def 插入会话前(请求):#重排会话槽
        """工作区内会话重排。"""
        载荷=请求['payload']#载荷
        工作区=next((区 for 区 in 工作区们 if 区['workspaceId']==载荷['workspaceId']),None)#按 id
        if 工作区 is None:#找不到
            return 失败(请求,{'code':'workspace-not-found','message':f"no workspace {载荷['workspaceId']}",'details':{'workspaceId':载荷['workspaceId']}})#缺失
        会话标识值=载荷['sessionId']#源
        锚会话=载荷.get('beforeSessionId')#锚
        if 会话标识值 not in 工作区['sessionIds'] or (锚会话 is not None and 锚会话 not in 工作区['sessionIds']):#非法
            细节={'workspaceId':载荷['workspaceId'],'sessionId':会话标识值}#细节
            if 锚会话 is not None:#有锚
                细节['beforeSessionId']=锚会话#补
            return 失败(请求,{'code':'workspace-move-invalid','message':f"session or anchor is not accounted by workspace {载荷['workspaceId']}",'details':细节})#非法
        无源=[号 for 号 in 工作区['sessionIds'] if 号!=会话标识值]#先摘源
        插入点=len(无源) if 锚会话 is None else 无源.index(锚会话)#插入点
        新序=[*无源[:插入点],会话标识值,*无源[插入点:]]#新序
        if 新序!=工作区['sessionIds']:#序真变了
            工作区['sessionIds']=新序#写回
            工作区['updatedAt']=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())#刷新
            广播宿主({'type':'host/workspace-changed','workspace':dict(工作区)})#广播
        return 成功(请求,{'workspace':dict(工作区)})#回视图

    def 归档会话(请求):#归档会话
        """登记并广播。"""
        缺=要求会话(请求)#必须存在
        if 缺 is not None:#未知
            return 缺#失败
        标识=请求['payload']['sessionId']#id
        if 标识 not in 已归档:#尚未归档
            已归档.append(标识)#记下
            广播宿主({'type':'host/archived-sessions-changed','archivedSessionIds':list(已归档)})#广播
        return 成功(请求,{'archivedSessionIds':list(已归档)})#回名单

    def 列预设(请求):#列预设
        """两种 trust。"""
        预设们=[{'id':标识,'trust':预设['trust'],'isDefault':标识==默认预设[0]} for 标识,预设 in 预设图.items()]#每条
        return 成功(请求,{'presets':预设们,'authorable':True,'hasDocument':True})#列表

    def 选预设(请求):#设默认预设
        """记下。"""
        默认预设[0]=请求['payload']['agentPreset']#记下
        return 成功(请求,{'agentPreset':请求['payload']['agentPreset']})#回所选

    def 读预设(请求):#读 YAML 正文
        """查表。"""
        名=请求['payload']['agentPreset']#名
        预设=预设图.get(名)#查表
        if 预设 is None:#未知
            return 失败(请求,{'code':'agent-preset-not-found','message':f'unknown agent preset "{名}"','details':{'agentPreset':名,'available':list(预设图.keys())}})#缺失
        return 成功(请求,{'agentPreset':名,'trust':预设['trust'],'content':预设['content']})#正文

    def 复制预设(请求):#复制为用户预设
        """新名占用则失败。"""
        源名=请求['payload']['from']#源
        新名=请求['payload']['agentPreset']#新名
        源=预设图.get(源名)#查源
        if 源 is None:#未知源
            return 失败(请求,{'code':'agent-preset-not-found','message':f'unknown agent preset "{源名}"','details':{'agentPreset':源名,'available':list(预设图.keys())}})#缺失
        if 新名 in 预设图:#新名占用
            return 失败(请求,{'code':'agent-preset-invalid','message':f'agent preset "{新名}" already exists','details':{'agentPreset':新名,'reason':'already exists'}})#已存在
        预设图[新名]={'trust':'user','content':源['content']}#用户副本
        return 成功(请求,{'agentPreset':新名})#回新名

    def 打开预设文档(请求):#用户预设可打开
        """系统只读。"""
        名=请求['payload']['agentPreset']#名
        已有=预设图.get(名)#查表
        if 已有 is None or 已有['trust']=='system':#缺失或系统
            return 失败(请求,{'code':'agent-preset-read-only','message':f'agent preset "{名}" ships with the deployment','details':{'agentPreset':名,'reason':'it ships with the deployment'}})#只读
        return 成功(请求,{'opened':True})#空操作成功

    def 删预设(请求):#删用户预设
        """系统拒删；未知也当成功。"""
        名=请求['payload']['agentPreset']#名
        已有=预设图.get(名)#查表
        if 已有 is not None and 已有['trust']=='system':#系统只读
            return 失败(请求,{'code':'agent-preset-read-only','message':f'agent preset "{名}" ships with the deployment','details':{'agentPreset':名,'reason':'it ships with the deployment'}})#拒删
        预设图.pop(名,None)#删掉
        return 成功(请求,{})#空成功

    def 列技能(请求):#按会话列
        """两条样本。"""
        缺=要求会话(请求)#必须存在
        if 缺 is not None:#未知
            return 缺#失败
        return 成功(请求,{'skills':[
            {'name':'fixture-demo','description':'fixture 技能样本','whenToUse':'仅供 UI 目录渲染验收','modelInvocable':True},
            {'name':'fixture-user-only','description':'fixture 仅用户技能样本','modelInvocable':False},
        ]})#样本

    def 旧创建目标(请求):#旧目标面 create
        """转规范 Remote。"""
        载荷=请求['payload']#载荷
        体={'objective':载荷['objective']}#规范
        if 载荷.get('maxGoalRounds') is not None:#可选上限
            体['maxGoalRounds']=载荷['maxGoalRounds']#挂
        def 映旧引用(值):#规范 → 旧引用
            """抽出 ref。"""
            return {'ref':{'id':值['ref']['id'],'revision':值['ref']['revision']}}#旧引用
        return 旧目标响应(请求,映射目标结果(创建目标(载荷['sessionId'],体),映旧引用))#信封

    def 旧编辑目标(请求):#旧 edit
        """转规范。"""
        载荷=请求['payload']#载荷
        体={}#可选
        if 载荷.get('objective') is not None:#目标
            体['objective']=载荷['objective']#挂
        if 载荷.get('maxGoalRounds') is not None:#上限
            体['maxGoalRounds']=载荷['maxGoalRounds']#挂
        return 旧目标响应(请求,目标引用结果(编辑目标(载荷['sessionId'],载荷['ref'],体)))#信封

    def 旧暂停目标(请求):#旧 pause
        """转规范。"""
        return 旧目标响应(请求,目标引用结果(暂停目标(请求['payload']['sessionId'],请求['payload']['ref'])))#信封

    def 旧恢复目标(请求):#旧 resume
        """转规范。"""
        return 旧目标响应(请求,目标引用结果(恢复目标(请求['payload']['sessionId'],请求['payload']['ref'])))#信封

    def 旧完成目标(请求):#旧 complete
        """转规范。"""
        return 旧目标响应(请求,目标引用结果(完成目标(请求['payload']['sessionId'],请求['payload']['ref'])))#信封

    def 旧清除目标(请求):#旧 clear
        """转规范。"""
        def 映已清(_值):#规范 → 旧回执
            """cleared true。"""
            return {'cleared':True}#旧回执
        return 旧目标响应(请求,映射目标结果(清除目标(请求['payload']['sessionId'],请求['payload']['ref']),映已清))#信封

    def mux流(_请求,信号):#复用事件流
        """打开基线 + drain。"""
        连接=夹具收件箱()#本连接
        mux连接们.add(连接)#登记

        def 打断():#时序钩用
            """breakNow。"""
            连接.breakNow()#打断

        流打断们.add(打断)#登记
        for 摘要 in 会话们:#跑着的才订阅
            if not 摘要['running']:#停着
                continue#跳过
            日志=日志图.get(摘要['sessionId']) or []#日志
            连接.push({'rpcId':铸造rpc(),'payload':{'type':'session/subscribed','sessionId':摘要['sessionId'],'lastSeq':len(日志)-1}})#订阅
            值们=投影值于(日志)#整包
            for 键 in 值们:#每键一帧
                连接.push({'rpcId':铸造rpc(),'payload':{'type':'session/projection','sessionId':摘要['sessionId'],'key':键,'value':值们[键],'seq':len(日志)-1}})#投影
        if 审批未决[0]:#重放常驻审批
            连接.push({'rpcId':未决审批rpc,'payload':{
                'type':'approval/requested','sessionId':会话标识('fx-alpha'),
                'approvalId':未决审批标识,'toolName':'dangerous_tool',
                'reason':'fixture 常驻审批（可答：批准/拒绝后消失）',
            }})#审批
        if 提问未决[0]:#重放常驻提问
            连接.push({'rpcId':未决提问rpc,'payload':{
                'type':'question/requested','sessionId':会话标识('fx-alpha'),'questions':夹具提问,
            }})#提问
        try:#泵到取消或打断
            yield from 连接.drain(信号)#吐帧
        finally:#摘登记
            流打断们.discard(打断)#摘钩
            mux连接们.discard(连接)#摘连接

    def 宿主流(_请求,信号):#宿主流
        """周期性翻转 fx-gamma。"""
        连接=夹具收件箱()#本连接
        宿主连接们.add(连接)#登记

        def 打断():#时序钩用
            """breakNow。"""
            连接.breakNow()#打断

        流打断们.add(打断)#登记
        停心跳={'v':False}#停旗

        def 心跳():#每 5s 翻转 fx-gamma
            """只动 fx-gamma。"""
            if 停心跳['v']:#已停
                return#完
            伽玛=摘要于(会话标识('fx-gamma'))#常驻
            if 伽玛 is not None:#仍在
                设运行中(伽玛['sessionId'],not 伽玛['running'])#翻转
            定时=threading.Timer(5.0,心跳)#下一拍
            定时.daemon=True#守护
            定时.start()#开
            停心跳['timer']=定时#记下

        首心跳=threading.Timer(5.0,心跳)#五秒后开
        首心跳.daemon=True#守护
        首心跳.start()#开
        停心跳['timer']=首心跳#记下
        try:#泵到取消或打断
            yield from 连接.drain(信号)#吐帧
        finally:#停心跳并摘登记
            停心跳['v']=True#停
            定时=停心跳.get('timer')#现定时
            if 定时 is not None:#可停
                定时.cancel()#停翻转
            流打断们.discard(打断)#摘钩
            宿主连接们.discard(连接)#摘连接

    def 描述设置(请求):#最小就绪设置
        """DeepSeek 命名空间。"""
        return 成功(请求,{'writable':True,'hasDocument':True,'namespaces':[{
            'ns':'llm-deepseek','schema':{},'value':{'apiKeyEnv':'DEEPSEEK_API_KEY'},
            'applies':'live','secrets':[{'path':['apiKey'],'set':False}],'revision':0,
        }]})#描述

    def 打开设置文档(请求):#空操作成功
        """opened。"""
        return 成功(请求,{'opened':True})#成功

    def 更新设置(请求):#只读拒更新
        """settings-rejected。"""
        return 失败(请求,{'code':'settings-rejected','message':'fixture: the minimal readiness settings descriptor is read-only','details':{'ns':请求['payload'].get('ns')}})#拒

    def 替换设置(请求):#只读拒替换
        """settings-rejected。"""
        return 失败(请求,{'code':'settings-rejected','message':'fixture: the minimal readiness settings descriptor is read-only','details':{'ns':请求['payload'].get('ns')}})#拒

    def 变更设置(请求):#无已注册命名空间
        """settings-rejected。"""
        return 失败(请求,{'code':'settings-rejected','message':'fixture: no settings namespaces are registered','details':{'ns':请求['payload'].get('ns')}})#拒

    def 描述凭证(请求):#按引用描述
        """configured 徽章。"""
        引用们=请求['payload'].get('refs') or []#引用
        凭证={}#结果
        for 引用 in 引用们:#每引用
            已配=引用 in 凭证图#是否已配
            项={'configured':已配,'writable':True}#基
            if 已配:#已配则来源为文件
                项['source']='file'#来源
            凭证[引用]=项#记下
        return 成功(请求,{'credentials':凭证})#描述

    def 设凭证(请求):#记为已配
        """写入。"""
        凭证图[请求['payload']['ref']]=True#写入
        return 成功(请求,{})#空成功

    def 清凭证(请求):#清除
        """删掉。"""
        凭证图.pop(请求['payload']['ref'],None)#删
        return 成功(请求,{})#空成功

    def 列提供方(请求):#列提供方
        """四条样本。"""
        return 成功(请求,{'providers':[
            {'provider':'deepseek-official','displayName':'DeepSeek','settingsNs':'llm-deepseek','settingsPath':[],'active':True},
            {'provider':'openai','displayName':'openai','settingsNs':'llm-pi-ai','settingsPath':['providers','openai'],'active':True,'declared':False},
            {'provider':'anthropic','displayName':'anthropic','settingsNs':'llm-pi-ai','settingsPath':['providers','anthropic'],'active':False,'declared':False},
            {'provider':'acme-gateway','displayName':'Acme Gateway','settingsNs':'llm-pi-ai','settingsPath':['providers','acme-gateway'],'active':True,'declared':True},
        ]})#提供方

    def 列llm模型(请求):#分组目录
        """无失败。"""
        return 成功(请求,{'groups':夹具模型分组(),'failures':[]})#目录

    def 探询模型(请求):#探询目录
        """展平为 id/name。"""
        模型们=[]#展平
        for 组 in 夹具模型分组():#每组
            for 模型 in 组.get('models') or []:#每模型
                模型们.append({'id':模型['id'],'name':模型['name']})#id/name
        return 成功(请求,{'models':模型们})#探询

    def 应答(消息):#答常驻审批/提问
        """先 rpcId，再载荷；已结算或未知 id 为 not-pending。"""
        if 消息.get('rpcId')==未决审批rpc:#审批回执
            if not 审批未决[0]:#已结算
                return {'accepted':False,'reason':'not-pending'}#已结算
            结果=消息.get('result') or {}#结果
            if not 结果.get('ok'):#失败体
                return {'accepted':False,'reason':'bad-response'}#坏
            值=结果.get('value') or {}#载荷
            if 值.get('approvalId')!=未决审批标识 or 值.get('outcome') not in ('allowed-once','rejected'):#对不上
                return {'accepted':False,'reason':'bad-response'}#坏回执
            审批未决[0]=False#结算
            广播mux({'type':'approval/resolved','sessionId':会话标识('fx-alpha'),'approvalId':未决审批标识,'outcome':值['outcome']})#已决
            return {'accepted':True}#接受
        if not 提问未决[0] or 消息.get('rpcId')!=未决提问rpc:#不是未决提问
            return {'accepted':False,'reason':'not-pending'}#未知或已结算
        提问未决[0]=False#结算
        结果=消息.get('result') or {}#结果
        广播mux({'type':'question/resolved','sessionId':会话标识('fx-alpha'),'questionRpcId':未决提问rpc,'outcome':'answered' if 结果.get('ok') else 'cancelled'})#已决
        return {'accepted':True}#接受

    def rpc调用(通道,端点,载荷,信号=None):#Remote 面
        """只服务 /api。"""
        if 通道!='/api':#只服务 /api
            raise Exception(f'fixture connection RPC channel {通道!r} is unavailable')#错误串勿改
        参数=(载荷 or {}).get('args') or {}#Remote 参数
        标识=参数.get('agentId')#会话 id
        if 端点=='commands/list':#列命令
            return 列命令(标识)#列表
        if 端点=='commands/execute':#执行
            return 执行命令(标识,参数.get('line') or '')#执行
        if 端点=='goals/create':#创建目标
            请求体={'objective':(参数.get('request') or {}).get('objective')}#规范
            上限=(参数.get('request') or {}).get('maxGoalRounds')#可选
            if 上限 is not None:#有上限
                请求体['maxGoalRounds']=上限#挂
            return 创建目标(标识,请求体)#创建
        if 端点=='goals/edit':#编辑
            return 编辑目标(标识,参数.get('ref') or {},参数.get('request') or {})#编辑
        if 端点=='goals/pause':#暂停
            return 暂停目标(标识,参数.get('ref') or {})#暂停
        if 端点=='goals/resume':#恢复
            return 恢复目标(标识,参数.get('ref') or {})#恢复
        if 端点=='goals/complete':#完成
            return 完成目标(标识,参数.get('ref') or {})#完成
        if 端点=='goals/clear':#清除
            return 清除目标(标识,参数.get('ref') or {})#清除
        raise Exception(f'fixture connection RPC endpoint {端点!r} is unavailable')#未知端点

    api=面对象(#旧一元/流面
        sessions=面对象(
            list=staticmethod(列会话),search=staticmethod(检索会话),create=staticmethod(创建会话),
            rename=staticmethod(重命名会话),fork=staticmethod(分叉会话),history=staticmethod(会话历史),
            models=staticmethod(会话模型),selectModel=staticmethod(选模型),prompt=staticmethod(提示会话),
            attachment=staticmethod(读附件),updateQueue=staticmethod(更新队列),cancel=staticmethod(取消会话),
        ),
        subagents=面对象(
            list=staticmethod(列子智能体),history=staticmethod(子历史),
            prompt=staticmethod(子提示),interrupt=staticmethod(子中断),
        ),
        host=面对象(
            describe=staticmethod(描述宿主),pickDirectory=staticmethod(选目录),
            listDirectory=staticmethod(列目录),createDirectory=staticmethod(建目录),
            openPath=staticmethod(打开路径),
        ),
        workspace=面对象(
            list=staticmethod(列工作区),create=staticmethod(建工作区),rename=staticmethod(改工作区名),
            delete=staticmethod(删工作区),insertBefore=staticmethod(插入工作区前),
            insertSessionBefore=staticmethod(插入会话前),archiveSession=staticmethod(归档会话),
        ),
        agentPresets=面对象(
            list=staticmethod(列预设),select=staticmethod(选预设),read=staticmethod(读预设),
            copy=staticmethod(复制预设),openDocument=staticmethod(打开预设文档),remove=staticmethod(删预设),
        ),
        skills=面对象(list=staticmethod(列技能)),
        goals=面对象(
            create=staticmethod(旧创建目标),edit=staticmethod(旧编辑目标),pause=staticmethod(旧暂停目标),
            resume=staticmethod(旧恢复目标),complete=staticmethod(旧完成目标),clear=staticmethod(旧清除目标),
        ),
        events=面对象(mux=staticmethod(mux流),host=staticmethod(宿主流)),
        settings=面对象(
            describe=staticmethod(描述设置),openDocument=staticmethod(打开设置文档),
            update=staticmethod(更新设置),replace=staticmethod(替换设置),mutate=staticmethod(变更设置),
        ),
        credentials=面对象(
            describe=staticmethod(描述凭证),set=staticmethod(设凭证),unset=staticmethod(清凭证),
        ),
        llm=面对象(
            providers=staticmethod(列提供方),models=staticmethod(列llm模型),
            discoverModels=staticmethod(探询模型),
        ),
        respond=staticmethod(应答),
        downloads=面对象(sessionLog=staticmethod(_会话导出桩)),
    )#结束 api
    rpc=面对象(call=staticmethod(rpc调用))#Remote 面
    return 面对象(api=api,rpc=rpc)#双面世界

def _会话导出桩():#下载 stub
    """fixture 不服务导出。"""
    return {'status':404,'body':'fixture mode does not serve session export'}#404

class 夹具接口客户端(抽象接口客户端):#无 HTTP 的假客户端
    """覆盖协议级虚方法，直接派进内存 ApiProxy；仍自造 rpcId 并喂观察 tap。"""

    def __init__(自身):#从 location 读分支
        """造世界并挂 rpc 与 IApiClient 形命名空间（供连接控制器走 host.describe / events.mux）。"""
        super().__init__()#抽象基类
        世界=造夹具世界(自定位读夹具选项())#造世界
        自身._api=世界.api#旧面
        自身.rpc=世界.rpc#Remote 面
        客户端=自身#捕获
        def 一元(方法键):#载荷直传闭包
            def 调用(载荷=None,信号=None,_超时=None):#直传
                return 客户端.callUnary(方法键,载荷 or {},信号)#走协议
            return 调用#闭包
        自身.host=面对象(#宿主域：连接控制器握手用
            describe=staticmethod(一元('host.describe')),
            pickDirectory=staticmethod(一元('host.pickDirectory')),
            listDirectory=staticmethod(一元('host.listDirectory')),
            createDirectory=staticmethod(一元('host.createDirectory')),
            openPath=staticmethod(一元('host.openPath')),
        )#结束宿主
        def 复用(载荷=None,信号=None,打开回调=None):#mux
            return 客户端.openMux(载荷 or {},信号,打开回调)#开
        def 宿主流(载荷=None,信号=None,打开回调=None):#host 流
            return 客户端.openHost(载荷 or {},信号,打开回调)#开
        自身.events=面对象(mux=staticmethod(复用),host=staticmethod(宿主流))#事件流
        自身.sessions=面对象(**{名:staticmethod(一元(键)) for 名,键 in [#会话域
            ('list','session.list'),('search','session.search'),('create','session.create'),
            ('history','session.history'),('models','session.models'),('selectModel','session.selectModel'),
            ('rename','session.rename'),('fork','session.fork'),('prompt','session.prompt'),
            ('attachment','session.attachment'),('updateQueue','session.updateQueue'),('cancel','session.cancel'),
        ]})#结束会话

    def doFetch(自身,*位置参数,**关键字参数):#必须不可达
        """Fixture 覆盖全部协议路径。"""
        raise Exception('FixtureApiClient overrides all protocol paths; doFetch must be unreachable')#错误串勿改

    def callUnary(自身,方法,载荷,信号=None,超时策略='default'):#一元
        """自造信封、打 tap、派进内存、再打响应 tap。"""
        请求=造rpc请求(载荷)#自造 rpcId
        完整={'type':'client-request','rpcId':请求['rpcId'],'method':方法,'payload':载荷}#完整形态
        if hasattr(自身,'onEnvelope'):#打 tap
            自身.onEnvelope(完整)#旁路
        响应=自身._派发(方法,请求,信号 if 信号 is not None else {'aborted':False})#派进内存
        完整响应={'type':'server-response','rpcId':响应['rpcId'],'result':响应['result']}#完整响应
        if hasattr(自身,'onEnvelope'):#打 tap
            自身.onEnvelope(完整响应)#旁路
        return 响应#给调用方

    def _派发(自身,方法,请求,信号):#方法键 → 实现
        """穷举 RpcMethodMap。"""
        api=自身._api#旧面
        if 方法=='session.list': return api.sessions.list(请求)#列会话
        if 方法=='session.search': return api.sessions.search(请求,信号)#检索
        if 方法=='session.create': return api.sessions.create(请求)#创建
        if 方法=='session.history': return api.sessions.history(请求)#历史
        if 方法=='session.models': return api.sessions.models(请求)#模型目录
        if 方法=='session.selectModel': return api.sessions.selectModel(请求)#选模型
        if 方法=='session.rename': return api.sessions.rename(请求)#改标题
        if 方法=='session.fork': return api.sessions.fork(请求)#分叉
        if 方法=='session.prompt': return api.sessions.prompt(请求)#提问
        if 方法=='session.attachment': return api.sessions.attachment(请求)#附件
        if 方法=='session.updateQueue': return api.sessions.updateQueue(请求)#队列
        if 方法=='session.cancel': return api.sessions.cancel(请求)#取消
        if 方法=='subagent.list': return api.subagents.list(请求)#列子智能体
        if 方法=='subagent.history': return api.subagents.history(请求)#子历史
        if 方法=='subagent.prompt': return api.subagents.prompt(请求)#子提问
        if 方法=='subagent.interrupt': return api.subagents.interrupt(请求)#子中断
        if 方法=='host.describe': return api.host.describe(请求)#宿主描述
        if 方法=='host.pickDirectory': return api.host.pickDirectory(请求)#选目录
        if 方法=='host.listDirectory': return api.host.listDirectory(请求)#列目录
        if 方法=='host.createDirectory': return api.host.createDirectory(请求)#建目录
        if 方法=='host.openPath': return api.host.openPath(请求)#打开路径
        if 方法=='workspace.list': return api.workspace.list(请求)#列工作区
        if 方法=='workspace.create': return api.workspace.create(请求)#建工作区
        if 方法=='workspace.rename': return api.workspace.rename(请求)#改名
        if 方法=='workspace.delete': return api.workspace.delete(请求)#删除
        if 方法=='workspace.insertBefore': return api.workspace.insertBefore(请求)#重排
        if 方法=='workspace.insertSessionBefore': return api.workspace.insertSessionBefore(请求)#会话重排
        if 方法=='workspace.archiveSession': return api.workspace.archiveSession(请求)#归档
        if 方法=='skill.list': return api.skills.list(请求)#列技能
        if 方法=='agentPreset.list': return api.agentPresets.list(请求)#列预设
        if 方法=='agentPreset.select': return api.agentPresets.select(请求)#选预设
        if 方法=='agentPreset.read': return api.agentPresets.read(请求)#读预设
        if 方法=='agentPreset.copy': return api.agentPresets.copy(请求)#复制
        if 方法=='agentPreset.openDocument': return api.agentPresets.openDocument(请求)#打开文档
        if 方法=='agentPreset.remove': return api.agentPresets.remove(请求)#删除预设
        if 方法=='goal.create': return api.goals.create(请求)#创建目标
        if 方法=='goal.edit': return api.goals.edit(请求)#编辑目标
        if 方法=='goal.pause': return api.goals.pause(请求)#暂停
        if 方法=='goal.resume': return api.goals.resume(请求)#恢复
        if 方法=='goal.complete': return api.goals.complete(请求)#完成
        if 方法=='goal.clear': return api.goals.clear(请求)#清除
        if 方法=='settings.describe': return api.settings.describe(请求)#设置描述
        if 方法=='settings.openDocument': return api.settings.openDocument(请求)#打开设置
        if 方法=='settings.update': return api.settings.update(请求)#更新
        if 方法=='settings.replace': return api.settings.replace(请求)#替换
        if 方法=='settings.mutate': return api.settings.mutate(请求)#变更
        if 方法=='credentials.describe': return api.credentials.describe(请求)#凭证描述
        if 方法=='credentials.set': return api.credentials.set(请求)#设置凭证
        if 方法=='credentials.unset': return api.credentials.unset(请求)#清除凭证
        if 方法=='llm.providers': return api.llm.providers(请求)#提供方
        if 方法=='llm.models': return api.llm.models(请求)#模型
        if 方法=='llm.discoverModels': return api.llm.discoverModels(请求)#发现
        raise Exception(f'fixture: unknown unary method {方法!r}')#未知

    def openMux(自身,载荷,信号,打开回调=None):#mux
        """打开 mux 流并打 tap。"""
        return 自身._点流(自身._api.events.mux(造rpc请求(载荷),信号),打开回调)#自造请求后泵

    def openHost(自身,载荷,信号,打开回调=None):#host
        """打开宿主流并打 tap。"""
        return 自身._点流(自身._api.events.host(造rpc请求(载荷),信号),打开回调)#自造请求后泵

    def _点流(自身,流,打开回调=None):#tap 生成器
        """迭代一开始即视为已建立。"""
        if callable(打开回调):#有回调
            打开回调()#通知已开
        for 信封 in 流:#逐帧
            完整={'type':'server-request','rpcId':信封['rpcId'],'method':信封['payload']['type'],'payload':信封['payload']}#完整形态
            if hasattr(自身,'onEnvelope'):#打 tap
                自身.onEnvelope(完整)#旁路
            yield 信封#交给泵

    def respond(自身,消息,信号=None):#应答
        """无 HTTP POST，进内存实现。"""
        if hasattr(自身,'onEnvelope'):#打 tap
            自身.onEnvelope(消息)#旁路
        return 自身._api.respond(消息)#进内存

FixtureApiClient=夹具接口客户端#上游名
