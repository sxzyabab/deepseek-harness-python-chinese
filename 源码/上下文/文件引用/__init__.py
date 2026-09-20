"""宿主侧共享的文件引用发现能力缝。"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类
from .词法 import 光标处活动令牌,格式化文件提及#再导出词法
from .类型 import 文件引用候选字段#候选字段约定

文件引用提示=('Tokens prefixed with @ are workspace paths the user explicitly referenced, relative to the workspace root. '#模型指引前段
    +'A trailing slash marks a directory: list it when its contents matter. Anything else is a file: use the read tool when its contents are needed, and do not claim to have inspected it before reading. @"..." quotes a path containing spaces.')#模型指引后段

__all__=[
    '包名','名称','默认','文件引用提示','文件引用服务','文件引用候选字段',
    '光标处活动令牌','格式化文件提及',
]
包名='@deepseek-ai/dsh-file-reference'
名称='file-reference'

class 文件引用服务(服务):
    """宿主能力：为某智能体工作目录列举文件/目录候选。"""
    def __init__(自身,上下文):
        """登记为 ctx.fileReferences。"""
        super().__init__(上下文,'fileReferences')#服务名

    def 列举(自身,智能体,查询,信号):
        """子类实现：返回确定性的纯路径候选。"""
        raise NotImplementedError('FileReferenceService.list')#子类必须实现

默认=文件引用服务
name=名称#框架槽
default=默认#框架槽
