"""会话控制器文件引用 Remote 适配器。

对齐上游 `session-controller/src/file-references.ts`。公开面仅中文名。
"""
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .工具 import 解开#辅助

__all__=['会话文件引用']#仅中文公开名

class 会话文件引用(远程服务):#fileReferences 命名空间
    """在已解析智能体上列出文件引用候选。"""
    注入=['fileReferences','typert']#依赖

    def __init__(自身,上下文):#构造
        """登记 sessionFileReferences 服务。"""
        super().__init__(上下文,'sessionFileReferences',{'namespace':'fileReferences'})#注册

    @_远程
    def list(自身,智能体,查询,信号):#列出候选
        """委托给已组合的 fileReferences 提供方。"""
        return 解开(自身.ctx.fileReferences.list(智能体,查询,信号))#委托
