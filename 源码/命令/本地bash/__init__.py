"""叠在子进程能力上的本地 bash 服务提供方。

公开命令经子进程在受管进程组里以 bash -c 跑；子类可用显式 argv 复用同一套机制。
本执行器拥有命令默认值、截止与原因分类、对模型友好的终端环境，以及后台读取时面向模型的 stdout/stderr 合并。
"""
import os,math,threading#工作目录、有限数与后台结算线程
from concurrent.futures import Future as 原生结果#单次操作结果
from ...依赖.schemastery import 字符串字段,数字字段#配置字段
from ..命令 import 外壳设置命名空间,外壳执行器#shell 设置命名空间与执行器基类
from ...配置.配置 import 安装设置段#设置段安装
from ...工具.超时 import (
    夹取超时,#夹取超时
    截止,#融合截止
    定时器延迟上限毫秒,#定时器延迟上限
    取超时,#取出超时原因
    若已中止则抛出,#写前已中止则抛
)#超时库

__all__=[#仅中文公开名
    '环境覆盖','断言可用Bash配置','本地Bash执行器','配置模式',
]#公开面结束

环境覆盖={'NO_COLOR':'1','TERM':'dumb','PAGER':'cat','GIT_PAGER':'cat'}#面向模型的环境覆盖：关掉颜色、哑终端和分页器
默认宽限毫秒=3000#默认 SIGTERM 到 SIGKILL 宽限
默认溢出字节=64*1024*1024#默认每路溢出 64MiB
配置模式={
    'cwd':字符串字段(),#工作目录字符串
    'timeoutMs':数字字段(默认值=120000),#默认超时 120 秒
    'maxTimeoutMs':数字字段(默认值=600000),#超时上限 600 秒
    'maxOutputBytes':数字字段(默认值=64000),#默认内存输出 64000 字节
    'maxSpillBytes':数字字段(默认值=默认溢出字节),#默认溢出文件上限
    'graceMs':数字字段(默认值=默认宽限毫秒),#默认杀进程宽限
}#插件配置模式

class 本地bash错误(Exception):#本包异常基类
    """本地 bash 执行器入参、配置或组合失败。"""
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
                自身.未来.set_exception(本地bash错误(错误))#包装拒绝

    def 等待(自身,超时=None):#阻塞等待
        """阻塞到结算。"""
        return 自身.未来.result(timeout=超时)#取结果或抛错

def 已中止(信号):#读中止事实
    """信号按 Event 定死。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#事件已置位

def 最终输出(读取器):#把已结算的收集模式读取器投影成最终收集输出
    """把已结算的收集模式读取器投影成最终的已收集输出。"""
    读出=读取器.自偏移读取(0)#从开头读完整收集
    结果={'text':读出['text'],'truncated':读出['lossy']}#文本与是否丢失
    if 'spillPath' in 读出:#有溢出路径键
        结果['spillPath']=读出['spillPath']#带上溢出路径
    return 结果#最终输出

def 断言正有限(名称,值):#断言值为正有限数
    """断言值为正有限数；布尔先排除。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<=0:#不是正有限数
        raise 本地bash错误('bash-local: '+名称+' must be a positive finite number')#用字段名报配置不可用

def 断言可用Bash配置(配置):#断言配置能拿来跑
    """拒绝本执行器没法拿来跑的已解析设置段。模式既不表达正且有限，也不表达 graceMs 必须装进的定时器上限，所以在写入处拒绝存进去的值。"""
    断言正有限('timeoutMs',配置['timeoutMs'])#检查默认超时
    断言正有限('maxTimeoutMs',配置['maxTimeoutMs'])#检查超时上限
    断言正有限('maxOutputBytes',配置['maxOutputBytes'])#检查内存输出上限
    断言正有限('maxSpillBytes',配置['maxSpillBytes'])#检查溢出文件上限
    宽限=配置['graceMs']#杀进程宽限
    断言正有限('graceMs',宽限)#检查杀进程宽限
    if 宽限>定时器延迟上限毫秒:#宽限超过定时器上限
        raise 本地bash错误('bash-local: graceMs must be no greater than '+str(定时器延迟上限毫秒))#拒绝过大的宽限

def 取出已收集(句柄):#取出收集模式的两路读取器
    """执行器自己请求的收集模式读取器（按构造即存在）。"""
    已收集输出=句柄.collected#收集输出集合
    标准输出=已收集输出['stdout'] if 'stdout' in 已收集输出 else None#标准输出读取器
    标准误=已收集输出['stderr'] if 'stderr' in 已收集输出 else None#标准误读取器
    if 标准输出 is None or 标准误 is None:#实现丢掉了请求的收集流
        raise 本地bash错误('bash-local: subprocess implementation dropped a requested collect stream')#按约定这两路必须在
    return {'stdout':标准输出,'stderr':标准误}#两路读取器

