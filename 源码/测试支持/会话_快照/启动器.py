"""ACP 测试共享启动器：经 JSON-RPC stdio 驱动智能体子进程。

对齐上游 `session-snapshot/src/launcher.ts`。公开面仅中文名。
"""
import json,os,tempfile,threading,subprocess,time,sys#进程与 IO
import yaml#YAML 补丁
from ..加载器_冒烟 import 解析示例启动#示例启动解析
from ...acp.acp import 协议版本#ACP 协议版本

__all__=['启动ACP测试智能体','物化配置档补丁']#仅中文公开名

退出标记宽限毫秒=250#退出标记宽限
Error=Exception#错误别名

def 仍在运行(子进程):#是否仍运行
    """子进程是否仍缺少任一 OS 终止标记。"""
    return 子进程.poll() is None#无退出码

def 等退出(子进程):#等退出
    """运行中子进程退出时返回。"""
    子进程.wait()#等 exit

def 宽限内已退出(子进程,超时秒):#宽限内是否退出
    """给已接受的终止请求一个有界窗口。"""
    截止=time.monotonic()+超时秒#截止
    while time.monotonic()<截止:#等待
        if not 仍在运行(子进程):#已退出
            return True#已退出
        time.sleep(0.01)#短睡
    return not 仍在运行(子进程)#最终检查

def 回放补丁路径(源):#回放补丁路径
    """推导仅回放兄弟补丁。"""
    基=os.path.basename(源)#基名
    回放名=基.replace('cordis.yml','cordis.snapshot.yml').replace('cordis.yaml','cordis.snapshot.yml')#回放名
    return os.path.join(os.path.dirname(源),回放名)#绝对路径

def 裸包名(说明符):#解析裸包名
    """把裸包或子路径说明符解析为包名。"""
    if 说明符.startswith('.') or 说明符.startswith('/') or ':' in 说明符:#非裸包
        return None#非裸包
    段=说明符.split('/')#拆段
    return f'{段[0]}/{段[1]}' if 说明符.startswith('@') and len(段)>=2 else 段[0]#作用域或普通

def 物化配置档补丁(源,工作目录,目标目录,索引):#物化配置补丁
    """把手写补丁拷进启动 cwd，并把相对插件名改成绝对。"""
    with open(源,'r',encoding='utf-8') as 句柄:#读补丁
        解析=yaml.safe_load(句柄.read())#解析 YAML
    if not isinstance(解析,list):#必须数组
        raise Error(f'snapshot profile patch must be a top-level array: {源}')#必须数组
    基目录=os.path.dirname(源)#基础目录
    def 解析名(值):#解析模块名
        """相对路径转 file URL；裸包保留。"""
        if 值.startswith('./') or 值.startswith('../'):#相对
            return 'file://'+os.path.abspath(os.path.join(基目录,值)).replace('\\','/')#绝对 file URL
        return 值#原样
    def 访问条目(条目):#访问条目
        """递归解析 name。"""
        if isinstance(条目,dict) and isinstance(条目.get('name'),str):#有名
            条目['name']=解析名(条目['name'])#解析名
            if 条目.get('group') is True and isinstance(条目.get('config'),list):#分组
                for 子 in 条目['config']:#递归
                    访问条目(子)#递归
    for 补丁 in 解析:#遍历补丁
        if isinstance(补丁,dict):#映射
            if isinstance(补丁.get('name'),str):#顶层名
                补丁['name']=解析名(补丁['name'])#解析
            for 条目 in 补丁.get('insert') or []:#插入项
                访问条目(条目)#访问
    目标=os.path.join(目标目录,f'{索引}-{os.path.basename(源)}')#目标路径
    with open(目标,'w',encoding='utf-8') as 句柄:#写出
        yaml.safe_dump(解析,句柄,allow_unicode=True,width=1000)#写出
    return 目标#返回路径

def 配置档参数(配置档,基础补丁,选定补丁,快照模式,工作目录):#构建配置档参数
    """从基础与可选场景补丁构建一次 dsh 配置档调用。"""
    基础=os.path.abspath(os.path.join(工作目录,基础补丁))#基础补丁
    选定=os.path.abspath(os.path.join(工作目录,选定补丁))#选定补丁
    补丁们=[基础,回放补丁路径(选定)] if 快照模式=='replay' else list(dict.fromkeys([基础,选定]))#补丁列表
    物化根=os.path.join(工作目录,'.dsh-profile-patches')#物化根
    os.makedirs(物化根,exist_ok=True)#确保根存在
    物化目录=tempfile.mkdtemp(prefix='launch-',dir=物化根)#物化目录
    物化=[物化配置档补丁(文件,工作目录,物化目录,索引) for 索引,文件 in enumerate(补丁们)]#物化各补丁
    参数=['--profile',配置档]#参数起点
    for 文件 in 物化:#逐补丁
        参数.extend(['--patch',文件])#追加
    return 参数#返回

