"""本地沙箱后端。它选择平台运行器链（Linux 先 bwrap 再 Landlock；macOS Seatbelt；Windows 为 ACL 受限令牌运行器），对竞争候选做一次功能探测，并报告每次包装的强制完整程度与 stderr 分类事实。缺失或无法使用的隔离失败即关闭，而不是返回原始 argv。

windows-acl 这一档另外拥有写入授权：写入 SID 是从规范工作区路径推导的按工作区身份（`workspaceWriteSid`），每个在场会话收到一个随机私有临时目录及其自己推导的能力（`tempWriteSid`）。工作区根 ACE 在每个服务器生命周期每个工作区只物化一次并常驻（跨会话复用缓存——精确 ACE 跳过让每次后续供给变成 O(1)，而不是每个会话再传播整棵树）；私有临时 ACE 在拆除时撤销。运行器收到两个 SID（它们的出现标记 seam 管理的约定）并停止自己管理 DACL。这一档报告部分强制，因为 WRITE_RESTRICTED 必须在其限制列表里保留 Everyone，且 NTFS 硬链接会把同一个文件对象跨路径别名。
"""
import json#会话/工作区键序列化
import math#有限数判定
import os#存在判定与路径拼接
import re#失败签名换行检查
import shutil#递归删除临时目录
import subprocess#功能探测 spawn
import sys#解释器路径与平台
import tempfile#平台临时根与私有临时目录
from ...依赖.schemastery import 路径上节点,字符串字段,自然数字段,列表字段#配置字段
from ..llm import 断言永不#导入封闭联合穷尽辅助
from ..沙盒 import 沙箱提供方,沙箱不可用错误#导入沙箱提供方与不可用错误
from ..沙盒_windows访问控制 import (#导入 ACL 授权、临时根断言与 SID 推导
    ACL写入授权,#写入授权物化
    断言临时根在工作区外,#临时根边界
    临时写入SID,#临时 SID
    工作区写入SID,#工作区 SID
    聚合错误,#聚合清理失败
)#windows-acl 导入结束
from .配置 import bwrap配置参数,landlock配置参数,seatbelt配置参数#导入各平台配置构建（profiles）
from .landlock入口 import (#从 Landlock 入口缝导入（镜像 node-addon-landlock-run）
    启动器二进制名,#启动器二进制名
    启动器失败退出,#启动器失败退出码
    启动器路径 as landlock启动器路径,#启动器路径
    探测 as 默认探测Landlock,#默认 Landlock 探测
)#Landlock 导入结束

名称='sandbox-local'#Cordis 插件名（包目录用下划线，插件名保留上游连字符）
name=名称#Cordis 插件名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

配置模式=路径上节点({#插件配置：全部可选——Config 供给默认
    'runnerCommand':列表字段(字符串字段(),默认值=[]),#运行器覆盖，默认空
    'runnerFailureSignatures':列表字段(字符串字段(),默认值=[]),#失败签名，默认空
    'probeTimeoutMs':自然数字段(默认值=5000),#探测超时默认 5 秒
})#Config 模式结束
Config=配置模式#Cordis 配置模式

def 默认探测Bwrap(超时毫秒):#探测 bwrap
    """探测 `bwrap` 能否创建配置；提供方缓存有界结果。"""
    try:#缺失二进制读作不可用
        探测=subprocess.run(#只读根探测
            ['bwrap','--ro-bind','/','/','--dev','/dev','--proc','/proc','--die-with-parent','--','true'],#探测 argv
            timeout=(超时毫秒/1000.0),#探测超时
            stdout=subprocess.DEVNULL,#忽略 stdout
            stderr=subprocess.DEVNULL,#忽略 stderr
        )#run 结束
    except (FileNotFoundError,PermissionError,subprocess.TimeoutExpired,OSError):#不可用或超时
        return False#不可用
    return 探测.returncode==0#退出 0 则可用

