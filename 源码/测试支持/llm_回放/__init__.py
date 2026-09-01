"""LLM 回放驱动（测试）。公开面仅中文名。"""
__all__=['应用','apply','创建回放提供者']#仅中文公开名

def 创建回放提供者(记录路径):#从录制创建 LLM 提供者
    raise NotImplementedError('llm-replay')#由上游 index.ts 接线

def 应用(上下文对象):pass#测试支持

apply=应用#入口
