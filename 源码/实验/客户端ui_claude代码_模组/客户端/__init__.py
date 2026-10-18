'浏览器入口：挂上桥的 Remote，并在提示上方登记条带'
from . import 挂载,条带,文案#同目录模块，导入即执行顶层
from .挂载 import 依赖,登记界面#依赖清单与登记回调

__all__=['挂载','条带','文案','依赖','应用']

远程贡献={
    'package':'@deepseek-ai/dsh-experimental-claude-code-mods',#上游 ./remote 的包名
    'descriptors':[],#描述符不在本包
}

def 应用(上下文,配置=None):
    '挂上桥的 Remote 并登记条带。返回卸除函数'
    卸远程=getattr(上下文.remote,'$mount')(远程贡献)#安装远程贡献
    界面=上下文.依赖启动(['remote.claudeCodeMods','slots','locale'],登记界面)#依赖齐了再登记
    try:#登记失败要卸掉 Remote
        界面.等待()#启动错误在这里抛出
    except Exception as 错误:#登记没成
        界面.拆除()#卸掉半成品界面
        卸远程()#卸掉 Remote
        raise 错误#原错误继续抛
    def 卸除():
        '卸掉条带登记和 Remote'
        界面.拆除()#先界面
        卸远程()#再 Remote
    return 卸除#调用方拿去拆除

inject=依赖#加载器读 inject
apply=应用#加载器读 apply
