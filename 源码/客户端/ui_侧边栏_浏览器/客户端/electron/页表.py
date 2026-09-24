from .electron网页视图实现 import electron网页视图实现
from .electron网页视图呈现形式 import electron网页视图呈现形式

__all__=['创建electron页']

def 创建electron页(选项,桥,工作区):
    """组装空闲桌面提供方；宾客创建等挂载与导航。"""
    箱={'帧':None}
    def 已挂():
        箱['帧'].附着()
    def 已卸():
        箱['帧'].脱离()
    呈现=electron网页视图呈现形式({'mounted':已挂,'unmounted':已卸})
    帧=electron网页视图实现(选项,桥,工作区,呈现)
    箱['帧']=帧
    return {'frame':帧,'presentation':呈现}
