'文本标签类型：身份、地址模式、以及芯片上的文件名'
from urllib.parse import unquote

__all__=['文本预览种类','文本预览标识','基名']

文本预览种类='text'
文本预览标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview'

def 基名(地址):
    '一个 file 地址的标签标题：解码后的最后一段。百分号序列坏了就原样显示'
    名=地址[地址.rfind('/')+1:]
    if 名=='':
        return 地址
    try:
        return unquote(名,errors='strict')
    except UnicodeDecodeError:
        return 名
