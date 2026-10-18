'浏览器插件：持有会话导出的下载状态，并把对话框挂进会话页眉'
from ....客户端.存储 import 创建快照存储#反馈插件是否还在
from . import (
    控制器,#下载状态
    区域设置,#中英文案表
    页眉动作,#页眉菜单
    对话框,#状态对话框
)

依赖=['slots','locale']#槽位和区域
名称='session-log-download'#插件名
__all__=['控制器','区域设置','页眉动作','对话框','依赖','名称','应用']


def 应用(上下文,配置=None):
    '提供下载控制器，登记中英文案表，并挂上页眉菜单'
    下载=控制器.会话日志下载控制器()#每个会话一份在途下载
    上下文.提供服务('sessionLogDownload',下载)#服务名

    def 登记寿命():
        '拆插件时中止还在飞的请求'
        def 拆除():
            '中止活跃下载'
            下载.dispose()#关
        return 拆除#拆除器

    上下文.副作用(登记寿命,'session-log-download: browser download lifecycle')#寿命

    def 登记词典():
        '登记中英文案表。界面显示不走英文表'
        return 上下文.locale.register(区域设置.命名空间,{'zh':区域设置.简体中文,'en':区域设置.英文})#两张表

    上下文.副作用(登记词典,'session-log-download: browser dictionaries')#文案
    反馈可用=创建快照存储(False)#反馈插件还没到

    def 反馈上线(范围):
        '反馈插件到达时菜单多一项，卸掉后收回'
        def 效应():
            '标记可用，并在这条纤程结束时收回'
            反馈可用.set(True)#开
            def 卸():
                '反馈插件离开'
                反馈可用.set(False)#关
            return 卸#拆除
        范围.副作用(效应,'session-log-download: feedback availability')#跟着反馈插件

    上下文.依赖启动(['feedbackUi'],反馈上线)#可选，不挡住页眉

    def 命令已执行(会话标识,命令名,结果):
        'export 成功后启动下载'
        if 命令名=='export' and 结果['kind']=='success':#这一条命令成功
            下载.download(会话标识)#含后代和附件

    上下文.监听('command/executed',命令已执行)#命令回执

    def 打开反馈(会话标识):
        '打开已有的会话反馈草稿。插件已卸则什么都不做'
        反馈=上下文.获取服务('feedbackUi')#可能已经卸掉
        if 反馈 is None:#没有
            return#无事
        反馈.openSession(会话标识)#不写入反馈

    def 注入页眉(*位置参数):
        '槽位会传入会话键和动作。这一份注入不随那两个参数变'
        return {#注入面
            'hooks':{'sessionLogDownload':下载.store,'feedbackAvailable':反馈可用},#钩子
            'request':下载.download,#下载
            'dismiss':下载.dismiss,#只关对话框
            'openFeedback':打开反馈,#反馈
        }

    def 登记页眉():
        '等会话页眉工具槽出现再登记'
        return 上下文.slots.register({#槽
            'name':'conversation.session.header.utilities',#页眉右侧
            'id':'session-log-download',#这一条
            'locale':区域设置.命名空间,#文案命名空间
            'inject':注入页眉,#注入面
        },页眉动作.会话日志下载页眉动作)#组件

    上下文.slots.inject('conversation.session.header.utilities',登记页眉)#等槽声明


name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#默认导出
