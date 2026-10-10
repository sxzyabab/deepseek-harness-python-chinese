'实验桥：把 Claude Code 模组的钩子接到宿主扩展点。模组经 定义模组 挂上，由本服务的 添加 登记'
import json,threading,time#参数对照、分离运行、回合耗时
from ...内核.会话 import 会话标识#按会话号找智能体
from ...内核.作用域 import 获取作用域#工具按智能体作用域可见
from ...内核.工具 import 校验json模式值#内置工具的输出模式
from ...内核.工具.代码模式 import 中止控制器#桥卸掉时中止还在跑的钩子
from ...类型化远程调用.协议 import 远程 as _远程,远程服务#条带的远程方法
from .值 import 消息,记录,编码json,是有限数,兑现#抛出文案、入参、JSON、按钮回调
from .链 import 改写被拒错误#钩子改了已记入日志的调用
from .引擎 import 模组引擎#引发事件
from .宿主操作 import 创建宿主操作,工具调用结果来自,模组接口版本# $ 与工具结果投影
from .表面 import 表面表#提示上方的条带
from .工具名 import 创建工具名别名,默认工具别名#Claude 工具名与宿主工具名
from .匹配器 import 已知事件#on 接受的事件名
from .定义模组 import 定义模组,模组配置模式#包成插件；组合里调用 添加
from .类型 import (
    钩子来源,钩子失败,钩子预算,模组定义,
    序列化元素,表面快照,
    界面绘制输入,会话开始输入,会话开始结果,会话结束输入,会话结束结果,
    提示提交输入,提示提交结果,回合开始输入,回合开始结果,回合用量,回合完成输入,回合完成结果,
    工具调用输入,工具调用结果,命令运行输入,命令运行结果,
    命令规格,命令信息,工具规格,工具信息,会话消息,工具使用摘要,会话用量,会话版本,
    询问选项,界面日志选项,提示条选项,窗格打开参数,窗格打开结果,状态引用,
    文件项,文件状态,进程运行初始,进程运行结果,请求初始,请求响应,提示提交参数,
)#包入口再导出这些结构

__all__=[
    '克劳德代码模组','已服务事件',
    '定义模组','模组配置模式','默认工具别名','已知事件','模组接口版本',
    '钩子来源','钩子失败','钩子预算','模组定义',
    '序列化元素','表面快照',
    '界面绘制输入','会话开始输入','会话开始结果','会话结束输入','会话结束结果',
    '提示提交输入','提示提交结果','回合开始输入','回合开始结果','回合用量','回合完成输入','回合完成结果',
    '工具调用输入','工具调用结果','命令运行输入','命令运行结果',
    '命令规格','命令信息','工具规格','工具信息','会话消息','工具使用摘要','会话用量','会话版本',
    '询问选项','界面日志选项','提示条选项','窗格打开参数','窗格打开结果','状态引用',
    '文件项','文件状态','进程运行初始','进程运行结果','请求初始','请求响应','提示提交参数',
]#公开面。框架槽不在这里

已服务事件=frozenset([
    'session.start','session.end','prompt.submit','turn.start','turn.complete','tool.call','command.run','ui.render',
])#这个宿主会引发的事件。别的已知事件可以登记，但会报成未服务
改写说明='.agents/notes/proposed/feature/2026-06-30-pre-tool-input-rewrite.md'#参数改写还没接上，错误里指向这份说明
缺席=object()#区分「键不在」和 None

class 桥配置:
    '钩子时限、工具别名，以及条带报给 ui.render 的列数行数'
    def 校验数据(自身,数据=None):
        '缺省补上数字。toolAliases 没有就省略。非法值在挂载时失败'
        if 数据 is None:#没给配置
            数据={}#空对象
        if not isinstance(数据,dict):#不是对象
            raise ValueError('claude-code-mods：配置必须是对象')#拒绝
        结果={
            'hookTimeoutMs':10000,#一条钩子
            'catchTimeoutMs':1000,#.catch
            'processTimeoutMs':30000,#进程与请求
            'bandColumns':120,#条带列
            'bandRows':10,#条带行
        }#数字缺省
        for 键 in 结果:#逐个数字
            if 键 not in 数据 or 数据[键] is None:#没给
                continue#留缺省
            值=数据[键]#调用方的值
            if isinstance(值,bool) or not isinstance(值,(int,float)):#不是数字
                raise ValueError('claude-code-mods：'+键+'必须是数字')#拒绝
            结果[键]=值#收下，正数留给构造器
        if 'toolAliases' in 数据 and 数据['toolAliases'] is not None:#有别名表
            别名=数据['toolAliases']#表
            if not isinstance(别名,dict):#不是对象
                raise ValueError('claude-code-mods：toolAliases 必须是对象')#拒绝
            for 名,宿主名 in 别名.items():#逐条
                if not isinstance(名,str) or not isinstance(宿主名,str):#键值都要是字符串
                    raise ValueError('claude-code-mods：toolAliases 的键和值都必须是字符串')#拒绝
            结果['toolAliases']=dict(别名)#副本
        return 结果#归一化配置

