"""目录选择缝的 native 后端：把 `ctx.directoryPicker` 登记为 `native` 能力。

对齐上游 `@deepseek-ai/dsh-host-directory-picker-native`。公开面仅中文名。每次 pick 在宿主显示器上打开一次操作系统原生选择器。本包默认导出服务类。
"""
from ..directory_picker import 目录选择器#缝定义
from .原生选择 import 选原生目录#按平台打开原生选择器

__all__=['原生目录选择器','选原生目录']#仅中文公开名

class 原生目录选择器(目录选择器):#native 后端
    """`ctx.directoryPicker` 的 native 实现（服务生命周期内能力对象稳定）。"""
    def __init__(自身,上下文):#按上下文构造
        """登记为 ctx.directoryPicker 并钉住稳定 native 能力。"""
        super().__init__(上下文)#登记服务
        def 选(信号):#打开选择器
            """转给按平台实现的原生选择器。"""
            return 选原生目录(信号)#真实选择器
        自身.原生能力={'kind':'native','pick':选}#稳定能力对象

    def capability(自身):#原生交互能力
        """返回稳定的 native 能力对象。"""
        return 自身.原生能力#同一对象
