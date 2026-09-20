"""`glob` / `grep` 共用的搜索执行管道：打包 ripgrep 以前台 argv 启动、取完整内存 stdout、格式化结果并尽力溢出保存。

不经 shell 层；只解析 `rawOutputMaxBytes` 内完整 stdout，截断则失败。格式化结果经溢出存储保存供模型恢复。
"""
import importlib#惰性解析打包rg路径
import os#绝对路径、相对路径与分隔符
import re#非法模式stderr匹配
from ...模型后端.llm import 装备错误#带类型的Harness错误基类
from ...工具.输出保留 import 条目保留器,文本保留器#条数与文本保留器
from ...子进程.本地子进程 import 本地子进程错误#spawn与等待失败

原始输出最大字节=20_000_000#原始stdout默认字节上限
搜索超时毫秒=30_000#协作超时默认毫秒
搜索标准错误最大字节=64*1024#stderr诊断尾默认上限
搜索宽限毫秒=3_000#终止宽限期默认毫秒
搜索元最大字节=65_536#presentationMeta默认字节上限

rg路径记忆=None#进程内惰性解析一次的rg路径
非法模式=re.compile(r'regex parse error|error parsing glob',re.I|re.ASCII)#ripgrep拒绝正则或glob的stderr

class 搜索工具错误(Exception):#参数校验失败
    """搜索工具入参非法；详情保持英文线协议原文。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 已中止(信号):#读取中止标志
    """信号已置位则为已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event置位

def 字节长(文本):#UTF-8字节长度
    """按 UTF-8 字节计长。"""
    return len(文本.encode('utf-8'))#按utf8计字节

class 搜索错误(装备错误):#搜索带类型错误
    """带类型的搜索失败。扩展装备错误，因此携带稳定的搜索错误码并链接 cause；工具注册表在 isError 结果上暴露 { name, code }，以便重试/权限/UI 层无需解析消息即可分支。

    稳定错误码：SEARCH_INVALID_PATTERN — ripgrep 拒绝了正则或 glob；SEARCH_FAILED — 搜索无法运行或其输出无法解析；SEARCH_RAW_OUTPUT_OVERFLOW — 原始 rg 输出超出 rawOutputMaxBytes；SEARCH_ABORTED — 协作工具超时或调用方取消。
    """
    def __init__(自身,消息,码,选项=None):#记下稳定搜索错误码
        """记下稳定搜索错误码，并把 cause 链到本错误。"""
        super().__init__(消息,码,选项)#交给装备错误保存消息、错误码与cause
        自身.code=码#再写下本类的错误码字段
        自身.name='SearchError'#固定错误名

def 标准错误摘录(标准错误文本,已截断):#stderr诊断摘录
    """把保留的 stderr 尾做成诊断摘录；子进程丢掉字节时附截断说明。"""
    文本=标准错误文本.strip()
    if len(文本)==0:
        return ''
    if 已截断:#子进程侧已截断则标注
        return 文本+' [stderr truncated]'
    return 文本

def 归类运行失败(工具名,退出码,标准错误文本,标准错误已截断):#把非0/1退出归类为搜索错误
    """把非零退出的 rg 运行归入搜索错误词汇。不存在 shell 层，因此不会出现 exit 127 或 shell「找不到命令」文本——启动失败在 spawn 时拒绝。"""
    标准错误=标准错误摘录(标准错误文本,标准错误已截断)#诊断摘录
    if 非法模式.search(标准错误) is not None:#ripgrep拒绝正则或glob
        return 搜索错误(工具名+' pattern rejected by ripgrep: '+标准错误,'SEARCH_INVALID_PATTERN')#模式非法
    if len(标准错误)>0:#有stderr则接上
        后缀=': '+标准错误
    else:
        后缀=''
    return 搜索错误(工具名+' search failed (exit '+str(退出码)+')'+后缀,'SEARCH_FAILED')#其余非零退出

