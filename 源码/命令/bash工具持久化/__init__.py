"""面向模型的持久 bash 工具，叠在按所有者隔离的 PTY 能力缝上。

对齐上游 `@deepseek-ai/dsh-tool-bash-persistent`。公开面仅中文名。配置键与诊断英文字面量保持上游。
"""
import re,time,uuid,threading,weakref#正则、轮询休眠、随机标记、中止锁与弱表
from schemastery import 模式#配置校验库
from tools import 定义工具#定义面向模型的工具
from timeout import 截止,取超时#命令截止与超时原因
from cordis.工具 import 已兑现,承诺,是否thenable#立刻兑现、承诺与可等待判定

__all__=['名称','注入','配置','应用','默认']#仅中文公开名

# TODO: 替换文件搜索建议；任意命令输出不必来自可搜索文件。
截断说明='<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>'#截断后追加给模型的说明
丢失前缀说明='<response clipped><NOTE>The beginning of this command output was dropped by the terminal scrollback limit. The following text is the earliest retained output.</NOTE>\n'#滚回丢掉开头时的说明
壳重置说明='The persistent bash shell was reset; the next bash call starts from the workspace with a fresh current directory and environment.'#壳被重置后告诉模型的说明
壳提示符='__DSH_PERSISTENT_BASH_PROMPT__ '#持久 bash 的提示符标记
超时码='PERSISTENT_BASH_TIMEOUT'#超时原因码
#一页足够找到刚发出的完成标记；整段滚回只在命令结算或需要部分输出时拼起来
滚回页行数=1000#每次读取的滚回页行数
轮询间隔毫秒=25#轮询间隔毫秒
默认描述='Run commands in a persistent bash shell. State, including the current directory and exported environment variables, persists across calls for this agent.'#默认工具描述
安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER
生成UUID=uuid.uuid4#随机UUID
退出码模式=re.compile(r'^(\d+)\r?\n')#结束标记后的退出码
末尾换行模式=re.compile(r'\r?\n$')#末尾换行
名称='tool-bash-persistent'#Cordis插件名（字面量）
注入=['tools','terminals']#依赖工具与终端
配置=模式.对象({#持久Bash工具配置
    'backendType':模式.字符串().默认('shell'),#默认shell后端
    'timeoutMs':模式.数字().默认(300000),#默认300秒
    'maxOutputChars':模式.数字().默认(16000),#默认16000字符
    'description':模式.字符串().默认(默认描述),#默认工具描述
})#配置模式结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#落在安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=安全整数上限#落在安全范围
    return False#其它类型

def 已中止(信号):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#无信号
    if getattr(信号,'aborted',False):#英文旗标
        return True#英文旗标
    if getattr(信号,'已中止',False):#中文旗标
        return True#中文旗标
    return False#未中止

def 中止原因(信号):#取出中止原因
    """取出中止原因。"""
    if 信号 is None:#无信号
        return None#无信号
    原因=getattr(信号,'reason',None)#英文原因
    if 原因 is not None:#有英文原因
        return 原因#英文原因
    return getattr(信号,'原因',None)#中文原因

def 听中止(信号,回调):#登记一次性abort回调
    """登记一次性 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'addEventListener'):#Web API
        信号.addEventListener('abort',回调,{'once':True})#听一次
        return#已登记
    if hasattr(信号,'加入监听'):#中文API
        信号.加入监听('abort',回调,{'once':True})#听一次

def 抛若中止(信号):#已中止则抛出原因
    """已中止则抛出原因。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'throwIfAborted'):#英文API
        信号.throwIfAborted()#英文API
        return#已抛或仍活
    if hasattr(信号,'抛若中止'):#中文API
        信号.抛若中止()#中文API
        return#已抛或仍活
    if not 已中止(信号):#仍活着
        return#仍活着
    原因=中止原因(信号)#中止原因
    if isinstance(原因,BaseException):#已是异常
        raise 原因#原样抛
    错=Exception('aborted')#非异常则包装
    错.cause=原因#挂上原因
    raise 错#抛出

def 全部结算(任务列表):#对齐Promise.allSettled
    """等全部落定，吞掉失败。"""
    for 任务 in 任务列表:#逐路
        try:#等待
            解开(任务)#等待
        except Exception:#排空不抛
            pass#排空不抛

