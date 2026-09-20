import os,tempfile,subprocess,shutil#环境、临时目录、子进程与清理
from .智能体轮次 import 驱动夹具轮次#再导出轮次驱动

代理环境名=(
    'http_proxy','HTTP_PROXY','https_proxy','HTTPS_PROXY',
    'no_proxy','NO_PROXY','all_proxy','ALL_PROXY',
)

__all__=[
    '驱动夹具轮次','加载器冒烟测试超时毫秒','示例模式环境名','清代理环境',
    '解析示例模式','解析示例启动','运行加载器冒烟','应用',
]

默认进程超时毫秒=30_000#子进程诊断超时
加载器冒烟测试超时毫秒=默认进程超时毫秒+15_000#测试超时
示例模式环境名='DSH_EXAMPLE_MODE'#模式环境名
def 清代理环境():#为子进程清掉代理名
    """返回把全部代理环境名置为 None 的覆盖表。"""
    return {名:None for 名 in 代理环境名}

def 解析示例模式(原始=None):#解析启动模式
    """从原始字符串解析示例模式；缺席默认 src。"""
    if 原始 is None:#缺省读环境
        原始=os.environ.get(示例模式环境名)#读环境
    if 原始 is None or 原始=='' or 原始=='src':#源模式
        return 'src'#开发/默认
    if 原始=='lib':#已构建
        return 'lib'#已构建
    raise Exception(f"{示例模式环境名} 必须是 'src' 或 'lib'，实际为 {原始!r}")

def 派生库入口(源入口):#从源 bin 派生 lib bin
    """从 `<pkg>/src/<name>.ts` 派生 `<pkg>/lib/<name>.js`。"""
    标记长=len('/src/')#路径段长度
    切点=max(源入口.rfind('/src/'),源入口.rfind('\\src\\'))#定位 src 段
    if 切点==-1:#路径非法
        raise Exception('解析示例启动: 源入口缺少 /src/ 段')
    分隔=源入口[切点:切点+1]#路径分隔符
    尾部=源入口[切点+标记长:]#尾部
    if 尾部.endswith('.ts'):#改 js
        尾部=尾部[:-3]+'.js'#替换扩展
    return f'{源入口[:切点]}{分隔}lib{分隔}{尾部}'#拼出 lib 路径

def 解析示例启动(选项):#解析如何 spawn 示例 bin
    """按所选模式解析 spawn 命令、参数与环境。"""
    if 'mode' not in 选项:#缺省
        模式=解析示例模式()#解析环境
    else:
        模式=选项['mode']#模式
    配置参数=选项.get('configArgs') or []#配置参数
    环境={**清代理环境(),**(选项.get('env') or {})}#清代理后叠加
    if 模式=='src':#源模式
        if 'tsconfigPath' not in 选项:#缺 tsconfig
            raise Exception("resolveExampleLaunch: 'src' 模式需要 tsconfigPath 才能建立工作区路径表。")#缺 tsconfig
        #Python 侧无 tsx；保留 --import 形态供对照，实际命令仍为当前解释器入口
        源导入=选项.get('sourceImport')#tsx 导入形态
        钩子='tsx/esm' if 源导入=='tsx/esm' else 'tsx'#钩子名
        环境['TSX_TSCONFIG_PATH']=选项['tsconfigPath']#告知 tsconfig
        return {#src 启动
            'command':os.environ.get('NODE') or 'node',#Node 二进制
            'args':['--import',钩子,选项['srcBin'],*配置参数],#参数向量
            'env':环境,#环境
        }#返回
    库入口=选项.get('libBin') or 派生库入口(选项['srcBin'])#lib 入口
    return {'command':os.environ.get('NODE') or 'node','args':[库入口,*配置参数],'env':环境}#lib 启动

def 运行加载器冒烟(选项):#运行真实 Loader 冒烟
    """从隔离 cwd 启动一棵真实 Loader 树，关闭 stdin，等待干净退出。"""
    父目录=选项.get('tempDirParent') or tempfile.gettempdir()#临时父目录
    工作目录=tempfile.mkdtemp(prefix=选项['tempDirPrefix'],dir=父目录)#隔离 cwd
    进程超时=选项.get('processTimeoutMs') or 默认进程超时毫秒#进程超时
    try:#主路径
        准备=选项.get('prepare')#可选准备
        if 准备 is not None:#有准备
            准备(工作目录)#运行准备
        模式覆盖={}#可选模式
        if 'mode' in 选项 and 选项['mode'] is not None:#显式模式
            模式覆盖={'mode':选项['mode']}#写入
        启动=解析示例启动({#解析启动
            'srcBin':选项['binScript'],#源 bin
            'libBin':选项.get('libBinScript'),#可选 lib bin
            'configArgs':选项.get('binArgs') or [选项['configPath']],#配置参数
            **模式覆盖,#可选模式
            'tsconfigPath':选项['tsconfigPath'],#tsconfig
            'env':{#环境
                'DSH_HOME':os.path.join(工作目录,'.dsh'),#隔离 home
                'DSH_AGENTS_HOME':os.path.join(工作目录,'.agents'),#隔离 agents
                **(选项.get('env') or {}),#调用方覆盖
            },#环境结束
        })#解析启动
        结果=subprocess.run(#运行子进程
            [启动['command'],*启动['args']],#命令行
            cwd=工作目录,#工作目录
            env={**os.environ,**{键:值 for 键,值 in 启动['env'].items() if 值 is not None}},#合并环境并去掉 None
            input='',#关闭 stdin
            text=True,#文本模式
            capture_output=True,#捕获输出
            timeout=进程超时/1000,#超时秒
        )#运行结束
        if 'expectedExitCode' not in 选项:#缺省零
            期望退出=0#成功
        else:
            期望退出=选项['expectedExitCode']#期望码
        if 结果.returncode!=期望退出:#退出码不符
            raise Exception(f"{选项['label']} 退出码 {结果.returncode}（期望 {期望退出}）。标准输出:\n{结果.stdout}\n标准错误:\n{结果.stderr}")
        检查=选项.get('inspect')#可选检查
        if 检查 is not None:#有检查
            检查(工作目录)#运行检查
        return {'stdout':结果.stdout,'stderr':结果.stderr}#返回输出
    except subprocess.TimeoutExpired as 超时错误:#超时
        标准出=超时错误.stdout or ''#stdout
        标准错=超时错误.stderr or ''#stderr
        raise Exception(f"{选项['label']} 未在 {进程超时/1000} 秒内退出。标准输出:\n{标准出}\n标准错误:\n{标准错}") from 超时错误
    finally:#无论成败
        shutil.rmtree(工作目录,ignore_errors=True)#清理临时目录

def 应用(上下文):#测试支持入口
    """冒烟包由 harness 直接调用，无 Cordis 挂载面。"""
    return#空 apply

apply=应用
