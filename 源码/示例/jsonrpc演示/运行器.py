"""通用入口与封闭运行时 JSON-RPC 二进制共享的进程生命周期。

对齐上游 `示例/jsonrpc-demo/src/runner.ts`。公开面仅中文名。
"""
import os,sys,signal#路径存在、进程与信号
from app_boot import 启动,安装大声失败,加载环境,解析配置路径#启动粘合层

__all__=['运行JSONRPC智能体']#仅中文公开名

名称='dsh-jsonrpc-agent'#二进制诊断名前缀

def 运行JSONRPC智能体(裸模块基址=None):#跑 JSON-RPC 智能体进程
    """启动显式选定的外部配置并拥有进程退出。裸模块基址可选；配置项目自有插件包时省略。"""
    安装大声失败(名称)#安装大声失败的 Loader 守卫
    加载环境(名称)#加载 .env
    来自环境=os.environ.get('DSH_CORDIS_CONFIG')#环境给出的配置路径
    来自参数=sys.argv[2] if len(sys.argv)>2 else None#位置参数给出的配置路径
    if 来自环境 is not None and 来自环境!='':#环境非空则胜出
        请求=来自环境#用环境路径
    elif 来自参数 is not None and 来自参数!='':#否则用 argv
        请求=来自参数#argv
    else:#缺失
        请求=None#无请求
    配置路径=None if 请求 is None else 解析配置路径(请求,None)#解析为绝对路径
    if 配置路径 is None or not os.path.exists(配置路径):#未给或文件不存在
        sys.stderr.write(#写出用法
            'usage: '+名称+' <path/to/cordis.yml> (or set DSH_CORDIS_CONFIG=<path>, which wins); the config is required — there is no built-in fallback\n'
        )#结束 stderr.write
        sys.exit(1)#用法错误退出
    上下文对象=启动(名称,配置路径,None,None,裸模块基址)#启动结算树
    退出中=[False]#是否已进入退出（列表便于闭包改写）

    def 拆除并退出(码):#拆除树并以给定码退出
        """拆除 fiber 后按码退出进程。"""
        if 退出中[0]:#已在退出则忽略
            return#忽略
        退出中[0]=True#标记正在退出
        try:#拆除 fiber
            结果=上下文对象.fiber.dispose()#等待树拆除
            if hasattr(结果,'等待'):#可等待
                结果.等待()#等待
        finally:#无论拆除成败都退出
            sys.exit(码)#按码退出进程

    def 标准输入结束(_句柄=None):#EOF 正常退出
        """stdin EOF。"""
        拆除并退出(0)#以 0 退出

    def 终止信号(_号,_帧):#SIGTERM 正常退出
        """SIGTERM。"""
        拆除并退出(0)#以 0 退出

    def 中断信号(_号,_帧):#SIGINT 以 130 退出
        """SIGINT。"""
        拆除并退出(130)#以 130 退出

    try:#挂 stdin EOF（Windows 下可能无）
        import threading#后台读
        def 监视标准输入结束():#监视 EOF
            """阻塞读到 EOF。"""
            try:#读尽 stdin
                sys.stdin.read()#读到结束
            except Exception:#读失败
                pass#忽略
            标准输入结束()#触发退出
        threading.Thread(target=监视标准输入结束,daemon=True).start()#后台监视
    except Exception:#挂载失败
        pass#忽略
    if hasattr(signal,'SIGTERM'):#有 SIGTERM
        signal.signal(signal.SIGTERM,终止信号)#登记
    if hasattr(signal,'SIGINT'):#有 SIGINT
        signal.signal(signal.SIGINT,中断信号)#登记
