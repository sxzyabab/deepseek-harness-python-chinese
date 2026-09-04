"""SDK profile 的命令行与 stdin 生命周期提供方。

解析成功后发布 `SDK应用启动服务`；JSON-RPC 服务器等待该服务，因此 help 不会启动任何传输。

对齐上游 `@deepseek-ai/dsh-sdk-app`。公开面仅中文名。
"""
from ...启动.命令行 import 命令,解析命令行,标准输入结束退出#命令行助手
from ...依赖.schemastery import 字符串字段#配置字段

__all__=['名称','注入','SDK应用启动服务','配置','应用']#仅中文公开名

名称='sdk-app-startup'#插件名
注入=['cmdlineArgs']#依赖命令行参数服务
SDK应用启动服务='sdkAppStartup'#启动就绪服务名

配置={#SDK stdio 启动配置
    'profile':字符串字段(默认值='sdk'),#帮助与诊断中渲染的 profile 名
}#配置结束

def SDK命令(配置档名):#构建SDK命令
    """按 profile 名构建本应用的零选项命令与帮助。"""
    return (命令()#新建program
        .name(f'dsh --profile {配置档名}')#命令显示名
        .description('Serve DeepSeek Harness SDK clients over stdio JSON-RPC.')#命令描述
        .helpOption('-h, --help','show this help')#帮助选项
        .addHelpText('after',f'''
Example:
  dsh --profile {配置档名}     serve one SDK runtime until its client disconnects
''')#追加示例帮助
    )#结束

def 应用(上下文,配置对象=None):#安装插件
    """接受一次 SDK profile 调用，发布就绪，并把 EOF 绑到启动器的有界关闭。"""
    if 配置对象 is None:#缺省配置
        配置对象={}#空映射
    配置档名=配置对象.get('profile') if isinstance(配置对象,dict) else getattr(配置对象,'profile',None)#取 profile
    if not 配置档名:#缺席
        配置档名='sdk'#默认
    程序=SDK命令(配置档名)#按 profile 构建命令
    def 动作():#解析成功动作
        """stdin EOF 触发有界关闭并发布启动就绪。"""
        标准输入结束退出(上下文,'sdk-app.stdin')#stdin EOF 触发有界关闭
        上下文.provide(SDK应用启动服务,{'accepted':True})#发布启动就绪
    程序.action(动作)#登记动作
    解析命令行(上下文,程序)#解析并执行命令行

apply=应用#Cordis入口
