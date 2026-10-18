'浏览器半边。提供 resources，并把每个地址的活源交给槽位组件'
from . import 资源#注册表与地址协议
from . import 约定#公开面说明

__all__=['资源','约定','依赖','应用']#同目录模块与入口

依赖=['slots']#浏览器入口依赖槽位服务


def 应用(上下文,配置=None):
    '提供 resources，并贡献根键控钩子 resource。组件上的名字是 useResource'
    注册表=资源.资源注册表(上下文)#在应用顶层建造，供其它插件的应用阶段登记
    拆除服务=上下文.提供服务('resources',注册表)#服务面

    def 服务面寿命():
        '后登记的提供方先卸，服务面留到最后'
        def 拆除():
            '卸掉 resources'
            拆除服务()#拆除提供
        return 拆除#拆除器

    上下文.副作用(服务面寿命,'client-resources: service face')#服务面寿命

    def 资源钩子(地址):
        '这一地址的活源'
        return 注册表.取源(地址)#同一地址始终是同一个源

    上下文.slots.provideRoot({#根标准源
        'keyedHooks':{#键控钩子
            'resource':资源钩子,#useResource
        },#键控结束
    })#提供根结束


inject=依赖#框架槽
apply=应用#框架槽
