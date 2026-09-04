"""Dedicated Web Worker 入口。本应用拥有的 Node 兼容层以模块表与捕获的请求
监听器形式交给宿主装配；装配拥有其余一切。

对齐上游 `webworker-runtime/src/worker.ts`。公开面仅中文名。
"""
from .工作线程宿主 import 创建工作线程宿主#宿主装配工厂
#对齐上游预装：buffer / async_hooks / timers / crypto / builtins / http / shell
#本批次未迁 node/ 与 shell/；入口保留装配顺序与消息分派。

__all__=['安装工作线程入口']#仅中文公开名

def 安装工作线程入口(#工作线程入口
    创建内建=None,#createNodeBuiltins
    替换前缀=None,#REPLACED_PREFIXES
    请求监听器=None,#whenRequestListener
    als因果=None,#alsCausality
    在异步上下文根运行=None,#runAtAsyncContextRoot
    安装异步上下文钩子=None,#installAsyncContextHooks
    安装定时器全局=None,#installTimerGlobals
    安装crypto全局=None,#installCryptoGlobals
    安装process全局=None,#installProcessGlobal
    是否shell启动帧=None,#isShellStartFrame
    跑shell进程=None,#runShellProcess
    自身=None,#worker global scope
):
    """安装消息入口：init 前排队，shell 角色分派，装配后根上下文派发。"""
    if 安装异步上下文钩子 is not None:#在timer全局之前
        安装异步上下文钩子()#安装ALS钩子
    if 安装定时器全局 is not None:#安装定时器
        安装定时器全局()#安装
    if 安装crypto全局 is not None:#安装crypto
        安装crypto全局()#安装
    宿主=[None]#已装配宿主
    shell角色=[False]#是否shell角色
    排队=[]#init前排队消息
    作用域=自身 if 自身 is not None else globals()#全局作用域

    def 收消息(事件):#消息入口
        """按角色与 init 帧分派。"""
        数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',事件)#载荷
        if 宿主[0] is None and 是否shell启动帧 is not None and 是否shell启动帧(数据):#shell启动
            shell角色[0]=True#标记角色
            if 安装process全局 is not None:#安装最小process
                安装process全局({'cwd':数据.get('cwd'),'env':数据.get('env')})#安装
            if 跑shell进程 is not None:#跑shell命令
                跑shell进程(数据,作用域)#跑
            return#结束
        if 宿主[0] is None and isinstance(数据,dict) and 数据.get('t')=='init':#开局init
            if not isinstance(数据.get('image'),str):#镜像URL缺失
                raise Exception('webworker: init frame needs a string image url')#拒绝
            覆盖层=数据.get('overlays')#overlays
            if not isinstance(覆盖层,list) or any(not isinstance(层,str) for 层 in 覆盖层):#overlays非法
                raise Exception('webworker: init frame needs an array of string overlay urls')#拒绝
            创建=创建工作线程宿主({#装配宿主
                'staticModules':创建内建() if callable(创建内建) else {},#内建模块表
                'staticModulePrefixes':替换前缀 or {},#前缀代理
                'requestListener':请求监听器,#HTTP监听器
                'alsCausality':als因果,#ALS因果面
                'image':数据['image'],#镜像URL
                'overlays':覆盖层,#overlay URL列表
            })#装配结束
            宿主[0]=创建#保存宿主
            for 已排 in 排队:#冲刷排队
                if callable(在异步上下文根运行):#根上下文派发
                    在异步上下文根运行(lambda 消=已排,主=创建:主.handleMessage(消) if hasattr(主,'handleMessage') else 主['handleMessage'](消))#派发
                else:#直接派发
                    (创建.handleMessage if hasattr(创建,'handleMessage') else 创建['handleMessage'])(已排)#派发
            排队.clear()#清空队列
            启动=创建.start if hasattr(创建,'start') else 创建.get('start')#启动
            if callable(启动):#有启动
                启动()#启动树；失败由tunnel.fail报告
            return#结束
        if 宿主[0] is None:#尚未装配
            if shell角色[0]:#shell交还给专用监听
                return#结束
            排队.append(数据)#排队待init
            return#结束
        就绪=宿主[0]#已就绪宿主
        def 派发():#根上下文派发
            """派发消息。"""
            (就绪.handleMessage if hasattr(就绪,'handleMessage') else 就绪['handleMessage'])(数据)#派发
        if callable(在异步上下文根运行):#根上下文
            在异步上下文根运行(派发)#派发
        else:#直接
            派发()#派发

    加监听=作用域.get('addEventListener') if isinstance(作用域,dict) else getattr(作用域,'addEventListener',None)#监听API
    if callable(加监听):#有监听器
        加监听('message',收消息)#挂处理器
    return 收消息#返回入口供测试
