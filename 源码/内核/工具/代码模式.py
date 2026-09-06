"""Code Mode 的 run_code 传输。程序经嵌套执行调用注册表里该智能体可见的工具。对齐上游 `tools/src/code-mode.ts`。公开面仅中文名。"""
import json,threading
from concurrent.futures import Future as 原生结果#单次操作结果
from ...模型后端.llm import 调用标识,装备错误 as 框架错误#导入调用 id 与框架错误
from ..会话 import 快照json值#导入无损 JSON 快照
from .模式 import 定义工具,参数模式规格转json模式#导入工具定义器与参数编译

__all__=(
    '运行代码名','sdk段顺序','代码sdk语言',
    '创建运行代码工具','代码运行失败错误',
    '已中止','若已中止则抛出','中止控制器','代码模式错误',
)#仅中文公开名

运行代码名='run_code'#传输工具名
sdk段顺序=150#SDK 段顺序
json缩进='  '#两空格 JSON 呈现
json缩进上限=10#总缩进上限

class 代码模式错误(Exception):
    """内核工具代码模式包的异常基类。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():
            if isinstance(错误,BaseException):
                自身._原生结果.set_exception(错误)#原样拒绝
            else:
                包装=代码模式错误('task rejected')#包装拒绝
                包装.原因=错误#附加信息做成属性
                自身._原生结果.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。原因用异常对象承载。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止标志
        自身._异常=None#中止时抛出的异常
        if 已中止标志:
            自身._事件.set()#置位
            自身._异常=代码模式错误('aborted')#默认中止异常

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():
            return#已触发
        if isinstance(原因,BaseException):
            自身._异常=原因#用异常对象承载
        elif 原因 is not None:
            中止异常=代码模式错误('aborted')#包装
            中止异常.原因=原因#附加属性
            自身._异常=中止异常#记下
        else:
            自身._异常=代码模式错误('aborted')#默认
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
    if 信号 is None:
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:
        return#无信号
    if not 信号._事件.is_set():
        return#仍活着
    if 信号._异常 is not None:
        raise 信号._异常#抛出
    raise 代码模式错误('aborted')#默认中止

def 在线程执行(函数):
    """在工作线程执行并返回任务。回调翻译时已是同步函数。"""
    任务=操作任务()#本次任务
    def 执行并结算():
        """执行函数并结算。"""
        try:
            任务.兑现(函数())#兑现同步返回值
        except BaseException as 错误:
            任务.拒绝(错误)#拒绝
    工作=threading.Thread(target=执行并结算)#工作线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 任务#操作任务

def 全部结算(任务列表):
    """并发等全部落定，吞掉失败。列表项必须是操作任务。"""
    def 等待并吞错(任务):
        """等待一路并吞错。"""
        try:
            任务.等待()#等待
        except BaseException:
            pass#排空不抛
    线程表=[]#工作线程
    for 任务 in 任务列表:
        工作=threading.Thread(target=等待并吞错,args=(任务,))#工作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:
        工作.join()#等到结束

def 任一落定(任务集):
    """最先落定的那路胜出。"""
    完成=threading.Event()#任一完成
    def 盯(任务):
        """等待一路。"""
        try:
            任务.等待()#等待
        except BaseException:
            pass#赛跑不关心成败
        完成.set()#唤醒
    for 任务 in list(任务集):
        工作=threading.Thread(target=盯,args=(任务,))#盯梢线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
    完成.wait()#阻塞到任一落定

def 空结算任务():
    """立刻结算的空操作任务。"""
    任务=操作任务()#空任务
    任务.兑现(None)#立刻结算
    return 任务#已决议

typescript风味={
    'description':(
        'Execute a TypeScript program against the available tools. Takes two required '
        +'arguments: `code`, the BODY of an async function (erasable syntax only; top-level '
        +'`await` and `return` work), and `description`, a short summary of what the program '
        +'does. Call tools as `await tools.name(args)` per the declarations in the system '
        +'prompt. Only what you print or return comes back — curate it.'
    ),#工具描述
    'codeDescription':'The program: the body of an async TypeScript function.',#代码参数描述
}#TS 风味
python风味={
    'description':(
        'Execute a Python program against the available tools. Takes two required '
        +'arguments: `code`, the BODY of an async function (top-level `await` and `return` '
        +'work), and `description`, a short summary of what the program does. Call tools as '
        +'`await tools.name(args)` per the declarations in the system prompt. Answer '
        +'with `print(...)` and/or `return <value>` — only that comes back, so curate it.'
    ),#工具描述
    'codeDescription':'The program: the body of an async Python function.',#代码参数描述
}#Python 风味
运行代码风味={
    'typescript':typescript风味,#TS
    'python':python风味,#Python
}#风味表
运行代码描述参数文案=(
    'Clear, concise description of what this program does in active voice, '
    +'5-10 words (shown in the UI). Examples: "Count TODO markers across packages"; '
    +'"Read failing test and its fixture"; "Rename config key in every cordis.yml".'
)#description 参数文案

def 解析风味(窥探运行时):
    """按已加载运行时的语言解析 run_code 风味。"""
    运行时=窥探运行时()#窥探运行时
    if 运行时 is None:
        return typescript风味#TS 回落
    语言=运行时['language'] if isinstance(运行时,dict) and 'language' in 运行时 else getattr(运行时,'language',None)#语言名
    风味=运行代码风味[语言] if isinstance(语言,str) and 语言 in 运行代码风味 else None#查表
    if 风味 is None:
        已知=', '.join(json.dumps(名,ensure_ascii=False,separators=(',',':'),allow_nan=False) for 名 in 运行代码风味.keys())#已知语言
        raise 代码模式错误('dsh-tools: no run_code schema flavor registered for runtime language '+json.dumps(语言,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' (known: '+已知+')')#大声失败
    return 风味#该语言风味

class 代码运行失败错误(框架错误):
    """程序运行本身失败时由 run_code 抛出。"""
    def __init__(自身,消息):
        """用失败消息构造。"""
        super().__init__(消息,'CODE_RUN_FAILED')#框架错误码
        自身.name='CodeRunFailedError'#类名

def 错误文本(错误):
    """从抛出值取人类可读消息。"""
    if isinstance(错误,Exception):
        消息=getattr(错误,'message',None)#Error.message
        if isinstance(消息,str):
            return 消息#用它
        if 错误.args:
            return str(错误.args[0])#args
        return str(错误)#字符串化
    return str(错误)#其余

def json归一参数(值):
    """把一次绑定调用的参数快照成无损 JSON，再对这份已脱离值再快照一次。"""
    try:
        快照=快照json值(值)#脱离
    except Exception as 错误:
        raise 代码模式错误('tool arguments must be lossless JSON: '+错误文本(错误))#参数必须无损
    if 快照 is None:
        raise 代码模式错误('tool arguments must be lossless JSON (call the tool with an arguments object, e.g. `{}`)')#必须是参数对象
    已记=快照json值(快照)#再快照一份给日志
    if 已记 is None:
        raise 代码模式错误('tool arguments could not be detached for durable logging')#日志副本失败
    return {'dispatched':快照,'logged':已记}#派发用第一份，日志用第二份

def 渲染json数字(值):
    """对齐 JS String(number) 的十进制。"""
    if isinstance(值,bool):
        return 'true' if 值 else 'false'#布尔到不了这里
    if isinstance(值,int):
        return str(值)#整数
    if isinstance(值,float) and 值.is_integer():
        return str(int(值))#整值浮点
    return str(值)#浮点

def 渲染json值(值):
    """渲染一个非字符串 JSON 根，不用递归遍历，也不让缩进无界增长。"""
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
            块列表.append(json.dumps(当前,ensure_ascii=False,separators=(',',':'),allow_nan=False))#JSON 引号
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
                文本=前+json.dumps(键,ensure_ascii=False,separators=(',',':'),allow_nan=False)+':'#键后紧跟冒号
            else:
                前='\n' if 下标==0 else ',\n'#换行
                文本=前+json缩进*子深度+json.dumps(键,ensure_ascii=False,separators=(',',':'),allow_nan=False)+': '#换行缩进加冒号空格
            任务列表.append({'kind':'text','text':文本})#键与分隔
            下标-=1#前进
        任务=任务列表.pop() if 任务列表 else None#下一任务
    return ''.join(块列表)#拼成字符串

def 渲染完成值(值):
    """把一次程序完成值渲染成面向模型的结果文本。"""
    if isinstance(值,str):
        return 值#字符串原样
    return 渲染json值(值)#其余走 JSON

class 带取值定义(dict):
    """允许 description/parameters 以取值器发出。"""
    def __init__(自身,源,描述取值=None,参数取值=None):
        """记下静态字段与取值器。"""
        super().__init__(源)#拷贝静态
        自身._描述取值=描述取值#描述 getter
        自身._参数取值=参数取值#参数 getter
    def __getitem__(自身,键):
        """读字段，取值器优先。"""
        if 键=='description' and 自身._描述取值 is not None:
            return 自身._描述取值()#发出时读风味
        if 键=='parameters' and 自身._参数取值 is not None:
            return 自身._参数取值()#发出时重编译
        return super().__getitem__(键)#静态字段
    def get(自身,键,缺省=None):
        """对齐 dict.get，走取值器。"""
        if 键=='description' and 自身._描述取值 is not None:
            return 自身._描述取值()#描述
        if 键=='parameters' and 自身._参数取值 is not None:
            return 自身._参数取值()#参数
        return super().get(键,缺省)#静态

def 创建运行代码工具(注册表,选项):
    """构建 run_code 工具定义。"""
    要求运行时=选项['requireRuntime']#必需运行时
    窥探运行时=选项['peekRuntime']#窥探运行时
    并行上限=选项['maxParallel']#并行上限
    整形派发日志=选项['shapeDispatchLog']#整形日志内容
    def 渲染运行代码输出(_参数,值):
        """渲染模型文本。"""
        return _渲染运行代码(值)#委托
    def 执行运行代码(参数,执行):
        """跑程序。"""
        return 执行运行代码(注册表,要求运行时,窥探运行时,并行上限,整形派发日志,参数,执行)#委托
    def 呈现运行代码调用(参数):
        """待处理呈现。"""
        return {
            'card':'generic',#通用卡片
            'title':参数['description'],#UI 标题
            'kind':'execute',#执行类
            'rawInput':参数['code'],#程序体
        }#呈现卡片
    定义=定义工具({
        'name':运行代码名,#传输名
        'description':typescript风味['description'],#占位描述
        'parameters':{
            'code':{'type':'string','required':True,'description':typescript风味['codeDescription']},#代码体
            'description':{
                'type':'string',#字符串
                'required':True,#必填
                'description':运行代码描述参数文案,#语言无关文案
            },#UI 标签
        },#静态参数规格
        'output':{
            'schema':{
                'type':'object',#对象
                'additionalProperties':False,#封闭
                'properties':{
                    'logs':{'type':'array','required':True,'items':{'type':'string'}},#捕获日志
                    'result':{'type':'json'},#可选返回值
                },#字段
            },#schema
            'render':渲染运行代码输出,#渲染模型文本
        },#规范输出
        'execute':执行运行代码,#跑程序
        'presentCall':呈现运行代码调用,#待处理呈现
    })#经 defineTool 编译
    def 读描述():
        """发出时读风味描述。"""
        return 解析风味(窥探运行时)['description']#当前风味
    def 读参数():
        """按当前风味重编译参数模式。"""
        return 参数模式规格转json模式({
            'code':{'type':'string','required':True,'description':解析风味(窥探运行时)['codeDescription']},#代码描述随语言
            'description':{'type':'string','required':True,'description':运行代码描述参数文案},#标签文案不变
        })#投影成模型可见模式
    return 带取值定义(定义,读描述,读参数)#替换 description/parameters

def _渲染运行代码(值):
    """渲染 run_code 规范输出。"""
    渲染='' if 'result' not in 值 else 渲染完成值(值['result'])#返回值文本
    段列表=[项 for 项 in ['\n'.join(值['logs']),渲染] if len(项)>0]#去掉空段
    文本='\n'.join(段列表) if len(段列表)>0 else '(run_code completed with no output)'#无输出时的哨兵句
    return [{'type':'text','text':文本}]#文本块

def 执行运行代码(注册表,要求运行时,窥探运行时,并行上限,整形派发日志,参数,执行):
    """跑一次 run_code 程序并排空子派发。"""
    from . import 调度器符号#延迟导入
    if len(参数['description'].strip())==0:
        raise 代码模式错误('invalid description: expected a non-empty string')#必须非空
    运行时=要求运行时()#组装/执行时必需运行时
    本轮=中止控制器()#本轮控制器
    外层信号=执行['signal'] if 'signal' in 执行 else None#外层取消通道
    def 跟外层中止():
        """外层中止则跟中止。"""
        if 外层信号 is None:
            return#无外层
        外层信号._事件.wait()#阻塞到外层置位
        本轮.中止(外层信号._异常)#转发异常原因
    if 已中止(外层信号):
        本轮.中止(外层信号._异常)#已中止则立刻跟
    elif 外层信号 is not None:
        盯外层=threading.Thread(target=跟外层中止)#盯梢线程
        盯外层.daemon=True#不挡住退出
        盯外层.start()#启动
    子调用序号=0#子调用序号
    未开始队列=[]#未开始队列
    在飞=set()#在飞体
    日志工作=set()#日志副作用
    提交队列=[]#提交序队列
    独占活动=False#独占屏障是否立着
    驾驶中=False#驱动车道是否在跑
    驾驶任务=空结算任务()#当前驱动任务
    条件=threading.Condition()#唤醒车道
    def 唤醒():
        """唤醒驱动。"""
        with 条件:
            条件.notify_all()#唤醒等待
    def 本轮已结束():
        """本轮是否已结束。"""
        return 已中止(本轮.信号)#现场读取
    def 驱动():
        """唯一有序车道。"""
        nonlocal 驾驶中,驾驶任务,独占活动
        with 条件:
            if 驾驶中:
                return 驾驶任务#已在跑则复用
            驾驶中=True#占车道
        def 车道():
            """新一轮驱动。"""
            nonlocal 驾驶中,独占活动
            try:
                while True:
                    可提交=None#提交队头
                    可开始=None#未开始队头
                    模式=None#分类
                    with 条件:
                        if len(提交队列)>0 and 提交队列[0]['settled']:
                            可提交=提交队列.pop(0)#出队
                        elif len(未开始队列)>0:
                            队头=未开始队列[0]#未开始队头
                            if 本轮已结束():
                                未开始队列.pop(0)#出队
                                队头['abandon']()#放弃未开始者
                                continue#再看队列
                            模式=队头['classify']()#当前分类
                            有槽=(not 独占活动) and (len(在飞)==0 if 模式=='exclusive' else len(在飞)<并行上限)#独占要空池，并行要低于上限
                            if 有槽:
                                可开始=未开始队列.pop(0)#出未开始队
                        if 可提交 is None and 可开始 is None:
                            if len(未开始队列)==0 and len(提交队列)==0 and len(在飞)==0:
                                return#静止
                            条件.wait()#等落定或新提交
                            continue#再看
                    if 可提交 is not None:
                        可提交['commit']()#有序后执行 + 落定
                        if 可提交.get('mode')=='exclusive':
                            独占活动=False#放下独占屏障
                        continue#再看队头
                    if 可开始 is not None:
                        if 模式=='exclusive':
                            独占活动=True#立独占屏障
                        可开始['mode']=模式#记下开始分类
                        提交队列.append(可开始)#入提交序
                        可开始['start']()#有序 prepare + 启动体
                        飞行=可开始['flight']#在飞体
                        def 离池(任务=飞行):
                            """体结束后离池。"""
                            在飞.discard(任务)#离池
                            唤醒()#唤醒车道
                        def 盯飞(任务=飞行,收尾=离池):
                            """等到飞行落定。"""
                            try:
                                任务.等待()#等待
                            except BaseException:
                                pass#飞行失败仍离池
                            收尾()#离池
                        在飞.add(飞行)#入池
                        盯梢=threading.Thread(target=盯飞)#盯梢线程
                        盯梢.daemon=True#不挡住退出
                        盯梢.start()#启动
            finally:
                with 条件:
                    驾驶中=False#释放占位
        驾驶任务=在线程跑(车道)#新一轮驱动
        return 驾驶任务#返回本轮驱动
    def 排空派发():
        """每次派发都已落定并提交。"""
        驱动().等待()#跑到静止
        while len(日志工作)>0:
            全部结算(list(日志工作))#排空日志副作用
    def 绑定(名称):
        """绑定一个工具。"""
        def 调用(原始参数):
            """一次 SDK 子派发。"""
            nonlocal 子调用序号
            if 本轮已结束():
                raise 代码模式错误('run_code run is over ('+str(本轮.信号._异常)+'); '+名称+' not dispatched')#不再派发
            归一=json归一参数(原始参数)#派发/日志两份快照
            子调用序号+=1#子调用序号
            子调用号=调用标识(str(执行['callId'])+':code:'+str(子调用序号))#确定性子 id
            输入={
                'callId':子调用号,#子调用 id
                'rootCallId':执行['rootCallId'],#根调用
                'name':名称,#工具名
                'arguments':归一['dispatched'],#派发副本
                'parent':执行['token'],#外层 token
                'signal':本轮.信号,#本轮信号
            }#子执行输入
            if 'agent' in 执行 and 执行['agent'] is not None:
                输入['agent']=执行['agent']#有智能体则带上
            调度器=注册表[调度器符号]#分阶段调度器
            结局任务=操作任务()#程序可见结局
            停住盒=[None]#停住的结局
            def 落定(结果):
                """把结局交给程序并记日志。"""
                if 结果['isError']:
                    结局任务.兑现({'isError':True,'message':结果['error']['message']})#程序可见错误
                else:
                    结局任务.兑现({'isError':False,'value':结果['value']})#规范值
                智能体=执行['agent'] if 'agent' in 执行 else None#记日志需要会话
                if 智能体 is None:
                    return#无智能体则不追加
                def 日志体():
                    """日志副作用。"""
                    已记=整形派发日志({
                        'exec':执行,#父执行
                        'agent':智能体,#智能体
                        'subCallId':子调用号,#子 id
                        'name':名称,#工具名
                        'isError':结果['isError'],#是否错误
                        'content':结果['content'],#默认内容
                    })#整形要记的内容
                    智能体.session.append('tool/code-dispatch',{
                        'rootCallId':执行['rootCallId'],#根
                        'parentCallId':执行['callId'],#父 run_code
                        'subCallId':子调用号,#子 id
                        'name':名称,#工具名
                        'arguments':归一['logged'],#日志副本
                        'isError':结果['isError'],#是否错误
                        'content':已记,#可能被替换的耐久内容
                    })#落定事件
                日志任务=在线程跑(日志体)#跟踪副作用
                def 日志离集(任务=日志任务):
                    """落定后离集。"""
                    日志工作.discard(任务)#离集
                def 盯日志(任务=日志任务,收尾=日志离集):
                    """等到日志落定。"""
                    try:
                        任务.等待()#等待
                    except BaseException:
                        pass#shapeDispatchLog 是收住的
                    收尾()#离集
                日志工作.add(日志任务)#跟踪副作用
                盯梢=threading.Thread(target=盯日志)#盯梢
                盯梢.daemon=True#不挡住退出
                盯梢.start()#启动
            条目={
                'flight':空结算任务(),#占位，start() 替换
                'settled':False,#尚未停住
            }#排队条目
            def 分类():
                """惰性分类。"""
                return 注册表.执行模式(输入)['kind']#对照 SDK 声明的同一智能体视图
            def 放弃():
                """放弃未开始者。"""
                结局任务.拒绝(代码模式错误('run_code run is over ('+str(本轮.信号._异常)+'); '+名称+' tool call abandoned'))#未开始被放弃
            def 开始():
                """有序开始。"""
                智能体=执行['agent'] if 'agent' in 执行 else None#可选智能体
                if 智能体 is not None:
                    智能体.session.append('tool/code-dispatch-start',{
                        'rootCallId':执行['rootCallId'],#根
                        'parentCallId':执行['callId'],#父
                        'subCallId':子调用号,#子 id
                        'name':名称,#工具名
                        'arguments':归一['logged'],#日志副本
                    })#开始事件
                已准备=调度器['prepare'](输入)#预执行/守卫
                if 已准备['kind']=='dispatch':
                    def 飞():
                        """启动体。"""
                        派发结局=调度器['dispatch'](已准备['exec'])#环绕+体
                        停住盒[0]={'kind':派发结局['kind'],'exec':已准备['exec'],'result':派发结局['result']}#停住
                        条目['settled']=True#允许提交
                        唤醒()#唤醒车道
                    条目['flight']=在线程跑(飞)#体在飞
                    return#体在飞
                停住盒[0]={'kind':已准备['kind'],'exec':已准备['exec'],'result':已准备['result']}#预落定
                条目['settled']=True#可提交
            def 提交():
                """有序提交。"""
                停住=停住盒[0]#已停住结局
                if 停住 is None:
                    return#防御
                if 停住['kind']=='post-result':
                    结果=调度器['finalize'](停住['exec'],停住['result'])#后执行 + 最终化
                else:
                    结果=调度器['finish'](停住['exec'],停住['result'])#跳过后执行
                for 上下文块 in (结果.get('additionalContexts') or []):
                    执行['deferContext'](上下文块)#渡到外层结果
                if 结果.get('concludesTurn'):
                    执行['concludeTurn']()#嵌套成功才终止外层
                落定(结果)#交给程序并记日志
                while len(日志工作)>并行上限:
                    任一落定(日志工作)#回压日志副作用
            条目['classify']=分类#惰性分类
            条目['abandon']=放弃#放弃
            条目['start']=开始#有序开始
            条目['commit']=提交#有序提交
            未开始队列.append(条目)#入未开始队
            唤醒()#唤醒车道
            驱动()#确保车道在跑
            结局=结局任务.等待()#等到提交
            if 本轮已结束():
                raise 代码模式错误('run_code run is over ('+str(本轮.信号._异常)+'); '+名称+' result discarded')#丢弃结果
            if 结局['isError']:
                raise 代码模式错误(结局['message'])#程序可见失败
            return 结局['value']#规范值
        return 调用#绑定函数
    函数表={}#无原型绑定表
    for 模式项 in 注册表.诸模式(执行['agent'] if 'agent' in 执行 else None):
        if 模式项['name']==运行代码名:
            continue#不绑定传输自身
        函数表[模式项['name']]=绑定(模式项['name'])#自有可枚举绑定

    try:
        运行结局=运行时.run({
            'program':参数['code'],#程序体
            'bindings':[{
                'global':'tools',#全局名
                'functions':函数表,#绑定表
                'errorClass':{'name':'ToolCallError','memberNameProperty':'toolName'},#绑定失败类
            }],#bindings
            'signal':本轮.信号,#本轮信号
        })#交给代码运行时
    finally:
        本轮.中止('run_code settled')#本轮落定
        排空派发()#排空派发与日志
    if 运行结局.get('error'):
        错误=运行结局['error']#程序失败
        日志文本=('\nCaptured output:\n'+'\n'.join(运行结局['logs'])) if len(运行结局['logs'])>0 else ''#捕获输出
        raise 代码运行失败错误('code run failed ('+错误['kind']+'): '+错误['message']+日志文本)#带种类与日志
    成功={'logs':运行结局['logs']}#成功规范值
    if 'value' in 运行结局:
        成功['result']=运行结局['value']#有返回值才带，含 JSON null
    return 成功#规范值

代码sdk语言=('typescript','python')#随附 SDK 语言
