"""构建可中止内置 API 共用的 Node 风格取消错误。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/abort-error.ts`。
公开面仅中文名。文件名下划线以便 Python import。
"""
__all__=['中止错误']#仅中文公开名

def 中止错误(原因=None):#构造中止错误
    """创建携带 Node 稳定错误码的 `AbortError`。

    参数:
        原因: 可选 AbortSignal reason，作为错误 cause 暴露。
    返回:
        Node 兼容的中止错误。
    """
    错误=Exception('The operation was aborted')#基错误
    错误.name='AbortError'#Node名
    错误.code='ABORT_ERR'#稳定错误码
    if 原因 is not None: 错误.cause=原因#挂上cause
    return 错误#交回
