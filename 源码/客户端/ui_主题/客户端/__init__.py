from ..主题设置 import 主题设置命名空间#命名空间字面
from .文案 import 设置命名空间,中文,英文,主题文案键#词典
from .主题运行时 import 主题运行时,解析活动主题,合并令牌覆盖,内置主题,内置检视令牌#运行时
from .外观行 import 外观行,立方顺序,样式表 as 外观样式表#外观行
from .字号行 import 字号行,样式表 as 字号样式表#字号行
from .外观行存储 import 创建外观行存储,创建字号行存储#存储
from .样式 import (
    基线样式,滚动条样式,设计平台样式,代码高亮样式,渐变阴影样式,字号令牌样式,
    主题样式合计,样式文件名,说明 as 样式说明,
)

__all__=[
    '依赖','应用','设置命名空间','中文','英文','主题文案键',
    '主题运行时','解析活动主题','合并令牌覆盖','内置主题','内置检视令牌',
    '外观行','立方顺序','创建外观行存储','外观样式表',
    '字号行','创建字号行存储','字号样式表',
    '基线样式','滚动条样式','设计平台样式','代码高亮样式','渐变阴影样式','字号令牌样式',
    '主题样式合计','样式文件名','样式说明',
]

依赖=['slots','locale','remote','configForms']#槽位、文案、远程、配置表单

def 应用(上下文):
    """提供主题服务，并登记 General 区外观行与字号行。"""
    宿主=上下文.configForms.get(主题设置命名空间)
    def 发出(名,载荷):
        """转发广播。"""
        上下文.广播(名,载荷)
    主题=主题运行时(发出=发出,宿主=宿主)
    上下文.提供服务('theme',主题)
    def 登记词典():
        """登记外观行词典。"""
        return 上下文.locale.register(设置命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-theme: settings row dictionaries')
    行存储=创建外观行存储()
    已烤=None
    字号存储=创建字号行存储()
    字号已烤=None

    def 同步(快照):
        """已烤才同步。快照是 dict。"""
        if 已烤 is not None:
            已烤['sync'](快照['preference'],快照['revision'])
        else:
            行存储['sync'](快照['preference'],快照['revision'])
        if 字号已烤 is not None:
            字号已烤['sync'](快照['fontSize'],快照['revision'])
        else:
            字号存储['sync'](快照['fontSize'],快照['revision'])

    上下文.监听('theme/change',同步)

    def 注入面(动作=None):
        """记下已烤动作并补当前快照。"""
        nonlocal 已烤
        if 动作 is not None:
            已烤=动作
        同步(主题.getTheme())
        def 写入主题(标识):
            """写入偏好。"""
            主题.setTheme(标识)
        return {'setTheme':写入主题}

    def 登记行():
        """登记外观行。"""
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'appearance',
            'order':10,
            'store':行存储,
            'locale':设置命名空间,
            'inject':注入面,
        },外观行)
    上下文.slots.inject('settings.general.item',登记行)

    def 字号注入面(动作=None):
        """记下已烤动作并补当前快照。"""
        nonlocal 字号已烤
        if 动作 is not None:
            字号已烤=动作
        同步(主题.getTheme())
        def 写入字号(像素):
            """写入内容字号。"""
            主题.setFontSize(像素)
        return {'setFontSize':写入字号}

    def 登记字号行():
        """登记字号行。"""
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'font-size',
            'order':11,
            'store':字号存储,
            'locale':设置命名空间,
            'inject':字号注入面,
        },字号行)
    上下文.slots.inject('settings.general.item',登记字号行)

inject=依赖
apply=应用