class 中止信号:#可监听的取消通道
    """对应 AbortSignal；公开方法仅中文。读外来信号时由 已中止/听中止 兼容英文字段。"""
    def __init__(自身,已中止旗=False):#创建一条取消通道
        """初始化未中止状态。"""
        自身.已中止=已中止旗#中止旗标
        自身.原因=None#中止原因
        自身._监听=[]#回调表
        自身._锁=threading.Lock()#并发锁

    def 触发(自身,原因=None):#标记中止并通知
        """标记中止并通知。"""
        with 自身._锁:#并发锁
            if 自身.已中止:#只触发一次
                return#只触发一次
            自身.已中止=True#旗标
            自身.原因=原因#原因
            回调们=list(自身._监听)#拷贝
            自身._监听=[]#清空
        for 回调 in 回调们:#通知
            回调()#通知

    def 加入监听(自身,事件名,回调,选项=None):#登记 abort 回调
        """登记 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#只支持 abort
        立刻=False#是否已中止
        with 自身._锁:#并发锁
            if 自身.已中止:#已中止
                立刻=True#锁外调用
            else:#尚未中止
                自身._监听.append(回调)#登记
        if 立刻:#已中止需立刻通知
            回调()#立刻通知

    def 移除监听(自身,事件名,回调):#去掉 abort 回调
        """去掉 abort 回调。"""
        if 事件名!='abort':#只支持 abort
            return#只支持 abort
        with 自身._锁:#并发锁
            自身._监听=[项 for 项 in 自身._监听 if 项 is not 回调]#按引用删除

    def 抛若中止(自身):#已中止则抛出原因
        """已中止则抛出原因。"""
        if not 自身.已中止:#仍活着
            return#仍活着
        原因=自身.原因#中止原因
        if isinstance(原因,BaseException):#已是异常
            raise 原因#原样抛
        错=Exception('aborted')#非异常则包装
        错.cause=原因#挂上原因
        raise 错#抛出

    @staticmethod#静态方法
    def 任一(信号列表):#最先中止的那路胜出
        """最先中止的那路胜出。"""
        融合=中止控制器()#融合控制器
        for 信号 in 信号列表:#已中止则立刻胜出
            if 已中止(信号):#已中止
                融合.中止(中止原因(信号))#已中止则立刻胜出
                return 融合.信号#已中止的融合信号
        def 绑定(来源):#转发某一路中止
            """转发某一路中止。"""
            def 转发(*位置参数):#把来源原因交给融合控制器
                """把来源原因交给融合控制器。"""
                融合.中止(中止原因(来源))#转发原因
            return 转发#该路回调
        for 信号 in 信号列表:#只听一次
            听中止(信号,绑定(信号))#只听一次
        return 融合.信号#融合信号

class 中止控制器:#发出中止的控制器
    """对应 AbortController；公开方法仅中文。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 或许截断(内容,最大输出字符,不完整=False):#按上限截断并追加说明
    """按上限截断并追加说明。"""
    if len(内容)<=最大输出字符 and not 不完整:#未超且完整则原样
        return 内容#原样
    if len(内容)<=最大输出字符:#仍未超长
        return 内容+截断说明#完整但调用方标了不完整，只追加说明
    return 内容[:最大输出字符]+截断说明#超长则切尾巴再追加说明

def 命令标记():#生成本次命令的唯一起止标记
    """生成本次命令的唯一起止标记。"""
    一次性=str(生成UUID())#一次性随机串
    return {#标记对
        'start':'__DSH_PERSISTENT_BASH_START_'+一次性+'__',#开始标记
        'end':'__DSH_PERSISTENT_BASH_END_'+一次性+':',#结束标记前缀，后面跟退出码
    }#返回结束

def 收成Bash引号(值):#把字符串收成bash ANSI-C引号
    """把字符串收成 bash ANSI-C 引号。"""
    return "$'"+值.replace('\\','\\\\').replace("'","\\'").replace('\r','\\r').replace('\n','\\n')+"'"#转义后合上引号

