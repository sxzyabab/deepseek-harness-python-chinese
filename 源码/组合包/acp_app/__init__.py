"""ACP profile 的命令行与 stdin 生命周期提供方。

解析成功后发布 `ACP应用启动服务`；ACP bridge 等待该服务，因此 help 不会启动任何传输。

对齐上游 `@deepseek-ai/dsh-acp-app`。公开面仅中文名。
"""
from ...启动.命令行 import 命令,解析命令行,标准输入结束退出#命令行助手

__all__=['名称','注入','ACP应用启动服务','应用']#仅中文公开名

名称='acp-app-startup'#插件名
注入=['cmdlineArgs']#依赖命令行参数服务
ACP应用启动服务='acpAppStartup'#启动就绪服务名

def ACP命令():#构建ACP命令
    """构建本应用的零选项命令与帮助。"""
    return (命令()#新建program
        .name('dsh --profile acp')#命令显示名
        .description('Serve automation clients over Agent Client Protocol stdio.')#命令描述
        .helpOption('-h, --help','show this help')#帮助选项
        .addHelpText('after','''
Example:
  dsh --profile acp     serve ACP until the client disconnects
''')#追加示例帮助
    )#结束

def 应用(上下文):#安装插件
    """接受一次 ACP profile 调用，发布就绪，并把 EOF 绑到启动器的有界关闭。"""
    程序=ACP命令()#构建命令
    def 动作():#解析成功动作
        """stdin EOF 触发有界关闭并发布启动就绪。"""
        标准输入结束退出(上下文,'acp-app.stdin')#stdin EOF 触发有界关闭
        上下文.provide(ACP应用启动服务,{'accepted':True})#发布启动就绪
    程序.action(动作)#登记动作
    解析命令行(上下文,程序)#解析并执行命令行

apply=应用#Cordis入口
