'需要凭据或没有匿名单文件接口的仓库，用深度 1、不含文件内容的裸克隆'
import os,re,time,signal,hashlib,shutil,tempfile,subprocess,threading#路径、诊断、时限、进程、摘要、线程
import urllib.request,urllib.error#不带凭据的探测
from ...工具.原子写入 import 带文件锁#跨进程锁
from ...工具.插件详情 import 详情失败,自述文件名#失败与 README 名
from ...子进程.子进程 import 擦洗父环境#去掉凭证形态和 DSH_
from ...内核.智能体循环.中止与并发 import 中止控制器,已中止,若已中止则抛出#寿命与本次读取
from ...基础设施.通用工具.线程工具 import 启动守护线程#大小监视与淘汰
from .异常 import 文件过大#超限文件不删克隆

__all__=['仓库缓存']#仅中文公开名

操作命令数=4#一次操作最多这么条会联系远端的 Git 命令
暂存前缀='.init-'#初始化中的目录；更旧的是被停掉的进程留下的
网络失败=re.compile('Could not resolve host|Failed to connect|Connection (?:refused|reset)|timed out|Network is unreachable|SSL|TLS',re.IGNORECASE)#连接失败或超时，不是服务器拒绝

def 目录大小(路径):
    '目录里普通文件的字节合计'
    合计=0#字节
    for 当前,目录名表,文件名表 in os.walk(路径):#递归
        for 文件名 in 文件名表:#每个文件
            文件路径=os.path.join(当前,文件名)#路径
            try:#可能正被删
                合计+=os.path.getsize(文件路径)#大小
            except FileNotFoundError:#测量途中被删掉
                continue#这一项不计
    return 合计#合计

def 删除树(路径):
    '删掉目录。已经不存在则什么也不做'
    if os.path.lexists(路径):#还在
        shutil.rmtree(路径)#递归删

def git环境():
    '每条 Git 命令的环境：擦洗后的父环境，去掉 GIT_ 覆盖，不提示、不下载 LFS'
    环境={}#新环境
    for 名,值 in 擦洗父环境().items():#父环境
        if 名.startswith('GIT_') and 名!='GIT_SSH' and 名!='GIT_SSH_COMMAND':#钩子留下的覆盖
            continue#丢掉
        环境[名]=值#留下
    if 'GIT_SSH' not in 环境 and 'GIT_SSH_COMMAND' not in 环境:#用户没指定 ssh
        环境['GIT_SSH_COMMAND']='ssh -o BatchMode=yes'#不交互
    环境.update({#固定项
        'LC_ALL':'C',#诊断语言
        'GIT_TERMINAL_PROMPT':'0',#不提示
        'GIT_ASKPASS':'',#不弹窗
        'SSH_ASKPASS':'',#不弹窗
        'SSH_ASKPASS_REQUIRE':'never',#不要求
        'GCM_INTERACTIVE':'never',#凭据管理器不交互
        'GIT_LFS_SKIP_SMUDGE':'1',#不下载 LFS
        'GIT_LITERAL_PATHSPECS':'1',#路径按字面
    })#固定项结束
    return 环境#环境

def 结束进程(进程):
    '停掉 Git 及其子进程'
    if 进程.poll() is not None:#已经结束
        return#不用
    if os.name=='nt':#Windows
        进程.kill()#结束
        return#完
    try:#进程组
        os.killpg(进程.pid,signal.SIGKILL)#整组
    except OSError:#组已经没了
        进程.kill()#只结束这一条

def 远端失败(结果,标签):
    '联系远端的 Git 失败：超时或连接失败是 network，其余是 denied'
    原因='network' if 网络失败.search(结果['diagnostic']) is not None else 'denied'#种类
    return 详情失败(原因,标签+': '+结果['diagnostic'])#失败

