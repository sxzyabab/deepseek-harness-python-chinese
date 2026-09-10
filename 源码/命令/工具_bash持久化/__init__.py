"""面向模型的持久 bash 工具，叠在按所有者隔离的 PTY 能力缝上。

对齐上游 `@deepseek-ai/dsh-tool-bash-persistent`。公开面仅中文名。配置键与诊断英文字面量保持上游。
"""
import re,time,uuid,threading,weakref#正则、轮询休眠、随机标记、中止锁与弱表
from concurrent.futures import Future as 原生结果#单次操作结果
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...工具.超时 import 截止,取超时,中止控制器,合成信号,已中止,若已中止则抛出#命令截止与中止通道

__all__=['名称','注入','配置','应用','或许截断','下一滚回偏移','保留滚回','追加状态标记','渲染已抽','渲染壳退出状态','暂停']#仅中文公开名

截断说明='<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>'#截断后追加给模型的说明
丢失前缀说明='<response clipped><NOTE>The beginning of this command output was dropped by the terminal scrollback limit. The following text is the earliest retained output.</NOTE>\n'#滚回丢掉开头时的说明
壳重置说明='The persistent bash shell was reset; the next bash call starts from the workspace with a fresh current directory and environment.'#壳被重置后告诉模型的说明
壳提示符='__DSH_PERSISTENT_BASH_PROMPT__ '#持久 bash 的提示符标记
超时状态标记='[Command timed out or OOM]'#超时或 OOM 状态标记
超时码='PERSISTENT_BASH_TIMEOUT'#超时原因码
滚回页行数=1000#每次读取的滚回页行数
轮询间隔毫秒=25#轮询间隔毫秒
默认描述='Run commands in a persistent bash shell. State, including the current directory and exported environment variables, persists across calls for this agent.'#默认工具描述
安全整数上限=9007199254740991#外来 JSON 校验点对齐 JS Number.MAX_SAFE_INTEGER
名称='tool-bash-persistent'#Cordis插件名（字面量）
注入=['tools','terminals']#依赖工具与终端
配置={#持久Bash工具配置
    'backendType':字符串字段(默认值='shell'),#默认shell后端
    'timeoutMs':数字字段(默认值=300000),#默认300秒
    'maxOutputChars':数字字段(默认值=16000),#默认16000字节预算（配置键沿用上游）
    'description':字符串字段(默认值=默认描述),#默认工具描述
}#配置模式结束
退出码模式=re.compile(r'^([0-9]+)\r?\n',re.ASCII)#结束标记后的退出码
末尾换行模式=re.compile(r'(?:\r?\n)+\Z')#末尾全部换行
开头换行模式=re.compile(r'^\r?\n')#开头换行

class 持久bash错误(Exception):#本包异常基类
    """持久 bash 工具入参、配置或壳生命周期失败。"""
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
                自身.未来.set_exception(持久bash错误(错误))#包装拒绝

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

def 按字节截到边界(文本,最大字节):#按UTF-8字节截断且落在字符边界
    """按 UTF-8 字节预算截断，切点落在字符边界。"""
    编码=文本.encode('utf-8')#UTF-8字节
    if len(编码)<=最大字节:#未超
        return 文本#原样
    切片=编码[:最大字节]#先按字节切
    while len(切片)>0 and (切片[-1]&0xC0)==0x80:#落在后续字节上则回退
        切片=切片[:-1]#丢掉后续字节
    return 切片.decode('utf-8')#解码为文本

def 或许截断(内容,最大输出字节,不完整=False):#按上限截断并追加说明
    """按 UTF-8 字节上限截断并追加说明。"""
    编码=内容.encode('utf-8')#UTF-8字节
    if len(编码)<=最大输出字节 and not 不完整:#未超且完整则原样
        return 内容#原样
    if len(编码)<=最大输出字节:#仍未超长
        return 内容+截断说明#完整但调用方标了不完整，只追加说明
    return 按字节截到边界(内容,最大输出字节)+截断说明#超长则切尾巴再追加说明

def 命令标记():#生成本次命令的唯一起止标记
    """生成本次命令的唯一起止标记。"""
    一次性=str(uuid.uuid4())#一次性随机串
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
    结果=末尾换行模式.sub('',文本)#先去掉末尾全部换行
    while 结果.endswith(壳提示符):#末尾还是提示符
        结果=结果[:-len(壳提示符)]#切掉一层提示符
    if 结果.endswith('\n'):#再去一层尾换行
        return 结果[:-1]#去掉尾换行
    return 结果#已干净

