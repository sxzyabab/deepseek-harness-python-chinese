"""浏览器 UI 渲染器。

对齐上游 `ui-renderer/src/client/index.ts`。公开面仅中文名。
在 Cordis 依赖激活后安装槽位渲染器，并暴露挂载操作。
"""
from .作用域槽 import 创建槽渲染器#槽位渲染器工厂
from .应用组装 import 构建渲染应用#应用组装
from .登记表 import 槽登记表#槽位注册表

__all__=[#仅中文公开名
    '注入','应用','槽登记表','创建槽渲染器','构建渲染应用','挂载应用','启动交接',
]#公开面结束

注入=[]#应用组装前无前置 inject

def 空卸载():
    """无卸载动作。"""
    return None#无

def 启动交接(应用工厂,启动快照):
    """在用应用替换前，先透传内核拥有的加载 DOM。"""
    return {#交接树
        'type':'boot-handoff',#类型
        'boot':启动快照,#启动快照
        'app':应用工厂,#真应用工厂
    }#树结束

def 挂载应用(容器,应用工厂):
    """经 hydrate 保留无框架启动 DOM；否则同步首帧。容器为 DOM 对象。"""
    启动=None#启动页
    try:#宿主 DOM 可选 querySelector
        查询=容器.querySelector#查子
    except AttributeError:#非 DOM
        查询=None#无
    if 查询 is not None:#有 DOM
        启动=查询(':scope > [data-dsh-boot]')#找启动页
    if 启动 is not None:#有启动页
        快照={#启动快照
            'className':启动.className,#保留 class
            'html':启动.innerHTML,#保留 HTML
        }#快照结束
        return {'type':'hydrated-root','tree':启动交接(应用工厂,快照),'unmount':空卸载}#hydrate 交接
    return {'type':'created-root','tree':应用工厂(),'unmount':空卸载}#新建根

def 应用(上下文):
    """安装槽位渲染器并提供应用挂载面。"""
    槽登记表实例=槽登记表(上下文)#构造注册表服务
    槽登记表实例.install(创建槽渲染器())#安装出口机械
    def 挂载(容器):
        """挂载并返回卸载。"""
        根=挂载应用(容器,构建渲染应用({'ctx':上下文}))#挂载应用
        return 根['unmount']#卸载根
    上下文.反射.提供服务('uiRenderer',{'mount':挂载})#提供挂载面
