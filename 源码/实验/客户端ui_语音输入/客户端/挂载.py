from .文案 import 命名空间,中文,英文
from .语音输入 import 语音输入
from .音频 import 录制
from .就绪度 import 观察就绪度
from .准备卡片 import 语音准备工作
from .语音输入安装提示 import 语音输入安装提示

__all__=['依赖','挂载语音输入','登记界面']

依赖=['remote','slots','locale']

组合包名='@deepseek-ai/dsh-experimental-voice-input-bundle'

def 登记界面(上下文):
    """登记词典、共享就绪度与三个槽。"""
    def 卸词典():
        """登记词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(卸词典)
    录制表=set()
    就绪=观察就绪度(上下文)
    def 拆就绪():
        """拆除共享就绪订阅。"""
        return 就绪['dispose']
    上下文.副作用(拆就绪)
    def 拆录制():
        """插件释放时拆掉未结束采集。"""
        def 拆():
            """逐个拆除。"""
            for 项 in list(录制表):
                项.拆除()
        return 拆
    上下文.副作用(拆录制)
    def 建录制():
        """一次由插件寿命拥有的麦克风操作。"""
        项=None
        def 丢掉():
            """从在途表删除。"""
            录制表.discard(项)
        项=录制(丢掉)
        录制表.add(项)
        return 项
    def 转写(请求,信号):
        """转发 speech.transcribe。"""
        return 上下文.remote.speech.transcribe(请求,信号).等待()
    def 配置(补丁):
        """失败则抛 Remote 错误。"""
        结果=上下文.remote.speech.configure(补丁).等待()
        if not 结果['ok']:
            raise 结果['error']
    def 准备(提供方标识,选项=None):
        """启动或加入 Host 准备。"""
        结果=上下文.remote.speech.prepare(提供方标识,选项).等待()
        if not 结果['ok']:
            raise 结果['error']
    def 取消准备(提供方标识):
        """显式取消准备。"""
        结果=上下文.remote.speech.cancelPreparation(提供方标识).等待()
        if not 结果['ok']:
            raise 结果['error']
    动作={
        'hooks':{'speechReadiness':就绪['state']},
        'createRecording':建录制,
        'transcribe':转写,
        'configure':配置,
        'prepare':准备,
        'cancelPreparation':取消准备,
    }
    def 依赖动作():
        """注入动作表。"""
        return 动作
    def 挂活动():
        """输入栏麦克风。"""
        return 上下文.slots.register({
            'name':'conversation.input.activity',
            'locale':命名空间,
            'inject':依赖动作,
        },语音输入)
    上下文.slots.inject('conversation.input.activity',挂活动)
    def 挂配置():
        """Bundle 详情准备卡片。"""
        return 上下文.slots.register({
            'name':'plugins.bundle.config',
            'key':组合包名,
            'locale':命名空间,
            'inject':依赖动作,
        },语音准备工作)
    上下文.slots.inject('plugins.bundle.config',挂配置)
    def 挂激活():
        """首次启用安装引导。"""
        return 上下文.slots.register({
            'name':'plugins.bundle.activation',
            'key':组合包名,
            'locale':命名空间,
            'inject':依赖动作,
        },语音输入安装提示)
    上下文.slots.inject('plugins.bundle.activation',挂激活)

def 挂载语音输入(上下文,贡献):
    """挂实验 Remote，不加入稳定 API Remotes。"""
    卸远程=上下文.remote.$mount(贡献).等待()
    界面=上下文.依赖启动(['remote.speech','slots','locale'],登记界面)
    try:
        界面.等待()
    except Exception:
        界面.dispose().等待()
        卸远程()
        raise
    def 卸除():
        """卸 UI 与 Remote。"""
        界面.dispose().等待()
        卸远程()
    return 卸除
