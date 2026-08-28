"""对话注册表包子路径导出。

对齐上游 `runtime/src/client/conversation/`。公开面仅中文名。
"""
from .定义注册表 import 会话定义注册表#基类
from .事件注册表 import 会话事件注册表#事件注册表
from .视图注册表 import 会话视图注册表#视图注册表

__all__=['会话定义注册表','会话事件注册表','会话视图注册表']#仅中文公开名