def 包装命令(命令,标记):#把用户命令包进打印标记与退出码的一行
    """把用户命令包进打印标记与退出码的一行。包装必须停在一行。交互 bash 遇到嵌入换行会先打 PS2，会把提示符和标记源码漏进面向模型的结果。"""
    return "printf '%s\\n' "+收成Bash引号(标记['start'])+'; eval -- '+收成Bash引号(命令)+'; __dsh_persistent_bash_status=$?; printf \'%s%s\\n\' '+收成Bash引号(标记['end'])+' "$__dsh_persistent_bash_status"'#打印开始标记、eval命令、记下状态、打印结束标记加退出码

def 剥提示符(文本):#剥掉末尾提示符和尾换行
    """剥掉末尾提示符和尾换行。"""
    结果=末尾换行模式.sub('',文本)#先去掉末尾换行
    while 结果.endswith(壳提示符):#末尾还是提示符
        结果=结果[:-len(壳提示符)]#切掉一层提示符
    if 结果.endswith('\n'):#再去一层尾换行
        return 结果[:-1]#去掉尾换行
    return 结果#已干净

def 命令输出(快照,标记):#从滚回抽出完整命令输出
    """从滚回抽出完整命令输出；尚未打完退出码则返回 None。"""
    文本=快照['text']#滚回文本
    结束=文本.rfind(标记['end'])#最后一次结束标记
    状态匹配=退出码模式.match(文本[结束+len(标记['end']):]) if 结束>=0 else None#结束标记后的退出码
    if 状态匹配 is None:#还没打完退出码
        return None#未完成
    开始标记=文本.rfind(标记['start'],0,结束)#结束标记前的开始标记
    起点=0 if 开始标记<0 else 开始标记+len(标记['start'])#没有开始标记则从0
    正文=剥提示符(re.sub(r'^\r?\n','',文本[起点:结束]))#正文去提示符和开头换行
    return {#抽出的输出
        'text':正文,#正文
        'incomplete':开始标记<0,#缺开始标记则开头丢了
        'exitCode':int(状态匹配.group(1)),#退出码
    }#返回结束

def 提示符已完成(结果):#视口是否停在提示符
    """视口是否停在提示符。"""
    视口=取字段(结果,'viewport')#视口文本
    if 视口.endswith(壳提示符):#裸提示符
        return True#完成
    if 视口.endswith(壳提示符+'\r\n'):#提示符加CRLF
        return True#完成
    if 视口.endswith(壳提示符+'\n'):#提示符加LF
        return True#完成
    return False#未完成

def 部分输出(快照,标记,回退,回退已截=False):#命令未完时尽量抽出已有输出
    """命令未完时尽量抽出已有输出。"""
    开始标记=快照['text'].rfind(标记['start'])#滚回里的开始标记
    if 开始标记>=0:#滚回里找到了开始
        return {#从开始标记后切
            'text':剥提示符(re.sub(r'^\r?\n','',快照['text'][开始标记+len(标记['start']):])),#正文
            'incomplete':False,#滚回里有开始标记，开头还在
        }#滚回分支结束
    回退开始=回退.rfind(标记['start'])#增量回退里的开始标记
    if 回退开始<0:#没找到开始
        开始后=回退#整段当正文
    else:#从开始后切
        开始后=re.sub(r'^\r?\n','',回退[回退开始+len(标记['start']):])#从开始后切
    回退结束=开始后.rfind(标记['end'])#回退里的结束标记
    if 回退结束<0:#没有结束标记
        结束前=开始后#整段
    else:#结束标记前
        结束前=开始后[:回退结束]#结束标记前
    return {#用回退拼出的部分输出
        'text':剥提示符(结束前.replace(壳提示符,'')),#去掉提示符
        'incomplete':回退已截 or 回退开始<0,#回退被截或没开始标记则不完整
    }#返回结束

def 暂停():#等一轮询间隔
    """等一轮询间隔。"""
    time.sleep(轮询间隔毫秒/1000)#定时休眠

def 下一滚回偏移(页,偏移):#下一页滚回起点
    """下一页滚回起点；空页或没前进则 None。"""
    if len(取字段(页,'text'))==0 or 取字段(页,'lineEnd')<=偏移:#空页或没前进
        return None#走不动
    return 取字段(页,'lineEnd')#下一页从本页行尾

