"""智能体团队工具（实验）。公开面仅中文名。"""
名称='tool-agent-team'#插件名
注入=['tools','agentTeam']#依赖
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象):pass#由上游 tool-agent-team 接线

apply=应用#入口
