"""Codex app-server 一次性生命周期（对齐 upstream subagent-codex/run.ts 骨架）。"""
import uuid#子 id
from ...内核.会话 import 会话标识#品牌
默认处置宽限毫秒=3000#宽限

def 启动codex跑(请求,规格):#startCodexRun 骨架
    """驱动 @openai/codex app-server。Python 侧待官方包绑定。"""
    try:
        import openai#仅占位检测
    except ImportError as 错误:
        raise Exception('subagent-codex: @openai/codex Python package is required: '+str(错误))#阻塞
    子标识=会话标识(str(uuid.uuid4()))#子 id
    raise Exception('subagent-codex: Codex app-server wire driver is not yet implemented in Python')#待实现

__all__=['默认处置宽限毫秒','启动codex跑']#公开面
