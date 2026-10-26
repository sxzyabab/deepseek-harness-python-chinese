from ...模块.客户端.通告 import 取握手窗口
from . import 发现区,文案,呈现,插件详情区,市场存储
from .发现区 import 发现区 as 发现区类
from .市场存储 import 发现控制
from .文案 import 中文,俄文,德文,日文,法文,英文,西班牙文,葡萄牙文

__all__=['发现区','文案','呈现','插件详情区','市场存储','名称','依赖','应用']

名称='ui-plugin-market'
命名空间='pluginMarket'
依赖=['slots','locale','remote','remote.pluginMarket','remote.pluginRegistryProbe']

def 应用(上下文,配置=None):
    '把发现登记到插件页，并在 Host 变更时保持最新'
    def 登记词典():
        '挂上各语言文案。看得见的字走中文表'
        return 上下文.locale.register(命名空间,{
            'zh':中文,'en':英文,'ja':日文,'es':西班牙文,'fr':法文,'de':德文,'ru':俄文,'pt':葡萄牙文,
        })
    上下文.副作用(登记词典,'ui-plugin-market: dictionaries')
    def 取基址():
        '图片地址相对这次页面的基址'
        return 取握手窗口().document.baseURI
    控制=发现控制(上下文,取基址)
    def 登记控制():
        '卸下时停止发布'
        def 清理():
            '停止发布'
            控制.拆除()
        return 清理
    上下文.副作用(登记控制,'ui-plugin-market: controller')
    def 订失效():
        '索引源、已安装组合包和重连'
        def 源变(块=None):
            '索引源变了'
            控制.源变更()
        def 包变(块=None):
            '组合包变了'
            控制.组合包变更()
        def 重置():
            '重连后重读索引源，并丢掉详情'
            控制.源变更()
            控制.详情重置()
        拆除表=[
            getattr(上下文.remote,'$on')('plugin-market/changed',源变),
            getattr(上下文.remote,'$on')('plugin-manager/changed',包变),
            上下文.on('connection/reset',重置),
        ]
        def 退订():
            '退掉全部订阅'
            for 拆 in 拆除表:
                拆()
        return 退订
    上下文.副作用(订失效,'ui-plugin-market: host invalidations')
    def 解析文本(文本):
        '索引自己的多语言字段'
        return 上下文.locale.resolveText(文本)
    面=控制.面(解析文本)
    def 标签():
        '标签上的中文'
        return 中文['title']
    def 注入():
        '发现页拿到控制器的面'
        return 面
    def 挂标签():
        '登记发现标签'
        return 上下文.slots.register({
            'name':'plugins.tab',
            'id':'discover',
            'label':标签,
            'locale':命名空间,
            'inject':注入,
        },发现区类)
    上下文.slots.inject('plugins.tab',挂标签)

inject=依赖
name=名称
apply=应用
default=应用