def 保留滚回(上下文,所有者,会话编号,最新=None):#从最新页往回拼完整保留滚回
    """从最新页往回拼完整保留滚回。"""
    if 最新 is None:#调用方没给最新页
        最新=上下文.terminals.read(所有者,会话编号,{'offset':0,'count':滚回页行数})#读最新一页
    if len(取字段(最新,'text'))==0:#空页
        页们=[]#无页
    else:#已有页
        页们=[取字段(最新,'text')]#已有页
    偏移=取字段(最新,'lineEnd')#下一页起点
    已截=bool(取字段(最新,'truncated'))#是否已被截
    while True:#一直往更早的页走
        if 偏移>=取字段(最新,'totalLines'):#已经盖到总行数
            break#停
        页=上下文.terminals.read(所有者,会话编号,{'offset':偏移,'count':滚回页行数})#再读一页
        已截=已截 or bool(取字段(页,'truncated'))#任一页截断则记下
        if len(取字段(页,'text'))>0:#非空页
            页们.insert(0,取字段(页,'text'))#插到前面
        下一=下一滚回偏移(页,偏移)#下一页起点
        if 下一 is None or 下一>=取字段(页,'totalLines'):#走不动了
            break#停
        偏移=下一#继续更早
    return {'text':'\n'.join(页们),'truncated':已截}#拼成一段文本

def 追加状态标记(内容,标记):#把状态标记接到正文后
    """把状态标记接到正文后。"""
    if 标记 is None:#没有标记
        return 内容#原文
    if len(内容)==0:#空正文
        return 标记#只有标记
    return 内容+'\n'+标记#换行再接

def 渲染已抽(输出,最大输出字符):#把抽出的输出渲染给模型
    """把抽出的输出渲染给模型。"""
    已渲染=或许截断(输出['text'],最大输出字符,bool(输出.get('incomplete')))#先截断
    if 输出.get('incomplete') and len(输出['text'])>0:#开头丢了且还有正文
        带前缀=丢失前缀说明+已渲染#加上丢失前缀说明
    else:#否则只用截断后文本
        带前缀=已渲染#截断后文本
    退出码=输出.get('exitCode')#可选退出码
    if 退出码 is not None and 退出码!=0:#非零退出
        标记='[exit code: '+str(退出码)+']'#退出码标记
    else:#零退出或没有退出码
        标记=None#不加
    return 追加状态标记(带前缀,标记)#正文后追加状态标记

def 渲染壳退出状态(内容,退出码,信号):#壳退出时追加退出原因
    """壳退出时追加退出原因。"""
    if 信号 is not None:#被信号杀死
        标记='[shell killed by signal: '+str(信号)+']'#信号标记
    elif 退出码 is not None:#有退出码
        标记='[shell exited: code '+str(退出码)+']'#退出码标记
    else:#只知道退出了
        标记='[shell exited]'#只知道退出了
    return 追加状态标记(内容,标记)#接到正文后

