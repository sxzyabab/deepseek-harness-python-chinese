"""一个 Remote 错误码应得的失败行。

对齐上游 `ui-sidebar-documentpreview/src/client/failure-line.ts`。公开面仅中文名。
与组件分开，使映射可单独测试。本读取器未命名的码落到携带载体消息的通用行。
"""

__all__=['人读字节','失败行']#仅中文公开名


def 人读字节(字节数):
    """按人可读方式渲染字节数。"""
    if 字节数>=1024*1024:#兆
        return str(round(字节数/(1024*1024)))+' MB'
    if 字节数>=1024:#千
        return str(round(字节数/1024))+' KB'
    return str(字节数)+' B'#字节


def 失败行(翻译,失败):
    """用文件口吻而非传输口吻说明出错原因。失败为跨包 RemoteFailure dict。"""
    码=失败['code'] if 'code' in 失败 else None#错误码
    if 码=='workspace-file/not-found':#不存在
        return 翻译('error.notFound')
    if 码=='workspace-file/too-large':#过大
        详情=失败['details'] if 'details' in 失败 else {}
        上限=详情['limit'] if 'limit' in 详情 else 0
        return 翻译('error.tooLarge',{'limit':人读字节(上限)})
    if 码=='workspace-file/not-text':#非文本
        return 翻译('error.notText')
    if 码=='workspace-file/not-regular-file':#非普通文件
        return 翻译('error.notRegularFile')
    消息=失败['message'] if 'message' in 失败 else ''#载体消息
    return 翻译('error.unavailable',{'message':消息})#透传