配置模式=桥配置()#框架 Config 槽

class 合并信号:
    '两路取消合成一路。先看先传入的那路'
    def __init__(自身,甲,乙):
        '甲、乙是已有的中止信号'
        自身._甲=甲#第一路
        自身._乙=乙#第二路

    def is_set(自身):
        '任一路已置位'
        if 自身._甲 is not None and 自身._甲.is_set():#第一路
            return True#已中止
        return 自身._乙 is not None and 自身._乙.is_set()#第二路

    @property
    def 原因(自身):
        '已中止那一路的原因。两路都中止时用第一路'
        if 自身._甲 is not None and 自身._甲.is_set():#第一路已中止
            return getattr(自身._甲,'原因',None)#它的原因
        if 自身._乙 is not None and 自身._乙.is_set():#第二路已中止
            return getattr(自身._乙,'原因',None)#它的原因
        return None#还没中止

def 断言正数(字段,值):
    '时限必须是正的毫秒，列数和行数必须是正数'
    if not 是有限数(值) or 值<=0:#零、负数、非有限、布尔
        if str(字段).endswith('Ms'):#时限
            raise ValueError('claude-code-mods：'+字段+'必须是正的毫秒数')#拒绝
        raise ValueError('claude-code-mods：'+字段+'必须是正数')#列数行数

def 现在毫秒():
    '墙钟毫秒，用来记回合开始与耗时'
    return int(time.time()*1000)#纪元毫秒

def 块文本(块们):
    '把内容块里的文本接起来'
    段=[]#文本
    for 块 in 块们:#逐块
        if isinstance(块,dict) and 块.get('type')=='text':#文本块
            段.append(块['text'] if isinstance(块.get('text'),str) else '')#缺席当空
    return ''.join(段)#接上

def 人的消息(已认领):
    '一批领取里，人自己打的那些。注入的上下文不算提示'
    结果=[]#人的消息
    for 消息 in 已认领:#逐条
        来源=消息.get('source') if isinstance(消息,dict) else None#来源
        if isinstance(来源,dict) and 来源.get('kind')=='user':#人打的
            结果.append(消息)#留下
    return 结果#列表

def 换内容(消息,内容):
    '复制一条消息并换掉内容块，不改原来那条'
    下一份=dict(消息)#浅拷贝
    下一份['content']=内容#新块
    return 下一份#新消息

def 改写提示文本(提示,文本):
    '用一段新文本换掉人的消息里的文本块。第一块文本承接它，其余文本块去掉，非文本块留在原处。一段文本都没有时，接到第一条消息后面'
    放置={'已放':False}#写在闭包里，后面的消息能看见已经放过
    改过=[]#新列表
    for 消息 in 提示:#逐条
        内容=消息['content'] if isinstance(消息.get('content'),(list,tuple)) else []#块
        if not any(isinstance(块,dict) and 块.get('type')=='text' for 块 in 内容):#没有文本块
            改过.append(消息)#原条留下
            continue#下一条
        新内容=[]#这条的新块
        for 块 in 内容:#逐块
            if not isinstance(块,dict) or 块.get('type')!='text':#非文本
                新内容.append(块)#留在原处
            elif not 放置['已放']:#第一块文本
                放置['已放']=True#只放一次
                新内容.append({'type':'text','text':文本})#换成新文本
        改过.append(换内容(消息,新内容))#换这条
    if len(改过)==0:#没有消息
        return 改过#空
    if 放置['已放'] or len(文本)==0:#已经放过，或新文本是空的
        return 改过#不用再补
    首=改过[0]#第一条
    首内容=list(首['content'] if isinstance(首.get('content'),(list,tuple)) else [])#它的块
    首内容.append({'type':'text','text':文本})#补在后面
    return [换内容(首,首内容)]+改过[1:]#第一条换成带文本的

def 附上上下文(提示,上下文块):
    '钩子附上的上下文，按原样接在人的最后一条消息后面'
    if len(提示)==0:#没有消息
        return list(提示)#原样
    末=提示[-1]#最后一条
    块们=[{'type':'text','text':行} for 行 in 上下文块]#每行一块
    末内容=list(末['content'] if isinstance(末.get('content'),(list,tuple)) else [])#原块
    return list(提示[:-1])+[换内容(末,末内容+块们)]#换掉最后一条

def 收下提示提交(结果,原文):
    '只留下模组可以设的字段，并且各自符合声明的类型'
    if isinstance(结果,dict) and isinstance(结果.get('drop'),str):#丢掉
        return {'drop':结果['drop']}#只留原因
    上下文块=[]#附上的行
    if isinstance(结果,dict) and isinstance(结果.get('context'),(list,tuple)):#有上下文
        上下文块=[行 for 行 in 结果['context'] if isinstance(行,str)]#只留字符串
    文本=原文#没改就用原文
    if isinstance(结果,dict) and isinstance(结果.get('text'),str):#给了文本
        文本=结果['text']#用它
    出来={'text':文本}#文本一定有
    if len(上下文块)>0:#有行才带
        出来['context']=上下文块#上下文
    return 出来#结果

