"""一条 Remote 错误码应得的失败行。

对齐上游 `ui-sidebar-textpreview/src/client/failure-line.ts`。公开面仅中文名。
与组件分开，使映射可单独测试。本读者未点名的码落到带载体消息的通用行。
"""

__all__=['可读字节','失败行']#仅中文公开名


def 可读字节(字节数):
    """把字节数写成常人可读的量。"""
    if 字节数>=1024*1024:#兆
        return str(round(字节数/(1024*1024)))+' MB'#兆字节
    if 字节数>=1024:#千
        return str(round(字节数/1024))+' KB'#千字节
    return str(字节数)+' B'#字节


def 失败行(翻译,失败):
    """用文件口吻说明为何读不出。失败为跨包 RemoteFailure dict。"""
    码=失败['code'] if 'code' in 失败 else None#错误码
    if 码=='workspace-file/not-found':#不存在
        return 翻译('error.notFound')#文案
    if 码=='workspace-file/outside-workspace':#工作区外
        return 翻译('error.outsideWorkspace')#文案
    if 码=='workspace-file/too-large':#超限
        详情=失败['details'] if 'details' in 失败 and 失败['details'] is not None else {}#详情
        上限=详情['limit'] if 'limit' in 详情 else 0#字节上限
        return 翻译('error.tooLarge',{'limit':可读字节(上限)})#带上限
    if 码=='workspace-file/not-text':#非文本
        return 翻译('error.notText')#文案
    if 码=='workspace-file/not-regular-file':#非普通文件
        return 翻译('error.notRegularFile')#文案
    # 载体与未分类宿主失败原样到达读者：本面板对传输级消息无额外可说
    消息=失败['message'] if 'message' in 失败 else ''#载体消息
    return 翻译('error.unavailable',{'message':消息})#透传
