'可选 Remote 与思考槽的登记寿命'
from functools import partial as 偏函数
from ....基础设施.js特性 import PromiseEX as 期约#挂载、限额与卸除的异步结果
from ....基础设施.通用工具 import 获取内部数据
from ....客户端.存储 import 创建快照存储
from ...机器翻译.类型 import 中止控制器,已中止,若已中止则抛出,码元数
from .文案 import 命名空间,中文,英文
from .偏好表单 import 翻译偏好表单
from .思考正文 import 思考正文
from .思考设置 import 思考设置

__all__=['依赖','挂载思考翻译','登记界面']

依赖=['remote','slots','locale','configForms']

组合包名='@deepseek-ai/dsh-experimental-cot-translation-bundle'

def 失败说明(错误):
    '失败句去掉绝对路径，其余原文保留'
    if isinstance(错误,BaseException) and len(错误.args)>0:
        原文=str(错误.args[0])
    else:
        原文=str(错误)
    留下=[]
    for 词 in 原文.split():
        去引=词.strip('\'"()[]{}<>')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return '失败'

def 抛结果错误(错误):
    'Remote 失败对象不是异常时包成 RuntimeError。文案不含绝对路径'
    if isinstance(错误,BaseException):
        raise 错误
    if isinstance(错误,dict):
        消息=错误.get('message')
        raise RuntimeError(失败说明(错误) if 消息 is None else 失败说明(消息))
    raise RuntimeError(失败说明(错误))

def 调用无参(函数,结果=None):
    '期约回调丢掉兑现值，再调用无参函数'
    return 函数()

def 抛出保留错误(错误,结果=None):
    '回滚完成后抛出原错误'
    raise 错误

def 卸纤程(界面):
    '卸掉界面纤程。返回期约'
    界面.拆除()
    完成=期约()
    完成.解决(None)
    return 完成

def 卸界面与远程(界面,卸远程):
    '卸 UI 与 Remote'
    return 卸纤程(界面).然后(偏函数(调用无参,卸远程))

def 回滚界面(界面,卸远程,错误):
    '界面启动失败：卸界面与 Remote 后抛出原错误'
    return 卸纤程(界面).然后(偏函数(调用无参,卸远程)).然后(偏函数(抛出保留错误,错误))

