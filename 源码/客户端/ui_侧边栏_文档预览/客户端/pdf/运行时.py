from ...异常 import pdf工作线程失败#失败
from ..面 import 已中止#中止

__all__=['打开pdf']

def 打开pdf(数据,信号,报告失败):
    """用显式拥有的工作线程打开完整 PDF 字节。

    返回 dict：document（可调用取文档或抛错）/ dispose（清理）。
    无 PDF.js 时经报告失败投递工作线程失败并 dispose
    """
    已关=[False]#关闭旗

    def 拆除():
        '幂等清理'
        已关[0]=True#标记
        return None#完成

    def 取文档():
        '加载文档；无后端则失败'
        if 已中止(信号) or 已关[0]:#已停
            raise RuntimeError('已中止')
        错误体=pdf工作线程失败(None)
        报告错=None
        try:
            报告失败(错误体)
        except Exception as 回调错:
            报告错=回调错
        拆除()
        if 报告错 is not None:
            raise 错误体 from 报告错
        raise 错误体

    return {'document':取文档,'dispose':拆除}#会话
