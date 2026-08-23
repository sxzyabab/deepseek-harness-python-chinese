"""通用 stdio LSP 提供方所用的文件系统 seam 源访问。"""
from .取消 import 若已中止则抛#已中止即抛错
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

宿主工作区字段=('target','canonicalPath','fileUrl')#文件系统/子进程执行世界中的规范工作区
宿主源字段=('fileUrl','text')#已校验的源文件，以及发给语言服务器的精确 URI

def 错误消息(错误):#把未知错误收成消息字符串
    """Error 取 message，否则 String 强制。"""
    if isinstance(错误,BaseException):#异常
        return str(错误)#消息
    return str(错误)#强制字符串

def 规范化工作区(文件系统,工作区根,信号=None):#把调用方工作区路径规范成宿主工作区
    """通过 ctx.fs 解析并校验一个工作区。"""
    若已中止则抛(信号)#进入前若已取消则抛错
    try:#解析工作区路径
        选项={} if 信号 is None else {'signal':信号}#可选取消
        目标=解开(文件系统.resolve(工作区根,选项) if hasattr(文件系统,'resolve') else 文件系统.解析(工作区根,选项))#经文件系统解析工作区
    except BaseException as 错误:#解析失败
        若已中止则抛(信号)#若是取消则抛取消错误
        包装=Exception('workspace root "'+str(工作区根)+'" cannot be resolved: '+错误消息(错误))#包装解析失败
        包装.__cause__=错误#挂上cause
        raise 包装#抛出
    若已中止则抛(信号)#解析后再次检查取消
    try:#取工作区元数据
        信息=解开(文件系统.stat(目标,信号) if hasattr(文件系统,'stat') else 文件系统.状态(目标,信号))#stat
    except BaseException as 错误:#stat失败
        若已中止则抛(信号)#stat失败时优先暴露取消
        raise 错误#否则原样抛出stat错误
    若已中止则抛(信号)#stat后再检查取消
    类型=取字段(信息,'type') if 信息 is not None else None#目标类型
    if 类型!='directory':#目标不是目录
        raise Exception('workspace root "'+str(工作区根)+'" is not a directory')#拒绝非目录工作区
    进程路径=文件系统.processPath(目标) if hasattr(文件系统,'processPath') else 文件系统.进程路径(目标)#规范进程路径
    文件网址=文件系统.fileUrl(目标) if hasattr(文件系统,'fileUrl') else 文件系统.文件网址(目标)#规范file URI
    return {'target':目标,'canonicalPath':进程路径,'fileUrl':文件网址}#组装规范工作区

def 读宿主源(文件系统,文件路径,工作区,最大文档字节,信号=None):#读取并约束一份查询源
    """通过 ctx.fs 解析、约束并读取一份带字节上限的查询源。本层拥有 LSP 特有的完整文档上限，而文件系统提供方拥有流式读取、普通文件检查与 UTF-8 校验。"""
    若已中止则抛(信号)#进入前若已取消则抛错
    try:#相对工作区解析源路径
        选项={'cwd':取字段(工作区,'canonicalPath')}#带cwd解析源路径
        if 信号 is not None:#有取消
            选项['signal']=信号#叠上信号
        目标=解开(文件系统.resolve(文件路径,选项) if hasattr(文件系统,'resolve') else 文件系统.解析(文件路径,选项))#resolve
    except BaseException as 错误:#解析失败
        若已中止则抛(信号)#若是取消则抛取消错误
        包装=Exception('source "'+str(文件路径)+'" cannot be resolved: '+错误消息(错误))#包装解析失败
        包装.__cause__=错误#挂上cause
        raise 包装#抛出
    若已中止则抛(信号)#解析后再检查取消
    包含=文件系统.contains if hasattr(文件系统,'contains') else 文件系统.包含#包含关系
    if not 包含(取字段(工作区,'target'),目标):#源落在工作区外
        raise Exception('source "'+str(文件路径)+'" resolves outside the workspace')#拒绝越界源
    块们=[]#已接受的文本块
    字节=0#已累计字节
    try:#流式读取源文本
        # XXX(lsp-source-replacement): 仅当真实查询在规范包含检查与提供方打开此流之间观察到替换时，再回头看稳定句柄身份。
        流入口=文件系统.streamText if hasattr(文件系统,'streamText') else 文件系统.流文本#文本流入口
        流=解开(流入口(目标,信号))#打开文本流
        for 块 in 流:#逐块读取
            若已中止则抛(信号)#每块前检查取消
            if isinstance(块,bytes):#原始字节
                增量=len(块)#按字节累计
                文本=块.decode('utf-8')#解码
            else:#已解码文本
                文本=块#文本块
                增量=len(文本.encode('utf-8'))#按UTF-8字节累计
            字节+=增量#累计
            if 字节>最大文档字节:#超过上限则停止继续收块
                break#停止
            块们.append(文本)#收下未超限的块
    except BaseException as 错误:#读取失败
        若已中止则抛(信号)#若是取消则抛取消错误
        包装=Exception('source "'+str(文件路径)+'" could not be read: '+错误消息(错误))#包装读取失败
        包装.__cause__=错误#挂上cause
        raise 包装#抛出
    if 字节>最大文档字节:#累计已超上限
        raise Exception('source "'+str(文件路径)+'" exceeds the '+str(最大文档字节)+'-byte limit; reading stopped after '+str(字节)+' bytes')#拒绝过大源
    若已中止则抛(信号)#返回前再检查取消
    文件网址=文件系统.fileUrl(目标) if hasattr(文件系统,'fileUrl') else 文件系统.文件网址(目标)#规范URI
    return {'fileUrl':文件网址,'text':''.join(块们)}#组装宿主源
