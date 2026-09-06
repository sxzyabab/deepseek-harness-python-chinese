"""ACP 子智能体跑生命周期（对齐 upstream subagent-acp/run.ts 骨架）。"""
from ..子智能体.错误 import 子智能体错误#缝内失败
默认处置eof宽限毫秒=6000#EOF 宽限
默认处置宽限毫秒=3000#处置宽限

def 启动acp跑(请求,规格):
    """启动 ACP 子进程并返回跑句柄。完整 ACP 线协议驱动尚未实现。"""
    raise 子智能体错误('subagent-acp: ACP wire protocol driver is not yet implemented in Python','NOT_IMPLEMENTED')#待实现

__all__=['默认处置eof宽限毫秒','默认处置宽限毫秒','启动acp跑']#公开面
