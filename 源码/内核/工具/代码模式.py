import math,threading
from threading import Event as 事件#本轮取消通道
from ...基础设施.通用工具 import (
    紧凑json编码,启动守护线程,
)

class 中止信号(事件):
    '取消通道。Event 本身就是信号'
    def __init__(自身):
        '创建未中止的通道'
        事件.__init__(自身)#未置位
        自身.原因=None#跨包读取的中止原因

    def 等待(自身):
        '阻塞到中止'
        自身.wait()#阻塞

class 中止控制器:
    '发出中止的控制器'
    def __init__(自身):
        '创建配套信号'
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        '中止配套信号，只生效一次'
        if 自身.信号.is_set():#已经中止
            return#只生效一次
        自身.信号.原因=原因#记下原因
        自身.信号.set()#置位

def 已中止(信号):
    '信号是否已中止。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 已置位

def 若已中止则抛出(信号):
    '已中止则抛出承载原因的异常'
    if not 已中止(信号):#无信号或仍活着
        return#仍活着
    if 信号.原因 is not None:#有承载异常
        raise 信号.原因#抛出
    raise 代码模式错误('已中止')#默认中止
from ...基础设施.js特性 import PromiseEX as 期约#期约
from ...模型后端.llm import 调用标识,深冻结,创建用户消息#导入调用 id、冻结与用户消息
from ...沙盒.沙盒 import 批准升级,校验升级参数,升级目标#导入沙箱升级
from ..会话 import 快照json值#导入无损 JSON 快照
from .模式 import 定义工具,参数模式规格转json模式#导入工具定义器与参数编译
from .异常 import 代码模式错误,代码运行失败错误

__all__=(
    '运行代码名','sdk段顺序','代码sdk语言',
    '创建运行代码工具','代码运行失败错误',
    '已中止','若已中止则抛出','中止控制器','代码模式错误',
)#仅中文公开名

运行代码名='run_code'#传输工具名
sdk段顺序=5000#SDK 段顺序，对齐 TOOLS_SDK
json缩进='  '#两空格 JSON 呈现
json缩进上限=10#总缩进上限

typescript风味={
    'description':(
        'Execute a TypeScript program against the available tools. Takes two required '
        +'arguments: `description`, a short summary of what the program does, and `code`, '
        +'the BODY of an async function (erasable syntax only; top-level `await` and '
        +'`return` work). Call tools as `await tools.name(args)` per the declarations in the system '
        +'prompt. Only what you print or return is program output — curate it. Image-bearing '
        +'subtool results are attached after the run.'
    ),#工具描述
    'codeDescription':'The program: the body of an async TypeScript function.',#代码参数描述
}#TS 风味
python风味={
    'description':(
        'Execute a Python program against the available tools. Takes two required '
        +'arguments: `description`, a short summary of what the program does, and `code`, '
        +'the BODY of an async function (top-level `await` and `return` work). Call tools as '
        +'`await tools.name(args)` per the declarations in the system prompt. Use '
        +'`print(...)` and/or `return <value>` for program output — curate it. Image-bearing '
        +'subtool results are attached after the run.'
    ),#工具描述
    'codeDescription':'The program: the body of an async Python function.',#代码参数描述
}#Python 风味
运行代码风味={
    'typescript':typescript风味,#TS
    'python':python风味,#Python
}#风味表
运行代码描述参数文案=(
    'Clear, concise description of what this program does in active voice, '
    +'5-10 words (shown in the UI). Provide `description` before `code` in the arguments. '
    +'Examples: "Count TODO markers across packages"; '
    +'"Read failing test and its fixture"; "Rename config key in every cordis.yml".'
)#description 参数文案
运行代码控件={
    'timeoutMs':{'type':'number','description':'Positive elapsed-time budget in milliseconds, capped by the deployment maximum.'},#超时
    'sandbox_permissions':{'type':'string','enum':list(升级目标),'description':'Wider sandbox mode for this complete program execution; requires justification and approval.'},#沙箱权限
    'justification':{'type':'string','description':'Reason this complete program needs wider access, shown to the user for approval. Use the language of the user’s current request.'},#理由
}#控件参数
升级指引文案=' A sandbox escalation approves this complete program for one execution only. Nested tools retain their own policies and approvals. Request wider access only after evidence of a denial. Earlier effects may already have completed: inspect them before explicitly retrying. Programs are never replayed automatically.'#升级指引

