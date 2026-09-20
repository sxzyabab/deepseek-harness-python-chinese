"""面向模型的持久 pwsh 工具。

与 bash 持久化工具共享 PTY 轮询与重置契约；仅包装命令、提示符与工具名不同。
"""
import re,uuid,threading,weakref#正则、标记、线程与弱表
from concurrent.futures import Future as 原生结果#单次操作结果
from ..工具_bash持久化 import (
    保留滚回,#拼滚回
    渲染已抽,#抽出输出渲染
    渲染壳退出状态,#壳退出渲染
    暂停,#轮询间隔
)#共用滚回与渲染
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from ...内核.工具 import 定义工具#工具定义
from ...工具.超时 import 截止,取超时,中止控制器,合成信号,已中止,若已中止则抛出#超时与中止

__all__=['名称','依赖','配置','应用']#公开面

壳提示符='__DSH_PERSISTENT_PWSH_PROMPT__ '#pwsh 提示符
超时码='PERSISTENT_PWSH_TIMEOUT'#超时码
壳重置说明='The persistent pwsh shell was reset; the next pwsh call starts from the workspace with a fresh current directory and environment.'#重置说明
默认描述='Run commands in a persistent PowerShell shell. State, including the current directory and exported environment variables, persists across calls for this agent.'#默认描述
pwsh提示符安装="function prompt { [Console]::Write([char]27 + ']133;D;' + [int]$LASTEXITCODE + [char]7); '"+壳提示符+"' }"#初始化
名称='tool-pwsh-persistent'#Cordis 插件名
依赖=['tools','terminals']#依赖工具与终端
配置={#配置模式
    'backendType':字符串字段(默认值='shell'),#后端类型
    'timeoutMs':数字字段(默认值=300000),#默认超时
    'maxOutputChars':数字字段(默认值=16000),#输出字节预算（配置键为线协议英文）
    'description':字符串字段(默认值=默认描述),#工具描述
}#结束
滚回页行数=1000#滚回页行数
安全整数上限=9007199254740991#外来 JSON 校验点
退出码模式=re.compile(r'^([0-9]+)\r?\n',re.ASCII)#结束退出码
末尾换行模式=re.compile(r'\r?\n\Z')#尾换行
开头换行模式=re.compile(r'^\r?\n')#开头换行

class 持久pwsh错误(Exception):#本包异常基类
    """持久 pwsh 工具入参、配置或壳生命周期失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

class 操作任务:#单次操作结果
    """单次操作的 Future 包装，只留等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身.未来=原生结果()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身.未来.done():#尚未结算
            自身.未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身.未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身.未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身.未来.set_exception(持久pwsh错误(错误))#包装拒绝

    def 等待(自身,超时=None):#阻塞等待
        """阻塞到结算。"""
        return 自身.未来.result(timeout=超时)#取结果或抛错

def 全部结算(任务列表):#等全部落定，吞掉失败
    """并发原语按本包持有：等全部落定，吞掉失败。"""
    for 任务 in 任务列表:#逐路
        try:#等待
            任务.等待()#等待
        except BaseException:#排空不抛
            pass#排空不抛

def 收成pwsh引号(值):#把字符串收成 pwsh 转义
    """把字符串收成 PowerShell 双引号转义。"""
    return (值.replace('`','``').replace('"','`"').replace('$','`$').replace('\r','').replace('\n','`n').replace('\x1b','`e'))#转义

def 命令标记():#生成本次命令的唯一起止标记
    """生成本次命令的唯一起止标记。"""
    一次性=str(uuid.uuid4())#一次性随机串
    return {#标记对
        'start':'__DSH_PERSISTENT_PWSH_START_'+一次性+'__',#开始
        'end':'__DSH_PERSISTENT_PWSH_END_'+一次性+':',#结束
    }#返回

