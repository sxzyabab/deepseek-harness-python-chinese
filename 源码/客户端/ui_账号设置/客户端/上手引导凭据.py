'桌面登录桥报告有没有配置过模型密钥'
from ...模块.客户端.通告 import 取握手窗口

__all__=['读上手引导密钥']

def 读上手引导密钥():
    '读和原生登录同一份安全事实。没有桌面桥就失败'
    窗口=取握手窗口()
    桥=getattr(窗口,'dshOnboarding',None)
    if 桥 is None:
        raise RuntimeError('desktop login bridge unavailable')
    return 桥.hasApiKey()
