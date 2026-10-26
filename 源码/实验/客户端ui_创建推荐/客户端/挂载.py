'登记个性化页面卡片正文和它的文案'
from .文案 import 中文,日文,俄文,德文,英文,法文,葡萄牙文,西班牙文
from .信息存储 import 创建创建信息存储
from .卡片 import 页面卡片正文

__all__=['依赖','应用']

依赖=['locale','actionCards']
inject=依赖


def 应用(上下文,配置值=None):
    '为 create_personalized_page 登记正文。说明是否收起记在这个浏览器里'
    信息已收=创建创建信息存储()

    def 登记词典():
        '登记八种语言'
        return 上下文.locale.register('creationRecommendations',{
            'en':英文,'zh':中文,'ja':日文,'es':西班牙文,
            'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })

    上下文.副作用(登记词典,'creation-recommendations: locale')

    def 正文(份额):
        '带上这个浏览器的说明偏好'
        属性=dict(份额)
        属性['infoDismissed']=信息已收
        return 页面卡片正文(属性)

    def 登记正文():
        '登记创建卡片正文'
        return 上下文.actionCards.登记({
            'action':'create_personalized_page',
            'locale':'creationRecommendations',
            'Body':正文,
        })

    上下文.副作用(登记正文,'creation-recommendations: card body')


apply=应用