def 包装命令(命令,标记):#把用户命令包进打印标记与退出码的一行
    """把用户命令包进打印标记与退出码的一行。"""
    体=收成pwsh引号(命令)#转义体
    return ("Write-Output '"+标记['start']+"'; $LASTEXITCODE = $null; $__s = 1; try { Invoke-Expression \""+体+"\"; $__ok = $? } catch { $__ok = $false }; if ($null -ne $LASTEXITCODE) { $__s = [int]$LASTEXITCODE } else { $__s = if ($__ok) { 0 } else { 1 } }; Write-Output ('"+标记['end']+"' + $__s)")#一行包装

def 剥提示符(文本):#剥掉末尾提示符和尾换行
    """剥掉末尾提示符和尾换行。"""
    结果=末尾换行模式.sub('',文本,count=1)#去尾换行
    while 结果.endswith(壳提示符):#末尾还是提示符
        结果=结果[:-len(壳提示符)]#剥提示符
    if 结果.endswith('\n'):#再去换行
        return 结果[:-1]#去掉尾换行
    return 结果#返回

def 去掉开头换行(文本):#去掉开头的一次换行
    """去掉开头的一次换行。"""
    return 开头换行模式.sub('',文本,count=1)#只换第一处

def 命令输出(快照,标记):#从滚回抽出完整命令输出
    """从滚回抽出完整命令输出；尚未打完退出码则返回 None。"""
    文本=快照['text']#滚回
    结束=文本.rfind(标记['end'])#结束标记
    状态匹配=退出码模式.match(文本[结束+len(标记['end']):]) if 结束>=0 else None#退出码
    if 状态匹配 is None:#未完成
        return None#未完成
    开始标记=文本.rfind(标记['start'],0,结束)#开始
    起点=0 if 开始标记<0 else 开始标记+len(标记['start'])#起点
    正文=剥提示符(去掉开头换行(文本[起点:结束]))#正文
    return {'text':正文,'incomplete':开始标记<0,'exitCode':int(状态匹配.group(1))}#输出

def 提示符已完成(结果):#视口是否停在提示符
    """视口是否停在提示符。"""
    视口=结果['viewport']#视口
    if 视口.endswith(壳提示符):#裸提示符
        return True#完成
    if 视口.endswith(壳提示符+'\r\n'):#提示符加CRLF
        return True#完成
    if 视口.endswith(壳提示符+'\n'):#提示符加LF
        return True#完成
    return False#未完成

def 部分输出(快照,标记,回退,回退已截=False):#命令未完时尽量抽出已有输出
    """命令未完时尽量抽出已有输出。"""
    开始标记=快照['text'].rfind(标记['start'])#开始
    if 开始标记>=0:#滚回里找到了开始
        return {'text':剥提示符(去掉开头换行(快照['text'][开始标记+len(标记['start']):])),'incomplete':False}#从开始后切
    回退开始=回退.rfind(标记['start'])#回退开始
    if 回退开始<0:#没找到开始
        开始后=回退#整段
    else:#从开始后切
        开始后=去掉开头换行(回退[回退开始+len(标记['start']):])#正文
    回退结束=开始后.rfind(标记['end'])#结束
    if 回退结束<0:#没有结束
        结束前=开始后#整段
    else:#结束前
        结束前=开始后[:回退结束]#截断
    return {'text':剥提示符(结束前.replace(壳提示符,'')),'incomplete':回退已截 or 回退开始<0}#返回

