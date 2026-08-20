"""DeepSeek Harness 沙箱 seam 的 Windows ACL 写入限制沙箱后端。镜像 github.com/huoyaoyuan/windows-acl-restrict-poc @ 10e4dfb（钉死修订）的机制：一个 WRITE_RESTRICTED 令牌，其限制 SID 包含本沙箱加到其拥有目录 DACL 上的、彼此不同的工作区与临时写入 SID——交集检查于是恰好在任一能力有 Write ACE 的地方允许写入，就那些 SID 而言别无他处（该检查还继承其他限制 SID 的环境写入 ACE——保活组登录 SID + Everyone；Authenticated Users、INTERACTIVE 与 LOCAL 两份列表里都没有——完整边界见 sandbox_local 的 seam 双列表约定与本包 README 的 Modes 节）。写入 SID 是按工作区身份（workspaceWriteSid）：从规范工作区路径确定性推导，因此工作区根 ACE 在每台机器每个工作区只物化一次，每次后续供给都命中精确 ACE 跳过。每个私有临时目录改收自己的 SID，因此共享工作区的兄弟会话不能进入彼此的临时树。与 POC 不同，每次 API 失败都带 API 名与精确 Win32 码抛出；子进程永远不会未受限地被 spawn。

已知边界（受限令牌固有，不是本移植）：
 - 写入受限制；读取、网络与进程可见性不受限（WRITE_RESTRICTED 只交集写入访问）；
 - 控制台隔离不可用——子进程共享宿主控制台（CREATE_NO_WINDOW / CREATE_NEW_CONSOLE 子进程在该限制下以 STATUS_DLL_INIT_FAILED 死去）；
 - 私有临时目录与每个可写目录必须由调用方拥有（所有者隐式 WRITE_DAC）；
 - 授权是对真实目录的常驻 ACE 变更。工作区授权故意永不撤销——ACE 是跨会话复用缓存。临时授权可撤销：dispose() 去掉它们。环境临时根从不被隐式授予。manageDacls: false 时调用方拥有 DACL：init()/dispose() 完全跳过授予/撤销。
"""
import os#存在判定与路径

from .acl import 授予写入,撤销写入#授予与撤销写入ACE
from .错误 import Win32错误#Win32错误
from .ffi import 分配指针槽,解码指针,是否空指针,抛上次错误,解析绑定#指针槽、解码、空指针、错误抛出与绑定
from .路径边界 import 断言私有临时不相交,断言临时根在工作区外#私有临时不相交与临时根断言
from .spawn import 引用参数,排空管道,隔离生成,隔离继承生成,等待退出#引用、排空、隔离spawn与等待
from .令牌 import 创建受限令牌,查找登录SID,制作众所周知SID,打开当前进程令牌,设令牌默认DACL授予#受限令牌构造
from . import win32_abi as abi#Win32 ABI常量
from .工作区sid import 临时写入SID,工作区写入SID#SID推导
from .授权 import ACL写入授权,聚合错误#写入授权与聚合错误

def 尽力释放SID(接口,sid指针,标签,失败们):#尽力释放SID
    """释放一个可选 SID，同时为尽力的兄弟清理保留失败。"""
    if sid指针 is None:#没有指针
        return#跳过
    try:#LocalFree
        释放=接口.localFree(sid指针)#释放
        if not 是否空指针(释放):#非空则失败
            抛上次错误(接口,'LocalFree',标签)#抛出
    except BaseException as 错误:#释放失败
        失败们.append(错误)#记下

