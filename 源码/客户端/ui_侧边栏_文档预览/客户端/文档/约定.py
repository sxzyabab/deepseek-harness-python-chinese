"""文档渲染器槽：拥有方供给共享文件状态，渲染器拥有各自的呈现。

对齐上游 `ui-sidebar-documentpreview/src/client/document/contract.ts`。公开面仅中文名。
槽位声明为跨包约定；owner 含 resourceAddress / content / wrap / scrollportRef。
本模块只导出标签信息工厂。
"""

__all__=['文档标签信息工厂']#仅中文公开名


def 文档标签信息工厂(_标准,取标签信息):
    """把框架的标签读取器转发给所选文档正文，无另一订阅适配器。"""
    return 取标签信息#同一读取器