def 登记界面(上下文,寿命):
    '登记词典、偏好镜像和两个槽。返回期约，初值读完后兑现'
    修订={'值':0}
    上次读取修订={'值':-1}
    已接受修订={'值':-1}
    读任务={'期约':None}
    更新中={'期约':None}
    仓={'偏好':None,'上限':None,'可用':None}

    def 已拆除():
        '寿命已中止或纤程编号已清空'
        return 已中止(寿命.信号) or 上下文.纤程.编号 is None

    def 拆查询():
        '中止后来的查询，并等已发出的限额请求结算。返回期约'
        寿命.中止()
        待等=[]
        if 读任务['期约'] is not None:
            待等.append(读任务['期约'])
        if 更新中['期约'] is not None:
            待等.append(更新中['期约'])
        if len(待等)==0:
            完成=期约()
            完成.解决(None)
            return 完成
        return 期约.全部已结算(待等)

    def 提供拆查询():
        '插件释放时拆掉在途限额查询'
        return 拆查询
    上下文.副作用(提供拆查询,'cot-translation: metadata queries')

    def 读取():
        '读到修订稳定的快照。返回期约；已拆除则兑现 None'
        def 一轮(值=None):
            '记下观测到的修订再读限额'
            观测=修订['值']
            上次读取修订['值']=观测
            读任务['期约']=上下文.remote.cotTranslation.limits(寿命.信号)
            def 看结果(结果):
                '修订变了就再读；已拆除则停'
                if 已拆除():
                    return None
                if 观测==修订['值']:
                    return 结果
                return 一轮()
            return 读任务['期约'].然后(看结果)
        起点=期约()
        链=起点.然后(一轮)
        起点.解决(None)
        return 链

    def 刷新():
        '在途、尚未接受初值或已拆除则跳过'
        if 更新中['期约'] is not None or 已接受修订['值']<0 or 已拆除():
            return
        def 体(值=None):
            '读成功才写入三份快照'
            def 应用(结果):
                'ok 才接受这次读到的修订'
                if 结果 is not None and 结果.get('ok'):
                    仓['偏好'].set(结果['value']['preferences'])
                    仓['上限'].set(结果['value']['maxTextChars'])
                    仓['可用'].set(结果['value']['availableProviders'])
                    已接受修订['值']=上次读取修订['值']
            def 失败(错误):
                '未拆除才记一条警告'
                if not 已拆除():
                    上下文.日志.警告('cot-translation: could not refresh Host preferences and request limits')
            return 读取().然后(应用).捕获(失败)
        def 收尾(值=None):
            '清掉在途；修订又变了就再刷新'
            更新中['期约']=None
            if 修订['值']!=上次读取修订['值'] and not 已拆除():
                刷新()
        起点=期约()
        更新中['期约']=起点.然后(体).最终(收尾)
        起点.解决(None)

    def 失效():
        '修订加一并尝试刷新'
        修订['值']+=1
        刷新()

    def 订远程():
        '设置、适配器、账号和凭据变化都使偏好失效'
        远程开=获取内部数据(上下文.remote,'on')
        yield 远程开('settings/document-updated',失效)
        yield 远程开('llm/adapters-updated',失效)
        yield 远程开('deepseek-account/session-expired',失效)
        yield 远程开('deepseek-account/model-sign-in-required',失效)
        yield 远程开('credentials/record-updated',失效)
        yield 远程开('credentials/reference-updated',失效)
    上下文.副作用(订远程)
    上下文.监听('connection/reset',失效)

    def 装上(初始):
        '初值有效才建快照、表单和两个槽'
        if 初始 is None:
            return None
        if not 初始.get('ok'):
            抛结果错误(初始['error'])
        仓['偏好']=创建快照存储(初始['value']['preferences'])
        仓['上限']=创建快照存储(初始['value']['maxTextChars'])
        仓['可用']=创建快照存储(初始['value']['availableProviders'])
        已接受修订['值']=上次读取修订['值']
        作用域=上下文.configForms.get('cot-translation')
        def 订作用域():
            '表单变化使偏好失效'
            return 作用域.subscribe(失效)
        上下文.副作用(订作用域)
        def 卸词典():
            '登记词典'
            return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
        上下文.副作用(卸词典)
        表单=翻译偏好表单(作用域)
        def 拆表单():
            '释放表单订阅'
            表单.拆除()
        上下文.副作用(拆表单)

        def 翻译请求(会话标识):
            '把这次展开绑到该会话。返回期约，兑现译文'
            def 翻译(请求,信号):
                '偏好或上限变了就拒绝，否则走 Remote'
                if 已接受修订['值']!=修订['值']:
                    刷新()
                def 等更新(值=None):
                    '等当前刷新结束；期间又刷新则继续等'
                    在途=更新中['期约']
                    if 在途 is None:
                        return None
                    return 在途.然后(等更新)
                def 发出(值=None):
                    '核对仍是已接受的偏好和上限，再翻译'
                    若已中止则抛出(信号)
                    已接受=仓['偏好'].getSnapshot()
                    上限=仓['上限'].getSnapshot()
                    语言不符=已接受['targetLanguage']!='auto' and 请求.get('targetLanguage')!=已接受['targetLanguage']
                    超限=码元数(请求['text'])>上限
                    if (已拆除() or 已接受修订['值']!=修订['值'] or 请求.get('provider')!=已接受['provider']
                            or 语言不符 or 超限):
                        raise RuntimeError('Translation preferences or limits changed')
                    def 取译文(结果):
                        'Remote 失败则抛 Remote 错误'
                        if not 结果['ok']:
                            抛结果错误(结果['error'])
                        return 结果['value']
                    体=dict(请求)
                    体['sessionId']=会话标识
                    return 上下文.remote.cotTranslation.translate(体,信号).然后(取译文)
                起点=期约()
                结果=起点.然后(等更新).然后(发出)
                起点.解决(None)
                return 结果
            return 翻译

        def 注入正文(会话标识):
            '偏好、界面语言、上限和按会话翻译'
            return {
                'hooks':{
                    'preferences':仓['偏好'],
                    'translationLocale':上下文.locale,
                    'translationLimit':仓['上限'],
                },
                'translate':翻译请求(会话标识),
            }
        def 挂正文():
            '展开思考的正文槽'
            return 上下文.slots.register({
                'name':'conversation.chat.reasoning.body',
                'locale':命名空间,
                'inject':注入正文,
            },思考正文)
        上下文.slots.inject('conversation.chat.reasoning.body',挂正文)

        def 注入设置():
            '表单动作、合格提供方和刷新'
            面=表单.注入()
            钩=dict(面['hooks'])
            钩['availableProviders']=仓['可用']
            return {**面,'hooks':钩,'refreshProviders':失效}
        def 挂设置():
            '组合包详情里的偏好表单'
            return 上下文.slots.register({
                'name':'plugins.bundle.config',
                'key':组合包名,
                'locale':命名空间,
                'inject':注入设置,
            },思考设置)
        上下文.slots.inject('plugins.bundle.config',挂设置)
        return None

    def 读失败(错误):
        '已拆除则停，否则把初值失败抛出去'
        if 已拆除():
            return None
        raise 错误
    def 开始(值=None):
        '先读一份限额快照'
        return 读取()
    起点=期约()
    结果=起点.然后(开始).捕获(读失败).然后(装上)
    起点.解决(None)
    return 结果

