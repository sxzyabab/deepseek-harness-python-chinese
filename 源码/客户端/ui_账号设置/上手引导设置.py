'桌面上手引导写在宿主设置文档里的进度'

__all__=['桌面引导命名空间','引导步骤','引导目的','引导过程','新进度','引导设置','Config']

桌面引导命名空间='ui-settings-account'
引导步骤=('welcome','credit','purpose','process','done')
引导目的=('office','development','both')
引导过程=('compact','standard','detailed')
完成原因=('completed','skipped','api-key')

def 新进度():
    '一次全新安装的进度'
    return {
        'version':1,
        'step':'welcome',
        'purpose':None,
        'process':None,
        'completion':None,
        'usage':'compact',
        'developerTools':False,
    }

def 取枚举(原始,键,允许,默认):
    '缺席用默认。null 保留。其余必须落在允许值里'
    if 键 not in 原始:
        return 默认
    值=原始[键]
    if 值 is None:
        return None
    if 值 not in 允许:
        raise RuntimeError(键+' is invalid')
    return 值

def 引导设置(原始=None):
    '校验设备本地的上手引导进度。没选过的项是 null'
    if 原始 is None:
        原始={}
    if isinstance(原始,dict) is False:
        raise RuntimeError('onboarding settings must be an object')
    版本=原始['version'] if 'version' in 原始 else 1
    if 版本!=1:
        raise RuntimeError('version must be 1')
    步=取枚举(原始,'step',引导步骤,'welcome')
    if 步 is None:
        raise RuntimeError('step is invalid')
    用量=取枚举(原始,'usage',('compact','detailed'),'compact')
    if 用量 is None:
        raise RuntimeError('usage is invalid')
    if 'developerTools' in 原始:
        开发工具=原始['developerTools']
        if isinstance(开发工具,bool) is False:
            raise RuntimeError('developerTools must be a boolean')
    else:
        开发工具=False
    return {
        'version':版本,
        'step':步,
        'purpose':取枚举(原始,'purpose',引导目的,None),
        'process':取枚举(原始,'process',引导过程,None),
        'completion':取枚举(原始,'completion',完成原因,None),
        'usage':用量,
        'developerTools':开发工具,
    }

Config=引导设置
