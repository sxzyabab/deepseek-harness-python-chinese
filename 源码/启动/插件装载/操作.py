"""dsh plugin 与运行中装载服务共用的配置档包操作。"""
import os,re,json,tempfile,threading,subprocess
from ...工具.原子写入 import 带文件锁,原子写文件
from ...子进程.子进程 import 擦洗父环境
from ..app启动 import (
    默认组合包,
    初始化配置档,
    配置模板,
    读配置清单,
    解析组合包目录,
    解析配置目录,
    加载覆盖补丁,
)

__all__=[
    '锚定路径规格','组合包清单','保存清单','跑配置档pnpm','跑插件命令','查看配置档包',
]

相对路径规格=re.compile(r'^(?P<prefix>(?:file|link):)?(?P<path>\.{1,2}(?:[/\\].*)?)$')

def 锚定路径规格(参数,工作目录):
    """相对包规格锚定到调用方目录，从不相对配置档目录。"""
    匹配=相对路径规格.match(参数)
    if 匹配 is None or 匹配.group('path') is None:
        return 参数
    前缀=匹配.group('prefix') or ''
    return 前缀+os.path.abspath(os.path.join(工作目录,匹配.group('path')))

def 组合包清单(名称,目录,锚点):
    """读组合包元数据而不加载其 JavaScript；无组合包元数据则返回 None。"""
    包目录=解析组合包目录('dsh',名称,锚点,目录)
    清单=读配置清单('dsh',包目录)
    补丁=((清单.get('dsh') or {}).get('bundle') or {}).get('patch')
    return None if 补丁 is None else 清单

def 保存清单(目录,清单):
    """原子保存配置档清单并保留无关字段。"""
    文本=json_dumps_清单(清单)
    原子写文件(os.path.join(目录,'package.json'),文本,{'mode':0o600})

def json_dumps_清单(清单):
    """缩进两空格的 JSON 加换行。"""
    return json.dumps(清单,ensure_ascii=False,indent=2,allow_nan=False)+'\n'

def 调和(之前,目录,锚点,选项):
    """调和包删除与新装组合包，不重开保留依赖。"""
    之后=读配置清单('dsh',目录)
    依赖=list((之后.get('dependencies') or {}).keys())
    之前依赖=set((之前.get('dependencies') or {}).keys())
    先前=list(((之后.get('dsh') or {}).get('profile') or {}).get('bundles') or [])
    组合包=[]
    for 名称 in 先前:
        if 名称 not in 之前依赖 and 名称 not in 依赖:
            组合包.append(名称)
            continue
        if 名称 in 依赖 and 组合包清单(名称,目录,锚点) is not None:
            组合包.append(名称)
    for 名称 in 依赖:
        if 名称 in 之前依赖:
            continue
        元数据=组合包清单(名称,目录,锚点)
        if 元数据 is None or 'bundle' not in (元数据.get('dsh') or {}):
            回调=选项.get('onOutput')
            if 回调 is not None:
                回调('dsh: 警告: '+名称+' 未声明 dsh.bundle — 已作为普通依赖安装，不是配置档层\n','stderr')
            continue
        补丁=((元数据.get('dsh') or {}).get('bundle') or {}).get('patch')
        加载覆盖补丁('dsh',os.path.join(解析组合包目录('dsh',名称,锚点,目录),补丁))
        if 名称 not in 组合包:
            组合包.append(名称)
    if json.dumps(先前,ensure_ascii=False,separators=(',',':'),allow_nan=False)==json.dumps(组合包,ensure_ascii=False,separators=(',',':'),allow_nan=False):
        return
    dsh=dict(之后.get('dsh') or {})
    配置=dict(dsh.get('profile') or {})
    配置['bundles']=组合包
    dsh['profile']=配置
    之后=dict(之后)
    之后['dsh']=dsh
    保存清单(目录,之后)

def 收集流(流,种类,日志句柄,写出锁,状态,选项):
    """同步读子进程流并写入日志与有界输出。"""
    try:
        while True:
            块=流.read(4096)
            if not 块:
                break
            字节=块 if isinstance(块,(bytes,bytearray)) else 块.encode('utf-8')
            with 写出锁:
                日志句柄.write(字节)
                日志句柄.flush()
            回调=选项.get('onOutput')
            if 回调 is not None:
                回调(字节.decode('utf-8',errors='replace'),种类)
            with 写出锁:
                状态['output']=状态['output']+字节
                if len(状态['output'])>选项['outputBytes']:
                    状态['truncated']=True
                    状态['output']=状态['output'][-选项['outputBytes']:]
    except Exception:
        状态['streamError']=True
        raise

