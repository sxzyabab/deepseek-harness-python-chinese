"""私有 Web profile 层，挂载 Agent Teams 客户端插件。

对齐上游 `@deepseek-ai/dsh-experimental-agent-team-web-profile`。
本模块不导出运行时 API。公开面仅中文名。
"""
__all__=['名称','注入','应用']#仅中文公开名

名称='agent-team-web-profile'#插件名
注入=['agentTeam']#依赖
name=名称#Cordis 名
inject=注入#Cordis 注入

def 应用(上下文=None,配置=None):#空模块入口
    """运行时内容在 patch；本模块无宿主行为。"""
    return None#空

apply=应用#入口
