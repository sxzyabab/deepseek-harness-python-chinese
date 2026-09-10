"""增量高亮源码；文档拥有方供给累计文本与换行偏好。

对齐上游 `ui-sidebar-documentpreview/src/client/code/CodeBody.tsx`。公开面仅中文名。
无 React：正文为视图模型。
"""
from .语言 import 路径语言#文法
from ..远程过程调用 import 宿主文件#宿主文件

__all__=['代码体','样式表']#仅中文公开名

样式表=''#样式见旁路 代码体.module.css；运行时由宿主注入


def 代码体(资源地址,内容,换行,翻译):
    """产出稳定代码块结构，或字节内容时无正文。"""
    if 内容.get('kind')!='text':#非文本
        return None#无
    文件=宿主文件(资源地址)#会话文件
    语言=路径语言(文件['path'])#文法
    return {#结构
        'kind':'code-body',
        'wrap':换行,
        'code':内容['text'],
        'lang':语言,
        'streaming':not 内容['eof'],
        'copyLabel':翻译('copy'),
        'copiedLabel':翻译('copied'),
    }#结束
