"""注册 `turnOutline` 投影单元。"""
from .投影 import 轮次大纲投影定义

包名='@deepseek-ai/dsh-session-turn-outline'
名称='session-turn-outline'
依赖=['sessionProjections']

__all__=['包名','名称','依赖','应用','默认','轮次大纲投影定义']

def 应用(上下文):
    """向 sessionProjections 登记 turnOutline 单元。"""
    上下文.sessionProjections.登记(轮次大纲投影定义)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
