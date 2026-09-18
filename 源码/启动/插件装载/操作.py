"""dsh plugin 与运行中装载服务共用的配置档包操作。"""
import os,re,json,tempfile,threading,subprocess#路径、锚定、JSON、临时日志、流收集、子进程
from ...工具.原子写入 import 带文件锁,原子写文件#清单锁与原子写
from ...子进程.子进程 import 擦洗父环境#清理后的父环境
from ..app启动 import (#配置档操作
    默认组合包,#默认组合包
    初始化配置档,#初始化
    配置模板,#模板
    读配置清单,#读清单
    解析组合包目录,#解析组合包目录
    解析配置目录,#解析配置目录
    加载覆盖补丁,#加载覆盖
)#导入结束

__all__=[#仅中文公开名
    '锚定路径规格','组合包清单','保存清单','跑配置档pnpm','跑插件命令','查看配置档包',
]#公开面结束

相对路径规格=re.compile(r'^(?P<prefix>(?:file|link):)?(?P<path>\.{1,2}(?:[/\\].*)?)$')#相对规格

def 锚定路径规格(参数,工作目录):
    """相对包规格锚定到调用方目录，从不相对配置档目录。"""
    匹配=相对路径规格.match(参数)#试匹配
    if 匹配 is None or 匹配.group('path') is None:#非相对
        return 参数#原样
    前缀=匹配.group('prefix') or ''#可选前缀
    return 前缀+os.path.abspath(os.path.join(工作目录,匹配.group('path')))#锚定

def 组合包清单(名称,目录,锚点):
    """读组合包元数据而不加载其 JavaScript；无组合包元数据则返回 None。"""
    包目录=解析组合包目录('dsh',名称,锚点,目录)#包目录
    清单=读配置清单('dsh',包目录)#清单
    补丁=((清单.get('dsh') or {}).get('bundle') or {}).get('patch')#补丁路径
    return None if 补丁 is None else 清单#有补丁才算组合包

def 保存清单(目录,清单):
    """原子保存配置档清单并保留无关字段。"""
    文本=json_dumps_清单(清单)#格式化 JSON
    原子写文件(os.path.join(目录,'package.json'),文本,{'mode':0o600})#原子写

def json_dumps_清单(清单):
    """与上游 JSON.stringify(manifest, undefined, 2)+'\\n' 对齐。"""
    return json.dumps(清单,ensure_ascii=False,indent=2,allow_nan=False)+'\n'#缩进两空格

def 调和(之前,目录,锚点,选项):
    """调和包删除与新装组合包，不重开保留依赖。"""
    之后=读配置清单('dsh',目录)#装后清单
    依赖=list((之后.get('dependencies') or {}).keys())#依赖名
    之前依赖=set((之前.get('dependencies') or {}).keys())#装前依赖
    先前=list(((之后.get('dsh') or {}).get('profile') or {}).get('bundles') or [])#先前组合包
    组合包=[]#调和后列表
    for 名称 in 先前:#过滤先前
        if 名称 not in 之前依赖 and 名称 not in 依赖:#幽灵名保留
            组合包.append(名称)#保留
            continue#下一项
        if 名称 in 依赖 and 组合包清单(名称,目录,锚点) is not None:#仍是组合包
            组合包.append(名称)#保留
    for 名称 in 依赖:#新依赖
        if 名称 in 之前依赖:#旧有
            continue#跳过
        元数据=组合包清单(名称,目录,锚点)#元数据
        if 元数据 is None or (元数据.get('dsh') or {}).get('bundle') is None:#非组合包
            回调=选项.get('onOutput')#输出回调
            if 回调 is not None:#有回调
                回调('dsh: warning: '+名称+' declares no dsh.bundle — installed as a plain dependency, not a profile layer\n','stderr')#警告
            continue#跳过
        补丁=((元数据.get('dsh') or {}).get('bundle') or {}).get('patch')#补丁相对路径
        加载覆盖补丁('dsh',os.path.join(解析组合包目录('dsh',名称,锚点,目录),补丁))#加载覆盖
        if 名称 not in 组合包:#未选入
            组合包.append(名称)#追加
    if json.dumps(先前,ensure_ascii=False,separators=(',',':'),allow_nan=False)==json.dumps(组合包,ensure_ascii=False,separators=(',',':'),allow_nan=False):#同序同值
        return#无写
    dsh=dict(之后.get('dsh') or {})#dsh
    配置=dict(dsh.get('profile') or {})#profile
    配置['bundles']=组合包#写回
    dsh['profile']=配置#写回
    之后=dict(之后)#拷贝
    之后['dsh']=dsh#写回
    保存清单(目录,之后)#保存

