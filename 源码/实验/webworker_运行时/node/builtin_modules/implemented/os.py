"""worker 侧的 `node:os`：每个值指向 VFS 或报告主机树所建的固定平台身份
（`linux`，一颗 CPU）。值为真实而非抛错，因为若干 `[Service.init]` 体在
构造期间会读取它们。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/os.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
from ....storage.路径 import dsh主目录,dsh临时#VFS路径常量

__all__=[#中文公开名与Node英文挂名
    '临时目录','主目录','平台','类型','架构','发行','主机名','可用并行度','处理器们','网络接口',
    'EOL','tmpdir','homedir','platform','type','arch','release','hostname',
    'availableParallelism','cpus','networkInterfaces','constants','__esModule','default',
]#公开结束

EOL='\n'#行尾

def 临时目录():#临时目录
    """返回 VFS 临时路径。"""
    return dsh临时#VFS临时根

def 主目录():#主目录
    """返回 VFS 内的 `$DSH_HOME`。"""
    return dsh主目录#VFS家目录

def 平台():#平台
    """始终为 'linux'。"""
    return 'linux'#固定linux

def 类型():#系统类型
    """始终为 'Linux'。"""
    return 'Linux'#固定Linux

def 架构():#架构
    """始终为 'x64'。"""
    return 'x64'#固定x64

def 发行():#发行版
    """合成的发行字符串。"""
    return '0.0.0-dsh-worker'#合成版本

def 主机名():#主机名
    """合成名称。"""
    return 'dsh-worker'#合成名

def 可用并行度():#并行度
    """浏览器硬件并发，至少为 1。"""
    导航=globals().get('navigator')#navigator
    并发=getattr(导航,'hardwareConcurrency',1) if 导航 is not None else 1#并发度
    return max(1,并发)#至少1

def 处理器们():#CPU列表
    """空列表（worker 内无逐核事实）。"""
    return []#无逐核信息

def 网络接口():#网卡表
    """空记录——worker webserver 绑定回环字面量。"""
    return {}#空记录

tmpdir=临时目录#Node面
homedir=主目录#Node面
platform=平台#Node面
type=类型#Node面
arch=架构#Node面
release=发行#Node面
hostname=主机名#Node面
availableParallelism=可用并行度#Node面
cpus=处理器们#Node面
networkInterfaces=网络接口#Node面

constants={#OS常量
    'signals':{#信号表
        'SIGHUP':1,'SIGINT':2,'SIGQUIT':3,'SIGILL':4,'SIGTRAP':5,'SIGABRT':6,'SIGBUS':7,'SIGFPE':8,#信号1-8
        'SIGKILL':9,'SIGUSR1':10,'SIGSEGV':11,'SIGUSR2':12,'SIGPIPE':13,'SIGALRM':14,'SIGTERM':15,#信号9-15
    },#signals结束
    'errno':{},#空errno
    'priority':{},#空priority
}#constants结束

__esModule=True#CJS互操作
default={#默认导出
    'EOL':EOL,'tmpdir':临时目录,'homedir':主目录,'platform':平台,'type':类型,#身份
    'arch':架构,'release':发行,'hostname':主机名,'availableParallelism':可用并行度,#续
    'cpus':处理器们,'networkInterfaces':网络接口,'constants':constants,#网络与常量
}#默认导出结束
