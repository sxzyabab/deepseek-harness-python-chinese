"""Web 应用的命令行提供方。

对齐上游 `web-app/src/startup.ts`。公开面仅中文名。
"""
from ...启动.cmdline import 命令,解析命令行#命令行解析
from . import 网页启动服务键#启动服务键

__all__=['名称','注入','网页启动服务键','应用']#仅中文公开名

名称='web-startup'#插件名
注入=['cmdlineArgs']#依赖内部参数服务

def 网页命令():
    """本应用的命令：其旗标、描述与帮助文本。"""
    return (命令()#新建
        .name('dsh --profile web')#程序名
        .description('Serve the DeepSeek Harness browser UI.')#描述
        .helpOption('-h, --help','show this help')#帮助旗标
        .option('--host <host>','bind host')#绑定主机
        .option('--port <port>','listen port; pass 0 to let the OS pick a free one')#监听端口
        .option('--trusted-host <authority...>','extra authority the /api browser-trust fence accepts (host or host:port; repeatable)')#额外受信
        .addHelpText('after','''
Examples:
  dsh --profile web                          serve on the composed host and port
  dsh --profile web --port 8080              serve on another port
''')#帮助示例
    )#结束

def 应用(上下文):
    """把 Web 调用解析并作为普通 Cordis 服务提供。"""
    程序=网页命令()#构造程序
    def 动作():
        """发布旗标；拒绝全接口绑定与非数字端口。选项为 dict。"""
        选项=程序.opts()#取出解析选项
        主机=选项['host'] if 'host' in 选项 else None#绑定主机
        if 主机=='0.0.0.0':#全接口尚未支持
            程序.error('error: --host 0.0.0.0 is intentionally not supported yet for safety: it would expose remote code execution to the network; use 127.0.0.1 instead')#安全拒绝
        端口=选项['port'] if 'port' in 选项 else None#端口
        if 端口 is not None and not str(端口).isdigit():#端口不是数字
            程序.error('error: --port must be a number, got '+repr(端口))#用法错误
        受信=选项['trustedHost'] if 'trustedHost' in 选项 else []#受信权威；?? 缺席才空
        载荷={'trustedHosts':list(受信)}#受信权威
        if 主机 is not None:#有 host
            载荷['host']=主机#带上
        if 端口 is not None:#有 port
            载荷['port']=int(端口)#转成数字
        上下文.提供服务(网页启动服务键,载荷)#发布启动服务
    程序.action(动作)#登记
    解析命令行(上下文,程序)#解析

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
