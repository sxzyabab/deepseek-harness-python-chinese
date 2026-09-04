"""测试加载具体智能体循环前所需服务的共享挂载。

调用方仍拥有上下文、循环、适配器、可选插件与拆除。
对齐上游 `agent-loop-testkit/src/index.ts`。公开面仅中文名。
"""
from ...模型后端.llm import 默认 as 语言模型运行时#LLM运行时插件
from ...内核.会话 import 默认 as 会话存储#会话存储插件
from ...内核.系统提示词 import 默认 as 系统提示词#系统提示词插件
from ...内核.工具 import 默认 as 工具运行时#工具运行时插件
from ...内核.智能体 import 默认 as 智能体注册表#智能体注册表插件

__all__=['挂载智能体循环测试依赖','应用']#仅中文公开名

def 挂载智能体循环测试依赖(上下文,选项=None):#挂载智能体循环测试依赖
    """为 AgentLoop 测试挂载标准先决服务。

    故意不挂载 AgentLoop、也不注册适配器，使测试保留加载顺序与待测拓扑的控制权。
    上下文拥有每一个已挂载服务并负责释放。
    """
    if 选项 is None:#缺省选项
        选项={}#空映射
    系统配置=选项.get('systemPrompt')#系统提示词配置
    工具配置=选项.get('tools')#工具配置
    上下文.plugin(语言模型运行时)#挂载LLM运行时
    上下文.plugin(会话存储)#挂载会话存储
    上下文.plugin(系统提示词,{} if 系统配置 is None else 系统配置)#挂载系统提示词
    上下文.plugin(工具运行时,{} if 工具配置 is None else 工具配置)#挂载工具运行时
    上下文.plugin(智能体注册表)#挂载智能体注册表

def 应用(上下文对象,选项=None):#Cordis入口
    """挂载先决服务（测试工具包通常由 harness 直接调用挂载函数）。"""
    挂载智能体循环测试依赖(上下文对象,选项)#委托挂载

apply=应用#入口
mountAgentLoopTestDependencies=挂载智能体循环测试依赖#上游名
