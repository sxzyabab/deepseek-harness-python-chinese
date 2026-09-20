"""SDK profile 的命令行与 stdin 生命周期提供方。

解析成功后发布 `SDK应用启动服务`；JSON-RPC 服务器等待该服务，因此 help 不会启动任何传输。
"""
from ...启动.命令行 import 命令,解析命令行,标准输入结束退出
from ...依赖.schemastery import 字符串字段

__all__=['名称','依赖','SDK应用启动服务','配置','应用']

名称='sdk-app-startup'
依赖=['cmdlineArgs']
SDK应用启动服务='sdkAppStartup'

配置={
    'profile':字符串字段(默认值='sdk'),
}

def SDK命令(配置档名):
    """按 profile 名构建本应用的零选项命令与帮助。"""
    return (命令()
        .name(f'dsh --profile {配置档名}')
        .description('经 stdio JSON-RPC 为 DeepSeek Harness SDK 客户端提供服务。')
        .helpOption('-h, --help','显示此帮助')
        .addHelpText('after',f'''
示例:
  dsh --profile {配置档名}     为一个 SDK 运行时服务直到其客户端断开
''')
    )

def 应用(上下文,配置对象=None):
    """接受一次 SDK profile 调用，发布就绪，并把 EOF 绑到启动器的有界关闭。"""
    if 配置对象 is None:
        配置对象={}
    配置档名=配置对象.get('profile') if isinstance(配置对象,dict) else getattr(配置对象,'profile',None)
    if not 配置档名:
        配置档名='sdk'
    程序=SDK命令(配置档名)
    def 动作():
        """stdin EOF 触发有界关闭并发布启动就绪。"""
        标准输入结束退出(上下文,'sdk-app.stdin')
        上下文.提供服务(SDK应用启动服务,{'accepted':True})
    程序.action(动作)
    解析命令行(上下文,程序)

name=名称
inject=依赖
apply=应用
Config=配置
