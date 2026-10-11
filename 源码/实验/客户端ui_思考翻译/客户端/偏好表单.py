'用共享插件表单暂存翻译偏好'
from ....客户端.ui_基础界面组件.表单模型 import 设置表单模型,设置文本字段
from ..偏好 import 提供方偏好,语言偏好模式

__all__=['翻译偏好表单']

def 解析提供方(文本):
    '空草稿清除；不在清单里则挡住保存'
    提供方=文本.strip()
    if 提供方=='':
        return {'kind':'clear'}
    if 提供方 in 提供方偏好:
        return {'kind':'set','value':提供方}
    return None

def 解析语言(文本):
    'auto 或语言代码才写入'
    修剪=文本.strip()
    if 语言偏好模式.fullmatch(修剪) is not None:
        return {'kind':'set','value':修剪}
    return None

class 翻译偏好表单:
    '暂存提供方和语言，保存时一次写入'
    def __init__(自身,作用域):
        '用共享设置表单暂存两项'
        提供方字段=设置文本字段('provider')
        提供方字段['parse']=解析提供方
        语言字段=设置文本字段('targetLanguage')
        语言字段['parse']=解析语言
        自身.表单=设置表单模型(作用域,[提供方字段,语言字段])
        def 投影():
            '外壳加上两个字段'
            return {
                **自身.表单.外壳(),
                'provider':自身.表单.字段('provider'),
                'targetLanguage':自身.表单.字段('targetLanguage'),
            }
        自身.状态=自身.表单.绑定(投影)

    def 注入(自身):
        '草稿快照与共享编辑动作'
        return {'hooks':{'translationForm':自身.状态},**自身.表单.动作()}

    def 拆除(自身):
        '释放已接受偏好订阅'
        自身.表单.拆除()
