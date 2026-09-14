__all__=['是否终端','isatty','__esModule','default']#中文与Node面

def 是否终端(描述符):#检测是否终端
    """测试数字文件描述符是否指向终端；Worker 中恒为 false。"""
    return False#Worker无终端fd

isatty=是否终端#Node面
__esModule=True#CJS互操作
default={'isatty':是否终端}#默认导出
