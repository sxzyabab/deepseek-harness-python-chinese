# 上游 npm：@deepseek-ai/libreoffice-kit（独立发布的 LibreOffice kit 入口）
# 本地尚未接入原生/WASM 引擎绑定；渲染时拒绝，保持与「引擎不可用」同形。

__all__=['创建转换器']#仅中文公开名

class 占位转换器:
    """占位转换器：渲染报告不可用，拆除无操作。"""
    def 渲染(自身,请求,信号=None):
        """对齐 Converter.render；占位拒绝。"""
        错误=RuntimeError('LibreOffice kit is not available in this Python build.')#英文诊断
        错误.code='unavailable'#分类码
        raise 错误#拒绝
    def 拆除(自身):
        """对齐 Converter.dispose；占位无资源。"""
        return#无操作

def 创建转换器(选项):
    """对齐 createConverter(options)；返回占位转换器。"""
    return 占位转换器()#占位实例
