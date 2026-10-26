'登记官方插件卡片正文、目录 Remote 和文案'
from ....客户端.存储 import 创建快照存储
from .文案 import 中文,日文,俄文,德文,英文,法文,葡萄牙文,西班牙文
from .卡片 import 插件卡片正文

__all__=['依赖','挂载插件推荐']

依赖=['locale','remote','actionCards','pluginNavigation']


def 远程值(结果):
    '成功时取出目录文本。回复丢失时是 None'
    if isinstance(结果,dict) and 结果.get('ok') is True:
        return 结果.get('value')
    if isinstance(结果,dict) and 'ok' in 结果:
        return None
    return 结果


def 登记正文(上下文):
    '目录文本按插件名记住。这一插件活着的时候都在'
    目录=创建快照存储({})

    def 描述(会话标识,调用号):
        '读这一张卡片当前的目录文本'
        return 远程值(上下文.remote.pluginRecommendations.describe(会话标识,调用号))

    def 打开详情(包名):
        '打开插件详情，不启用'
        上下文.pluginNavigation.openBundle(包名)

    服务={
        'catalog':目录,
        'describe':描述,
        'openDetails':打开详情,
        'resolveText':上下文.locale.resolveText,
    }

    def 登记词典():
        '登记八种语言'
        return 上下文.locale.register('pluginRecommendations',{
            'en':英文,'zh':中文,'ja':日文,'es':西班牙文,
            'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })

    上下文.副作用(登记词典,'plugin-recommendations: locale')

    def 正文(份额):
        '把目录服务并进框架份额'
        属性=dict(份额)
        属性.update(服务)
        return 插件卡片正文(属性)

    def 登记卡片():
        '登记官方插件卡片正文'
        return 上下文.actionCards.登记({
            'action':'enable_official_plugin',
            'locale':'pluginRecommendations',
            'Body':正文,
        })

    上下文.副作用(登记卡片,'plugin-recommendations: card body')


def 挂载插件推荐(上下文,贡献):
    '先挂目录 Remote，再登记正文。卸的时候正文先走'
    卸远程=getattr(上下文.remote,'$mount')(贡献)
    正文纤程=None
    try:
        正文纤程=上下文.依赖启动(['remote.pluginRecommendations'],登记正文)
        正文纤程.等待()
    except Exception as 错误:
        if 正文纤程 is not None:
            正文纤程.拆除()
        if callable(卸远程):
            卸远程()
        raise 错误

    def 卸下():
        '先卸正文，再卸 Remote'
        正文纤程.拆除()
        if callable(卸远程):
            卸远程()

    return 卸下
