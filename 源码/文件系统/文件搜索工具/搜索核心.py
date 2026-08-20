"""`glob` / `grep` 搜索工具共用的执行管道：本包拥有的 `SEARCH_*` 错误词汇、一个以普通 argv 向量跑打包 ripgrep 二进制并返回完整原始 stdout 的 spawn 助手、尽力而为的格式化结果溢出交接，以及工作目录相对路径展示。

两个工具都作为普通前台 spawn 通过 `ctx.subprocess` 执行——绝不用 `ctx.shell`，绝不用 `ctx.shell.start()`，也绝不是模型可见的后台任务。ripgrep 二进制随依赖附带，因此不需要系统安装 `rg`；argv 向量与 ripgrep 之间不存在 shell 层，因此不涉及 shell 引号。原始 `rg` stdout 是内部传输细节：工具向子进程 seam 请求每次运行的 stdout 捕获预算，只解析 `rawOutputMaxBytes` 内完整的内存 stdout，从不读溢出文件。面向模型的恢复产物是通过 `ctx.spillStore.saveText()` 保存的格式化结果（`尽力保存格式化结果`）。
"""
import importlib#惰性解析打包rg路径
import os#绝对路径、相对路径与分隔符
import re#非法模式stderr匹配
from cordis.工具 import 是否thenable#可等待判定
from llm import 装备错误#带类型的Harness错误基类
from output_retention import 条目保留器,文本保留器#条数与文本保留器

原始输出最大字节=20_000_000#原始stdout默认字节上限
搜索超时毫秒=30_000#协作超时默认毫秒
搜索标准错误最大字节=64*1024#stderr诊断尾默认上限
搜索宽限毫秒=3_000#终止宽限期默认毫秒
搜索元最大字节=65_536#presentationMeta默认字节上限

_rg路径记忆=None#进程内惰性解析一次的rg路径

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
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

def 字节长(文本):#UTF-8字节长度
    """对齐 Buffer.byteLength(text, 'utf8')。"""
    return len(文本.encode('utf-8'))#按utf8计字节

class 搜索错误(装备错误):#搜索带类型错误
    """带类型的搜索失败。扩展装备错误，因此携带稳定的搜索错误码并链接 cause；工具注册表在 isError 结果上暴露 { name, code }，以便重试/权限/UI 层无需解析消息即可分支。

    稳定错误码：SEARCH_INVALID_PATTERN — ripgrep 拒绝了正则或 glob；SEARCH_FAILED — 搜索无法运行或其输出无法解析；SEARCH_RAW_OUTPUT_OVERFLOW — 原始 rg 输出超出 rawOutputMaxBytes；SEARCH_ABORTED — 协作工具超时或调用方取消。
    """
    def __init__(自身,消息,码,选项=None):#构造搜索错误
        """记下稳定搜索错误码，并把 cause 链到本错误。"""
        super().__init__(消息,码,选项)#交给装备错误保存消息、错误码与cause
        自身.code=码#再写下本类的错误码字段
        自身.name='SearchError'#固定错误名

def 标准错误摘录(标准错误文本,已截断):#stderr诊断摘录
    """把保留的 stderr 尾做成诊断摘录；子进程 seam 丢掉字节时附截断说明。"""
    文本=标准错误文本.strip()#去掉首尾空白
    if len(文本)==0:#空则无摘录
        return ''#空摘录
    return (文本+' [stderr truncated]') if 已截断 else 文本#被截断则标注

def 归类运行失败(工具名,退出码,标准错误文本,标准错误已截断):#把非0/1退出归类为搜索错误
    """把非零退出的 rg 运行归入搜索错误词汇。不存在 shell 层，因此不会出现 exit 127 或 shell「找不到命令」文本——启动失败在 spawn 时拒绝。"""
    标准错误=标准错误摘录(标准错误文本,标准错误已截断)#诊断摘录
    if re.search(r'regex parse error|error parsing glob',标准错误,re.I):#ripgrep拒绝正则或glob
        return 搜索错误(工具名+' pattern rejected by ripgrep: '+标准错误,'SEARCH_INVALID_PATTERN')#模式非法
    后缀=(': '+标准错误) if len(标准错误)>0 else ''#有stderr则接上
    return 搜索错误(工具名+' search failed (exit '+str(退出码)+')'+后缀,'SEARCH_FAILED')#其余非零退出