class 后台进程句柄:#外壳执行器.启动 返回的后台进程
    """后台进程句柄：方法仅中文读取输出与杀死。"""
    def __init__(自身,运行中,收集,规格,宿主):#钉住子进程与收集器
        """记下存活子进程、两路收集器、规格与宿主执行器。"""
        自身.status='running'#刚拉起，算在跑
        自身.exitCode=None#尚未退出
        自身.signal=None#尚未被信号打死
        自身.done=操作任务()#结算任务
        自身.sandbox=None#沙箱事实由子类盖章
        自身.运行中=运行中#存活子进程句柄
        自身.收集=收集#两路收集读取器
        自身.规格=规格#已解析规格
        自身.执行器=宿主#执行器，供结算钩子
        自身.失败说明=None#待交付的启动失败说明
        自身.标准输出偏移=0#标准输出已读偏移
        自身.标准误偏移=0#标准误已读偏移

    def 消费启动失败(自身):#读走并清空启动失败说明
        """读走并清空启动失败说明。"""
        说明='' if 自身.失败说明 is None else 自身.失败说明#没有说明则给空串
        自身.失败说明=None#只交付一次
        return 说明#返回本次说明

    def 读取输出(自身):#读出上次以来的新输出
        """读出上次以来的新输出（消费式）。"""
        标准输出读取=自身.收集['stdout'].自偏移读取(自身.标准输出偏移)#从上次偏移读标准输出
        标准误读取=自身.收集['stderr'].自偏移读取(自身.标准误偏移)#从上次偏移读标准误
        自身.标准输出偏移=标准输出读取['nextOffset']#推进标准输出偏移
        自身.标准误偏移=标准误读取['nextOffset']#推进标准误偏移
        启动失败=自身.消费启动失败()#取出一次提供方失败说明
        if len(标准误读取['text'])>0 and not 标准误读取['text'].endswith('\n'):#标准误非空且缺换行
            失败分隔='\n'#补分隔
        else:#已经换行或为空
            失败分隔=''#不插分隔
        标准误文本=标准误读取['text']#标准误正文
        if len(启动失败)>0:#有提供方失败说明
            标准误文本=标准误文本+失败分隔+启动失败#追加失败说明
        标准输出文本=标准输出读取['text']#标准输出增量
        if len(标准输出文本)>0 and not 标准输出文本.endswith('\n'):#标准输出非空且没换行
            分隔='\n'#插分隔
        else:#已经换行或为空
            分隔=''#不插分隔
        if len(标准误文本)>0:#有标准误或失败说明
            增量=标准输出文本+分隔+'[stderr]\n'+标准误文本#拼上带[stderr]头的标准误
        else:#没有标准误
            增量=标准输出文本#只留标准输出
        读取={'delta':增量,'lossy':标准输出读取['lossy'] is True or 标准误读取['lossy'] is True}#合并后的增量
        if 'spillPath' in 标准输出读取:#有标准输出溢出路径
            读取['stdoutSpillPath']=标准输出读取['spillPath']#带上
        if 'spillPath' in 标准误读取:#有标准误溢出路径
            读取['stderrSpillPath']=标准误读取['spillPath']#带上
        return 读取#本次读取

    def 杀死(自身):#请求杀掉后台进程
        """请求杀掉后台进程。已经结束时返回 False。"""
        if 自身.status!='running':#已经不在跑
            return False#杀不动
        自身.status='killed'#先标成已杀
        自身.运行中.终止()#请子进程服务终止进程树
        return True#发出了终止

    def 盯退出(自身):#正常结算或启动拒绝
        """把子进程 done 投影到后台句柄。"""
        try:#正常结算
            结算=自身.运行中.done.等待()#等到关闭
            if 自身.status=='running':#还没被杀死标过
                规格信号=自身.规格['signal'] if 'signal' in 自身.规格 else None#规格上的中止信号
                上游中止=已中止(规格信号)#上游是否已中止
                if 上游中止 or 结算['signal'] is not None:#中止或有信号
                    自身.status='killed'#killed
                else:#干净退出
                    自身.status='completed'#completed
            自身.exitCode=结算['exitCode']#记下退出码
            自身.signal=结算['signal']#记下终止信号
            错快照=自身.收集['stderr'].自偏移读取(0)#整路标准误
            自身.执行器.进程已结束(自身,错快照['text'],False)#通知子类进程已结算，非启动失败
            自身.done.兑现()#句柄 done 决议
        except BaseException as 错误:#启动拒绝
            自身.status='killed'#没有进程，算被杀掉
            细节='unprintable provider failure'#不可打印失败的回退文案
            try:#尝试把拒绝值转成字符串
                细节=str(错误)#可读细节
            except BaseException:#拒绝值本身不可打印
                pass#提供方拥有的拒绝值不能让句柄 done 拒绝
            自身.失败说明='subprocess failed before reporting an outcome: '+细节#失败说明
            自身.执行器.进程已结束(自身,自身.失败说明,True,错误)#通知子类这是启动失败
            自身.done.兑现()#句柄 done 仍决议，不拒绝

