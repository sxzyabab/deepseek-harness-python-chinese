"""Dedicated Web Worker 入口。本应用拥有的 Node 兼容层以模块表与捕获的请求
监听器形式交给宿主装配；装配拥有其余一切（process 全局、VFS 镜像、
Cordis 树、隧道服务器）。

装配存在之前需要基础镜像与所选 overlays；它们经隧道开局 `init` 帧到达。
本束不从自身 URL 读取任何东西，因此部署决定每个归档放在何处。
`init` 之前的消息在此排队；boot 期间的请求在宿主内排队。

对齐上游 `webworker-runtime/src/worker.ts`。公开面仅中文名。
"""
from .工作者宿主 import 创建工作者宿主#宿主装配工厂
from .node.builtins import 创建节点内置,替换前缀表#内建表与前缀
from .node.builtin_modules.implemented.async_hooks import als因果,在异步上下文根运行#ALS因果与根派发
from .node.builtin_modules.implemented.http import 当请求监听器#请求监听器
from .node.globals.定时器 import 安装定时器全局#定时器全局
from .node.globals.进程 import 安装进程全局#process全局
from .node.globals.密码学 import 安装密码学全局#crypto全局
from .polyfill.async_context.异步上下文钩子 import 安装异步上下文钩子#平台钩子
from .shell.process.协议 import 是否shell启动帧#shell启动帧判定
from .shell.process.宿主 import 运行shell进程#shell进程宿主

__all__=[]#入口无导出；副作用装配

安装异步上下文钩子()#安装ALS钩子
安装定时器全局()#安装定时器
安装密码学全局()#安装crypto

_宿主=None#已装配宿主
_shell角色=False#是否shell角色
_排队=[]#init前排队消息

def 处理消息(数据):#消息入口
    """worker 消息入口；对齐 self.addEventListener('message')。"""
    global _宿主,_shell角色#可变槽
    if _宿主 is None and 是否shell启动帧(数据):#shell启动
        _shell角色=True#标记角色
        安装进程全局({'cwd':数据['cwd'],'env':数据['env']})#安装最小process
        运行shell进程(数据,{'postMessage':lambda 帧:None,'addEventListener':lambda *位置参数:None,'close':lambda:None})#跑shell；作用域由宿主注入
        return#结束
    if _宿主 is None and isinstance(数据,dict) and 数据.get('t')=='init':#开局init
        if not isinstance(数据.get('image'),str):#镜像URL缺失
            raise Exception('webworker: init frame needs a string image url')#拒绝
        覆盖层=数据.get('overlays')#overlays
        if not isinstance(覆盖层,list) or any(not isinstance(层,str) for 层 in 覆盖层):#overlays非法
            raise Exception('webworker: init frame needs an array of string overlay urls')#拒绝
        已建=创建工作者宿主({#装配宿主
            'staticModules':创建节点内置(),#内建模块表
            'staticModulePrefixes':替换前缀表,#前缀代理
            'requestListener':当请求监听器,#HTTP监听器
            'alsCausality':als因果,#ALS因果面
            'image':数据['image'],#镜像URL
            'overlays':覆盖层,#overlay URL列表
        })#装配结束
        _宿主=已建#保存宿主
        for 已排 in _排队:#冲刷排队
            在异步上下文根运行(lambda 载=已排:已建['handleMessage'](载))#根上下文派发
        _排队.clear()#清空队列
        try:#启动树
            已建['start']()#启动
        except Exception:#start已通过tunnel.fail报告
            pass#丢弃重复噪声
        return#结束
    if _宿主 is None:#尚未装配
        if _shell角色:#shell交还给专用监听
            return#结束
        _排队.append(数据)#排队待init
        return#结束
    就绪=_宿主#已就绪宿主
    在异步上下文根运行(lambda:就绪['handleMessage'](数据))#根上下文派发
