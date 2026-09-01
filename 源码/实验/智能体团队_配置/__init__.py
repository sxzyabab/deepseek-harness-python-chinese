"""智能体团队配置 profile（实验）。公开面仅中文名。"""
名称='agent-team-profile'#插件名
注入=['agentTeam']#依赖团队服务
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象,配置):#加载团队配置
    pass#由上游 profile 模块接线

apply=应用#Cordis 插件入口
