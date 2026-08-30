"""bash 能力缝的本地 PowerShell 服务提供方。

对齐上游 `pwsh-local/src/index.ts`。公开面仅中文名；无英文别名。
每条命令经 ctx.subprocess 拉起受管进程，以 `pwsh -NoLogo -NoProfile -NonInteractive -Command` 运行；
执行器负责命令缺省、截止与原因分类、面向模型的终端环境，以及后台读取时面向模型的 stdout/stderr 合并。
命令字符串作为 `-Command` 的一个 argv 元素传入：由 PowerShell 自己解析文本，中间没有 shell。
"""
import os,math,threading#工作目录、有限数与后台结算线程
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
字符串字段=schemastery.字符串字段#配置字段
数字字段=schemastery.数字字段#配置字段
from ..命令 import 外壳设置命名空间,外壳执行器#shell设置命名空间与执行器基类
from ...配置.配置 import 安装设置段#设置段安装
from ...工具.超时 import (
    夹取超时,#夹取超时
    截止,#融合截止
    定时器延迟上限毫秒,#定时器延迟上限
    取超时,#取出超时原因
)#超时库
from .解析 import 解析Pwsh路径,候选Pwsh路径#再导出 pwsh 路径解析

__all__=(#仅中文公开名；无英文别名
    '环境覆盖','编码前导','断言可用Pwsh配置',
    '本地PowerShell执行器','配置模式','默认',
    '解析Pwsh路径','候选Pwsh路径',
)#公开面结束

环境覆盖={'NO_COLOR':'1','PAGER':'cat','GIT_PAGER':'cat'}#面向模型的环境覆盖：关掉颜色与分页器；故意不加 TERM=dumb
编码前导='[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); $OutputEncoding = [System.Text.UTF8Encoding]::new($false); '#每条命令前钉住无 BOM 的 UTF-8 输出（5.1 兜底需要）
默认宽限毫秒=3000#默认 SIGTERM→SIGKILL 宽限（graceMs）
默认溢出字节=64*1024*1024#默认每路溢出文件上限 64MiB
配置模式={#插件配置模式；cwd/pwshPath 无默认值
    'cwd':字符串字段(),#可选默认工作目录
    'timeoutMs':数字字段(默认值=120000),#默认前台超时 120 秒
    'maxTimeoutMs':数字字段(默认值=600000),#每次调用超时覆盖上限 600 秒
    'maxOutputBytes':数字字段(默认值=64000),#每路内存输出上限；超出溢到临时文件
    'maxSpillBytes':数字字段(默认值=默认溢出字节),#每路溢出文件上限
    'graceMs':数字字段(默认值=默认宽限毫秒),#杀进程升级与继承管道宽限
    'pwshPath':字符串字段(),#显式 pwsh 可执行路径；省略则探测
}#插件配置模式结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

    return getattr(对象,键,缺省)#对象属性

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 解开(值):#可等待则等待否则原样
    """可等待则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 最终输出(读取器):#把已结算的收集模式读取器投影成最终收集输出
    """把已结算的收集模式读取器投影成最终的 CollectedOutput。"""
    读出=读取器.readFrom(0)#从开头读完整收集
    结果={'text':取字段(读出,'text'),'truncated':取字段(读出,'lossy')}#文本与是否丢失
    溢出=取字段(读出,'spillPath')#溢出路径
    if 溢出 is not None:#有溢出路径
        结果['spillPath']=溢出#带上溢出路径
    return 结果#最终输出

def 断言正有限(名称,值):#断言值为正有限数
    """断言值为正有限数。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<=0:#不是正有限数
        raise Exception('pwsh-local: '+名称+' must be a positive finite number')#用字段名报配置不可用

def 断言可用Pwsh配置(配置):#断言配置能拿来跑
    """拒绝本执行器没法拿来跑的已解析设置段。模式既不表达正且有限，也不表达 graceMs 必须装进的定时器上限，所以在写入处拒绝存进去的值。"""
    断言正有限('timeoutMs',取字段(配置,'timeoutMs'))#检查默认超时
    断言正有限('maxTimeoutMs',取字段(配置,'maxTimeoutMs'))#检查超时上限
    断言正有限('maxOutputBytes',取字段(配置,'maxOutputBytes'))#检查内存输出上限
    断言正有限('maxSpillBytes',取字段(配置,'maxSpillBytes'))#检查溢出文件上限
    宽限=取字段(配置,'graceMs')#杀进程宽限
    断言正有限('graceMs',宽限)#检查杀进程宽限
    if 宽限>定时器延迟上限毫秒:#宽限超过定时器上限
        raise Exception('pwsh-local: graceMs must be no greater than '+str(定时器延迟上限毫秒))#拒绝过大的宽限

