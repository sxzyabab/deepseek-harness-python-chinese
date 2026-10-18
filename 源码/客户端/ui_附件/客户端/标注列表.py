'灯箱两处共用的中文标签。其余句子在使用处直接读对话包的中文表，显示不走英文表'
from ...ui_对话.客户端.文案 import 中文

__all__=['灯箱文案']

def 灯箱文案():
    '原图预览的对话框名和关闭名'
    return {'dialog':中文['image.preview'],'close':中文['image.closePreview']}
