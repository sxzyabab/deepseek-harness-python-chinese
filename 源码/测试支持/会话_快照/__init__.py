"""会话快照测试工具。公开面仅中文名。"""
__all__=['应用','apply','加载快照','规范化快照']#仅中文公开名

def 加载快照(路径):#从目录加载会话快照
    raise NotImplementedError('session-snapshot')#由上游 harness 接线

def 规范化快照(快照):#规范化快照用于对比
    raise NotImplementedError('normalize snapshot')#由上游 normalize 接线

def 应用(上下文对象):pass#测试支持

apply=应用#入口
