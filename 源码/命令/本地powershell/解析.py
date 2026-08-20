"""PowerShell 可执行文件解析，无依赖。

对齐上游 `pwsh-local/src/resolve.ts`。公开面仅中文名；无英文别名。
无依赖是为了让非本包消费方与执行器共用同一份解析定义——探测若与被测代码解析得不一样，可能放过套件实际会跑的文件。
"""
import os,stat#路径拼接与不跟随链接的文件状态

__all__=('候选Pwsh路径','解析Pwsh路径')#仅中文公开名

def 取环境值(环境,键,缺省=None):#从环境映射或对象读键
    """从环境映射或对象读键，缺席则缺省。"""
    取值=getattr(环境,'get',None)#映射 get
    if callable(取值):#有 get（如 os.environ / dict）
        值=取值(键)#读取
        if 值 is None:#缺席
            return 缺省#用缺省
        return 值#命中
    值=getattr(环境,键,None)#对象属性
    if 值 is None:#缺席
        return 缺省#用缺省
    return 值#命中

def 候选Pwsh路径(环境=None):#列出候选路径
    """众所周知的 Windows PowerShell 安装位置加上 PATH 条目，新的在前。

    显式参数化环境，因此解析在每个平台上都是其输入的纯函数。
    """
    if 环境 is None:#未传入环境
        环境=os.environ#进程环境
    程序目录=取环境值(环境,'ProgramFiles','C:\\Program Files')#Program Files；缺省经典路径
    系统根=取环境值(环境,'SystemRoot','C:\\Windows')#系统根；缺省经典路径
    候选们=[os.path.join(程序目录,'PowerShell','7','pwsh.exe')]#先放 PowerShell 7 安装
    路径值=取环境值(环境,'PATH','')#PATH；Microsoft Store 等安装活在这里
    for 条目 in 路径值.split(';'):#拆 PATH（Windows 分号）
        整理=条目.strip()#去掉空白
        if 整理.startswith('"'):#setx 风格前导引号
            整理=整理[1:]#去掉前导引号
        if 整理.endswith('"'):#尾随引号
            整理=整理[:-1]#去掉尾随引号
        if len(整理)==0:#空条目
            continue#跳过
        候选们.append(os.path.join(整理,'pwsh.exe'))#PATH 上的 pwsh.exe
    候选们.append(os.path.join(系统根,'System32','WindowsPowerShell','v1.0','powershell.exe'))#5.1 遗留回退
    return 候选们#按解析顺序

def 候选存在(候选):#候选是否可 spawn
    """候选是否能被 spawn。

    lstat 打开条目本身而不跟随重解析点，因此能看见 Store 应用执行别名；真正的目录永不匹配。
    """
    try:#探测条目本身
        信息=os.lstat(候选)#不跟随重解析点
    except Exception:#吞掉 ENOENT 及任何使该路径不可 spawn 的探测错误
        return False#不可用
    模式=信息.st_mode#模式位
    return stat.S_ISREG(模式) or stat.S_ISLNK(模式)#文件或符号链接（含别名形态）

def 解析Pwsh路径(已配置=None,环境=None,平台=None):#解析 pwsh 路径
    """解析本执行器要 spawn 的 pwsh 可执行文件。

    显式配置原样信任。Windows 上取第一个存在的众所周知位置（PS7、PATH、再 5.1），否则 `pwsh` 交给 PATH 解析。
    """
    if 环境 is None:#未传入环境
        环境=os.environ#进程环境
    if 平台 is None:#未传入平台
        平台='win32' if os.name=='nt' else os.name#当前平台（nt → win32 字面量对齐上游）
    if 已配置 is not None and len(已配置)>0:#显式配置非空
        return 已配置#原样信任，不探测
    if 平台=='win32':#Windows 上按候选探测
        for 候选 in 候选Pwsh路径(环境):#逐候选
            if 候选存在(候选):#能 spawn
                return 候选#第一个能 spawn 的
    return 'pwsh'#非 Windows 或全未命中则交给 PATH
