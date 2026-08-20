"""windows-acl 隔离运行器：沙箱 seam 用来代替调用方命令生成的 argv 前缀包装。它用工作区写入 SID 允许列表创建 WRITE_RESTRICTED 令牌，在其下生成被包装的 argv，并继承调用方的 stdio（字节直通），镜像子进程退出码，退出时撤销其临时授权（工作区 ACE 作为复用缓存保持常驻）。

稳定 argv 约定（seam 构建它；原生 exe 替换会保持同一约定）：
  [python, 运行器.py, '--workspace', <dir>, '--temp', <dir>,
   '--mode', <read-only|workspace-write>,
   ['--write-sid', <S-1-4-…>,
    '--temp-write-sid', <S-1-4-…>], '--', <argv...>]

模式：
 - workspace-write：工作区与临时目录携带不同的能力 SID 写入授权；其余 ACL 可寻址写入被拒绝，除已文档化的 Everyone 与硬链接边界。
 - read-only：没有能力 SID 授权；限制列表不携带能力 SID，因此更早 workspace-write 期留下的常驻授权 ACE 保持惰性。两种模式都丢掉 Authenticated Users 以及 INTERACTIVE/LOCAL；两份列表共享保活组（登录 SID、EVERYONE），只在能力上不同。

`--write-sid` + `--temp-write-sid`：seam 的授权约定——调用方已经物化了不同的工作区与私有临时 ACE 并拥有其撤销，因此运行器既不授予也不撤销（manageDacls: false）。没有这一对时，workspace-write 把 `--temp` 当根，创建随机私有子目录，推导自己的临时 SID，子进程退出后删掉该目录。两条流里运行器都在生成之前把自身环境的 TMP/TEMP 改写成私有目录。

失败约定：每次运行器侧失败向 stderr 打印 `windows-acl-run: <detail>` 并以 127 退出——seam 的 RUNNER_FAILURE_RULES 匹配该签名。子进程从不在未受限状态下生成。
"""
import os,sys,tempfile,shutil#目录、参数、临时目录与删除

from .ffi import 解析绑定#惰性Win32绑定
from . import ACL沙箱,断言临时根在工作区外#沙箱与临时根边界检查
from .工作区sid import 临时写入SID,工作区写入SID#临时与工作区SID推导

运行器签名='windows-acl-run'#失败签名前缀
运行器失败退出=127#运行器失败退出码

class 运行器失败(Exception):#已打印过签名的失败
    """已向 stderr 打印签名行的运行器失败。"""
    pass#无额外字段

def 失败(细节):#打印并抛出
    """打印运行器失败签名行并展开。"""
    sys.stderr.write(运行器签名+': '+细节+'\n')#签名行
    raise 运行器失败(细节)#已打印，外层不再重复

def 解析参数(原始):#解析运行器argv
    """解析运行器 argv 为工作区/临时/模式/SID/命令。"""
    工作区=None#工作区
    临时=None#临时
    模式=None#模式
    写入SID=None#工作区SID
    解析临时写入SID=None#临时SID
    下标=0#当前下标
    while 下标<len(原始):#直到--或结束
        标记=原始[下标]#当前标记
        if 标记=='--':#命令分隔
            下标+=1#跳过--
            break#进入命令
        下标+=1#前进到值
        if 下标>=len(原始):#缺值
            失败('missing value after '+标记)#缺值
        值=原始[下标]#选项值
        if 标记=='--workspace':#工作区
            工作区=值#记下
        elif 标记=='--temp':#临时
            临时=值#记下
        elif 标记=='--mode':#模式
            模式=值#记下
        elif 标记=='--write-sid':#工作区SID
            写入SID=值#记下
        elif 标记=='--temp-write-sid':#临时SID
            解析临时写入SID=值#记下
        else:#未知选项
            失败('unknown argument: '+标记)#未知选项
        下标+=1#下一选项
    if 工作区 is None:#缺工作区
        失败('missing --workspace')#缺工作区
    if 临时 is None:#缺临时
        失败('missing --temp')#缺临时
    if 模式!='read-only' and 模式!='workspace-write':#未知模式
        失败('unknown mode: '+str(模式))#未知模式
    参数表=原始[下标:]#--之后
    if len(参数表)==0:#缺命令
        失败('missing command after --')#缺命令
    return {'workspace':工作区,'temp':临时,'mode':模式,'writeSid':写入SID,'tempWriteSid':解析临时写入SID,'command':参数表[0],'args':参数表[1:]}#已解析

def 要求目录(标签,路径):#要求已存在目录
    """要求路径是已存在目录。"""
    if not os.path.exists(路径) or not os.path.isdir(路径):#不是目录
        失败(标签+' is not an existing directory: '+路径)#边界失败

