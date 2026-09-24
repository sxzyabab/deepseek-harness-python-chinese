from .错误 import 表格预览错误

__all__=['excel格式']

def excel格式(路径):
    """按登记文件名选解析器。"""
    点=路径.rfind('.')
    后缀='' if 点<0 else 路径[点+1:].lower()
    if 后缀 in ('xlsx','xls','csv','tsv'):
        return 后缀
    raise 表格预览错误('invalid')
