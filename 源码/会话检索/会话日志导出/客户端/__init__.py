"""浏览器插件：拥有会话导出下载状态及其共享对话框。"""
from .控制器 import 会话日志下载控制器#控制器
from .区域设置 import 命名空间,简体中文,英文#文案

依赖=['slots','locale']#依赖
__all__=['应用','默认','会话日志下载控制器']#公开面

def 应用(上下文):#加载
    """提供下载控制器并登记区域文案。"""
    控制器=会话日志下载控制器()#控制器
    if hasattr(上下文,'provide'):#提供
        上下文.provide('sessionLogDownload',控制器)#登记
    def 拆除():#拆除
        """拆除控制器。"""
        控制器.dispose()#关
        return None#无
    上下文.副作用(lambda:拆除,'session-log-download: browser download lifecycle')#寿命
    if hasattr(上下文,'locale') and hasattr(上下文.locale,'register'):#区域
        上下文.副作用(lambda:上下文.locale.register(命名空间,{'zh':简体中文,'en':英文}),'session-log-download: browser dictionaries')#文案
    def 命令已执行(会话标识,命令名,结果):#命令完成
        """export 成功后启动下载。"""
        if 命令名=='export' and isinstance(结果,dict) and 结果.get('kind')=='success':#成功
            控制器.download(会话标识)#下载
    上下文.监听('command/executed',命令已执行)#监听

默认=应用
name='session-log-download'#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
