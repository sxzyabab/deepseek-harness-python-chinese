"""同机进程隔离能力 seam 的 Service Definition：在宿主路径文件政策下包装精确子进程 argv。容器、微虚拟机与远程执行替换的是周围的能力 seam；本服务共享宿主内核与文件系统。"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis服务基类
from ...模型后端.llm import 装备错误#导入Harness错误基类
from .升级 import (
    更宽模式,#更宽模式表
    升级目标,#可广告升级目标
    升级结果,#封闭升级结果
    升级审批方字段,#最小审批方字段
    升级审批字段,#升级审批配料
    升级请求字段,#升级请求字段
    校验升级参数,#校验升级参数
    沙箱拒绝标记,#拒绝标记
    升级提示标记,#升级提示
    批准升级,#批准升级
)#再导出升级辅助与类型字段
from .根 import 规范路径,可写根#再导出路径规范化与可写根

沙箱模式=('read-only','workspace-write','danger-full-access')#只读、工作区可写、完全放开

隔离沙箱模式=('read-only','workspace-write')#排除完全放开的隔离模式

执行政策字段=('mode','workspaceRoot','sessionId')#按次执行政策字段

沙箱强制=('full','partial')#完整或部分强制

隔离政策字段=('mode','workspaceRoot','sessionId')#隔离政策字段，mode须为隔离模式

运行器失败规则字段=('allowedExitCodes','fatalSignatures','informationalLines')#运行器失败规则字段

已隔离参数表字段=('argv','enforcement','denialSignatures','runnerFailureRules')#已隔离argv结果字段

沙箱不可用码='SANDBOX_UNAVAILABLE'#沙箱不可用码

class 沙箱不可用错误(装备错误):#沙箱不可用错误
    """隔离无法强制请求模式时抛出。经结构化错误通道携带 SANDBOX_UNAVAILABLE。"""
    def __init__(自身,模式,细节=None):#按模式与可选细节构造
        """按模式与可选细节构造。面向用户的不可用说明不翻译字面量。"""
        消息=('sandbox mode "'+模式+'" is requested but no sandbox backend is usable on this host; '
            +'refusing to run the command unconfined. Install bubblewrap or run a Landlock-enforcing '
            +'kernel (Linux), ensure sandbox-exec is usable (macOS), or ensure the ACL '
            +'restricted-token runner can start (Windows) — otherwise switch the consumer to '
            +'danger-full-access.'
            +('' if 细节 is None else ' Runner failure: '+细节))#面向用户的不可用说明
        装备错误.__init__(自身,消息,沙箱不可用码)#交给装备错误
        自身.name='SandboxUnavailableError'#固定类名

class 沙箱提供方(服务):#沙箱提供方
    """抽象进程沙箱服务。隔离必须返回强制 argv，或在包装或运行器执行时失败即关闭；禁止静默的未隔离透传。功能探测仲裁多运行器链，对唯一候选可以跳过，其自身拒绝仍是失败即关闭的终点。"""
    def __init__(自身,上下文对象):#注册为ctx.sandbox
        """注册为 ctx.sandbox。"""
        super().__init__(上下文对象,'sandbox')#服务名sandbox

    def 隔离(自身,参数表,政策):#包装为隔离argv
        """包装 argv 使它在本宿主上按政策隔离执行；调用方用返回的 argv 代替自己的去 spawn。参数表是调用方即将 spawn 的精确 argv，不是 shell 字符串；政策是本次执行所处的文件效果政策，按次携带。"""
        raise NotImplementedError('SandboxProvider.confine')#子类必须实现

默认=沙箱提供方#默认导出
default=沙箱提供方#Cordis默认导出

__all__=[#公开面
    '沙箱提供方','沙箱不可用错误','沙箱不可用码','沙箱模式','隔离沙箱模式',
    '执行政策字段','沙箱强制','隔离政策字段','运行器失败规则字段','已隔离参数表字段',
    '规范路径','可写根','更宽模式','升级目标','升级结果','校验升级参数','批准升级',
    '默认','default',
]#结束