def 执行命令(上下文,壳表,所有者,命令,配置值,上游):#在持久壳里跑一条命令
    """在持久壳里跑一条命令并返回面向模型的文本。"""
    命令截止=截止(上游,配置值['timeoutMs'],超时码)#截止
    try:#执行循环
        会话编号=壳表['get'](所有者,命令截止.信号).等待()#拿壳
        标记=命令标记()#标记
        已包装=包装命令(命令,标记)#包装
        首次=True#第一次才提交
        回退=''#回退
        回退已截=False#回退是否被截
        while True:#轮询
            try:#发送
                操作=上下文.terminals.开始发送(所有者,会话编号,{#向PTY发送
                    'text':已包装 if 首次 else '',#第一次发包装命令
                    'submit':首次,#第一次才提交
                    'signal':命令截止.信号,#跟截止
                })#开始发送结束
                首次=False#之后不再提交
                结果=操作.done.等待()#等这一轮
            except BaseException as 错误:#发送失败
                壳表['reset'](所有者,'persistent pwsh send failed')#丢掉这个壳
                raise 错误#原样抛出
            增量=操作.读取输出()#读增量
            增量文本=增量['delta']#增量正文
            if len(增量文本)>0:#有增量
                回退=回退+增量文本#累加
            else:#否则用视口
                回退=结果['viewport']#视口
            回退已截=回退已截 or 增量['truncated'] is True or 结果['truncated'] is True#截断
            最新=上下文.terminals.读取(所有者,会话编号,{'offset':0,'count':滚回页行数})#最新页
            已超时=取超时(命令截止.信号,超时码)#是否超时
            if 已超时 is not None:#超时
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                部分=渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])#部分输出
                壳表['reset'](所有者,'persistent pwsh command timed out')#超时重置
                秒数=round(已超时.timeoutMs/1000.0)#超时秒数
                return '\n'.join([#超时说明
                    'Your command timed out after '+str(秒数)+' seconds or experienced an OOM error. Below is partial output:',#说明
                    部分,#部分
                    壳重置说明,#重置
                ])#拼成一段
            if 已中止(命令截止.信号):#取消
                壳表['reset'](所有者,'persistent pwsh command aborted')#丢掉这个壳
                若已中止则抛出(命令截止.信号)#按取消抛出
            if 标记['end'] in 最新['text']:#见到结束标记
                完整=命令输出(保留滚回(上下文,所有者,会话编号,最新),标记)#抽出
                if 完整 is not None:#齐了
                    return 渲染已抽(完整,配置值['maxOutputChars'])#渲染
            会话状态=结果['sessionStatus']#会话状态
            if 会话状态['kind']=='exited':#壳退出
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                壳表['reset'](所有者,'persistent pwsh shell exited')#清缓存
                段=渲染壳退出状态(#退出原因
                    渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars']),#部分输出
                    会话状态['exitCode'] if 'exitCode' in 会话状态 else None,#退出码
                    会话状态['signal'] if 'signal' in 会话状态 else None,#信号
                )#渲染结束
                return '\n'.join([段,壳重置说明])#拼上重置
            if 提示符已完成(结果):#回到提示符
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                return 渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])#部分输出
            暂停()#再等一轮
    finally:#拆除定时器
        命令截止.释放()#释放

