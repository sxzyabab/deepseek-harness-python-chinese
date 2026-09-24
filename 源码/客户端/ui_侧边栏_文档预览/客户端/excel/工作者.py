from .转换 import 转换excel
from .错误 import 表格预览错误

__all__=['工作者入口']

def 工作者入口(字节,格式,上限):
    """一份工作簿一次解析；从不执行公式与外部链接。"""
    try:
        return {'ok':True,'value':转换excel(字节,格式,上限)}
    except 表格预览错误 as 错误:
        return {'ok':False,'code':错误.code}
    except Exception:
        return {'ok':False,'code':'invalid'}
