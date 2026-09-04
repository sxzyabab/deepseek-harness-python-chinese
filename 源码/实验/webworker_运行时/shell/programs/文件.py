"""命令表的文件与目录工具，全部叠在 shell 的文件系统上。列表每行打印一项：
此处从不是终端，因此真 `ls` 为 tty 选择的列布局在工具结果中只会是噪音。

对齐上游 `webworker-runtime/src/shell/programs/files.ts`。公开面仅中文名。
"""
import fnmatch as 文件名匹配#名称glob（对齐picomatch）
from datetime import datetime as 日期时间,timezone as 时区#修改时间
from ...module_system.posix路径 import 基名,目录名,解析 as 解析路径#路径工具
from ..文件系统访问 import 描述失败,在目录解析#FS辅助
from .选项 import 解析选项#选项解析

__all__=['文件程序']#仅中文公开名

def 长格式条目(统计,名):#长格式条目
    """按 `ls -l` 方式格式化一项，用 VFS 实际持有的事实。"""
    大小=str(0 if 统计 is None else 统计['size']).rjust(8)#对齐大小
    毫秒=0 if 统计 is None else 统计['mtimeMs']#修改时间毫秒
    修改=日期时间.fromtimestamp(毫秒/1000,时区.utc).isoformat().replace('T',' ')[:16]#修改时间
    模式='drwxr-xr-x' if 统计 is not None and 统计['directory'] is True else '-rw-r--r--'#模式
    return f'{模式} {大小} {修改} {名}'#拼长行

def ls程序(argv,io,state,fs):#ls程序
    """列出目录。"""
    选项=解析选项(argv)#解析选项
    操作数=选项['operands'] if len(选项['operands'])>0 else ['.']#默认当前目录
    状态=0#累积状态
    for 索引,操作数名 in enumerate(操作数):#逐操作数
        路径=在目录解析(state['cwd'],操作数名)#绝对路径
        统计=fs['stat'](路径)#查询
        if 统计 is None:#不存在
            io['err'](f'ls: {操作数名}: No such file or directory\n')#诊断
            状态=2#失败
            continue#下一操作数
        if len(操作数)>1:#多目标标题
            io['out'](f"{chr(10) if 索引>0 else ''}{操作数名}:\n")#标题
        if not 统计['directory']:#文件
            示=长格式条目(统计,操作数名) if 'l' in 选项['flags'] else 操作数名#显示
            io['out'](f'{示}\n')#打印文件
            continue#下一操作数
        条目们=[条目 for 条目 in fs['list'](路径) if 'a' in 选项['flags'] or not 条目['name'].startswith('.')]#过滤隐藏
        for 条目 in 条目们:#逐条目
            if 'l' in 选项['flags']:#长格式
                示=长格式条目(fs['stat'](解析路径(路径,条目['name'])),条目['name'])#长格式
            else:#短名
                示=条目['name']#短名
            io['out'](f'{示}\n')#打印
    return 状态#返回状态

def find程序(argv,io,state,fs):#find程序
    """查找路径。"""
    # `find` 用单短横拼写多字母谓词，共享选项解析器会将其读为捆绑短标志；本遍历自行读取。
    根们=[]#搜索根
    名称模式=None#名称模式
    种类=None#类型谓词
    最大深度=float('inf')#最大深度
    词们=argv[1:]#去掉程序名
    索引=0#游标
    while 索引<len(词们):#逐词
        词=词们[索引]#当前词
        if 词=='-name':#名称谓词
            索引+=1#取下一
            名称模式=词们[索引] if 索引<len(词们) else None#模式
            索引+=1#推进
            continue#下一
        if 词=='-type':#类型谓词
            索引+=1#取下一
            种类=词们[索引] if 索引<len(词们) else None#种类
            索引+=1#推进
            continue#下一
        if 词=='-maxdepth':#深度
            索引+=1#取下一
            try:#解析
                最大深度=int(词们[索引] if 索引<len(词们) else '',10)#深度
            except ValueError:#非法
                最大深度=float('nan')#非法
            索引+=1#推进
            continue#下一
        if 词.startswith('-'):#未知谓词
            io['err'](f'find: unsupported predicate {词}\n')#诊断
            return 2#用法错
        根们.append(词)#搜索根
        索引+=1#推进
    def 名称匹配(显示):#名称匹配
        """对齐 picomatch(namePattern, { dot: true })。"""
        if 名称模式 is None:#无模式
            return True#全过
        return 文件名匹配.fnmatch(基名(显示),名称模式)#匹配基名
    状态=[0]#累积状态（闭包可写）
    def 访问(路径,显示,深度):#递归访问
        """访问节点。"""
        统计=fs['stat'](路径)#查询
        if 统计 is None:#不存在
            io['err'](f'find: {显示}: No such file or directory\n')#诊断
            状态[0]=1#失败
            return#停止本支
        选中=名称匹配(显示) and (种类 is None or (种类=='d')==统计['directory'])#名称与类型
        if 选中:#打印匹配
            io['out'](f'{显示}\n')#打印
        if not 统计['directory'] or 深度>=最大深度:#非目录或达深度
            return#停止
        for 条目 in fs['list'](路径):#子项
            子显示=f"{'' if 显示=='/' else 显示}/{条目['name']}"#显示
            访问(解析路径(路径,条目['name']),子显示,深度+1)#递归
    for 根 in (根们 if len(根们)>0 else ['.']):#遍历根
        访问(在目录解析(state['cwd'],根),根,0)#访问
    return 状态[0]#返回状态

