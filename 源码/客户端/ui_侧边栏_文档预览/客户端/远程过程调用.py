import base64#线路 base64
from urllib.parse import unquote as 百分号解码

__all__=[
    '宿主文件','创建分页读','文档文件字节',
]


def 宿主文件(地址):
    """一个 `dsh-resource://file/…` 地址所命名的会话与路径。

    返回 dict：sessionId / path。非会话地址抛错。
    """
    前缀='dsh-resource://file/session/'#会话前缀
    if not 地址.startswith(前缀):#非会话
        raise ValueError('ui-sidebar-documentpreview: 不是会话文件地址 "'+地址+'"')
    余=地址[len(前缀):]#sessionId/path
    斜=余.find('/')#分隔
    if 斜<0:#无路径
        raise ValueError('ui-sidebar-documentpreview: 不是会话文件地址 "'+地址+'"')
    return {'sessionId':百分号解码(余[:斜]),'path':百分号解码(余[斜+1:])}


def 创建分页读(远程):
    """把分页读取绑到一份 Remote 面。页长是 Host 配置上限，因此不传 limit。"""

    def 读取(会话标识,路径,偏移,信号):
        """调用 workspaceFiles.read；结果原样透传。"""
        return 远程.workspaceFiles.read(会话标识,路径,{'offset':偏移},信号)#RemoteResult

    return 读取#绑定


def 文档文件字节(文件):
    """为文档渲染器解码一次成功的 Remote 字节结果。

    文件为跨包 WorkspaceFileBytes dict；返回同结构但 data 为 bytes。
    """
    解码=base64.b64decode(文件['data'])#原生字节
    结果=dict(文件)#浅拷
    结果['data']=解码#替换
    return 结果#文档字节
