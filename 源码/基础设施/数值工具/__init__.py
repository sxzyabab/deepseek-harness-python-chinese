def 十六进制(数据:int|bytes|bytearray):
    if isinstance(数据, int):
        return hex(数据)
    elif isinstance(数据,bytes):
        return 数据.hex()
    elif isinstance(数据, bytearray):
        return 数据.hex()
    raise TypeError("数据类型错误")