'目录选择缝的原生后端：在宿主屏幕上打开一次系统目录框'
from ..目录选择器 import 目录选择器#缝
from .原生选择 import 选原生目录#跨平台选择

__all__=['原生目录选择器','选原生目录']#仅中文公开名

class 原生能力:#稳定的 native 能力对象
    'pick 转到选原生目录'
    kind='native'#能力种类
    def pick(自身,信号):#打开系统选择框
        '返回绝对路径或 None'
        return 选原生目录(信号)#转发

class 原生目录选择器(目录选择器):#ctx.directoryPicker 的原生实现
    '能力对象在服务存活期间保持同一身份'
    def __init__(自身,上下文,配置=None):#构造
        '登记服务'
        super().__init__(上下文)#登记 directoryPicker
        自身.原生能力=原生能力()#稳定能力

    def capability(自身):#原生能力
        '返回稳定的 native 能力对象'
        return 自身.原生能力#同一对象

default=原生目录选择器#类插件
