"""shell 运行用的宿主内文件系统：直接叠在已挂载 VFS 上的
shell 文件系统面，外加每个程序共享的路径与诊断辅助。

本实现从内存应答。在自有 worker 中运行的命令使用消息后端实现
（`process/子进程.py`），由本实现从宿主侧服务。

对齐上游 `webworker-runtime/src/shell/fs-access.ts`。公开面仅中文名。
"""
from ..module_system.posix路径 import 解析 as 解析路径#路径解析
from ..storage.活动 import 要求活动vfs#活动VFS

__all__=['在目录解析','描述失败','文件系统错误','宿主文件系统']#仅中文公开名

def 在目录解析(工作目录,路径):#解析绝对路径
    """将一个 shell 词解析为绝对 VFS 路径。"""
    return 解析路径(工作目录,路径)#相对cwd解析

def 描述失败(程序,路径,错误):#重述FS失败
    """按 shell 工具的报告方式重述文件系统失败。"""
    码=getattr(错误,'code',None) if not isinstance(错误,dict) else 错误.get('code')#取出错误码
    if 码=='ENOENT':#不存在
        原因='No such file or directory'#文案
    elif 码=='ENOTDIR':#非目录
        原因='Not a directory'#文案
    elif 码=='EISDIR':#是目录
        原因='Is a directory'#文案
    elif 码=='ENOTEMPTY':#非空
        原因='Directory not empty'#文案
    elif 码=='EEXIST':#已存在
        原因='File exists'#文案
    else:#回退
        原因=str(错误) if isinstance(错误,BaseException) else str(错误)#Error.message 或 String(error)
    return f'{程序}: {路径}: {原因}'#拼诊断行

def 文件系统错误(码,系统调用,路径):#构造FS错误
    """构造 Node 形态的文件系统错误。"""
    原因='permission denied' if 码=='EACCES' else f'{系统调用} failed'#拒绝或失败文案
    错误=Exception(f"{码}: {原因}, {系统调用} '{路径}'")#创建错误
    错误.code=码#挂错误码
    错误.path=路径#挂路径
    错误.syscall=系统调用#挂系统调用名
    return 错误#返回错误

def 投影统计(统计):#投影统计
    """将 VFS 统计投影为程序读取的事实。"""
    是目录=统计['isDirectory']() if callable(统计.get('isDirectory')) else 统计.get('directory',False)#是否目录
    return {'directory':是目录,'size':统计['size'],'mtimeMs':统计['mtimeMs']}#取shell关心字段

def 宿主文件系统():#宿主内文件系统
    """由本线程已挂载 VFS 支撑的文件系统。"""
    def 取vfs():#惰性取活动VFS
        """取活动 VFS。"""
        return 要求活动vfs()#惰性取
    def 统计(路径):#stat实现
        """stat。"""
        try:#尝试读取
            return 投影统计(取vfs().statSync(路径))#同步stat
        except Exception:#失败当作无内容
            return None#无内容
    def 列出(路径):#列目录
        """列目录。"""
        名们=sorted(list(取vfs().readdirSync(路径)))#同步读名并排序
        条目们=[]#结果缓冲
        for 名 in 名们:#逐名
            子统计=统计(解析路径(路径,名))#查是否目录
            条目们.append({'name':名,'directory':False if 子统计 is None else 子统计['directory']})#条目
        return 条目们#返回条目
    def 读文本(路径):#读文本
        """读文本。"""
        子统计=统计(路径)#查询
        if 子统计 is not None and 子统计['directory'] is True:#拒读目录
            raise 文件系统错误('EISDIR','read',路径)#抛错
        return 取vfs().readFileSync(路径,'utf8')#同步读UTF-8
    def 写文本(路径,文本,追加=False):#写文本
        """写文本。"""
        if 追加:#追加
            取vfs().appendFileSync(路径,文本)#追加
        else:#覆盖写
            取vfs().writeFileSync(路径,文本)#覆盖写
    def 建目录(路径,递归):#建目录
        """建目录。"""
        取vfs().mkdirSync(路径,{'recursive':递归})#同步建
    def 移除(路径,选项):#移除
        """移除。"""
        取vfs().rmSync(路径,选项)#同步移除
    def 重命名(源,目标):#重命名
        """重命名。"""
        取vfs().renameSync(源,目标)#同步重命名
    return {'stat':统计,'list':列出,'readText':读文本,'writeText':写文本,'mkdir':建目录,'remove':移除,'rename':重命名}#组装面
