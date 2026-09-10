"""单进程 Worker 对 `@deepseek-ai/node-addon-system/flock` 的替换实现。

JSONL 后端的进程内写声明已排除所有写者，
因此其内核锁请求无需再占另一资源即可成功。

对齐上游 `webworker-runtime/src/node/external_packages/node-addon-system-flock.ts`。
文件名下划线：Python 无法 import 连字符模块名。
"""

__all__=['tryLockExclusive','__esModule','default']#Node面

def tryLockExclusive(_fd):
    """立即批准单进程 Worker 的排他锁请求。文件描述符未使用。"""
    return None#同步兑现（async→同步）

__esModule=True#CJS互操作

default={'tryLockExclusive':tryLockExclusive}#原生 flock API 面
