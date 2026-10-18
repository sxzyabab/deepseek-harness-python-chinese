'ctx.directoryPicker：网页宿主让操作者选工作区目录。后端给出 native 或 browse，消费方按 kind 分支；未知 kind 藏起选择入口，而不是失败'
from ...依赖.cordis.服务 import 服务#服务基类
from . import 类型,异常#同目录模块。导入包时执行它们的顶层
from .类型 import 目录项,目录列表#浏览一层的结构
from .异常 import 目录选择器错误,目录选择器错误码#带码失败与关闭码

__all__=['目录选择器','默认',#服务与默认导出
'原生目录选择能力','浏览目录选择能力',#两种交互形状
'目录选择器能力表','目录选择器能力',#形状表与联合
'目录选择器错误','目录选择器错误码',#带码失败
'目录项','目录列表',#浏览结构
'类型','异常',]#同目录模块


#native 在宿主屏幕上开一次系统框。browse 给应用内浏览器逐层列目录和建子目录
class 原生目录选择能力:#一次系统目录框
    '在宿主屏幕上打开一次系统目录框。kind 为 native'
    kind='native'#能力种类
    def pick(自身,信号):#打开选择框
        '打开选择框并等待操作者。信号中止时结束选择框。返回绝对路径，取消则为 None'
        raise NotImplementedError#原生后端实现


class 浏览目录选择能力:#应用内逐层浏览
    '列出一层并创建子目录。不在宿主屏幕上画东西。kind 为 browse'
    kind='browse'#能力种类
    def list(自身,路径=None,信号=None):#列一层
        """列出一层目录。
        路径省略时列家目录。信号中止扫描，并按中止原因拒绝。
        目标不是完全限定，或列不出来，抛目录选择器错误，码为 directory-unreadable。
        返回这一层和祖先。后端截断完整结果时 truncated 为真
        """
        raise NotImplementedError#浏览后端实现

    def createDirectory(自身,路径,名称):#建子目录
        """在已有父目录下建一个非空白单段子目录，名字不含分隔符，也不是 . 或 ..。
        返回新目录绝对路径。
        已存在为 directory-exists。父路径不是完全限定，或其他失败，为 directory-create-failed
        """
        raise NotImplementedError#浏览后端实现


#按 kind 并入形状。未知 kind 时消费方藏起选择入口，这个缝不因此失败
class 目录选择器能力表:#内建 kind → 交互形状
    '条目的 kind 字面量必须等于键。新后端并入自己的形状，不改这个包'
    native=原生目录选择能力#系统目录框
    browse=浏览目录选择能力#应用内浏览


目录选择器能力=原生目录选择能力 |浏览目录选择能力#能力表里两种形状的联合


class 目录选择器(服务):#抽象目录选择服务
    '子类实现 capability()，并以插件加载。一个上下文只能有一个。能力对象在服务存活期间保持同一身份，消费方可跨调用抓住它'
    def __init__(自身,上下文):#登记 directoryPicker
        '以 directoryPicker 名安装服务'
        super().__init__(上下文,'directoryPicker')#再加载第二个由上下文拒绝

    def capability(自身):#当前交互能力
        '返回带 kind 的稳定能力对象。消费方按 kind 分支'
        raise NotImplementedError#子类实现


默认=目录选择器#默认导出
default=默认#加载器槽
