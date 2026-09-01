"""WebWorker 打包器（实验）。公开面仅中文名。"""
名称='webworker-packer'#插件名
注入=[]#组合决定
__all__=['名称','注入','应用','apply']#仅中文公开名

def 应用(上下文对象,配置):pass#打包逻辑依赖 Node 工具链；Python 侧保留插件名与入口

apply=应用#入口
