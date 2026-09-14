from buffer import Buffer,kMaxLength#feross buffer包

__all__=['Buffer','kMaxLength','constants','__esModule','default']#Node面

globals()['Buffer']=Buffer#安装全局Buffer

constants={#大小常量
    'MAX_LENGTH':kMaxLength,#最大字节长度
    'MAX_STRING_LENGTH':536_870_888,#最大字符串长度
}#constants结束

__esModule=True#CJS互操作
default={'Buffer':Buffer,'constants':constants,'kMaxLength':kMaxLength}#默认导出
