"""浏览器主题偏好与插件激活前调色板的宿主登记。

对齐上游 `@deepseek-ai/dsh-client-ui-theme`。公开面仅中文名。在可选宿主服务被组合进来时，登记持久化主题分区与初始主题的 index 变换。浏览器半（ThemeRuntime、外观行、React/CSS）未迁入本 Python 树。
"""
from settings import 设置命名空间#设置命名空间品牌构造
from .启动主题 import 注入启动主题#主题启动脚本注入
from .主题设置 import (#主题设置常量与判定
    默认偏好,#默认偏好
    主题偏好字段,#偏好字段名
    主题偏好们,#内置偏好枚举
    主题设置命名空间,#设置命名空间字面量
    主题设置模式,#分区模式
    是否主题偏好,#偏好收窄
)#来自主题设置模块

__all__=[#仅中文公开名
    '应用',
    '默认偏好',
    '主题偏好字段',
    '主题偏好们',
    '主题设置命名空间',
    '主题设置模式',
    '是否主题偏好',
]#公开面结束

主题命名空间=设置命名空间(主题设置命名空间)#品牌化主题设置命名空间

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 读偏好(上下文):#读当前主题偏好
    """读取已登记的偏好；没有设置提供方时用模式默认值。"""
    设置服务=上下文.get('settings')#可选 settings 服务
    if 设置服务 is None:#无提供方则用默认
        return 默认偏好#默认
    分区=设置服务.get(主题命名空间)#读主题分区
    if 分区 is None:#无分区则用默认
        return 默认偏好#默认
    return 取字段(分区,'preference',默认偏好)#返回已登记偏好

def 应用(上下文):#安装宿主主题插件
    """在可选宿主服务被组合进来时，登记持久化主题分区与初始主题的 index 变换。"""
    def 设置接线(设置上下文):#等 settings 出现再登记
        """登记主题设置分区。"""
        设置上下文.settings.登记(主题命名空间,主题设置模式)#登记主题设置分区
    上下文.inject(['settings'],设置接线)#结束 inject
    def 网页接线(网页上下文):#等 webServer 出现再挂 index tap
        """按当前偏好注入启动主题。"""
        def 挂上():#登记初始主题引导
            """挂上 tapIndex 并在拆除时卸掉。"""
            return 网页上下文.webServer.tapIndex(lambda 网页:注入启动主题(网页,读偏好(上下文)))#按当前偏好注入启动主题
        网页上下文.effect(挂上,'client-ui-theme: initial theme bootstrap')#effect 标签
    上下文.inject(['webServer'],网页接线)#结束 inject