class ACL沙箱:#ACL沙箱实例
    """一个写入受限沙箱实例：令牌 + 写入 SID 授权 + spawn。init() 失败即关闭——任何 Win32 失败都撤销可撤销（临时）授权并抛出；dispose() 撤销临时授权，留下常驻工作区 ACE（跨实例复用缓存），释放每个分配，并报告每次清理失败。manageDacls: false 时调用方拥有授权：init() 不应用任何，dispose() 不撤销任何。"""
    def __init__(自身,选项):#校验并保存选项
        """校验并保存构造选项。"""
        自身.mode=选项['mode']#记下模式
        自身._manageDacls=选项.get('manageDacls',True)#默认自己管理DACL
        自身.writableDirs=[]#可写目录
        for 目录 in 选项['writableDirs']:#规范化可写目录
            绝对=os.path.abspath(目录)#绝对路径
            if not os.path.exists(绝对) or not os.path.isdir(绝对):#不存在或不是目录
                raise Exception('AclSandbox writable dir does not exist or is not a directory: '+绝对)#非法可写目录
            自身.writableDirs.append(绝对)#绝对路径
        自身._tempDirDefined='tempDir' in 选项#是否显式传入tempDir（含null）
        自身._tempDirOption=选项['tempDir'] if 自身._tempDirDefined else None#临时选项；未定义时为None哨兵
        自身.writeSid=选项.get('writeSid')#记下工作区SID
        自身.tempWriteSid=选项.get('tempWriteSid')#记下临时SID
        if 自身.mode=='workspace-write' and 自身.writeSid is None:#workspace-write缺SID
            raise Exception('AclSandbox workspace-write requires a write SID — derive it from the workspace via workspaceWriteSid()')#必须有工作区SID
        if 自身.mode=='workspace-write' and not 自身._tempDirDefined:#workspace-write缺临时
            raise Exception('AclSandbox workspace-write requires an explicit private temp directory or null')#必须显式临时或null
        if 自身.mode=='read-only' and 自身._tempDirDefined and 自身._tempDirOption is not None:#只读却给了临时路径
            raise Exception('AclSandbox read-only does not accept a temp directory')#只读不接受临时目录
        if 自身.mode=='read-only' and (自身.writeSid is not None or 自身.tempWriteSid is not None):#只读却给了SID
            raise Exception('AclSandbox read-only does not accept write SIDs')#只读不接受写入SID
        if 自身.mode=='workspace-write' and 自身._tempDirOption is not None and 自身.tempWriteSid is None:#有临时缺临时SID
            raise Exception('AclSandbox workspace-write with temp requires a temp write SID — derive it via tempWriteSid()')#必须有临时SID
        if 自身._tempDirDefined and 自身._tempDirOption is None and 自身.tempWriteSid is not None:#关掉临时却给了临时SID
            raise Exception('AclSandbox temp write SID requires a temp directory')#临时SID需要临时目录
        if 自身.writeSid is not None and 自身.tempWriteSid==自身.writeSid:#两个SID相同
            raise Exception('AclSandbox workspace and temp write SIDs must be distinct')#必须不同
        自身._tempDirResolved=None#init后解析的临时目录
        自身._tempDirUnset=True#尚未init
        自身._api=None#已加载绑定
        自身._token=None#受限令牌
        自身._writeSidPtr=None#工作区SID指针
        自身._tempWriteSidPtr=None#临时SID指针
        自身._sidAllocations=[]#SID分配
        自身._grantedPaths=[]#已授予的可撤销路径

    @property#只读
    def tempDir(自身):#已解析临时目录
        """已解析临时目录（init 之后可用；关掉临时授予时为 null）。"""
        if 自身._tempDirUnset:#尚未init
            return None#与TS undefined等价，对外用None
        return 自身._tempDirResolved#init后的值

    def 初始化(自身):#初始化沙箱
        """创建受限令牌并应用能力 SID 授权。非幂等安全：每个实例一次。"""
        if 自身._api is not None:#已初始化
            raise Exception('AclSandbox is already initialized')#不得重复init
        接口=解析绑定()#惰性加载绑定
        当前令牌=打开当前进程令牌(接口)#打开当前进程令牌
        当前令牌打开=True#当前令牌是否仍打开
        受限令牌=None#待创建的受限令牌
        try:#失败即关闭
            def 解析SID(sid):#解析SID字符串
                sid槽=分配指针槽()#接收指针的槽
                if 接口.convertStringSidToSidW(sid,sid槽)==0:#转换失败
                    抛上次错误(接口,'ConvertStringSidToSidW',sid)#带SID抛出
                已解析=解码指针(sid槽)#取出指针
                if 已解析 is None:#空指针
                    raise Win32错误('ConvertStringSidToSidW',接口.getLastError(),sid)#空指针则失败
                return 已解析#已解析指针
            自身._writeSidPtr=None if 自身.writeSid is None else 解析SID(自身.writeSid)#解析工作区SID
            自身._tempWriteSidPtr=None if 自身.tempWriteSid is None else 解析SID(自身.tempWriteSid)#解析临时SID
            if 自身.mode=='read-only' or 自身._tempDirOption is None:#只读或关掉临时
                临时目录=None#无临时
            else:#有临时字符串
                临时目录=自身._tempDirOption#解析临时目录
            if 临时目录 is not None:#有临时目录
                if not os.path.exists(临时目录) or not os.path.isdir(临时目录):#不存在或不是目录
                    raise Exception('AclSandbox temp dir does not exist or is not a directory: '+临时目录)#非法临时目录
                断言私有临时不相交(自身.writableDirs,临时目录)#不得与可写目录重叠
            自身._tempDirResolved=临时目录#记下已解析临时
            自身._tempDirUnset=False#已解析
            if 自身._manageDacls:#自己管理DACL
                if 自身._writeSidPtr is not None:#有工作区SID
                    for 路径 in 自身.writableDirs:#逐个可写目录
                        授予写入(接口,路径,自身._writeSidPtr)#授予常驻ACE
                    if 临时目录 is not None and 自身._tempWriteSidPtr is not None:#有临时
                        自身._grantedPaths.append({'path':临时目录,'sidPtr':自身._tempWriteSidPtr})#记下可撤销路径
                        授予写入(接口,临时目录,自身._tempWriteSidPtr)#授予临时ACE
            登录SID=查找登录SID(接口,当前令牌)#登录SID
            自身._sidAllocations.append(登录SID)#记下分配
            世界SID=制作众所周知SID(接口,abi.世界SID类型)#Everyone SID
            自身._sidAllocations.append(世界SID)#记下分配
            写入SID指针们=[项 for 项 in [自身._writeSidPtr,自身._tempWriteSidPtr] if 项 is not None]#能力SID
            受限令牌=创建受限令牌(接口,当前令牌,登录SID,写入SID指针们,{'world':世界SID},自身.mode)#创建受限令牌
            自身._token=受限令牌#记下令牌
            默认SID=自身._tempWriteSidPtr if 自身._tempWriteSidPtr is not None else (自身._writeSidPtr if 自身._writeSidPtr is not None else 世界SID)#合并默认DACL用的SID
            设令牌默认DACL授予(接口,受限令牌,默认SID)#合并默认DACL
            if 接口.closeHandle(当前令牌)==0:#关闭源令牌
                抛上次错误(接口,'CloseHandle','current process token')#抛出
            当前令牌打开=False#已关闭
            自身._api=接口#记下绑定
        except BaseException as 错误:#init失败
            清理失败=[]#清理失败
            if 当前令牌打开 and 接口.closeHandle(当前令牌)==0:#源令牌仍开
                清理失败.append(Win32错误('CloseHandle',接口.getLastError(),'current process token after init failure'))#关闭失败
            if 受限令牌 is not None and 接口.closeHandle(受限令牌)==0:#受限令牌已创建
                清理失败.append(Win32错误('CloseHandle',接口.getLastError(),'restricted token after init failure'))#关闭失败
            for 授权 in 自身._grantedPaths:#可撤销授权
                try:#撤销
                    撤销写入(接口,授权['path'],授权['sidPtr'])#撤销临时ACE
                except BaseException as 清理错误:#撤销失败
                    清理失败.append(清理错误)#记下
            for 标签,sid指针 in (('workspace write SID',自身._writeSidPtr),('temp write SID',自身._tempWriteSidPtr)):#写入SID
                尽力释放SID(接口,sid指针,标签,清理失败)#尽力释放
            for sid指针 in 自身._sidAllocations[:]:#init分配
                自身._sidAllocations.remove(sid指针)#弹出
                尽力释放SID(接口,sid指针,'init SID allocation',清理失败)#尽力释放
            自身._token=None#清令牌
            自身._writeSidPtr=None#清工作区指针
            自身._tempWriteSidPtr=None#清临时指针
            自身._tempDirResolved=None#清临时目录
            自身._tempDirUnset=True#恢复未设
            自身._grantedPaths=[]#清已授予路径
            if len(清理失败)>0:#有清理失败
                raise 聚合错误([错误,*清理失败],'AclSandbox init failed and '+str(len(清理失败))+' cleanup operation(s) also failed')#聚合失败
            raise 错误#原错误

    def 生成(自身,选项):#隔离spawn
        """在受限令牌下 spawn 一个进程。失败即关闭。"""
        接口=自身._api#已加载绑定
        令牌=自身._token#受限令牌
        if 接口 is None or 令牌 is None:#未初始化
            raise Exception('AclSandbox is not initialized: call init() first')#必须先init
        参数=选项.get('args') or []#参数
        工作目录=选项.get('cwd') or os.getcwd()#工作目录
        if 选项.get('stdio')=='inherit':#继承stdio
            原生=隔离继承生成(接口,令牌,{'command':选项['command'],'args':参数,'cwd':工作目录})#继承spawn
            退出码缓存=[None]#惰性等待
            def 等待():#等待结算
                if 退出码缓存[0] is None:#首次等待
                    退出码缓存[0]=等待退出(接口,原生['process'])#记下退出码
                if 接口.closeHandle(原生['job'])==0:#关闭作业
                    抛上次错误(接口,'CloseHandle','kill-on-close job')#抛出
                return {'stdout':b'','stderr':b'','exitCode':退出码缓存[0]}#继承时stdio为空
            return {'pid':原生['pid'],'wait':等待}#运行中的子进程
        原生=隔离生成(接口,令牌,{'command':选项['command'],'args':参数,'cwd':工作目录})#管道spawn
        标准出=排空管道(接口,原生['stdoutRead'])#排空stdout（同步）
        标准误=排空管道(接口,原生['stderrRead'])#排空stderr（同步）
        退出码缓存=[None]#惰性等待
        def 等待():#等待结算
            if 退出码缓存[0] is None:#首次等待
                退出码缓存[0]=等待退出(接口,原生['process'])#记下退出码
            return {'stdout':标准出,'stderr':标准误,'exitCode':退出码缓存[0]}#结果
        return {'pid':原生['pid'],'wait':等待}#运行中的子进程

    def 拆除(自身):#拆除沙箱
        """撤销可撤销（临时）授权，释放 SID，关闭令牌；常驻工作区 ACE 留下。"""
        接口=自身._api#已加载绑定
        if 接口 is None:#尚未init
            return#跳过
        失败们=[]#清理失败
        if 自身._manageDacls:#自己管理DACL
            for 授权 in 自身._grantedPaths:#可撤销授权
                try:#撤销
                    撤销写入(接口,授权['path'],授权['sidPtr'])#撤销临时ACE
                except BaseException as 错误:#撤销失败
                    失败们.append(错误)#记下
        for 标签,sid指针 in (('workspace write SID',自身._writeSidPtr),('temp write SID',自身._tempWriteSidPtr)):#写入SID
            尽力释放SID(接口,sid指针,标签,失败们)#尽力释放
        令牌=自身._token#受限令牌
        if 令牌 is not None:#有令牌
            try:#关闭令牌
                if 接口.closeHandle(令牌)==0:#关闭失败
                    抛上次错误(接口,'CloseHandle','restricted token')#抛出
            except BaseException as 错误:#关闭抛出
                失败们.append(错误)#记下
        for sid指针 in 自身._sidAllocations[:]:#init分配
            自身._sidAllocations.remove(sid指针)#弹出
            尽力释放SID(接口,sid指针,'init SID allocation',失败们)#尽力释放
        自身._api=None#清绑定
        自身._token=None#清令牌
        自身._writeSidPtr=None#清工作区指针
        自身._tempWriteSidPtr=None#清临时指针
        自身._grantedPaths=[]#清已授予路径
        if len(失败们)>0:#有清理失败
            raise 聚合错误(失败们,'AclSandbox dispose completed with '+str(len(失败们))+' cleanup failure(s)')#报告清理失败