def 去掉开头换行(文本):#去掉开头的CRLF或LF
    """去掉开头的一次换行。"""
    return 开头换行模式.sub('',文本,count=1)#只换第一处

def 命令输出(快照,标记):#从滚回抽出完整命令输出
    """从滚回抽出完整命令输出；尚未打完退出码则返回 None。"""
    文本=快照['text']#滚回文本
    结束=文本.rfind(标记['end'])#最后一次结束标记
    状态匹配=退出码模式.match(文本[结束+len(标记['end']):]) if 结束>=0 else None#结束标记后的退出码
    if 状态匹配 is None:#还没打完退出码
        return None#未完成
    开始标记=文本.rfind(标记['start'],0,结束)#结束标记前的开始标记
    起点=0 if 开始标记<0 else 开始标记+len(标记['start'])#没有开始标记则从0
    正文=剥提示符(去掉开头换行(文本[起点:结束]))#正文去提示符和开头换行
    return {#抽出的输出
        'text':正文,#正文
        'incomplete':开始标记<0,#缺开始标记则开头丢了
        'exitCode':int(状态匹配.group(1)),#退出码
    }#返回结束

def 提示符已完成(结果):#视口是否停在提示符
    """视口是否停在提示符。"""
    视口=结果['viewport']#视口文本
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
            'text':剥提示符(去掉开头换行(快照['text'][开始标记+len(标记['start']):])),#正文
            'incomplete':False,#滚回里有开始标记，开头还在
        }#滚回分支结束
    回退开始=回退.rfind(标记['start'])#增量回退里的开始标记
    if 回退开始<0:#没找到开始
        开始后=回退#整段当正文
    else:#从开始后切
        开始后=去掉开头换行(回退[回退开始+len(标记['start']):])#从开始后切
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
    time.sleep(轮询间隔毫秒/1000.0)#定时休眠

def 下一滚回偏移(页,偏移):#下一页滚回起点
    """下一页滚回起点；空页或没前进则 None。"""
    if len(页['text'])==0 or 页['lineEnd']<=偏移:#空页或没前进
        return None#走不动
    return 页['lineEnd']#下一页从本页行尾

def 保留滚回(上下文,所有者,会话编号,最新=None):#从最新页往回拼完整保留滚回
    """从最新页往回拼完整保留滚回。"""
    if 最新 is None:#调用方没给最新页
        最新=上下文.terminals.读取(所有者,会话编号,{'offset':0,'count':滚回页行数})#读最新一页
    if len(最新['text'])==0:#空页
        页列表=[]#无页
    else:#已有页
        页列表=[最新['text']]#已有页
    偏移=最新['lineEnd']#下一页起点
    已截=最新['truncated'] is True#是否已被截
    while True:#一直往更早的页走
        if 偏移>=最新['totalLines']:#已经盖到总行数
            break#停
        页=上下文.terminals.读取(所有者,会话编号,{'offset':偏移,'count':滚回页行数})#再读一页
        已截=已截 or 页['truncated'] is True#任一页截断则记下
        if len(页['text'])>0:#非空页
            页列表.insert(0,页['text'])#插到前面
        下一=下一滚回偏移(页,偏移)#下一页起点
        if 下一 is None or 下一>=页['totalLines']:#走不动了
            break#停
        偏移=下一#继续更早
    return {'text':'\n'.join(页列表),'truncated':已截}#拼成一段文本

def 追加状态标记(内容,标记):#把状态标记接到正文后
    """把状态标记接到正文后。"""
    if 标记 is None:#没有标记
        return 内容#原文
    if len(内容)==0:#空正文
        return 标记#只有标记
    return 内容+'\n'+标记#换行再接

def 渲染已抽(输出,最大输出字节):#把抽出的输出渲染给模型
    """把抽出的输出渲染给模型。"""
    不完整=输出['incomplete'] if 'incomplete' in 输出 else False#是否缺开头
    已渲染=或许截断(输出['text'],最大输出字节,不完整 is True)#先截断
    if 不完整 is True and len(输出['text'])>0:#开头丢了且还有正文
        带前缀=丢失前缀说明+已渲染#加上丢失前缀说明
    else:#否则只用截断后文本
        带前缀=已渲染#截断后文本
    退出码=输出['exitCode'] if 'exitCode' in 输出 else None#可选退出码
    if 退出码 is not None:#有退出码（含 0）
        标记='[Command finished with exit code '+str(退出码)+']'#完成退出码标记
    else:#没有退出码
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

