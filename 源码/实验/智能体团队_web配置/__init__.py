"""智能体团队 Web 配置（实验）。公开面仅中文名。"""
名称='agent-team-web-profile'#插件名
注入=['agentTeam']#依赖
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象,配置):pass#由上游 web-profile 接线

apply=应用#入口