def 持久pwsh壳表(上下文,配置值):#按所有者缓存 pwsh 壳
    """按所有者缓存持久壳。所有者按对象身份认。"""
    进行中=weakref.WeakKeyDictionary()#进行中的创建
    存活=weakref.WeakKeyDictionary()#已活着的会话
    创建中=set()#拆除时要等完的创建
    已装所有者拆除=weakref.WeakSet()#已给所有者装过拆除
    生命周期=中止控制器()#插件拆除时中止创建

    def 关闭(所有者,会话编号,原因):#关掉一个会话
        """关掉一个会话。"""
        名单=上下文.terminals.列出(所有者)#名单
        仍在=False#是否仍在
        for 快照 in 名单:#逐条
            if 快照['sessionId']==会话编号:#命中
                仍在=True#仍在
                break#停
        if not 仍在:#已经不在
            return#无需关
        上下文.terminals.关闭(所有者,会话编号,原因)#关掉

    def 副作用体():#插件拆除时清掉所有壳
        """登记插件拆除清壳。"""
        def 拆除():#清掉所有壳
            """插件拆除时清掉所有壳。"""
            生命周期.中止(持久pwsh错误('tool-pwsh-persistent disposed during shell creation'))#中止创建
            全部结算(list(创建中))#等创建结束
            for 所有者,会话编号 in list(存活.items()):#关掉存活
                关闭(所有者,会话编号,'tool-pwsh-persistent disposed')#关掉
            存活.clear()#清空
        return 拆除#拆除器
    上下文.副作用(副作用体,'tool-pwsh-persistent shell cleanup')#插件拆除清壳

    def 重置(所有者,原因):#丢掉该所有者的壳
        """丢掉该所有者的壳。"""
        进行中.pop(所有者,None)#去掉进行中
        会话编号=存活.pop(所有者,None)#取出
        if 会话编号 is not None:#有会话
            关闭(所有者,会话编号,原因)#关掉

    def 获取(所有者,信号):#拿到或创建该所有者的壳
        """拿到或创建该所有者的壳。"""
        if 所有者 in 进行中:#已有进行中
            return 进行中[所有者]#复用
        if 信号 is None:#未给取消
            组合信号=生命周期.信号#只跟拆除
        else:#两路
            组合信号=合成信号(信号,生命周期.信号)#合成
        创建=操作任务()#创建任务
        创建中.add(创建)#拆除时要等
        进行中[所有者]=创建#复用
        def 拉起并初始化():#拉起并初始化
            """拉起并初始化持久壳。"""
            try:#拉起
                头=所有者.session.header#会话头
                工作目录=头['cwd'] if 'cwd' in 头 else None#工作目录
                规格={'type':配置值['backendType']}#后端类型
                if 工作目录 is not None:#有cwd
                    规格['cwd']=工作目录#带上
                拉起=上下文.terminals.搭建(所有者,规格,组合信号)#搭建
                会话编号=拉起['sessionId']#会话id
                存活[所有者]=会话编号#记下
                if 所有者 not in 已装所有者拆除:#还没装拆除
                    已装所有者拆除.add(所有者)#记下
                    def 所有者副作用体():#所有者拆除清缓存
                        """登记所有者拆除清缓存。"""
                        def 清缓存():#清缓存
                            """所有者上下文拆除时清缓存。"""
                            进行中.pop(所有者,None)#去掉进行中
                            存活.pop(所有者,None)#去掉存活
                        return 清缓存#拆除器
                    所有者.ctx.副作用(所有者副作用体,'tool-pwsh-persistent owner cache cleanup')#所有者拆除
                发送=上下文.terminals.开始发送(所有者,会话编号,{#设提示符
                    'text':pwsh提示符安装,#初始化命令
                    'submit':True,#提交
                    'signal':组合信号,#信号
                })#开始发送结束
                结果=发送.done.等待()#等初始化
                会话状态=结果['sessionStatus']#会话状态
                if 会话状态['kind']=='exited' or 结果['waitReason']=='timeout':#初始化失败
                    raise 持久pwsh错误('persistent pwsh shell did not accept initialization')#失败
                创建.兑现(会话编号)#返回会话id
            except BaseException as 错误:#失败
                重置(所有者,'persistent pwsh initialization failed')#清半成品
                创建.拒绝(错误)#拒绝
            finally:#结束
                创建中.discard(创建)#摘掉
        工作=threading.Thread(target=拉起并初始化)#创建线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 创建#创建任务

    return {'get':获取,'reset':重置}#交出

def 是否正安全整数(值):#配置入口的安全整数校验
    """外来配置校验：正整数且不超过 JS 安全整数上限；布尔先排除。"""
    if isinstance(值,bool):#布尔不是数字
        return False#不是
    if isinstance(值,int):#整数
        return 值>0 and 值<=安全整数上限#正且安全
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>0 and 值<=安全整数上限#正且安全
    return False#其它

