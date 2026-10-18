'浏览器本地记住的壳。宿主发现结果决定这条路径现在还能不能用'
from ....客户端.模块.客户端.通告 import 取握手窗口

__all__=['首选命令解释器','记住命令解释器']#两处使用，留成函数

壳键='dsh.terminal.shell'#存储键


def 首选命令解释器():
    '读取上次选择的壳路径。存储不可用时为空'
    try:#私密浏览或没有 localStorage
        return 取握手窗口().localStorage.getItem(壳键)#上次的路径
    except Exception as 存储不可用:#读不到
        return None#这次启动仍可用


def 记住命令解释器(路径):
    '记住选中的壳。存储失败不挡住这次启动'
    try:#没有存储或配额满了就跳过
        取握手窗口().localStorage.setItem(壳键,路径)#写下路径
    except Exception as 存储不可用:#私密浏览或配额失败
        return#这次启动仍可用