def 挂载思考翻译(上下文,贡献):
    '挂会话绑定的翻译，并在生成的 Remote 之前卸掉 UI。返回期约，兑现值是卸除函数；卸除函数返回期约'
    寿命=中止控制器()
    def 插件拆除(纤程):
        '编号清空时先取消查询'
        if 纤程 is 上下文.纤程 and 纤程.编号 is None:
            寿命.中止()
    上下文.监听('internal/plugin',插件拆除)
    def 取消查询():
        '查询取消'
        def 拆():
            '中止寿命'
            寿命.中止()
        return 拆
    上下文.副作用(取消查询,'cot-translation: query cancellation')

    def 挂载界面(卸远程):
        'Remote 挂载完成后启动界面；界面启动失败则回滚 Remote'
        就绪=期约()
        def 登记(子):
            '登记界面，初始快照读完后兑现'
            try:
                结果=登记界面(子,寿命)
            except Exception as 错误:
                就绪.拒绝(错误)
                raise
            结果.然后(就绪.解决,就绪.拒绝)
        界面=上下文.依赖启动(['remote.cotTranslation',*依赖[1:]],登记)
        def 等登记(值=None):
            '纤程起来后再等初始快照'
            try:
                界面.等待()
            except Exception as 错误:
                if 就绪.状态=='pending':
                    就绪.拒绝(错误)
            return 就绪
        def 交出(登记值=None):
            '界面就绪后交出卸除函数'
            return 偏函数(卸界面与远程,界面,卸远程)
        def 回滚(错误):
            '启动失败则卸界面和 Remote'
            return 回滚界面(界面,卸远程,错误)
        起点=期约()
        结果=起点.然后(等登记).然后(交出).捕获(回滚)
        起点.解决(None)
        return 结果
    def 开始(值=None):
        '先挂 Remote，再挂界面；界面还没起来就卸 Remote'
        卸远程=获取内部数据(上下文.remote,'mount')(贡献)
        try:
            return 挂载界面(卸远程)
        except Exception as 错误:
            return 卸远程().然后(偏函数(抛出保留错误,错误))
    起点=期约()
    结果=起点.然后(开始)
    起点.解决(None)
    return 结果
