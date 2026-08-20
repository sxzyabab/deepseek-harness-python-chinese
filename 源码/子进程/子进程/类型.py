"""子进程服务定义的词汇。

对齐上游 `subprocess/src/types.ts`。公开面仅中文名；无英文别名。
带每路 stdio 模式的完全指定 spawn 请求、带溢出恢复的有界收集输出、原始管道流，以及树范围终止。
命令默认值、shell 语义、协议分帧和展示属于 bash 执行器缝这类消费方。
字段键字面量对齐上游载荷，保持跨缝可读。
"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=(#仅中文公开名；无英文别名
    '托管环境前缀','托管环境键','托管环境',
    '已收集输出字段','已收集输出',
    '收集模式字段','溢出配置字段','收集模式','溢出配置',
    '三路输入输出字段','三路输入输出',
    '启动规格字段','启动规格',
    '退出事实字段','退出事实',
    '一次读取字段','一次读取',
    '输出读取器字段','输出读取器',
    '收集输出集合字段','收集输出集合',
    '句柄字段','句柄',
    '终端信号','终端启动规格字段','终端启动规格',
    '前台组字段','前台组',
    '终端句柄字段','终端句柄',
    '标准输入模式','标准输出模式',
)#公开面结束

托管环境前缀='DSH_'#预留给 DeepSeek Harness 管理的子环境事实的命名空间前缀

def 托管环境键(键):#品牌托管键
    """把字符串标成托管环境键（DSH_*），不做校验。"""
    return 键#编译期品牌在 Python 中无运行时成本

托管环境=dict#托管环境表：托管键 → 字符串值

已收集输出字段=('text','truncated','spillPath')#一路已捕获流：可能被截断的文本加上恢复信息
class 已收集输出(TypedDict):#一路已收集输出
    text:str#收集到的文本——截断时是流的尾部
    truncated:bool#为真表示 text 里丢掉过字节
    spillPath:NotRequired[str]#在截断且仍可用时，保存完整流的文件路径

收集模式字段=('maxBytes','spill')#一路输出流的有界内存收集，可带完整流溢出文件
溢出配置字段=('maxBytes',)#完整流溢出文件；缺省则完全不溢出
class 溢出配置(TypedDict):#完整流溢出文件配置
    maxBytes:int#整路流字节上限；更大的流会丢掉现已不完整的溢出文件

class 收集模式(TypedDict):#一路输出的有界内存收集
    maxBytes:int#内存上限（字节）；溢出时保留尾部
    spill:NotRequired[溢出配置]#完整流溢出文件；缺省则完全不溢出

三路输入输出字段=('stdin','stdout','stderr')#每路 stdio 处置，全部显式——本缝不套默认值
class 三路输入输出(TypedDict):#每路 stdio 处置
    stdin:object#标准输入处置：ignore / pipe / {data}
    stdout:object#标准输出处置：pipe / inherit / 收集模式
    stderr:object#标准错误处置：pipe / inherit / 收集模式

启动规格字段=('argv','cwd','stdio','graceMs','signal','env')#完全指定的 spawn 请求
class 启动规格(TypedDict):#完全指定的 spawn 请求；本缝不套默认值
    argv:list#可执行文件与参数；argv[0] 是程序，从不按 shell 解释
    cwd:str#子进程工作目录
    stdio:三路输入输出#每路 stdio 处置
    graceMs:int#正有限宽限期毫秒，用于 terminate 升级与退出后排空
    signal:NotRequired[object]#中止信号——触发时对进程树开始 terminate 升级
    env:NotRequired[dict]#显式环境条目，合并到擦洗过的父环境基座上

退出事实字段=('exitCode','signal')#一个已关闭进程的退出事实
class 退出事实(TypedDict):#已关闭进程的退出事实；不带超时/取消分类，也不带输出
    exitCode:int|None#退出码；进程因信号死亡时为 None
    signal:str|None#终止信号名；正常退出时为 None

一次读取字段=('text','nextOffset','lossy','spillPath')#一次增量 readFrom 读取
class 一次读取(TypedDict):#一次增量读取结果
    text:str#从请求偏移起的流文本（有损失时是整段保留尾部）
    nextOffset:int#下次读取应继续的整路流偏移
    lossy:bool#请求的偏移已滑出内存尾窗口时为真
    spillPath:NotRequired[str]#完整流溢出文件路径（若已创建且仍完整）

输出读取器字段=('readFrom',)#一路已收集输出流的无游标增量访问（载荷键字面量）
class 输出读取器:#一路已收集输出流的无游标增量访问
    """偏移是调用方拥有的整路流字节坐标，独立读取器不会互相消费输出。"""
    def 自偏移读取(自身,起始字节):#从指定整路流偏移读取
        """读取自起始字节以来捕获的全部内容；滑出内存尾时本次为有损。"""
        raise NotImplementedError('输出读取器.自偏移读取')#由提供方实现

收集输出集合字段=('stdout','stderr')#以收集模式启动的那些流的基于偏移的读取器
class 收集输出集合(TypedDict):#收集模式输出集合
    stdout:NotRequired[object]#当且仅当 stdout 是收集模式时存在
    stderr:NotRequired[object]#当且仅当 stderr 是收集模式时存在

句柄字段=('pid','stdin','stdout','stderr','collected','done','terminate','waitForExit')#一棵自己的进程树里的存活子进程
class 句柄:#存活子进程句柄协议
    """收集输出在退出后仍可读；管道流属于调用方。终止处处按树范围。

    数据字段名对齐上游 SubprocessHandle；方法仅中文：终止、等待退出。
    dict 形态句柄若仍带 terminate/waitForExit/readFrom 键，属提供方迁移债。
    """
    pid=None#进程 id（树根）；spawn 本身失败时为 -1
    stdin=None#子的 stdin，当且仅当以 stdin:pipe 启动时存在
    stdout=None#子的原始 stdout，当且仅当以 stdout:pipe 启动时存在
    stderr=None#子的原始 stderr，当且仅当以 stderr:pipe 启动时存在
    collected=None#收集模式流的基于偏移的读取器（退出后也可读）
    done=None#在进程 close 时兑现退出事实；仅 spawn 级失败会拒绝

    def 终止(自身):#对进程树开始升级终止
        """对进程树开始 SIGTERM→宽限→SIGKILL 升级——本缝唯一的终止动词。幂等。"""
        raise NotImplementedError('句柄.终止')#由提供方实现

    def 等待退出(自身,信号=None):#等到进程树已退出
        """等到整树已退出，不只是直接子。树退出为真，信号先中止为假。"""
        raise NotImplementedError('句柄.等待退出')#由提供方实现

终端信号=('SIGINT','SIGTERM','SIGKILL','SIGTSTP','SIGHUP')#终端进程原语支持的信号（与 terminal 缝成员一致）

终端启动规格字段=('argv','cwd','env','rows','cols','graceMs','signal')#完全指定的终端进程启动
class 终端启动规格(TypedDict):#完全指定的终端进程启动
    argv:list#可执行文件与参数；argv[0] 是程序
    cwd:str#该子进程提供方执行世界中的工作目录
    env:NotRequired[dict]#在提供方环境擦洗之后叠上的显式环境
    rows:int#初始终端行数
    cols:int#初始终端列数
    graceMs:int#完整终端会话的 TERM-to-KILL 清理宽限
    signal:NotRequired[object]#终端分配的取消；已发布句柄拥有其后续生命周期

前台组字段=('processGroupId','inputWaiting')#一个终端当前前台进程组事实
class 前台组(TypedDict):#终端当前前台进程组事实
    processGroupId:int#终端驱动发布的前台进程组 id
    inputWaiting:bool#提供方当前能否证明该组正在等待终端输入

终端句柄字段=('pid','output','done','write','inspectForeground','signalForeground','terminate')#一个存活终端进程及其拥有的操作系统会话
class 终端句柄:#存活终端句柄协议
    """终端分配、前台组检查/发信号、会话树清理是同一深层子进程原语。

    数据字段名对齐上游；方法仅中文：写入、检查前台、发信号前台、终止。
    """
    pid=None#顶层终端进程 id
    output=None#按投递顺序的 UTF-8 终端输出字节；退出后排空已排队输出时结束
    done=None#顶层进程退出时兑现；仅存活传输失败会拒绝

    def 写入(自身,数据):#向终端输入写入文本
        """向终端输入写入文本，不做隐式换行转换。"""
        raise NotImplementedError('终端句柄.写入')#由提供方实现

    def 检查前台(自身):#检查当前前台进程组
        """返回其 id 与等待输入事实；无法解析前台组时为 None。"""
        raise NotImplementedError('终端句柄.检查前台')#由提供方实现

    def 发信号前台(自身,信号名):#向当前前台进程组投递信号
        """投递允许的终端信号，返回实际收到该信号的组 id。"""
        raise NotImplementedError('终端句柄.发信号前台')#由提供方实现

    def 终止(自身):#幂等终止整终端会话
        """幂等地终止提供方仍能观察到的每个终端会话成员并等待静止。"""
        raise NotImplementedError('终端句柄.终止')#由提供方实现

标准输入模式=('ignore','pipe')#stdin 处置字面量；另有 {data} 批处理形态
标准输出模式=('pipe','inherit')#stdout/stderr 处置字面量；另有收集配置对象
