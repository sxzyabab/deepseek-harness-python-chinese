__all__=['是已结算工具','是运行中工具']


def 是已结算工具(块):
    '工具根上带 kind 就是最终结果'
    return isinstance(块,dict) and 'kind' in 块


def 是运行中工具(块):
    '工具根还没有最终结果'
    return not 是已结算工具(块)
