"""无框架启动页的光纤状态投影词汇。

对齐上游 `web/src/loader-status.ts`。公开面仅中文名。
启动链订阅 `internal/status`，并投影拥有 loader 条目的当前状态。
标签字符串原样英文。
"""

__all__=['光纤状态值','状态标签']#仅中文公开名

光纤状态值={#cordis FiberState 值镜像
    'PENDING':0,#挂起
    'LOADING':1,#加载中
    'ACTIVE':2,#已激活
    'FAILED':3,#失败
    'DISPOSED':4,#已拆除
    'UNLOADING':5,#卸载中
}#光纤状态值结束

状态标签={#光纤状态 → 小写标签
    0:'pending',#挂起
    1:'loading',#加载中
    2:'active',#已激活
    3:'failed',#失败
    4:'disposed',#已拆除
    5:'unloading',#卸载中
}#状态标签结束
