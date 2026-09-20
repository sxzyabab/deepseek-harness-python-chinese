from ....storage.路径 import dsh主目录,dsh临时

__all__=[
    'EOL','tmpdir','homedir','platform','type','arch','release','hostname',
    'availableParallelism','cpus','networkInterfaces','constants','__esModule','default',
]

EOL='\n'

def 临时目录():
    """返回 VFS 临时路径。"""
    return dsh临时

def 主目录():
    """返回 VFS 主目录。"""
    return dsh主目录

def 平台():
    """始终为 'linux'。"""
    return 'linux'

def 类型():
    """始终为 'Linux'。"""
    return 'Linux'

def 架构():
    """始终为 'x64'。"""
    return 'x64'

def 发行():
    """合成的发行字符串。"""
    return '0.0.0-dsh-worker'

def 主机名():
    """合成名称。"""
    return 'dsh-worker'

def 可用并行度():
    """浏览器硬件并发，至少为 1。"""
    导航=globals()['navigator'] if 'navigator' in globals() else None
    并发=getattr(导航,'hardwareConcurrency',1) if 导航 is not None else 1
    return max(1,并发)

def 列出处理器():
    """空列表（worker 内无逐核事实）。"""
    return []

def 网络接口():
    """空记录——worker webserver 绑定回环字面量。"""
    return {}

tmpdir=临时目录
homedir=主目录
platform=平台
type=类型
arch=架构
release=发行
hostname=主机名
availableParallelism=可用并行度
cpus=列出处理器
networkInterfaces=网络接口

constants={
    'signals':{
        'SIGHUP':1,'SIGINT':2,'SIGQUIT':3,'SIGILL':4,'SIGTRAP':5,'SIGABRT':6,'SIGBUS':7,'SIGFPE':8,
        'SIGKILL':9,'SIGUSR1':10,'SIGSEGV':11,'SIGUSR2':12,'SIGPIPE':13,'SIGALRM':14,'SIGTERM':15,
    },
    'errno':{},
    'priority':{},
}

__esModule=True
default={
    'EOL':EOL,'tmpdir':临时目录,'homedir':主目录,'platform':平台,'type':类型,
    'arch':架构,'release':发行,'hostname':主机名,'availableParallelism':可用并行度,
    'cpus':列出处理器,'networkInterfaces':网络接口,'constants':constants,
}
