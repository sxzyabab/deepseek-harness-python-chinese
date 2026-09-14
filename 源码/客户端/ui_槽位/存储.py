__all__=['存储声明','存储工厂','存储句柄','存储规格','存储实例','已烤动作','动作声明','快照选择器钩']#仅中文公开名

class 存储规格:#StoreSpec 约定形
    """init / persist / actions。"""

class 存储实例:#StoreInstance 约定形
    """getSnapshot / subscribe / actions / clearPersisted。"""

class 存储句柄:#StoreHandle 约定形
    """spec + create(scopeKey?)。"""

class 存储工厂:#StoreFactory 约定形
    """() -> 存储句柄，独占。"""

class 存储声明:#StoreDecl 约定形
    """共享句柄或独占工厂。"""

class 动作声明:#ActionsDecl 约定形
    """draft 变换写集合。"""

class 已烤动作:#BakedActions 约定形
    """剥掉 draft 后的回调形。"""

class 快照选择器钩:#SnapshotSelectorHook 约定形
    """快照源上的带类型选择器钩。"""