def mkdir程序(argv,io,state,fs):#mkdir程序
    """建目录。"""
    选项=解析选项(argv)#解析选项
    状态=0#累积状态
    for 操作数 in 选项['operands']:#逐路径
        try:#尝试创建
            fs['mkdir'](在目录解析(state['cwd'],操作数),'p' in 选项['flags'])#建目录
        except Exception as 错误:#失败
            io['err'](f'{描述失败("mkdir",操作数,错误)}\n')#诊断
            状态=1#失败
    return 状态#返回状态

def rmdir程序(argv,io,state,fs):#rmdir程序
    """删空目录。"""
    选项=解析选项(argv)#解析选项
    状态=0#累积状态
    for 操作数 in 选项['operands']:#逐路径
        路径=在目录解析(state['cwd'],操作数)#绝对路径
        if len(fs['list'](路径))>0:#非空
            io['err'](f'rmdir: {操作数}: Directory not empty\n')#诊断
            状态=1#失败
            continue#下一路径
        try:#尝试移除
            fs['remove'](路径,{'recursive':True,'force':False})#移除空目录
        except Exception as 错误:#失败
            io['err'](f'{描述失败("rmdir",操作数,错误)}\n')#诊断
            状态=1#失败
    return 状态#返回状态

def rm程序(argv,io,state,fs):#rm程序
    """删除。"""
    选项=解析选项(argv)#解析选项
    递归='r' in 选项['flags'] or 'R' in 选项['flags']#递归
    强制='f' in 选项['flags']#强制
    状态=0#累积状态
    for 操作数 in 选项['operands']:#逐路径
        路径=在目录解析(state['cwd'],操作数)#绝对路径
        统计=fs['stat'](路径)#查询
        if 统计 is None:#不存在
            if 强制:#强制则忽略
                continue#下一
            io['err'](f'rm: {操作数}: No such file or directory\n')#诊断
            状态=1#失败
            continue#下一路径
        if 统计['directory'] and not 递归:#目录且非递归
            io['err'](f'rm: {操作数}: Is a directory\n')#诊断
            状态=1#失败
            continue#下一路径
        try:#尝试移除
            fs['remove'](路径,{'recursive':递归,'force':强制})#移除
        except Exception as 错误:#失败
            io['err'](f'{描述失败("rm",操作数,错误)}\n')#诊断
            状态=1#失败
    return 状态#返回状态

def 复制树(源,目标,fs):#复制树
    """复制一个文件或一整棵子树。"""
    统计=fs['stat'](源)#源统计
    if 统计 is None or 统计['directory'] is not True:#文件
        fs['writeText'](目标,fs['readText'](源))#复制内容
        return#结束
    fs['mkdir'](目标,True)#建目标目录
    for 条目 in fs['list'](源):#递归复制
        复制树(解析路径(源,条目['name']),解析路径(目标,条目['name']),fs)#递归

def 解析目标(目标,源,fs):#解析目标
    """解析复制或移动的真实目标：进入目录，或落到路径上。"""
    统计=fs['stat'](目标)#查询目标
    return 解析路径(目标,基名(源)) if 统计 is not None and 统计['directory'] is True else 目标#进目录或原路径

def cp程序(argv,io,state,fs):#cp程序
    """复制。"""
    选项=解析选项(argv)#解析选项
    源们=选项['operands'][:-1]#源列表
    目标=选项['operands'][-1] if len(选项['operands'])>0 else None#目标
    if 目标 is None or len(源们)==0:#参数不足
        io['err']('cp: expected a source and a destination\n')#诊断
        return 2#用法错
    目标路径=在目录解析(state['cwd'],目标)#目标绝对路径
    状态=0#累积状态
    for 源 in 源们:#逐源
        源路径=在目录解析(state['cwd'],源)#源绝对路径
        统计=fs['stat'](源路径)#查询源
        if 统计 is None:#不存在
            io['err'](f'cp: {源}: No such file or directory\n')#诊断
            状态=1#失败
            continue#下一源
        if 统计['directory'] and not ('r' in 选项['flags'] or 'R' in 选项['flags']):#目录未递归
            io['err'](f'cp: {源}: Is a directory\n')#诊断
            状态=1#失败
            continue#下一源
        try:#尝试复制
            复制树(源路径,解析目标(目标路径,源,fs),fs)#复制
        except Exception as 错误:#失败
            io['err'](f'{描述失败("cp",源,错误)}\n')#诊断
            状态=1#失败
    return 状态#返回状态