def 持久壳表(上下文,配置值):#按所有者缓存持久壳
    """按所有者缓存持久壳，交出 get/reset。所有者按对象身份认。"""
    进行中=weakref.WeakKeyDictionary()#进行中的创建
    存活=weakref.WeakKeyDictionary()#已活着的会话
    创建中=set()#拆除时要等完的创建
    已装所有者拆除=weakref.WeakSet()#已给所有者装过拆除
    生命周期=中止控制器()#插件拆除时中止创建

    def 关闭(所有者,会话编号,原因):#关掉一个会话
        """关掉一个会话。"""
        名单=上下文.terminals.列出(所有者)#该所有者的会话名单
        仍在=False#是否仍在名单
        for 快照 in 名单:#逐条
            if 快照['sessionId']==会话编号:#命中
                仍在=True#仍在
                break#停扫
        if not 仍在:#已经不在名单里
            return#无需关
        上下文.terminals.关闭(所有者,会话编号,原因)#按原因关掉

    def 副作用体():#插件拆除时清掉所有壳
        """登记插件拆除清壳。"""
        def 拆除():#清掉所有壳
            """插件拆除时清掉所有壳。"""
            生命周期.中止(持久bash错误('tool-bash-persistent disposed during shell creation'))#中止进行中的创建
            全部结算(list(创建中))#等创建结束
            for 所有者,会话编号 in list(存活.items()):#并行关掉存活会话
                关闭(所有者,会话编号,'tool-bash-persistent disposed')#关掉
            存活.clear()#清空存活表
        return 拆除#拆除器
    上下文.副作用(副作用体,'tool-bash-persistent shell cleanup')#插件拆除清壳

    def 重置(所有者,原因):#丢掉该所有者的壳
        """丢掉该所有者的壳。"""
        进行中.pop(所有者,None)#去掉进行中的创建
        会话编号=存活.pop(所有者,None)#取出并从表里拿掉
        if 会话编号 is not None:#有会话则关掉
            关闭(所有者,会话编号,原因)#关掉

    def 获取(所有者,信号):#拿到或创建该所有者的壳
        """拿到或创建该所有者的壳。"""
        if 所有者 in 进行中:#已有进行中的创建
            return 进行中[所有者]#复用
        if 信号 is None:#调用方未给取消
            组合信号=生命周期.信号#只跟插件拆除
        else:#调用取消与插件拆除都算
            组合信号=合成信号(信号,生命周期.信号)#两路合成
        创建=操作任务()#真正创建任务
        创建中.add(创建)#拆除时要等它
        进行中[所有者]=创建#给后续调用复用
        def 拉起并初始化():#拉起并初始化
            """拉起并初始化持久壳。"""
            try:#拉起并初始化
                头=所有者.session.header#会话头
                工作目录=头['cwd'] if 'cwd' in 头 else None#会话工作目录
                规格={'type':配置值['backendType']}#按后端类型搭建
                if 工作目录 is not None:#有cwd则带上
                    规格['cwd']=工作目录#带上
                拉起=上下文.terminals.搭建(所有者,规格,组合信号)#跟组合信号
                会话编号=拉起['sessionId']#会话id
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
                    所有者.ctx.副作用(所有者副作用体,'tool-bash-persistent owner cache cleanup')#所有者拆除清缓存
                发送=上下文.terminals.开始发送(所有者,会话编号,{#关掉回显并设提示符
                    'text':'stty -echo; PS1='+收成Bash引号(壳提示符),#初始化命令
                    'submit':True,#提交
                    'signal':组合信号,#跟组合信号
                })#开始发送结束
                结果=发送.done.等待()#等初始化发完
                会话状态=结果['sessionStatus']#会话状态
                if 会话状态['kind']=='exited' or 结果['waitReason']=='timeout':#壳没活过初始化
                    raise 持久bash错误('persistent bash shell did not accept initialization')#初始化失败
                创建.兑现(会话编号)#返回会话id
            except BaseException as 错误:#创建或初始化失败
                重置(所有者,'persistent bash initialization failed')#清掉半成品
                创建.拒绝(错误)#原样拒绝
            finally:#创建结束不论成败
                创建中.discard(创建)#从拆除等待集合摘掉
        工作=threading.Thread(target=拉起并初始化)#创建线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑
        return 创建#返回创建任务

    return {'get':获取,'reset':重置}#交出按所有者的get/reset