def 持久壳们(上下文,配置值):#按所有者缓存持久壳
    """按所有者缓存持久壳，交出 get/reset。"""
    进行中=weakref.WeakKeyDictionary()#进行中的创建
    存活={}#已活着的会话
    创建中=set()#拆除时要等完的创建
    已装所有者拆除=weakref.WeakSet()#已给所有者装过拆除
    生命周期=中止控制器()#插件拆除时中止创建

    def 关闭(所有者,会话编号,原因):#杀掉一个会话
        """杀掉一个会话。"""
        名单=上下文.terminals.list(所有者)#该所有者的会话名单
        仍在=False#是否仍在名单
        for 快照 in 名单:#逐条
            if 取字段(快照,'sessionId')==会话编号:#命中
                仍在=True#仍在
                break#停扫
        if not 仍在:#已经不在名单里
            return#无需杀
        解开(上下文.terminals.kill(所有者,会话编号,原因))#按原因杀掉

    def 副作用体():#插件拆除时清掉所有壳
        """登记插件拆除清壳。"""
        def 拆除():#清掉所有壳
            """插件拆除时清掉所有壳。"""
            生命周期.中止(Exception('tool-bash-persistent disposed during shell creation'))#中止进行中的创建
            全部结算(list(创建中))#等创建结束
            for 所有者,会话编号 in list(存活.items()):#并行关掉存活会话
                关闭(所有者,会话编号,'tool-bash-persistent disposed')#关掉
            存活.clear()#清空存活表
        return 拆除#拆除器
    上下文.effect(副作用体,'tool-bash-persistent shell cleanup')#插件拆除清壳

    def 重置(所有者,原因):#丢掉该所有者的壳
        """丢掉该所有者的壳。"""
        进行中.pop(所有者,None)#去掉进行中的创建
        会话编号=存活.pop(所有者,None)#取出并从表里拿掉
        if 会话编号 is not None:#有会话则杀掉
            关闭(所有者,会话编号,原因)#杀掉

    def 获取(所有者,信号):#拿到或创建该所有者的壳
        """拿到或创建该所有者的壳。"""
        已有=进行中.get(所有者)#已有进行中的创建
        if 已有 is not None:#复用同一承诺
            return 已有#复用
        组合信号=中止信号.任一([信号,生命周期.信号])#调用取消或插件拆除都算
        创建=承诺()#真正创建承诺
        创建中.add(创建)#拆除时要等它
        进行中[所有者]=创建#给后续调用复用
        def 拉起并初始化():#拉起并初始化
            """拉起并初始化持久壳。"""
            try:#拉起并初始化
                工作目录=取字段(取字段(取字段(所有者,'session'),'header'),'cwd')#会话工作目录
                规格={'type':配置值['backendType']}#按后端类型spawn
                if 工作目录 is not None:#有cwd则带上
                    规格['cwd']=工作目录#带上
                拉起=解开(上下文.terminals.spawn(所有者,规格,组合信号))#跟组合信号
                会话编号=取字段(拉起,'sessionId')#会话id
                存活[所有者]=会话编号#先记进存活表
                if 所有者 not in 已装所有者拆除:#还没给这个所有者装拆除
                    已装所有者拆除.add(所有者)#记下已装
                    def 所有者副作用体():#所有者上下文拆除时清缓存
                        """登记所有者拆除清缓存。"""
                        def 清缓存():#清缓存
                            """所有者上下文拆除时清缓存。"""
                            进行中.pop(所有者,None)#去掉进行中的创建
                            存活.pop(所有者,None)#去掉存活会话
                        return 清缓存#拆除器
                    所有者.ctx.effect(所有者副作用体,'tool-bash-persistent owner cache cleanup')#所有者拆除清缓存
                发送=上下文.terminals.startSend(所有者,会话编号,{#关掉回显并设提示符
                    'text':'stty -echo; PS1='+收成Bash引号(壳提示符),#初始化命令
                    'submit':True,#提交
                    'signal':组合信号,#跟组合信号
                })#startSend结束
                结果=解开(取字段(发送,'done'))#等初始化发完
                会话状态=取字段(结果,'sessionStatus')#会话状态
                if 取字段(会话状态,'kind')=='exited' or 取字段(结果,'waitReason')=='timeout':#壳没活过初始化
                    raise Exception('persistent bash shell did not accept initialization')#初始化失败
                创建.兑现(会话编号)#返回会话id
            except BaseException as 错误:#创建或初始化失败
                重置(所有者,'persistent bash initialization failed')#清掉半成品
                创建.拒绝(错误)#原样拒绝
            finally:#创建结束不论成败
                创建中.discard(创建)#从拆除等待集合摘掉
        工作=threading.Thread(target=拉起并初始化)#创建线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑
        return 创建#返回创建承诺

    return {'get':获取,'reset':重置}#交出按所有者的get/reset

