"""注册 `turnOutline` 投影单元（对齐上游 session-turn-outline）。"""
from .投影 import 轮次大纲投影定义#投影定义
名称='session-turn-outline'#Cordis 插件名
注入=['sessionProjections']#依赖投影注册表
name=名称#Cordis 插件名
inject=注入#Cordis 依赖
__all__=['名称','注入','应用','默认','轮次大纲投影定义']#仅中文公开名

def 应用(上下文):#登记投影单元
    """在 ctx.sessionProjections 上登记 turnOutline 单元。"""
    上下文.sessionProjections.register(轮次大纲投影定义)#登记

apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
默认=应用#中文默认导出
