"""结构化 PDF 工作线程失败；渲染器文案拥有可见说明。

对齐上游 `ui-sidebar-documentpreview/src/client/pdf/errors.ts`。公开面仅中文名。
"""

__all__=['pdf工作线程失败']#仅中文公开名


class pdf工作线程失败(Exception):
    """区分工作线程启动/传输失败与文档解析错误。"""

    种类='worker'#线路字面量

    def __init__(自身,原因=None):
        """记下原因供诊断。"""
        super().__init__()#无消息；文案层解释
        自身.__cause__=原因#保留
        自身.name='PdfWorkerFailure'#结构识别名
