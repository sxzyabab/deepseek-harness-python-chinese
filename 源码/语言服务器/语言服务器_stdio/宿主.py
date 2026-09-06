"""通用 stdio LSP 提供方所用的文件系统 seam 源访问。"""
from ...工具.超时 import 若已中止则抛出#已中止即抛错
from ..语言服务器 import 语言服务器错误#本缝异常基类

宿主工作区字段=('target','canonicalPath','fileUrl')#文件系统/子进程执行世界中的规范工作区
宿主源字段=('fileUrl','text')#已校验的源文件，以及发给语言服务器的精确 URI

def 错误消息(错误):
    """未知错误收成消息字符串。"""
    return str(错误)#消息

def 规范化工作区(文件系统,工作区根,信号=None):
    """通过 ctx.fs 解析并校验一个工作区。工作区与信息是 dict。"""
    若已中止则抛出(信号)#进入前若已取消则抛错
    try:#解析工作区路径
        选项={} if 信号 is None else {'signal':信号}#可选取消
        目标=文件系统.解析(工作区根,选项)#经文件系统解析工作区
    except BaseException as 错误:#解析失败；fs 服务错误类型由对面 seam 决定
        若已中止则抛出(信号)#若是取消则抛取消错误
        包装=语言服务器错误('workspace root "'+str(工作区根)+'" cannot be resolved: '+错误消息(错误),'LSP_WORKSPACE')#包装解析失败
        包装.__cause__=错误#挂上cause
        raise 包装#抛出
    若已中止则抛出(信号)#解析后再次检查取消
    try:#取工作区元数据
        信息=文件系统.状态(目标,信号)#stat
    except BaseException as 错误:#stat失败；fs 服务错误类型由对面 seam 决定
        若已中止则抛出(信号)#stat失败时优先暴露取消
        raise 错误#否则原样抛出stat错误
    若已中止则抛出(信号)#stat后再检查取消
    类型=信息['type'] if 信息 is not None and 'type' in 信息 else None#目标类型
    if 类型!='directory':#目标不是目录
        raise 语言服务器错误('workspace root "'+str(工作区根)+'" is not a directory','LSP_WORKSPACE')#拒绝非目录工作区
    进程路径=文件系统.进程路径(目标)#规范进程路径
    文件网址=文件系统.文件网址(目标)#规范file URI
    return {'target':目标,'canonicalPath':进程路径,'fileUrl':文件网址}#组装规范工作区

def 读宿主源(文件系统,文件路径,工作区,最大文档字节,信号=None):
    """通过 ctx.fs 解析、约束并读取一份带字节上限的查询源。本层拥有 LSP 特有的完整文档上限，而文件系统提供方拥有流式读取、普通文件检查与 UTF-8 校验。工作区是 dict。"""
    若已中止则抛出(信号)#进入前若已取消则抛错
    try:#相对工作区解析源路径
        选项={'cwd':工作区['canonicalPath']}#带cwd解析源路径
        if 信号 is not None:#有取消
            选项['signal']=信号#叠上信号
        目标=文件系统.解析(文件路径,选项)#resolve
    except BaseException as 错误:#解析失败；fs 服务错误类型由对面 seam 决定
        若已中止则抛出(信号)#若是取消则抛取消错误
        包装=语言服务器错误('source "'+str(文件路径)+'" cannot be resolved: '+错误消息(错误),'LSP_SOURCE')#包装解析失败
        包装.__cause__=错误#挂上cause
        raise 包装#抛出
    若已中止则抛出(信号)#解析后再检查取消
    if 文件系统.包含(工作区['target'],目标) is False:#源落在工作区外
        raise 语言服务器错误('source "'+str(文件路径)+'" resolves outside the workspace','LSP_SOURCE')#拒绝越界源
    块列表=[]#已接受的文本块
    字节=0#已累计字节
    try:#流式读取源文本
        流=文件系统.流文本(目标,信号)#打开文本流
        for 块 in 流:#逐块读取
            若已中止则抛出(信号)#每块前检查取消
            if isinstance(块,bytes):#原始字节
                增量=len(块)#按字节累计
                文本=块.decode('utf-8')#解码
            else:#已解码文本
                文本=块#文本块
                增量=len(文本.encode('utf-8'))#按UTF-8字节累计
            字节+=增量#累计
            if 字节>最大文档字节:#超过上限则停止继续收块
                break#停止
            块列表.append(文本)#收下未超限的块
    except BaseException as 错误:#读取失败；流错误类型由对面 seam 决定
        若已中止则抛出(信号)#若是取消则抛取消错误
        包装=语言服务器错误('source "'+str(文件路径)+'" could not be read: '+错误消息(错误),'LSP_SOURCE')#包装读取失败
        包装.__cause__=错误#挂上cause
        raise 包装#抛出
    if 字节>最大文档字节:#累计已超上限
        raise 语言服务器错误('source "'+str(文件路径)+'" exceeds the '+str(最大文档字节)+'-byte limit; reading stopped after '+str(字节)+' bytes','LSP_SOURCE')#拒绝过大源
    若已中止则抛出(信号)#返回前再检查取消
    文件网址=文件系统.文件网址(目标)#规范URI
    return {'fileUrl':文件网址,'text':''.join(块列表)}#组装宿主源
