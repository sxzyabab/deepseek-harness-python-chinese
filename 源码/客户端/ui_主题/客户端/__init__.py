"""浏览器主题注册表与外观偏好行登记。

对齐上游 `ui-theme/src/client/index.ts` 的 apply 面。公开面仅中文名。
ThemeRuntime 无 DOM；样式表字符串见 `.样式`（本包已落盘 design-platform 等全部分片）。
"""
from ..主题设置 import 主题设置命名空间#命名空间字面
from .文案 import 设置命名空间,中文,英文,主题文案键#词典
from .主题运行时 import 主题运行时,解析活动主题,合并令牌覆盖,内置主题,内置检视令牌#运行时
from .外观行 import 外观行,立方顺序,样式表 as 外观样式表#外观行
from .外观行存储 import 创建外观行存储#存储
from .样式 import (#样式合计
    基线样式,滚动条样式,设计平台样式,代码高亮样式,渐变阴影样式,字号令牌样式,
    主题样式合计,样式文件名,说明 as 样式说明,
)#样式

__all__=[#仅中文公开名
    '注入','应用','设置命名空间','中文','英文','主题文案键',
    '主题运行时','解析活动主题','合并令牌覆盖','内置主题','内置检视令牌',
    '外观行','立方顺序','创建外观行存储','外观样式表',
    '基线样式','滚动条样式','设计平台样式','代码高亮样式','渐变阴影样式','字号令牌样式',
    '主题样式合计','样式文件名','样式说明',
]#公开面结束

注入=['slots','locale','connection','remote','settingsScope']#依赖

def 应用(上下文):
    """提供主题服务，并登记 General 区外观行。"""
    宿主=上下文.settingsScope.bind({'namespace':主题设置命名空间})#绑定作用域
    def 发出(名,载荷):
        """转发广播。"""
        上下文.广播(名,载荷)#发
    主题=主题运行时(发出=发出,宿主=宿主)#运行时
    上下文.提供服务('theme',主题)#提供
    def 登记词典():
        """登记外观行词典。"""
        return 上下文.locale.register(设置命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-theme: settings row dictionaries')#词典
    行存储=创建外观行存储()#外观存储
    已烤=None#已绑动作

    def 同步(快照):
        """已烤才同步。快照是 dict。"""
        if 已烤 is not None:#有
            已烤['sync'](快照['preference'],快照['revision'])#同步
        else:#存储直写
            行存储['sync'](快照['preference'],快照['revision'])#同步

    上下文.监听('theme/change',同步)#订阅

    def 注入面(动作=None):
        """记下已烤动作并补当前快照。setTheme 是注入面键名。"""
        nonlocal 已烤#闭包
        if 动作 is not None:#有烤
            已烤=动作#记下
        同步(主题.getTheme())#补上
        def 写入主题(标识):
            """写入偏好。"""
            主题.setTheme(标识)#写
        return {'setTheme':写入主题}#注入

    def 登记行():
        """登记外观行。"""
        return 上下文.slots.register({#外观行
            'name':'settings.general.item',#槽
            'id':'appearance',#id
            'order':10,#序
            'store':行存储,#存储
            'locale':设置命名空间,#文案
            'inject':注入面,#注入
        },外观行)#组件
    上下文.slots.inject('settings.general.item',登记行)#外观行

inject=注入#框架槽
apply=应用#框架槽