def 跑配置档pnpm(上下文,参数列表,选项):
    """在调用方已持有配置档写锁的前提下于配置档内执行 pnpm。"""
    目录=上下文['dir'] if 上下文.get('dir') is not None else 解析配置目录(上下文['profile'],上下文.get('home'))
    之前=读配置清单('dsh',目录)
    日志根=os.path.join(目录,'.plugin-manager','logs')
    os.makedirs(日志根,mode=0o700,exist_ok=True)
    日志目录=tempfile.mkdtemp(prefix='operation-',dir=日志根)
    日志路径=os.path.join(日志目录,'pnpm.log')
    日志句柄=open(日志路径,'xb')
    try:
        os.chmod(日志路径,0o600)
    except OSError:
        pass
    状态={'output':b'','truncated':False,'streamError':False}
    写出锁=threading.Lock()
    命令=选项.get('command') or 'pnpm'
    前缀=list(选项.get('args') or [])
    锚定=[锚定路径规格(项,上下文['cwd']) for 项 in 参数列表]
    环境=dict(os.environ) if 选项['execution']=='cli' else 擦洗父环境()
    if 选项.get('env') is not None:
        环境.update(选项['env'])
    标准输入=None if 选项['execution']=='cli' else subprocess.DEVNULL
    子进程=subprocess.Popen(
        [命令]+前缀+锚定,
        cwd=目录,
        env=环境,
        stdin=标准输入 if 选项['execution']!='cli' else None,
        stdout=None if 选项['execution']=='cli' else subprocess.PIPE,
        stderr=None if 选项['execution']=='cli' else subprocess.PIPE,
        bufsize=0,
    )
    信号=选项.get('signal')
    监视=None
    if 信号 is not None:
        def 监视中止():
            """信号置位则杀子进程。"""
            while 子进程.poll() is None:
                if 信号.is_set():
                    子进程.kill()
                    return
                threading.Event().wait(0.05)
        监视=threading.Thread(target=监视中止,daemon=True)
        监视.start()
    线程表=[]
    try:
        if 子进程.stdout is not None:
            出=threading.Thread(target=收集流,args=(子进程.stdout,'stdout',日志句柄,写出锁,状态,选项),daemon=True)
            出.start()
            线程表.append(出)
        if 子进程.stderr is not None:
            错=threading.Thread(target=收集流,args=(子进程.stderr,'stderr',日志句柄,写出锁,状态,选项),daemon=True)
            错.start()
            线程表.append(错)
        退出码=子进程.wait()
        for 线程 in 线程表:
            线程.join()
        if 退出码 is None:
            退出码=127 if False else 1
        if 退出码!=0 and len(状态['output'])==0:
            诊断='pnpm 失败'
            日志句柄.write(诊断.encode('utf-8'))
            状态['truncated']=len(诊断.encode('utf-8'))>选项['outputBytes']
            状态['output']=诊断.encode('utf-8')[:选项['outputBytes']]
        if 退出码==0 and 选项.get('activateNewBundles') is not False:
            调和(之前,目录,上下文['installAnchor'],选项)
    finally:
        日志句柄.close()
    return {
        'exitCode':退出码,
        'output':状态['output'].decode('utf-8',errors='replace'),
        'truncated':状态['truncated'],
        'logPath':日志路径,
    }

def 跑插件命令(上下文,参数列表,选项):
    """与服务共用写锁地初始化并跑 dsh plugin 命令。"""
    目录=上下文['dir'] if 上下文.get('dir') is not None else 解析配置目录(上下文['profile'],上下文.get('home'))
    os.makedirs(目录,exist_ok=True)
    def 持锁():
        """持锁体。"""
        if not os.path.exists(os.path.join(目录,'package.json')):
            模板=配置模板.get(上下文['profile'])
            初始化配置档(目录,(模板['bundles'] if 模板 is not None else 默认组合包))
            回调=选项.get('onOutput')
            if 回调 is not None:
                回调('dsh: 已初始化配置档 '+上下文['profile']+'\n','stderr')
        return 跑配置档pnpm(上下文,参数列表,选项)
    return 带文件锁(os.path.join(目录,'package.json'),持锁)

def 查看配置档包(目录,规格,选项):
    """经 pnpm view 询问注册表该规格指向什么；在配置档目录跑以继承注册表与代理。"""
    命令=选项.get('command') or 'pnpm'
    前缀=list(选项.get('args') or [])
    环境=擦洗父环境()
    if 选项.get('env') is not None:
        环境.update(选项['env'])
    超时秒=选项['timeoutMs']/1000.0
    信号=选项.get('signal')
    try:
        完成=subprocess.run(
            [命令]+前缀+['view',规格,'name','version','description','dsh','--json'],
            cwd=目录,
            env=环境,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=超时秒,
            check=False,
        )
        超时=False
        退出码=完成.returncode
        标准输出=完成.stdout or ''
        标准错误=完成.stderr or ''
        原因=None
    except FileNotFoundError as 错误:
        超时=False
        退出码=None
        标准输出=''
        标准错误=''
        原因=错误
        原因.code='ENOENT'
    except subprocess.TimeoutExpired:
        超时=True
        退出码=None
        标准输出=''
        标准错误=''
        原因=None
    结果={'exitCode':退出码,'stdout':标准输出,'stderr':标准错误,'timedOut':超时}
    if 原因 is not None:
        结果['cause']=原因
    if 信号 is not None and 信号.is_set():
        结果['exitCode']=None
    return 结果