def 默认探测Seatbelt(seatbelt可执行,超时毫秒):#探测 Seatbelt
    """功能 Seatbelt 探测：经 `sandbox-exec -p` 应用真正的 `read-only` 配置并在其下跑 `true`——退出 0 表示内核接受并强制了该配置。缺失的 `sandbox-exec` 让 spawn 失败并探测为 `unusable`。"""
    try:#缺失二进制读作不可用
        探测=subprocess.run(#只读配置探测
            [seatbelt可执行,*seatbelt配置参数({'mode':'read-only','workspaceRoot':'/'}),'--','true'],#探测 argv
            timeout=(超时毫秒/1000.0),#探测超时
            stdout=subprocess.DEVNULL,#忽略 stdout
            stderr=subprocess.DEVNULL,#忽略 stderr
        )#run 结束
    except (FileNotFoundError,PermissionError,subprocess.TimeoutExpired,OSError):#不可用或超时
        return False#不可用
    return 探测.returncode==0#退出 0 则可用

def 默认探测WindowsAcl(运行器调用,超时毫秒):#探测 windows-acl
    """功能 windows-acl 探测：在只读模式（零授权、不改 ACL）下围绕 `cmd /c exit 0` 跑运行器——退出 0 表示运行器创建了受限令牌并在其下 spawn 了子进程。"""
    if len(运行器调用)==0:#空调用
        return False#不可用
    try:#缺失二进制读作不可用
        探测=subprocess.run(#探测 argv
            [*运行器调用,#运行器前缀
             '--workspace',tempfile.gettempdir(),'--temp',tempfile.gettempdir(),'--mode','read-only',#只读、零授权
             '--','cmd','/c','exit','0'],#探测命令
            timeout=(超时毫秒/1000.0),#探测超时
            stdout=subprocess.DEVNULL,#忽略 stdout
            stderr=subprocess.DEVNULL,#忽略 stderr
        )#run 结束
    except (FileNotFoundError,PermissionError,subprocess.TimeoutExpired,OSError):#不可用或超时
        return False#不可用
    return 探测.returncode==0#退出 0 则可用

#按平台的运行器链——选择先按平台，探测其次
平台链={#按平台的运行器链
    'linux':('bwrap','landlock'),#Linux：先 bwrap 再 Landlock
    'darwin':('seatbelt',),#macOS：Seatbelt
    'win32':('windows-acl',),#Windows：ACL 运行器
}#平台链结束

#一档在未经探测被选中时（链长度为 1）声称的强制完整程度
静态强制={#未探测选中时的强制程度
    'bwrap':'full',#bwrap 完整
    'landlock':'full',#表完整性；实际经探测
    'seatbelt':'full',#Seatbelt 完整
    'windows-acl':'partial',#部分强制
}#静态强制结束

def 断言正有限数(名称,值):#断言正有限数
    """探测界限必须是正有限数：未校验的 0 会静默表示「无界」。"""
    if not math.isfinite(值) or 值<=0:#非正或非有限
        raise Exception('sandbox-local: '+名称+' must be a positive finite number')#非法

#每个运行器的内核所说的拒绝方言
拒绝签名={#拒绝签名
    'bwrap':('read-only file system',),#只读文件系统
    'landlock':('permission denied',),#权限被拒绝
    'seatbelt':('operation not permitted',),#操作不允许
    'windows-acl':('access is denied','access to the path','permission denied'),#Windows 拒绝措辞
    'runnerCommand':('read-only file system','permission denied'),#覆盖运行器的并集
}#拒绝签名结束

windowsAcl运行器失败退出=127#windows-acl 失败退出码

#运行器拥有的致命诊断
运行器失败规则={#运行器失败规则
    'bwrap':({'fatalSignatures':('bwrap: ',)},),#仅签名
    'landlock':({#退出门加签名
        'allowedExitCodes':(启动器失败退出,),#启动器失败码
        'fatalSignatures':(启动器二进制名+': ',),#启动器前缀
        'informationalLines':(启动器二进制名+': partial enforcement (older Landlock ABI)',),#部分强制信息行
    },),#landlock 结束
    'seatbelt':({'fatalSignatures':('sandbox-exec: ',)},),#仅签名
    'windows-acl':({'allowedExitCodes':(windowsAcl运行器失败退出,),'fatalSignatures':('windows-acl-run: ',)},),#退出 127 加签名
}#运行器失败规则结束