def 折助手(回合记录,数据):
    '把一条已提交的助手消息折进这一回合的回答和用量'
    消息体=数据.get('message') if isinstance(数据,dict) else None#助手消息
    内容=消息体.get('content') if isinstance(消息体,dict) else []#块
    回合记录['answer']=块文本(内容 if isinstance(内容,(list,tuple)) else [])#最后一条的文本
    用量源=数据.get('usage') if isinstance(数据,dict) else None#这次用量
    if not isinstance(用量源,dict):#没有
        return#回答已经更新
    来源=消息体.get('source') if isinstance(消息体,dict) else None#来源
    模型=来源.get('model') if isinstance(来源,dict) else None#模型
    用量=回合记录.get('usage')#已有合计
    if not isinstance(用量,dict):#第一笔
        用量={
            'input_tokens':0,
            'output_tokens':0,
            'cache_read_input_tokens':0,
            'cache_creation_input_tokens':0,
            'model':模型,
        }#从零开始
    用量['input_tokens']+=用量源.get('inputTokens') or 0#输入
    用量['output_tokens']+=用量源.get('outputTokens') or 0#输出
    读缓存=用量源.get('cacheReadTokens')#读缓存
    写缓存=用量源.get('cacheWriteTokens')#写缓存
    用量['cache_read_input_tokens']+=0 if 读缓存 is None else 读缓存#缺席当零
    用量['cache_creation_input_tokens']+=0 if 写缓存 is None else 写缓存#缺席当零
    用量['model']=模型#以最后一条为准
    回合记录['usage']=用量#写回

def 紧凑(值):
    '对照用的 JSON。两边用同一种写法，才能看出钩子有没有改参数'
    return json.dumps(值,ensure_ascii=False,separators=(',',':'))#紧凑、保留非 ASCII

def json值(值):
    '能无损带走的 JSON。带不走则 None'
    文本=编码json(值)#编码
    if not isinstance(文本,str):#带不走
        return None#没有
    return json.loads(文本)#解析回普通值

def 读键(对象,键):
    '键不在时返回缺席，不把 None 当成没给'
    if isinstance(对象,dict) and 键 in 对象:#有这个键
        return 对象[键]#值，可以是 None
    return 缺席#没给

def 严格同(甲,乙):
    '对齐 ===：字符串按值，对象按身份，缺席只和缺席相同'
    if 甲 is 乙:#同一份，含两个缺席
        return True#相同
    if 甲 is 缺席 or 乙 is 缺席:#一边没给
        return False#不同
    if isinstance(甲,bool) or isinstance(乙,bool):#布尔不跟数字混
        return type(甲) is bool and type(乙) is bool and 甲==乙#只有布尔
    if isinstance(甲,str) and isinstance(乙,str):#文本
        return 甲==乙#按值
    if isinstance(甲,(int,float)) and isinstance(乙,(int,float)):#数字
        return type(甲) is type(乙) and 甲==乙#类型也要一致
    return False#其余对象要同一份才算

def 模组代答(文本,码,呈现=None):
    '用模组的文本代替工具自己的结果，形状是失败'
    if 呈现 is None:#没单独给呈现
        呈现=文本 if isinstance(文本,str) else ''#用文本
    名字='ModDenied' if 码=='MOD_DENIED' else 'ModAnswered'#两种码
    return {
        'isError':True,#失败
        'error':{'message':文本,'info':{'name':名字,'code':码}},#结构化错误
        'content':[{'type':'text','text':呈现 if isinstance(呈现,str) else ''}],#给人看的块
    }#工具结果

class 分离运行:
    '桥卸掉时要等的那些后台运行。失败记一行，不变成没人接的异常'
    def __init__(自身,报告):
        '报告收失败的一行'
        自身.报告=报告#诊断
        自身.待定=set()#还没结束的线程
        自身.控制器=中止控制器()#卸掉时中止
        自身.锁=threading.Lock()#待定表

    def 跟踪(自身,标签,动作):
        '在守护线程里跑。失败只记一行'
        def 体():
            '跑完把自己从待定表拿掉'
            try:#动作可抛
                动作()#跑
            except Exception as 错误:#失败
                自身.报告(标签+'失败：'+消息(错误))#一行
            finally:#离开待定表
                with 自身.锁:#摘掉
                    自身.待定.discard(线程)#摘掉
        线程=threading.Thread(target=体,daemon=True)#不挡住进程退出
        with 自身.锁:#先登记再启动
            自身.待定.add(线程)#排空能等得到
        线程.start()#启动

    def 取消(自身):
        '中止信号。已经在跑的要自己看这路信号'
        自身.控制器.中止(RuntimeError('claude-code-mods 已卸掉'))#只生效一次

    def 排空(自身):
        '先中止，再等到此刻已经跟踪的运行结束'
        自身.取消()#中止
        with 自身.锁:#快照
            待等=list(自身.待定)#这一批
        for 线程 in 待等:#逐个
            线程.join()#等到结束

