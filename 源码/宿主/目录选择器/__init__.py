'ctx.directoryPicker：网页宿主让操作者选工作区目录的能力缝'
from ...依赖.cordis.服务 import 服务#服务基类
from .类型 import 目录项,目录列表#再导出浏览结构
from .异常 import 目录选择器错误#再导出失败

__all__=['目录选择器','目录选择器错误','目录项','目录列表']#仅中文公开名

class 目录选择器(服务):#抽象目录选择服务
    '子类实现 capability()，并以插件加载；一个上下文里只能有一个'
    def __init__(自身,上下文):#登记 directoryPicker
        '以 directoryPicker 名安装服务'
        super().__init__(上下文,'directoryPicker')#服务名

    def capability(自身):#当前交互能力
        '返回带 kind 的稳定能力对象'
        raise NotImplementedError#子类实现

default=目录选择器#Cordis 默认导出
