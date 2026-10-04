'JSONL 会话持久化失败与格式、代次、zstd 辅助失败'
from ..会话持久化.异常 import 持久化错误#持久化错误基类

__all__=[#仅中文公开名
    '会话已有写主错误','格式辅助错误','代次源变更错误','代次不支持迁移错误',
    '代次目标冲突错误','代次辅助错误','zstd辅助错误',
]#公开面结束

class 会话已有写主错误(持久化错误):#已有写主
    '另一持有者仍占锁时'
    def __init__(自身,标识):#构造
        '记下被争用的会话身份'
        自身.id=标识#会话id
        super().__init__(f'session {标识!s} is already owned by another writer')#文案

class 格式辅助错误(Exception):#格式辅助错误
    'JSONL 格式辅助抛出的 Error 风格异常'

class 代次源变更错误(Exception):#源变更
    '历史源在解码与迁移遍之后发生了变更'
    def __init__(自身,路径):#构造
        '记下修订已变的历史代'
        自身.path=路径#路径
        自身.name='JsonlGenerationSourceChangedError'#错误名
        super().__init__(f'historical session generation changed during migration: "{路径}"')#消息

class 代次不支持迁移错误(Exception):#不支持迁移
    '历史产物完好，但格式边拒绝其内容'
    def __init__(自身,来自版本,原因):#构造
        '记下源版本与格式边拒绝'
        自身.fromVersion=来自版本#源版本
        自身.reason=原因#原因
        自身.name='JsonlGenerationUnsupportedMigrationError'#错误名
        super().__init__(str(原因))#消息
        自身.__cause__=原因#cause

class 代次目标冲突错误(Exception):#目标冲突
    '当代文件名已指向不同或非法字节'
    def __init__(自身,路径,原因):#构造
        '记下阻止独占发布的目标'
        自身.path=路径#路径
        自身.reason=原因#原因
        自身.name='JsonlGenerationTargetConflictError'#错误名
        super().__init__(f'current session generation already exists at "{路径}": {原因}')#消息
        自身.__cause__=原因#cause

class 代次辅助错误(Exception):#代次辅助错误
    '代次模块抛出的 Error 风格异常'

class zstd辅助错误(Exception):#zstd 辅助错误
    'Zstandard 帧原语抛出的 Error 风格异常'
