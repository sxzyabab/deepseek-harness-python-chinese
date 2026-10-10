'每条 $ 调用在这个桥上的行为，接到已装上的宿主服务。没装上的服务让这次调用失败并点名'
import json,os,re,threading,time,urllib.error,urllib.request,uuid#文件字节、进程、请求
from ...内核.工具.json模式 import 断言对象json模式#工具参数模式
from ...内核.工具.代码模式 import 中止控制器,已中止#进程截止
from ...模型后端.llm import 创建用户消息#提示消息
from ...模型后端.llm.标识构造 import 调用标识#工具调用号
from ...存储.存储域 import 定义域,域表#每插件一份存储
from ...依赖.schemastery import 任意字段#存储值没有 zod 那么严
from ...交互.命令 import 命令名形态#宿主命令名比 Claude 更严
from ...交互.用户提问 import 询问用户问题请求#向人提问
from .值 import 记录,要求字符串,编码json,兑现,是有限数#入参与等待

__all__=['模组接口版本','文件最大字节','存储最大字节','请求最大字节','模组工具名','工具调用结果来自','创建宿主操作']

模组接口版本={'version':'claude-code-mods/0.1','engine':'deepseek-harness'}#$.session.version
文件最大字节=4*1024*1024#$.fs.read 与 $.fs.write
存储最大字节=4*1024*1024#一个插件的 $.store
进程输出最大字节=1024*1024#stdout 或 stderr
请求最大字节=4*1024*1024#$.http.fetch 正文
登记名规则=re.compile(r'^[A-Za-z0-9_-]{1,64}$')#工具和命令的短名
存储域规格=定义域({
    'name':'claude_code_mods',
    'version':1,
    'tables':{'store':域表(任意字段())},
})#每插件一条 JSON 对象。任意字段不按 zod 逐项校验

def 模组工具名(插件,工具):
    '模型看见的全名：mcp__插件__工具'
    return 'mcp__'+插件+'__'+工具#MCP 式拼法

def 块文本(内容):
    '把内容块里的文本接起来'
    if not isinstance(内容,(list,tuple)):#没有块
        return ''#空
    段=[]#文本
    for 块 in 内容:#逐块
        if isinstance(块,dict) and 块.get('type')=='text':#文本块
            段.append(块['text'] if isinstance(块.get('text'),str) else '')#缺席当空
    return ''.join(段)#接上

def 工具调用结果来自(结果):
    '宿主工具结果投影成 tool.call 的 result。失败带 isError'
    文本=块文本(结果.get('content') if isinstance(结果,dict) else None)#文本
    if isinstance(结果,dict) and 结果.get('isError') is True:#失败
        return {'result':文本,'isError':True}#失败
    return {'result':文本}#成功

def 参数对象(原始):
    '模型的 JSON 参数。解析不了就当空对象'
    try:#解析
        return 记录(json.loads(原始))#对象
    except Exception:#截断或坏掉
        return {}#空输入

def 会话消息列表(消息们,别名):
    '只留用户和助手，工具名翻译成模组看见的名字'
    出来=[]#结果
    for 消息 in 消息们:#逐条
        if not isinstance(消息,dict) or 消息.get('role') not in ('user','assistant'):#其它角色不要
            continue#跳过
        内容=消息.get('content') if isinstance(消息.get('content'),(list,tuple)) else []#块
        调用=[]#工具调用
        for 块 in 内容:#逐块
            if isinstance(块,dict) and 块.get('type')=='tool-call':#工具调用
                调用.append({
                    'tool_use_id':块.get('id'),#调用号
                    'tool':别名.toMod(块.get('name')),#模组侧名字
                    'input':参数对象(块.get('arguments') if isinstance(块.get('arguments'),str) else '{}'),#参数对象
                })#一条
        出来.append({'role':消息['role'],'text':块文本(内容),'toolUses':调用})#一条消息
    return 出来#列表

def 种类名(类型):
    '文件种类换成 Claude Code 的词'
    if 类型=='file':#文件
        return 'file'#file
    if 类型=='directory':#目录
        return 'dir'#dir
    return 'other'#其它，含链接本身以外的类型

def 尺寸(信息):
    '没有尺寸时为 0'
    if not isinstance(信息,dict):#没有信息
        return 0#零
    大小=信息.get('size')#尺寸
    if isinstance(大小,bool) or not isinstance(大小,(int,float)):#没有
        return 0#零
    return 大小#原值

def 读输出(读取器):
    '从已收集的流开头读文本'
    if 读取器 is None:#没有这路
        return ''#空
    片=读取器.自偏移读取(0)#从头
    if isinstance(片,dict) and isinstance(片.get('text'),str):#有文本
        return 片['text']#文本
    return ''#空