def 完整标准输出(工具名,标准输出,原始输出最大字节值):#取完整stdout或报溢出
    """获取已完成运行的完整原始 stdout，对内存传输强制 rawOutputMaxBytes。截断结果意味着子进程 seam 无法在请求预算内保留完整 stdout，因此工具明确失败，而不是解析一份静默残缺的流。"""
    收窄='narrow pattern, path, or include and retry'#溢出时的收窄建议
    if not 取字段(标准输出,'lossy'):#seam声称stdout完整
        内联字节=字节长(取字段(标准输出,'text') or '')#内存文本的UTF-8字节
        if 内联字节>原始输出最大字节值:#完整但超过工具自己的解析上限
            raise 搜索错误(#原始输出过大
                工具名+' produced '+str(内联字节)+' bytes of raw output, over the '+str(原始输出最大字节值)+'-byte cap; '+收窄,#报告实际字节与上限
                'SEARCH_RAW_OUTPUT_OVERFLOW',#溢出码
            )#超上限错误结束
        return 取字段(标准输出,'text') or ''#完整且未超上限
    raise 搜索错误(#seam未能在预算内保留完整stdout
        工具名+' produced more raw output than the subprocess seam retained within the '+str(原始输出最大字节值)+'-byte cap; '+收窄,#截断即失败
        'SEARCH_RAW_OUTPUT_OVERFLOW',#溢出码
    )#lossy失败结束

def 解析rg路径():#惰性解析打包的rg绝对路径
    """打包的 ripgrep 二进制路径，每个进程惰性解析一次。

    对齐 `@vscode/ripgrep`：在调用边界解析平台包，把缺失或损坏的安装失败留在第一次搜索调用上，成为 SEARCH_FAILED——这是本包已文档化的「加载时不探测」约定。
    """
    global _rg路径记忆#进程内记忆
    if _rg路径记忆 is None:#首次调用才动态导入平台包
        模块=importlib.import_module('vscode_ripgrep')#对齐@vscode/ripgrep的Python面
        _rg路径记忆=取字段(模块,'rgPath')#具名导出rgPath
    return _rg路径记忆#之后复用同一路径

