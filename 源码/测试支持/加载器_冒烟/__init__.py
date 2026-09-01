"""加载器冒烟测试插件。公开面仅中文名。"""
名称='loader-smoke'#插件名
注入=[]#组合
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象):pass#由上游 loader-smoke 接线

apply=应用#入口
