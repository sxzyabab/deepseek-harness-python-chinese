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

def 启动交接(应用工厂,启动快照):#启动交接
    """在用应用替换前，先透传内核拥有的加载 DOM。"""
    return {#交接树
        'type':'boot-handoff',#类型
        'boot':启动快照,#启动快照
        'app':应用工厂,#真应用工厂
    }#树结束

def 挂载应用(容器,应用工厂):#挂载应用
    """经 hydrate 保留无框架启动 DOM；否则同步首帧。"""
    启动=None#启动页
    查询=getattr(容器,'querySelector',None)#查子
    if callable(查询):#有 DOM
        启动=查询(':scope > [data-dsh-boot]')#找启动页
    if 启动 is not None:#有启动页
        快照={#启动快照
            'className':getattr(启动,'className',''),#保留 class
            'html':getattr(启动,'innerHTML',''),#保留 HTML
        }#快照结束
        return {'type':'hydrated-root','tree':启动交接(应用工厂,快照),'unmount':lambda:None}#hydrate 交接
    return {'type':'created-root','tree':应用工厂(),'unmount':lambda:None}#新建根

def 应用(上下文):#浏览器侧安装入口
    """安装槽位渲染器并提供应用挂载面。"""
    槽们=槽登记表(上下文)#构造注册表服务
    槽们.install(创建槽渲染器())#安装出口机械
    def 挂载(容器):#挂载操作
        """挂载并返回卸载。"""
        根=挂载应用(容器,构建渲染应用({'ctx':上下文}))#挂载应用
        return 根['unmount']#卸载根
    上下文.reflect.provide('uiRenderer',{'mount':挂载})#提供挂载面

SlotRegistry=槽登记表#上游名
createSlotRenderer=创建槽渲染器#上游名
buildRenderApp=构建渲染应用#上游名