def 执行命令(上下文,壳们,所有者,命令,配置值,上游):#在持久壳里跑一条命令并返回面向模型的文本
    """在持久壳里跑一条命令并返回面向模型的文本。"""
    命令截止=截止(上游,配置值['timeoutMs'],超时码)#套上命令截止
    try:#等到命令结算再拆定时器
        会话编号=解开(壳们['get'](所有者,取字段(命令截止,'signal')))#拿到该所有者的壳
        标记=命令标记()#本次起止标记
        已包装=包装命令(命令,标记)#包成一行
        首次=True#第一次循环才提交命令
        回退=''#增量视口回退
        回退已截=False#回退是否被截
        while True:#轮询直到完成、超时、退出或回到提示符
            try:#发一次（首次带命令，之后空提交只为读）
                操作=上下文.terminals.startSend(所有者,会话编号,{#向PTY发送
                    'text':已包装 if 首次 else '',#第一次发包装命令
                    'submit':首次,#第一次才提交
                    'signal':取字段(命令截止,'signal'),#跟截止信号
                })#startSend结束
                首次=False#之后不再提交命令
                结果=解开(取字段(操作,'done'))#等这一轮发送结束
            except BaseException as 错误:#发送失败
                壳们['reset'](所有者,'persistent bash send failed')#丢掉这个壳
                raise 错误#原样抛出
            增量=操作.readOutput()#读本轮增量
            增量文本=取字段(增量,'delta')#增量正文
            if len(增量文本)>0:#有增量则累加
                回退=回退+增量文本#累加
            else:#否则用视口
                回退=取字段(结果,'viewport')#视口
            回退已截=回退已截 or bool(取字段(增量,'truncated')) or bool(取字段(结果,'truncated'))#任一截断则记下
            最新=上下文.terminals.read(所有者,会话编号,{'offset':0,'count':滚回页行数})#读最新一页滚回
            已超时=取超时(取字段(命令截止,'signal'),超时码)#是否本工具超时
            if 已超时 is not None:#超时
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                部分=渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])#渲染部分输出
                壳们['reset'](所有者,'persistent bash command timed out')#超时后重置壳
                # TODO: 只报告超时；本信号并不能证明发生了 OOM。
                return '\n'.join([#超时说明+部分输出+重置说明
                    'Your command timed out after '+str(round(取字段(已超时,'timeoutMs')/1000))+' seconds or experienced an OOM error. Below is partial output:',#超时说明
                    部分,#部分输出
                    壳重置说明,#壳已重置
                ])#拼成一段
            if 已中止(取字段(命令截止,'signal')):#上游取消
                壳们['reset'](所有者,'persistent bash command aborted')#丢掉这个壳
                抛若中止(取字段(命令截止,'signal'))#按取消抛出
            if 标记['end'] in 取字段(最新,'text'):#最新页已见到结束标记
                完整=命令输出(保留滚回(上下文,所有者,会话编号,最新),标记)#尝试抽出完整输出
                if 完整 is not None:#齐了就渲染返回
                    return 渲染已抽(完整,配置值['maxOutputChars'])#渲染返回
            会话状态=取字段(结果,'sessionStatus')#会话状态
            if 取字段(会话状态,'kind')=='exited':#壳自己退出了
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                壳们['reset'](所有者,'persistent bash shell exited')#清缓存
                段们=[#退出状态+重置说明
                    渲染壳退出状态(#带上退出原因
                        渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars']),#部分输出
                        取字段(会话状态,'exitCode'),#退出码
                        取字段(会话状态,'signal'),#信号
                    ),#渲染壳退出状态结束
                    壳重置说明,#壳已重置
                ]#段们
                return '\n'.join([段 for 段 in 段们 if len(段)>0])#丢掉空段再拼
            if 提示符已完成(结果):#已经回到提示符
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                return 渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])#按部分输出渲染
            暂停()#再等一轮
    finally:#拆除时清掉定时器
        命令截止.释放()#释放已武装定时器

