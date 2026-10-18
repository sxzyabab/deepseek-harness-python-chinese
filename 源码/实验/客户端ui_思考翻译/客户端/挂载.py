'可选 Remote 与思考槽的登记寿命'
from ....客户端.存储 import 创建快照存储#偏好、上限和合格路由
from ....客户端.连接.rpc import 中止控制器#查询寿命
from ...机器翻译.类型 import 码元数,若已中止则抛出#UTF-16 长度和取消
from .偏好表单 import 翻译偏好表单#暂存表单
from .思考正文 import 思考正文#展开区
from .思考设置 import 思考设置#插件页
from .文案 import 中文,命名空间,英文#登记用的中英文案表

__all__=['依赖','挂载思考翻译']

依赖=['remote','slots','locale','configForms']#客户端插件要等的服务
组合包名='@deepseek-ai/dsh-experimental-cot-translation-bundle'#插件页键


def 挂载思考翻译(上下文,贡献):
    '挂会话绑定的翻译，并在生成的 Remote 之前卸掉界面'
    寿命=中止控制器()#限额和翻译查询的取消

    def 插件拆除(纤程):
        '本纤程编号清空时取消查询'
        if 纤程 is 上下文.纤程 and 纤程.编号 is None:
            寿命.abort()#先取消再卸

    上下文.监听('internal/plugin',插件拆除)#纤程拆除通知
    def 取消查询():
        '离开时取消还没结束的限额查询'
        def 拆():
            '中止寿命'
            寿命.abort()#查询取消
        return 拆
    上下文.副作用(取消查询,'cot-translation: query cancellation')#随本纤程
    卸远程=getattr(上下文.remote,'$mount')(贡献)#先挂 Remote

    def 登记界面(子上下文,配置值=None):
        '词典、偏好镜像和两个槽。初值读完才登记'
        修订=0#失效次数
        上次读取修订=-1#最近一次读到的修订
        已接受修订=-1#已经写入快照的修订
        在途=False#刷新还没结束

        def 已拆除():
            '寿命中止或界面纤程已卸'
            return 寿命.signal.aborted or 子上下文.纤程.编号 is None

        def 读取():
            '修订变了就再读，直到读到稳定的一版'
            nonlocal 上次读取修订
            while True:
                观测=修订#这次看到的修订
                上次读取修订=观测#记下
                结果=子上下文.remote.cotTranslation.limits(寿命.signal)#不发送文本
                if 已拆除():
                    return None#卸了就丢掉
                if 观测==修订:
                    return 结果#读的过程中没有再失效

        def 刷新():
            '把宿主偏好和请求上限写进快照'
            nonlocal 在途,已接受修订,上次读取修订
            if 在途 or 已接受修订<0 or 已拆除():
                return#已经在刷新、还没有初值，或已卸
            在途=True#占住
            try:
                try:
                    结果=读取()#再读一版
                    if isinstance(结果,dict) and 结果.get('ok') is True:
                        值=结果['value']#快照
                        偏好仓.set(值['preferences'])#提供方和语言
                        上限仓.set(值['maxTextChars'])#请求上限
                        可用仓.set(值['availableProviders'])#合格路由
                        已接受修订=上次读取修订#这版已经收下
                except Exception:
                    if not 已拆除():
                        子上下文.日志.警告('cot-translation: could not refresh Host preferences and request limits')#刷新失败只记日志
            finally:
                在途=False#放开
                if 修订!=上次读取修订 and not 已拆除():
                    刷新()#读的过程中又失效了

        def 失效(*位置参数):
            '宿主事实变了就再读限额'
            nonlocal 修订
            修订=修订+1#记一次
            刷新()#有初值才真的读

        def 登记查询寿命():
            '界面纤程离开时取消查询'
            def 拆():
                '中止寿命并等同步读自己返回'
                寿命.abort()#取消
            return 拆
        子上下文.副作用(登记查询寿命,'cot-translation: metadata queries')#随界面纤程
        远程开=getattr(子上下文.remote,'$on')#转发事件
        拆除监听=[
            远程开('settings/document-updated',失效),#设置文档
            远程开('llm/adapters-updated',失效),#适配器
            远程开('deepseek-account/session-expired',失效),#账号过期
            远程开('deepseek-account/model-sign-in-required',失效),#需要登录
            远程开('credentials/record-updated',失效),#凭据记录
            远程开('credentials/reference-updated',失效),#凭据引用
        ]#这些变化都让限额失效

        def 登记监听():
            '卸界面时摘掉这些转发'
            def 拆():
                '逐个退订'
                for 项 in 拆除监听:
                    if callable(项):
                        项()#退订
            return 拆
        子上下文.副作用(登记监听)#随界面纤程
        子上下文.监听('connection/reset',失效)#连接重置
        try:
            初值=读取()#第一版限额
        except Exception:
            if 已拆除():
                return#卸掉了就不继续
            raise#其它失败交给纤程
        if 初值 is None:
            return#读的过程中卸了
        if not 初值.get('ok'):
            子上下文.日志.警告('cot-translation: translation preferences are unavailable')#宿主还没给限额，界面先不挂
            return#不把这次读取失败变成插件失败
        快照=初值['value']#宿主元数据
        偏好仓=创建快照存储(快照['preferences'])#已接受偏好
        上限仓=创建快照存储(快照['maxTextChars'])#请求上限
        可用仓=创建快照存储(快照['availableProviders'])#合格路由
        已接受修订=上次读取修订#初值收下了
        作用域=子上下文.configForms.get('cot-translation')#这一插件的配置表单

        def 订作用域():
            '草稿或已接受值变化时重新读宿主'
            return 作用域.subscribe(失效)#退订器
        子上下文.副作用(订作用域)#随界面纤程

        def 登记词典():
            '登记中英文案表。页面显示不走英文表'
            return 子上下文.locale.register(命名空间,{'en':英文,'zh':中文})#退订器
        子上下文.副作用(登记词典)#随界面纤程
        表单=翻译偏好表单(作用域)#暂存两项

        def 拆表单():
            '卸界面时拆掉表单订阅'
            def 拆():
                '释放已接受偏好'
                表单.拆除()#退订
            return 拆
        子上下文.副作用(拆表单)#随界面纤程

        def 注入正文(会话标识):
            '这一会话的偏好、上限和翻译回调'
            def 翻译请求(请求,信号):
                '限额没对齐就先刷新，再按已接受的选择翻译'
                if 已接受修订!=修订:
                    刷新()#先跟上宿主
                若已中止则抛出(信号)#刷新期间取消
                已接受=偏好仓.getSnapshot()#当前偏好
                语言不符=已接受['targetLanguage']!='auto' and 请求['targetLanguage']!=已接受['targetLanguage']#显式语言变了
                if (已拆除() or 已接受修订!=修订 or 请求['provider']!=已接受['provider']
                        or 语言不符 or 码元数(请求['text'])>上限仓.getSnapshot()):
                    raise RuntimeError('Translation preferences or limits changed')#这次作废
                带会话=dict(请求)#加上会话
                带会话['sessionId']=会话标识#这一展开区所属会话
                结果=子上下文.remote.cotTranslation.translate(带会话,信号)#远程翻译
                if not 结果['ok']:
                    raise 结果['error']#交给展开区标失败
                return 结果['value']#译文
            return {
                'hooks':{
                    'preferences':偏好仓,#已接受偏好
                    'translationLocale':子上下文.locale,#界面语言
                    'translationLimit':上限仓,#请求上限
                },
                'translate':翻译请求,#一段一次
            }

        def 登记正文():
            '登记展开思考的正文槽'
            return 子上下文.slots.register({
                'name':'conversation.chat.reasoning.body',#槽位
                'locale':命名空间,#词典
                'inject':注入正文,#按会话注入
            },思考正文)#界面类
        子上下文.slots.inject('conversation.chat.reasoning.body',登记正文)#声明出现时登记

        def 注入设置():
            '表单动作再加上合格路由'
            面=表单.注入()#草稿和保存
            钩子=dict(面['hooks'])#复制钩子
            钩子['availableProviders']=可用仓#合格路由
            交出=dict(面)#复制份额
            交出['hooks']=钩子#叠上路由
            交出['refreshProviders']=失效#不发送思考
            return 交出

        def 登记设置():
            '登记这个组合包的插件配置'
            return 子上下文.slots.register({
                'name':'plugins.bundle.config',#槽位
                'key':组合包名,#组合包
                'locale':命名空间,#词典
                'inject':注入设置,#表单份额
            },思考设置)#界面类
        子上下文.slots.inject('plugins.bundle.config',登记设置)#声明出现时登记

    界面=上下文.依赖启动(
        ['remote.cotTranslation','slots','locale','configForms'],
        登记界面,
    )#Remote 方法出现后再登记界面
    try:
        界面.等待()#启动失败就抛出
    except Exception:
        界面.拆除()#卸掉半成品
        if callable(卸远程):
            卸远程()#Remote 也卸
        raise#原错误继续抛
    def 卸下():
        '先卸界面，再卸 Remote'
        界面.拆除()#界面先走
        if callable(卸远程):
            卸远程()#然后 Remote
    return 卸下#调用方在离开时调用