def 控制参数(运行时):
    '按运行时能力裁剪 timeoutMs 与沙箱升级字段'
    if 运行时 is None:
        return dict(运行代码控件)#目录读者给全套
    结果={}#按能力收录
    截止=运行时.超时()#数值截止
    if 截止 is not None:
        超时=dict(运行代码控件['timeoutMs'])#拷贝
        超时['description']='Positive elapsed-time budget in milliseconds, including nested tool and approval waits. Default '+str(截止['defaultMs'])+'; capped at '+str(截止['maxMs'])+'. Zero does not disable the deadline.'#带上下限
        结果['timeoutMs']=超时#收录超时
    if 运行时.沙箱模式() is not None:
        结果['sandbox_permissions']=运行代码控件['sandbox_permissions']#收录权限
        结果['justification']=运行代码控件['justification']#收录理由
    return 结果#已裁剪

def 升级指引(运行时):
    '运行时有文件政策时返回升级指引，否则空串'
    if 运行时 is None:
        return ''#无运行时
    if 运行时.沙箱模式() is None:
        return ''#无围栏
    return 升级指引文案#指引

def 解析风味(窥探运行时):
    '按已加载运行时的语言解析 run_code 风味'
    运行时=窥探运行时()#窥探运行时
    if 运行时 is None:
        return typescript风味#TS 回落
    语言=运行时.语言()#语言名
    if 语言 not in 运行代码风味:
        已知=', '.join(紧凑json编码(名) for 名 in 运行代码风味.keys())#已知语言
        raise 代码模式错误('dsh-tools: no run_code schema flavor registered for runtime language '+紧凑json编码(语言)+' (known: '+已知+')')#大声失败
    return 运行代码风味[语言]#该语言风味

def 错误文本(错误):
    '从抛出值取人类可读消息'
    if isinstance(错误,Exception):
        消息=getattr(错误,'message',None)#Error.message
        if isinstance(消息,str):
            return 消息#用它
        if 错误.args:
            return str(错误.args[0])#args
        return str(错误)#字符串化
    return str(错误)#其余

def json归一参数(值):
    '把一次绑定调用的参数快照成无损 JSON，再对这份已脱离值再快照一次'
    try:
        快照=快照json值(值)#脱离
    except Exception as 错误:
        raise 代码模式错误('tool arguments must be lossless JSON: '+错误文本(错误))#参数必须无损
    if 快照 is None:
        raise 代码模式错误('tool arguments must be lossless JSON (call the tool with an arguments object, e.g. `{}`)')#必须是参数
    已记=快照json值(快照)#再快照一份给日志
    if 已记 is None:
        raise 代码模式错误('tool arguments could not be detached for durable logging')#日志副本失败
    return {'dispatched':快照,'logged':已记}#派发用第一份，日志用第二份

def 渲染json数字(值):
    '把数字渲染成十进制文本，匹配 JS String(number) 的输出（布尔为 true/false）'
    if isinstance(值,bool):
        return 'true' if 值 else 'false'#布尔到不了这里
    if isinstance(值,int):
        return str(值)#整数
    if isinstance(值,float) and 值.is_integer():
        return str(int(值))#整值浮点
    return str(值)#浮点

def 渲染json值(值):
    '渲染一个非字符串 JSON 根，不用递归遍历，也不让缩进无界增长'
    块列表=[]#输出块
    任务列表=[{'kind':'value','value':值,'depth':0,'compact':False}]#从根值起步
    任务=任务列表.pop() if 任务列表 else None#弹出任务
    while 任务 is not None:
        if 任务['kind']=='text':
            块列表.append(任务['text'])#直接写出
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        当前=任务['value']#当前值
        if 当前 is None:
            块列表.append('null')#null
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if 当前 is True:
            块列表.append('true')#布尔真
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if 当前 is False:
            块列表.append('false')#布尔假
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):
            块列表.append(渲染json数字(当前))#数字
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if isinstance(当前,str):
            块列表.append(紧凑json编码(当前))#JSON 引号
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        紧凑=任务['compact'] or (任务['depth']+1)*len(json缩进)>json缩进上限#超上限则紧凑
        子深度=任务['depth']+1#子深度
        if isinstance(当前,list):
            块列表.append('[')#开括号
            if len(当前)==0:
                块列表.append(']')#立刻闭合
                任务=任务列表.pop() if 任务列表 else None#下一任务
                continue
            任务列表.append({'kind':'text','text':']' if 紧凑 else '\n'+json缩进*任务['depth']+']'})#闭合
            下标=len(当前)-1#倒序入栈以正序写出
            while 下标>=0:
                项=当前[下标]#元素
                if 项 is None and 下标>=len(当前):
                    raise 代码模式错误('cannot render a sparse JSON array')#稀疏数组
                任务列表.append({'kind':'value','value':项,'depth':子深度,'compact':紧凑})#元素值
                if 紧凑:
                    分隔='' if 下标==0 else ','#首元素无逗号
                else:
                    分隔=('\n' if 下标==0 else ',\n')+json缩进*子深度#换行加缩进
                任务列表.append({'kind':'text','text':分隔})#分隔
                下标-=1#前进
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        键列表=list(当前.keys())#对象键
        块列表.append('{')#开花括号
        if len(键列表)==0:
            块列表.append('}')#立刻闭合
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        任务列表.append({'kind':'text','text':'}' if 紧凑 else '\n'+json缩进*任务['depth']+'}'})#闭合
        下标=len(键列表)-1#倒序入栈
        while 下标>=0:
            键=键列表[下标]#键
            if 键 is None:
                raise 代码模式错误('cannot render a missing JSON object key')#键缺失
            项=当前[键]#属性值
            if 项 is None and 键 not in 当前:
                raise 代码模式错误('cannot render an undefined JSON object property')#属性 undefined
            任务列表.append({'kind':'value','value':项,'depth':子深度,'compact':紧凑})#属性值
            if 紧凑:
                前= '' if 下标==0 else ','#首键无逗号
                文本=前+紧凑json编码(键)+':'#键后紧跟冒号
            else:
                前='\n' if 下标==0 else ',\n'#换行
                文本=前+json缩进*子深度+紧凑json编码(键)+': '#换行缩进加冒号空格
            任务列表.append({'kind':'text','text':文本})#键与分隔
            下标-=1#前进
        任务=任务列表.pop() if 任务列表 else None#下一任务
    return ''.join(块列表)#拼成字符串

