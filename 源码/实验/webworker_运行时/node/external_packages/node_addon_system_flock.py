
__all__=['tryLockExclusive','__esModule','default']#Node面

def tryLockExclusive(_fd):
    """立即批准单进程 Worker 的排他锁请求。文件描述符未使用。"""
    return None#同步兑现（async→同步）

__esModule=True#CJS互操作

default={'tryLockExclusive':tryLockExclusive}#原生 flock API 面
