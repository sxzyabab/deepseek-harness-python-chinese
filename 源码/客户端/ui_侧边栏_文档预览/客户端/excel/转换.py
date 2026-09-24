from .错误 import 表格预览错误
from .xlsx import 转换xlsx
from .xls import 转换xls
from .分隔文本 import 转换分隔文本

__all__=['转换excel']

def 转换excel(字节,格式,上限):
    """按后缀解码工作簿，不重算已存公式。"""
    if len(字节)>上限['maxBytes']:
        raise 表格预览错误('tooLarge')
    if 格式=='xlsx':
        return 转换xlsx(字节,上限)
    if 格式=='xls':
        return 转换xls(字节,上限)
    return 转换分隔文本(字节,格式,上限)
