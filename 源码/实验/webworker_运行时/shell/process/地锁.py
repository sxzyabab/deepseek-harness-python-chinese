"""Landlock 启动器解析与 worker shell 的每进程 VFS 强制。

对齐上游 `webworker-runtime/src/shell/process/landlock.ts`。公开面仅中文名。
"""
from ...module_system.posix路径 import 解析 as 解析路径#路径解析
from ...storage.路径 import dsh临时#临时根
from ..文件系统访问 import 文件系统错误#FS错误

__all__=['地锁启动器错误','解析地锁参数','地锁文件系统','地锁可执行']#仅中文公开名

class 地锁启动器错误(Exception):#启动器错误
    """启动器自有失败；调用方以其消息加 `landlock-run:` 前缀打印。"""

空设备统计={'directory':False,'size':0,'mtimeMs':0}#虚拟/dev/null统计
设备根='/dev'#设备根
空设备路径='/dev/null'#空设备路径

def 映射vfs路径(路径,工作目录):#映射进VFS
    """将宿主启动器的临时路径映射进 Worker VFS。"""
    已解析=解析路径(工作目录,路径)#相对cwd解析
    绝对=已解析 if len(已解析)<=1 else 已解析.rstrip('/')#去尾斜杠
    if 绝对=='/tmp':#映射临时根
        return dsh临时#临时根
    if 绝对.startswith('/tmp/'):#映射临时子路径
        return f'{dsh临时}{绝对[len("/tmp"):]}'#映射
    return 绝对#其它原样

def 包含(根,路径):#路径是否在根下
    """规范化路径是否为根自身或其后代之一。"""
    return 根=='/' or 路径==根 or 路径.startswith(f'{根}/')#根或后代

def 拒绝(系统调用,路径):#拒绝访问
    """抛出 `dsh-bash-sandbox` 所消费的拒绝方言。"""
    raise 文件系统错误('EACCES',系统调用,路径)#抛EACCES

def 启动器退出(退出码,标准输出='',标准错误=''):#终端退出
    """构建一次启动器自有的终端结果。"""
    return {'kind':'exit','exitCode':退出码,'stdout':标准输出,'stderr':标准错误}#组装退出

def 启动器失败(错误):#启动器失败
    """将解析器或授权失败转换为原生启动器的致命方言。"""
    细节=错误.args[0] if isinstance(错误,地锁启动器错误) and 错误.args else str(错误)#细节文案
    return 启动器退出(125,'',f'landlock-run: {细节}\n')#退出125

def 解析地锁参数(参数们):#解析启动器argv
    """解析原生启动器的 argv 文法。"""
    只读=[]#只读根缓冲
    读写=[]#读写根缓冲
    索引=0#游标
    while 索引<len(参数们):#逐参扫描
        参数=参数们[索引]#当前参数
        if 参数=='--probe':#探测标志
            if len(参数们)!=1:#禁止夹带
                raise 地锁启动器错误('usage error: --probe takes no other arguments')#拒绝
            return {'kind':'probe'}#探测结果
        if 参数 in ('--ro','--rw'):#授权标志
            if 索引+1>=len(参数们):#缺路径
                raise 地锁启动器错误(f'usage error: {参数} requires a path')#缺路径
            路径=参数们[索引+1]#紧随路径
            (只读 if 参数=='--ro' else 读写).append(路径)#记入对应列表
            索引+=2#消费两参
            continue#下一参数
        if 参数=='--':#命令分隔
            argv=list(参数们[索引+1:])#其后即命令
            if len(argv)==0:#缺命令
                raise 地锁启动器错误('usage error: missing `-- <argv>...` command')#缺命令
            return {'kind':'run','readOnly':只读,'readWrite':读写,'argv':argv}#受限运行
        raise 地锁启动器错误(f'usage error: unknown argument: {参数}')#未知参数
    raise 地锁启动器错误('usage error: missing `-- <argv>...` command')#未给命令

