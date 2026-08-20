"""对应 npm 包 `@deepseek-ai/node-addon-landlock-run` 的 Python 入口面：解析启动器路径、构建授权 argv、跑功能探测。

本模块拥有启动器 CLI 约定，使消费方不必自行拼写标志或解析启动器输出。政策（沙箱模式）仍属消费方：本包只知道哪些路径被授予读或写。本树尚未迁入 native/landlock-run，因此入口缝落在 sandbox_local 内；日后独立包迁入后可由该包替换。
"""
import os,re,subprocess,sys#路径、探测报告正则、同步探测与平台/架构
from pathlib import Path#入口模块目录

启动器二进制名='landlock-run'#平台包 bin/ 下的启动器文件名
启动器失败退出=125#每次启动器级失败的退出码（约定的一部分）
部分强制报告=re.compile(r'partially enforced')#探测 stdout 上的部分强制标记

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def _架构():#对齐 process.arch 词表
    """把 Python 机器名收成 npm cpu 词表（x64 / arm64）。"""
    机=''#机型
    if hasattr(os,'uname'):#POSIX
        try:#uname 可能失败
            机=os.uname().machine#POSIX 机型
        except Exception:#uname 失败
            机=''#回落
    if not 机:#Windows 等
        机=os.environ.get('PROCESSOR_ARCHITECTURE','')#环境机型
    低=机.lower()#小写比较
    if 低 in ('x86_64','amd64','x64'):#64 位 x86
        return 'x64'#npm cpu
    if 低 in ('aarch64','arm64'):#64 位 ARM
        return 'arm64'#npm cpu
    return 低 or 'unknown'#原样或未知

def 启动器路径(解析包清单=None):#本宿主启动器绝对路径
    """解析本宿主的 landlock-run 绝对路径。故意不检查是否存在；探测才是可用性信号。

    默认在本模块旁查找 `node_modules/@deepseek-ai/node-addon-landlock-run-<platform>-<arch>/bin/landlock-run`；
    无平台包时返回该固定路径（通常不存在），与 JS 入口在缺可选依赖时的回落一致。
    """
    平台=sys.platform#宿主平台
    if 平台.startswith('linux'):#Linux 族收成 linux
        平台='linux'#npm os
    平台包='@deepseek-ai/node-addon-landlock-run-'+平台+'-'+_架构()#按平台/架构拼包名
    if 解析包清单 is not None:#测试钩子：解析 platform 包的 package.json
        try:#可解析则取其旁 bin
            清单路径=解析包清单(平台包+'/package.json')#抛出表示不可解析
            return os.path.join(os.path.dirname(清单路径),'bin',启动器二进制名)#bin 下启动器
        except Exception:#不可解析；只有解析失败能到这里
            pass#落入固定回落路径
    #固定回落：落在本入口包边界内，永不相对 cwd
    return str(Path(__file__).resolve().parent/'node_modules'/平台包/'bin'/启动器二进制名)#可能不存在

def 授权参数(授权):#构建 --ro/--rw argv
    """为一组文件系统授权构建启动器参数（`--` 分隔符之前）。调用方 spawn `[启动器路径(), ...授权参数(授权), '--', ...命令]`。"""
    只读=取字段(授权,'readOnly')#只读根
    读写=取字段(授权,'readWrite')#可写根
    参数=[]#累积 argv
    for 根 in (只读 or []):#只读根在前，调用方顺序
        参数.extend(['--ro',根])#--ro <path>
    for 根 in (读写 or []):#可写根随后
        参数.extend(['--rw',根])#--rw <path>
    return 参数#授权参数表

def 探测(启动器=None,选项=None):#功能强制探测
    """跑 `landlock-run --probe`：仅当内核真正强制时退出 0。返回 `'full' | 'partial' | 'unusable'`。"""
    if 启动器 is None:#默认解析本宿主路径
        启动器=启动器路径()#已解析路径
    if 选项 is None:#默认选项
        选项={}#空映射
    超时毫秒=取字段(选项,'timeoutMs',2000)#默认 2 秒（入口包默认；提供方调用时传入 probeTimeoutMs）
    try:#spawn 可能因缺失二进制失败
        结果=subprocess.run(#同步探测
            [启动器,'--probe'],#探测 argv
            timeout=(超时毫秒/1000.0) if 超时毫秒 else None,#毫秒转秒
            capture_output=True,#捕获输出
            text=True,#文本
            stdin=subprocess.DEVNULL,#关掉 stdin
        )#run 结束
    except Exception:#缺失、超时、无法执行；只有这类抛出能到这里
        return 'unusable'#与无强制内核同裁决
    if 结果.returncode!=0:#非零则不可用
        return 'unusable'#不可用
    输出=结果.stdout or ''#探测报告
    if 部分强制报告.search(输出):#部分强制标记
        return 'partial'#按 ABI 部分
    return 'full'#完整强制
