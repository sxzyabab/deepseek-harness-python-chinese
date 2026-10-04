class 设置错误(Exception):
    '设置服务失败'
    pass

class 设置冲突错误(Exception):
    '因命名空间在调用方读过之后发生了移动而被拒绝的写入'
    def __init__(自身,命名空间,期望,实际):
        '构造冲突错误'
        super().__init__('settings namespace "'+str(命名空间)+'" changed since it was read (expected revision '+str(期望)+', now '+str(实际)+')')#诊断原文不改
        自身.name='SettingsConflictError'
        自身.code='SETTINGS_CONFLICT'
        自身.expected=期望
        自身.actual=实际