def 执行命令(上下文,壳表,所有者,命令,配置值,上游):#在持久壳里跑一条命令并返回面向模型的文本
    """在持久壳里跑一条命令并返回面向模型的文本。"""
    命令截止=截止(上游,配置值['timeoutMs'],超时码)#套上命令截止
    try:#等到命令结算再拆定时器
        会话编号=壳表['get'](所有者,命令截止.信号).等待()#拿到该所有者的壳
        标记=命令标记()#本次起止标记
        已包装=包装命令(命令,标记)#包成一行
        首次=True#第一次循环才提交命令
        回退=''#增量视口回退
        回退已截=False#回退是否被截
        while True:#轮询直到完成、超时、退出或回到提示符
            try:#发一次（首次带命令，之后空提交只为读）
                操作=上下文.terminals.开始发送(所有者,会话编号,{#向PTY发送
                    'text':已包装 if 首次 else '',#第一次发包装命令
                    'submit':首次,#第一次才提交
                    'signal':命令截止.信号,#跟截止信号
                })#开始发送结束
                首次=False#之后不再提交命令
                结果=操作.done.等待()#等这一轮发送结束
            except BaseException as 错误:#发送失败
                壳表['reset'](所有者,'persistent bash send failed')#丢掉这个壳
                raise 错误#原样抛出
            增量=操作.读取输出()#读本轮增量
            增量文本=增量['delta']#增量正文
            if len(增量文本)>0:#有增量则累加
                回退=回退+增量文本#累加
            else:#否则用视口
                回退=结果['viewport']#视口
            回退已截=回退已截 or 增量['truncated'] is True or 结果['truncated'] is True#任一截断则记下
            最新=上下文.terminals.读取(所有者,会话编号,{'offset':0,'count':滚回页行数})#读最新一页滚回
            已超时=取超时(命令截止.信号,超时码)#是否本工具超时
            if 已超时 is not None:#超时
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                部分=渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])#渲染部分输出
                壳表['reset'](所有者,'persistent bash command timed out')#超时后重置壳
                秒数=round(已超时.timeoutMs/1000.0)#超时秒数
                return '\n'.join([#超时说明+部分输出+重置说明
                    'Your command timed out after '+str(秒数)+' seconds or experienced an OOM error. Below is partial output:',#超时说明
                    追加状态标记(部分,超时状态标记),#部分输出附超时标记
                    壳重置说明,#壳已重置
                ])#拼成一段
            if 已中止(命令截止.信号):#上游取消
                壳表['reset'](所有者,'persistent bash command aborted')#丢掉这个壳
                若已中止则抛出(命令截止.信号)#按取消抛出
            if 标记['end'] in 最新['text']:#最新页已见到结束标记
                完整=命令输出(保留滚回(上下文,所有者,会话编号,最新),标记)#尝试抽出完整输出
                if 完整 is not None:#齐了就渲染返回
                    return 渲染已抽(完整,配置值['maxOutputChars'])#渲染返回
            会话状态=结果['sessionStatus']#会话状态
            if 会话状态['kind']=='exited':#壳自己退出了
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                壳表['reset'](所有者,'persistent bash shell exited')#清缓存
                段=渲染壳退出状态(#带上退出原因
                    渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars']),#部分输出
                    会话状态['exitCode'] if 'exitCode' in 会话状态 else None,#退出码
                    会话状态['signal'] if 'signal' in 会话状态 else None,#信号
                )#渲染壳退出状态结束
                if len(段)>0:#有退出段
                    return 段+'\n'+壳重置说明#拼上重置说明
                return 壳重置说明#只有重置说明
            if 提示符已完成(结果):#已经回到提示符
                快照=保留滚回(上下文,所有者,会话编号,最新)#拼滚回
                return 渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])#按部分输出渲染
            暂停()#再等一轮
    finally:#拆除时清掉定时器
        命令截止.释放()#释放已武装定时器

