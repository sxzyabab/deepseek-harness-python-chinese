'快捷键协议、登记和桌面桥的失败。多处相同的抛出留在这里'

__all__=[#仅中文公开名
    '快捷键错误',
    '抛出非法快捷键绑定','抛出非法快捷键编辑','抛出非法快捷键定义',
    '抛出冲突或预留默认','抛出重复快捷键命令','抛出桌面键盘桥不可用',
    '抛出非法快捷键配置',
]

class 快捷键错误(Exception):
    '说明与上游 Error 相同，调用方按说明判断失败原因'

def 抛出非法快捷键绑定():
    'JSON 绑定字段不合法，或带了不能回写的未知字段'
    raise 快捷键错误('Invalid shortcut binding')

def 抛出非法快捷键编辑():
    '偏好编辑不是 set、reset 或 reset-all'
    raise 快捷键错误('Invalid shortcut edit')

def 抛出非法快捷键定义():
    '命令目录条目缺少标识、默认或带了未知字段'
    raise 快捷键错误('Invalid shortcut definition')

def 抛出冲突或预留默认():
    '产品默认绑定互相重叠，或落在预留组合上'
    raise 快捷键错误('Conflicting or reserved shortcut default')

def 抛出重复快捷键命令(标识):
    '同一个命令标识不能同时进可编辑表和固定表'
    raise 快捷键错误('Duplicate shortcut command: '+str(标识))

def 抛出桌面键盘桥不可用():
    '桌面壳启动时没有键盘桥，或关闭窗口时桥已经不在'
    raise 快捷键错误('Desktop keyboard bridge unavailable')

def 抛出非法快捷键配置():
    'stopSequenceMs 不是 1 到 2147483646 的整数，或根值不是对象'
    raise 快捷键错误('Invalid shortcut config')