def 收集流(流,种类,日志句柄,写出锁,状态,选项):
    """同步读子进程流并写入日志与有界输出。"""
    try:#读
        while True:#直到 EOF
            块=流.read(4096)#读一块
            if not 块:#EOF
                break#结束
            字节=块 if isinstance(块,(bytes,bytearray)) else 块.encode('utf-8')#统一字节
            with 写出锁:#串行写日志
                日志句柄.write(字节)#写日志
                日志句柄.flush()#刷盘
            回调=选项.get('onOutput')#输出回调
            if 回调 is not None:#有回调
                回调(字节.decode('utf-8',errors='replace'),种类)#转发文本
            with 写出锁:#更新有界缓冲
                状态['output']=状态['output']+字节#追加
                if len(状态['output'])>选项['outputBytes']:#超限
                    状态['truncated']=True#截断
                    状态['output']=状态['output'][-选项['outputBytes']:]#保留尾部
    except Exception:#读失败
        状态['streamError']=True#标记
        raise#原样

def 跑配置档pnpm(上下文,参数列表,选项):
    """在调用方已持有配置档写锁的前提下于配置档内执行 pnpm。"""
    目录=上下文['dir'] if 上下文.get('dir') is not None else 解析配置目录(上下文['profile'],上下文.get('home'))#配置档目录
    之前=读配置清单('dsh',目录)#装前清单
    日志根=os.path.join(目录,'.plugin-manager','logs')#日志根
    os.makedirs(日志根,mode=0o700,exist_ok=True)#确保
    日志目录=tempfile.mkdtemp(prefix='operation-',dir=日志根)#一次操作目录
    日志路径=os.path.join(日志目录,'pnpm.log')#日志文件
    日志句柄=open(日志路径,'xb')#独占创建
    try:#设权限
        os.chmod(日志路径,0o600)#仅所有者
    except OSError:#部分平台忽略
        pass#继续
    状态={'output':b'','truncated':False,'streamError':False}#输出状态
    写出锁=threading.Lock()#写锁
    命令=选项.get('command') or 'pnpm'#可执行
    前缀=list(选项.get('args') or [])#前缀参数
    锚定=[锚定路径规格(项,上下文['cwd']) for 项 in 参数列表]#锚定参数
    环境=dict(os.environ) if 选项['execution']=='cli' else 擦洗父环境()#基环境
    if 选项.get('env') is not None:#应用环境
        环境.update(选项['env'])#合并
    标准输入=None if 选项['execution']=='cli' else subprocess.DEVNULL#stdin
    子进程=subprocess.Popen(#启动 pnpm
        [命令]+前缀+锚定,#argv
        cwd=目录,#工作目录
        env=环境,#环境
        stdin=标准输入 if 选项['execution']!='cli' else None,#stdin
        stdout=None if 选项['execution']=='cli' else subprocess.PIPE,#stdout
        stderr=None if 选项['execution']=='cli' else subprocess.PIPE,#stderr
        bufsize=0,#无缓冲
    )#Popen 结束
    信号=选项.get('signal')#中止信号
    监视=None#监视线程
    if 信号 is not None:#有中止
        def 监视中止():
            """信号置位则杀子进程。"""
            while 子进程.poll() is None:#仍在跑
                if hasattr(信号,'已中止') and 信号.已中止():#本包信号
                    子进程.kill()#杀掉
                    return#结束
                if hasattr(信号,'is_set') and 信号.is_set():#Event
                    子进程.kill()#杀掉
                    return#结束
                信号.wait(0.05) if hasattr(信号,'wait') else threading.Event().wait(0.05)#短等
        监视=threading.Thread(target=监视中止,daemon=True)#守护
        监视.start()#启动
    线程表=[]#收集线程
    try:#收集输出
        if 子进程.stdout is not None:#有 stdout
            出=threading.Thread(target=收集流,args=(子进程.stdout,'stdout',日志句柄,写出锁,状态,选项),daemon=True)#线程
            出.start()#启动
            线程表.append(出)#登记
        if 子进程.stderr is not None:#有 stderr
            错=threading.Thread(target=收集流,args=(子进程.stderr,'stderr',日志句柄,写出锁,状态,选项),daemon=True)#线程
            错.start()#启动
            线程表.append(错)#登记
        退出码=子进程.wait()#等结束
        for 线程 in 线程表:#等收集
            线程.join()#汇合
        if 退出码 is None:#无码
            退出码=127 if False else 1#失败
        if 退出码!=0 and len(状态['output'])==0:#失败且无输出
            诊断='pnpm failed'#短诊断
            日志句柄.write(诊断.encode('utf-8'))#写日志
            状态['truncated']=len(诊断.encode('utf-8'))>选项['outputBytes']#是否截断
            状态['output']=诊断.encode('utf-8')[:选项['outputBytes']]#有界
        if 退出码==0 and 选项.get('activateNewBundles') is not False:#成功且要激活
            调和(之前,目录,上下文['installAnchor'],选项)#调和
    finally:#关日志
        日志句柄.close()#关闭
    return {#包结果
        'exitCode':退出码,#退出码
        'output':状态['output'].decode('utf-8',errors='replace'),#输出文本
        'truncated':状态['truncated'],#是否截断
        'logPath':日志路径,#日志路径
    }#结果结束

