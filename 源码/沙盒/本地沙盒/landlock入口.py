"""对应 npm 包 `@deepseek-ai/node-addon-system/landlock-run` 的 Python 入口面：解析启动器路径、构建授权 argv、跑功能探测。

本模块拥有启动器 CLI 约定，使消费方不必自行拼写标志或解析启动器输出。政策（沙箱模式）仍属消费方：本包只知道哪些路径被授予读或写。本树尚未迁入 native/landlock-run，因此入口缝落在 sandbox_local 内；日后独立包迁入后可由该包替换。
"""
import os,re,subprocess,sys#路径、探测报告正则、同步探测与平台/架构

启动器二进制名='landlock-run'#平台包 bin/ 下的启动器文件名
启动器失败退出=125#每次启动器级失败的退出码（约定的一部分）
部分强制报告=re.compile(r'partially enforced')#探测 stdout 上的部分强制标记

def _架构():
    """把 Python 机器名收成 npm cpu 词表（x64 / arm64）。"""
    机=''#机型
    if hasattr(os,'uname'):#POSIX 才有 uname
        try:
            机=os.uname().machine#POSIX 机型
        except OSError:
            机=''#回落
    if 机=='':#Windows 等
        机=os.environ['PROCESSOR_ARCHITECTURE'] if 'PROCESSOR_ARCHITECTURE' in os.environ else ''#环境机型
    低=机.lower()#小写比较
    if 低 in ('x86_64','amd64','x64'):#64 位 x86
        return 'x64'#npm cpu
    if 低 in ('aarch64','arm64'):#64 位 ARM
        return 'arm64'#npm cpu
    return 低 if 低!='' else 'unknown'#原样或未知

def 启动器路径(解析包清单=None):
    """解析本宿主的 landlock-run 绝对路径。故意不检查是否存在；探测才是可用性信号。"""
    平台=sys.platform#宿主平台
    if 平台.startswith('linux'):#Linux 族收成 linux
        平台='linux'#npm os
    平台包='@deepseek-ai/node-addon-system-'+平台+'-'+_架构()#按平台/架构拼包名
    if 解析包清单 is not None:#测试钩子：解析 platform 包的 package.json
        try:
            清单路径=解析包清单(平台包+'/package.json')#抛出表示不可解析
            return os.path.join(os.path.dirname(清单路径),'bin',启动器二进制名)#bin 下启动器
        except (OSError,TypeError,ValueError,KeyError):
            #测试钩子用抛出表示不可解析
            pass#落入固定回落路径
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),'node_modules',平台包,'bin',启动器二进制名)#可能不存在

def 授权参数(授权):
    """为一组文件系统授权构建启动器参数（`--` 分隔符之前）。授权是 dict。"""
    只读=授权['readOnly'] if 'readOnly' in 授权 else None#只读根
    读写=授权['readWrite'] if 'readWrite' in 授权 else None#可写根
    参数=[]#累积 argv
    只读路径列表=只读 if 只读 is not None else []#缺席当空
    读写路径列表=读写 if 读写 is not None else []#缺席当空
    for 根 in 只读路径列表:#只读根在前，调用方顺序
        参数.extend(['--ro',根])#--ro <path>
    for 根 in 读写路径列表:#可写根随后
        参数.extend(['--rw',根])#--rw <path>
    return 参数#授权参数表

def 探测(启动器=None,选项=None):
    """跑 `landlock-run --probe`：仅当内核真正强制时退出 0。返回 `'full' | 'partial' | 'unusable'`。选项是 dict。"""
    if 启动器 is None:#默认解析本宿主路径
        启动器=启动器路径()#已解析路径
    if 选项 is None:#默认选项
        选项={}#空映射
    if 'timeoutMs' in 选项:#调用方给了超时
        超时毫秒=选项['timeoutMs']#毫秒
    else:
        超时毫秒=2000#默认 2 秒
    try:
        结果=subprocess.run(#同步探测
            [启动器,'--probe'],#探测 argv
            timeout=(超时毫秒/1000.0) if 超时毫秒 else None,#毫秒转秒
            capture_output=True,#捕获输出
            text=True,#文本
            stdin=subprocess.DEVNULL,#关掉 stdin
        )#run 结束
    except (FileNotFoundError,PermissionError,subprocess.TimeoutExpired,OSError):
        return 'unusable'#与无强制内核同裁决
    if 结果.returncode!=0:#非零则不可用
        return 'unusable'#不可用
    输出=结果.stdout if 结果.stdout is not None else ''#探测报告
    if 部分强制报告.search(输出):#部分强制标记
        return 'partial'#按 ABI 部分
    return 'full'#完整强制
