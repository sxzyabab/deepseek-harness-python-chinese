"""PDF 渲染器拥有的文案。

对齐上游 `ui-sidebar-documentpreview/src/client/pdf/locales.ts`。公开面仅中文名。
"""

__all__=['中文','英文','pdf文案键']#仅中文公开名

中文={
    'title':'PDF',
    'pageImage':'PDF 第 {page} 页',
    'loading':'正在打开 PDF…',
    'rendering':'正在绘制页面…',
    'failed':'无法显示 PDF：{message}',
    'password':'此 PDF 需要密码，暂不支持预览。',
    'workerFailed':'PDF 渲染进程无法继续，请重试。',
    'unsupported':'PDF 预览需要完整文件内容。',
    'retry':'重试',
}

pdf文案键=tuple(中文.keys())

英文={
    'title':'PDF',
    'pageImage':'PDF page {page}',
    'loading':'Opening PDF…',
    'rendering':'Rendering page…',
    'failed':'Cannot display PDF: {message}',
    'password':'This PDF requires a password; password-protected previews are not supported.',
    'workerFailed':'The PDF rendering process could not continue. Please retry.',
    'unsupported':'PDF preview requires the complete file contents.',
    'retry':'Retry',
}
