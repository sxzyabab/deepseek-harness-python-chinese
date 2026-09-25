"""不可预览文档空态上的文件打开动作。"""
from .打开路径动作 import 文件打开目标#文件适配

__all__=['打开路径空动作']#仅中文公开名

class 打开路径空动作:#不可预览空态贡献
    """更大带标签主钮的共享文件打开菜单。"""

    def __init__(自身,属性):
        """记下 props，强制 empty。"""
        面=dict(属性) if 属性 is not None else {}#拷贝
        面['empty']=True#空态大钮
        自身.目标=文件打开目标(面)#目标

    def 更新(自身,属性):
        """刷新并保持 empty。"""
        面=dict(属性) if 属性 is not None else {}#拷贝
        面['empty']=True#空态
        自身.目标.更新(面)#透传

    def 渲染(自身):
        """共享文件打开动作。"""
        return 自身.目标.渲染()#渲染

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