class 仓库缓存:
    '一个服务拥有的详情仓库部分克隆'
    def __init__(自身,选项):
        '记下目录、上限、时限、传输和寿命'
        自身.目录=选项['目录']#克隆根
        自身.单库上限=选项['单库上限']#一条命令最多增加的字节
        自身.缓存上限=选项['缓存上限']#全部克隆上限
        自身.超时毫秒=选项['超时毫秒']#一条 Git 命令的时限
        自身.存活毫秒=选项['存活毫秒']#默认分支提交与匿名可达的复用时长
        自身.传输=list(选项['传输'])#允许的 Git 传输
        自身.寿命=选项['寿命']#服务中止
        自身.轮询毫秒=选项['轮询毫秒']#取回时量目录的间隔
        自身.表锁=threading.Lock()#锁表与可见性
        自身.目录锁={}#仓库目录到线程锁
        自身.头={}#网址到默认分支提交
        自身.git能启动=False#git --version 已成功
        自身.可见={}#网址到是否匿名可达
        自身.检查中={}#同一网址的探测共用一次
        自身.运行中=set()#还没结束的操作

    def 是否公开(自身,网址):
        '智能 HTTP 端点是否不带凭据就回答。2xx 为真；401、403、404 和重定向为假'
        现在=int(time.time()*1000)#现在
        缓存=自身.可见.get(网址)#已有
        if 缓存 is not None and 缓存['expiresAt']>现在:#未过期
            return 缓存['value']#复用
        with 自身.表锁:#共用一次
            进行=自身.检查中.get(网址)#已有
            if 进行 is None:#本调用负责
                进行={'事件':threading.Event(),'盒子':{}}#盒子
                自身.检查中[网址]=进行#登记
                负责=True#负责
            else:#等待
                负责=False#不负责
        if not 负责:#等那一次
            进行['事件'].wait()#阻塞
            if '错误' in 进行['盒子']:#失败
                raise 进行['盒子']['错误']#再抛
            return 进行['盒子']['值']#结果
        try:#探测
            公开=自身.探测(网址)#问端点
            进行['盒子']['值']=公开#交给等待者
            return 公开#结果
        except Exception as 错误:#失败
            进行['盒子']['错误']=错误#交给等待者
            raise#再抛
        finally:#摘掉
            进行['事件'].set()#放开
            with 自身.表锁:#摘
                if 自身.检查中.get(网址) is 进行:#仍是这一次
                    del 自身.检查中[网址]#摘掉

    def 探测(自身,网址):
        '不带用户配置、凭据助手和 netrc，问 info/refs'
        端点=网址+'/info/refs?service=git-upload-pack'#智能 HTTP
        若已中止则抛出(自身.寿命)#已拆
        请求=构造请求(端点)#GET
        try:#发出
            响应=不跟随打开(请求,自身.超时毫秒/1000)#不跟随重定向
        except Exception as 错误:#到不了
            raise 详情失败('network','Could not reach '+端点+': '+str(错误))#网络
        try:#只看状态
            状态=响应.status if getattr(响应,'status',None) is not None else 响应.code#状态码
            成功=200<=状态<=299#2xx
        finally:#关掉正文
            响应.close()#不读正文
        if not 成功 and 状态 not in (401,403,404) and not (300<=状态<=399):#其它状态
            raise 详情失败('network',端点+' answered HTTP '+str(状态))#网络
        自身.可见[网址]={'value':成功,'expiresAt':int(time.time()*1000)+自身.存活毫秒}#缓存
        return 成功#是否公开

    def 读取(自身,网址,提交,路径,最大字节,信号):
        '读仓库里的一个普通文件。提交缺省为默认分支。没有该文件则返回 None'
        def 操作(仓库):
            '在锁里读'
            已解析=自身.提交(仓库,网址,提交,信号)#提交
            文件表=自身.文件表(仓库,已解析,路径,信号)#该路径
            对象=文件表.get(路径)#blob
            if 对象 is None:#不是普通文件
                return None#没有
            return 自身.对象(仓库,网址,对象,路径,最大字节,信号)#内容
        return 自身.加锁(网址,操作)#串行

    def 读自述(自身,网址,提交,目录,最大字节,信号):
        '读目录里的 README.md、README.markdown 或 README，大小写不限'
        def 操作(仓库):
            '在锁里读'
            已解析=自身.提交(仓库,网址,提交,信号)#提交
            前缀='' if 目录=='' else 目录+'/'#目录前缀
            列举=None if 目录=='' else 前缀#根则列全部直接子项
            文件表=自身.文件表(仓库,已解析,列举,信号)#文件
            名字=自述文件名([路径[len(前缀):] for 路径 in 文件表 if 路径.startswith(前缀)])#README 名
            if 名字 is None:#没有
                return None#没有
            路径=前缀+名字#完整路径
            return {'path':路径,'bytes':自身.对象(仓库,网址,文件表[路径],路径,最大字节,信号)}#文件
        return 自身.加锁(网址,操作)#串行

    def 等结束(自身):
        '等到每条还在跑的 Git 命令结束。寿命信号会停掉它们'
        for 事件 in list(自身.运行中):#拷贝
            事件.wait()#等这一条

    def 取目录锁(自身,仓库):
        '同一仓库目录的进程内锁'
        with 自身.表锁:#建锁
            锁=自身.目录锁.get(仓库)#已有
            if 锁 is None:#新建
                锁=threading.Lock()#锁
                自身.目录锁[仓库]=锁#记下
            return 锁#锁

    def 加锁(自身,网址,操作):
        '同一仓库串行。除文件超过本次读取上限外，失败或取消都删掉克隆'
        仓库=os.path.join(自身.目录,hashlib.sha256(网址.encode('utf-8')).hexdigest()[:24])#按网址摘要命名

        def 跑():
            '操作失败则删仓库'
            try:#操作
                return 操作(仓库)#结果
            except 文件过大:#文件超限，克隆仍可用
                raise#再抛
            except Exception:#其它失败或取消
                删除树(仓库)#删掉损坏的克隆
                raise#再抛

        return 自身.串行(仓库,跑)#跨进程也串行

    def 串行(自身,仓库,操作):
        '本进程和共用缓存目录的其它进程都排完后才跑'
        锁=自身.取目录锁(仓库)#进程内
        完成=threading.Event()#给等结束
        自身.运行中.add(完成)#登记
        锁.acquire()#排在本仓库已有操作之后
        try:#持锁
            os.makedirs(自身.目录,exist_ok=True)#缓存根
            等待毫秒=操作命令数*自身.超时毫秒#文件锁等待
            return 带文件锁(仓库,操作,{'waitMs':等待毫秒})#跨进程
        finally:#放开
            锁.release()#下一条可进
            完成.set()#已结束
            自身.运行中.discard(完成)#摘掉

    def 提交(自身,仓库,网址,提交,信号):
        '要读的提交。必要时取回该提交或默认分支'
        if not 自身.git能启动:#先确认 Git 能启动
            try:#版本一行就够
                自身.运行(自身.目录,['--version'],信号,1024)#短输出
            except Exception as 错误:#不能启动
                raise 详情失败('git-unavailable',str(错误))#不是仓库拒绝
            自身.git能启动=True#之后不再查
        if not os.path.exists(仓库):#还没有克隆
            暂存=tempfile.mkdtemp(prefix=暂存前缀,dir=自身.目录)#旁边初始化
            try:#初始化完再改名
                自身.运行(暂存,['init','--quiet','--bare','--template='],信号)#空模板
                for 键,值 in (('remote.origin.url',网址),('remote.origin.promisor','true'),('remote.origin.partialclonefilter','blob:none')):#部分克隆
                    自身.运行(暂存,['config',键,值],信号)#配置
                os.rename(暂存,仓库)#完整后才出现
            finally:#暂存还在就删
                if os.path.exists(暂存):#改名失败或中途失败
                    删除树(暂存)#不留半截
        现在=time.time()#访问时间
        os.utime(仓库,(现在,现在))#最近使用
        已有头=自身.头.get(网址)#缓存的默认分支
        if 提交 is not None:#指定提交
            已知=提交#该提交
        elif 已有头 is not None and 已有头['expiresAt']>int(time.time()*1000):#默认分支仍有效
            已知=已有头['value']#复用
        else:#需要取回
            已知=None#未知
        if 已知 is not None and not 自身.运行git(['show-ref','--verify','--quiet','refs/dsh/'+已知],仓库,信号)['failed']:#本地已有
            return 已知#不用再取
        自身.取回(仓库,网址,提交 if 提交 is not None else 'HEAD',信号)#取回
        if 提交 is not None:#指定的就是结果
            已取=提交#原样
        else:#默认分支在 FETCH_HEAD
            已取=自身.运行(仓库,['rev-parse','FETCH_HEAD'],信号).decode('utf-8').strip()#提交
        自身.运行(仓库,['update-ref','refs/dsh/'+已取,已取],信号)#记下，避免无大小监视的惰性取回
        if 提交 is None:#默认分支
            自身.头[网址]={'value':已取,'expiresAt':int(time.time()*1000)+自身.存活毫秒}#缓存
        return 已取#提交

    def 取回(自身,仓库,网址,目标,信号):
        '取回一个提交，不带文件内容，然后按总上限淘汰'
        参数=['fetch','--quiet','--depth','1','--filter=blob:none','--no-tags','origin',目标]#部分取回
        自身.监视(仓库,网址,参数,信号,网址+': git fetch')#带大小监视
        自身.淘汰(仓库)#总量

    def 监视(自身,仓库,网址,参数,信号,标签,最大缓冲=None):
        '可能下载对象的命令。增长超过单库上限则停掉，调用方的锁再删仓库'
        if 最大缓冲 is None:#默认按仓库上限截断输出
            最大缓冲=自身.单库上限#输出上限
        之前=目录大小(仓库)#命令前
        过大=中止控制器()#真的超过单库上限
        停止监视=threading.Event()#命令结束就让轮询退出，这不是超限

        def 轮询():
            '间隔量目录'
            while not 停止监视.is_set() and not 已中止(过大.信号):#还没停
                try:#量
                    大小=目录大小(仓库)#现在
                except OSError:#测量途中目录被改
                    大小=None#这次跳过
                if 大小 is not None and 大小-之前>自身.单库上限:#超限
                    过大.中止()#停 Git
                    return#结束监视
                if 停止监视.wait(自身.轮询毫秒/1000):#等到间隔或命令已结束
                    return#停

        启动守护线程(轮询)#后台量
        try:#跑命令
            结果=自身.运行git(参数,仓库,信号,过大.信号,最大缓冲)#Git
        finally:#停监视
            停止监视.set()#轮询退出
        if 已中止(过大.信号) or (not 结果['failed'] and 目录大小(仓库)-之前>自身.单库上限):#超限
            raise 详情失败('too-large',网址+': one fetch adds more than '+str(自身.单库上限)+' bytes')#太大
        if 结果['failed'] and not 结果['overflowed']:#命令失败且不是输出被截断
            raise 远端失败(结果,标签)#网络或拒绝
        return 结果#输出

    def 淘汰(自身,保留):
        '删到总量以内。正在用的仓库最后删，而且只排队不等待'
        现在毫秒数=int(time.time()*1000)#现在
        条目表=[]#可淘汰目录
        try:#列目录
            名字表=os.listdir(自身.目录)#名字
        except FileNotFoundError:#缓存根还没有
            return#不用淘汰
        for 名字 in 名字表:#逐个
            路径=os.path.join(自身.目录,名字)#路径
            try:#测量
                状态=os.stat(路径)#时间与种类
            except FileNotFoundError:#测量时被删
                continue#不计
            if 名字.startswith(暂存前缀):#暂存
                if 现在毫秒数-状态.st_mtime*1000>自身.超时毫秒:#超过一条 Git 命令的时限
                    删除树(路径)#删旧暂存
            elif os.path.isdir(路径):#克隆
                条目表.append({'path':路径,'size':目录大小(路径),'used':状态.st_mtime})#记下
        合计=sum(条目['size'] for 条目 in 条目表)#总量

        def 排序键(条目):
            '正在用的放最后，其余按最近使用从旧到新'
            return (1 if 条目['path']==保留 else 0,条目['used'])#键

        for 条目 in sorted(条目表,key=排序键):#从旧到新
            if 合计<=自身.缓存上限:#已经放下
                return#停
            自身.后台删除(条目['path'])#排到该仓库自己的操作后面
            合计-=条目['size']#先按测量值减

    def 后台删除(自身,路径):
        '不等待的删除。调用方可能正持有另一仓库的锁'
        def 跑():
            '串行删'
            def 删除():
                '强制递归删。删不掉就留到下次再量'
                try:#删
                    删除树(路径)#删
                except OSError:#权限等
                    return#留下
            自身.串行(路径,删除)#排在该仓库的操作后
        启动守护线程(跑)#不等

    def 文件表(自身,仓库,提交,路径,信号):
        '树路径下的直接普通文件，或该路径上的文件，带 blob 标识。列树不下载文件内容'
        参数=['ls-tree','-z',提交]#列树
        if 路径 is not None:#限定路径
            参数.extend(['--',路径])#路径
        列表=自身.运行(仓库,参数,信号).decode('utf-8')#以 NUL 分隔
        文件={}#路径到 blob
        for 行 in 列表.split('\0'):#每一行
            匹配=re.match(r'^100(?:644|755) blob ([0-9a-f]+)\t(.+)$',行)#普通文件；链接、子模块和树不是
            if 匹配 is not None:#是文件
                文件[匹配.group(2)]=匹配.group(1)#记下
        return 文件#表

    def 对象(自身,仓库,网址,对象标识,路径,最大字节,信号):
        '读 blob。克隆里还没有内容时在仓库大小上限内下载'
        结果=自身.监视(仓库,网址,['cat-file','blob',对象标识],信号,'git cat-file '+路径,最大字节)#截断在上限
        if 结果['overflowed']:#超过本次读取
            raise 文件过大(路径,最大字节)#不删克隆
        自身.淘汰(仓库)#下载后也卡总量
        return 结果['stdout']#字节

    def 运行(自身,仓库,参数,信号,最大缓冲=None):
        '跑一条只碰本地对象的 Git。失败是普通错误，不表示仓库拒绝'
        结果=自身.运行git(参数,仓库,信号,None,最大缓冲)#本地
        if 结果['failed']:#失败
            首段=参数[0] if len(参数)>0 else ''#子命令
            raise RuntimeError('git '+首段+': '+结果['diagnostic'])#不缓存
        return 结果['stdout']#输出

    def 运行git(自身,参数,工作目录,信号,停止=None,最大缓冲=None):
        '禁止仓库自带程序，并且只允许配置的传输。停止信号让 Git 以失败结果结束'
        if 最大缓冲 is None:#默认
            最大缓冲=自身.单库上限#输出上限
        安全=[]#每次命令的 -c
        设置表=[#不跑仓库提供的程序
            'core.askPass=','core.hooksPath=/dev/null','core.fsmonitor=false','submodule.recurse=false',
            'gc.auto=0','maintenance.auto=false','protocol.allow=never',
        ]#设置结束
        for 传输 in 自身.传输:#允许的传输
            设置表.append('protocol.'+传输+'.allow=always')#放开这一种
        for 设置 in 设置表:#逐条
            安全.extend(['-c',设置])#成对
        信号表=[信号,自身.寿命]#调用方与寿命
        if 停止 is not None:#大小超限
            信号表.append(停止)#也停
        try:#启动
            进程=subprocess.Popen(#不继承额外环境
                ['git',*安全,*参数],#参数
                cwd=工作目录,#仓库
                env=git环境(),#擦洗后的环境
                stdin=subprocess.DEVNULL,#不读标准输入
                stdout=subprocess.PIPE,#保留末尾换行
                stderr=subprocess.PIPE,#诊断
                start_new_session=(os.name!='nt'),#非 Windows 才能整组停
            )#进程
        except FileNotFoundError as 错误:#没有 git
            return {'stdout':b'','failed':True,'overflowed':False,'diagnostic':str(错误)}#当失败结果
        输出=bytearray()#标准输出
        错误输出=bytearray()#标准错误
        溢出={'是':False}#输出超过上限
        输出完=threading.Event()#读完标准输出
        错误完=threading.Event()#读完标准错误

        def 读输出():
            '读到上限就停 Git'
            while True:#逐块
                输出块=进程.stdout.read(65536)#一块
                if not 输出块:#结束
                    break#停
                输出.extend(输出块)#留下
                if len(输出)>最大缓冲:#超过
                    溢出['是']=True#标记
                    结束进程(进程)#停
                    break#不再读
            输出完.set()#完

        def 读错误():
            '标准错误也有上限，避免堵住管道'
            while True:#逐块
                错误块=进程.stderr.read(65536)#一块
                if not 错误块:#结束
                    break#停
                if len(错误输出)+len(错误块)>自身.单库上限:#太大
                    结束进程(进程)#停
                    break#不再读
                错误输出.extend(错误块)#留下
            错误完.set()#完

        threading.Thread(target=读输出,daemon=True).start()#读输出
        threading.Thread(target=读错误,daemon=True).start()#读错误
        截止=time.monotonic()+自身.超时毫秒/1000.0#时限
        超时了=False#是否超时
        while 进程.poll() is None:#还在跑
            if time.monotonic()>=截止:#到时
                超时了=True#标记
                结束进程(进程)#停
                break#不再等
            if any(已中止(一项) for 一项 in 信号表):#中止
                结束进程(进程)#停
                break#不再等
            time.sleep(0.05)#短等
        进程.wait()#收尸
        输出完.wait(2)#给读线程一点时间
        错误完.wait(2)#标准错误
        若已中止则抛出(信号)#调用方中止优先于结果
        若已中止则抛出(自身.寿命)#服务已拆
        返回码=进程.returncode#退出码
        if 超时了:#时限
            简述='timed out'#诊断
        elif 返回码 not in (0,None):#失败退出
            简述='Command failed with exit code '+str(返回码)#诊断
        elif 返回码 is None:#被停掉且没有码
            简述='killed'#诊断
        else:#成功
            简述=''#无
        错误文本=bytes(错误输出).decode('utf-8','replace').strip()#错误输出
        诊断=(简述+'\n'+错误文本).strip()#合成
        return {#结果
            'stdout':bytes(输出),#原样字节
            'failed':返回码 not in (0,) or 超时了,#非零或超时
            'overflowed':溢出['是'] and len(输出)>=最大缓冲,#输出被截断
            'diagnostic':诊断,#诊断
        }#结果结束

class 重定向处理(urllib.request.HTTPRedirectHandler):
    '把重定向留在这一次响应里，不继续请求'
    def redirect_request(自身,请求对象,响应,状态码,消息,响应头,新网址):
        '不发出下一次请求'
        return None#让上层看见 3xx

def 构造请求(网址):
    '不带凭据的 GET'
    return urllib.request.Request(网址,method='GET')#请求

def 不跟随打开(请求,超时秒):
    '3xx 作为响应交回'
    开启器=urllib.request.build_opener(重定向处理)#只这一次
    try:#打开
        return 开启器.open(请求,timeout=超时秒)#2xx
    except urllib.error.HTTPError as 错误:#含不跟随的 3xx
        return 错误#带状态的响应