def 完整标准输出(工具名,标准输出,原始输出最大字节值):#取完整stdout或报溢出
    """取已完成运行的完整原始 stdout，强制 `rawOutputMaxBytes`。截断则失败，不解析残缺流。"""
    收窄='narrow pattern, path, or include and retry'#溢出时的收窄建议
    if 标准输出['lossy'] is not True:#lossy 非真表示 stdout 完整
        if 'text' not in 标准输出 or 标准输出['text'] is None:#缺席或显式空当空串
            内存文本=''
        else:
            内存文本=标准输出['text']
        内联字节=字节长(内存文本)#内存文本的 UTF-8 字节
        if 内联字节>原始输出最大字节值:#完整但超过工具自己的解析上限
            raise 搜索错误(#报告实际字节与上限
                工具名+' produced '+str(内联字节)+' bytes of raw output, over the '+str(原始输出最大字节值)+'-byte cap; '+收窄,
                'SEARCH_RAW_OUTPUT_OVERFLOW',
            )
        return 内存文本
    raise 搜索错误(#子进程未能在预算内保留完整 stdout
        工具名+' produced more raw output than the subprocess seam retained within the '+str(原始输出最大字节值)+'-byte cap; '+收窄,#截断即失败
        'SEARCH_RAW_OUTPUT_OVERFLOW',
    )

def 解析rg路径():#惰性解析打包的rg绝对路径
    """打包的 ripgrep 二进制路径，每个进程惰性解析一次。

    在调用边界解析平台包，缺失或损坏的安装在第一次搜索时以 SEARCH_FAILED 失败——加载时不探测。
    """
    global rg路径记忆#进程内记忆
    if rg路径记忆 is None:#首次调用才动态导入平台包
        模块=importlib.import_module('vscode_ripgrep')
        rg路径记忆=模块.rgPath#平台包导出的二进制路径
    return rg路径记忆#之后复用同一路径

