'原生目录选择的失败'
class 目录选择器原生错误(Exception):
    '原生目录选择失败时抛出。调用方按 Exception 接住'


def 选择已中止():
    '构造调用方已经中止这次选择的失败。驱动里两处共用这一句'
    return 目录选择器原生错误('native directory picker aborted')#中止文案
