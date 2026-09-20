import atexit,os,threading#宿主退出收尾、路径解析与后台释放线程
from ...依赖 import node_pty as 伪终端库#node-pty 的 Python 面（依赖胶水，禁止顶层 import）
from ...工具.超时 import 若已中止则抛出#中止入口；信号来自超时库
from .命令活动 import 准备命令活动#shell 活动
from .终端 import 本地子进程错误,本地终端句柄,贯通流#本包错误、PTY 句柄与输出流
from ..子进程 import 子进程运行时,可执行未找到错误#子进程服务定义与查找失败
from .启动 import 启动子进程,子环境,输出收集器,准备受管进程绑定,节点平台#管道启动与收集
from .Linux范围 import (
    探测Linux管理器,#已引导后的廉价探测
    探测Linux原生,#首次引导+范围探测
    准备Linux终端范围,#终端 scope
    向Linux直接进程发信号,#直接进程信号
    直接范围,#终端绑定用直接面
    操作任务,#直接结算闩
)#Linux 受管范围
from .进程检查 import (
    进程身份,#精确身份
    创建进程检查器,#按平台选实现
    Posix进程检查器,#POSIX 基类
    Linux进程检查器,#Linux
    Mac进程检查器,#macOS
    组内有活成员,#组内存活探针
)#进程检查公开面

__all__=(#仅中文公开名；无英文别名
    '本地子进程运行时','本地子进程错误',
    '启动子进程','子环境','输出收集器','准备受管进程绑定',
    '进程身份','创建进程检查器','Posix进程检查器','Linux进程检查器','Mac进程检查器','组内有活成员',
    '本地终端句柄','贯通流',
)#公开面结束

def 环境键值(环境,键名):#按平台语义取 PATH/PATHEXT
    """用平台大小写不敏感语义读取一个 Windows 环境键。环境是 dict。"""
    if 环境 is None:#无环境
        return None#缺席
    if 键名 in 环境:#精确键
        return 环境[键名]#命中
    if os.name!='nt':#非 Windows 不再模糊
        return None#缺席
    规范=键名.upper()#规范化成大写
    for 键,值 in 环境.items():#大小写不敏感查找
        if str(键).upper()==规范:#命中
            return 值#返回
    return None#未命中

def 目标环境(规格):#物化并校验最终目标环境
    """空字节校验后叠控制通道标记。"""
    参数表=list(规格['argv']) if 'argv' in 规格 and 规格['argv'] is not None else []#argv
    for 下标,值 in enumerate(参数表):#逐参
        if '\0' in str(值):#空字节
            名='file' if 下标==0 else 'args['+str(下标-1)+']'#属性名
            raise TypeError("The argument '"+名+"' must be a string without null bytes. Received "+repr(值))#拒
    工作目录=规格['cwd'] if 'cwd' in 规格 else None#cwd
    if 工作目录 is not None and '\0' in str(工作目录):#cwd 空字节
        raise TypeError("The property 'options.cwd' must be a string without null bytes. Received "+repr(工作目录))#拒
    环境=子环境(规格['env'] if 'env' in 规格 else None)#擦洗后叠加
    for 键,值 in list(环境.items()):#逐条
        if '\0' in str(键) or (值 is not None and '\0' in str(值)):#键或值空字节
            raise TypeError("The property 'options.env["+repr(键)+"]' must be a string without null bytes.")#拒
    标准流=规格['stdio'] if 'stdio' in 规格 else None#可选 stdio
    控制=标准流['control'] if isinstance(标准流,dict) and 'control' in 标准流 else None#控制
    from .控制派生 import 控制环境#控制标记
    return 控制环境(环境,控制)#盖启动标记

def 拉起伪终端(程序,参数,选项):#分配本地 PTY
    """分配本地 PTY 会话。"""
    return 伪终端库.spawn(程序,list(参数),选项)#启动 PTY 进程

def 探测Windows作业(内部=None):#Windows Job 路径；本树未迁入 windows-job runner
    """本地无 Win32 Job runner 时恒为 False。"""
    return False#未迁入则不可用