def 执行ripgrep(上下文,执行,工具名,参数向量,原始输出最大字节值,宽限毫秒,标准错误最大字节值):#执行打包的ripgrep并取完整stdout
    """以前台 argv 执行打包 ripgrep 并返回完整原始 stdout。工作目录优先取会话 cwd，否则取进程 cwd。转发 exec.signal 以支持超时与取消。

    前置 --no-config，避免宿主 RIPGREP_CONFIG_PATH 注入 --pre。只读内存内 stdout；截断失败为 SEARCH_RAW_OUTPUT_OVERFLOW。

    退出语义：exit 0 有结果成功，exit 1 零结果成功（noMatches），其余抛搜索错误。
    """
    信号=执行['signal'] if 'signal' in 执行 else None#中止信号
    if 已中止(信号):#调用前已中止
        raise 搜索错误(工具名+' was aborted before completion (tool timeout or caller cancellation)','SEARCH_ABORTED')#报SEARCH_ABORTED
    智能体=执行['agent'] if 'agent' in 执行 else None#可选智能体
    if 智能体 is None:#无智能体
        会话工作目录=None#无会话cwd
    else:#有智能体
        头=智能体.session.header#会话头是dict
        会话工作目录=头['cwd'] if 'cwd' in 头 else None#会话工作目录（若有）
    工作目录=会话工作目录 if 会话工作目录 is not None else os.getcwd()#无会话则用进程cwd
    try:#创建spawn
        句柄=上下文.subprocess.spawn({#拉起打包的rg
            'argv':[解析rg路径(),'--no-config',*list(参数向量)],#二进制、禁用宿主配置、工具argv
            'cwd':工作目录,#在已解析工作目录运行
            'stdio':{#收集stdout/stderr诊断尾
                'stdin':'ignore',#不向rg喂stdin
                'stdout':{'maxBytes':原始输出最大字节值},#请求的stdout预算
                'stderr':{'maxBytes':标准错误最大字节值},#stderr诊断尾预算
            },#stdio结束
            'graceMs':宽限毫秒,#终止升级宽限期
            'signal':信号,#协作超时与调用方取消
        })#规格交给spawn
    except (本地子进程错误,OSError) as 错误:#创建期失败
        if 已中止(信号):#创建失败时若已中止则改报SEARCH_ABORTED
            raise 搜索错误(工具名+' was aborted before completion (tool timeout or caller cancellation)','SEARCH_ABORTED')#中止优先于启动失败
        raise 搜索错误(工具名+' could not start its search command (ripgrep launch failed)','SEARCH_FAILED',{'cause':错误})#其余创建失败带cause
    try:#等待进程结束
        结局=句柄.done.等待()#结束时给出退出码或信号
    except (本地子进程错误,OSError) as 错误:#等待失败：子进程基础设施错误
        raise 搜索错误(工具名+' could not start its search command (ripgrep launch failed)','SEARCH_FAILED',{'cause':错误})#归为SEARCH_FAILED并链cause
    已收集=句柄.collected#已收集输出
    标准输出读取器=已收集['stdout'] if 'stdout' in 已收集 else None#stdout读取器
    标准错误读取器=已收集['stderr'] if 'stderr' in 已收集 else None#stderr读取器
    标准输出=标准输出读取器.自偏移读取(0) if 标准输出读取器 is not None else None#从头读已收集的stdout
    标准错误=标准错误读取器.自偏移读取(0) if 标准错误读取器 is not None else None#从头读已收集的stderr
    if 标准输出 is None or 标准错误 is None:#缺少收集流
        raise 搜索错误(工具名+' search command produced no collected output streams','SEARCH_FAILED')#无法解析则失败
    if 已中止(信号):#结束后若已中止则不把部分输出当成功
        raise 搜索错误(工具名+' was aborted before completion (tool timeout or caller cancellation)','SEARCH_ABORTED')#报SEARCH_ABORTED
    信号名=结局['signal'] if 'signal' in 结局 else None#结束信号
    退出码=结局['exitCode'] if 'exitCode' in 结局 else None#退出码
    if 信号名 is not None or 退出码 is None:#被信号杀死或没有退出码
        信号展示=信号名 if 信号名 is not None else '(unknown)'#未知信号占位
        raise 搜索错误(工具名+' search command was killed by signal '+str(信号展示),'SEARCH_FAILED')#信号杀死归SEARCH_FAILED
    if 退出码!=0 and 退出码!=1:#非成功退出
        if 'text' not in 标准错误 or 标准错误['text'] is None:#缺席或null当空
            错误文本=''#空stderr
        else:#有文本
            错误文本=标准错误['text']#stderr文本
        raise 归类运行失败(工具名,退出码,错误文本,bool(标准错误['lossy']))#按stderr归类非法模式或一般失败
    文本=完整标准输出(工具名,标准输出,原始输出最大字节值)#强制完整stdout预算
    return {'stdout':文本,'noMatches':退出码==1,'workdir':工作目录}#exit 1视为成功零结果

def 改成工作目录相对(路径,工作目录):#绝对路径尽量改成工作目录相对
    """把 rg 输出路径映射为展示形态：已解析工作目录内的绝对路径变成工作目录相对；其余（相对输出、工作目录外的路径）原样通过。仅用于展示。"""
    if not os.path.isabs(路径):#相对输出原样返回
        return 路径#相对路径
    相对=os.path.relpath(路径,工作目录)#相对工作目录
    if 相对=='.' or 相对=='':#就是工作目录本身
        return '.'#展示为.
    if 相对=='..' or 相对.startswith('..'+os.sep):#在工作目录外则保持绝对
        return 路径#保持绝对
    return 相对#工作目录内则返回相对路径

