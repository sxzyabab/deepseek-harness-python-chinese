"""一次性应用的命令行提供方。

对齐上游 `headless/src/startup.ts`。公开面仅中文名。
"""
from cmdline import 命令,解析命令行#命令行解析

__all__=['名称','注入','无头启动服务键','应用']#仅中文公开名

名称='headless-startup'#插件名
注入=['cmdlineArgs']#依赖命令行参数
无头启动服务键='headlessStartup'#启动服务键

def 无头命令():#构造无头命令
    """本应用的命令：任务位置参数、其描述与帮助文本。"""
    return (命令()#新程序
        .name('dsh --profile headless')#程序名
        .description('Answer one task, print the final assistant message, and exit.')#描述
        .helpOption('-h, --help','show this help')#帮助选项
        .argument('[task...]','the task text; multiple words are joined by spaces')#任务位置参数
        .addHelpText('after','''
Examples:
  dsh --profile headless "run the tests"     answer one task and exit
''')#帮助示例
    )#结束

def 应用(上下文):#安装无头启动解析
    """把一次性任务解析并作为普通 Cordis 服务提供。"""
    程序=无头命令()#构造命令
    def 动作():#解析成功后发布任务
        """发布任务；空任务拒绝。"""
        任务=' '.join(程序.args)#用空格拼接词
        if 任务.strip()=='':#空任务
            程序.error('error: a task is required, for example: dsh --profile headless "run the tests"')#空任务失败
        上下文.provide(无头启动服务键,{'task':任务})#发布启动服务
    程序.action(动作)#登记 action
    解析命令行(上下文,程序)#解析命令行
