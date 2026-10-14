'浏览器插件：拥有会话导出下载状态及其共享对话框'
from .控制器 import 会话日志下载控制器#控制器
from .区域设置 import 命名空间,简体中文,英文#文案
from .页眉动作 import 会话日志下载页眉动作,快照仓#页眉

依赖=['slots','locale']#依赖
__all__=['应用','默认','会话日志下载控制器']#公开面

def 应用(上下文):#加载
    '提供下载控制器并登记区域文案'
    控制器=会话日志下载控制器()#控制器
    if hasattr(上下文,'provide'):#提供
        上下文.provide('sessionLogDownload',控制器)#登记
    def 拆除():#拆除
        '拆除控制器'
        控制器.dispose()#关
        return None#无
    上下文.副作用(lambda:拆除,'session-log-download: browser download lifecycle')#寿命
    if hasattr(上下文,'locale') and hasattr(上下文.locale,'register'):#区域
        上下文.副作用(lambda:上下文.locale.register(命名空间,{'zh':简体中文,'en':英文}),'session-log-download: browser dictionaries')#文案
    def 命令已执行(会话标识,命令名,结果):#命令完成
        'export 成功后启动下载'
        if 命令名=='export' and isinstance(结果,dict) and 结果.get('kind')=='success':#成功
            控制器.download(会话标识)#下载
    上下文.监听('command/executed',命令已执行)#监听
    反馈可用=快照仓(False)#反馈插件是否仍在
    def 反馈上线(范围):#反馈插件到达
        '在则菜单多一项，卸掉后收回'
        def 效应():#效应
            '标记可用，并在纤程结束时收回'
            反馈可用.set(True)#开
            def 卸():#卸
                '反馈插件离开'
                反馈可用.set(False)#关
            return 卸#拆除
        范围.副作用(效应,'session-log-download: feedback availability')#寿命
    if hasattr(上下文,'依赖启动'):#可等可选服务
        上下文.依赖启动(['feedbackUi'],反馈上线)#不挡住页眉
    def 打开反馈(会话标识):#打开反馈
        '反馈插件已卸则什么都不做'
        反馈=上下文.get('feedbackUi') if hasattr(上下文,'get') else None#服务
        if 反馈 is None or not hasattr(反馈,'openSession'):#没有
            return#无事
        反馈.openSession(会话标识)#打开草稿
    def 注入页眉():#注入
        '下载状态、请求、关闭，以及反馈'
        return {#面
            'hooks':{'sessionLogDownload':控制器.store,'feedbackAvailable':反馈可用},
            'request':控制器.download,
            'dismiss':控制器.dismiss,
            'openFeedback':打开反馈,
        }#面结束
    def 登记页眉():#登记
        '会话 Header 的更多菜单'
        return 上下文.slots.register({#槽
            'name':'conversation.session.header.utilities',
            'id':'session-log-download',
            'locale':命名空间,
            'inject':注入页眉,
        },会话日志下载页眉动作)#组件
    上下文.slots.inject('conversation.session.header.utilities',登记页眉)#页眉

默认=应用
name='session-log-download'#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
