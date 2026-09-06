"""无会话级选择时，Agent 使用的默认模型选择。

对齐上游 `agent-default-model/src/index.ts`。公开面仅中文名；设置文档键与 Cordis 服务槽名（`agentDefaultModel`）保持上游字面量。
"""
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段#配置字段
服务=cordis.服务#导入 Cordis 服务基类
from ...模型后端.llm import 推理力度标识#导入推理力度品牌
from ...配置.配置 import 安装设置段,设置命名空间#导入设置段安装与命名空间
from .类型 import 智能体默认模型设置,插件配置#再导出设置与插件配置结构类型

智能体默认模型设置命名空间=设置命名空间('agent-default-model')#默认模型设置命名空间（kebab 字面量不译）

智能体默认模型设置模式={#Settings 分节模式；含可选推理力度，与智能体默认模型设置字段对齐
    'provider':字符串字段(可空=False),#提供方路由必填（Settings 文档键字面量）
    'model':字符串字段(可空=False),#模型 id 必填（Settings 文档键字面量）
    'reasoningEffort':字符串字段(),#推理力度可选；故意不进插件配置，便于整节替换时清除
}#设置模式结束

__all__=(#仅中文公开名；无英文别名
    '智能体默认模型设置命名空间','智能体默认模型设置模式',
    '智能体默认模型设置','插件配置',
    '投影选择','智能体默认模型配置',
)#公开面结束

def 投影选择(设置):
    """把已存储并参与组合的默认模型设置投影为 Agent 侧选择类型。有 reasoningEffort 时打成推理力度品牌。"""
    结果={'provider':设置['provider'],'model':设置['model']}#脱离的提供方与模型
    if 'reasoningEffort' in 设置 and 设置['reasoningEffort'] is not None:#有力度才带上，避免空键覆盖下游缺省
        结果['reasoningEffort']=推理力度标识(设置['reasoningEffort'])#打成推理力度品牌值
    return 结果#脱离的选择，供新建 Agent 使用

class 智能体默认模型配置(服务):#独立于 Host 或传输拥有默认模型选择
    """独立于任何 Host 或传输拥有默认模型选择。没有设置提供方时组合入口仍可用；挂上提供方后实时读取其用户层。"""
    配置={#运行时插件配置；字段与插件配置对齐，不含 reasoningEffort
        'provider':字符串字段(可空=False),#提供方路由必填（组合配置键字面量）
        'model':字符串字段(可空=False),#模型 id 必填（组合配置键字面量）
    }#运行时配置模式

    def __init__(自身,上下文对象,配置):#构造默认模型配置服务
        """构造默认模型配置服务，登记为 ctx.agentDefaultModel，并安装可选 Settings 分节。"""
        super().__init__(上下文对象,'agentDefaultModel')#注册服务名（字面量不译）
        入口={'provider':配置['provider'],'model':配置['model']}#组合入口初值；故意无 reasoningEffort
        def 读入口():#无设置提供方时读入口
            """无设置提供方时读组合入口。"""
            return 入口#回退到组合入口
        自身.源=读入口#当前设置读取函数；有 Settings 后由 setSource 切换
        def 设源(当前):#切换权威读取函数
            """把权威读取切到 Settings 作用域解析值。"""
            自身.源=当前#切换为实时读取作用域 get
        def 变更():#设置文档变更钩子
            """每个消费方都经当前选择()读取，设置文档变更时无需重建注册级事实。"""
            return#无派生注册级事实可重建
        安装设置段(上下文对象,智能体默认模型设置命名空间,智能体默认模型设置模式,入口,{#可选 Settings 接线
            'setSource':设源,#钩子键保持上游字面量，供 settings 取字段
            'onChange':变更,#无派生
        })#安装结束

    def 当前选择(自身):#读取当前默认模型选择
        """读取当前默认模型选择，返回一份脱离的提供方、模型与可选推理选择。"""
        return 投影选择(自身.源())#经当前源投影，与 Settings 叠层或组合入口一致

    def 保存选择(自身,下一选择):#保存完整默认模型选择
        """保存完整默认模型选择。没有设置提供方的部署会保留其组合入口（本调用为空操作）。"""
        设置服务=自身.ctx.获取服务('settings')#可选设置服务；缺席则无法持久化
        if 设置服务 is None:#没有设置提供方
            return#保留组合入口，空操作
        段落={'provider':下一选择['provider'],'model':下一选择['model']}#整节替换的基础字段
        if 'reasoningEffort' in 下一选择 and 下一选择['reasoningEffort'] is not None:#有力度才写入，缺席即清除旧值（整节替换语义）
            段落['reasoningEffort']=str(下一选择['reasoningEffort'])#写成字符串，便于 Settings 文档层存储
        设置服务.替换(智能体默认模型设置命名空间,段落)#整节替换用户层

智能体默认模型配置.Config=智能体默认模型配置.配置#Cordis Config 槽
default=智能体默认模型配置#Cordis 默认导出槽
