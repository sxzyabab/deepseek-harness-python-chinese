"""私有 Agent Teams profile 捆。

对齐上游 `@deepseek-ai/dsh-experimental-agent-team-profile`。
本包的运行时内容是其 `dsh.bundle.patch` 文档；本模块不导出运行时 API。
公开面仅中文名。
"""
__all__=['名称','注入','应用']#仅中文公开名

名称='agent-team-profile'#插件名
注入=['agentTeam']#依赖团队服务
name=名称#Cordis 名
inject=注入#Cordis 注入

def 应用(上下文=None,配置=None):#空模块入口
    """运行时内容在 patch；本模块无宿主行为。"""
    return None#空

apply=应用#Cordis 插件入口
