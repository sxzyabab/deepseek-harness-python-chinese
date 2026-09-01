"""客户端 UI：智能体团队（实验）。公开面仅中文名。

上游含 React 组件；Python 侧仅保留 Cordis 客户端插件骨架，UI 由 TS 客户端承载。
"""
名称='client-ui-agent-team'#插件名
注入=['client']#依赖客户端
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象):pass#客户端 UI 在 TS 侧实现

apply=应用#入口