def mv程序(argv,io,state,fs):#mv程序
    """移动。"""
    选项=解析选项(argv)#解析选项
    源们=选项['operands'][:-1]#源列表
    目标=选项['operands'][-1] if len(选项['operands'])>0 else None#目标
    if 目标 is None or len(源们)==0:#参数不足
        io['err']('mv: expected a source and a destination\n')#诊断
        return 2#用法错
    目标路径=在目录解析(state['cwd'],目标)#目标绝对路径
    状态=0#累积状态
    for 源 in 源们:#逐源
        try:#尝试移动
            fs['rename'](在目录解析(state['cwd'],源),解析目标(目标路径,源,fs))#重命名
        except Exception as 错误:#失败
            io['err'](f'{描述失败("mv",源,错误)}\n')#诊断
            状态=1#失败
    return 状态#返回状态

def touch程序(argv,io,state,fs):#touch程序
    """更新时间戳。"""
    选项=解析选项(argv)#解析选项
    状态=0#累积状态
    for 操作数 in 选项['operands']:#逐路径
        路径=在目录解析(state['cwd'],操作数)#绝对路径
        try:#尝试更新
            # 重写已有字节是推进 VFS 时间戳的方式。
            内容='' if fs['stat'](路径) is None else fs['readText'](路径)#空或读回
            fs['writeText'](路径,内容)#写回或建空
        except Exception as 错误:#失败
            io['err'](f'{描述失败("touch",操作数,错误)}\n')#诊断
            状态=1#失败
    return 状态#返回状态

def stat程序(argv,io,state,fs):#stat程序
    """打印统计。"""
    选项=解析选项(argv)#解析选项
    状态=0#累积状态
    for 操作数 in 选项['operands']:#逐路径
        路径=在目录解析(state['cwd'],操作数)#绝对路径
        统计=fs['stat'](路径)#查询
        if 统计 is None:#不存在
            io['err'](f'stat: {操作数}: No such file or directory\n')#诊断
            状态=1#失败
            continue#下一路径
        种类='directory' if 统计['directory'] else 'file'#种类
        时间=日期时间.fromtimestamp(统计['mtimeMs']/1000,时区.utc).isoformat().replace('+00:00','Z')#ISO
        io['out'](f"{路径} {种类} {统计['size']} {时间}\n")#打印事实
    return 状态#返回状态

def dirname程序(argv,io,state=None,fs=None):#dirname程序
    """打印目录名。"""
    for 操作数 in argv[1:]:#逐参
        io['out'](f'{目录名(操作数)}\n')#打印目录名
    return 0 if len(argv)>1 else 2#有参成功否则用法错

def basename程序(argv,io,state=None,fs=None):#basename程序
    """打印基名。"""
    路径=argv[1] if len(argv)>1 else None#路径
    后缀=argv[2] if len(argv)>2 else None#后缀
    if 路径 is None:#缺路径
        io['err']('basename: expected a path\n')#诊断
        return 2#用法错
    io['out'](f'{基名(路径,后缀)}\n')#打印基名
    return 0#成功

def 不可用(名):#不可用桩
    """拒绝 VFS 完全无法表示其效果的工具。"""
    def 程序(argv,io,state=None,fs=None):#程序体
        """报告不可用。"""
        io['err'](f'{名}: not available in the worker host\n')#诊断
        return 127#未找到
    return 程序#返回

文件程序={#文件程序表
    'ls':ls程序,#列表
    'find':find程序,#查找
    'mkdir':mkdir程序,#建目录
    'rmdir':rmdir程序,#删空目录
    'rm':rm程序,#删除
    'cp':cp程序,#复制
    'mv':mv程序,#移动
    'touch':touch程序,#更新时间戳
    'stat':stat程序,#统计
    'dirname':dirname程序,#目录名
    'basename':basename程序,#基名
    # 符号链接在 VFS 中无表示；拒绝是诚实的，并阻止脚本以为自己创建了一个。
    'ln':不可用('ln'),#拒绝ln
    'readlink':不可用('readlink'),#拒绝readlink
}#文件程序结束
