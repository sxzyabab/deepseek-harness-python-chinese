"""槽位登记与运行时引擎共用的框架无关 store 约定。

对齐上游 `ui-slots/src/store.ts`。公开面仅中文名。
上游本文件仅类型；真实现住在运行时包。此处给出可导入的约定名，供登记选项与 Props 份额引用。
"""

__all__=['仓库声明','仓库工厂','仓库句柄','仓库规格','仓库实例','已烤动作','动作声明','快照选择器钩']#仅中文公开名

class 仓库规格:#StoreSpec 约定形
    """init / persist / actions。"""

class 仓库实例:#StoreInstance 约定形
    """getSnapshot / subscribe / actions / clearPersisted。"""

class 仓库句柄:#StoreHandle 约定形
    """spec + create(scopeKey?)。"""

class 仓库工厂:#StoreFactory 约定形
    """() -> 仓库句柄，独占。"""

class 仓库声明:#StoreDecl 约定形
    """共享句柄或独占工厂。"""

class 动作声明:#ActionsDecl 约定形
    """draft 变换写集合。"""

class 已烤动作:#BakedActions 约定形
    """剥掉 draft 后的回调形。"""

class 快照选择器钩:#SnapshotSelectorHook 约定形
    """快照源上的带类型选择器钩。"""