def 登记持久pwsh(上下文,配置值):#注册工具
    """注册面向模型的持久 pwsh 工具。"""
    壳表=持久pwsh壳表(上下文,配置值)#壳管家
    队列=weakref.WeakKeyDictionary()#串行队列

    def 串行(所有者,操作):#同一所有者串行
        """同一所有者上串行执行。"""
        先前=队列[所有者] if 所有者 in 队列 else None#上一条
        运行=操作任务()#本条
        尾巴=操作任务()#尾巴
        def 接龙():#接上一条
            """无论上一条成败都跑本条。"""
            try:#等上一条
                if 先前 is not None:#有上一条
                    try:#等
                        先前.等待()#等上一条
                    except BaseException:#失败也继续
                        pass#吞掉
                try:#跑本条
                    运行.兑现(操作())#兑现
                except BaseException as 错误:#失败
                    运行.拒绝(错误)#拒绝
            finally:#结束
                尾巴.兑现(None)#尾巴落定
        队列[所有者]=尾巴#记下
        接龙()#开跑
        try:#等本条
            return 运行.等待()#结果
        finally:#结束后
            if 所有者 in 队列 and 队列[所有者] is 尾巴:#自己的尾巴
                队列.pop(所有者,None)#删掉

    def 渲染(_参数,值):#原样文本块
        """原样文本块。"""
        return [{'type':'text','text':值}]#文本块

    def 执行(参数,执行上下文):#执行一条持久pwsh
        """执行一条持久 pwsh。"""
        if len(参数['command'].strip())==0:#空命令
            raise 持久pwsh错误('command must be a non-empty string')#拒绝
        所有者=执行上下文['agent'] if 'agent' in 执行上下文 else None#所有者
        if 所有者 is None:#必须有会话
            raise 持久pwsh错误('pwsh requires an owning agent session')#拒绝
        def 本条():#进队列后仍可能已取消
            """进队列后仍可能已取消。"""
            若已中止则抛出(执行上下文['signal'] if 'signal' in 执行上下文 else None)#取消
            return 执行命令(上下文,壳表,所有者,参数['command'],配置值,执行上下文['signal'] if 'signal' in 执行上下文 else None)#跑命令
        return 串行(所有者,本条)#串行

    def 呈现调用(参数):#调用卡片
        """调用卡片标题是命令。"""
        return {'card':'terminal','title':参数['command']}#终端卡片

    上下文.tools.登记(定义工具({#注册pwsh
        'name':'pwsh',#工具名
        'description':配置值['description'],#描述
        'parameters':{#参数
            'command':{#命令
                'type':'string',#字符串
                'required':True,#必填
                'description':'The PowerShell command to run. Relative path is preferred in the command.',#说明
            },#command结束
        },#parameters结束
        'output':{#输出
            'schema':{'type':'string'},#字符串
            'render':渲染,#渲染
        },#output结束
        'execute':执行,#执行
        'presentCall':呈现调用,#卡片
    }))#登记结束

def 应用(上下文,配置值):#加载持久pwsh工具插件
    """注册一个按所有者隔离的持久 pwsh 工具。"""
    if 配置值 is None:#未传
        配置值={}#空配置
    已解析={#填默认
        'backendType':配置值['backendType'] if 'backendType' in 配置值 and 配置值['backendType'] is not None else 'shell',#后端
        'timeoutMs':配置值['timeoutMs'] if 'timeoutMs' in 配置值 and 配置值['timeoutMs'] is not None else 300000,#超时
        'maxOutputChars':配置值['maxOutputChars'] if 'maxOutputChars' in 配置值 and 配置值['maxOutputChars'] is not None else 16000,#上限
        'description':配置值['description'] if 'description' in 配置值 and 配置值['description'] is not None else 默认描述,#描述
    }#结束
    if len(已解析['backendType'].strip())==0:#空后端
        raise 持久pwsh错误('tool-pwsh-persistent: backendType must be non-empty')#拒绝
    if not 是否正安全整数(已解析['timeoutMs']):#超时非法
        raise 持久pwsh错误('tool-pwsh-persistent: timeoutMs must be a positive safe integer')#拒绝
    if not 是否正安全整数(已解析['maxOutputChars']):#上限非法
        raise 持久pwsh错误('tool-pwsh-persistent: maxOutputChars must be a positive safe integer')#拒绝
    if len(已解析['description'].strip())==0:#空描述
        raise 持久pwsh错误('tool-pwsh-persistent: description must be non-empty')#拒绝
    登记持久pwsh(上下文,已解析)#注册

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#框架槽
