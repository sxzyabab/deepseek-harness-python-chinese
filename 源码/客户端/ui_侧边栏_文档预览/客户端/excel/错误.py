__all__=['表格预览错误']

class 表格预览错误(Exception):
    """与文案无关的表格解析失败类别。"""
    def __init__(自身,code):
        super().__init__(code)
        自身.code=code
        自身.name='ExcelPreviewError'
