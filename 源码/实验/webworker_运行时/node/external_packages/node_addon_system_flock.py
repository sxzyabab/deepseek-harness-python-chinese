__all__=['tryLockExclusive','__esModule','default']

def tryLockExclusive(_fd):
    """立即批准单进程 Worker 的排他锁请求。文件描述符未使用。"""
    return None

__esModule=True

default={'tryLockExclusive':tryLockExclusive}