def 渲染完成值(值):
    '把一次程序完成值渲染成面向模型的结果文本'
    if isinstance(值,str):
        return 值#字符串原样
    return 渲染json值(值)#其余走 JSON

class 带取值定义(dict):
    '允许 description/parameters 以取值器发出'
    def __init__(自身,源,描述取值=None,参数取值=None):
        '记下静态字段与取值器'
        super().__init__(源)#拷贝静态
        自身._描述取值=描述取值#描述 getter
        自身._参数取值=参数取值#参数 getter
    def __getitem__(自身,键):
        '读字段，取值器优先'
        if 键=='description' and 自身._描述取值 is not None:
            return 自身._描述取值()#发出时读风味
        if 键=='parameters' and 自身._参数取值 is not None:
            return 自身._参数取值()#发出时重编译
        return super().__getitem__(键)#静态字段
    def get(自身,键,缺省=None):
        '对齐 dict.get，走取值器'
        if 键=='description' and 自身._描述取值 is not None:
            return 自身._描述取值()#描述
        if 键=='parameters' and 自身._参数取值 is not None:
            return 自身._参数取值()#参数
        return super().get(键,缺省)#静态

def 创建运行代码工具(注册表,选项):
    '构建 run_code 工具定义'
    要求运行时=选项['requireRuntime']#必需运行时
    窥探运行时=选项['peekRuntime']#窥探运行时
    窥探审批=选项['peekApprover']#窥探审批通道
    解析沙箱政策=选项['resolveSandboxPolicy']#解析站立政策
    解析工作目录=选项['resolveWorkingDirectory']#解析工作目录
    并行上限=选项['maxParallel']#并行上限
    整形派发日志=选项['shapeDispatchLog']#整形日志内容
    def 渲染运行代码输出(_参数,值):
        '渲染模型文本'
        return _渲染运行代码(值,窥探运行时)#委托
    def 跑传输(参数,执行):
        '跑程序'
        return 执行运行代码(注册表,要求运行时,窥探审批,解析沙箱政策,解析工作目录,并行上限,整形派发日志,参数,执行)#委托
    def 呈现运行代码调用(参数):
        '待处理呈现'
        return {
            'card':'generic',#通用卡片
            'title':参数['description'],#UI 标题
            'kind':'execute',#执行类
            'rawInput':参数['code'],#程序体
        }#呈现卡片
    静态参数={
        'description':{
            'type':'string',#字符串
            'required':True,#必填
            'description':运行代码描述参数文案,#语言无关文案
        },#UI 标签
        'code':{'type':'string','required':True,'description':typescript风味['codeDescription']},#代码体
    }#必填参数
    静态参数.update(运行代码控件)#控件字段
    定义=定义工具({
        'name':运行代码名,#传输名
        'description':typescript风味['description'],#占位描述
        'parameters':静态参数,#含控件
        'output':{
            'schema':{
                'type':'object',#对象
                'additionalProperties':False,#封闭
                'properties':{
                    'logs':{'type':'array','required':True,'items':{'type':'string'}},#捕获日志
                    'result':{'type':'json'},#可选返回值
                    'sandbox':{
                        'type':'object',#对象
                        'additionalProperties':False,#封闭
                        'properties':{
                            'mode':{'type':'string','required':True,'enum':['read-only','workspace-write','danger-full-access']},#沙箱模式
                            'denied':{'type':'boolean','required':True},#是否拒绝
                            'enforcement':{'type':'string','enum':['full','partial']},#强制程度
                        },#字段
                    },#沙箱投影
                },#字段
            },#schema
            'render':渲染运行代码输出,#渲染模型文本
        },#规范输出
        'execute':跑传输,#跑程序
        'presentCall':呈现运行代码调用,#待处理呈现
    })#经 defineTool 编译
    def 读描述():
        '发出时读风味描述、执行说明与升级指引'
        运行时=窥探运行时()#当前运行时
        说明=运行时.执行说明() if 运行时 is not None else ''#提供方说明
        文案=解析风味(窥探运行时)['description']#当前风味
        if 说明:
            文案=文案+' '+说明#接说明
        if 运行时 is not None:
            文案=文案+" Each program starts in the Session's current directory. Running programs keep their initial directory."#工作目录句
        return 文案+升级指引(运行时)#接升级指引
    def 读参数():
        '按当前风味重编译参数模式'
        规格={
            'description':{'type':'string','required':True,'description':运行代码描述参数文案},#标签文案不变
            'code':{'type':'string','required':True,'description':解析风味(窥探运行时)['codeDescription']},#代码描述随语言
        }#必填
        规格.update(控制参数(窥探运行时()))#按能力收录控件
        return 参数模式规格转json模式(规格)#投影成模型可见模式
    return 带取值定义(定义,读描述,读参数)#替换 description/parameters