def 登记持久Bash(上下文,配置值):#注册持久bash工具
    """注册面向模型的持久 bash 工具。"""
    壳们=持久壳们(上下文,配置值)#按所有者的壳管家
    队列=weakref.WeakKeyDictionary()#每所有者串行队列

    def 串行(所有者,操作):#同一所有者上串行执行
        """同一所有者上串行执行。"""
        先前=队列.get(所有者)#上一条
        if 先前 is None:#没有上一条
            先前=已兑现(None)#立刻
        运行=承诺()#本条结果
        尾巴=承诺()#吞掉结果，只当队列尾巴
        def 接龙():#无论上一条成败都跑本条
            """无论上一条成败都跑本条。"""
            try:#等上一条
                try:#等上一条
                    解开(先前)#等上一条
                except Exception:#上一条失败也继续
                    pass#吞掉
                try:#跑本条
                    运行.兑现(解开(操作()))#兑现本条
                except BaseException as 错误:#本条失败
                    运行.拒绝(错误)#拒绝本条
            finally:#本条结束后
                尾巴.兑现(None)#尾巴落定
        队列[所有者]=尾巴#记下尾巴
        接龙()#开跑
        try:#等本条
            return 解开(运行)#返回本条结果
        finally:#本条结束后
            if 队列.get(所有者) is 尾巴:#还是自己这条尾巴才删
                队列.pop(所有者,None)#删掉

    def 渲染(_参数,值):#原样文本块
        """原样文本块。"""
        return [{'type':'text','text':值}]#原样文本块

    def 执行(参数,执行上下文):#执行一条持久bash
        """执行一条持久 bash。"""
        if len(取字段(参数,'command').strip())==0:#拒绝空命令
            raise Exception('command must be a non-empty string')#拒绝空命令
        所有者=取字段(执行上下文,'agent')#调用方智能体
        if 所有者 is None:#必须有所有者会话
            raise Exception('bash requires an owning agent session')#必须有所有者会话
        def 本条():#同一所有者串行
            """进队列后仍可能已取消。"""
            抛若中止(取字段(执行上下文,'signal'))#进队列后仍可能已取消
            return 执行命令(上下文,壳们,所有者,取字段(参数,'command'),配置值,取字段(执行上下文,'signal'))#跑命令
        return 串行(所有者,本条)#同一所有者串行

    def 呈现调用(参数):#调用卡片标题是命令
        """调用卡片标题是命令。"""
        return {'card':'terminal','title':取字段(参数,'command')}#终端卡片

    上下文.tools.登记(定义工具({#注册bash工具
        'name':'bash',#工具名
        'description':配置值['description'],#描述
        'parameters':{#参数
            'command':{#命令
                'type':'string',#字符串
                'required':True,#必填
                'description':'The bash command to run. Relative path is preferred in the command.',#命令说明
            },#command结束
        },#parameters结束
        'output':{#输出约定
            'schema':{'type':'string'},#输出是字符串
            'render':渲染,#原样文本块
        },#output结束
        'execute':执行,#执行一条持久bash
        'presentCall':呈现调用,#调用卡片
    }))#bash工具结束

def 应用(上下文,配置值):#加载持久bash工具插件
    """注册一个按所有者隔离的持久 bash 工具。"""
    已解析={#填默认值
        'backendType':取字段(配置值,'backendType') if 取字段(配置值,'backendType') is not None else 'shell',#后端
        'timeoutMs':取字段(配置值,'timeoutMs') if 取字段(配置值,'timeoutMs') is not None else 300000,#超时
        'maxOutputChars':取字段(配置值,'maxOutputChars') if 取字段(配置值,'maxOutputChars') is not None else 16000,#输出上限
        'description':取字段(配置值,'description') if 取字段(配置值,'description') is not None else 默认描述,#描述
    }#resolved结束
    if len(已解析['backendType'].strip())==0:#后端为空
        raise Exception('tool-bash-persistent: backendType must be non-empty')#拒绝空后端
    if (not 是否安全整数(已解析['timeoutMs'])) or 已解析['timeoutMs']<=0:#超时非法
        raise Exception('tool-bash-persistent: timeoutMs must be a positive safe integer')#拒绝非正超时
    if (not 是否安全整数(已解析['maxOutputChars'])) or 已解析['maxOutputChars']<=0:#输出上限非法
        raise Exception('tool-bash-persistent: maxOutputChars must be a positive safe integer')#拒绝非正上限
    if len(已解析['description'].strip())==0:#描述为空
        raise Exception('tool-bash-persistent: description must be non-empty')#拒绝空描述
    登记持久Bash(上下文,已解析)#注册工具
    return#加载完成

apply=应用#Cordis插件入口（协议槽）
default=应用#Cordis默认导出（协议槽）

默认=应用#中文默认导出