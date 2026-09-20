"""ACP profile 的命令行与 stdin 生命周期提供方。

解析成功后发布 `ACP应用启动服务`；ACP bridge 等待该服务，因此 help 不会启动任何传输。
"""
from ...启动.命令行 import 命令,解析命令行,标准输入结束退出

__all__=['名称','依赖','ACP应用启动服务','应用']

名称='acp-app-startup'
依赖=['cmdlineArgs']
ACP应用启动服务='acpAppStartup'

def ACP命令():
    """构建本应用的零选项命令与帮助。"""
    return (命令()
        .name('dsh --profile acp')
        .description('经 Agent Client Protocol 的 stdio 为自动化客户端提供服务。')
        .helpOption('-h, --help','显示此帮助')
        .addHelpText('after','''
示例:
  dsh --profile acp     提供 ACP 服务直到客户端断开
''')
    )

def 应用(上下文):
    """接受一次 ACP profile 调用，发布就绪，并把 EOF 绑到启动器的有界关闭。"""
    程序=ACP命令()
    def 动作():
        """stdin EOF 触发有界关闭并发布启动就绪。"""
        标准输入结束退出(上下文,'acp-app.stdin')
        上下文.提供服务(ACP应用启动服务,{'accepted':True})
    程序.action(动作)
    解析命令行(上下文,程序)

name=名称
inject=依赖
apply=应用