class 本地Bash执行器(外壳执行器):#本地 bash 执行器
    """架在子进程能力上的本地 bash 执行器。

    有界输出、溢出文件和进程组 SIGTERM→SIGKILL 升级是子进程服务的机制；
    本执行器在每次启动时提供它们的配置预算。公开方法仅中文：解析、运行、启动、按参数表运行/启动。
    """
    依赖=['subprocess']
    inject=依赖
    Config=配置模式
    def __init__(自身,上下文,配置):#用上下文和配置构造执行器
        """用上下文和配置构造执行器；入口配置必须能拿来跑。"""
        super().__init__(上下文)#交给 shell 执行器基类
        断言可用Bash配置(配置)#入口配置必须能拿来跑
        def 读入口():#组合入口配置源
            """组合入口配置源。"""
            return 配置#入口配置
        自身.源=读入口#先把配置源钉成这份入口
        def 设源(当前):#切换权威配置源
            """切换权威配置源。"""
            自身.源=当前#之后都从设置段读
        def 变更时():#每个字段都在每条命令经 getter 读取
            """文档变化时没有从源派生、需要重建的东西。"""
            return#空变更钩子
        安装设置段(上下文,外壳设置命名空间,配置模式,配置,{
            'validate':断言可用Bash配置,#写入时再断言能跑
            'setSource':设源,#切换权威配置源
            'onChange':变更时,#空变更钩子
        })#设置段安装结束

    @property
    def 配置(自身):#读取当前权威配置
        """当前权威配置：设置段，或组合入口。"""
        return 自身.源()#调用当前配置源

    def 解析(自身,请求):#把请求解析成完整规格
        """把请求解析成完整规格：workdir 从 config.cwd 填（否则进程 cwd），timeoutMs 从 config.timeoutMs 填，并夹在 config.maxTimeoutMs 内。"""
        当前=自身.配置#权威配置
        超时毫秒=夹取超时(请求['timeoutMs'] if 'timeoutMs' in 请求 else None,当前['timeoutMs'],当前['maxTimeoutMs'],'bash-local: request.timeoutMs')#夹取本次超时
        标准输出上限=请求['stdoutMaxBytes'] if 'stdoutMaxBytes' in 请求 else None#请求里的标准输出上限
        if 标准输出上限 is None:#缺省
            标准输出上限=当前['maxOutputBytes']#用配置
        断言正有限('request.stdoutMaxBytes',标准输出上限)#请求的输出上限必须是正有限数
        工作目录=请求['workdir'] if 'workdir' in 请求 else None#请求工作目录
        if 工作目录 is None:#请求没给
            工作目录=当前['cwd'] if 'cwd' in 当前 else None#配置工作目录
        if 工作目录 is None:#配置也没给
            工作目录=os.getcwd()#进程cwd
        规格={
            'command':请求['command'],#要跑的命令文本
            'workdir':工作目录,#工作目录
            'timeoutMs':超时毫秒,#夹取后的超时
            'stdoutMaxBytes':标准输出上限,#标准输出上限
            'sandboxPolicy':请求['sandboxPolicy'] if 'sandboxPolicy' in 请求 else None,#透传沙箱策略
        }#规格骨架
        if 'signal' in 请求 and 请求['signal'] is not None:#有中止信号
            规格['signal']=请求['signal']#带上
        if 'stdin' in 请求 and 请求['stdin'] is not None:#有标准输入
            规格['stdin']=请求['stdin']#带上
        if 'env' in 请求 and 请求['env'] is not None:#有额外环境
            规格['env']=请求['env']#带上
        if 'dshEnv' in 请求 and 请求['dshEnv'] is not None:#有dsh环境
            规格['dshEnv']=请求['dshEnv']#带上
        return 规格#完整规格

    def 拉起规格(自身,规格,标准输出上限,信号,参数表):#把规格和argv映射成子进程启动规格
        """把一条已解析 bash 规格加上显式 argv 映射成完整的子进程启动规格。"""
        当前=自身.配置#权威配置
        def 收集(最大字节):#按字节上限构造收集配置
            """按字节上限构造收集配置。"""
            return {'maxBytes':最大字节,'spill':{'maxBytes':当前['maxSpillBytes']}}#内存上限加溢出文件上限
        if 'stdin' in 规格 and 规格['stdin'] is not None:#有stdin就喂数据
            输入处置={'data':规格['stdin']}#写入后关闭
        else:#没有stdin
            输入处置='ignore'#忽略
        调用环境=dict(环境覆盖)#先放模型友好覆盖
        if 'env' in 规格 and 规格['env'] is not None:#有普通环境
            调用环境.update(规格['env'])#叠普通环境
        if 'dshEnv' in 规格 and 规格['dshEnv'] is not None:#有托管环境
            调用环境.update(规格['dshEnv'])#叠托管环境
        return {
            'argv':list(参数表),#复制argv，避免共享只读数组
            'cwd':规格['workdir'],#在规格的工作目录里跑
            'stdio':{
                'stdin':输入处置,#标准输入处置
                'stdout':收集(标准输出上限),#按本次上限收集标准输出
                'stderr':收集(当前['maxOutputBytes']),#按配置上限收集标准误
            },#三路标准流
            'graceMs':当前['graceMs'],#杀进程宽限
            'signal':信号,#透传中止信号
            'env':调用环境,#模型友好覆盖再叠请求环境
        }#子进程启动规格

    def 运行(自身,规格):#前台跑一条已解析规格
        """前台跑一条已解析规格。"""
        return 自身.按参数表运行(规格,['bash','-c',规格['command']])['result']#用bash -c前台跑，只回结果

    def 按参数表运行(自身,规格,参数表或准备):#按给定argv或准备函数前台运行
        """用本执行器的前台生命周期、环境、输出、超时与取消语义跑一条显式 argv。准备函数被同一截止取消。"""
        截止对象=截止(规格['signal'] if 'signal' in 规格 else None,规格['timeoutMs'],'BASH_TIMEOUT')#为本次前台跑装上截止
        try:#等到进程结束再拆定时器
            if callable(参数表或准备):#准备函数与执行共用截止
                try:#准备期间也可被超时取消
                    若已中止则抛出(截止对象.信号)#准备前已中止则抛
                    参数表=参数表或准备(截止对象.信号)#准备 argv
                    若已中止则抛出(截止对象.信号)#准备后再查
                except BaseException as 错误:#准备失败或中止
                    if 取超时(截止对象.信号,'BASH_TIMEOUT') is None:#不是本执行器超时
                        raise 错误#原样抛出
                    return {'spawnRequested':False,'result':{
                        'exitCode':None,'signal':None,'timedOut':True,'aborted':False,'timeoutMs':规格['timeoutMs'],
                        'stdout':{'text':'','truncated':False},'stderr':{'text':'','truncated':False},
                    }}#未派生，空结果
            else:#已经是 argv
                参数表=参数表或准备#直接用
            句柄=自身.ctx.subprocess.启动(自身.拉起规格(规格,规格['stdoutMaxBytes'],截止对象.信号,参数表))#按规格启动子进程
            结算=句柄.done.等待()#等到进程结束
            收集=取出已收集(句柄)#取出两路收集读取器
            已超时=取超时(截止对象.信号,'BASH_TIMEOUT') is not None#是否因本执行器超时结束
            被中止=已中止(截止对象.信号) is True and not 已超时#中止但不是本执行器超时
            return {'spawnRequested':True,'result':{
                'exitCode':结算['exitCode'],#退出码
                'signal':结算['signal'],#终止信号
                'timedOut':已超时,#是否超时
                'aborted':被中止,#是否中止
                'timeoutMs':规格['timeoutMs'],#本次超时预算
                'stdout':最终输出(收集['stdout']),#收成最终标准输出
                'stderr':最终输出(收集['stderr']),#收成最终标准误
            }}#已派生的前台运行结果
        finally:#拆除时清掉定时器
            截止对象.释放()#释放已武装定时器

    def 启动(自身,规格):#后台拉起一条已解析规格
        """后台拉起一条已解析规格。"""
        return 自身.按参数表启动(规格,['bash','-c',规格['command']])#用bash -c后台拉起

    def 按参数表启动(自身,规格,参数表):#按给定argv后台启动
        """用本执行器的后台生命周期、环境、输出、取消与进程树所有权语义启动一条显式 argv。后台运行忽略 timeoutMs。"""
        若已中止则抛出(规格['signal'] if 'signal' in 规格 else None)#后台启动前已中止则抛
        当前=自身.配置#权威配置
        运行中=自身.ctx.subprocess.启动(自身.拉起规格(规格,当前['maxOutputBytes'],规格['signal'] if 'signal' in 规格 else None,参数表))#按配置输出上限启动后台进程
        收集=取出已收集(运行中)#取出两路收集读取器
        进程=后台进程句柄(运行中,收集,规格,自身)#后台进程句柄
        工作=threading.Thread(target=进程.盯退出)#后台结算线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 进程#返回后台进程

    def 进程已结束(自身,进程,标准误,启动失败,启动错误=None):#给子类的结算钩子
        """给子类往进程上贴执行事实的结算钩子。基类实现故意留空。"""
        return#基类故意留空

default=本地Bash执行器#框架槽