def 信号已中止(信号):#读取中止标志
    """对齐 AbortSignal.aborted。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文属性
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文属性
        return True#已中止
    return False#未中止

def 跑ripgrep(上下文,执行,工具名,参数向量,原始输出最大字节值,宽限毫秒,标准错误最大字节值):#跑打包的ripgrep并取完整stdout
    """以普通 argv 向量跑打包的 ripgrep 二进制并返回其完整原始 stdout。工作目录在可用时为调用 agent 的会话 cwd，否则为 process.cwd()。转发 exec.signal，以便协作工具超时与调用方取消终止进程树。

    spawn 不受限（普通 ctx.subprocess 调用），因此前置 --no-config：否则宿主 RIPGREP_CONFIG_PATH（或二进制旁的 rg.conf）可能注入 --pre。collect 处置是 seam 的诊断尾形态（无溢出文件）：工具从不读原始溢出路径，截断的 stdout 失败为 SEARCH_RAW_OUTPUT_OVERFLOW。

    退出语义由工具拥有：exit 0 是带结果的成功，exit 1 是零结果的成功（noMatches），其余抛出搜索错误。
    """
    信号=取字段(执行,'signal')#中止信号
    if 信号已中止(信号):#调用前已中止
        raise 搜索错误(工具名+' was aborted before completion (tool timeout or caller cancellation)','SEARCH_ABORTED')#报SEARCH_ABORTED
    智能体=取字段(执行,'agent')#可选智能体
    会话=取字段(智能体,'session')#会话
    头=取字段(会话,'header')#会话头
    会话工作目录=取字段(头,'cwd')#会话工作目录（若有）
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
    except BaseException as 错误:#创建期同步失败
        #创建失败时若已中止则改报SEARCH_ABORTED；静态收窄无法看见AbortSignal状态变化，故此复查不能删。
        if 信号已中止(信号):#创建失败时若已中止则改报SEARCH_ABORTED
            raise 搜索错误(工具名+' was aborted before completion (tool timeout or caller cancellation)','SEARCH_ABORTED')#中止优先于启动失败
        raise 搜索错误(工具名+' could not start its search command (ripgrep launch failed)','SEARCH_FAILED',{'cause':错误})#其余创建失败带cause
    try:#等待进程结束
        结局=解开(取字段(句柄,'done'))#seam在结束时给出退出码或信号
    except BaseException as 错误:#handle.done拒绝：seam基础设施失败
        raise 搜索错误(工具名+' could not start its search command (ripgrep launch failed)','SEARCH_FAILED',{'cause':错误})#归为SEARCH_FAILED并链cause
    已收集=取字段(句柄,'collected')#已收集输出
    标准输出读取器=取字段(已收集,'stdout')#stdout读取器
    标准错误读取器=取字段(已收集,'stderr')#stderr读取器
    标准输出=标准输出读取器.readFrom(0) if 标准输出读取器 is not None else None#从头读已收集的stdout
    标准错误=标准错误读取器.readFrom(0) if 标准错误读取器 is not None else None#从头读已收集的stderr
    if 标准输出 is None or 标准错误 is None:#缺少收集流
        raise 搜索错误(工具名+' search command produced no collected output streams','SEARCH_FAILED')#无法解析则失败
    #等待spawn期间信号可能中止；静态收窄无法看见AbortSignal状态变化，故此复查不能删。
    if 信号已中止(信号):#结束后若已中止则不把部分输出当成功
        raise 搜索错误(工具名+' was aborted before completion (tool timeout or caller cancellation)','SEARCH_ABORTED')#报SEARCH_ABORTED
    信号名=取字段(结局,'signal')#结束信号
    退出码=取字段(结局,'exitCode')#退出码
    if 信号名 is not None or 退出码 is None:#被信号杀死或没有退出码
        信号展示=信号名 if 信号名 is not None else '(unknown)'#未知信号占位
        raise 搜索错误(工具名+' search command was killed by signal '+str(信号展示),'SEARCH_FAILED')#信号杀死归SEARCH_FAILED
    if 退出码!=0 and 退出码!=1:#非成功退出
        raise 归类运行失败(工具名,退出码,取字段(标准错误,'text') or '',bool(取字段(标准错误,'lossy')))#按stderr归类非法模式或一般失败
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
    return (取字段(留下,'text')+' (line truncated)') if 取字段(留下,'truncated') else 取字段(留下,'text')#被截断则标注

def 保留grep命中(命中们,最大命中数,最大行字节):#内联截断grep命中并预览行
    """对规范 grep 命中列表应用共用内联上限：把每条保留行预览到 maxLineBytes，并留下前 maxMatches 条。面向模型渲染与搜索卡片投影都消费这一次保留。"""
    保留器=条目保留器({'maxItems':最大命中数})#从头保留maxMatches条
    for 命中 in 命中们:#每条先截行再计入
        保留器.推入({#已预览的命中
            'path':取字段(命中,'path'),#展示路径
            'lineNumber':取字段(命中,'lineNumber'),#1基行号
            'line':预览行(取字段(命中,'line'),最大行字节),#行预览
        })#单条推入结束
    return 保留器.收尾()#返回保留页与截断信息

def 保留glob路径(路径们,最大结果数):#内联截断glob路径
    """对规范 glob 路径列表应用共用内联上限：留下前 maxResults 条。面向模型渲染与搜索卡片投影都消费这一次保留。"""
    保留器=条目保留器({'maxItems':最大结果数})#从头保留maxResults条
    for 路径 in 路径们:#按发现顺序喂入
        保留器.推入(路径)#收下路径
    return 保留器.收尾()#返回保留页与截断信息

def 尽力保存格式化结果(上下文,执行,建议名,内容):#尽力保存完整格式化搜索结果
    """通过 ctx.spillStore.saveText() 尽力保存一份完整格式化搜索结果——截断结果面向模型的恢复路径。用 ctx.get() 读 spillStore（不是静态注入），因为格式化结果溢出是可选的；溢出所有者是调用 agent 的会话头 id。缺失后端、调用没有会话所有者、或 saveText() 拒绝时记一条警告并返回 None——调用方保留内联结果并报告完整结果未能保存；溢出存储不可用时，搜索成功绝不变成 isError。"""
    智能体=取字段(执行,'agent')#可选智能体
    会话=取字段(智能体,'session')#会话
    头=取字段(会话,'header')#会话头
    会话标识=取字段(头,'id')#溢出所有者会话id
    工具名=取字段(执行,'name')#工具名
    if 会话标识 is None:#没有会话所有者
        上下文.logger.warn('tool-fs-search: no session owner for '+str(工具名)+' result; complete result not saved')#警告后放弃保存
        return None#调用方报告未能保存
    溢出存储=上下文.get('spillStore')#机会性读取可选后端
    if not 溢出存储:#未加载溢出后端
        上下文.logger.warn('tool-fs-search: no ctx.spillStore backend loaded; complete '+str(工具名)+' result not saved')#警告后放弃保存
        return None#调用方报告未能保存
    保存={#一次文本溢出保存请求
        'owner':{'sessionId':会话标识},#所属会话
        'source':{'toolName':工具名,'callId':取字段(执行,'callId'),'label':'result'},#来源是此次工具调用的结果
        'suggestedName':建议名,#建议文件名
        'content':内容,#完整格式化正文
    }#save请求结束
    try:#调用后端保存
        return 解开(溢出存储.保存文本(保存))#成功则返回溢出引用
    except BaseException as 错误:#保存失败不得让搜索变isError
        #尽力而为：存储失败绝不能让搜索失败或藏起内联结果——改由页脚报告未保存的剩余。
        上下文.logger.warn('tool-fs-search: saveText failed for '+str(工具名)+': '+str(错误)+'; complete result not saved')#记下失败原因
        return None#调用方报告未能保存
