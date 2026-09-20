from ...依赖.schemastery import 枚举字段
from .类型 import 工具呈现模式,插件配置

名称='tool-presentation'
依赖=['tools']#不列出 codeRuntime：native 行必须能在未组合运行时的部署上挂载，按模式等待改在 应用 内声明

配置模式={
    'mode':枚举字段('native','code','both',可空=False),#native 发全部可见模式；code 只发 run_code 外加生成 SDK；both 两者都发
}

def 应用(上下文,配置):
    """为本组合覆盖的每个 Agent 声明工具呈现。挂载组合的作用域上下文即预设的常驻作用域；`呈现为` 本身就是 effect，本行拆除时声明一并解开，无需第二层包装。"""
    模式值=配置['mode'] if isinstance(配置,dict) else 配置.mode
    if 模式值=='native':
        上下文.tools.呈现为('native')
        return
    def 在运行时(运行时上下文,*位置参数):
        """等到 `codeRuntime` 后在运行时作用域声明呈现。等待即大声失败：仍挂在其上的条目会被 agent-presets 报成不可用行，并点名本 id。"""
        运行时上下文.tools.呈现为(模式值)
    上下文.依赖启动(['codeRuntime'],在运行时)

__all__=('名称','依赖','配置模式','应用','工具呈现模式','插件配置')

name=名称
inject=依赖
Config=配置模式
apply=应用
