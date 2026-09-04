"""`node:sqlite` 桩。Web 配置把 session-query-sqlite 设为
`:memory:` 与 `openAt: never`，因此验收链期间不打开数据库；
到达构造器意味着该配置已变。

对齐上游 `webworker-runtime/src/node/builtin_modules/mock/sqlite.ts`。
"""
from ...未实现失败 import 不可用错误,未实现失败#导入拒绝辅助

__all__=['DatabaseSync','StatementSync','backup','__esModule','default']#Node面

模块='node:sqlite'#模块说明符
DatabaseSync=未实现失败(模块,'DatabaseSync')#DatabaseSync拒绝桩
StatementSync=未实现失败(模块,'StatementSync')#StatementSync拒绝桩

def backup(*位置参数,**关键字参数):#备份拒绝
    """备份辅助（不可用）。"""
    raise 不可用错误(模块,'backup')#抛不可用错误

__esModule=True#CJS互操作标记
default={'DatabaseSync':DatabaseSync,'StatementSync':StatementSync,'backup':backup}#默认导出