def 规范平台(平台):#把 sys.platform 收到平台链表键
    """把宿主平台名收到 PLATFORM_CHAINS 键。"""
    if 平台.startswith('linux'):#Linux 族
        return 'linux'#链键
    return 平台#原样（darwin/win32/其他）

class 本地沙箱提供方(沙箱提供方):#本地进程沙箱提供方
    """本地进程沙箱提供方。注册为 `ctx.sandbox`。缓存链裁决，并在 windows-acl 档上缓存写入授权；一次性探测不再 spawn 别的东西。"""
    Config=配置模式#静态配置模式
    def __init__(自身,上下文对象,配置):#构造本地提供方
        """记下覆盖运行器与探测超时，并在拆除时撤销临时 ACL 授权。"""
        super().__init__(上下文对象)#注册为 ctx.sandbox
        运行器=取字段(配置,'runnerCommand') or []#运行器覆盖
        失败签名=取字段(配置,'runnerFailureSignatures') or []#失败签名
        if len(运行器)==0 and len(失败签名)>0:#有签名没有运行器
            raise Exception('sandbox-local: runnerFailureSignatures requires runnerCommand')#签名依赖运行器
        if len(运行器)>0 and len(失败签名)==0:#有运行器没有签名
            raise Exception('sandbox-local: runnerCommand requires at least one runnerFailureSignatures entry')#运行器需要签名
        for 签名 in 失败签名:#逐条检查形态
            if len(签名.strip())==0 or re.search(r'[\r\n]',签名) is not None:#空或含换行
                raise Exception('sandbox-local: runnerFailureSignatures entries must be non-empty single-line strings')#必须是非空单行
        自身.runnerCommand=运行器 if len(运行器)>0 else None#空则未配置
        自身.configuredRunnerFailureSignatures=list(失败签名)#记下签名
        自身.probeTimeoutMs=取字段(配置,'probeTimeoutMs')#记下超时
        if 自身.probeTimeoutMs is None:#模式应已填默认
            自身.probeTimeoutMs=5000#回落 5 秒
        断言正有限数('probeTimeoutMs',自身.probeTimeoutMs)#必须正有限
        自身.selectedRunner=None#已选运行器；首次隔离前为 None
        自身.workspaceGrants={}#工作区授权
        自身.tempCapabilities={}#临时能力
        自身.internals={}#测试钩子
        自身.内部钩子=自身.internals#中文别名
        def 挂拆():#拆除时撤销
            """返回撤销 ACL 授权的拆除器。"""
            def 拆除():#撤销临时授权
                """提供方拆除时撤销临时 ACE。"""
                自身.撤销ACL授权()#撤销 ACL 授权
            return 拆除#释放器
        上下文对象.effect(挂拆,'sandbox-local acl grant cleanup')#临时授权随提供方撤销

    def 隔离(自身,参数表,政策):#包装为隔离 argv
        """按 `policy` 把 `argv` 包进所选运行器的调用——有已配置 `runnerCommand` 时用它（操作者的断言，不探测），否则用说自己配置方言的平台链运行器。"""
        if 自身.runnerCommand is not None:#有覆盖
            return {#覆盖运行器
                'argv':[*自身.runnerCommand,*bwrap配置参数(政策),'--',*参数表],#覆盖加 bwrap 配置
                'enforcement':'full',#覆盖断言完整强制
                'denialSignatures':list(拒绝签名['runnerCommand']),#覆盖拒绝签名
                'runnerFailureRules':[{'fatalSignatures':list(自身.configuredRunnerFailureSignatures)}],#配置的失败签名
            }#返回结束
        已选=自身.选择运行器(取字段(政策,'mode'))#选择运行器
        运行器参数表=自身.运行器参数表(取字段(已选,'runner'),政策)#运行器调用
        return {#平台运行器
            'argv':[*运行器参数表,'--',*参数表],#运行器加调用方 argv
            'enforcement':取字段(已选,'enforcement'),#所选强制程度
            'denialSignatures':list(拒绝签名[取字段(已选,'runner')]),#该运行器拒绝签名
            'runnerFailureRules':[{键:list(值) if isinstance(值,tuple) else 值 for 键,值 in 规则.items()} for 规则 in 运行器失败规则[取字段(已选,'runner')]],#该运行器失败规则
        }#返回结束

    def 运行器参数表(自身,运行器,政策):#构建运行器 argv
        """所选档的运行器调用（程序加配置参数）对应一份政策。"""
        if 运行器=='bwrap':#bwrap
            return ['bwrap',*bwrap配置参数(政策)]#bwrap 配置
        if 运行器=='landlock':#Landlock
            return [自身.landlock启动器(),*landlock配置参数(政策)]#Landlock 启动器
        if 运行器=='seatbelt':#Seatbelt
            return [自身.seatbelt可执行(),*seatbelt配置参数(政策)]#sandbox-exec
        if 运行器=='windows-acl':#ACL 运行器
            return 自身.windowsAcl运行器参数表(政策)#ACL 运行器
        return 断言永不(运行器,'SelectedRunner.runner')#封闭联合穷尽

    def windowsAcl运行器参数表(自身,政策):#构建 windows-acl argv
        """一份政策的 windows-acl 运行器 argv。有调用会话且处于 workspace-write 时，授权在每个提供方生命周期物化一次。"""
        会话号=取字段(政策,'sessionId')#调用会话
        if 会话号 is None or 取字段(政策,'mode')=='read-only':#无会话或只读
            return [#不物化授权
                *自身.windowsAcl运行器调用(),#运行器前缀
                '--workspace',取字段(政策,'workspaceRoot'),#工作区
                '--temp',tempfile.gettempdir(),#环境临时根
                '--mode',取字段(政策,'mode'),#模式
            ]#返回结束
        临时=自身.物化ACL授权(会话号,取字段(政策,'workspaceRoot'))#物化授权
        return [#seam 管理的授权
            *自身.windowsAcl运行器调用(),#运行器前缀
            '--workspace',取字段(政策,'workspaceRoot'),#工作区
            '--temp',取字段(临时,'dir'),#私有临时目录
            '--mode',取字段(政策,'mode'),#模式
            '--write-sid',工作区写入SID(取字段(政策,'workspaceRoot')),#工作区 SID
            '--temp-write-sid',取字段(临时,'writeSid'),#临时 SID
        ]#返回结束

    def 物化ACL授权(自身,会话号,工作区根):#物化 ACL 授权
        """在每个提供方生命周期内物化一份 workspace-write 政策的 ACE 一次。失败即关闭：半物化的临时授权在错误传播之前被撤销。"""
        断言临时根在工作区外(工作区根,tempfile.gettempdir())#临时根必须在工作区外
        写入SID=工作区写入SID(工作区根)#工作区 SID
        if 工作区根 not in 自身.workspaceGrants:#尚未常驻
            授权=ACL写入授权.创建(写入SID)#解析 SID
            try:#授予工作区根
                授权.添加(工作区根,True)#常驻 ACE
            except BaseException as 错误:#授予失败
                try:#拆除授权
                    授权.拆除()#释放 SID
                except BaseException as 清理错误:#清理也失败
                    raise 聚合错误([错误,清理错误],'sandbox-local windows-acl workspace grant failed and its cleanup also failed')#聚合失败
                raise 错误#原错误
            自身.workspaceGrants[工作区根]=授权#记下常驻授权
        键=json.dumps([str(会话号),工作区根],ensure_ascii=False,separators=(',',':'))#会话/工作区键
        已有=自身.tempCapabilities.get(键)#已有临时能力
        if 已有 is not None:#复用
            return 已有#已有能力
        临时目录=tempfile.mkdtemp(prefix='dsh-',dir=tempfile.gettempdir())#随机私有临时目录
        临时SID=临时写入SID(临时目录)#临时 SID
        授权=None#待创建的临时授权
        try:#物化临时授权
            授权=ACL写入授权.创建(临时SID)#解析 SID
            授权.添加(临时目录)#可撤销 ACE
        except BaseException as 错误:#物化失败
            清理失败=[]#清理失败
            if 授权 is not None:#已创建授权
                try:#拆除
                    授权.拆除()#撤销并释放
                except BaseException as 清理错误:#清理失败
                    清理失败.append(清理错误)#记下
            try:#删除临时目录
                自身.删除临时目录(临时目录)#删除
            except BaseException as 清理错误:#删除失败
                清理失败.append(清理错误)#记下
            if len(清理失败)>0:#有清理失败
                raise 聚合错误([错误,*清理失败],'sandbox-local windows-acl temp grant materialization failed and its cleanup also failed')#聚合失败
            raise 错误#原错误
        能力={'dir':临时目录,'writeSid':临时SID,'grant':授权}#临时能力
        自身.tempCapabilities[键]=能力#记下
        return 能力#新能力

    def 撤销ACL授权(自身):#撤销 ACL 授权
        """拆除每份写入授权（提供方拆除）：可撤销临时 ACE 被撤销，本提供方创建的私有临时目录被删除；常驻工作区 ACE 留下。清理失败被报告，不抛出。"""
        if len(自身.workspaceGrants)==0 and len(自身.tempCapabilities)==0:#没有授权
            return#跳过
        失败们=[]#清理失败
        授权们=[*自身.workspaceGrants.values(),*[能力['grant'] for 能力 in 自身.tempCapabilities.values()]]#每份授权
        for 授权 in 授权们:#逐份拆除
            try:#拆除
                授权.拆除()#工作区跳过常驻 ACE；临时撤销
            except BaseException as 错误:#拆除失败
                失败们.append(错误)#记下
        for 能力 in 自身.tempCapabilities.values():#每个临时目录
            try:#删除
                自身.删除临时目录(能力['dir'])#删除
            except BaseException as 错误:#删除失败
                失败们.append(错误)#记下
        自身.workspaceGrants.clear()#清空工作区授权
        自身.tempCapabilities.clear()#清空临时能力
        if len(失败们)>0:#有清理失败
            自身.ctx.logger.warn('sandbox-local: windows-acl grant cleanup completed with '+str(len(失败们))+' failure(s)')#警告文案
            for 错误 in 失败们:#逐条错误
                自身.ctx.logger.warn(错误)#记日志

    def 删除临时目录(自身,目录):#删除临时目录
        """删除一个提供方拥有的私有临时目录（可注入供清理测试）。"""
        钩子删除=取字段(自身.internals,'rmTempDir')#钩子
        if 钩子删除 is not None:#有钩子
            钩子删除(目录)#用钩子
            return#结束
        shutil.rmtree(目录,ignore_errors=False)#递归删除

    def 选择运行器(自身,模式):#选择运行器
        """为提供方生命周期解析一次哪个运行器隔离命令。平台没有链或没有候选通过时失败即关闭。"""
        if 自身.selectedRunner is None:#首次裁决
            自身.selectedRunner=自身.链裁决()#走链
        if 自身.selectedRunner=='unavailable':#不可用
            raise 沙箱不可用错误(模式)#失败即关闭
        return 自身.selectedRunner#已选运行器

    def 链裁决(自身):#链裁决
        """走本平台的链：唯一候选不探测，多个按顺序探测，没有可用的 → unavailable。"""
        钩子链=取字段(自身.internals,'chain')#钩子链
        if 钩子链 is not None:#有钩子链
            链=list(钩子链)#用钩子
        else:#平台链
            平台=取字段(自身.internals,'platform')#钩子平台
            if 平台 is None:#未注入
                平台=规范平台(sys.platform)#宿主平台
            链=list(平台链.get(规范平台(平台),()))#平台链或空
        if len(链)==0:#没有链
            return 'unavailable'#不可用
        if len(链)==1:#唯一候选
            第一=链[0]#唯一档
            return {'runner':第一,'enforcement':静态强制[第一]}#不探测选中
        for 运行器 in 链:#按顺序探测
            强制=自身.探测运行器(运行器)#本档探测
            if 强制!='unusable':#第一可用
                return {'runner':运行器,'enforcement':强制}#选中
        return 'unavailable'#全部不可用

    def 探测运行器(自身,运行器):#探测一档
        """一档的功能探测（经链走访至多一次）。"""
        if 运行器=='bwrap':#bwrap
            探测=取字段(自身.internals,'probeBwrap')#钩子
            if 探测 is None:#无钩子
                探测=lambda:默认探测Bwrap(自身.probeTimeoutMs)#默认
            return 'full' if 探测() else 'unusable'#通过则完整
        if 运行器=='landlock':#Landlock
            探测=取字段(自身.internals,'probeLandlock')#钩子
            if 探测 is None:#无钩子
                探测=lambda 启动器:默认探测Landlock(启动器,{'timeoutMs':自身.probeTimeoutMs})#默认
            return 探测(自身.landlock启动器())#启动器探测报告
        if 运行器=='seatbelt':#Seatbelt
            探测=取字段(自身.internals,'probeSeatbelt')#钩子
            if 探测 is None:#无钩子
                探测=lambda 可执行:默认探测Seatbelt(可执行,自身.probeTimeoutMs)#默认
            return 'full' if 探测(自身.seatbelt可执行()) else 'unusable'#通过则完整
        if 运行器=='windows-acl':#windows-acl
            探测=取字段(自身.internals,'probeWindowsAcl')#钩子
            if 探测 is None:#无钩子
                探测=lambda:默认探测WindowsAcl(自身.windowsAcl运行器调用(),自身.probeTimeoutMs)#默认
            return 'partial' if 探测() else 'unusable'#通过则部分
        return 断言永不(运行器,'SelectedRunner.runner')#封闭联合穷尽

    def landlock启动器(自身):#Landlock 启动器路径
        """要探测并 exec 的 Landlock 启动器（测试钩子盖过已解析的）。"""
        覆盖=取字段(自身.internals,'landlockLauncher')#钩子
        if 覆盖 is not None:#有钩子
            return 覆盖#用钩子
        return landlock启动器路径()#已解析

    def seatbelt可执行(自身):#sandbox-exec 路径
        """要探测并 exec 的 `sandbox-exec` 可执行文件（测试钩子盖过系统的）。"""
        覆盖=取字段(自身.internals,'seatbeltExec')#钩子
        if 覆盖 is not None:#有钩子
            return 覆盖#用钩子
        return 'sandbox-exec'#系统名

    def windowsAcl运行器调用(自身):#windows-acl 运行器前缀
        """windows-acl 运行器 argv 前缀：有 `运行器.py` 入口时用解释器跑它（生产/开发同一约定）。"""
        覆盖=取字段(自身.internals,'windowsAclRunnerArgs')#钩子覆盖
        if 覆盖 is not None:#用钩子
            return list(覆盖)#钩子 argv
        入口覆盖=取字段(自身.internals,'windowsAclRunnerEntry')#假入口
        if 入口覆盖 is not None:#测试注入入口
            if os.path.exists(入口覆盖):#存在则用
                return [sys.executable,入口覆盖]#解释器 + 入口
            return [sys.executable,入口覆盖]#仍返回（探测会失败）
        try:#定位已安装的 windows-acl 运行器模块
            from .. import 沙盒_windows访问控制 as acl包#导入包以取目录
            入口=os.path.join(os.path.dirname(acl包.__file__),'运行器.py')#运行器入口
        except Exception:#导入失败
            入口=os.path.join(os.path.dirname(__file__),'..','沙盒_windows访问控制','运行器.py')#相对回落
            入口=os.path.normpath(入口)#规范化
        return [sys.executable,入口]#解释器 + 运行器.py

default=本地沙箱提供方#默认导出本地提供方
默认=本地沙箱提供方#中文默认导出

__all__=['名称','name','配置模式','Config','本地沙箱提供方','默认','default']#公开面