def 地锁文件系统(底层,调用,工作目录):#构建受限FS
    """校验授权根并创建一份进程本地文件系统守卫。"""
    def 规范化授权(路径):#规范化授权根
        """规范化授权根。"""
        if 路径=='':#空路径
            raise 地锁启动器错误('cannot open rule path: : No such file or directory')#空路径
        目标=映射vfs路径(路径,工作目录)#映射路径
        if 目标!=设备根 and 目标!=空设备路径 and 底层['stat'](目标) is None:#非虚拟且不存在
            raise 地锁启动器错误(f'cannot open rule path: {路径}: No such file or directory')#授权根无效
        return 目标#返回规范化根
    只读=[规范化授权(路径) for 路径 in 调用['readOnly']]#规范化只读根
    读写=[规范化授权(路径) for 路径 in 调用['readWrite']]#规范化读写根
    可读=只读+读写#可读根并集
    def 已检路径(路径,系统调用):#校验并映射
        """校验并映射。"""
        目标=映射vfs路径(路径,工作目录)#映射
        if 目标.startswith(f'{空设备路径}/'):#null下非法
            raise 文件系统错误('ENOTDIR',系统调用,路径)#抛错
        return 目标#返回目标
    def 读路径(路径,系统调用):#读授权检查
        """读授权检查。"""
        目标=已检路径(路径,系统调用)#先映射
        if not any(包含(根,目标) for 根 in 可读):#不在可读根
            拒绝(系统调用,路径)#拒绝
        return 目标#放行
    def 写路径(路径,系统调用):#写授权检查
        """写授权检查。"""
        目标=已检路径(路径,系统调用)#先映射
        if not any(包含(根,目标) for 根 in 读写):#不在读写根
            拒绝(系统调用,路径)#拒绝
        return 目标#放行
    def 统计(路径):#stat
        """stat。"""
        目标=读路径(路径,'stat')#读检查
        if 目标==空设备路径:#虚拟null
            return 空设备统计#虚拟统计
        if 目标==设备根 and not 底层['stat'](目标):#虚拟/dev
            return {'directory':True,'size':0,'mtimeMs':0}#虚拟目录
        return 底层['stat'](目标)#委托底层
    def 列出(路径):#list
        """list。"""
        目标=读路径(路径,'scandir')#读检查
        if 目标==设备根:#虚拟/dev内容
            return [{'name':'null','directory':False}]#虚拟内容
        if 目标==空设备路径:#null非目录
            raise 文件系统错误('ENOTDIR','scandir',路径)#抛错
        return 底层['list'](目标)#委托底层
    def 读文本(路径):#读文本
        """读文本。"""
        目标=读路径(路径,'open')#读检查
        return '' if 目标==空设备路径 else 底层['readText'](目标)#null空串否则读
    def 写文本(路径,文本,追加=False):#写文本
        """写文本。"""
        目标=写路径(路径,'open')#写检查
        if 目标!=空设备路径:#null吞写
            底层['writeText'](目标,文本,追加)#委托
    def 建目录(路径,递归):#建目录
        """建目录。"""
        目标=写路径(路径,'mkdir')#写检查
        if 目标==空设备路径:#null已存在
            raise 文件系统错误('EEXIST','mkdir',路径)#抛错
        底层['mkdir'](目标,递归)#委托底层
    def 移除(路径,选项):#移除
        """移除。"""
        目标=写路径(路径,'rm')#写检查
        if 目标==空设备路径:#禁删null
            拒绝('rm',路径)#拒绝
        底层['remove'](目标,选项)#委托底层
    def 重命名(源,目标路径):#重命名
        """重命名。"""
        源目标=写路径(源,'rename')#源写检查
        目的=写路径(目标路径,'rename')#目标写检查
        if 源目标==空设备路径 or 目的==空设备路径:#禁涉null
            拒绝('rename',源 if 源目标==空设备路径 else 目标路径)#拒绝
        底层['rename'](源目标,目的)#委托底层
    return {'stat':统计,'list':列出,'readText':读文本,'writeText':写文本,'mkdir':建目录,'remove':移除,'rename':重命名}#受限面

def 地锁准备(参数们,上下文):#异步准备
    """准备 landlock 调用。"""
    try:#解析并准备
        调用=解析地锁参数(参数们)#解析argv
        if 调用['kind']=='probe':#探测成功
            return 启动器退出(0,'landlock: fully enforced\n')#探测
        return {#委托运行
            'kind':'delegate',#种类
            'argv':调用['argv'],#被包裹命令
            'filesystem':地锁文件系统(上下文['filesystem'],调用,上下文['cwd']),#受限FS
            'missingExecutable':启动器退出(125,'','landlock-run: exec failed: No such file or directory\n'),#缺可执行
        }#委托结束
    except Exception as 错误:#失败
        return 启动器失败(错误)#转致命方言

def 地锁同步运行(参数们):#同步子集
    """处理可同步完成的子集。"""
    try:#解析
        调用=解析地锁参数(参数们)#解析argv
        if 调用['kind']=='probe':#探测可同步
            return 启动器退出(0,'landlock: fully enforced\n')#探测成功
        return {'kind':'asynchronous'}#运行需异步
    except Exception as 错误:#失败
        return 启动器失败(错误)#转致命方言

地锁可执行={#landlock虚拟可执行
    'name':'landlock-run',#逻辑名
    'prepare':地锁准备,#异步准备
    'runSync':地锁同步运行,#同步运行子集
}#地锁可执行结束
