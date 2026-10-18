'实验 speech Remote 和浏览器界面的寿命'
from .文案 import 命名空间,中文,英文#登记用的两份表
from .语音输入 import 语音输入#输入栏麦克风
from .音频 import 录制#一次采集
from .麦克风设备 import 创建麦克风设备存储#浏览器设备偏好
from .就绪度 import 观察就绪度#共享宿主就绪
from .准备卡片 import 语音准备工作#插件详情里的准备
from .语音输入安装提示 import 语音输入安装提示#首次启用引导

__all__=['依赖','挂载语音输入','登记界面']#客户端入口要用

依赖=['remote','slots','locale','pluginNavigation']#所需服务
组合包名='@deepseek-ai/dsh-experimental-voice-input-bundle'#详情和激活槽的键


def 登记界面(上下文):
    '登记词典、共享就绪度和三个槽'
    def 卸词典():
        '登记 voice-input，卸下时由返回的函数拆掉'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#中英都留下
    上下文.副作用(卸词典)#插件卸载时拆词典
    录制表=set()#还没结束的采集
    麦克风=创建麦克风设备存储()#浏览器本地偏好
    就绪=观察就绪度(上下文)#一份就绪，所有界面共用

    def 拆就绪():
        '停掉共享就绪订阅'
        就绪['dispose']()#停流并等观察结束
    上下文.副作用(拆就绪)#插件卸载时拆

    def 拆全部录制():
        '拆除全部未结束的采集'
        for 项 in list(录制表):#拷贝，拆除时会改表
            项.拆除()#停轨并关闭音频上下文
    上下文.副作用(拆全部录制)#插件卸载时拆

    def 要求成功(结果):
        'Remote 失败则抛出错误对象'
        if isinstance(结果,dict) and 'ok' in 结果 and 结果['ok'] is False:#失败信封
            raise 结果['error']#Remote 错误
        return 结果#成功或没有信封

    def 开设置():
        '打开语音组合包详情，不启动准备'
        上下文.pluginNavigation.openBundle(组合包名)#插件详情

    def 选择麦克风(设备):
        '记住预览和后续录音要用的浏览器设备'
        麦克风.set(设备)#整份写入

    def 建一条录制():
        '一次由插件寿命拥有的麦克风操作'
        快照=麦克风.getSnapshot()#当前设备
        标识=''#跟随系统
        if isinstance(快照,dict) and isinstance(快照.get('id'),str):#有合法 id
            标识=快照['id']#用它
        盒={'项':None}#拆除回调要指到这一条

        def 丢掉():
            '从在途表删除'
            录制表.discard(盒['项'])#摘掉

        项=录制(丢掉,标识)#这一次采集
        盒['项']=项#回调能找到它
        录制表.add(项)#插件卸载时一起拆
        return 项#交给界面

    def 转写(请求,信号):
        '把录音交给 speech.transcribe，结果原样返回'
        return 上下文.remote.speech.transcribe(请求,信号)#识别

    def 配置(补丁):
        '写入识别偏好。失败则抛 Remote 错误'
        return 要求成功(上下文.remote.speech.configure(补丁))#持久化

    def 准备(提供方标识,选项=None):
        '启动或加入宿主准备。失败则抛 Remote 错误'
        return 要求成功(上下文.remote.speech.prepare(提供方标识,选项))#准备

    def 取消准备(提供方标识):
        '显式取消准备。失败则抛 Remote 错误'
        return 要求成功(上下文.remote.speech.cancelPreparation(提供方标识))#取消

    动作={#三个槽注入同一份
        'openSettings':开设置,#打开详情
        'hooks':{'speechReadiness':就绪['state'],'microphoneDevice':麦克风},#渲染器绑成钩子
        'selectMicrophone':选择麦克风,#记住设备
        'createRecording':建一条录制,#新建采集
        'transcribe':转写,#识别
        'configure':配置,#偏好
        'prepare':准备,#下载并准备
        'cancelPreparation':取消准备,#取消准备
    }

    def 依赖动作():
        '注入动作表'
        return 动作#同一份

    def 挂活动():
        '输入栏上的麦克风'
        return 上下文.slots.register({
            'name':'conversation.input.activity',#槽名保持英文
            'locale':命名空间,#文案命名空间
            'inject':依赖动作,#动作
        },语音输入)#控件

    上下文.slots.inject('conversation.input.activity',挂活动)#等槽声明

    def 挂配置():
        '组合包详情里的准备和偏好'
        return 上下文.slots.register({
            'name':'plugins.bundle.config',#槽名保持英文
            'key':组合包名,#这一包
            'locale':命名空间,#文案命名空间
            'inject':依赖动作,#动作
        },语音准备工作)#准备卡片

    上下文.slots.inject('plugins.bundle.config',挂配置)#等槽声明

    def 挂激活():
        '首次启用时的安装引导'
        return 上下文.slots.register({
            'name':'plugins.bundle.activation',#槽名保持英文
            'key':组合包名,#这一包
            'locale':命名空间,#文案命名空间
            'inject':依赖动作,#动作
        },语音输入安装提示)#引导

    上下文.slots.inject('plugins.bundle.activation',挂激活)#等槽声明


def 挂载语音输入(上下文,贡献):
    '挂上实验 Remote，不加入稳定 API Remotes。返回卸除函数'
    卸远程=getattr(上下文.remote,'$mount')(贡献)#安装生成的 speech 贡献
    界面=None#还没启动
    try:#界面启动失败则回滚 Remote
        界面=上下文.依赖启动(['remote.speech','slots','locale','pluginNavigation'],登记界面)#等服务再登记
        界面.等待()#启动错误在这里抛出
    except Exception as 错误:#登记或启动失败
        if 界面 is not None:#纤程已经建出来
            try:#先卸界面
                界面.拆除()#拆槽和副作用
            except Exception as 拆除错误:#卸界面失败仍要卸远程
                拆除错误=None#留下原错误
        if callable(卸远程):#远程已经挂上
            卸远程()#卸掉
        raise 错误#原错误继续抛

    def 卸除():
        '卸界面和 Remote'
        界面.拆除()#先拆槽
        卸远程()#再拆 Remote

    return 卸除#调用方在卸载时调用
