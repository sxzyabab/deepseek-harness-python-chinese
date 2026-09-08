"""本包登记的第一阶段：`text` tab 类型是什么。

对齐上游 `ui-sidebar-textpreview/src/client/definition.ts`。公开面仅中文名。
该类型认领任一作用域的 `dsh-resource://file/` 地址，优先级为 `fallback`——
更具体的同址类型应压过它，位置对齐 VS Code 文本编辑器在编辑器族中的角色。
`canOpen` 在认领时拒绝 `解析文件地址` 拒收的地址；未被认领的地址是文档化的接线错误。
"""
from urllib.parse import unquote#段解码
from .读页 import 解析文件地址#文件地址语法

__all__=['文本预览种类','文本预览标识','取基名','文本定义']#仅中文公开名

文本预览种类='text'#本包拥有的 tab 种类（线路字面量）
文本预览标识='@deepseek-ai/dsh-client-ui-sidebar-textpreview'#实现身份，亦为正文登记键


def 取基名(地址):
    """`file:` 形地址的标签标题：解码后的末段。

    整址仍是内容身份，同名异目录仍是两 tab；只有芯片文字缩短。
    按段解码，与地址构造一致，使含 `#`、`?` 或空格的名原样可读。
    """
    名=地址[地址.rfind('/')+1:]#末段
    if 名=='':#无段
        return 地址#整址
    return unquote(名)#解码名；畸形百分序列仍作名


def 文本定义():
    """文本类型的注册表定义。"""
    return {#右侧侧栏 tab 定义
        'id':文本预览标识,#实现身份
        'kind':文本预览种类,#种类
        'patterns':['dsh-resource://file/**'],#认领模式
        'priority':'fallback',#回退优先级
        'canOpen':lambda 地址:解析文件地址(地址) is not None,#可开
        'title':取基名,#标题
    }#定义结束
