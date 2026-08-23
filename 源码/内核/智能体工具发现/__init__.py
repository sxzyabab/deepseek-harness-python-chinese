"""Agent 平面展示选择器：Agent 预设携带的一行，声明模型看到其工具的哪种形态。

工具注册表本身留在宿主平面——Agent 循环调度器、API 代理的展示器、以及每个工具插件都是它的消费方，因此不能搬进预设。
预设能拥有的是展示：`ctx.tools.呈现为()` 为挂载作用域声明它，而这正是预设的常驻挂载，因此该声明覆盖加入该预设的每个 Agent，Code Mode 预设可与原生预设同进程并存。每个组合一行，而不是每个会话一行。

Code Mode 需要代码运行时（宿主平面服务）。因此本行等待该服务而不是假定它存在：在未组合运行时的部署上选择 Code Mode 的预设会在挂载时失败，并出现在该预设自己的激活审计里，而不是第一次提示时才失败。

对齐上游 `@deepseek-ai/dsh-agent-tool-presentation`。公开面仅中文名。配置键与模式字面量保持上游字面量。
"""
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#导入配置模式库
from .类型 import 工具展示模式,插件配置#再导出结构类型

名称='tool-presentation'#Cordis 插件名（字面量）
注入=['tools']#必需服务；不列出 codeRuntime：native 行必须能在未组合运行时的部署上挂载，按模式等待改在 应用 内声明
name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖声明槽

配置模式=模式.对象({#运行时配置模式：mode 必填而非给默认——部署默认就是没有本行的预设已经得到的东西，省略取值等于白组合这一行
    'mode':模式.联合(['native','code','both']).必填(),#native 发全部可见模式；code 只发 run_code 外加生成 SDK；both 两者都发
})#配置模式
Config=配置模式#Cordis Config 槽

def 应用(上下文对象,配置):#为本组合覆盖的每个 Agent 声明工具展示
    """为本组合覆盖的每个 Agent 声明工具展示。挂载组合的作用域上下文即预设的常驻作用域；`呈现为` 本身就是 effect，本行拆除时声明一并解开，无需第二层包装。"""
    模式值=配置['mode'] if isinstance(配置,dict) else 配置.mode#所选展示（字面量 native|code|both）
    if 模式值=='native':#原生模式无需代码运行时
        上下文对象.tools.呈现为('native')#声明原生展示
        return#挂载完成
    def 在运行时(运行时上下文,*位置参数):#等到代码运行时后声明展示
        """等到 `codeRuntime` 后在运行时作用域声明展示。等待即大声失败：仍挂在其上的条目会被 agent-presets 报成不可用行，并点名本 id。"""
        运行时上下文.tools.呈现为(模式值)#在运行时作用域声明展示
    上下文对象.inject(['codeRuntime'],在运行时)#等到代码运行时；未组合则停在等待，预设激活审计会点名本行

apply=应用#Cordis 插件入口槽

__all__=('名称','注入','配置模式','应用','工具展示模式','插件配置')#仅中文公开名