def 跑插件命令(上下文,参数列表,选项):
    """与服务共用写锁地初始化并跑 dsh plugin 命令。"""
    目录=上下文['dir'] if 上下文.get('dir') is not None else 解析配置目录(上下文['profile'],上下文.get('home'))#目录
    os.makedirs(目录,exist_ok=True)#确保
    def 持锁():
        """持锁体。"""
        if not os.path.exists(os.path.join(目录,'package.json')):#未初始化
            模板=配置模板.get(上下文['profile'])#模板
            初始化配置档(目录,(模板['bundles'] if 模板 is not None else 默认组合包))#初始化
            回调=选项.get('onOutput')#输出
            if 回调 is not None:#有回调
                回调('dsh: initialized profile '+上下文['profile']+' at '+目录+'\n','stderr')#通知
        return 跑配置档pnpm(上下文,参数列表,选项)#跑 pnpm
    return 带文件锁(os.path.join(目录,'package.json'),持锁)#持锁

def 查看配置档包(目录,规格,选项):
    """经 pnpm view 询问注册表该规格指向什么；在配置档目录跑以继承注册表与代理。"""
    命令=选项.get('command') or 'pnpm'#可执行
    前缀=list(选项.get('args') or [])#前缀
    环境=擦洗父环境()#擦洗
    if 选项.get('env') is not None:#应用环境
        环境.update(选项['env'])#合并
    超时秒=选项['timeoutMs']/1000.0#超时秒
    信号=选项.get('signal')#中止
    try:#跑 view
        完成=subprocess.run(#同步跑
            [命令]+前缀+['view',规格,'name','version','description','dsh','--json'],#argv
            cwd=目录,#工作目录
            env=环境,#环境
            stdin=subprocess.DEVNULL,#忽略 stdin
            capture_output=True,#捕获
            text=True,#文本
            timeout=超时秒,#超时
            check=False,#不抛
        )#run 结束
        超时=False#未超时
        退出码=完成.returncode#退出码
        标准输出=完成.stdout or ''#stdout
        标准错误=完成.stderr or ''#stderr
        原因=None#启动失败
    except FileNotFoundError as 错误:#可执行缺失
        超时=False#非超时
        退出码=None#无码
        标准输出=''#空
        标准错误=''#空
        原因=错误#原因
        原因.code='ENOENT'#对齐 Node
    except subprocess.TimeoutExpired:#超时
        超时=True#超时
        退出码=None#无码
        标准输出=''#空
        标准错误=''#空
        原因=None#无启动失败
    结果={'exitCode':退出码,'stdout':标准输出,'stderr':标准错误,'timedOut':超时}#基结果
    if 原因 is not None:#有原因
        结果['cause']=原因#挂上
    if 信号 is not None and ((hasattr(信号,'已中止') and 信号.已中止()) or (hasattr(信号,'is_set') and 信号.is_set())):#已中止
        结果['exitCode']=None#无码
    return 结果#查看结果
