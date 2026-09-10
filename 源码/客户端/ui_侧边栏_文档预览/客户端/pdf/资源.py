"""构建拥有、同版本的 PDF.js 资源；全部二进制资源在本地解码。

对齐上游 `ui-sidebar-documentpreview/src/client/pdf/assets.ts`。公开面仅中文名。
Python 半无打包的 worker 源与内联资源；打开 PDF 须由宿主注入。
"""
import base64#解码

__all__=['工作线程源','创建pdf二进制数据工厂']#仅中文公开名

工作线程源=''#构建内联；空表示未打包


def 创建pdf二进制数据工厂(资源=None):
    """捕获本构建的二进制资源，无网络回退。

    资源为 kind → filename → base64；缺省空表。返回可调用的工厂类。
    """
    表=资源 if 资源 is not None else {}#资源表

    class 二进制数据工厂:
        """PDF.js BinaryDataFactory 形。"""

        def fetch(自身,请求):
            """按种类与文件名取独立字节。请求为 dict：kind / filename。"""
            种类=请求['kind']#种类
            文件名=请求['filename']#文件名
            文件表=表[种类] if 种类 in 表 else {}#文件表
            if 文件名 not in 文件表:#未打包
                raise LookupError('PDF.js asset is not bundled: '+种类+'/'+文件名)
            return base64.b64decode(文件表[文件名])#字节

    return 二进制数据工厂#构造器
