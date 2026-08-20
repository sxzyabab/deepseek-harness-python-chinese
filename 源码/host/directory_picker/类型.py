"""目录选择缝的纯类型：能力词表、列举行与 browse 业务失败。

对齐上游 `directory-picker/src/types` 与 index 中的接口声明。公开面仅中文名；判别标签、业务码英文字面量保持上游。
"""

__all__=[#仅中文公开名
    '目录选择原生能力',
    '目录条目',
    '目录列举',
    '目录选择浏览能力',
    '目录选择能力表',
    '目录选择能力',
    '目录选择错误码',
    '目录选择错误',
]#公开面结束

目录选择错误码=('directory-unreadable','directory-exists','directory-create-failed')#browse 原语的封闭业务失败码

class 目录选择错误(Exception):#browse 原语的带业务码失败
    """browse 原语抛出的带类型失败，消费方无需字符串匹配即可映射业务码。"""
    def __init__(自身,码,路径,说明):#按业务码、路径与说明构造
        """记下业务码、绝对路径与面向操作者的说明。"""
        super().__init__(说明)#交给 Exception 保存说明
        自身.code=码#封闭业务码
        自身.path=路径#失败所针对的绝对路径
        自身.name='DirectoryPickerError'#固定错误名，对齐上游

class 目录选择原生能力(dict):#原生选择器能力映射形状
    """原生交互：在宿主显示器上打开一次操作系统目录选择器。键：kind、pick。"""

class 目录条目(dict):#目录条目映射形状
    """一行目录：列举子项或面包屑祖先。键：name、path、hidden。"""

class 目录列举(dict):#一层目录列举映射形状
    """一层目录及其祖先链。键：path、home、crumbs、entries、truncated。"""

class 目录选择浏览能力(dict):#浏览能力映射形状
    """browse 交互：应用内浏览器逐层驱动的列举/创建原语。键：kind、list、createDirectory。"""

class 目录选择能力表(dict):#可合并扩展登记表
    """按能力 kind 索引的可合并扩展交互形态登记表。键：native、browse。"""

目录选择能力=dict#由能力登记表推导的交互形态联合，运行时为映射