def 启动ACP测试智能体(选项):#启动 ACP 测试智能体
    """启动 ACP 智能体子进程，并把 JSON-RPC 客户端接到其 stdio。"""
    智能体=选项['agent']#待测智能体
    工作目录=选项['cwd']#工作目录
    选定配置=选项.get('configPath') or 智能体['configPath']#选定配置
    配置参数=(#配置参数
        ['--config',选定配置] if 智能体.get('profile') is None
        else 配置档参数(智能体['profile'],智能体['configPath'],选定配置,(选项.get('env') or {}).get('DSH_SNAPSHOT'),工作目录)
    )#参数结束
    启动覆盖={'sourceImport':'tsx/esm'} if 智能体.get('profile') is not None else {}#esm 钩子
    启动=解析示例启动({#解析启动
        'srcBin':智能体['binScript'],#源 bin
        'libBin':智能体.get('libBinScript'),#可选 lib bin
        'configArgs':配置参数,#配置参数
        'tsconfigPath':智能体['tsconfigPath'],#tsconfig
        **启动覆盖,#可选钩子
        'env':{#环境
            **(选项.get('env') or {}),#调用方覆盖
            'DSH_HOME':os.path.join(工作目录,'.dsh'),#隔离 home
            'DSH_AGENTS_HOME':os.path.join(工作目录,'.agents'),#隔离 agents
        },#环境结束
    })#解析启动
    环境={**os.environ,**{键:值 for 键,值 in 启动['env'].items() if 值 is not None}}#合并环境
    子进程=subprocess.Popen(#spawn 子进程
        [启动['command'],*启动['args']],#命令行
        cwd=工作目录,#工作目录
        env=环境,#环境
        stdin=subprocess.PIPE,#stdin
        stdout=subprocess.PIPE,#stdout
        stderr=subprocess.PIPE,#stderr
        bufsize=0,#无缓冲
    )#spawn 结束
    标准错块=[]#stderr 块
    原始缓冲=[]#stdout 缓冲
    更新们=[]#更新列表
    更新等待者=[]#更新等待者
    更新流失败=[None]#更新流失败
    锁=threading.Lock()#共享锁
    下一标识=[1]#JSON-RPC id
    挂起={}#飞行中请求
    def 读标准错():#读 stderr
        """收集 stderr。"""
        while True:#循环
            块=子进程.stderr.read(4096) if 子进程.stderr else b''#读
            if not 块:#结束
                break#停
            标准错块.append(块.decode('utf-8',errors='replace'))#追加
    def 读标准出():#读 stdout
        """分流 stdout 到缓冲与 JSON-RPC。"""
        缓冲=b''#行缓冲
        while True:#循环
            块=子进程.stdout.read(4096) if 子进程.stdout else b''#读
            if not 块:#结束
                break#停
            原始缓冲.append(块)#记账
            缓冲+=块#追加
            while b'\n' in 缓冲:#按行
                行,缓冲=缓冲.split(b'\n',1)#拆行
                if 行.strip()==b'':#空
                    continue#跳过
                try:#解析帧
                    帧=json.loads(行.decode('utf-8'))#解析
                except Exception:#非法
                    continue#跳过
                with 锁:#串行
                    if 'id' in 帧 and 帧['id'] in 挂起:#响应
                        事件,盒=挂起.pop(帧['id'])#取等待
                        盒['frame']=帧#写入
                        事件.set()#放行
                    elif 帧.get('method')=='session/update':#会话更新
                        更新=帧.get('params',{}).get('update')#更新
                        更新们.append(更新)#记账
                        for 索引 in range(len(更新等待者)-1,-1,-1):#逆序匹配
                            等待=更新等待者[索引]#等待者
                            try:#匹配
                                命中=等待['match'](更新)#匹配
                            except Exception as 错误:#匹配抛错
                                更新等待者.pop(索引)#移除
                                等待['reject'](错误)#拒绝
                                continue#下一项
                            if 命中:#命中
                                更新等待者.pop(索引)#移除
                                等待['resolve'](更新)#兑现
                    elif 帧.get('method')=='session/request_permission':#权限请求
                        回调=选项.get('requestPermission') or (lambda _参数:{'outcome':{'outcome':'cancelled'}})#默认取消
                        应答=回调(帧.get('params') or {})#回调
                        响应={'jsonrpc':'2.0','id':帧.get('id'),'result':应答}#响应
                        子进程.stdin.write((json.dumps(响应,ensure_ascii=False)+'\n').encode('utf-8'))#写回
                        子进程.stdin.flush()#冲刷
        with 锁:#流关闭
            if 更新流失败[0] is None:#首次
                更新流失败[0]=Error('ACP test agent update stream closed before a matching session update arrived')#失败
                for 等待 in 更新等待者[:]:#拒绝等待者
                    等待['reject'](更新流失败[0])#拒绝
                更新等待者.clear()#清空
    threading.Thread(target=读标准错,daemon=True).start()#stderr 线程
    threading.Thread(target=读标准出,daemon=True).start()#stdout 线程
    def 请求(方法,参数):#JSON-RPC 请求
        """发请求并等响应。"""
        事件=threading.Event()#等待门闩
        盒={}#结果盒
        with 锁:#分配 id
            标识=下一标识[0]#id
            下一标识[0]+=1#推进
            挂起[标识]=(事件,盒)#登记
        帧={'jsonrpc':'2.0','id':标识,'method':方法,'params':参数}#请求帧
        子进程.stdin.write((json.dumps(帧,ensure_ascii=False)+'\n').encode('utf-8'))#写
        子进程.stdin.flush()#冲刷
        事件.wait()#等待
        响应=盒.get('frame') or {}#响应
        if 'error' in 响应:#错误
            raise Error(json.dumps(响应['error'],ensure_ascii=False))#拒绝
        return 响应.get('result')#结果
    def 通知(方法,参数):#JSON-RPC 通知
        """发通知。"""
        帧={'jsonrpc':'2.0','method':方法,'params':参数}#通知帧
        子进程.stdin.write((json.dumps(帧,ensure_ascii=False)+'\n').encode('utf-8'))#写
        子进程.stdin.flush()#冲刷
    客户端={#测试客户端
        'initialize':lambda 参数:请求('initialize',参数),#初始化
        'newSession':lambda 参数:请求('session/new',参数),#新建会话
        'listSessions':lambda 参数:请求('session/list',参数),#列会话
        'resumeSession':lambda 参数:请求('session/resume',参数),#恢复
        'closeSession':lambda 参数:请求('session/close',参数),#关闭会话
        'setSessionConfigOption':lambda 参数:请求('session/setConfigOption',参数),#设配置项
        'prompt':lambda 参数:请求('session/prompt',参数),#提示
        'cancel':lambda 参数:通知('session/cancel',参数),#取消
    }#客户端结束
    def 等更新(匹配):#等更新
        """未来某次会话更新匹配谓词时返回。"""
        if 更新流失败[0] is not None:#已失败
            raise 更新流失败[0]#拒绝
        事件=threading.Event()#门闩
        盒={}#结果
        def 兑现(更新):#兑现
            """写入并放行。"""
            盒['update']=更新#写入
            事件.set()#放行
        def 拒绝(原因):#拒绝
            """写入错误并放行。"""
            盒['error']=原因#写入
            事件.set()#放行
        with 锁:#登记
            for 已有 in 更新们:#先扫历史
                try:#匹配
                    if 匹配(已有):#命中
                        return 已有#返回
                except Exception as 错误:#匹配抛错
                    raise 错误#再抛
            更新等待者.append({'match':匹配,'resolve':兑现,'reject':拒绝})#登记
        事件.wait()#等待
        if 'error' in 盒:#失败
            raise 盒['error']#拒绝
        return 盒['update']#返回
    def 关闭(信号名=None):#关闭
        """关闭进程并排空流。"""
        if not 仍在运行(子进程):#已停
            return#结束
        if 信号名 is None:#优雅
            if 子进程.stdin:#关 stdin
                子进程.stdin.close()#关闭
        else:#信号
            子进程.send_signal(getattr(__import__('signal'),信号名,getattr(__import__('signal'),'SIGTERM')))#发信号
        if 宽限内已退出(子进程,退出标记宽限毫秒/1000):#已退出
            return#结束
        子进程.kill()#强制
        子进程.wait()#等
    return {#已启动句柄
        'child':子进程,#子进程
        'spawned':True,#spawn 完成
        'client':客户端,#客户端
        'updates':更新们,#更新列表
        'rawStdout':lambda:b''.join(原始缓冲).decode('utf-8',errors='replace'),#原始 stdout
        'stderr':lambda:''.join(标准错块),#stderr
        'waitForUpdate':等更新,#等更新
        'close':关闭,#关闭
        'protocolVersion':协议版本,#协议版本供步骤用
    }#句柄结束

launchAcpTestAgent=启动ACP测试智能体#上游名
materializeProfilePatch=物化配置档补丁#上游名
