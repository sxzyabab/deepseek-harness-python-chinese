"""bash 执行器的执行类型。

后台作业语义属于通用任务层；本能力只暴露进程句柄。托管环境与捕获输出词表由子进程能力拥有，
并在此再导出同名常量，使 bash 消费方保持一个导入根。字段键字面量保持英文载荷。
"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=[#仅中文公开名
    '托管环境前缀','托管环境键','托管环境',
    '已收集输出字段','已收集输出',
    '进程状态','沙箱事实字段','沙箱事实',
    '执行请求字段','执行请求','执行规格字段','执行规格',
    '运行结果字段','运行结果',
    '增量读取字段','增量读取','后台进程字段','后台进程',
    '有效期策略','已观察流字段',
]#公开面结束

托管环境前缀='DSH_'#预留给 Harness 管理的子环境事实的命名空间前缀

def 托管环境键(键):#品牌托管键
    """把字符串标成托管环境键（DSH_*），不做校验。"""
    return 键#编译期品牌在 Python 中无运行时成本

托管环境=dict#托管环境表：托管键 → 字符串值

已收集输出字段=('text','truncated','spillPath')#捕获输出字段键
class 已收集输出(TypedDict):#一次捕获输出
    text:str#已捕获文本
    truncated:bool#是否因预算截断
    spillPath:NotRequired[str]#完整流溢出文件路径（若有）

进程状态=Literal['running','completed','killed']#后台进程生命周期：运行中、已完成、已杀死

沙箱事实字段=('mode','denied','enforcement','runnerFailed')#一次运行的沙箱事实键
class 沙箱事实(TypedDict):#沙箱执行事实（仅当沙箱执行器处理了它才存在）
    mode:str#命令实际运行所处的模式
    denied:bool#沙箱是否拒绝了一次文件操作
    enforcement:NotRequired[str]#所选运行器对请求模式的强制完整程度
    runnerFailed:NotRequired[bool]#沙箱运行器是否在命令能运行之前就失败

有效期策略=('kill','none')#到期政策：kill 在超时杀死，none 不武装截止

已观察流字段=('stdout','stderr')#非消费偏移读取器

执行请求字段=('command','workdir','timeoutMs','onExpiry','stdoutMaxBytes','signal','stdin','env','dshEnv','sandboxPolicy')#调用方请求键
class 执行请求(TypedDict):#调用方执行请求；省略字段由执行器解析填入
    command:str#命令
    workdir:NotRequired[str]#工作目录覆盖（默认：实现配置）
    timeoutMs:NotRequired[int]#超时覆盖，毫秒（实现会封顶）
    onExpiry:NotRequired[str]#到期政策，默认 kill
    stdoutMaxBytes:NotRequired[int]#前台 stdout 捕获预算，字节；面向模型的工具不暴露
    signal:NotRequired[object]#中止信号——触发时实现杀死命令
    stdin:NotRequired[str]#写入命令 stdin 的字节，然后关闭；面向模型工具不暴露
    env:NotRequired[dict]#普通环境条目，在凭证擦除之后、托管环境之前合并
    dshEnv:NotRequired[dict]#本次执行的 Harness 拥有 DSH_* 快照
    sandboxPolicy:NotRequired[object]#完全解析的按次沙箱政策

执行规格字段=('command','workdir','timeoutMs','onExpiry','stdoutMaxBytes','signal','stdin','env','dshEnv','sandboxPolicy')#已解析规格键
class 执行规格(TypedDict):#已解析执行规格
    command:str#命令
    workdir:str#工作目录
    timeoutMs:int#超时毫秒
    onExpiry:str#到期政策
    stdoutMaxBytes:int#已解析前台 stdout 捕获预算
    signal:NotRequired[object]#中止信号
    stdin:NotRequired[str]#关闭前写入 stdin 的字节
    env:NotRequired[dict]#普通环境条目
    dshEnv:NotRequired[dict]#托管 DSH_* 快照，在 env 之后合并
    sandboxPolicy:object#已解析沙箱政策；不隔离的执行器可忽略（值可为 None）

运行结果字段=('exitCode','signal','timedOut','aborted','timeoutMs','stdout','stderr','sandbox')#前台运行结果键
class 运行结果(TypedDict):#一次已完成（或被杀死）的前台运行结果
    exitCode:int|None#退出码；因信号死亡时为 None
    signal:str|None#终止信号名；正常退出时为 None
    timedOut:bool#执行器自己的超时是切断第一原因
    aborted:bool#调用方 AbortSignal 是杀死第一原因（与 timedOut 互斥）
    timeoutMs:int#本次运行生效的超时
    stdout:已收集输出#标准输出
    stderr:已收集输出#标准错误
    sandbox:NotRequired[沙箱事实]#沙箱执行事实；非沙箱执行器缺席

增量读取字段=('delta','lossy','stdoutSpillPath','stderrSpillPath')#增量读取键
class 增量读取(TypedDict):#一次增量 readOutput 读取
    delta:str#自上次读取以来产出的输出（stderr 在标记段里）
    lossy:bool#截断丢掉了增量无法包含的未读字节时为真
    stdoutSpillPath:NotRequired[str]#完整 stdout 溢出文件
    stderrSpillPath:NotRequired[str]#完整 stderr 溢出文件

后台进程字段=('status','exitCode','signal','done','sandbox','observed')#后台进程句柄数据键（载荷键字面量）
class 后台进程:#外壳执行器.执行 返回的执行句柄协议
    """唯一访问路径；缓冲输出在退出后仍可读。

    数据字段为线协议载荷键（status/exitCode/signal/done/sandbox/observed）；方法仅中文：读取输出、杀死、结果。
    """
    status=None#生命周期（进程状态）
    exitCode=None#结束后的退出码（None = 被信号杀死 / 仍在运行）
    signal=None#被信号杀死时的终止信号名
    done=None#底层进程关闭时决议的承诺（从不拒绝）
    sandbox=None#沙箱事实，隔离进程结算时盖章
    observed=None#非消费偏移读取器

    def 读取输出(自身):#增量读取
        """读取自上次以来产出的输出（消费式——连续读取从不重投）。"""
        raise NotImplementedError('后台进程.读取输出')#由提供方实现

    def 杀死(自身):#杀死进程组
        """杀死进程组。已经结束时返回 False（空操作）；幂等。"""
        raise NotImplementedError('后台进程.杀死')#由提供方实现

    def 结果(自身):
        """前台投影：进程关闭时结算；仅基础设施失败拒绝。"""
        raise NotImplementedError('后台进程.结果')#由提供方实现
