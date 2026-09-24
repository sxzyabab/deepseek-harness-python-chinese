from .....工具.值 import 断言永不
import json

__all__=['聊天渲染键']

def 聊天渲染键(条目):
    """与呈现模式无关的渲染位置身份。条目为 dict。"""
    种=条目['kind']
    if 种=='node':
        组分=条目['groupPart'] if 'groupPart' in 条目 else None
        return json.dumps(['node',条目['key'],组分],ensure_ascii=False,separators=(',',':'),allow_nan=False)
    if 种=='group':
        return json.dumps(['group',条目['key']],ensure_ascii=False,separators=(',',':'),allow_nan=False)
    return 断言永不(条目)