def 预览行(行,最大字节):#按字节预算截断单行预览
    """把一条命中行预览限制到 maxBytes（保持 UTF-8 边界）并标记截断。上限是逐行预算事实；完整行仍在被搜索文件里供 read。"""
    保留器=文本保留器({'kind':'head','maxBytes':最大字节})#从头保留maxBytes
    保留器.推入(行)#喂入整行
    留下=保留器.收尾()#取出保留文本
    if 留下['truncated']:#被截断则标注
        return 留下['text']+' (line truncated)'#带截断标记
    return 留下['text']#完整预览

def 保留grep命中(命中列表,最大命中数,最大行字节):#内联截断grep命中并预览行
    """对规范 grep 命中列表应用共用内联上限：把每条保留行预览到 maxLineBytes，并留下前 maxMatches 条。面向模型渲染与搜索卡片投影都消费这一次保留。"""
    保留器=条目保留器({'maxItems':最大命中数})#从头保留maxMatches条
    for 命中 in 命中列表:#每条先截行再计入
        保留器.推入({#已预览的命中
            'path':命中['path'],#展示路径
            'lineNumber':命中['lineNumber'],#1基行号
            'line':预览行(命中['line'],最大行字节),#行预览
        })#单条推入结束
    return 保留器.收尾()#返回保留页与截断信息

def 保留glob路径(路径列表,最大结果数):#内联截断glob路径
    """对规范 glob 路径列表应用共用内联上限：留下前 maxResults 条。面向模型渲染与搜索卡片投影都消费这一次保留。"""
    保留器=条目保留器({'maxItems':最大结果数})#从头保留maxResults条
    for 路径 in 路径列表:#按发现顺序喂入
        保留器.推入(路径)#收下路径
    return 保留器.收尾()#返回保留页与截断信息

def 尽力保存格式化结果(上下文,执行,建议名,内容):#尽力保存完整格式化搜索结果
    """通过 上下文.spillStore.保存文本() 尽力保存一份完整格式化搜索结果——截断结果面向模型的恢复路径。用 上下文.获取服务() 读 spillStore（不是静态注入），因为格式化结果溢出是可选的；溢出所有者是调用 agent 的会话头 id。缺失后端、调用没有会话所有者、或 saveText() 拒绝时记一条警告并返回 None——调用方保留内联结果并报告完整结果未能保存；溢出存储不可用时，搜索成功绝不变成 isError。"""
    智能体=执行['agent'] if 'agent' in 执行 else None#可选智能体
    if 智能体 is None:#没有智能体
        会话标识=None#无会话id
    else:#有智能体
        头=智能体.session.header#会话头是dict
        会话标识=头['id'] if 'id' in 头 else None#溢出所有者会话id
    工具名=执行['name'] if 'name' in 执行 else None#工具名
    if 会话标识 is None:#没有会话所有者
        上下文.日志.警告('tool-fs-search: no session owner for '+str(工具名)+' result; complete result not saved')#警告后放弃保存
        return None#调用方报告未能保存
    溢出存储=上下文.获取服务('spillStore',False)#机会性读取可选后端
    if 溢出存储 is None:#未加载溢出后端；判空
        上下文.日志.警告('tool-fs-search: no ctx.spillStore backend loaded; complete '+str(工具名)+' result not saved')#警告后放弃保存
        return None#调用方报告未能保存
    保存={#一次文本溢出保存请求
        'owner':{'sessionId':会话标识},#所属会话
        'source':{'toolName':工具名,'callId':执行['callId'] if 'callId' in 执行 else None,'label':'result'},#来源是此次工具调用的结果
        'suggestedName':建议名,#建议文件名
        'content':内容,#完整格式化正文
    }#save请求结束
    try:#调用后端保存
        return 溢出存储.保存文本(保存)#成功则返回溢出引用
    except (OSError,NotImplementedError) as 错误:#保存失败不得让搜索变isError
        上下文.日志.警告('tool-fs-search: saveText failed for '+str(工具名)+': '+str(错误)+'; complete result not saved')#记下失败原因
        return None#调用方报告未能保存
