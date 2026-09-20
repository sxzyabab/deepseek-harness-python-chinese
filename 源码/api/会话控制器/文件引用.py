"""会话控制器文件引用 Remote 适配器。"""
from ...typert.协议 import 远程服务,远程 as _远程

__all__=['会话文件引用']

class 会话文件引用(远程服务):
    """在已解析智能体上列出文件引用候选。"""

    def __init__(自身,上下文):
        """登记 sessionFileReferences 服务。"""
        super().__init__(上下文,'sessionFileReferences',{'namespace':'fileReferences'})#注册

    @_远程
    def list(自身,智能体,查询,信号):
        """委托给已组合的 fileReferences 提供方。"""
        return 自身.ctx.fileReferences.list(智能体,查询,信号)

依赖=['fileReferences','typert']
会话文件引用.inject=依赖#框架槽
