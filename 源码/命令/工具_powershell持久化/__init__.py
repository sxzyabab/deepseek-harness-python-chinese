"""面向模型的持久 pwsh 工具（对齐 upstream tool-pwsh-persistent）。

与 bash 持久化工具共享 PTY 轮询与重置契约；仅包装命令、提示符与工具名不同。
"""
import re,uuid,threading,weakref#正则、标记、线程与弱表
from ..bash工具持久化 import (
    注入,取字段,解开,是否安全整数,或许截断,下一滚回偏移,保留滚回,
    追加状态标记,渲染已抽,渲染壳退出状态,中止信号,中止控制器,已中止,抛若中止,暂停,
    操作任务,已兑现,全部结算,
)
from ...依赖 import schemastery#配置字段
from ...内核.工具 import 定义工具#工具定义
from ...工具.超时 import 截止,取超时#超时

__all__=['名称','注入','配置','应用','默认']#公开面

壳提示符='__DSH_PERSISTENT_PWSH_PROMPT__ '#pwsh 提示符
超时码='PERSISTENT_PWSH_TIMEOUT'#超时码
截断说明='<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with Select-String in order to find the line numbers of what you are looking for.</NOTE>'#截断说明
壳重置说明='The persistent pwsh shell was reset; the next pwsh call starts from the workspace with a fresh current directory and environment.'#重置说明
默认描述='Run commands in a persistent PowerShell shell. State, including the current directory and exported environment variables, persists across calls for this agent.'#默认描述
pwsh提示符安装="function prompt { [Console]::Write([char]27 + ']133;D;' + [int]$LASTEXITCODE + [char]7); '"+壳提示符+"' }"#初始化
名称='tool-pwsh-persistent'#Cordis 插件名
配置={#配置模式
    'backendType':schemastery.字符串字段(默认值='shell'),
    'timeoutMs':schemastery.数字字段(默认值=300000),
    'maxOutputChars':schemastery.数字字段(默认值=16000),
    'description':schemastery.字符串字段(默认值=默认描述),
}#结束

def 收成pwsh引号(值):#quoteForPwsh
    return (值.replace('`','``').replace('"','`"').replace('$','`$').replace('\r','').replace('\n','`n').replace('\x1b','`e'))#转义

def 命令标记():#标记对
    一次性=str(uuid.uuid4())#随机
    return {'start':'__DSH_PERSISTENT_PWSH_START_'+一次性+'__','end':'__DSH_PERSISTENT_PWSH_END_'+一次性+':'}#返回

def 包装命令(命令,标记):#wrapCommand
    体=收成pwsh引号(命令)#转义体
    return ("Write-Output '"+标记['start']+"'; $LASTEXITCODE = $null; $__s = 1; try { Invoke-Expression \""+体+"\"; $__ok = $? } catch { $__ok = $false }; if ($null -ne $LASTEXITCODE) { $__s = [int]$LASTEXITCODE } else { $__s = if ($__ok) { 0 } else { 1 } }; Write-Output ('"+标记['end']+"' + $__s)")#一行包装

退出码模式=re.compile(r'^(\d+)\r?\n')#结束退出码
末尾换行模式=re.compile(r'\r?\n$')#尾换行

def 剥提示符(文本):#剥提示符
    结果=末尾换行模式.sub('',文本)#去尾换行
    while 结果.endswith(壳提示符):结果=结果[:-len(壳提示符)]#剥提示符
    if 结果.endswith('\n'):return 结果[:-1]#再去换行
    return 结果#返回

def 命令输出(快照,标记):#抽完整输出
    文本=快照['text']#滚回
    结束=文本.rfind(标记['end'])#结束标记
    状态匹配=退出码模式.match(文本[结束+len(标记['end']):]) if 结束>=0 else None#退出码
    if 状态匹配 is None:return None#未完成
    开始标记=文本.rfind(标记['start'],0,结束)#开始
    起点=0 if 开始标记<0 else 开始标记+len(标记['start'])#起点
    正文=剥提示符(re.sub(r'^\r?\n','',文本[起点:结束]))#正文
    return {'text':正文,'incomplete':开始标记<0,'exitCode':int(状态匹配.group(1))}#输出

def 提示符已完成(结果):#提示符完成
    视口=取字段(结果,'viewport')#视口
    return 视口.endswith(壳提示符) or 视口.endswith(壳提示符+'\r\n') or 视口.endswith(壳提示符+'\n')#判断

