"""注册 `sessionStats` 投影单元。"""
from .投影 import 会话统计投影定义

包名='@deepseek-ai/dsh-session-stats'
名称='session-stats'
依赖=['sessionProjections']

__all__=['包名','名称','依赖','应用','默认']

def 应用(上下文):
    """向 sessionProjections 登记 sessionStats 单元。"""
    上下文.sessionProjections.登记(会话统计投影定义)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
