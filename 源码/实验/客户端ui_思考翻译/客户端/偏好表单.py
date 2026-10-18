'用共享插件表单暂存翻译偏好'
from ....客户端.ui_基础界面组件.表单模型 import 设置表单模型,设置文本字段#暂存表单
from ..偏好 import 提供方偏好,语言偏好模式#与宿主同一套校验

__all__=['翻译偏好表单']


class 翻译偏好表单:
    '暂存提供方和语言，保存时一次写入'
    def __init__(自身,作用域):
        '用共享设置表单暂存两项'
        提供方字段=dict(设置文本字段('provider'))#先拿文本字段

        def 解析提供方(文本):
            '空草稿清除。不在清单里则挡住保存'
            提供方=文本.strip()#去掉空白
            if 提供方=='':
                return {'kind':'clear'}#与复位一样
            if 提供方 in 提供方偏好:
                return {'kind':'set','value':提供方}#写入这项
            return None#挡住保存

        提供方字段['parse']=解析提供方#换掉默认解析
        语言字段=dict(设置文本字段('targetLanguage'))#目标语言

        def 解析语言(文本):
            'auto 或语言代码才写入'
            修剪=文本.strip()#去掉空白
            if 语言偏好模式.fullmatch(修剪) is None:
                return None#挡住保存
            return {'kind':'set','value':修剪}#写入修剪后的代码

        语言字段['parse']=解析语言#换掉默认解析
        自身.表单=设置表单模型(作用域,[提供方字段,语言字段])#两项一起保存
        自身.状态=自身.表单.绑定(自身.投影)#槽位读的快照

    def 投影(自身):
        '外壳叠上提供方和目标语言'
        return {
            **自身.表单.外壳(),#可用、可写、保存中
            'provider':自身.表单.字段('provider'),#提供方草稿
            'targetLanguage':自身.表单.字段('targetLanguage'),#语言草稿
        }

    def 注入(自身):
        '草稿快照与共享编辑动作'
        return {'hooks':{'translationForm':自身.状态},**自身.表单.动作()}#槽位份额

    def 拆除(自身):
        '释放已接受偏好订阅'
        自身.表单.拆除()#退订
