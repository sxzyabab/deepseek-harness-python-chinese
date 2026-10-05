from .....工具.值 import 断言永不
from .....基础设施.通用工具 import 紧凑json编码

__all__=['聊天渲染键']

def 聊天渲染键(条目):
    '与呈现模式无关的渲染位置身份。条目为 dict'
    种=条目['kind']
    if 种=='node':
        组分=条目['groupPart'] if 'groupPart' in 条目 else None
        return 紧凑json编码(['node',条目['key'],组分])
    if 种=='group':
        return 紧凑json编码(['group',条目['key']])
    return 断言永不(条目)
