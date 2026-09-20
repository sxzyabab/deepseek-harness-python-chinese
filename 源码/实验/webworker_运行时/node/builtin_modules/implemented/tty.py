__all__=['isatty','__esModule','default']

def 是否终端(描述符):
    """测试数字文件描述符是否指向终端；Worker 中恒为 false。"""
    return False

isatty=是否终端
__esModule=True
default={'isatty':是否终端}