class 克劳德代码模组(远程服务):
    '已加载的模组、它们的钩子，以及从宿主扩展点把事件引发出去的监听器'
    def __init__(自身,上下文,配置值=None):
        '登记 claudeCodeMods，并接上会话、回合、提示和工具'
        super().__init__(上下文,'claudeCodeMods',{'namespace':'claudeCodeMods'})#服务名与远程命名空间
        if not isinstance(配置值,dict):#直接构造没给配置
            配置值=配置模式.校验数据(配置值)#补缺省
        钩子超时=配置值['hookTimeoutMs'] if 'hookTimeoutMs' in 配置值 else 10000#钩子时限
        捕获超时=配置值['catchTimeoutMs'] if 'catchTimeoutMs' in 配置值 else 1000#处理函数时限
        进程超时=配置值['processTimeoutMs'] if 'processTimeoutMs' in 配置值 else 30000#进程与请求
        条带列=配置值['bandColumns'] if 'bandColumns' in 配置值 else 120#列
        条带行=配置值['bandRows'] if 'bandRows' in 配置值 else 10#行
        断言正数('hookTimeoutMs',钩子超时)#必须为正
        断言正数('catchTimeoutMs',捕获超时)#必须为正
        断言正数('processTimeoutMs',进程超时)#必须为正
        断言正数('bandColumns',条带列)#必须为正
        断言正数('bandRows',条带行)#必须为正
        别名覆盖=配置值.get('toolAliases') if 'toolAliases' in 配置值 else None#可省略
        别名=创建工具名别名(别名覆盖)#内置加上部署覆盖
        调用来源={}#$.tool.call 的调用号到来源模组
        模组命令=set()#模组登记的命令
        模组工具=set()#模组登记的工具全名
        自身.登记表={}#会话号到拆除器集合。空键是没有会话的那些
        def 报告(行):
            '记一条警告，前面加上桥的名字'
            上下文.日志.警告('claude-code-mods：'+行)#一行
        def 智能体来自(会话号):
            '注册表里这个会话的智能体。还没装上或已经拆了则 None'
            智能体们=上下文.获取服务('agents',False)#可选
            if 智能体们 is None:#没装
                return None#没有
            return 智能体们.获取(会话标识(会话号))#在线的那一个
        分离=分离运行(报告)#后台的 session.end 与 turn.complete
        引擎盒={'引擎':None}#绘制回调晚于引擎构造
        def 绘制(会话号,输入):
            '向 ui.render 要这一会话的树。智能体已经不在就画空'
            智能体=智能体来自(会话号)#还在不在
            if 智能体 is None:#拆了
                return None#空树
            return 引擎盒['引擎'].发起('ui.render',输入,lambda 事件:None,{
                'binding':{'agent':智能体},#这次绘制的会话
                'signal':分离.控制器.信号,#桥的寿命
            })#模组的树
        def 跑动作(会话号,回调):
            '跑按钮的 onPress。失败记一行，不打断条带'
            try:#回调可抛
                兑现(回调())#若返回期约则等到它
            except Exception as 错误:#失败
                报告('按钮 onPress 失败：'+消息(错误))#一行
        表面=表面表({
            'columns':条带列,#报给 ui.render 的列
            'rows':条带行,#报给 ui.render 的行
            'render':绘制,#引发绘制
            'runAction':跑动作,#按钮
            'report':报告,#诊断
        })#条带表
        自身.表面=表面#远程方法用
        def 重画(会话号):
            '推迟到当前这段同步代码之后。模组往往在触发重画的那次 $ 返回后才写状态'
            def 稍后():
                '智能体还在才重画'
                try:#绘制可抛
                    if 智能体来自(会话号) is not None:#还在
                        表面.刷新(会话号)#重画
                except Exception as 错误:#失败
                    报告('条带重画失败：'+消息(错误))#一行
            定时=threading.Timer(0,稍后)#下一趟
            定时.daemon=True#不挡住进程退出
            定时.start()#启动
        模组提交={}#消息号到提交它的模组名
        操作表=创建宿主操作({
            'ctx':上下文,#插件上下文
            'aliases':别名,#工具名
            'processTimeoutMs':进程超时,#进程与请求的缺省时限
            'registrations':自身.登记表,#命令和工具的拆除器
            'callOrigins':调用来源,#谁发起的 $.tool.call
            'modCommands':模组命令,#列表里标成插件
            'modTools':模组工具,#钩子可以成功回答的工具
            'redraw':重画,#请条带稍后重画
            'submitted':lambda 消息号,模组名:模组提交.__setitem__(消息号,模组名),#prompt.submit 的来源
        })#操作表
        引擎=模组引擎({
            'ops':lambda 操作:操作表.get(操作),#没有的交给引擎自己的 state 和 clock
            'stateKey':lambda 绑定:'' if not isinstance(绑定,dict) or 绑定.get('agent') is None else 绑定['agent'].session.id,#按会话分状态
            'budgetMs':钩子超时,#钩子预算
            'catchBudgetMs':捕获超时,#处理函数预算
            'report':报告,#诊断
            'onStateRead':lambda 键,槽:表面.读了状态(键,槽),#绘制订阅
            'onStateWritten':lambda 键,槽:表面.写了状态(键,槽),#写下就重画
        })#引擎
        引擎盒['引擎']=引擎#绘制可以引发了
        自身.引擎=引擎#添加与列表
        def 卸掉模组():
            '先中止还在等的钩子，再拆条带、登记、引擎，最后等到后台运行结束'
            分离.取消()#定时与钩子看这路信号
            表面.丢弃()#不再画
            for 拥有 in list(自身.登记表.values()):#各组
                for 拆除 in list(拥有):#逐个
                    拆除()#拆命令或工具
            自身.登记表.clear()#清掉
            引擎.丢弃()#卸模组并关掉定时器
            分离.排空()#等到 session.end 和 turn.complete
        def 登记卸掉():
            '副作用体立刻执行，返回的函数才是拆除器'
            return 卸掉模组#桥卸掉时
        上下文.副作用(登记卸掉,'claude-code-mods：卸掉模组')#登记拆除
        def 是根(智能体):
            '没有注册表时当成根。有注册表则必须在根列表里'
            智能体们=上下文.获取服务('agents',False)#可选
            if 智能体们 is None:#没装
                return True#当成根
            for 根 in 智能体们.诸根():#逐个根
                if 根 is 智能体:#同一份
                    return True#是根
            return False#子智能体
        已开始根=set()#收到过 session.start 的根会话
        def 智能体号(智能体):
            '子智能体才带 agentId。根不带'
            if 智能体 is not None and not 是根(智能体):#子智能体
                return {'agentId':智能体.id}#带上
            return {}#根或没有
        回合表={}#会话号到当前回合的回答和用量
        已开始回合={}#会话号到已经引发过 turn.start 的回合号
        替换表={}#执行令牌到钩子换上的文本
        def 智能体已创建(载荷):
            '根智能体创建后引发 session.start，再请条带画一次'
            智能体=载荷['agent']#本智能体
            if not 是根(智能体):#子智能体不发会话事件
                return#结束
            已开始根.add(智能体.session.id)#先记下，创建中途失败也会在拆除时收尾
            信号=载荷.get('signal')#创建信号，可以没有
            if 信号 is None:#没有
                放弃=分离.控制器.信号#只看桥的寿命
            else:#两路
                放弃=合并信号(信号,分离.控制器.信号)#创建取消或桥卸掉
            输入={
                'cwd':兑现(上下文.workingDirectory.ensure(智能体,放弃)),#会话目录
                'surface':None,#这个宿主没有 Claude 的界面面
                'isInteractive':上下文.获取服务('userQuestions',False) is not None,#装了提问才算交互
            }#session.start
            引擎.发起('session.start',输入,lambda 事件:{'cwd':事件['cwd']},{
                'binding':{'agent':智能体},#会话
                'signal':放弃,#取消
            })#等钩子
            重画(智能体.session.id)#画条带
        上下文.监听('agent/created',智能体已创建)#创建
        def 智能体已拆除(载荷):
            '根若收过 session.start，就在后台引发 session.end。状态在钩子结束前仍可读'
            智能体=载荷['agent']#本智能体
            会话号=智能体.session.id#会话
            回合表.pop(会话号,None)#丢掉回合折合
            已开始回合.pop(会话号,None)#丢掉回合标记
            自身.登记表.pop(会话号,None)#这个会话的命令和工具已经随它的上下文拆了
            表面.忘掉(会话号)#结束观看
            def 忘掉会话():
                '忘掉 $.state 并关掉这个会话的定时器'
                引擎.忘记会话(会话号)#忘掉
            曾开始=会话号 in 已开始根#收过 session.start
            已开始根.discard(会话号)#摘掉
            if not 曾开始:#没开始过
                分离.跟踪('会话清理',忘掉会话)#后台忘掉
                return#不引发 session.end
            输入={'reason':'other','sessionId':会话号}#收尾原因
            def 结束():
                '引发 session.end。失败也要忘掉会话；忘掉成功则不再把引发的失败报出来'
                try:#钩子可抛
                    引擎.发起('session.end',输入,lambda 事件:{'sessionId':事件['sessionId']},{
                        'binding':{'agent':智能体},#会话还在绑定上
                        'signal':分离.控制器.信号,#桥的寿命
                    })#等钩子
                except Exception:#引发失败
                    忘掉会话()#仍然忘掉
                    return#不再上报这次引发失败
                忘掉会话()#成功之后忘掉
            分离.跟踪('session.end',结束)#不挡住拆除监听器
        上下文.监听('agent/disposed',智能体已拆除)#拆除
        def 步骤前(载荷,下一步):
            '人的提示先走 prompt.submit，回合的第一步再走 turn.start，然后才让循环继续'
            智能体=载荷['agent']#本步智能体
            消息们=载荷['messages'] if isinstance(载荷.get('messages'),(list,tuple)) else []#领取的消息
            回合=载荷['turn']#回合号
            信号=载荷.get('signal')#本步取消
            绑定={'agent':智能体}#钩子绑定
            已开始=已开始回合.get(智能体.session.id)#这个会话
            if 已开始 is None:#还没有
                已开始=set()#新建
                已开始回合[智能体.session.id]=已开始#记下
            首次=回合 not in 已开始#这一回合的第一步
            已开始.add(回合)#记过了
            提示=人的消息(消息们)#人打的
            块列=[]#全部块
            for 消息 in 提示:#逐条
                内容=消息['content'] if isinstance(消息.get('content'),(list,tuple)) else []#块
                块列.extend(内容)#摊开
            文本=块文本(块列)#提示文本
            已提交={'text':文本}#没人改就用原文
            if len(提示)>0:#空的注入批不是提示
                提交者=None#哪个模组提交的
                for 消息 in 提示:#找第一个
                    名=模组提交.get(消息.get('id')) if isinstance(消息,dict) else None#模组名
                    if 名 is not None:#找到了
                        提交者=名#用它
                        break#停止
                for 消息 in 提示:#用过就删
                    if isinstance(消息,dict):#有号
                        模组提交.pop(消息.get('id'),None)#删掉
                输入={
                    'text':文本,#原文
                    'wait':False,#不等待
                    'origin':{'kind':'composer'} if 提交者 is None else {'kind':'plugin','name':提交者},#来源
                }#prompt.submit
                def 提示核(事件):
                    '没人改时交回原文，有上下文就带上'
                    核={'text':事件['text']}#文本
                    if isinstance(事件,dict) and 'context' in 事件 and 事件['context'] is not None:#有上下文
                        核['context']=事件['context']#带上
                    return 核#结果
                已提交=收下提示提交(引擎.发起('prompt.submit',输入,提示核,{
                    'binding':绑定,#会话
                    'signal':信号,#取消
                }),文本)#只留允许的字段
                if isinstance(已提交.get('drop'),str):#丢掉
                    上下文.日志.信息('claude-code-mods：提示被丢掉：'+已提交['drop'])#原因
                    return {'kind':'reject'}#这一步不进模型
            if 首次:#回合开始
                开始入={'text':已提交['text'],'turnId':str(回合)}#回合号用文本
                开始入.update(智能体号(智能体))#子智能体带号
                引擎.发起('turn.start',开始入,lambda 事件:{'turnId':事件['turnId']},{
                    'binding':绑定,#会话
                    'signal':信号,#取消
                })#等钩子
            下游=下一步()#其余监听器和循环自己的决定
            if not isinstance(下游,dict) or 下游.get('kind')!='enter' or len(消息们)==0:#拒绝，或这批是空的
                return 下游#原样
            上下文块=已提交.get('context') if isinstance(已提交.get('context'),list) else []#附上的行
            if 已提交.get('text')==文本 and len(上下文块)==0:#没改
                return 下游#原样
            if 已提交.get('text')==文本:#只附上下文
                改过=list(提示)#同一批消息
            else:#换文本
                改过=改写提示文本(提示,已提交['text'])#新文本
            if len(上下文块)>0:#还有上下文
                改过=附上上下文(改过,上下文块)#接在最后一条
            对照=list(zip(提示,改过))#原消息到新消息，按身份
            换过=[]#下游消息
            for 消息 in 下游.get('messages') or []:#逐条
                换成=消息#默认留着
                for 原,新 in 对照:#找人的那几条
                    if 消息 is 原:#就是这一条
                        换成=新#换成改过的
                        break#停止
                换过.append(换成)#一条
            下一份=dict(下游)#不改原来的决定
            下一份['messages']=换过#换上人的消息
            return 下一份#进入
        上下文.监听('agent/pre-step',步骤前)#步骤前
        def 执行工具(执行,下一步):
            'tool.call 包住真正的执行。没有钩子就直接往下，不画条带'
            引发者=调用来源.get(执行['callId'])#$.tool.call 只让更早的模组看见
            钩子=引擎.注册表.选择('tool.call',引发者)#外层在前
            if len(钩子)==0:#没人听
                return 下一步()#直接执行
            智能体=执行['agent'] if 'agent' in 执行 else None#可以没有
            原始参数=记录(执行.get('arguments'))#模型参数
            if not isinstance(原始参数,dict):#不是对象
                原始参数={}#空
            else:#拷成普通字典，键顺序留着
                原始参数=dict(原始参数)#副本
            模组名=别名.toMod(执行['name'])#模组看见的工具名
            输入=dict(原始参数)#参数在前
            输入['tool']=模组名#工具
            输入['tool_use_id']=执行['callId']#调用号
            输入.update(智能体号(智能体))#子智能体带号
            已记录=紧凑(原始参数)#日志里已经记下的参数
            底下盒={'结果':None}#下一步若跑了，结果在这里
            def 工具核(事件):
                '真正执行一次，再投影成钩子看见的结果'
                底下盒['结果']=下一步()#瀑布往下
                return 工具调用结果来自(底下盒['结果'])#投影
            def 校验下一步(事件,钩子条=None):
                '不许改工具名，也不许改已经记入日志的参数'
                if not isinstance(事件,dict):#不是对象
                    raise 改写被拒错误('改写了 '+模组名+' 的参数；参数改写需要工具前输入改写机制（'+改写说明+'）')#拒绝
                其余={}#去掉工具名和调用号之后
                for 键,值 in 事件.items():#逐个
                    if 键 not in ('tool','tool_use_id','agentId'):#参数
                        其余[键]=值#留下
                if 事件.get('tool')!=模组名:#改了工具
                    raise 改写被拒错误('把调用从 '+模组名+' 改到了 '+str(事件.get('tool'))+'；已记入日志的调用仍跑它点名的工具')#拒绝
                if 紧凑(其余)!=已记录:#改了参数
                    raise 改写被拒错误('改写了 '+模组名+' 的参数；参数改写需要工具前输入改写机制（'+改写说明+'）')#拒绝
            答案=引擎.发起已选('tool.call',钩子,引发者,输入,工具核,{
                'binding':{'agent':智能体},#会话
                'signal':执行.get('signal'),#这次调用的取消
                'validateNext':校验下一步,#不许改写
            })#钩子的答案
            if 智能体 is not None:#有会话
                重画(智能体.session.id)#工具之后重画
            if isinstance(答案,dict) and 'deny' in 答案:#拒绝，null 也算给了
                拒绝=答案['deny']#原因
                if 拒绝 is None:#空原因
                    return 模组代答(None,'MOD_DENIED','Error: null')#失败
                拒绝文本=拒绝 if isinstance(拒绝,str) else str(拒绝)#文本
                return 模组代答(拒绝文本,'MOD_DENIED','Error: '+拒绝文本)#失败
            结果值=答案.get('result') if isinstance(答案,dict) else None#钩子的结果
            if isinstance(结果值,str):#已经是文本
                文本=结果值#用它
            else:#别的值
                编=编码json(结果值)#能带走才有文本
                文本=编 if isinstance(编,str) else ''#带不走当空
            底下=底下盒['结果']#可能没执行
            if 底下 is not None:#执行过
                映射=工具调用结果来自(底下)#投影
                if 严格同(读键(映射,'result'),读键(答案,'result')) and 严格同(读键(映射,'isError'),读键(答案,'isError')):#钩子没改
                    return 底下#原结果
                if isinstance(答案,dict) and 答案.get('isError') is True and not (isinstance(底下,dict) and 底下.get('isError')):#成功被标成失败
                    return 模组代答(文本,'MOD_ANSWERED')#换成失败
                替换表[执行['token']]=文本#后执行时换内容
                return 底下#先把原结果交下去
            if isinstance(答案,dict) and 答案.get('isError') is True:#没执行，但是失败
                return 模组代答(文本,'MOD_ANSWERED')#失败
            if 执行['name'] in 模组工具:#模组自己的工具
                return {'isError':False,'value':文本,'content':[{'type':'text','text':文本}]}#文本就是结果
            工具们=上下文.获取服务('tools',False)#工具注册表
            定义=None#可见定义
            if 工具们 is not None:#装了
                作用域=None if 智能体 is None else 获取作用域(智能体.ctx)#这个智能体看见的
                定义=工具们.获取(执行['name'],作用域)#定义
            值=json值(答案.get('result') if isinstance(答案,dict) else None)#无损值
            if 定义 is not None and 值 is not None and len(校验json模式值(定义['output']['schema'],值))==0:#符合它自己的输出
                return {'isError':False,'value':值,'content':定义['output']['render'](执行['arguments'],值)}#按工具呈现
            return 模组代答(文本,'MOD_ANSWERED')#其余当失败文本
        上下文.监听('tools/execute',执行工具)#执行
        def 工具结果(执行,结果=None):
            '没走到后执行的调用，也要把替换表里的条目清掉'
            替换表.pop(执行['token'],None)#清掉
        上下文.监听('tools/result',工具结果)#结果
        def 工具后(执行,结果,下一步):
            '钩子换过文本时，接受的那一路改用这段文本。挡住的一路原样交回'
            if 执行['token'] not in 替换表:#没换
                return 下一步()#原样
            替换=替换表.pop(执行['token'])#用掉
            下游=下一步()#其余决定
            if isinstance(下游,dict) and 下游.get('kind')=='block':#挡住
                return 下游#不改
            出来={'kind':'accept','content':[{'type':'text','text':替换}]}#换成这段文本
            if isinstance(下游,dict) and 'additionalContexts' in 下游 and 下游['additionalContexts'] is not None:#有附加
                出来['additionalContexts']=下游['additionalContexts']#留下
            return 出来#接受
        上下文.监听('tools/post-execute',工具后)#后执行
        def 会话事件(会话,事件):
            '折合同一回合的助手消息，回合结束时在后台引发 turn.complete'
            if not isinstance(事件,dict):#没有事件
                return#结束
            if 事件.get('type')=='turn/start':#回合开始
                数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
                回合表[会话.id]={
                    'turn':数据.get('turn'),#回合号
                    'startedAt':现在毫秒(),#开始
                    'answer':'',#还没有回答
                    'usage':None,#还没有用量
                }#记下
                return#结束
            if 事件.get('type')=='assistant/message':#助手消息
                记录项=回合表.get(会话.id)#当前回合
                if 记录项 is not None:#还开着
                    折助手(记录项,事件.get('data'))#折进去
                return#结束
            if 事件.get('type')!='turn/end':#别的事件
                return#不看
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
            回合=数据.get('turn')#回合号
            原因=数据.get('reason') if isinstance(数据.get('reason'),dict) else {}#结束原因
            已有=已开始回合.get(会话.id)#这个会话
            if 已有 is not None:#有标记
                已有.discard(回合)#这一回合结束了
            智能体=智能体来自(会话.id)#还在不在
            if 智能体 is None:#已经拆了
                return#不引发
            记录项=回合表.get(会话.id)#折合
            折好=记录项 if isinstance(记录项,dict) and 记录项.get('turn')==回合 else None#对得上才用
            种类=原因.get('kind')#原因种类
            输入={
                'turnId':str(回合),#文本回合号
                'answer':'' if 折好 is None else 折好.get('answer') or '',#回答
                'durationMs':0 if 折好 is None else 现在毫秒()-折好['startedAt'],#耗时
                'isAborted':种类=='aborted',#是否中止
                'reason':'aborted' if 种类=='aborted' else ('error' if 种类=='error' else 'answer'),#三种
            }#turn.complete
            输入.update(智能体号(智能体))#子智能体带号
            if 折好 is not None and isinstance(折好.get('usage'),dict):#有用量
                输入['usage']=dict(折好['usage'])#副本
            if 折好 is not None:#用过了
                回合表.pop(会话.id,None)#丢掉
            def 完成():
                '引发 turn.complete。有文本就记到日志，然后重画'
                结果=引擎.发起('turn.complete',输入,lambda 事件:{'text':''},{
                    'binding':{'agent':智能体},#会话
                    'signal':分离.控制器.信号,#桥的寿命
                })#等钩子
                if isinstance(结果,dict) and isinstance(结果.get('text'),str) and len(结果['text'])>0:#有字
                    上下文.日志.信息('claude-code-mods：'+结果['text'])#记下来
                重画(会话.id)#重画
            分离.跟踪('turn.complete',完成)#不挡住会话事件
        上下文.监听('session/event',会话事件)#会话事件

    @property
    def 模组列表(自身):
        '已加载的模组，按加载顺序'
        return 自身.引擎.注册表.列出()#链上的顺序

    @_远程({'mode':'stream'})
    def 观看条带(自身,agent,signal):
        '观看一条会话提示上方的条带：先给当前画面，之后每次重画给一次，直到取消'
        return 自身.表面.观看(agent.session.id,signal)#快照序列
    观看条带._typert_remote_marker['exportName']='watchBand'#线上的方法名

    @_远程('pressBand')
    def 按下条带(自身,agent,generation,actionId):
        '按下当前画面里的一个按钮，跑它的 onPress，再交出新画面'
        return 自身.表面.按下(agent.session.id,generation,actionId)#新快照

    def 添加(自身,定义):
        '加载一份模组，放在此前所有模组的里面。名字不合法、重名，或 register 抛错，都让这次挂载失败'
        模组=自身.引擎.添加(定义)#跑 register
        未服务=自身.引擎.注册表.未服务(模组,已服务事件)#登记了但本宿主不引发的
        描述=自身.引擎.描述(模组)#hooks 行
        自身.所属上下文.日志.信息(
            'claude-code-mods：钩子模块 '+模组['name']+'@inline 已加载（层 user）；事件：'+(描述 if 描述 else '（无）')
        )#加载一行
        if len(未服务)>0:#有未服务的
            列出=', '.join(json.dumps(事件,ensure_ascii=False) for 事件 in 未服务)#带引号的事件名
            哪句='那个事件' if len(未服务)==1 else '那些事件'#单数复数
            自身.所属上下文.日志.警告(
                'claude-code-mods：'+模组['name']+'：on('+列出+') 已登记，但这个宿主从不引发'+哪句
            )#警告
        def 卸下():
            '卸掉这份模组的钩子并取消它的定时器'
            自身.引擎.卸载(模组['name'])#卸掉
        return 卸下#挂载方拿去当拆除器

def 应用(上下文,配置值=None):
    '构造桥。配置缺省时按模式补齐'
    if 配置值 is None:#加载器没给
        配置值=配置模式.校验数据(None)#缺省
    克劳德代码模组(上下文,配置值)#登记服务

name='claude-code-mods'#插件名
inject=['workingDirectory']#会话目录
apply=应用#函数插件入口
Config=配置模式#配置校验
default=应用#加载器只取 default
应用.name=name#default 是函数时，加载器从函数上读这些槽
应用.inject=inject#依赖
应用.Config=Config#配置
