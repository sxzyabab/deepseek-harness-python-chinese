'对展示中的思考内容做机器翻译'
from ...基础设施.js特性 import PromiseEX as 期约#限额、翻译与激活的异步结果
from ...基础设施.通用工具 import 启动守护线程
from ...依赖.工具 import 未传参
from ...依赖.schemastery import 无数据
from ...类型化远程调用.协议 import 远程,远程服务,远程错误
from ..机器翻译.异常 import 翻译错误
from ..机器翻译.类型 import 已中止,取原因,读易失,若已中止则抛出
from .偏好 import 提供方偏好,语言偏好模式
from .类型 import 失败码

__all__=['依赖','配置','应用','思考翻译控制器','远程贡献']

依赖=['translator','typert','sessionController']

def 配置项(配置值,键,缺省):
    '缺省或空字段用缺省；易失单元格原样保留'
    if not isinstance(配置值,dict) or 键 not in 配置值 or 配置值[键] is None:
        return 缺省
    return 配置值[键]

class 配置模式:
    '思考翻译提供方与目标语言'
    def 校验数据(自身,数据=未传参):
        '缺省展开成 bing 与 auto，并核对当前明文'
        if 数据 is 未传参 or 数据 is 无数据 or 数据 is None:
            数据={}
        if not isinstance(数据,dict):
            raise ValueError('思考翻译配置必须是对象')
        提供方=配置项(数据,'provider','bing')
        if 读易失(提供方) not in 提供方偏好:
            raise ValueError('翻译提供方必须是 bing、google、deepseek-account 或 deepseek-official')
        语言=配置项(数据,'targetLanguage','auto')
        明文语言=读易失(语言)
        if not isinstance(明文语言,str) or 语言偏好模式.fullmatch(明文语言) is None:
            raise ValueError('目标语言必须是 auto 或语言代码')
        return {'provider':提供方,'targetLanguage':语言}

配置=配置模式()

def 等中止(信号):
    '阻塞到信号中止'
    事件=getattr(信号,'_事件',None)
    if 事件 is not None:
        事件.wait()
        return
    信号.wait()

def 中止原因(信号):
    '竞速拒绝用的中止异常'
    原因=取原因(信号)
    if isinstance(原因,BaseException):
        return 原因
    if 原因 is not None:
        return RuntimeError(str(原因))
    return RuntimeError('The operation was aborted')

class 思考翻译控制器(远程服务):
    '可选的思考翻译把会话存储交给 translator'
    def __init__(自身,上下文,配置值=None):
        '登记 cotTranslation，并关掉 settings 自动写入'
        super().__init__(上下文,'cotTranslation',{'namespace':'cotTranslation'})
        自身.上下文=上下文
        自身.配置=配置.校验数据({} if 配置值 is None else 配置值)

        def 关闭设置自动(子):
            '本纤程关闭 settings 自动写入'
            def 挂配置():
                '把 auto:false 绑到本插件纤程'
                return 子.settings.configure({'auto':False},上下文.纤程)
            子.副作用(挂配置)
        上下文.依赖启动(['settings'],关闭设置自动)

    @远程
    def limits(自身,信号):
        '读已接受偏好和请求上限，不发送文本。返回期约'
        def 读取(值=None):
            '核对取消后再读可用提供方'
            若已中止则抛出(信号)
            可用=自身.上下文.translator.可用提供方(信号)
            若已中止则抛出(信号)
            return {
                'maxTextChars':自身.上下文.translator.最大文本字符,
                'preferences':{
                    'provider':读易失(自身.配置['provider']),
                    'targetLanguage':读易失(自身.配置['targetLanguage']),
                },
                'availableProviders':可用,
            }
        起点=期约()
        结果=起点.然后(读取)
        起点.解决(None)
        return 结果

    @远程
    def translate(自身,请求,信号):
        '按读者所选提供方翻译一段展示文本。返回期约，兑现译文；取消只停本次等待'
        def 转失败(错误):
            '已取消则抛取消原因，其余包成翻译失败'
            若已中止则抛出(信号)
            raise 远程错误(失败码,'Translation failed',{})
        def 执行(值=None):
            '先直接翻译；未激活会话则激活后再试一次'
            try:
                若已中止则抛出(信号)
                规格=自身.解析所选(请求)
                try:
                    return 自身.上下文.translator.翻译(规格,信号)
                except 翻译错误 as 错误:
                    if 错误.code!='TRANSLATION_SESSION_INACTIVE' or 规格.get('sessionId') is None:
                        raise
                若已中止则抛出(信号)
                return 自身.等激活再译(规格,信号).捕获(转失败)
            except Exception:
                return 转失败(None)
        起点=期约()
        结果=起点.然后(执行)
        起点.解决(None)
        return 结果

    def 等激活再译(自身,规格,信号):
        '未激活会话先走普通激活，再重试一次。返回期约；取消只停本次等待'
        激活=期约()
        def 跑激活():
            '激活完成则兑现；失败在已取消时记一条警告再拒绝'
            try:
                结果=自身.上下文.sessionController.resolveAgent(规格['sessionId'])
                if isinstance(结果,dict) and 'error' in 结果:
                    raise 结果['error']
                激活.解决(None)
            except Exception as 错误:
                if 已中止(信号):
                    自身.上下文.日志.警告('Reasoning translation Session activation failed after cancellation')
                激活.拒绝(错误)
        启动守护线程(跑激活)
        取消=期约()
        def 转发中止():
            '信号中止时拒绝取消期约'
            等中止(信号)
            取消.拒绝(中止原因(信号))
        if 已中止(信号):
            取消.拒绝(中止原因(信号))
        else:
            启动守护线程(转发中止)
        def 激活后(值=None):
            '激活结束后再按当前偏好翻译一次'
            若已中止则抛出(信号)
            return 自身.上下文.translator.翻译(自身.解析所选(规格),信号)
        return 期约.竞速([激活,取消]).然后(激活后)

    def 解析所选(自身,请求):
        '请求必须使用已接受的提供方和显式目标语言'
        已接受=读易失(自身.配置['provider'])
        提供方=已接受 if 请求.get('provider') is None else 请求['provider']
        if 提供方!=已接受:
            raise RuntimeError('Translation provider is not selected')
        目标语言=读易失(自身.配置['targetLanguage'])
        if 目标语言!='auto' and 请求.get('targetLanguage')!=目标语言:
            raise RuntimeError('Translation language is not selected')
        体=dict(请求)
        体['provider']=提供方
        return 自身.上下文.translator.解析(体)

远程贡献={
    'package':'@deepseek-ai/dsh-experimental-client-ui-cot-translation',
    'namespace':'cotTranslation',
}

def 应用(上下文,配置值=None):
    '挂上思考翻译 Remote'
    return 思考翻译控制器(上下文,配置值)

inject=依赖
apply=应用
Config=配置
default=思考翻译控制器
name='cotTranslation'