def 部分输出(快照,标记,回退,回退已截=False):#部分输出
    开始标记=快照['text'].rfind(标记['start'])#开始
    if 开始标记>=0:
        return {'text':剥提示符(re.sub(r'^\r?\n','',快照['text'][开始标记+len(标记['start']):])),'incomplete':False}
    回退开始=回退.rfind(标记['start'])#回退开始
    开始后=回退 if 回退开始<0 else re.sub(r'^\r?\n','',回退[回退开始+len(标记['start']):])#正文
    回退结束=开始后.rfind(标记['end'])#结束
    结束前=开始后 if 回退结束<0 else 开始后[:回退结束]#截断
    return {'text':剥提示符(结束前.replace(壳提示符,'')),'incomplete':回退已截 or 回退开始<0}#返回

def 执行命令(上下文,壳们,所有者,命令,配置值,上游):#执行
    命令截止=截止(上游,配置值['timeoutMs'],超时码)#截止
    try:#执行循环
        会话编号=解开(壳们['get'](所有者,取字段(命令截止,'signal')))#拿壳
        标记=命令标记();已包装=包装命令(命令,标记);首次=True;回退='';回退已截=False#状态
        while True:#轮询
            try:#发送
                操作=上下文.terminals.startSend(所有者,会话编号,{'text':已包装 if 首次 else '','submit':首次,'signal':取字段(命令截止,'signal')})
                首次=False;结果=解开(取字段(操作,'done'))
            except BaseException as 错误:
                壳们['reset'](所有者,'persistent pwsh send failed');raise 错误
            增量=操作.readOutput();增量文本=取字段(增量,'delta')
            回退=回退+增量文本 if len(增量文本)>0 else 取字段(结果,'viewport')
            回退已截=回退已截 or bool(取字段(增量,'truncated')) or bool(取字段(结果,'truncated'))
            最新=上下文.terminals.read(所有者,会话编号,{'offset':0,'count':滚回页行数})
            已超时=取超时(取字段(命令截止,'signal'),超时码)
            if 已超时 is not None:
                快照=保留滚回(上下文,所有者,会话编号,最新)
                部分=渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])
                壳们['reset'](所有者,'persistent pwsh command timed out')
                return '\n'.join(['Your command timed out after '+str(round(取字段(已超时,'timeoutMs')/1000))+' seconds or experienced an OOM error. Below is partial output:',部分,壳重置说明])
            if 已中止(取字段(命令截止,'signal')):
                壳们['reset'](所有者,'persistent pwsh command aborted');抛若中止(取字段(命令截止,'signal'))
            if 标记['end'] in 取字段(最新,'text'):
                完整=命令输出(保留滚回(上下文,所有者,会话编号,最新),标记)
                if 完整 is not None:return 渲染已抽(完整,配置值['maxOutputChars'])
            会话状态=取字段(结果,'sessionStatus')
            if 取字段(会话状态,'kind')=='exited':
                快照=保留滚回(上下文,所有者,会话编号,最新);壳们['reset'](所有者,'persistent pwsh shell exited')
                段=渲染壳退出状态(渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars']),取字段(会话状态,'exitCode'),取字段(会话状态,'signal'))
                return '\n'.join([段,壳重置说明])
            if 提示符已完成(结果):
                快照=保留滚回(上下文,所有者,会话编号,最新)
                return 渲染已抽(部分输出(快照,标记,回退,回退已截),配置值['maxOutputChars'])
            暂停()
    finally:命令截止.释放()

滚回页行数=1000#滚回页行数

def 持久pwsh壳们(上下文,配置值):#按所有者缓存 pwsh 壳
    进行中=weakref.WeakKeyDictionary();存活={};创建中=set();已装所有者拆除=weakref.WeakSet();生命周期=中止控制器()
    def 关闭(所有者,会话编号,原因):
        名单=上下文.terminals.list(所有者)
        if not any(取字段(快照,'sessionId')==会话编号 for 快照 in 名单):return
        解开(上下文.terminals.kill(所有者,会话编号,原因))
    def 副作用体():
        def 拆除():
            生命周期.中止(Exception('tool-pwsh-persistent disposed during shell creation'))
            全部结算(list(创建中))
            for 所有者,会话编号 in list(存活.items()):关闭(所有者,会话编号,'tool-pwsh-persistent disposed')
            存活.clear()
        return 拆除
    上下文.effect(副作用体,'tool-pwsh-persistent shell cleanup')
    def 重置(所有者,原因):
        进行中.pop(所有者,None);会话编号=存活.pop(所有者,None)
        if 会话编号 is not None:关闭(所有者,会话编号,原因)
    def 获取(所有者,信号):
        已有=进行中.get(所有者)
        if 已有 is not None:return 已有
        组合信号=中止信号.任一([信号,生命周期.信号]);创建=操作任务();创建中.add(创建);进行中[所有者]=创建
        def 拉起并初始化():
            try:
                工作目录=取字段(取字段(取字段(所有者,'session'),'header'),'cwd')
                规格={'type':配置值['backendType']}
                if 工作目录 is not None:规格['cwd']=工作目录
                拉起=解开(上下文.terminals.spawn(所有者,规格,组合信号));会话编号=取字段(拉起,'sessionId');存活[所有者]=会话编号
                if 所有者 not in 已装所有者拆除:
                    已装所有者拆除.add(所有者)
                    def 所有者副作用体():
                        def 清缓存():进行中.pop(所有者,None);存活.pop(所有者,None)
                        return 清缓存
                    所有者.ctx.effect(所有者副作用体,'tool-pwsh-persistent owner cache cleanup')
                发送=上下文.terminals.startSend(所有者,会话编号,{'text':pwsh提示符安装,'submit':True,'signal':组合信号})
                结果=解开(取字段(发送,'done'))
                会话状态=取字段(结果,'sessionStatus')
                if 取字段(会话状态,'kind')=='exited' or 取字段(结果,'waitReason')=='timeout':
                    raise Exception('persistent pwsh shell did not accept initialization')
                创建.兑现(会话编号)
            except BaseException as 错误:
                重置(所有者,'persistent pwsh initialization failed');创建.拒绝(错误)
            finally:创建中.discard(创建)
        工作=threading.Thread(target=拉起并初始化);工作.daemon=True;工作.start();return 创建
    return {'get':获取,'reset':重置}

def 登记持久pwsh(上下文,配置值):#注册工具
    壳们=持久pwsh壳们(上下文,配置值)#pwsh 壳管家
    import weakref#队列
    队列=weakref.WeakKeyDictionary()#串行
    def 串行(所有者,操作):
        先前=队列.get(所有者) or 已兑现(None);运行=操作任务();尾巴=操作任务()
        def 接龙():
            try:
                try:解开(先前)
                except Exception:pass
                try:运行.兑现(解开(操作()))
                except BaseException as 错误:运行.拒绝(错误)
            finally:尾巴.兑现(None)
        队列[所有者]=尾巴;接龙()
        try:return 解开(运行)
        finally:
            if 队列.get(所有者) is 尾巴:队列.pop(所有者,None)
    def 执行(参数,执行上下文):
        if len(取字段(参数,'command').strip())==0:raise Exception('command must be a non-empty string')
        所有者=取字段(执行上下文,'agent')
        if 所有者 is None:raise Exception('pwsh requires an owning agent session')
        return 串行(所有者,lambda:(抛若中止(取字段(执行上下文,'signal')),执行命令(上下文,壳们,所有者,取字段(参数,'command'),配置值,取字段(执行上下文,'signal')))[1])
    上下文.tools.登记(定义工具({
        'name':'pwsh','description':配置值['description'],
        'parameters':{'command':{'type':'string','required':True,'description':'The PowerShell command to run. Relative path is preferred in the command.'}},
        'output':{'schema':{'type':'string'},'render':lambda _参数,值:[{'type':'text','text':值}]},
        'execute':执行,'presentCall':lambda 参数:{'card':'terminal','title':取字段(参数,'command')},
    }))

def 应用(上下文,配置值):#加载
    已解析={
        'backendType':取字段(配置值,'backendType') or 'shell',
        'timeoutMs':取字段(配置值,'timeoutMs') or 300000,
        'maxOutputChars':取字段(配置值,'maxOutputChars') or 16000,
        'description':取字段(配置值,'description') or 默认描述,
    }
    if len(已解析['backendType'].strip())==0:raise Exception('tool-pwsh-persistent: backendType must be non-empty')
    if (not 是否安全整数(已解析['timeoutMs'])) or 已解析['timeoutMs']<=0:raise Exception('tool-pwsh-persistent: timeoutMs must be a positive safe integer')
    if (not 是否安全整数(已解析['maxOutputChars'])) or 已解析['maxOutputChars']<=0:raise Exception('tool-pwsh-persistent: maxOutputChars must be a positive safe integer')
    if len(已解析['description'].strip())==0:raise Exception('tool-pwsh-persistent: description must be non-empty')
    登记持久pwsh(上下文,已解析)

apply=应用;default=应用;默认=应用
