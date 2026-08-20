"""Cordis `FiberState` 常量枚举的运行时镜像与标签。

对齐上游 `拓展/tool-cordis/src/fiber-state.ts`。公开面仅中文名。
"""

__all__=['光纤状态','状态标签']#仅中文公开名

光纤状态={#运行时状态值镜像
    'PENDING':0,#等待加载
    'LOADING':1,#正在加载
    'ACTIVE':2,#已激活
    'FAILED':3,#加载失败
    'DISPOSED':4,#已拆除
    'UNLOADING':5,#正在卸载
}#只读镜像

状态标签={#状态标签表
    0:'pending',#等待
    1:'loading',#加载中
    2:'active',#活跃
    3:'failed',#失败
    4:'disposed',#已拆除
    5:'unloading',#卸载中
}#标签与状态一一对应
