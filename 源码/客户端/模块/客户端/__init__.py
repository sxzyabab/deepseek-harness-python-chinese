from . import (
    通告,#订阅派发
    发行变更,#宿主发行门
    清单,#启动图解析
    条目生命周期,#纤程与样式拆除
    条目,#页面条目表
    系统,#模块系统
)
from ..异常 import 客户端模块错误#本包异常
from .清单 import (
    精确包说明符,#裸包根
    解析启动清单,#解析启动图
    解析客户端声明,#dsh.client
    剥客户端后缀,#剥 /client
)
from .条目生命周期 import 拆除条目纤程#替换前拆纤程
from .系统 import 客户端模块系统#模块系统类


__all__=[#同目录模块，以及 index 里的运行时名字
    '通告','发行变更','清单','条目生命周期','条目','系统',
    '创建客户端模块系统','应用','createClientModuleSystem','apply','inject',
    '客户端模块系统','拆除条目纤程',
    '精确包说明符','解析启动清单','解析客户端声明','剥客户端后缀',
]

依赖=['加载器']#页面加载器。上游服务名是 loader，这里的服务名是加载器


def 创建客户端模块系统(目标,启动模块,选项):
    '从门面已经物化的 modules 包建造活的模块系统'
    系统选项={#构造选项
        'manifest':解析启动清单(选项['boot']),#解析启动图
        'staticModules':选项['staticModules'],#平台种子
        'registrationTarget':目标,#登记门面
        'bootstrapModule':启动模块,#已物化的启动模块
    }#基
    if 'loadBundle' in 选项 and 选项['loadBundle'] is not None:#可选加载钩
        系统选项['loadBundle']=选项['loadBundle']#写入
    if 'document' in 选项:#这次握手的文档
        系统选项['document']=选项['document']#样式认领用它
    return 客户端模块系统(系统选项)#构造


def 应用(上下文,配置=None):
    '把内核建成的模块系统登记为 ctx.modules'
    加载器=上下文.加载器#页面加载器
    模块=加载器.内部加载器#内部模块系统
    if 模块 is None or getattr(模块,'version',None)!='client':#不是客户端模块系统
        raise 客户端模块错误('client-modules: the Loader has no client module system')#大声失败
    上下文.反射.提供服务('modules',模块)#提供 modules


createClientModuleSystem=创建客户端模块系统#引导脚本要的导出名
apply=应用#插件入口
inject=依赖#框架槽
