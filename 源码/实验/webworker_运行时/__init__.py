"""WebWorker 运行时（实验）。公开面仅中文名。

浏览器 Worker 与 Node 垫片混合；Python 侧保留服务骨架，完整运行时仍由 TS 包承载。
"""
名称='webworker-runtime'#插件名
注入=[]#组合决定
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象,配置):pass#由上游 webworker-runtime 接线

apply=应用#入口
