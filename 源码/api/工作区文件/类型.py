"""`workspaceFiles` Remote 命名空间的线路类型说明。

仅类型与错误码契约：运行时 Remote 错误类供宿主与客户端共用。
跨线值为 dict。

两套路经词汇离开本包，每个方法只用其中一套：
- `read` / `readBytes` / `stat` / `changes` 以文件系统执行世界的绝对路径命名文件；
- `list` 使用工作区相对路径（根自身为空串）。
"""

__all__=[#仅中文公开名
    '远程错误','远程错误消息','已中止','若已中止则抛出',
    '工作区文件状态字段','工作区文件行窗口字段','工作区文件文本字段',
    '工作区字节窗口字段','工作区文件字节字段','工作区目录条目字段',
    '工作区目录列举字段','工作区文件监视帧种类',
]#公开面结束

# ---------------------------------------------------------------------------
# 线路字段名（英文键，跨线 dict）
# ---------------------------------------------------------------------------

工作区文件状态字段=('absolutePath','version','bytes')#stat：绝对路径、版本、可选整文件字节
工作区文件行窗口字段=('offset','limit')#read 行窗：可选 1 起算 offset / limit
工作区文件文本字段=('absolutePath','version','bytes','offset','text','lines','eof')#read 页
工作区字节窗口字段=('offset','length')#readBytes 字节窗：可选 0 起算 offset / length
工作区文件字节字段=('absolutePath','version','bytes','offset','data','eof')#readBytes 窗
工作区目录条目字段=('name','type','size')#list 子项：基名、类型、可选 size
工作区目录列举字段=('path','entries','truncated')#list 结果
工作区文件监视帧种类=('ready','change')#changes 帧 kind

# RemoteErrorDetailsMap（宿主发射；客户端另见 客户端/类型）：
# 'workspace-file/not-found': {path}
# 'workspace-file/outside-workspace': {path}
# 'workspace-file/too-large': {path, limit}
# 'workspace-file/not-text': {path}
# 'workspace-file/not-regular-file': {path, kind: directory|symlink|other}
# 'workspace-file/not-directory': {path, kind: file|symlink|other}


class 远程错误(Exception):
    """远程错误。附加信息做成属性；消息原样英文。"""

    def __init__(自身,码,消息,详情=None,原因=None):
        """记下 code/message/details。"""
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因链
            自身.__cause__=原因#链接


def 远程错误消息(错误):
    """把错误收成字符串。"""
    return str(错误)#消息


def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位


def 若已中止则抛出(信号):
    """已中止则抛出取消。"""
    if 已中止(信号):#已中止
        raise 远程错误('gateway/cancelled','aborted',{})#取消
