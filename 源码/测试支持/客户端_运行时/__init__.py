"""测试用客户端运行时 Remote 投影。公开面仅中文名。"""
名称='client-runtime-test'#插件名
注入=['client']#依赖
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象):pass#由上游 client-runtime 接线

apply=应用#入口
