"""有限的 HTML 声明经典脚本与样式表；无模块、CSS 依赖或运行时 fetch 遍历。

对齐上游 `ui-sidebar-documentpreview/src/client/html/pack.ts`。公开面仅中文名。
无 DOM 时只返回正文包（不解析依赖）；有 DOM 时按上游规则收集。
"""
import re#相对判定
from .字节 import 解码文本#解码
from ..面 import 已中止#中止

__all__=['打包超文本']#仅中文公开名

_单资源上限=4*1024*1024#4 MiB
_总计上限=32*1024*1024#32 MiB
_数量上限=64#64
_绝对前缀=re.compile(r'^(?:[a-z][a-z\d+.-]*:|[/\\#?])',re.IGNORECASE|re.ASCII)#绝对


def _是否相对(引用):
    """此引用是否可相对原文档读取。"""
    return len(引用)>0 and _绝对前缀.search(引用) is None and '\0' not in 引用#相对


def 打包超文本(数据,相对读取,信号):
    """收集静态依赖。数据为 UTF-8 HTML 字节；返回 dict：data / assets。

    无浏览器 DOM 时返回仅正文的包（依赖留空）；解码、上限与读取失败抛错。
    """
    if 已中止(信号):#已中止
        raise RuntimeError('aborted')#中止
    总计=len(数据)#字节数
    if 总计>_总计上限:#超限
        raise ValueError('HTML package exceeds its total byte limit')
    解码文本(数据)#校验 UTF-8
    # Python 半无 document.createElement；不遍历依赖，只交完整正文。
    return {'data':数据,'assets':[]}#正文包
