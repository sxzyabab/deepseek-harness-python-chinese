"""Web 应用的命令行提供方。"""
from ...启动.命令行 import 命令,解析命令行
from . import 网页启动服务键

__all__=['名称','依赖','网页启动服务键','应用']

名称='web-startup'
依赖=['cmdlineArgs']

def 网页命令():
    """本应用的命令：其旗标、描述与帮助文本。"""
    return (命令()
        .name('dsh --profile web')
        .description('提供 DeepSeek Harness 浏览器界面。')
        .helpOption('-h, --help','显示此帮助')
        .option('--host <host>','绑定主机')
        .option('--port <port>','监听端口；传 0 由操作系统选空闲端口')
        .option('--trusted-host <authority...>','/api 浏览器信任围栏额外接受的权威（主机或 主机:端口；可重复）')
        .addHelpText('after','''
示例:
  dsh --profile web                          按组合后的主机与端口提供服务
  dsh --profile web --port 8080              使用另一端口
''')
    )

def 应用(上下文):
    """把 Web 调用解析并作为普通 Cordis 服务提供。"""
    程序=网页命令()
    def 动作():
        """发布旗标；拒绝全接口绑定与非数字端口。选项为 dict。"""
        选项=程序.opts()
        主机=选项['host'] if 'host' in 选项 else None
        if 主机=='0.0.0.0':
            程序.error('error: 出于安全故意暂不支持 --host 0.0.0.0：会把远程代码执行暴露到网络；请改用 127.0.0.1')
        端口=选项['port'] if 'port' in 选项 else None
        if 端口 is not None and not str(端口).isdigit():
            程序.error('error: --port 必须是数字，实际为 '+repr(端口))
        受信=选项['trustedHost'] if 'trustedHost' in 选项 else []
        载荷={'trustedHosts':list(受信)}
        if 主机 is not None:
            载荷['host']=主机
        if 端口 is not None:
            载荷['port']=int(端口)
        上下文.提供服务(网页启动服务键,载荷)
    程序.action(动作)
    解析命令行(上下文,程序)

name=名称
inject=依赖
apply=应用
