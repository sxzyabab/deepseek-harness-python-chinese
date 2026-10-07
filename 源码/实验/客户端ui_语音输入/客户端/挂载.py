from functools import partial as 偏函数
from .文案 import 命名空间,中文,英文
from ....基础设施.js特性 import PromiseEX as 期约#远程调用与卸除的异步结果
from ....基础设施.通用工具 import 获取内部数据
from .语音输入 import 语音输入
from .音频 import 录制
from .就绪度 import 观察就绪度
from .准备卡片 import 语音准备工作
from .语音输入安装提示 import 语音输入安装提示

__all__=['依赖','挂载语音输入','登记界面']

依赖=['remote','slots','locale','pluginNavigation']

组合包名='@deepseek-ai/dsh-experimental-voice-input-bundle'

def 拆全部录制(录制表):
    '同时拆除全部未结束采集，返回期约'
    return 期约.全部([项.拆除() for 项 in list(录制表)])

def 提供拆录制(录制表):
    '插件释放时拆掉未结束采集'
    return 偏函数(拆全部录制,录制表)

def 建一条录制(录制表):
    '一次由插件寿命拥有的麦克风操作'
    项持有={'项':None}
    def 丢掉():
        '从在途表删除'
        录制表.discard(项持有['项'])
    项=录制(丢掉)
    项持有['项']=项
    录制表.add(项)
    return 项

def 调用无参(函数,结果=None):
    '期约回调丢掉兑现值，再调用无参函数'
    return 函数()

def 抛出保留错误(错误,结果=None):
    '回滚完成后抛出原错误'
    raise 错误

def 卸界面与远程(界面,卸远程):
    '卸 UI 与 Remote'
    return 界面.dispose().然后(偏函数(调用无参,卸远程))

def 回滚界面(界面,卸远程,错误):
    '界面启动失败：卸界面与 Remote 后抛出原错误'
    return 界面.dispose().然后(偏函数(调用无参,卸远程)).然后(偏函数(抛出保留错误,错误))

def 交出卸除器(界面,卸远程,界面就绪值=None):
    '界面就绪后交出卸除函数'
    return 偏函数(卸界面与远程,界面,卸远程)

def 登记界面(上下文):
    '登记词典、共享就绪度与三个槽'
    def 卸词典():
        '登记词典'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(卸词典)
    录制表=set()
    就绪=观察就绪度(上下文)
    def 拆就绪():
        '拆除共享就绪订阅'
        return 就绪['dispose']
    上下文.副作用(拆就绪)
    上下文.副作用(偏函数(提供拆录制,录制表))
    def 检查远程结果(结果):
        'Remote 调用结算后，失败则抛 Remote 错误'
        if not 结果['ok']:
            raise 结果['error']
    def 配置(补丁):
        '失败则以 Remote 错误拒绝，返回期约'
        return 上下文.remote.speech.configure(补丁).然后(检查远程结果)
    def 准备(提供方标识,选项=None):
        '启动或加入 Host 准备，返回期约'
        return 上下文.remote.speech.prepare(提供方标识,选项).然后(检查远程结果)
    def 取消准备(提供方标识):
        '显式取消准备，返回期约'
        return 上下文.remote.speech.cancelPreparation(提供方标识).然后(检查远程结果)
    def 开设置():
        '打开语音 Bundle 详情，不启动准备'
        上下文.pluginNavigation.openBundle(组合包名)
    动作={
        'openSettings':开设置,
        'hooks':{'speechReadiness':就绪['state']},
        'createRecording':偏函数(建一条录制,录制表),
        'transcribe':上下文.remote.speech.transcribe,
        'configure':配置,
        'prepare':准备,
        'cancelPreparation':取消准备,
    }
    def 依赖动作():
        '注入动作表'
        return 动作
    def 挂活动():
        '输入栏麦克风'
        return 上下文.slots.register({
            'name':'conversation.input.activity',
            'locale':命名空间,
            'inject':依赖动作,
        },语音输入)
    上下文.slots.inject('conversation.input.activity',挂活动)
    def 挂配置():
        'Bundle 详情准备卡片'
        return 上下文.slots.register({
            'name':'plugins.bundle.config',
            'key':组合包名,
            'locale':命名空间,
            'inject':依赖动作,
        },语音准备工作)
    上下文.slots.inject('plugins.bundle.config',挂配置)
    def 挂激活():
        '首次启用安装引导'
        return 上下文.slots.register({
            'name':'plugins.bundle.activation',
            'key':组合包名,
            'locale':命名空间,
            'inject':依赖动作,
        },语音输入安装提示)
    上下文.slots.inject('plugins.bundle.activation',挂激活)

def 挂载语音输入(上下文,贡献):
    '挂实验 Remote，不加入稳定 API Remotes。返回期约，兑现值是卸除函数；卸除函数返回期约'
    def 挂载界面(卸远程):
        'Remote 挂载完成后启动界面；界面启动失败则回滚 Remote'
        界面=上下文.依赖启动(['remote.speech','slots','locale','pluginNavigation'],登记界面)
        return 界面.等待().然后(偏函数(交出卸除器,界面,卸远程)).捕获(偏函数(回滚界面,界面,卸远程))
    return 获取内部数据(上下文.remote,'mount')(贡献).然后(挂载界面)