class 本地子进程运行时(子进程运行时):#本地子进程服务
    """本地子进程服务：平台选定的受管范围、Node 形 stdio 处置（原始管道、继承、带溢出文件的有界保尾收集）、凭证擦洗环境，以及提供方拥有的范围发信号。POSIX 先 TERM 再 KILL；Windows 立即终止。JavaScript 可观察的宿主退出也会做同步最终终止。

    公开方法仅中文：解析可执行文件、终端环境、启动、启动终端。
    """
    def __init__(自身,上下文):#用 Cordis 上下文构造本地提供方
        """登记为子进程服务，并挂拆除与宿主退出收尾。"""
        super().__init__(上下文)#登记为 subprocess 服务
        自身.存活=set()#存活子进程句柄
        自身.终端表=set()#存活终端句柄
        自身.控制通道=set()#调用方控制端点
        自身.内部={}#spawn 测试钩子
        自身.回退警告已发=False#弱包含警告闩
        自身.Linux深探测已过=False#Linux 引导探测正缓存
        自身.终端检查器=None#可选终端检查器覆盖
        def 宿主退出时():#宿主退出时强制停树
            """同步强制停仍拥有的树与终端。"""
            自身.为宿主退出终止()#强制停
        atexit.register(宿主退出时)#进程退出前尽量跑
        def 拆除():#fiber 拆除时的清理
            """先正常销毁受管进程，再摘掉退出收尾。"""
            try:#先正常销毁
                自身.销毁受管进程()#终止并等待整树
            finally:#无论成败都摘掉 exit 收尾
                try:#atexit 可能已跑过
                    atexit.unregister(宿主退出时)#去掉宿主退出监听
                except ValueError:#unregister 失败
                    pass#宿主退出收尾最多再跑一次空操作
            return None#拆除完成
        上下文.副作用(拆除,'local subprocess teardown')#登记拆除

    def 为宿主退出终止(自身):#宿主退出路径上同步强制停树
        """遍历存活集合，分别包含每个目标的失败。"""
        for 句柄 in list(自身.存活):#遍历存活子进程
            try:#尝试强制终止一棵树
                句柄.为宿主退出终止()#同步强制停该树
            except (本地子进程错误,OSError):#单棵树终止失败
                pass#宿主退出不能等待或报告单个目标；继续处理其余
        for 终端 in list(自身.终端表):#遍历存活终端
            try:#尝试强制终止一个终端
                终端.为宿主退出终止()#同步强制停该终端
            except (本地子进程错误,OSError):#单终端终止失败
                pass#一个终端不得阻止对其余目标的最终终止

    def 销毁受管进程(自身):#正常销毁全部受管进程
        """先终止，再等待整棵受管范围退出；等待期间集合仍权威。"""
        失败列表=[]#收集拒绝原因
        for 句柄 in list(自身.存活):#遍历存活子进程
            try:#开始升级终止
                句柄.终止()#TERM→KILL
            except (本地子进程错误,OSError) as 错误:#终止本身失败
                失败列表.append(错误)#记下
            try:#忽略 spawn 失败后再等整树
                句柄.done.等待() if hasattr(句柄,'done') else 句柄.等待结局()#等到孩子结局
            except (本地子进程错误,OSError):#spawn 级失败已结算
                pass#仍要等整树
            try:#等整树
                句柄.等待退出()#等整树
            except (本地子进程错误,OSError) as 错误:#等待失败
                失败列表.append(错误)#记下
            自身.存活.discard(句柄)#范围走后释放所有权
        for 终端 in list(自身.终端表):#遍历存活终端
            try:#等待终端会话静止
                终端.终止()#幂等拆除
                自身.终端表.discard(终端)#静止后摘
            except (本地子进程错误,OSError) as 错误:#拆除失败
                失败列表.append(错误)#记下
        for 控制 in list(自身.控制通道):#关闭控制端点
            try:#尽力关闭
                控制.close()#关闭
            except OSError:#已关
                pass#吞掉
        自身.控制通道.clear()#清空控制通道
        if len(失败列表)>0:#仍有失败则走宿主退出式强制停
            自身.为宿主退出终止()#强制停
        if len(失败列表)==1:#单个失败原样抛出
            raise 失败列表[0]#原样
        if len(失败列表)>1:#多个失败
            raise 本地子进程错误('local subprocess teardown failed: '+'; '.join(str(项) for 项 in 失败列表))#聚合说明

    def 解析可执行文件(自身,命令,环境=None,信号=None):#在本机执行世界解析可执行文件
        """绝对路径核验；裸名按擦洗后 PATH 查找；带分隔符的相对路径拒绝。"""
        if 命令 is None or len(str(命令))==0:#空命令
            raise 本地子进程错误('subprocess-local: executable must be non-empty')#空命令直接失败
        若已中止则抛出(信号)#查找开始前检查取消
        查找环境=子环境(环境)#叠上擦洗后的子环境
        绝对=os.path.isabs(命令)#是否绝对路径
        if (not 绝对) and (('/' in 命令) or (os.name=='nt' and '\\' in 命令)):#带分隔符的相对路径
            raise 本地子进程错误('subprocess-local: command '+repr(命令)+' is a relative path; use an absolute path or a bare PATH name')#拒绝相对路径
        if 绝对:#绝对路径只试自己
            候选列表=[命令]#唯一候选
        else:#按 PATH 展开
            候选列表=自身.可执行候选(命令,查找环境)#PATH/PATHEXT
        for 候选 in 候选列表:#逐个候选试
            若已中止则抛出(信号)#每个候选前检查取消
            try:#检查是否为可执行文件
                if not os.path.isfile(候选):#不是文件
                    continue#试下一个
                if not os.access(候选,os.X_OK):#需可执行
                    continue#试下一个
                若已中止则抛出(信号)#命中后再检查一次取消
                return 候选#返回命中路径
            except OSError:#这个候选不可用
                continue#试下一个 PATH 候选
        若已中止则抛出(信号)#报错前再检查取消
        if 绝对:#绝对路径不是可执行文件
            raise 可执行未找到错误('subprocess-local: command '+repr(命令)+' is not an executable file')#稳定错误
        raise 可执行未找到错误('subprocess-local: command '+repr(命令)+' was not found on PATH')#PATH 上找不到

    def 可执行候选(自身,命令,环境):#按 PATH/PATHEXT 展开候选路径
        """每个 PATH 目录相对 cwd 拼出绝对候选。"""
        路径=环境键值(环境,'PATH')#取出 PATH
        if 路径 is None:#没有 PATH
            路径=''#空
        if os.name=='nt' and os.path.splitext(命令)[1]=='':#Windows 且命令无扩展名
            扩展串=环境键值(环境,'PATHEXT')#PATHEXT
            if 扩展串 is None:#缺省常见扩展
                扩展串='.COM;.EXE;.BAT;.CMD'#默认
            扩展列表=扩展串.split(';')#展开
        else:#其他平台不加扩展
            扩展列表=['']#空后缀
        分隔=os.pathsep#PATH 分隔
        候选列表=[]#结果
        for 目录 in 路径.split(分隔):#每个 PATH 目录
            for 扩展 in 扩展列表:#每个扩展
                候选列表.append(os.path.abspath(os.path.join(os.getcwd(),目录,命令+扩展)))#相对 cwd 绝对化
        return 候选列表#候选列表

    def 选择包含模式(自身,种类):#ordinary|terminal → linux-scope|windows-job|fallback
        """按平台选受管范围；不可用则回退。"""
        平台=自身.内部['platform'] if 'platform' in 自身.内部 and 自身.内部['platform'] is not None else 节点平台()#平台
        回退原因=None#可选原因
        if 平台=='linux':#Linux
            if 自身.Linux深探测已过:#已引导
                可用=探测Linux管理器(自身.内部)#廉价
            else:#首次
                可用=探测Linux原生(自身.内部)#深探测
            if 可用:#可用
                自身.Linux深探测已过=True#缓存正结果
                return 'linux-scope'#Linux scope
            回退原因='the current user-systemd scope or private bootstrap is unavailable'#原因
        if 种类=='ordinary' and 平台=='win32':#普通进程才试 Job
            if 探测Windows作业(自身.内部):#Job 可用
                return 'windows-job'#Job
        自身.警告回退(平台,种类,回退原因)#弱包含警告
        return 'fallback'#回退

    def 警告回退(自身,平台,种类,选定原因=None):#弱包含警告只发一次
        """提供方生命周期内只警告一次。"""
        if 自身.回退警告已发:#已发
            return#空操作
        自身.回退警告已发=True#闩上
        if 选定原因 is not None:#已有原因
            原因=选定原因#用选定
        elif 平台=='darwin':#macOS
            原因='macOS has no supported persistent process-range owner'#mac
        elif 平台=='win32':#Windows
            if 种类=='terminal':#终端
                原因='Windows ConPTY remains outside Job containment'#ConPTY
            else:#普通
                原因='the Win32 Job runner is unavailable'#Job
        else:#其它
            原因='platform '+str(平台)+' has no native managed range'#平台
        日志=getattr(自身.ctx,'logger',None) if hasattr(自身,'ctx') else None#日志
        文案='subprocess-local is using weaker process-tree containment because '+原因+'; descendants that escape the process group or direct-parent tree are not guaranteed to terminate or delay waitForExit()'#警告
        if 日志 is not None and hasattr(日志,'warn'):#有 warn
            日志.warn(文案)#打日志
        else:#无 logger
            print(文案)#打印

    def 终端环境(自身,信号=None):#查看壳选择事实
        """查看本机执行环境里的壳选择事实。"""
        若已中止则抛出(信号)#取消
        if os.name=='nt':#Windows
            平台='windows'#Windows 族
            壳=os.environ['ComSpec'] if 'ComSpec' in os.environ else None#ComSpec
        else:#POSIX
            平台='posix'#POSIX 族
            if 'SHELL' in os.environ:#环境壳
                壳=os.environ['SHELL']#SHELL
            else:#口令库登录壳
                import pwd as 口令#登录数据库
                壳=口令.getpwuid(os.getuid()).pw_shell#登录壳
        结果={'platform':平台}#平台
        if 壳 is not None and len(壳)>0:#有壳
            结果['defaultShell']=壳#默认壳
        return 结果#环境事实

    def 启动(自身,规格):#启动一个受管子进程
        """按规格 spawn，纳入存活集合；整树退出后释放所有权。规格是 dict。"""
        自身.选择包含模式('ordinary')#探测并可能警告；普通路径本地仍走回退 spawn
        句柄=启动子进程(规格,自身.内部)#按规格 spawn（绑定受管进程未迁入前恒回退）
        自身.存活.add(句柄)#纳入存活集合
        控制=句柄.control#控制通道
        if 控制 is not None:#请求了控制通道
            自身.控制通道.add(控制)#纳入集合
            def 控制关闭(*位置参数):#close 后摘
                """控制端关闭后从集合移除。"""
                自身.控制通道.discard(控制)#摘
            if hasattr(控制,'once'):#有 once
                控制.once('close',控制关闭)#听 close
            elif hasattr(控制,'监听'):#中文贯通
                控制.一次('close',控制关闭)#听 close
        def 释放():#整树退出后从集合移除
            """等整树再释放。"""
            try:#等待可能因取消返回 False
                句柄.等待退出()#等整树
            except (本地子进程错误,OSError):#等待失败仍释放所有权
                pass#释放
            自身.存活.discard(句柄)#移除
        def 跟完成():#无论 spawn 成败都安排释放
            """先等 done，再释放。"""
            try:#spawn 失败会拒绝
                if hasattr(句柄,'done'):#有 done
                    句柄.done.等待()#等到孩子结局或拒绝
                else:#中文
                    句柄.等待结局()#等到孩子结局
            except (本地子进程错误,OSError):#spawn 级失败已结算
                pass#仍释放
            释放()#等整树再删
        工作=threading.Thread(target=跟完成)#释放线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 句柄#返回存活句柄

    def 启动终端(自身,规格):#启动一个本地终端会话
        """经 PTY 后端分配终端会话；Linux 可用时走 scope。规格是 dict。"""
        参数表=list(规格['argv']) if 'argv' in 规格 and 规格['argv'] is not None else []#argv
        if len(参数表)==0 or 参数表[0] is None or len(str(参数表[0]))==0:#argv 没有程序
            raise 本地子进程错误('subprocess-local: terminal argv must contain a program')#终端必须有程序
        若已中止则抛出(规格['signal'] if 'signal' in 规格 else None)#分配前检查取消
        if 自身.终端检查器 is not None:#测试覆盖
            检查器=自身.终端检查器#覆盖
        else:#生产惰性创建
            检查器=创建进程检查器()#平台检查器
        包含模式=自身.选择包含模式('terminal')#包含模式
        环境=目标环境(规格)#物化目标环境
        平台=自身.内部['platform'] if 'platform' in 自身.内部 and 自身.内部['platform'] is not None else 节点平台()#平台
        活动=准备命令活动(规格,环境,平台)#可选 shell 活动
        启动规格=dict(规格)#拷贝
        if 活动 is not None:#改 argv/env
            启动规格['argv']=活动.参数表#活动 argv
            启动规格['env']=活动.环境#活动环境
        启动环境=活动.环境 if 活动 is not None else 环境#环境
        类型=规格['terminalType']#经 TERM 广告的仿真
        选项={#组装 PTY fork 选项
            'name':类型,#终端类型
            'rows':规格['rows'] if 'rows' in 规格 else None,#行数
            'cols':规格['cols'] if 'cols' in 规格 else None,#列数
            'cwd':规格['cwd'] if 'cwd' in 规格 else None,#工作目录
            'env':dict(启动环境,TERM=类型),#擦洗后叠加的环境
        }#结束 PTY 选项
        范围=None#Linux 终端 scope
        try:#启动
            if 包含模式=='linux-scope':#Linux scope
                范围环境=dict(启动环境)#拷贝
                if 'cwd' in 规格:#有 cwd
                    范围环境['PWD']=规格['cwd']#PWD
                范围环境['TERM']=类型#TERM
                范围=准备Linux终端范围(启动规格,范围环境,自身.内部)#准备
                选项['cwd']=范围.cwd#scope cwd
                选项['env']=范围.env#scope env
                终端=拉起伪终端(范围.command,范围.args,选项)#经 systemd-run
            else:#回退
                启动参数=参数表 if 活动 is None else list(活动.参数表)#argv
                终端=拉起伪终端(启动参数[0],启动参数[1:],选项)#直接 PTY
        except Exception:#失败
            if 范围 is not None:#有范围
                范围.清理()#清理启动文件
            if 活动 is not None:#有活动
                活动.拆除()#清理
            raise#原样
        句柄盒={'句柄':None}#所有者可在句柄发布前查 running
        直接结算=操作任务()#直接退出闩
        所有者=None#可选所有者
        结算结局=None#可选结局改写
        if 范围 is not None:#绑所有者
            def 是否在跑():#句柄是否仍运行
                """句柄未发布前当仍运行。"""
                句=句柄盒['句柄']#当前
                return True if 句 is None else 句.运行中#在跑
            def 发直接信号(信号):#向直接进程发信号
                """node-pty 吞信号错误；scope 需要投递结果。"""
                import signal as 信号模块#信号常量
                return 向Linux直接进程发信号(终端.pid,lambda:os.kill(终端.pid,getattr(信号模块,信号)))#投递
            所有者=范围.绑定所有者(直接范围(是否在跑,发直接信号,直接结算))#绑
            结算结局=范围.结算结局#改写
        def 静止摘表():#静止后摘
            """从存活集合移除。"""
            自身.终端表.discard(句柄盒['句柄'])#摘
        句柄=本地终端句柄(#包成本地终端句柄
            终端,检查器,规格['graceMs'],平台,所有者,结算结局,活动,静止摘表,规格.get('shellActivity') is True,
        )#构造结束
        句柄盒['句柄']=句柄#发布
        自身.终端表.add(句柄)#纳入存活终端集合
        def 释放():#终端结束后释放所有权
            """先确保会话静止，再从集合移除。"""
            直接结算.兑现()#兑现直接结算
            if 规格.get('shellActivity') is True:#shell 活动由客户端回收
                return#不 terminate
            try:#拆除
                句柄.终止()#先确保会话静止
            except (本地子进程错误,OSError):#释放失败不再向外抛
                pass#吞掉
            自身.终端表.discard(句柄)#再从集合移除
        def 跟完成():#结算后释放
            """等 done 再释放。"""
            try:#done 可能拒绝
                句柄.等待结局()#等到退出
            except (本地子进程错误,OSError):#传输失败
                pass#仍释放
            释放()#释放所有权
        工作=threading.Thread(target=跟完成)#释放线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 句柄#返回存活终端句柄

default=本地子进程运行时#框架槽
