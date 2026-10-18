'macOS 原生计算机操作提供方。先准备原生组件，再交给共享执行器登记工具'
import os,platform,sys
from ...内核.智能体循环.中止与并发 import 中止控制器
from ..计算机操作 import 计算机操作后端,计算机操作配置,安装计算机操作
from ..计算机操作.原生客户端 import 若已中止则抛出
from .原生构建 import 等到,本机原生架构,准备原生可执行文件
from .共享原生 import 创建共享原生通道
from .指引 import 指引

__all__=['名称','依赖','说明','应用']

def 节点架构():
    '把 Python 的机器名收成 Node 的 arm64 或 x64'
    机器=os.uname().machine if hasattr(os,'uname') else platform.machine()#机器名
    机器=机器.lower()#忽略大小写
    if 机器 in ('arm64','aarch64'):#苹果芯片
        return 'arm64'#Node 名
    if 机器 in ('x86_64','amd64','x64'):#英特尔
        return 'x64'#Node 名
    return 机器#原样交给架构检查

def 应用(上下文,配置):
    '辅助路径必须是绝对路径。未给出时按本机架构准备包内可执行文件'
    if 配置.辅助路径 is not None:#调用方指定了可执行文件
        if not os.path.isabs(配置.辅助路径):#必须绝对
            raise RuntimeError('dsh-cua helperPath must be absolute')#拒绝
        安装计算机操作(上下文,配置,计算机操作后端(配置.辅助路径,创建共享原生通道,指引,说明))#直接登记
        return#结束
    架构=本机原生架构(sys.platform,节点架构())#darwin arm64 或 x64
    控制器=中止控制器()#准备可以被拆除取消
    包根=os.path.dirname(os.path.abspath(__file__))#这个提供方目录
    已准备=准备原生可执行文件({#准备规格
        'packageRoot':包根,#包根
        'architecture':架构,#架构
        'subprocess':上下文.subprocess,#受管子进程
        'timeoutMs':配置.构建超时毫秒,#准备截止
        'graceMs':配置.宽限毫秒,#进程宽限
        'signal':控制器.信号,#取消
    })#期约
    def 挂拆除():
        '拆除只等准备结束，失败由应用自己抛出'
        def 拆除():
            '取消并吞掉准备失败'
            控制器.中止()#取消
            def 吞掉(_值=None):
                '拆除不把准备失败再抛一次'
                return None#吞掉
            已准备.然后(吞掉,吞掉)#两边都吞
        return 拆除#拆除器
    上下文.副作用(挂拆除,'dsh-cua.native-preparation')#随本插件
    辅助路径=等到(已准备)#阻塞到可执行文件就绪
    若已中止则抛出(控制器.信号)#准备完已经被取消
    安装计算机操作(上下文,配置,计算机操作后端(辅助路径,创建共享原生通道,指引,说明))#登记工具

名称='experimental-cua-macos'#插件名
依赖=['computerUse','tools','systemPrompt','subprocess','agents']#必需服务
说明='Inspect macOS permissions, select an application and window, read AX state, capture screenshots or dispatch input. Use appHandle from getApp; verify actions by reading fresh state.'#工具说明
name=名称#框架槽
inject=依赖#框架槽
Config=计算机操作配置#框架槽
apply=应用#框架槽
default=应用#框架槽
