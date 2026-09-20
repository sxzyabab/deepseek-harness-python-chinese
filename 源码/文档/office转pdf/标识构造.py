"""源定位与转换器拥有的身份，供共享 PDF 复用。"""
from ...工具.标识构造 import 标识构造

__all__=['office源键','office转pdf世代','office转pdf键']

def office源键(键):
    """标注已授权源定位，供读前去重；授权仍由调用方负责。"""
    return 标识构造(键)

def office转pdf世代(值):
    """标注提供方寿命（引擎、渲染与字体配置）。"""
    return 标识构造(值)

def office转pdf键(值):
    """标注转换器拥有的内容身份；调用方不得解析。"""
    return 标识构造(值)