def _渲染运行代码(值,窥探运行时):
    '渲染 run_code 规范输出'
    渲染='' if 'result' not in 值 else 渲染完成值(值['result'])#返回值文本
    段列表=[项 for 项 in ['\n'.join(值['logs']),渲染] if len(项)>0]#去掉空段
    沙箱=值.get('sandbox')#沙箱投影
    if isinstance(沙箱,dict) and 沙箱.get('enforcement')=='partial':
        段列表.append('File sandbox enforcement is partial on this host.')#部分强制
    if isinstance(沙箱,dict) and 沙箱.get('denied'):
        段列表.append('The '+str(沙箱.get('mode'))+' file sandbox denied an operation.'+升级指引(窥探运行时()))#拒绝加指引
    文本='\n'.join(段列表) if len(段列表)>0 else '(run_code completed with no output)'#无输出时的哨兵句
    return [{'type':'text','text':文本}]#文本块

def 执行运行代码(注册表,要求运行时,窥探审批,解析沙箱政策,解析工作目录,并行上限,整形派发日志,参数,执行):
    '跑一次 run_code 程序并排空子派发'
    from . import 调度器符号#延迟导入
    if len(参数['description'].strip())==0:
        raise 代码模式错误('invalid description: expected a non-empty string')#必须非空
    运行时=要求运行时()#组装/执行时必需运行时
    校验升级参数(参数.get('sandbox_permissions'),参数.get('justification'))#配对校验
    if 参数.get('timeoutMs') is not None and 运行时.超时() is None:
        raise 代码模式错误('timeoutMs is not available for this PTC runtime')#运行时无截止
    超时毫秒=参数.get('timeoutMs')#可选截止
    if 超时毫秒 is not None:
        if isinstance(超时毫秒,bool) or (not isinstance(超时毫秒,(int,float))) or (not math.isfinite(超时毫秒)) or 超时毫秒<=0:
            raise 代码模式错误('invalid timeoutMs: expected a positive finite number')#必须正有限
    站立政策=None if 运行时.沙箱模式() is None else 解析沙箱政策(执行)#有围栏才解析
    政策=站立政策#本次政策
    if 参数.get('sandbox_permissions') is not None and 参数.get('justification') is not None:
        if 站立政策 is None:
            raise 代码模式错误('sandbox_permissions is not available for this PTC runtime')#运行时无围栏
        批准模式=批准升级({
            'requestedMode':参数['sandbox_permissions'],#目标模式
            'justification':参数['justification'],#理由
            'effectiveMode':站立政策['mode'],#当前模式
            'subject':'program',#主语
        },{
            'approver':窥探审批(),#审批通道
            'agent':执行.get('agent'),#智能体
            'callId':执行['callId'],#调用 id
            'toolName':运行代码名,#传输名
            'signal':执行.get('signal'),#取消信号
        })#一次批准
        政策=dict(站立政策)#拷贝站立
        政策['mode']=批准模式#盖上批准模式
    工作目录=解析工作目录(执行)#有智能体时解析当前目录
    若已中止则抛出(执行.get('signal'))#解析后若已取消则停
    本轮=中止控制器()#本轮控制器
    外层信号=执行['signal'] if 'signal' in 执行 else None#外层取消通道
    def 跟外层中止():
        '外层中止则跟中止'
        if 外层信号 is None:
            return#无外层
        外层信号.等待()#阻塞到外层置位
        本轮.中止(外层信号.原因)#转发异常原因
    if 已中止(外层信号):
        本轮.中止(外层信号.原因)#已中止则立刻跟
    elif 外层信号 is not None:
        启动守护线程(跟外层中止)#跟外层中止线程
    子调用序号=0#子调用序号
    未开始队列=[]#未开始队列
    在飞=set()#在飞体
    日志工作=set()#日志副作用
    提交队列=[]#提交序队列
    独占活动=False#独占屏障是否立着
    驾驶中=False#驱动车道是否在跑
    驾驶任务=None#真正开跑后才是期约
    条件=threading.Condition()#队列临界区
    唤醒槽=[None]#车道睡眠期约的解决函数
    def 唤醒():
        '唤醒驱动'
        with 条件:
            释放=唤醒槽[0]#取走本轮解决
            唤醒槽[0]=None#避免重复解决
        if 释放 is not None:
            释放(None)#解决睡眠期约
    def 本轮已结束():
        '本轮是否已结束'
        return 已中止(本轮.信号)#现场读取
    def 驱动():
        '唯一有序车道'
        nonlocal 驾驶中,驾驶任务,独占活动
        车道门=threading.Lock()#串行车道步
        车道进行中=False#车道函数是否在栈上
        车道待重入=False#让出期间又有人要跑一轮
        提交条目盒=[None]#本轮正在提交的条目
        开始条目盒=[None]#本轮正在开始的条目
        def 车道结束():
            '车道静止，兑现驾驶期约'
            nonlocal 驾驶中
            with 条件:
                if not 驾驶中:
                    return#已经结束
                驾驶中=False#释放占位
                唤醒槽[0]=None#丢掉未睡的解决
            驾驶任务.解决(None)#静止
        def 车道失败(错误):
            '车道失败，拒绝驾驶期约'
            nonlocal 驾驶中
            with 条件:
                if not 驾驶中:
                    return#已经结束
                驾驶中=False#释放占位
                唤醒槽[0]=None#丢掉未睡的解决
            驾驶任务.拒绝(错误)#失败
        def 挂上唤醒(解决,拒绝回调):
            '把本轮睡眠期约的解决收进槽'
            唤醒槽[0]=解决#稍后唤醒时调用
        def 提交后(结算值):
            '提交落定后放下独占屏障并再跑车道'
            nonlocal 独占活动
            条目=提交条目盒[0]#本轮提交
            if 条目 is not None and 条目.get('mode')=='exclusive':
                独占活动=False#放下独占屏障
            进入车道()#继续
        def 开始后(结算值):
            '有序开始已返回。预落定没有在飞期约'
            条目=开始条目盒[0]#本轮开始
            飞行=条目['flight']#未派发则没有在飞期约
            if 飞行 is None:#预落定，没有要等的体
                进入车道()#继续
                return
            在飞.add(飞行)#先入池，最终回调即使同步也能摘掉
            def 本条离池(落定值=None,任务=飞行):
                '这条体离池并唤醒'
                在飞.discard(任务)#离池
                唤醒()#唤醒车道
            飞行.最终(本条离池)#成败都离池
            进入车道()#不等体，继续车道
        def 车道一步():
            '车道一轮。让出=已挂钩期约；结束=静止'
            nonlocal 独占活动
            while True:
                可提交=None#提交队头
                可开始=None#未开始队头
                模式=None#分类
                要放弃=None#已中止的未开始者
                要睡=False#本轮无事可做
                静止=False#队列与在飞都空
                with 条件:
                    睡眠=期约(挂上唤醒)#检查前先挂上唤醒
                    if len(提交队列)>0 and 提交队列[0]['settled']:
                        可提交=提交队列.pop(0)#出队
                    elif len(未开始队列)>0:
                        队头=未开始队列[0]#未开始队头
                        if 本轮已结束():
                            未开始队列.pop(0)#出队
                            要放弃=队头#锁外放弃
                        else:
                            模式=队头['classify']()#当前分类
                            有槽=(not 独占活动) and (len(在飞)==0 if 模式=='exclusive' else len(在飞)<并行上限)#独占要空池，并行要低于上限
                            if 有槽:
                                可开始=未开始队列.pop(0)#出未开始队
                    if 可提交 is None and 可开始 is None and 要放弃 is None:
                        if len(未开始队列)==0 and len(提交队列)==0 and len(在飞)==0:
                            唤醒槽[0]=None#不再睡
                            静止=True#锁外结束
                        else:
                            要睡=True#等落定或新提交
                if 静止:
                    车道结束()#静止
                    return '结束'
                if 要放弃 is not None:
                    要放弃['abandon']()#放弃未开始者
                    continue#再看队列
                if 要睡:
                    睡眠.然后(进入车道).捕获(车道失败)#睡到被唤醒
                    return '让出'
                if 可提交 is not None:
                    提交条目盒[0]=可提交#提交后读取
                    可提交['commit']().然后(提交后).捕获(车道失败)#等有序提交
                    return '让出'
                if 模式=='exclusive':
                    独占活动=True#立独占屏障
                可开始['mode']=模式#记下开始分类
                提交队列.append(可开始)#入提交序
                开始条目盒[0]=可开始#开始后读取
                可开始['start']().然后(开始后).捕获(车道失败)#等有序开始
                return '让出'
        def 进入车道(落定值=None):
            '串行进入车道。已经在跑则只登记重入'
            nonlocal 车道进行中,车道待重入
            if not 驾驶中:
                return#驾驶期约已结束
            with 车道门:
                if 车道进行中:
                    车道待重入=True#当前这轮返回后续跑
                    return
                车道进行中=True#占住车道
            while True:
                try:
                    动作=车道一步()#一轮
                except BaseException as 错误:
                    车道失败(错误)#收进驾驶期约
                    动作='结束'
                with 车道门:
                    if 动作=='让出' and 车道待重入:
                        车道待重入=False#同步回调登记的下一轮
                        continue
                    车道待重入=False#本段结束
                    车道进行中=False#放开车道
                    return
        with 条件:
            if 驾驶中:
                return 驾驶任务#已在跑则复用
            驾驶任务=期约()#真正开跑后才是期约
            驾驶中=True#与期约同一临界区，避免并发拿到空占位
        进入车道()#开跑
        return 驾驶任务
    def 排空派发():
        '每次派发都已落定并提交'
        排空落定=threading.Event()#驾驶与日志都排空后放行
        排空错误=[None]#排空失败
        def 排空失败(错误):
            '驾驶或日志期约拒绝'
            排空错误[0]=错误#记下
            排空落定.set()#放行
        def 再排日志(结算值=None):
            '日志副作用清空后放行，否则再等一轮'
            if len(日志工作)==0:
                排空落定.set()#已空
                return
            期约.全部已结算(list(日志工作)).然后(再排日志).捕获(排空失败)#本轮都结算后再看
        驱动().然后(再排日志).捕获(排空失败)#先等到车道静止
        排空落定.wait()#调用方要同步结果
        if 排空错误[0] is not None:
            raise 排空错误[0]#原样抛出
    def 绑定(模式):
        '绑定一个工具'
        名称=模式['name']#工具名
        def 调用(原始参数):
            '一次 SDK 子派发'
            nonlocal 子调用序号
            if 本轮已结束():
                raise 代码模式错误('run_code run is over ('+str(本轮.信号.原因)+'); '+名称+' not dispatched')#不再派发
            归一=json归一参数(原始参数)#派发/日志两份快照
            子调用序号+=1#子调用序号
            子调用号=调用标识(str(执行['callId'])+':ptc:'+str(子调用序号))#确定性子 id
            输入={
                'callId':子调用号,#子调用 id
                'rootCallId':执行['rootCallId'],#根调用
                'name':名称,#工具名
                'schema':模式,#绑定期模式，不入日志
                'arguments':归一['dispatched'],#派发副本
                'parent':执行['token'],#外层 token
                'signal':本轮.信号,#本轮信号
            }#子执行输入
            if 'agent' in 执行 and 执行['agent'] is not None:
                输入['agent']=执行['agent']#有智能体则带上
            调度器=注册表[调度器符号]#分阶段调度器
            结局任务=期约()#程序可见结局
            停住盒=[None]#停住的结局
            已准备盒=[None]#本轮准备，记下停住与开始同级
            日志链接盒=[None]#本条日志期约，离集与落定同级
            提交完成盒=[None]#本轮提交期约，回压与提交同级
            def 日志离集(落定值=None):
                '落定后离集'
                日志工作.discard(日志链接盒[0])#离集
            def 落定(结果):
                '把结局交给程序并记日志'
                if 结果['isError']:
                    结局任务.解决({'isError':True,'message':结果['error']['message']})#程序可见错误
                else:
                    结局任务.解决({'isError':False,'value':结果['value']})#规范值
                智能体=执行['agent'] if 'agent' in 执行 else None#记日志需要会话
                if 智能体 is None:
                    return#无智能体则不追加
                日志任务=期约()#日志副作用
                def 日志体():
                    '日志副作用'
                    try:
                        已记=整形派发日志({
                            'exec':执行,#父执行
                            'agent':智能体,#智能体
                            'subCallId':子调用号,#子 id
                            'name':名称,#工具名
                            'isError':结果['isError'],#是否错误
                            'content':结果['content'],#默认内容
                        })#整形要记的内容
                        事件={
                            'rootCallId':执行['rootCallId'],#根
                            'parentCallId':执行['callId'],#父 run_code
                            'subCallId':子调用号,#子 id
                            'name':名称,#工具名
                            'arguments':归一['logged'],#日志副本
                            'isError':结果['isError'],#是否错误
                            'content':已记,#可能被替换的耐久内容
                        }#落定事件
                        失败=结果.get('error')#失败细节
                        if isinstance(失败,dict) and 'info' in 失败:
                            事件['error']=失败['info']#结构化错误身份，含 JSON null
                        if 'meta' in 结果:
                            事件['meta']=结果['meta']#派发元数据，含 JSON null
                        智能体.session.append('tool/ptc-dispatch',事件)#落定事件
                        日志任务.解决(None)#记完
                    except BaseException as 错误:
                        日志任务.拒绝(错误)#记失败
                日志链接盒[0]=日志任务.最终(日志离集)#离集在最终之后，竞速才看得到摘除
                日志工作.add(日志链接盒[0])#跟踪副作用
                启动守护线程(日志体)#日志线程
            条目={
                'flight':None,#真正派发后才赋期约
                'settled':False,#尚未停住
            }#排队条目
            def 分类():
                '惰性分类'
                return 注册表.执行模式(输入)['kind']#对照 SDK 声明的同一智能体视图
            def 放弃():
                '放弃未开始者'
                结局任务.拒绝(代码模式错误('run_code run is over ('+str(本轮.信号.原因)+'); '+名称+' tool call abandoned'))#未开始被放弃
            def 记下停住(派发结局):
                '派发落定后停住，供提交按序收尾'
                已准备执行=已准备盒[0]#本轮准备
                停住盒[0]={'kind':派发结局['kind'],'exec':已准备执行['exec'],'result':派发结局['result']}#停住
                条目['settled']=True#允许提交
            def 开始():
                '有序开始'
                智能体=执行['agent'] if 'agent' in 执行 else None#可选智能体
                if 智能体 is not None:
                    智能体.session.append('tool/ptc-dispatch-start',{
                        'rootCallId':执行['rootCallId'],#根
                        'parentCallId':执行['callId'],#父
                        'subCallId':子调用号,#子 id
                        'name':名称,#工具名
                        'arguments':归一['logged'],#日志副本
                    })#开始事件
                已准备=调度器['prepare'](输入)#预执行/守卫
                开始结果=期约()#有序开始阶段
                if 已准备['kind']=='dispatch':
                    已准备盒[0]=已准备#记下停住读取
                    体期约=期约()#派发体
                    def 执行体():
                        '工作线程跑派发'
                        try:
                            体期约.解决(调度器['dispatch'](已准备['exec']))#环绕+体
                        except BaseException as 错误:
                            体期约.拒绝(错误)#体失败
                    启动守护线程(执行体)#体在另一线程
                    条目['flight']=体期约.然后(记下停住)#体在飞，记下停住后才算落定
                    开始结果.解决(None)#开始阶段结束，体另算
                    return 开始结果
                停住盒[0]={'kind':已准备['kind'],'exec':已准备['exec'],'result':已准备['result']}#预落定
                条目['settled']=True#可提交
                开始结果.解决(None)#预落定没有在飞体
                return 开始结果
            def 压住日志(结算值=None):
                '超出并行上限时等一条日志副作用落定'
                完成=提交完成盒[0]#本轮提交期约
                if len(日志工作)<=并行上限:
                    完成.解决(None)#回压结束
                    return
                期约.竞速(list(日志工作)).然后(压住日志).捕获(完成.拒绝)#最先落定的一条
            def 提交():
                '有序提交'
                完成=期约()#提交阶段
                提交完成盒[0]=完成#回压回调读取
                停住=停住盒[0]#已停住结局
                if 停住 is None:
                    完成.解决(None)#没有停住
                    return 完成
                if 停住['kind']=='post-result':
                    结果=调度器['finalize'](停住['exec'],停住['result'])#后执行 + 最终化
                else:
                    结果=调度器['finish'](停住['exec'],停住['result'])#跳过后执行
                if not 结果.get('isError'):
                    for 块 in (结果.get('content') or []):
                        if 块.get('type')=='image':
                            执行['deferContext'](创建用户消息({
                                'content':结果['content'],
                                'source':{'kind':'ptc-mode'},
                            }))
                            break#一块即可
                for 上下文块 in (结果.get('additionalContexts') or []):
                    执行['deferContext'](上下文块)#渡到外层结果
                if 结果.get('concludesTurn'):
                    执行['concludeTurn']()#嵌套成功才终止外层
                落定(结果)#交给程序并记日志
                压住日志()#回压日志副作用
                return 完成
            条目['classify']=分类#惰性分类
            条目['abandon']=放弃#放弃
            条目['start']=开始#有序开始
            条目['commit']=提交#有序提交
            结局盒={'结局值':None,'错误':None}#同步边界
            落定事件=threading.Event()#期约落定后放行绑定线程
            def 结局已解决(结局值):
                '期约兑现，记下值并放行'
                结局盒['结局值']=结局值#规范结局
                落定事件.set()#放行
            def 结局已拒绝(错误):
                '期约拒绝，记下错误并放行'
                结局盒['错误']=错误#拒绝原因
                落定事件.set()#放行
            结局任务.然后(结局已解决).捕获(结局已拒绝)#挂钩，不在期约上等待
            未开始队列.append(条目)#入未开始队
            唤醒()#唤醒车道
            驱动()#确保车道在跑
            落定事件.wait()#绑定调用方要同步值
            if 结局盒['错误'] is not None:
                raise 结局盒['错误']#放弃或提交失败
            结局=结局盒['结局值']#规范结局
            if 本轮已结束():
                raise 代码模式错误('run_code run is over ('+str(本轮.信号.原因)+'); '+名称+' result discarded')#丢弃结果
            if 结局['isError']:
                raise 代码模式错误(结局['message'])#程序可见失败
            return 结局['value']#规范值
        return 调用#绑定函数
    函数表={}#无原型绑定表
    for 模式项 in 注册表.诸模式(执行['agent'] if 'agent' in 执行 else None):
        if 模式项['name']==运行代码名:
            continue#不绑定传输自身
        函数表[模式项['name']]=绑定(深冻结(模式项))#自有可枚举绑定

    try:
        请求={
            'program':参数['code'],#程序体
            'bindings':[{
                'global':'tools',#全局名
                'functions':函数表,#绑定表
                'errorClass':{'name':'ToolCallError','memberNameProperty':'toolName'},#绑定失败类
            }],#bindings
            'signal':本轮.信号,#本轮信号
        }#运行请求
        if 工作目录 is not None:
            请求['cwd']=工作目录#本次程序的起始目录
        if 政策 is not None:
            请求['sandboxPolicy']=政策#本次政策
        if 超时毫秒 is not None:
            请求['timeoutMs']=超时毫秒#本次截止
        运行结局=运行时.运行(运行时.解析(请求))#先解析再跑
    finally:
        本轮.中止('run_code settled')#本轮落定
        排空派发()#排空派发与日志
    if 运行结局.get('error'):
        错误=运行结局['error']#程序失败
        日志文本=('\nCaptured output:\n'+'\n'.join(运行结局['logs'])) if len(运行结局['logs'])>0 else ''#捕获输出
        if 'sandbox' not in 运行结局:
            沙箱文本=''#无沙箱
        else:
            沙箱=运行结局['sandbox']#沙箱投影
            强制=沙箱.get('enforcement')#强制程度
            沙箱文本=('\nFile sandbox: '+沙箱['mode']
                +( '' if 强制 is None else '; enforcement: '+强制)
                +( '; operation denied' if 沙箱.get('denied') else '')
                +'.')#沙箱句
        升级=升级指引(运行时) if 沙箱 is not None and 沙箱.get('denied') else ''#拒绝才接指引
        raise 代码运行失败错误('code run failed ('+错误['kind']+'): '+错误['message']+日志文本+沙箱文本+升级)#带种类、日志与沙箱
    成功={'logs':运行结局['logs']}#成功规范值
    if 运行结局.get('sandbox') is not None:
        成功['sandbox']=运行结局['sandbox']#有沙箱才带
    if 'value' in 运行结局:
        成功['result']=运行结局['value']#有返回值才带，含 JSON null
    return 成功#规范值

代码sdk语言=('typescript','python')#随附 SDK 语言