def 登记持久Bash(上下文,配置值):#注册持久bash工具
    """注册面向模型的持久 bash 工具。"""
    壳表=持久壳表(上下文,配置值)#按所有者的壳管家
    队列=weakref.WeakKeyDictionary()#每所有者串行队列

    def 串行(所有者,操作):#同一所有者上串行执行
        """同一所有者上串行执行。"""
        先前=队列[所有者] if 所有者 in 队列 else None#上一条
        运行=操作任务()#本条结果
        尾巴=操作任务()#吞掉结果，只当队列尾巴
        def 接龙():#无论上一条成败都跑本条
            """无论上一条成败都跑本条。"""
            try:#等上一条
                if 先前 is not None:#有上一条
                    try:#等上一条
                        先前.等待()#等上一条
                    except BaseException:#上一条失败也继续
                        pass#吞掉
                try:#跑本条
                    运行.兑现(操作())#兑现本条
                except BaseException as 错误:#本条失败
                    运行.拒绝(错误)#拒绝本条
            finally:#本条结束后
                尾巴.兑现(None)#尾巴落定
        队列[所有者]=尾巴#记下尾巴
        接龙()#开跑
        try:#等本条
            return 运行.等待()#返回本条结果
        finally:#本条结束后
            if 所有者 in 队列 and 队列[所有者] is 尾巴:#还是自己这条尾巴才删
                队列.pop(所有者,None)#删掉

    def 渲染(_参数,值):#原样文本块
        """原样文本块。"""
        return [{'type':'text','text':值}]#原样文本块

    def 执行(参数,执行上下文):#执行一条持久bash
        """执行一条持久 bash。"""
        if len(参数['command'].strip())==0:#拒绝空命令
            raise 持久bash错误('command must be a non-empty string')#拒绝空命令
        所有者=执行上下文['agent'] if 'agent' in 执行上下文 else None#调用方智能体
        if 所有者 is None:#必须有所有者会话
            raise 持久bash错误('bash requires an owning agent session')#必须有所有者会话
        def 本条():#同一所有者串行
            """进队列后仍可能已取消。"""
            若已中止则抛出(执行上下文['signal'] if 'signal' in 执行上下文 else None)#进队列后仍可能已取消
            return 执行命令(上下文,壳表,所有者,参数['command'],配置值,执行上下文['signal'] if 'signal' in 执行上下文 else None)#跑命令
        return 串行(所有者,本条)#同一所有者串行

    def 呈现调用(参数):#调用卡片标题是命令
        """调用卡片标题是命令。"""
        return {'card':'terminal','title':参数['command']}#终端卡片

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

def 是否正安全整数(值):#配置入口的安全整数校验
    """外来配置校验：正整数且不超过 JS 安全整数上限；布尔先排除。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return 值>0 and 值<=安全整数上限#正且安全
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>0 and 值<=安全整数上限#正且安全
    return False#其它类型

def 应用(上下文,配置值):#加载持久bash工具插件
    """注册一个按所有者隔离的持久 bash 工具。"""
    if 配置值 is None:#未传
        配置值={}#空配置
    已解析={#填默认值
        'backendType':配置值['backendType'] if 'backendType' in 配置值 and 配置值['backendType'] is not None else 'shell',#后端
        'timeoutMs':配置值['timeoutMs'] if 'timeoutMs' in 配置值 and 配置值['timeoutMs'] is not None else 300000,#超时
        'maxOutputChars':配置值['maxOutputChars'] if 'maxOutputChars' in 配置值 and 配置值['maxOutputChars'] is not None else 16000,#输出上限
        'description':配置值['description'] if 'description' in 配置值 and 配置值['description'] is not None else 默认描述,#描述
    }#resolved结束
    if len(已解析['backendType'].strip())==0:#后端为空
        raise 持久bash错误('tool-bash-persistent: backendType must be non-empty')#拒绝空后端
    if not 是否正安全整数(已解析['timeoutMs']):#超时非法
        raise 持久bash错误('tool-bash-persistent: timeoutMs must be a positive safe integer')#拒绝非正超时
    if not 是否正安全整数(已解析['maxOutputChars']):#输出上限非法
        raise 持久bash错误('tool-bash-persistent: maxOutputChars must be a positive safe integer')#拒绝非正上限
    if len(已解析['description'].strip())==0:#描述为空
        raise 持久bash错误('tool-bash-persistent: description must be non-empty')#拒绝空描述
    登记持久Bash(上下文,已解析)#注册工具

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
