from ..子智能体.错误 import 子智能体错误
默认处置eof宽限毫秒=6000
默认处置宽限毫秒=3000

def 启动acp运行(请求,规格):
    """启动 ACP 子进程并返回跑句柄。完整 ACP 线协议驱动尚未实现。"""
    raise 子智能体错误('subagent-acp: ACP wire protocol driver is not yet implemented in Python','NOT_IMPLEMENTED')

__all__=['默认处置eof宽限毫秒','默认处置宽限毫秒','启动acp运行']