def 创建宿主操作(选项):
    '按已装上的服务做出操作表。选项里的 ctx 是插件上下文'
    上下文=选项['ctx']#插件上下文
    别名=选项['aliases']#工具名
    域盒={'域':None}#存储域只打开一次
    域锁=threading.Lock()#打开域
    存储写锁={}#每个插件一把，串起读改写
    写锁总=threading.Lock()#创建写锁

    def 取服务(名,从=None):
        '从给定上下文取服务。没给就用插件上下文'
        从哪=上下文 if 从 is None else 从#默认插件上下文
        获取=getattr(从哪,'获取服务',None)#可选查找
        if callable(获取):#有查找
            return 获取(名,False)#没有就 None
        return getattr(从哪,名,None)#属性

    def 存储():
        '打开 claude_code_mods 域'
        with 域锁:#只开一次
            if 域盒['域'] is not None:#已开
                return 域盒['域']#域
            设施=取服务('storageDomain')#域设施
            if 设施 is None:#没装
                raise RuntimeError('$.store 需要存储域服务，这次部署没有装上')#点名
            打开=兑现(设施.open(存储域规格))#同步打开
            def 关闭():
                '插件卸掉时关闭域'
                打开.close()#关闭
            def 登记关闭():
                '副作用体立刻执行，返回的函数才是拆除器'
                return 关闭#卸掉时关
            上下文.副作用(登记关闭,'claude-code-mods: 关闭存储域')#登记拆除
            域盒['域']=打开#记下
            return 打开#域

    def 目录服务():
        'workingDirectory。这个包没有把它再实现一遍'
        服务=取服务('workingDirectory')#服务
        if 服务 is None:#没装
            raise RuntimeError('$.session.cwd 以及按会话的目录操作需要 workingDirectory，这次部署没有装上')#点名
        return 服务#服务

    def 当前目录(智能体,信号):
        '没有智能体就没有会话目录'
        if 智能体 is None:#没有
            return None#不设 cwd
        return 兑现(目录服务().ensure(智能体,信号))#确保并取目录

    def 文件系统():
        '文件系统服务'
        服务=取服务('fs')#服务
        if 服务 is None:#没装
            raise RuntimeError('$.fs 需要文件系统服务，这次部署没有装上')#点名
        return 服务#服务

    def 目标(路径,智能体,信号):
        '相对会话目录解析路径'
        目录=当前目录(智能体,信号)#cwd
        解析选项={'signal':信号}#取消
        if 目录 is not None:#有目录
            解析选项['cwd']=目录#带上
        return 兑现(文件系统().解析(路径,解析选项))#目标

    def 跟踪(拆除,智能体):
        '登记的命令和工具按会话收着，桥卸掉时拆掉'
        键='' if 智能体 is None else 智能体.session.id#没有会话用空键
        拥有=选项['registrations'].get(键)#这组
        if 拥有 is None:#还没有
            拥有=set()#新建
            选项['registrations'][键]=拥有#记下
        拥有.add(拆除)#收着

    def 串行存储(插件,写入):
        '同一个插件的存储写一次只跑一个'
        with 写锁总:#取锁
            锁=存储写锁.get(插件)#已有
            if 锁 is None:#没有
                锁=threading.Lock()#新建
                存储写锁[插件]=锁#记下
        with 锁:#串行
            写入()#读改写

    def 重画(智能体):
        '有条带时请它稍后重画'
        再画=选项.get('redraw')#可选
        if 智能体 is not None and 再画 is not None:#有会话也有条带
            再画(智能体.session.id)#安排

    def 投影(会话,键):
        '读一个投影。没装注册表或没这个投影则 None'
        注册表=取服务('sessionProjections')#投影
        if 注册表 is None:#没装
            return None#没有
        return 注册表.状态(会话,键)#主机状态

    def 要求智能体(操作上下文,操作):
        '这次事件必须有会话'
        绑定=操作上下文['binding']#绑定
        智能体=绑定.get('agent') if isinstance(绑定,dict) else None#智能体
        if 智能体 is None:#没有
            raise RuntimeError('$.'+操作+' 需要会话，这次事件没有')#点名
        return 智能体#智能体

    def 从智能体取(智能体,名):
        '优先用智能体上下文，这样登记落在它的作用域层'
        从=智能体.ctx if 智能体 is not None and getattr(智能体,'ctx',None) is not None else 上下文#作用域
        return 取服务(名,从)#服务

    def 界面日志(输入,操作上下文):
        '$.ui.log 写到宿主日志'
        字段=记录(输入)#字段
        行=操作上下文['mod']['name']+'：'+要求字符串(字段.get('text'),'$.ui.log text')#一行
        if 字段.get('to')=='debug':#调试
            上下文.日志.调试(行)#调试
        else:#记录
            上下文.日志.信息(行)#信息

    def 提示条(输入,操作上下文):
        '$.ui.toast 写到宿主日志'
        上下文.日志.信息(操作上下文['mod']['name']+'（提示）：'+要求字符串(记录(输入).get('text'),'$.ui.toast text'))#一行

    def 界面状态(输入,操作上下文):
        '$.ui.status'
        文本=记录(输入).get('text')#可以没有
        if 文本 is None:#清除
            上下文.日志.信息(操作上下文['mod']['name']+'（状态）：（已清除）')#清除
        else:#有文本
            上下文.日志.信息(操作上下文['mod']['name']+'（状态）：'+要求字符串(文本,'$.ui.status text'))#一行

    def 作废(输入,操作上下文):
        '$.ui.invalidate'
        重画(操作上下文['binding'].get('agent'))#重画

    def 打开窗格(输入,操作上下文):
        '不放窗格。模组可以改画到条带'
        重画(操作上下文['binding'].get('agent'))#重画
        return {'id':要求字符串(记录(输入).get('id'),'$.ui.open id'),'isPlaced':False,'reason':'这个宿主不放窗格；请画在 AbovePrompt'}#没放

    def 关闭窗格(输入,操作上下文):
        '$.ui.close'
        重画(操作上下文['binding'].get('agent'))#重画

    def 窗格(输入,操作上下文):
        '$.ui.panes'
        return []#没有窗格

    def 询问(输入,操作上下文):
        '$.ui.ask'
        智能体=要求智能体(操作上下文,'ui.ask')#必须有会话
        提问=取服务('userQuestions')#提问服务
        if 提问 is None:#没装
            raise RuntimeError('$.ui.ask 需要用户提问服务，这次部署没有装上')#点名
        字段=记录(输入)#字段
        标签=字段.get('options')#选项标签
        选项列表=None#没有选项
        if isinstance(标签,(list,tuple)):#有标签
            选项列表=[{'label':要求字符串(标签项,'$.ui.ask option')} for 标签项 in 标签]#收成选项
        题目={
            'id':'answer',#固定题号
            'question':要求字符串(字段.get('question'),'$.ui.ask question'),#问题
        }#一题
        if isinstance(字段.get('header'),str):#有标题
            题目['header']=字段['header']#带上
        if 选项列表 is not None:#有选项
            题目['options']=选项列表#带上
        if 字段.get('multiSelect') is True:#多选
            题目['multiSelect']=True#带上
        答案=兑现(提问.ask(询问用户问题请求([题目],智能体,操作上下文['signal'])))#等人
        各项=答案.get('answers') if isinstance(答案,dict) else None#答案列表
        if not isinstance(各项,(list,tuple)) or len(各项)==0:#人关掉了
            raise RuntimeError('$.ui.ask：用户关掉了这个问题')#没有答案
        项=各项[0]#第一题
        if isinstance(项,dict) and 项.get('custom') is not None:#自定义文本，空字符串也算
            return 项['custom']#自定义
        选中=项.get('selected') if isinstance(项,dict) else None#选中的标签
        if not isinstance(选中,(list,tuple)):#没有
            选中=[]#空
        return ', '.join(str(一段) for 一段 in 选中)#用逗号接上

    def 登记命令(输入,操作上下文):
        '$.command.register'
        规格=记录(输入)#规格
        名字=要求字符串(规格.get('name'),'$.command.register name')#原名
        if 登记名规则.fullmatch(名字) is None:#Claude 的规则
            raise RuntimeError('"/'+名字+'" 被拒绝：命令名是字母、数字、_ 和 -，最多 64 个字符')#拒绝
        描述=要求字符串(规格.get('description'),'$.command.register description')#描述
        if len(描述.strip())==0:#宿主不收空白描述
            raise TypeError('$.command.register 的 description 不能是空白')#拒绝
        小写=名字.lower()#宿主命令名是小写
        if 命令名形态.fullmatch(小写) is None:#宿主更严：必须小写字母开头
            raise RuntimeError('"/'+名字+'" 被拒绝：本机命令注册表要求小写字母开头，随后只能是小写字母、数字、_ 或 -')#拒绝
        智能体=操作上下文['binding'].get('agent')#可能没有
        注册表=从智能体取(智能体,'commands')#命令注册表
        if 注册表 is None:#没装
            raise RuntimeError('$.command.register 需要命令注册表，这次部署没有装上')#点名
        引擎=操作上下文['engine']#用来引发 command.run
        模组=操作上下文['mod']#登记者
        定义={'name':小写,'description':描述}#命令定义
        if isinstance(规格.get('argumentHint'),str):#有提示
            提示=规格['argumentHint']#提示
            if len(提示.strip())==0:#空白
                raise TypeError('$.command.register 的 argumentHint 不能是空白')#拒绝
            定义['input']={'hint':提示}#输入提示
        def 处理(调用):
            '人敲了这条命令。同步跑 command.run'
            原始=调用.get('rawInput') if isinstance(调用.get('rawInput'),str) else ''#逐字输入
            def 没人答(事件):
                '没有钩子回答时的默认文本'
                return {'text':模组['name']+' 登记了 /'+小写+'，但没有 command.run 钩子回答它；请加 on(\'command.run\', { command: \''+小写+'\' }, hook)'}#提示
            跑出=引擎.发起('command.run',{
                'command':小写,#小写名
                'args':原始.strip(),#参数
                'origin':{'kind':'composer'},#来自输入
            },没人答,{'binding':{'agent':调用.get('agent')},'signal':调用.get('signal')})#引发
            结果={'kind':'success'}#成功
            if isinstance(跑出,dict) and isinstance(跑出.get('text'),str):#有文本
                结果['text']=模组['name']+': '+跑出['text']#点名模组
            return 结果#命令结果
        定义['handler']=处理#同步处理
        拆除=注册表.登记(定义)#登记
        选项['modCommands'].add(小写)#列表里标成插件
        跟踪(拆除,智能体)#卸掉时拆

    def 运行命令(输入,操作上下文):
        '$.command.run'
        智能体=要求智能体(操作上下文,'command.run')#必须有会话
        注册表=取服务('commands')#用插件上下文执行已有命令
        if 注册表 is None:#没装
            raise RuntimeError('$.command.run 需要命令注册表，这次部署没有装上')#点名
        字段=记录(输入)#字段
        名字=要求字符串(字段.get('command'),'$.command.run command')#名字
        参数=字段.get('args')#参数
        行='/'+名字+(' '+参数 if isinstance(参数,str) and len(参数)>0 else '')#命令行
        执行结果=兑现(注册表.执行(智能体,行,[],操作上下文['signal']))#同步执行
        if 执行结果 is None:#不是命令
            raise RuntimeError('/'+名字+' 不是命令')#没有
        结果=执行结果.get('result') if isinstance(执行结果,dict) else None#结果
        if isinstance(结果,dict) and 结果.get('kind')=='error':#命令报错
            raise RuntimeError(结果.get('text') if isinstance(结果.get('text'),str) else '命令失败')#用它的文本
        if isinstance(结果,dict) and isinstance(结果.get('text'),str):#有文本
            return {'text':结果['text']}#文本
        return {}#什么都不打印

    def 列出命令(输入,操作上下文):
        '$.command.list'
        智能体=要求智能体(操作上下文,'command.list')#必须有会话
        注册表=取服务('commands')#注册表
        if 注册表 is None:#没装
            return []#空
        列表=[]#结果
        for 描述项 in 注册表.列出(智能体):#有效命令
            列表.append({
                'name':描述项['name'],#名
                'description':描述项['description'],#描述
                'source':'plugin' if 描述项['name'] in 选项['modCommands'] else 'builtin',#来源
            })#一条
        return 列表#列表

    def 登记工具(输入,操作上下文):
        '$.tool.register'
        规格=记录(输入)#规格
        名字=要求字符串(规格.get('name'),'$.tool.register name')#短名
        if 登记名规则.fullmatch(名字) is None:#规则
            raise RuntimeError('工具 "'+名字+'" 被拒绝：工具名是字母、数字、_ 和 -，最多 64 个字符')#拒绝
        描述=要求字符串(规格.get('description'),'$.tool.register description')#描述
        模式= {'type':'object','properties':{}} if 'inputSchema' not in 规格 or 规格.get('inputSchema') is None else 记录(规格.get('inputSchema'))#默认空对象
        断言对象json模式(模式)#不支持的关键字在这里失败
        智能体=操作上下文['binding'].get('agent')#可能没有
        注册表=从智能体取(智能体,'tools')#工具注册表
        if 注册表 is None:#没装
            raise RuntimeError('$.tool.register 需要工具注册表，这次部署没有装上')#点名
        全名=模组工具名(操作上下文['mod']['name'],名字)#模型看见的名字
        模组名=操作上下文['mod']['name']#登记者
        def 执行体(参数,执行上下文):
            '没有 tool.call 钩子回答时失败'
            raise RuntimeError(模组名+' 登记了 '+全名+'，但没有 tool.call 钩子回答它；请加 on(\'tool.call\', { tool: \''+全名+'\' }, hook)')#提示
        def 呈现(参数,值):
            '回答文本'
            return [{'type':'text','text':值 if isinstance(值,str) else str(值)}]#一块文本
        定义={
            'name':全名,#全名
            'description':描述,#描述
            'parameters':模式,#参数
            'output':{'schema':{'type':'string'},'render':呈现},#结果是字符串
            'execute':执行体,#默认失败
        }#工具定义
        跟踪(注册表.登记(定义),智能体)#卸掉时拆
        选项['modTools'].add(全名)#钩子可以成功回答它

    def 调用工具(输入,操作上下文):
        '$.tool.call。管道会再引发 tool.call，这里不再选钩子'
        智能体=操作上下文['binding'].get('agent')#可以没有
        注册表=取服务('tools')#工具注册表
        if 注册表 is None:#没装
            raise RuntimeError('$.tool.call 需要工具注册表，这次部署没有装上')#点名
        字段=记录(输入)#字段
        参数={}#去掉工具名和调用号
        for 键,值 in 字段.items():#逐个
            if 键 not in ('tool','tool_use_id','agentId'):#参数
                参数[键]=值#留下
        调用号=调用标识('mod-'+str(uuid.uuid4()))#这次调用
        选项['callOrigins'][调用号]=操作上下文['mod']#管道用它选定更早的模组
        try:#用完就删
            执行输入={
                'callId':调用号,#调用号
                'name':别名.toHarness(要求字符串(字段.get('tool'),'$.tool.call tool')),#宿主工具名
                'arguments':参数,#参数
                'signal':操作上下文['signal'],#取消
            }#执行
            if 智能体 is not None:#有智能体
                执行输入['agent']=智能体#带上
            结果=兑现(注册表.执行(执行输入))#跑工具
            if 智能体 is not None and isinstance(结果,dict):#推迟的上下文仍要进模型
                附加=结果.get('additionalContexts')#附加
                if isinstance(附加,(list,tuple)):#有
                    for 一段 in 附加:#逐段
                        智能体.注入(一段)#注入
            return 工具调用结果来自(结果)#投影
        finally:#无论成败
            if 调用号 in 选项['callOrigins']:#还在
                del 选项['callOrigins'][调用号]#删掉

    def 列出工具(输入,操作上下文):
        '$.tool.list'
        注册表=取服务('tools')#注册表
        if 注册表 is None:#没装
            return []#空
        智能体=操作上下文['binding'].get('agent')#作用域键就是智能体
        模式们=注册表.诸模式(智能体)#可见模式
        return [{'name':别名.toMod(模式['name']),'description':模式['description']} for 模式 in 模式们]#翻译名字

    def 提交提示(输入,操作上下文):
        '$.prompt.submit'
        智能体=要求智能体(操作上下文,'prompt.submit')#必须有会话
        字段=记录(输入)#字段
        正文=要求字符串(字段.get('text'),'$.prompt.submit text')#文本
        if 字段.get('asUser') is True:#当成用户自己的话
            装框=正文#不点名
        else:#点名模组
            装框='来自模组 "'+操作上下文['mod']['name']+'" 的消息：\n'+正文#框起来
        消息=创建用户消息({'content':[{'type':'text','text':装框}],'source':{'kind':'user'}})#用户消息
        已提交=选项.get('submitted')#可选
        if 已提交 is not None:#记下是哪个模组提交的
            已提交(消息['id'],操作上下文['mod']['name'])#供 prompt.submit 的来源
        智能体.后续(消息)#下一轮
        return {'text':装框}#实际送出的文本

    def 会话号(输入,操作上下文):
        '$.session.id'
        return 要求智能体(操作上下文,'session.id').session.id#会话号

    def 会话目录(输入,操作上下文):
        '$.session.cwd'
        智能体=要求智能体(操作上下文,'session.cwd')#必须有会话
        return 兑现(目录服务().get(智能体.session))#当前目录

    def 会话根(输入,操作上下文):
        '$.session.root'
        头=要求智能体(操作上下文,'session.root').session.header#会话头
        if isinstance(头,dict) and isinstance(头.get('cwd'),str) and 头['cwd']!='':#有目录
            return 头['cwd']#创建时的目录
        return os.getcwd()#否则进程当前目录

    def 会话模型(输入,操作上下文):
        '$.session.model'
        智能体=要求智能体(操作上下文,'session.model')#必须有会话
        头=智能体.session.请求头()#折叠后的请求头
        if isinstance(头,dict) and isinstance(头.get('config'),dict):#有配置
            模型=头['config'].get('model')#模型
            if isinstance(模型,str) and 模型!='':#有
                return 模型#模型
        选项表=智能体.options if isinstance(getattr(智能体,'options',None),dict) else {}#智能体选项
        模型=选项表.get('model')#回落
        return 模型 if isinstance(模型,str) else ''#没有就空串

    def 会话回合(输入,操作上下文):
        '$.session.turns'
        智能体=要求智能体(操作上下文,'session.turns')#必须有会话
        边界=投影(智能体.session,'turnBoundary')#回合边界
        if not isinstance(边界,dict) or 'lastTurn' not in 边界:#没装
            raise RuntimeError('$.session.turns 需要 turnBoundary 投影，这次部署没有装上')#点名
        return 边界['lastTurn']#最近回合

    def 会话消息(输入,操作上下文):
        '$.session.messages'
        智能体=要求智能体(操作上下文,'session.messages')#必须有会话
        return 会话消息列表(智能体.session.派生消息(),别名)#投影

    def 会话用量(输入,操作上下文):
        '$.session.usage'
        智能体=要求智能体(操作上下文,'session.usage')#必须有会话
        压力=投影(智能体.session,'contextPressure')#上下文压力
        令牌=压力.get('pressureTokens') if isinstance(压力,dict) else None#已用
        窗口=压力.get('contextWindow') if isinstance(压力,dict) and isinstance(压力.get('contextWindow'),(int,float)) and not isinstance(压力.get('contextWindow'),bool) else 0#窗口
        上下文用量={}#context
        if isinstance(令牌,(int,float)) and not isinstance(令牌,bool):#有令牌
            上下文用量['tokens']=令牌#令牌
        上下文用量['window']=窗口#窗口
        if isinstance(令牌,(int,float)) and not isinstance(令牌,bool) and 窗口!=0:#能算百分比
            上下文用量['percent']=round((令牌/窗口)*100)#四舍五入
        return {'startedAt':智能体.session.header['createdAt'],'context':上下文用量,'rateLimits':[]}#用量

    def 版本(输入,操作上下文):
        '$.session.version'
        return 模组接口版本#固定

    def 读存储(输入,操作上下文):
        '$.store.get'
        表=存储().table('store')#表
        已有=表.get(操作上下文['mod']['name'])#这个插件
        键=要求字符串(记录(输入).get('key'),'$.store.get key')#键
        if not isinstance(已有,dict) or 键 not in 已有:#没有
            return None#缺席
        return 已有[键]#值

    def 写存储(输入,操作上下文):
        '$.store.set'
        字段=记录(输入)#字段
        键名=要求字符串(字段.get('key'),'$.store.set key')#键
        模组名=操作上下文['mod']['name']#插件
        def 写入():
            '读改写'
            表=存储().table('store')#表
            已有=表.get(模组名)#当前
            下一份=dict(已有) if isinstance(已有,dict) else {}#拷贝
            下一份[键名]=字段.get('value')#写入
            编码=编码json(下一份)#字节
            if 编码 is None or len(编码.encode('utf-8'))>存储最大字节:#太大或带不走
                raise RuntimeError('$.store.set：'+模组名+' 的存储会超过 '+str(存储最大字节)+' 字节的 JSON')#拒绝
            表.put(模组名,json.loads(编码))#存 JSON 能带走的值
        串行存储(模组名,写入)#串行

    def 删存储(输入,操作上下文):
        '$.store.delete'
        键名=要求字符串(记录(输入).get('key'),'$.store.delete key')#键
        模组名=操作上下文['mod']['name']#插件
        def 写入():
            '删掉一个键'
            表=存储().table('store')#表
            已有=表.get(模组名)#当前
            if not isinstance(已有,dict) or 键名 not in 已有:#没有这个键
                return#不用写
            剩余=dict(已有)#拷贝
            del 剩余[键名]#删掉
            表.put(模组名,剩余)#写回
        串行存储(模组名,写入)#串行

    def 存储键(输入,操作上下文):
        '$.store.keys'
        已有=存储().table('store').get(操作上下文['mod']['name'])#当前
        if not isinstance(已有,dict):#没有
            return []#空
        return list(已有.keys())#键

    def 读文件(输入,操作上下文):
        '$.fs.read'
        路径=要求字符串(记录(输入).get('path'),'$.fs.read path')#路径
        解析后=目标(路径,操作上下文['binding'].get('agent'),操作上下文['signal'])#目标
        信息=兑现(文件系统().状态(解析后,操作上下文['signal']))#元数据
        if isinstance(信息,dict) and isinstance(信息.get('size'),(int,float)) and not isinstance(信息.get('size'),bool) and 信息['size']>文件最大字节:#太大
            raise RuntimeError('$.fs.read：'+路径+' 大于 '+str(文件最大字节)+' 字节')#拒绝
        return 兑现(文件系统().读文本(解析后,操作上下文['signal']))#文本

    def 写文件(输入,操作上下文):
        '$.fs.write'
        字段=记录(输入)#字段
        正文=要求字符串(字段.get('text'),'$.fs.write text')#文本
        if len(正文.encode('utf-8'))>文件最大字节:#太大
            raise RuntimeError('$.fs.write：内容大于 '+str(文件最大字节)+' 字节')#拒绝
        路径=要求字符串(字段.get('path'),'$.fs.write path')#路径
        解析后=目标(路径,操作上下文['binding'].get('agent'),操作上下文['signal'])#目标
        兑现(文件系统().写文本(解析后,正文,None,操作上下文['signal']))#写入

    def 列目录(输入,操作上下文):
        '$.fs.list。链接一律报不是链接'
        路径=要求字符串(记录(输入).get('path'),'$.fs.list path')#路径
        解析后=目标(路径,操作上下文['binding'].get('agent'),操作上下文['signal'])#目标
        各项=兑现(文件系统().列目录(解析后,操作上下文['signal']))#子项
        结果=[]#结果
        for 项 in 各项:#逐个
            结果.append({'name':项['name'],'kind':种类名(项.get('type')),'size':尺寸(项),'isLink':False})#一条
        return 结果#列表

    def 存在文件(输入,操作上下文):
        '$.fs.exists'
        路径=要求字符串(记录(输入).get('path'),'$.fs.exists path')#路径
        解析后=目标(路径,操作上下文['binding'].get('agent'),操作上下文['signal'])#目标
        return 兑现(文件系统().状态(解析后,操作上下文['signal'])) is not None#有元数据就是存在

    def 文件状态(输入,操作上下文):
        '$.fs.stat。链接报告它指向的目标，mtimeMs 恒为 0'
        路径=要求字符串(记录(输入).get('path'),'$.fs.stat path')#路径
        目录=当前目录(操作上下文['binding'].get('agent'),操作上下文['signal'])#cwd
        选项={} if 目录 is None else {'cwd':目录}#链接状态的选项
        信息=兑现(文件系统().链接状态(路径,选项,操作上下文['signal']))#不跟随末段
        if 信息 is None:#不存在
            raise RuntimeError('$.fs.stat：'+路径+' 不存在')#没有
        if 信息.get('type')!='symlink':#不是链接
            return {'kind':种类名(信息.get('type')),'size':尺寸(信息),'mtimeMs':0,'isLink':False}#普通
        解析选项={'signal':操作上下文['signal']}#跟随
        if 目录 is not None:#有目录
            解析选项['cwd']=目录#带上
        解析后=兑现(文件系统().解析(路径,解析选项))#指向
        跟随=兑现(文件系统().状态(解析后,操作上下文['signal']))#目标，悬空则没有
        类型='other' if not isinstance(跟随,dict) else 跟随.get('type')#悬空算 other
        return {'kind':种类名(类型),'size':尺寸(跟随),'mtimeMs':0,'isLink':True}#链接

    def 运行进程(输入,操作上下文):
        '$.process.run。不经壳，收集输出'
        子进程=取服务('subprocess')#子进程
        if 子进程 is None:#没装
            raise RuntimeError('$.process.run 需要子进程服务，这次部署没有装上')#点名
        字段=记录(输入)#字段
        参数列表=字段.get('argv')#参数
        if not isinstance(参数列表,(list,tuple)) or len(参数列表)==0 or not all(isinstance(项,str) for 项 in 参数列表):#不合法
            raise TypeError('$.process.run 需要非空的字符串 argv 列表')#类型
        设置=记录(字段.get('init'))#选项
        超时=设置['timeoutMs'] if 是有限数(设置.get('timeoutMs')) else 选项['processTimeoutMs']#超时
        if isinstance(设置.get('cwd'),str):#指定了目录
            目录=设置['cwd']#用它
        else:#会话目录或进程目录
            会话目录=当前目录(操作上下文['binding'].get('agent'),操作上下文['signal'])#会话
            目录=会话目录 if isinstance(会话目录,str) else os.getcwd()#回落
        环境=None#可选环境
        if isinstance(设置.get('env'),dict):#给了环境
            环境={}#只收字符串
            for 键,值 in 设置['env'].items():#逐个
                if not isinstance(键,str) or not isinstance(值,str):#不合法
                    raise TypeError('$.process.run 的 env 必须是字符串到字符串')#类型
                环境[键]=值#留下
        组合=中止控制器()#调用方取消或超时
        停=threading.Event()#看守结束
        程序=参数列表[0]#名字
        def 看守():
            '到点或调用方取消时中止子进程'
            截止=time.monotonic()+超时/1000#截止
            while not 停.is_set():#还在跑
                if 已中止(操作上下文['signal']) or time.monotonic()>=截止:#该停
                    组合.中止(RuntimeError('$.process.run：'+程序+' 没在 '+str(超时)+' 毫秒内退出'))#中止
                    return#结束
                停.wait(0.05)#短等
        看守线程=threading.Thread(target=看守,daemon=True)#看守
        看守线程.start()#启动
        try:#结束时停看守
            规格={
                'argv':list(参数列表),#参数
                'cwd':目录,#目录
                'stdio':{'stdin':'ignore','stdout':{'maxBytes':进程输出最大字节},'stderr':{'maxBytes':进程输出最大字节}},#收集
                'graceMs':1000,#宽限
                'signal':组合.信号,#取消
            }#规格
            if 环境 is not None:#有环境
                规格['env']=环境#带上
            句柄=子进程.启动(规格)#启动
            结局=兑现(句柄.done)#等退出
        finally:#停看守
            停.set()#唤醒
            看守线程.join()#等它退出
        if 已中止(组合.信号):#取消或超时都按超时说
            raise RuntimeError('$.process.run：'+程序+' 没在 '+str(超时)+' 毫秒内退出')#没在时限内退出
        if not isinstance(结局,dict) or 结局.get('exitCode') is None:#被信号杀掉
            信号名=结局.get('signal') if isinstance(结局,dict) else None#信号
            raise RuntimeError('$.process.run：'+程序+' 被信号 '+str(信号名)+' 终止')#终止
        return {'exitCode':结局['exitCode'],'stdout':读输出(句柄.collected.stdout),'stderr':读输出(句柄.collected.stderr)}#结果

    def 请求(输入,操作上下文):
        '$.http.fetch。4xx 和 5xx 也是响应，不抛错。读正文时取消停不下来'
        if 已中止(操作上下文['signal']):#开始前已取消
            原因=getattr(操作上下文['signal'],'原因',None)#原因
            if isinstance(原因,BaseException):#异常
                raise 原因#原样
            raise RuntimeError('$.http.fetch 已取消')#取消
        字段=记录(输入)#字段
        设置=记录(字段.get('init'))#选项
        超时=设置['timeoutMs'] if 是有限数(设置.get('timeoutMs')) else 选项['processTimeoutMs']#超时
        地址=要求字符串(字段.get('url'),'$.http.fetch url')#地址
        头=设置.get('headers') if isinstance(设置.get('headers'),dict) else {}#头
        头表={}#只收字符串
        for 名,值 in 头.items():#逐个
            if isinstance(名,str) and isinstance(值,str):#字符串
                头表[名]=值#留下
        数据=None#没有正文
        if isinstance(设置.get('body'),str):#有正文
            数据=设置['body'].encode('utf-8')#字节
        方法=设置['method'] if isinstance(设置.get('method'),str) else None#方法
        请求对象=urllib.request.Request(地址,data=数据,headers=头表,method=方法)#请求
        try:#发出
            响应=urllib.request.urlopen(请求对象,timeout=超时/1000)#等待
        except urllib.error.HTTPError as 错误响应:#4xx 5xx 仍是响应
            响应=错误响应#当响应读
        except urllib.error.URLError as 错误:#连不上或超时
            raise RuntimeError('$.http.fetch 失败：'+消息(getattr(错误,'reason',错误))) from 错误#失败
        状态码=getattr(响应,'status',None)#状态
        if 状态码 is None:#HTTPError 用 code
            状态码=响应.code#状态
        响应头={}#小写名
        for 名,值 in 响应.headers.items():#逐个
            响应头[str(名).lower()]=值#后写覆盖
        块=[]#正文
        总量=0#字节
        while True:#按块读
            片=响应.read(65536)#一块
            if not 片:#读完
                break#停
            总量+=len(片)#累计
            if 总量>请求最大字节:#太大
                raise RuntimeError('$.http.fetch：响应体大于 '+str(请求最大字节)+' 字节')#拒绝
            块.append(片)#留下
        正文=b''.join(块).decode('utf-8','replace')#文本
        return {'status':状态码,'ok':200<=状态码<400,'headers':响应头,'text':正文}#响应

    def 读环境(输入,操作上下文):
        '$.env.get'
        名字=要求字符串(记录(输入).get('name'),'$.env.get name')#名字
        if 名字 in os.environ:#有
            return os.environ[名字]#值
        return None#没有

    def 写环境(输入,操作上下文):
        '$.env.set。不带 value 就删掉'
        字段=记录(输入)#字段
        键=要求字符串(字段.get('name'),'$.env.set name')#名字
        if 'value' not in 字段 or 字段.get('value') is None:#删除
            if 键 in os.environ:#还在
                del os.environ[键]#删掉
            return None#无值
        os.environ[键]=要求字符串(字段.get('value'),'$.env.set value')#写入
        return None#无值

    return {
        'ui.log':界面日志,
        'ui.toast':提示条,
        'ui.status':界面状态,
        'ui.invalidate':作废,
        'ui.open':打开窗格,
        'ui.close':关闭窗格,
        'ui.panes':窗格,
        'ui.ask':询问,
        'command.register':登记命令,
        'command.run':运行命令,
        'command.list':列出命令,
        'tool.register':登记工具,
        'tool.call':调用工具,
        'tool.list':列出工具,
        'prompt.submit':提交提示,
        'session.id':会话号,
        'session.cwd':会话目录,
        'session.root':会话根,
        'session.model':会话模型,
        'session.turns':会话回合,
        'session.messages':会话消息,
        'session.usage':会话用量,
        'session.version':版本,
        'store.get':读存储,
        'store.set':写存储,
        'store.delete':删存储,
        'store.keys':存储键,
        'fs.read':读文件,
        'fs.write':写文件,
        'fs.list':列目录,
        'fs.exists':存在文件,
        'fs.stat':文件状态,
        'process.run':运行进程,
        'http.fetch':请求,
        'env.get':读环境,
        'env.set':写环境,
    }#操作表
