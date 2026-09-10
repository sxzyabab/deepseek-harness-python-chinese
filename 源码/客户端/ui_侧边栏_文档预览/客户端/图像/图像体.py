"""以固有 CSS 像素尺寸渲染的完整图片字节。

对齐上游 `ui-sidebar-documentpreview/src/client/image/ImageBody.tsx`。公开面仅中文名。
"""
from ..远程过程调用 import 宿主文件#宿主文件

__all__=['图像媒体类型','图像体','图像扩展名']#仅中文公开名

_图像媒体类型={#后缀 → MIME
    'png':'image/png',
    'jpg':'image/jpeg',
    'jpeg':'image/jpeg',
    'gif':'image/gif',
    'webp':'image/webp',
    'bmp':'image/bmp',
    'ico':'image/x-icon',
    'svg':'image/svg+xml',
}#媒体类型结束

图像扩展名=tuple(_图像媒体类型.keys())#后缀


def 图像媒体类型(路径):
    """把受支持文件名解析为媒体类型；未登记后缀为 None。"""
    归一=路径.replace('\\','/')#归一
    名=归一[归一.rfind('/')+1:].lower()#文件名
    点=名.rfind('.')#末点
    if 点<0:#无扩展
        return None#无
    扩展=名[点+1:]#后缀
    return _图像媒体类型[扩展] if 扩展 in _图像媒体类型 else None#类型


def 图像体(内容,资源地址,翻译):
    """产出固有尺寸图片结构。"""
    路径=宿主文件(资源地址)['path']#路径
    媒体=图像媒体类型(路径)#媒体类型
    数据=内容['data'] if 内容.get('kind')=='bytes' else None#字节
    if 数据 is None or 媒体 is None:#不支持
        return {'kind':'image-status','status':'unsupported','message':翻译('unsupported')}#状态
    名=路径.replace('\\','/')#归一
    名=名[名.rfind('/')+1:]#文件名
    return {#结构
        'kind':'image-body',
        'mediaType':媒体,
        'data':数据,
        'alt':翻译('preview',{'name':名}),
        'loading':翻译('loading'),
        'failed':翻译('failed'),
    }#结束
