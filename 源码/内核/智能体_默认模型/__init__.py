from ...依赖 import cordis
from ...依赖.schemastery import 字符串字段
服务=cordis.服务
from ...模型后端.llm import 推理力度标识
from .类型 import 智能体默认模型设置,插件配置

__all__=(
    '智能体默认模型设置','插件配置',
    '投影选择','智能体默认模型配置',
)

def 投影选择(设置):
    """把配置上的默认模型投影为 Agent 侧选择类型。"""
    结果={'provider':设置['provider'],'model':设置['model']}
    if 'reasoningEffort' in 设置 and 设置['reasoningEffort'] is not None:
        结果['reasoningEffort']=推理力度标识(设置['reasoningEffort'])
    return 结果

class 智能体默认模型配置(服务):
    """独立于任何 Host 或传输拥有默认模型选择。每次操作读拥有配置。"""
    配置={
        'provider':字符串字段(可空=False),
        'model':字符串字段(可空=False),
        'reasoningEffort':字符串字段(),
    }

    def __init__(自身,上下文,配置):
        """构造默认模型配置服务，登记为 ctx.agentDefaultModel。"""
        super().__init__(上下文,'agentDefaultModel')
        自身.拥有上下文=上下文
        自身.配置=配置
        def 挂设置(子上下文):
            """settings 出现后关闭自动生成。"""
            def 配置自动():
                """写 auto:false。"""
                子上下文.settings.configure({'auto':False},上下文.纤程)
                return lambda: None
            子上下文.副作用(配置自动,'agent-default-model: settings auto')
        上下文.依赖启动(['settings'],挂设置)

    def 当前选择(自身):
        """读取当前默认模型选择。"""
        配置=自身.配置
        力度=配置['reasoningEffort'] if 'reasoningEffort' in 配置 else None
        设置={'provider':配置['provider'],'model':配置['model']}
        if 力度 is not None:
            设置['reasoningEffort']=力度
        return 投影选择(设置)

    def 保存选择(自身,下一选择):
        """保存完整默认模型选择。没有配置编辑器的部署保留组合入口。"""
        入口=自身.拥有上下文.纤程.插件配置
        if 入口 is None:
            return
        编辑器=自身.所属上下文.获取服务('configEditor')
        if 编辑器 is None:
            return
        段落={'provider':下一选择['provider'],'model':下一选择['model']}
        if 'reasoningEffort' in 下一选择 and 下一选择['reasoningEffort'] is not None:
            段落['reasoningEffort']=str(下一选择['reasoningEffort'])
        def 写出(当前,继承):
            """交出完整下一份配置。"""
            return 段落
        编辑器.编辑(入口,写出)

智能体默认模型配置.Config=智能体默认模型配置.配置
default=智能体默认模型配置