def 取出已收集(句柄):#取出收集模式的两路读取器
    """执行器自己请求的收集模式读取器（按构造即存在）。"""
    已收集输出=取字段(句柄,'collected')#收集输出集合
    标准输出=取字段(已收集输出,'stdout')#标准输出读取器
    标准误=取字段(已收集输出,'stderr')#标准误读取器
    if 标准输出 is None or 标准误 is None:#实现丢掉了请求的收集流
        raise Exception('pwsh-local: subprocess implementation dropped a requested collect stream')#按缝约定这两路必须在
    return {'stdout':标准输出,'stderr':标准误}#两路读取器

class 本地PowerShell执行器(外壳执行器):#本地 PowerShell 执行器
    """架在 ctx.subprocess 上的本地 PowerShell 执行器。

    有界输出、溢出文件和进程树终止是子进程服务的机制；本执行器在每次 spawn 时提供它们的配置预算。
    公开方法仅中文：解析、运行、启动、按参数表运行/启动、参数表、进程已结束。
    """
    注入=['subprocess']#构造前须具备子进程服务
    def __init__(自身,上下文对象,配置):#用上下文和配置构造执行器
        """用上下文和配置构造执行器；入口配置必须能拿来跑，并解析 pwsh 可执行文件。"""
        super().__init__(上下文对象)#交给 shell 执行器基类
        断言可用Pwsh配置(配置)#入口配置必须能拿来跑
        def 读入口():#组合入口配置源
            """组合入口配置源。"""
            return 配置#入口配置
        自身.源=读入口#先把配置源钉成这份入口
        自身.已声明Pwsh路径=取字段(配置,'pwshPath')#记下声明的 pwsh 路径（可缺席）
        自身.已解析Pwsh路径=解析Pwsh路径(自身.已声明Pwsh路径)#按声明解析出可执行文件
        def 设源(当前):#切换权威配置源
            """切换权威配置源。"""
            自身.源=当前#之后都从设置段读
        def 变更时():#声明路径变了就重新解析
            """探测文件系统是从源派生出的唯一事实：其余字段每次命令都经 配置/pwsh路径 读。"""
            声明=取字段(自身.源(),'pwshPath')#读出当前声明的 pwsh 路径
            if 声明==自身.已声明Pwsh路径:#声明没变
                return#不用重探文件系统
            自身.已声明Pwsh路径=声明#记下新的声明
            自身.已解析Pwsh路径=解析Pwsh路径(声明)#按新声明重新解析
        安装设置段(上下文对象,外壳设置命名空间,配置模式,配置,{#与 bash 家族共用外壳设置命名空间
            'validate':断言可用Pwsh配置,#写入时再断言能跑
            'setSource':设源,#切换权威配置源
            'onChange':变更时,#仅声明路径变化才重探
        })#设置段安装结束

    @property#只读属性
    def 配置(自身):#读取当前权威配置
        """当前权威配置：设置段，或组合入口。"""
        return 自身.源()#调用当前配置源

    @property#只读属性
    def pwsh路径(自身):#读取解析后的pwsh路径
        """每条命令都经这个 pwsh 可执行文件运行。"""
        return 自身.已解析Pwsh路径#返回当前解析结果

    def 解析(自身,请求):#把请求解析成完整规格
        """把请求解析成完整规格：workdir 从 config.cwd 填（否则进程 cwd），timeoutMs 从 config.timeoutMs 填，并夹在 config.maxTimeoutMs 内。"""
        超时毫秒=夹取超时(取字段(请求,'timeoutMs'),取字段(自身.配置,'timeoutMs'),取字段(自身.配置,'maxTimeoutMs'),'pwsh-local: request.timeoutMs')#夹取本次超时
        标准输出上限=取字段(请求,'stdoutMaxBytes')#请求里的标准输出上限
        if 标准输出上限 is None:#缺省
            标准输出上限=取字段(自身.配置,'maxOutputBytes')#用配置
        断言正有限('request.stdoutMaxBytes',标准输出上限)#请求的输出上限必须是正有限数
        工作目录=取字段(请求,'workdir')#请求工作目录
        if 工作目录 is None:#请求没给
            工作目录=取字段(自身.配置,'cwd')#配置工作目录
        if 工作目录 is None:#配置也没给
            工作目录=os.getcwd()#进程cwd
        规格={
            'command':取字段(请求,'command'),#要跑的命令文本
            'workdir':工作目录,#工作目录
            'timeoutMs':超时毫秒,#夹取后的超时
            'stdoutMaxBytes':标准输出上限,#标准输出上限
            'sandboxPolicy':取字段(请求,'sandboxPolicy'),#透传沙箱策略
        }#规格骨架
        信号=取字段(请求,'signal')#中止信号
        if 信号:#有中止信号
            规格['signal']=信号#带上
        标准输入=取字段(请求,'stdin')#标准输入
        if 标准输入 is not None:#有标准输入
            规格['stdin']=标准输入#带上
        环境=取字段(请求,'env')#额外环境
        if 环境 is not None:#有额外环境
            规格['env']=环境#带上
        托管环境=取字段(请求,'dshEnv')#dsh环境
        if 托管环境 is not None:#有dsh环境
            规格['dshEnv']=托管环境#带上
        return 规格#完整规格

    def 参数表(自身,规格):#拼出本次pwsh调用argv
        """一条已解析规格对应的 pwsh 调用 argv——隔离子类经 ctx.sandbox.confine 包装的 argv 级缝。"""
        return [自身.pwsh路径,'-NoLogo','-NoProfile','-NonInteractive','-Command',编码前导+取字段(规格,'command')]#pwsh加编码钉住语句再跟命令

    def 拉起规格(自身,规格,标准输出上限,信号,参数表):#把规格和argv映射成子进程spawn规格
        """把一条已解析规格加上它的 argv 映射成完整的子进程 spawn。"""
        def 收集(最大字节):#按字节上限构造收集配置
            """按字节上限构造收集配置。"""
            return {'maxBytes':最大字节,'spill':{'maxBytes':取字段(自身.配置,'maxSpillBytes')}}#内存上限加溢出文件上限
        标准输入=取字段(规格,'stdin')#规格里的标准输入
        if 标准输入 is not None:#有stdin就喂数据
            输入处置={'data':标准输入}#写入后关闭
        else:#没有stdin
            输入处置='ignore'#忽略
        调用环境=dict(环境覆盖)#先放模型友好覆盖
        额外环境=取字段(规格,'env')#请求普通环境
        if 额外环境 is not None:#有普通环境
            调用环境.update(额外环境)#叠普通环境
        托管环境=取字段(规格,'dshEnv')#请求托管环境
        if 托管环境 is not None:#有托管环境
            调用环境.update(托管环境)#叠托管环境
        return {
            'argv':list(参数表),#复制argv，避免共享只读数组
            'cwd':取字段(规格,'workdir'),#在规格的工作目录里跑
            'stdio':{
                'stdin':输入处置,#标准输入处置
                'stdout':收集(标准输出上限),#按本次上限收集标准输出
                'stderr':收集(取字段(自身.配置,'maxOutputBytes')),#按配置上限收集标准误
            },#三路标准流
            'graceMs':取字段(自身.配置,'graceMs'),#杀进程宽限
            'signal':信号,#透传中止信号
            'env':调用环境,#模型友好覆盖再叠请求环境
        }#子进程spawn规格

    def 运行(自身,规格):#前台跑一条已解析规格
        """前台跑一条已解析规格。"""
        return 自身.按参数表运行(规格,自身.参数表(规格))#用本执行器拼出的argv前台跑

    def 按参数表运行(自身,规格,参数表):#按给定argv前台运行
        """用精确 argv 做前台运行（隔离子类会重新包装它）。"""
        截止对象=截止(取字段(规格,'signal'),取字段(规格,'timeoutMs'),'BASH_TIMEOUT')#为本次前台跑装上截止
        try:#等到进程结束再拆定时器
            句柄=自身.ctx.subprocess.spawn(自身.拉起规格(规格,取字段(规格,'stdoutMaxBytes'),取字段(截止对象,'signal'),参数表))#按规格spawn子进程
            结算=解开(取字段(句柄,'done'))#等到进程结束
            收集=取出已收集(句柄)#取出两路收集读取器
            已超时=取超时(取字段(截止对象,'signal'),'BASH_TIMEOUT') is not None#是否因本执行器超时结束
            截止信号=取字段(截止对象,'signal')#融合后的中止信号
            已中止=取字段(截止信号,'aborted') is True and not 已超时#中止但不是本执行器超时
            return {
                'exitCode':取字段(结算,'exitCode'),#退出码
                'signal':取字段(结算,'signal'),#终止信号
                'timedOut':已超时,#是否超时
                'aborted':已中止,#是否中止
                'timeoutMs':取字段(规格,'timeoutMs'),#本次超时预算
                'stdout':最终输出(收集['stdout']),#收成最终标准输出
                'stderr':最终输出(收集['stderr']),#收成最终标准误
            }#前台运行结果
        finally:#拆除时清掉定时器
            截止对象.释放()#释放已武装定时器

    def 启动(自身,规格):#后台拉起一条已解析规格
        """后台拉起一条已解析规格。"""
        return 自身.按参数表启动(规格,自身.参数表(规格))#用本执行器拼出的argv后台拉起

    def 按参数表启动(自身,规格,参数表):#按给定argv后台启动
        """用精确 argv 做后台启动（隔离子类会重新包装它）。后台运行忽略 timeoutMs。"""
        运行中=自身.ctx.subprocess.spawn(自身.拉起规格(规格,取字段(自身.配置,'maxOutputBytes'),取字段(规格,'signal'),参数表))#按配置输出上限spawn后台进程
        收集=取出已收集(运行中)#取出两路收集读取器
        失败说明=None#待交付的spawn失败说明
        标准输出偏移=0#标准输出已读偏移
        标准误偏移=0#标准误已读偏移
        def 消费启动失败():#读走并清空spawn失败说明
            """读走并清空 spawn 失败说明。"""
            nonlocal 失败说明#改外层说明
            说明='' if 失败说明 is None else 失败说明#没有说明则给空串
            失败说明=None#只交付一次
            return 说明#返回本次说明
        def 读输出():#读出上次以来的新输出
            """读出上次以来的新输出。"""
            nonlocal 标准输出偏移,标准误偏移#推进偏移
            出=收集['stdout'].readFrom(标准输出偏移)#从上次偏移读标准输出
            错=收集['stderr'].readFrom(标准误偏移)#从上次偏移读标准误
            标准输出偏移=取字段(出,'nextOffset')#推进标准输出偏移
            标准误偏移=取字段(错,'nextOffset')#推进标准误偏移
            错文本=取字段(错,'text')#标准误文本
            if len(错文本)==0:#没有真正的标准误
                错文本=消费启动失败()#用spawn说明
            出文本=取字段(出,'text')#标准输出增量
            if len(出文本)>0 and not 出文本.endswith('\n'):#标准输出非空且没换行
                分隔='\n'#插分隔
            else:#已经换行或为空
                分隔=''#不插分隔
            if len(错文本)>0:#有标准误或失败说明
                增量=出文本+分隔+'[stderr]\n'+错文本#拼上带[stderr]头的标准误
            else:#没有标准误
                增量=出文本#只留标准输出
            读取={'delta':增量,'lossy':bool(取字段(出,'lossy')) or bool(取字段(错,'lossy'))}#合并后的增量
            出溢出=取字段(出,'spillPath')#标准输出溢出路径
            if 出溢出 is not None:#有标准输出溢出路径
                读取['stdoutSpillPath']=出溢出#带上
            错溢出=取字段(错,'spillPath')#标准误溢出路径
            if 错溢出 is not None:#有标准误溢出路径
                读取['stderrSpillPath']=错溢出#带上
            return 读取#本次读取
        def 杀死():#请求杀掉后台进程
            """请求杀掉后台进程。"""
            if 进程['status']!='running':#已经不在跑
                return False#杀不动
            进程['status']='killed'#先标成已杀
            运行中.terminate()#请子进程服务终止进程树
            return True#发出了终止
        完成=操作任务()#后台句柄的done
        进程={
            'status':'running',#刚拉起，算在跑
            'exitCode':None,#尚未退出
            'signal':None,#尚未被信号打死
            'done':完成,#结算承诺
            'readOutput':读输出,#增量读取
            'kill':杀死,#终止
        }#后台进程句柄
        def 盯退出():#正常结算或spawn拒绝
            """把子进程 done 投影到后台句柄。"""
            nonlocal 失败说明#spawn失败时写入说明
            try:#正常结算
                结算=解开(取字段(运行中,'done'))#等到关闭
                if 进程['status']=='running':#还没被kill标过
                    规格信号=取字段(规格,'signal')#规格上的中止信号
                    上游中止=取字段(规格信号,'aborted') is True if 规格信号 is not None else False#上游是否已中止
                    if 上游中止 or 取字段(结算,'signal') is not None:#中止或有信号
                        进程['status']='killed'#killed
                    else:#干净退出
                        进程['status']='completed'#completed
                进程['exitCode']=取字段(结算,'exitCode')#记下退出码
                进程['signal']=取字段(结算,'signal')#记下终止信号
                自身.进程已结束(进程,取字段(收集['stderr'].readFrom(0),'text'),False)#通知子类进程已结算，非spawn失败
                完成.兑现()#句柄done决议
            except BaseException as 错误:#spawn拒绝
                进程['status']='killed'#没有进程，算被杀掉
                失败说明='spawn failed: '+str(错误)#把失败说明留给读取路径
                自身.进程已结束(进程,失败说明,True,错误)#通知子类这是spawn失败
                完成.兑现()#句柄done仍决议，不拒绝
        工作=threading.Thread(target=盯退出)#后台结算线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 进程#返回后台进程

    def 进程已结束(自身,进程,标准误,启动失败,启动错误=None):#给子类的结算钩子
        """给子类往进程上贴执行事实的结算钩子。基类实现故意留空；pwsh 隔离消费方是 pwsh_sandbox。"""
        return#基类故意留空

默认=本地PowerShell执行器#默认导出该执行器类（中文名；无英文 default 别名）
