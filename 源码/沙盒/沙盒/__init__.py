'同机进程隔离服务：在宿主路径文件政策下包装精确子进程 argv'
from ...依赖 import cordis
服务=cordis.服务
from .升级 import (
    更宽模式,
    升级目标,
    升级结果,
    升级审批方字段,
    升级审批字段,
    升级请求字段,
    校验升级参数,
    沙箱拒绝标记,
    升级提示标记,
    批准升级,
)
from .异常 import 沙箱不可用错误,沙箱升级错误
from .根 import 规范路径,可写根
from ...工具.超时 import 若已中止则抛出
from .诊断 import 分类运行器失败,是否运行器派生失败,匹配签名

沙箱模式=('read-only','workspace-write','danger-full-access')
隔离沙箱模式=('read-only','workspace-write')
执行政策字段=('mode','workspaceRoot','sessionId')
沙箱强制=('full','partial')
隔离政策字段=('mode','workspaceRoot','sessionId')
运行器失败规则字段=('allowedExitCodes','fatalSignatures','informationalLines')
已隔离参数表字段=('argv','enforcement','denialSignatures','runnerFailureRules')
沙箱不可用码='SANDBOX_UNAVAILABLE'

class 沙箱提供方(服务):
    """抽象进程沙箱服务。
    隔离必须返回强制 argv，或在包装或运行器执行时失败即关闭；禁止静默的未隔离透传
    """
    def __init__(自身,上下文):
        '登记为 sandbox'
        super().__init__(上下文,'sandbox')

    def 隔离(自身,参数表,政策,信号=None):
        """包装 argv 使它在本宿主上按政策隔离执行；调用方用返回的 argv 代替自己的去 spawn。
        参数表是精确 argv，不是 shell 字符串；政策按次携带。
        信号在解析政策与运行器期间取消
        """
        若已中止则抛出(信号)
        raise NotImplementedError('SandboxProvider.confine')

__all__=[
    '沙箱提供方','沙箱不可用错误','沙箱升级错误','沙箱不可用码','沙箱模式','隔离沙箱模式',
    '执行政策字段','沙箱强制','隔离政策字段','运行器失败规则字段','已隔离参数表字段',
    '规范路径','可写根','更宽模式','升级目标','升级结果','校验升级参数','批准升级',
    '沙箱拒绝标记','升级提示标记',
    '分类运行器失败','是否运行器派生失败','匹配签名',
]
default=沙箱提供方
