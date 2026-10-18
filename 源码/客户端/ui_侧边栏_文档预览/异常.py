'本包异常类。只被一处抛出的语句留在业务文件'

__all__=['表格预览错误','pdf工作线程失败']

class 表格预览错误(Exception):
    '与文案无关的表格解析失败类别'
    def __init__(自身,code,原因=None):
        '记下类别。code 为 invalid、tooLarge、timeout、encoding'
        super().__init__(code)
        自身.code=code
        自身.name='ExcelPreviewError'
        if 原因 is not None:
            自身.__cause__=原因

class pdf工作线程失败(Exception):
    '区分工作线程启动或传输失败与文档解析错误'
    种类='worker'
    def __init__(自身,原因=None):
        '记下原因供诊断。可见说明由 PDF 文案负责'
        super().__init__()
        自身.name='PdfWorkerFailure'
        自身.kind='worker'
        if 原因 is not None:
            自身.__cause__=原因
