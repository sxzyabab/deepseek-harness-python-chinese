class 基础压缩错误(Exception):
    '基础压缩包的异常基类'

class 目标压力配置错误(基础压缩错误):
    '目标特有压力配置失败，可抑制重复警告'

    def __init__(自身,目标键,消息):
        '记下用作警告键的精确提供方/模型路由与可操作的配置失败细节'
        super().__init__(消息)#交给基类
        自身.targetKey=目标键#警告键
        自身.message=消息#诊断文案
        自身.name='TargetPressureConfigError'#错误名

class 表面已变错误(基础压缩错误):
    '与摘要器及收缩失败区分开，以便手动调用方可分别报告两种原因'
    pass#标记类
