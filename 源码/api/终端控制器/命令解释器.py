'壳选择与可执行文件核验走目标执行提供方'

__all__=['解析命令解释器','发现命令解释器']#公开的两个探测


def 可执行名(路径):
    '取路径最后一段，斜杠与反斜杠都算分隔'
    斜杠=路径.rfind('/')#正斜杠
    反斜杠=路径.rfind('\\')#反斜杠
    return 路径[max(斜杠,反斜杠)+1:]#最后一段


def 壳种类(路径):
    '按可执行名归类，忽略大小写和 .exe'
    名称=可执行名(路径).lower()#小写文件名
    if 名称.endswith('.exe'):#去掉 Windows 后缀
        return 名称[:-4]#种类
    return 名称#种类


def 壳剖面(路径):
    'cmd 无参数，PowerShell 用 -NoLogo，其余用 -i'
    种类=壳种类(路径)#种类
    if 种类=='cmd':#命令提示符
        参数=[]#无参数
    elif 种类=='pwsh' or 种类=='powershell':#PowerShell
        参数=['-NoLogo']#不显示标志
    else:#其余交互壳
        参数=['-i']#交互
    return {'path':路径,'name':可执行名(路径),'args':参数}#剖面


def 解析命令解释器(子进程,已配置,信号):
    '解析已配置的壳，或执行环境的默认壳。声明了却解析不了则拒绝'
    壳=已配置#调用方剖面
    if 壳 is None:#没有剖面就问环境
        环境=子进程.终端环境(信号)#平台与默认壳
        默认壳=环境['defaultShell'] if 'defaultShell' in 环境 else None#提供方声明
        if 默认壳 is None:#提供方没声明
            if 环境['platform']=='windows':#Windows
                默认壳='cmd.exe'#回落
            else:#POSIX
                默认壳='/bin/sh'#回落
        壳=壳剖面(默认壳)#做成剖面
    路径=子进程.解析可执行文件(壳['path'],None,信号)#核验可执行文件
    结果=dict(壳)#拷贝剖面
    结果['path']=路径#换成解析后的路径
    return 结果#一个已核验的壳


def 发现命令解释器(子进程,已配置,候选,信号):
    '默认壳在前。同名只留最早一条，忽略大小写和 .exe。传输失败则拒绝'
    首选=解析命令解释器(子进程,已配置,信号)#配置或环境默认
    找到=[]#候选解析结果，没有的位置是 None
    for 一项 in 候选:#按给出的顺序
        try:#这一条解析失败时看是不是没找到
            找到.append(解析命令解释器(子进程,壳剖面(一项),信号))#已核验
        except Exception as 错误:#没找到就跳过，其余照抛
            if getattr(错误,'name',None)=='SubprocessExecutableNotFoundError':#确定没有这个可执行文件
                找到.append(None)#留空位
            else:#传输或别的失败
                raise#拒绝整次发现
    按种类={}#种类到最早的壳
    for 壳 in [首选,*找到]:#默认在前
        if 壳 is None:#这条候选没有
            continue#下一条
        种类=壳种类(壳['path'])#归类
        if 种类 not in 按种类:#只留最早
            按种类[种类]=壳#记下
    return list(按种类.values())#默认在前的列表
