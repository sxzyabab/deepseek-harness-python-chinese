"""LLM 模拟 HTTP 服务器（测试）。公开面仅中文名。"""
__all__=['应用','apply','启动模拟服务器']#仅中文公开名

def 启动模拟服务器(选项=None):#启动本地 mock LLM 服务器
    raise NotImplementedError('llm-mock-server')#由上游实现

def 应用(上下文对象):pass#测试包通常由 harness 直接调用

apply=应用#入口
