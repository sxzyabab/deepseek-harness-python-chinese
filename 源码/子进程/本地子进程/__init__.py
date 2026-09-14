import atexit,os,threading#宿主退出收尾、路径解析与后台释放线程
import node_pty as 伪终端库#node-pty 的 Python 面；缺失则模块加载失败
from ...工具.超时 import 若已中止则抛出#中止入口；信号来自超时库
from .终端 import 本地子进程错误,本地终端句柄,贯通流#本包错误、PTY 句柄与输出流
from ..子进程 import 子进程运行时#子进程服务定义
from .启动 import 启动子进程,子环境,输出收集器#管道启动与收集
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
    '启动子进程','子环境','输出收集器',
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

def 拉起伪终端(程序,参数,选项):#分配本地 PTY
    """分配本地 PTY 会话。"""
    return 伪终端库.spawn(程序,list(参数),选项)#启动 PTY 进程

class 本地子进程运行时(子进程运行时):#本地子进程服务
    """本地子进程服务：分离进程树、stdio 处置（原始管道、继承、带溢出文件的有界保尾收集）、凭证擦洗环境、带 SIGTERM→宽限→SIGKILL 升级的树范围发信号，以及宿主退出期间的同步最终终止。

    公开方法仅中文：解析可执行文件、启动、启动终端。
    """
    def __init__(自身,上下文对象):#用 Cordis 上下文构造本地提供方
        """登记为 ctx.subprocess，并挂拆除与宿主退出收尾。"""
        super().__init__(上下文对象)#登记为 subprocess 服务
        自身.存活=set()#存活子进程句柄
        自身.终端表=set()#存活终端句柄
        自身.内部={}#spawn 测试钩子
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
        上下文对象.副作用(拆除,'local subprocess teardown')#登记拆除

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
        """先终止（升级），再等待整树退出。"""
        失败列表=[]#收集拒绝原因
        for 句柄 in list(自身.存活):#遍历存活子进程
            try:#开始升级终止
                句柄.终止()#TERM→KILL
            except (本地子进程错误,OSError) as 错误:#终止本身失败
                失败列表.append(错误)#记下
            try:#忽略 spawn 失败后再等整树
                句柄.done.等待()#等到孩子结局
            except (本地子进程错误,OSError):#spawn 级失败已结算
                pass#仍要等整树
            try:#等整树
                句柄.等待退出()#等整树
            except (本地子进程错误,OSError) as 错误:#等待失败
                失败列表.append(错误)#记下
        for 终端 in list(自身.终端表):#遍历存活终端
            try:#等待终端会话静止
                终端.终止().等待()#幂等拆除
            except (本地子进程错误,OSError) as 错误:#拆除失败
                失败列表.append(错误)#记下
        if len(失败列表)>0:#仍有失败则走宿主退出式强制停
            自身.为宿主退出终止()#强制停
        自身.存活.clear()#清空子进程集合
        自身.终端表.clear()#清空终端集合
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
                if os.name!='nt' and not os.access(候选,os.X_OK):#POSIX 需可执行
                    continue#试下一个
                若已中止则抛出(信号)#命中后再检查一次取消
                return 候选#返回命中路径
            except OSError:#这个候选不可用
                continue#试下一个 PATH 候选
        若已中止则抛出(信号)#报错前再检查取消
        if 绝对:#绝对路径不是可执行文件
            raise 本地子进程错误('subprocess-local: command '+repr(命令)+' is not an executable file')#稳定错误
        raise 本地子进程错误('subprocess-local: command '+repr(命令)+' was not found on PATH')#PATH 上找不到

    def 可执行候选(自身,命令,环境):#按 PATH/PATHEXT 展开候选路径
        """每个 PATH 目录拼出绝对候选。"""
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
                候选列表.append(os.path.abspath(os.path.join(目录,命令+扩展)))#拼出绝对候选
        return 候选列表#候选列表

    def 启动(自身,规格):#启动一个受管子进程
        """按规格 spawn，纳入存活集合；整树退出后释放所有权。规格是 dict。"""
        句柄=启动子进程(规格,自身.内部)#按规格 spawn
        自身.存活.add(句柄)#纳入存活集合
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
                句柄.done.等待()#等到孩子结局或拒绝
            except (本地子进程错误,OSError):#spawn 级失败已结算
                pass#仍释放
            释放()#等整树再删
        工作=threading.Thread(target=跟完成)#释放线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 句柄#返回存活句柄

    def 启动终端(自身,规格):#启动一个本地终端会话
        """经 PTY 后端分配终端会话；纳入存活集合。规格是 dict。"""
        参数表=list(规格['argv']) if 'argv' in 规格 and 规格['argv'] is not None else []#argv
        if len(参数表)==0 or 参数表[0] is None or len(str(参数表[0]))==0:#argv 没有程序
            raise 本地子进程错误('subprocess-local: terminal argv must contain a program')#终端必须有程序
        若已中止则抛出(规格['signal'] if 'signal' in 规格 else None)#分配前检查取消
        选项={#组装 PTY fork 选项
            'name':'dumb',#终端类型
            'rows':规格['rows'] if 'rows' in 规格 else None,#行数
            'cols':规格['cols'] if 'cols' in 规格 else None,#列数
            'cwd':规格['cwd'] if 'cwd' in 规格 else None,#工作目录
            'env':子环境(规格['env'] if 'env' in 规格 else None),#擦洗后叠加的环境
        }#结束 PTY 选项
        if 自身.终端检查器 is not None:#测试覆盖
            检查器=自身.终端检查器#覆盖
        else:#生产惰性创建
            检查器=创建进程检查器()#平台检查器
        终端=拉起伪终端(参数表[0],参数表[1:],选项)#启动 PTY 进程
        句柄=本地终端句柄(终端,检查器,规格['graceMs'])#包成本地终端句柄
        自身.终端表.add(句柄)#纳入存活终端集合
        def 释放():#终端结束后释放所有权
            """先确保会话静止，再从集合移除。"""
            try:#拆除
                句柄.终止().等待()#先确保会话静止
            except (本地子进程错误,OSError):#释放失败不再向外抛
                pass#吞掉
            自身.终端表.discard(句柄)#再从集合移除
        def 跟完成():#结算后释放
            """等 done 再释放。"""
            try:#done 可能拒绝
                句柄.done.等待()#等到退出
            except (本地子进程错误,OSError):#传输失败
                pass#仍释放
            释放()#释放所有权
        工作=threading.Thread(target=跟完成)#释放线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 句柄#返回存活终端句柄

default=本地子进程运行时#Cordis默认导出
