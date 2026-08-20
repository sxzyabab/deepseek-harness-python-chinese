"""插件清单 Remote 的纯类型与 Fiber 阶段投影。

对齐上游 `plugin-inventory/src/types.ts`。公开面仅中文名；阶段字面量保持上游。
"""

__all__=[#仅中文公开名
    '插件条目标识',
    '插件光纤阶段',
    '插件清单条目',
    '插件清单快照',
    '打品牌条目标识',
    '光纤状态表',
    '光纤阶段表',
]#公开面结束

插件光纤阶段=('pending','loading','active','failed','unloading',None)#对外阶段词表

光纤状态表={#数值与 Cordis FiberState 对齐
    'PENDING':0,#尚未加载
    'LOADING':1,#正在加载
    'ACTIVE':2,#已激活
    'FAILED':3,#加载失败
    'DISPOSED':4,#已处置
    'UNLOADING':5,#正在卸载
}#状态表结束

光纤阶段表={#FiberState → 清单阶段；已处置对外为 null
    0:'pending',#尚未加载
    1:'loading',#正在加载
    2:'active',#已激活
    3:'failed',#加载失败
    4:None,#已处置不出现
    5:'unloading',#正在卸载
}#阶段表结束

def 打品牌条目标识(值):#string 收成品牌 id
    """在拥有边界把已有 Loader 树条目 id 打上品牌。"""
    return 值#Loader 已保证 id 存在；运行时仍是 str

插件条目标识=str#品牌化条目 id 运行时类型
插件清单条目=dict#清单行映射
插件清单快照=dict#一次 list 的完整投影
