__all__=['纤程状态值','状态标签']#仅中文公开名

纤程状态值={#cordis FiberState 值镜像
    'PENDING':0,#挂起
    'LOADING':1,#加载中
    'ACTIVE':2,#已激活
    'FAILED':3,#失败
    'DISPOSED':4,#已拆除
    'UNLOADING':5,#卸载中
}#纤程状态值结束

状态标签={#纤程状态 → 小写标签
    0:'pending',#挂起
    1:'loading',#加载中
    2:'active',#已激活
    3:'failed',#失败
    4:'disposed',#已拆除
    5:'unloading',#卸载中
}#状态标签结束