def 主():#运行器入口
    """解析参数、物化沙箱、生成隔离子进程并镜像退出码。"""
    解析=解析参数(sys.argv[1:])#解析参数
    要求目录('--workspace',解析['workspace'])#工作区必须存在
    要求目录('--temp',解析['temp'])#临时必须存在
    seam管理=解析['writeSid'] is not None or 解析['tempWriteSid'] is not None#seam是否已物化授权
    if 解析['mode']=='read-only' and seam管理:#只读却带了SID
        失败('read-only does not accept --write-sid or --temp-write-sid')#只读不接受SID
    if 解析['mode']=='workspace-write' and (解析['writeSid'] is None)!=(解析['tempWriteSid'] is None):#只给了一半
        失败('workspace-write requires --write-sid and --temp-write-sid together')#必须成对
    if 解析['mode']=='workspace-write':#工作区可写
        断言临时根在工作区外(解析['workspace'],解析['temp'])#临时根不得在工作区内
    接口=解析绑定()#加载Win32绑定
    if 接口.setConsoleCtrlHandler(None,1)==0:#忽略控制台CTRL
        失败('SetConsoleCtrlHandler failed (Win32 '+str(接口.getLastError())+')')#设置失败
    自有临时目录=None#本运行器创建的临时目录
    沙箱=None#沙箱实例
    已初始化=False#是否已init
    try:#生成子进程
        私有临时目录=None#私有临时目录
        写入SID=None#工作区SID
        私有临时SID=None#临时SID
        if 解析['mode']=='workspace-write':#工作区可写才推导SID
            写入SID=工作区写入SID(解析['workspace'])#从工作区路径推导
            if seam管理:#seam已物化
                if 解析['writeSid']!=写入SID:#必须匹配工作区
                    失败('--write-sid does not match --workspace')#不匹配
                私有临时目录=解析['temp']#临时就是私有目录
                私有临时SID=临时写入SID(私有临时目录)#从临时路径推导
                if 解析['tempWriteSid']!=私有临时SID:#必须匹配临时
                    失败('--temp-write-sid does not match --temp')#不匹配
            else:#独立使用
                自有临时目录=tempfile.mkdtemp(prefix='dsh-',dir=解析['temp'])#在根下创建私有子目录
                私有临时目录=自有临时目录#用作临时
                私有临时SID=临时写入SID(私有临时目录)#推导临时SID
        选项={'writableDirs':[解析['workspace']] if 解析['mode']=='workspace-write' else [],'tempDir':私有临时目录,'mode':解析['mode'],'manageDacls':not seam管理}#构造选项
        if 写入SID is not None:#有工作区SID
            选项['writeSid']=写入SID#带上
        if 私有临时SID is not None:#有临时SID
            选项['tempWriteSid']=私有临时SID#带上
        沙箱=ACL沙箱(选项)#构造沙箱
        沙箱.初始化()#物化授权与令牌
        已初始化=True#此后dispose必须跑
        if 私有临时目录 is not None:#有私有临时
            if 接口.setEnvironmentVariableW('TMP',私有临时目录)==0:#改写TMP
                失败('SetEnvironmentVariableW TMP failed (Win32 '+str(接口.getLastError())+')')#设置失败
            if 接口.setEnvironmentVariableW('TEMP',私有临时目录)==0:#改写TEMP
                失败('SetEnvironmentVariableW TEMP failed (Win32 '+str(接口.getLastError())+')')#设置失败
        子进程=沙箱.生成({'command':解析['command'],'args':解析['args'],'stdio':'inherit'})#生成隔离子进程
        结果=子进程['wait']()#等到退出
        return 结果['exitCode']#镜像退出码
    finally:#无论成败
        if 已初始化:#已init
            try:#拆除沙箱
                if 沙箱 is not None:#有实例
                    沙箱.拆除()#撤销可撤销授权
            except BaseException as 错误:#清理失败
                消息=错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)#清理消息
                if isinstance(错误,Exception) and hasattr(错误,'args') and len(错误.args)>0 and isinstance(错误.args[0],str):#有消息
                    消息=str(错误)#用str
                else:#兜底
                    消息=str(错误)#字符串化
                sys.stderr.write(运行器签名+': cleanup: '+消息+'\n')#报告清理
        if 自有临时目录 is not None:#本运行器创建的临时
            try:#删除私有目录
                shutil.rmtree(自有临时目录,ignore_errors=False)#递归删除
            except BaseException as 错误:#删除失败
                sys.stderr.write(运行器签名+': cleanup: '+str(错误)+'\n')#报告清理

if __name__=='__main__':#脚本入口
    try:#入口结算
        退出码=主()#跑主流程
        sys.exit(退出码)#镜像退出码
    except 运行器失败:#已打印签名
        sys.exit(运行器失败退出)#运行器失败码
    except BaseException as 错误:#尚未打印签名
        sys.stderr.write(运行器签名+': '+str(错误)+'\n')#补打签名
        sys.exit(运行器失败退出)#运行器失败码
