__all__=['pdf工作线程失败','表格预览错误']#仅中文公开名

class 文档预览错误(Exception):
    '本包文档预览登记失败'

    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文

class pdf工作线程失败(Exception):
    '区分工作线程启动/传输失败与文档解析错误'

    种类='worker'#线路字面量

    def __init__(自身,原因=None):
        '记下原因供诊断'
        super().__init__()#无消息；文案层解释
        自身.__cause__=原因#保留
        自身.name='PdfWorkerFailure'#结构识别名

class 表格预览错误(Exception):
    '与文案无关的表格解析失败类别'
    def __init__(自身,code):
        super().__init__(code)
        自身.code=code
        自身.name='ExcelPreviewError'
