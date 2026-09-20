from .系统 import 客户端模块系统#再导出模块系统
from .条目 import 客户端条目表,客户端条目状态#页面条目调和面
from .条目生命周期 import 拆除条目纤程,移除包拥有样式#条目纤程与样式拆除
from .清单 import (#再导出线约定
    客户端模块错误,#本包异常
    精确包说明符,#裸包根说明符
    解析启动清单,#解析
    解析客户端声明,#dsh.client 声明
    剥客户端后缀,#剥 /client
    启动清单,#清单
    启动模块行,#模块行
    启动插件行,#插件行
    网页启动入口,#入口
    网页启动图,#图
    客户端插件交接,#交接
    客户端窗口,#窗口
    客户端模块记录,#记录
    客户端模块加载器,#加载器
    客户端模块系统选项,#选项
)#清单面

__all__=[#仅中文公开名
    '应用',
    '创建客户端模块系统',
    '客户端模块错误',
    '客户端模块系统',
    '客户端条目表',
    '客户端条目状态',
    '拆除条目纤程',
    '移除包拥有样式',
    '精确包说明符',
    '解析启动清单',
    '解析客户端声明',
    '剥客户端后缀',
    '启动清单',
    '启动模块行',
    '启动插件行',
    '网页启动入口',
    '网页启动图',
    '客户端插件交接',
    '客户端窗口',
    '客户端模块记录',
    '客户端模块加载器',
    '客户端模块系统选项',
]

依赖=['loader']#所需服务：发布其内部模块系统的 Loader

def 创建客户端模块系统(目标,启动模块,选项):
    """从 HTML 门面已物化的 modules 打包建造活模块系统。"""
    系统选项={#构造选项
        'manifest':解析启动清单(选项['boot']),#解析启动图
        'staticModules':选项['staticModules'] if 'staticModules' in 选项 else None,#平台种子
        'registrationTarget':目标,#登记门面
        'bootstrapModule':启动模块,#已物化启动模块
    }#基
    if 'loadBundle' in 选项 and 选项['loadBundle'] is not None:#可选加载钩
        系统选项['loadBundle']=选项['loadBundle']#写入
    return 客户端模块系统(系统选项)#构造系统

def 应用(上下文):#安装浏览器半边
    """把内核建成的模块系统登记为 ctx.modules。"""
    加载器=上下文.loader#取 Loader
    模块=加载器.internal#内部模块系统
    if 模块 is None or getattr(模块,'version',None)!='client':#不是客户端模块系统
        raise 客户端模块错误('client-modules: the Loader has no client module system')#大声失败
    上下文.反射.提供服务('modules',模块)#提供 ctx.modules

inject=依赖#框架槽
apply=应用#框架槽
