"""每个已挂载二进制文档一份真实模块工作线程与 PDF.js 加载任务。

对齐上游 `ui-sidebar-documentpreview/src/client/pdf/runtime.ts`。公开面仅中文名。
Python 半无浏览器 Worker / PDF.js；打开入口声明会话形，缺后端时失败回调。
"""
from .错误 import pdf工作线程失败#失败
from ..面 import 已中止#中止

__all__=['打开pdf']#仅中文公开名


def 打开pdf(数据,信号,报告失败):
    """用显式拥有的工作线程打开完整 PDF 字节。

    返回 dict：document（可调用取文档或抛错）/ dispose（清理）。
    无 PDF.js 时经报告失败投递工作线程失败并 dispose。
    """
    已关=[False]#关闭旗

    def 拆除():
        """幂等清理。"""
        已关[0]=True#标记
        return None#完成

    def 取文档():
        """加载文档；无后端则失败。"""
        if 已中止(信号) or 已关[0]:#已停
            raise RuntimeError('aborted')
        错=pdf工作线程失败(None)#无 Worker
        try:
            报告失败(错)#回调
        except Exception:#回调抛
            pass#忽略
        拆除()#清
        raise 错#失败

    return {'document':取文档,'dispose':拆除}#会话
