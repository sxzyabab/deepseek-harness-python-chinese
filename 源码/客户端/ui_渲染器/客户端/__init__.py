from . import (
    作用域槽,
    应用组装,
    同步外部存储声明,
    登记表,
    绑定,
    绑定选择器,
)
from .作用域槽 import 创建槽渲染器,取出口,标记已连接#渲染器与卸下
from .应用组装 import 构建渲染应用#应用树
from .登记表 import 槽登记表#槽登记服务

__all__=[#同目录模块，以及 index 里的业务名
    '作用域槽','应用组装','同步外部存储声明','登记表','绑定','绑定选择器',
    '依赖','应用','槽登记表','创建槽渲染器','构建渲染应用','挂载应用','启动交接',
]#公开面结束

依赖=[]#组装前没有 inject


def 启动交接(应用工厂,启动快照):
    '启动页的类名和 HTML 已在浏览器读出。同步收场是应用树'
    if isinstance(启动快照,dict):#快照已传到 Python
        应用树=应用工厂()#应用
        return 应用树#替换启动页
    return 应用工厂()#没有快照也挂应用


def 挂载应用(容器,应用工厂):
    '读启动页后把应用挂进容器。返回的函数卸下时调用拆除'
    启动=None#启动页节点
    查询=getattr(容器,'querySelector',None)#浏览器查询
    if callable(查询):#容器是文档节点
        启动=查询(':scope > [data-dsh-boot]')#内核留下的启动页
    if 启动 is not None:#有启动页
        快照={#浏览器上读到的快照
            'className':启动.className,#类名
            'html':启动.innerHTML,#内部 HTML
        }#快照
        树=启动交接(应用工厂,快照)#换成应用
        if getattr(启动,'parentNode',None) is not None:#还挂着
            启动.remove()#摘掉启动页
    else:#没有启动页
        树=应用工厂()#直接画应用
    if 树 is not None and getattr(树,'parentNode',None) is None:#还没进容器
        容器.appendChild(树)#挂上
    标记已连接(树)#之后被摘掉才拆除

    def 卸载():
        '卸下根，并调用拆除'
        出口=取出口(树)#根出口
        if 出口 is not None:#有出口
            出口.拆除()#退订并调用拆除
        if 树 is not None and getattr(树,'parentNode',None) is not None:#还在容器里
            树.remove()#摘掉

    return 卸载#交给启动内核


def 应用(上下文,配置=None):
    '安装槽位渲染器，并交出挂载面'
    槽登记表实例=槽登记表(上下文)#登记服务
    槽登记表实例.install(创建槽渲染器())#装上包裹渲染

    def 挂载(容器):
        '挂上应用。卸下时调用拆除'
        return 挂载应用(容器,构建渲染应用({'ctx':上下文}))#卸载函数

    上下文.反射.提供服务('uiRenderer',{'mount':挂载})#挂载面


apply=应用#加载器入口
inject=依赖#依赖名
