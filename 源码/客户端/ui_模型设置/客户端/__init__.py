from ...模块.客户端.通告 import 取握手窗口
from ..上手引导配置 import 上手引导配置全局键,配置
from ..引导文案 import 欢迎通知设置命名空间
from . import (
    DeepSeek模型编辑器,
    密钥判定,
    密钥输入,
    存储,
    协议标注,
    模型分区,
    模型列表编辑器,
    模型推理强度,
    模型表行,
    模型输入类型,
    槽位约定,
    编辑器页脚,
    自定义提供方卡片,
    文案,
    欢迎存储,
    欢迎通知,
    引导对话框,
    引导模态,
    提供方编辑器,
)
from .文案 import 中文,英文
from .存储 import 模型设置存储
from .欢迎存储 import 欢迎通知存储

__all__=[
    'DeepSeek模型编辑器','密钥判定','密钥输入','存储','协议标注',
    '模型分区','模型列表编辑器','模型推理强度','模型表行','模型输入类型',
    '槽位约定','编辑器页脚','自定义提供方卡片','文案','欢迎存储','欢迎通知',
    '引导对话框','引导模态','提供方编辑器',
    '命名空间','依赖','应用','已加载则刷新',
]

命名空间='settings.models'
依赖=[
    'slots','locale','remote','remote.credentials','remote.llm','remote.settings','remote.session',
    'configForms','settingsSchema',
]

def 已加载则刷新(控制器):
    '没打开过的模型页不因后台失效去拉取'
    if 控制器.存储.getSnapshot()['status']=='idle':
        return
    控制器.加载()

def 应用(上下文,配置=None):
    '登记模型页、预览说明和官方 DeepSeek 引导，并在推送失效时刷新已打开的页'
    窗口=取握手窗口()
    if 上手引导配置全局键 in 窗口:
        载荷=窗口[上手引导配置全局键]
    else:
        载荷=None
    已配=配置({} if 载荷 is None else 载荷)
    凭据引导=已配['credentialOnboarding'] is True and getattr(窗口,'dshDesktop',None) is None
    def 登记词典():
        '登记本页中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-models: copy dictionaries')
    模式服务=上下文.settingsSchema
    模式={
        '再水合':模式服务.再水合,
        '校验':模式服务.校验,
        '路径节点':模式服务.路径节点,
        '取路径':模式服务.取路径,
        '有路径':模式服务.有路径,
        '设路径':模式服务.设路径,
        '删路径':模式服务.删路径,
    }
    def 存凭据(引用,值):
        '存一条凭据。拒绝时返回宿主消息'
        应答=上下文.remote.credentials.set(引用,值)
        if 应答['ok'] is True:
            return None
        return 应答['error']['message']
    def 卸凭据(引用):
        '去掉一条凭据。拒绝时返回宿主消息'
        应答=上下文.remote.credentials.unset(引用)
        if 应答['ok'] is True:
            return None
        return 应答['error']['message']
    def 写设置(名字空间,操作表,期望修订):
        '按路径改一个设置命名空间'
        应答=上下文.remote.settings.mutate(名字空间,操作表,期望修订)
        if 应答['ok'] is True:
            return {'kind':'written','view':应答['value']}
        码=应答['error']['code']
        消息=应答['error']['message']
        if 码=='settings/conflict':
            return {'kind':'conflict','message':消息}
        return {'kind':'refused','message':消息}
    def 探询模型(设置名,请求):
        '问端点现在有哪些模型'
        应答=上下文.remote.llm.discoverModels(设置名,请求)
        if 应答['ok'] is True:
            return {'kind':'found','models':应答['value']}
        return {'kind':'refused','message':应答['error']['message']}
    操作={
        '存凭据':存凭据,
        '卸凭据':卸凭据,
        '写设置':写设置,
        '探询模型':探询模型,
    }
    控制器=模型设置存储(上下文,模式,上下文.configForms.describe())
    翻译=上下文.locale.bind(命名空间)
    def 注入模型():
        '模型页的存储、操作和文案'
        return {
            'controller':控制器,
            'hooks':{'snapshot':控制器.存储},
            'operations':操作,
            'schema':模式,
            't':翻译,
        }
    def 注入官方():
        '官方引导复用同一份存储'
        def 跟踪(名,属性=None):
            '有产品埋点才记'
            埋点=上下文.get('productAnalytics')
            if 埋点 is None:
                return
            埋点.track(名,属性)
        return {
            'automatic':凭据引导,
            'track':跟踪,
            'controller':控制器,
            'hooks':{'models':控制器.存储},
            'operations':操作,
            'schema':模式,
            't':翻译,
        }
    欢迎控制器=欢迎通知存储(上下文.configForms.get(欢迎通知设置命名空间))
    def 注入欢迎():
        '预览说明的确认存储'
        return {
            'controller':欢迎控制器,
            'hooks':{'welcome':欢迎控制器.存储},
            't':翻译,
        }
    def 推送失效():
        '设置、凭据、适配器或连接重置时，已打开的模型页再读一次'
        def 刷新模型(*_位置):
            '忽略事件参数'
            已加载则刷新(控制器)
        远程开=getattr(上下文.remote,'$on')
        拆除器=[
            远程开('settings/document-updated',刷新模型),
            远程开('credentials/record-updated',刷新模型),
            远程开('credentials/reference-updated',刷新模型),
            远程开('llm/adapters-updated',刷新模型),
            上下文.监听('connection/reset',刷新模型),
        ]
        def 拆除():
            '停欢迎跟随，并拆掉这些监听'
            欢迎控制器.拆除()
            for 拆 in 拆除器:
                拆()
        return 拆除
    上下文.副作用(推送失效,'ui-settings-models: pushed invalidations')
    def 导航():
        '侧栏标题用中文表原文'
        return 中文['nav']
    def 登记模型():
        '登记 settings.section 的模型页，并留出卡片和页脚空位'
        return 上下文.slots.register({
            'name':'settings.section',
            'id':'models',
            'order':10,
            'label':导航,
            'inject':注入模型,
            'children':{
                'settings.models.provider-card':{'kind':'keyed','scope':'root'},
                'settings.models.footer':{'kind':'list','scope':'root'},
            },
        },模型分区.模型分区)
    上下文.slots.inject('settings.section',登记模型)
    if getattr(窗口,'dshDesktop',None) is None:
        def 登记欢迎():
            '浏览器里才登记预览说明'
            return 上下文.slots.register({
                'name':'settings.onboarding',
                'id':'welcome-notice',
                'order':-100,
                'inject':注入欢迎,
            },欢迎通知.欢迎通知)
        上下文.slots.inject('settings.onboarding',登记欢迎)
    def 登记官方():
        '官方 DeepSeek 引导，并留出登录空位'
        return 上下文.slots.register({
            'name':'settings.onboarding',
            'id':'deepseek-official',
            'order':0,
            'inject':注入官方,
            'children':{
                'settings.models.sign-in':{'kind':'single','scope':'root'},
            },
        },引导对话框.官方引导对话框)
    上下文.slots.inject('settings.onboarding',登记官方)

inject=依赖
apply=应用
