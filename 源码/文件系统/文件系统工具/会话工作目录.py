"""推导文件系统工具解析相对路径所用的工作目录：调用方 agent 的每会话 workspace（exec.agent.session.header.cwd），使每个会话的 read/write/edit 作用在它自己的 workspace 上，而不是服务器启动目录——镜像 dsh-tool-bash 把 bash workdir 默认到会话 cwd。非 agent 调用返回 None，把回退留给提供方，而不是在工具边界读 process.cwd()。对齐上游 tool-fs/src/session-cwd.ts。"""
import re#父目录段匹配
from ...沙盒.沙盒 import 规范路径#导入规范路径
from .辅助 import 试取,取字段#字段读取

父路径段=re.compile(r'(?:^|[\\/])\.\.(?:[\\/]|$)')#匹配路径中的父目录段

def 会话工作目录(执行,请求路径):#推导此次调用的会话cwd
    """此次调用的会话 workspace cwd；不适用时为 None。父目录穿越会使符号链接 cwd 的文件系统身份可观察，因此有穿越时规范化 cwd。"""
    智能体=试取(执行,'agent')#调用方智能体
    if 智能体 is None:#非agent调用
        return None#交给提供方默认
    工作目录=试取(取字段(取字段(智能体,'session'),'header'),'cwd')#取出会话头上的cwd
    if 工作目录 is None:#无cwd
        return 工作目录#原样空
    if (not 父路径段.search(工作目录)) and (not 父路径段.search(请求路径)):#双方都无父目录穿越
        return 工作目录#原样返回
    return 规范路径(工作目录)#规范化cwd，避免符号链接身份泄漏

def 会话解析选项(执行,请求路径,政策工作区根=None):#组装resolve所用的cwd与取消信号
    """所有面向模型的文件系统工具共享的解析选项。政策根（变更携带沙箱策略时）优先，否则会话 cwd；同时带上取消信号。"""
    工作目录=政策工作区根 if 政策工作区根 is not None else 会话工作目录(执行,请求路径)#策略根优先
    选项={'signal':试取(执行,'signal')}#带上取消信号
    if 工作目录 is not None:#有cwd
        选项['cwd']=工作目录#放入cwd
    return 选项#解析选项
