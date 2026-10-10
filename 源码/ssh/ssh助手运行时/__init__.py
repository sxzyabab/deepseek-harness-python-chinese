'私有可执行引导：一次分发已打包的 SSH 辅助或 PTC 工作进程'
import os,sys#环境选择与打包探测
from ..ssh.入口 import 主入口#OpenSSH 进程入口
from ...子进程.子进程.控制 import 打开继承控制通道#继承控制管
from ...ptc运行时.ptc运行时_node.进程 import 运行节点主程序#子进程主程序
from ...ptc运行时.ptc运行时_node.进程入口 import 程序进程#本进程状态

__all__=['ssh助手运行时错误','运行ssh助手运行时']#仅中文公开名

class ssh助手运行时错误(Exception):#本包异常
    'SSH 助手运行时拒绝继续'
    def __init__(自身,消息):#记下消息
        '用中文消息构造'
        super().__init__(消息)#消息

def 运行ssh助手运行时():#一次分发
    '必须从已打包的可执行文件运行。PTC 标记优先；没有运行器选择时跑 SSH 辅助'
    if not hasattr(sys,'frozen'):#不是打包可执行
        raise ssh助手运行时错误('SSH 助手运行时必须从已打包的可执行文件运行')#拒绝
    #先消费运行器选择，再看 PTC。两者同时给出时只跑 PTC
    选择=os.environ.pop('DSH_SUBPROCESS_RUNNER',None)#读后删除，缺席为 None
    if os.environ.get('DSH_PTC_RUNTIME_NODE')=='1':#打包 PTC 工作进程
        os.environ.pop('DSH_PTC_RUNTIME_NODE',None)#消费标记
        状态=程序进程()#绑到当前进程
        运行节点主程序(打开继承控制通道(),int(sys.argv[1]),状态)#上限在第一个参数
        状态.控制读线程.join()#读完再取退出码
        码=状态.exitCode#退出码
        sys.exit(0 if 码 is None else 码)#进程出口
    if 选择 is not None:#已给出运行器选择
        raise ssh助手运行时错误('SSH 助手运行时没有子进程运行器入口')#无法执行该选择
    主入口()#SSH 辅助
