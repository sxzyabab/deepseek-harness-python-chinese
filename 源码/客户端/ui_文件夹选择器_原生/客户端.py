import builtins#页面 window 可能挂在内置名上
from .流 import 原生目录流#无渲染原生选目录占用方

__all__=['依赖','应用','原生目录流']#仅中文公开名

依赖=['slots','uiWorkspace']#槽位注册表与工作区 UI

def 取桌面桥():#读页面注入的选择器
    '优先模块名，其次 window。没有则 None，交给宿主选择器。'
    try:#本模块被注入时
        return __DSH_DIRECTORY_PICKER__#桌面桥
    except NameError:#未注入到模块
        pass#再看窗口
    窗口=globals().get('window', getattr(builtins, 'window', None))#页面窗口
    if isinstance(窗口,dict):#字典窗口
        if '__DSH_DIRECTORY_PICKER__' in 窗口:#有桥
            return 窗口['__DSH_DIRECTORY_PICKER__']#桥
        return None#没有
    if 窗口 is not None:#对象窗口
        return getattr(窗口, '__DSH_DIRECTORY_PICKER__', None)#桥或没有
    return getattr(builtins, '__DSH_DIRECTORY_PICKER__', None)#内置或没有

def 应用(上下文):#安装原生选目录浏览器半边
    '经 slots.inject 把无渲染的原生流程登记进两个 directory-flow 洞。选出的路径交给 onPicked，不登记工作区。'
    桌面=取桌面桥()#桌面桥
    def 注入面():#挑选入口
        '桌面桥优先，否则 Host OS 选择器'
        def 挑选():#打开选择器
            '请桌面桥或 Host 打开单目录选择器'
            if 桌面 is not None:#有桥
                return 桌面['pick']() if isinstance(桌面,dict) else 桌面.pick()#桌面
            return 上下文.uiWorkspace.pickDirectory()#Host
        return {'pick':挑选}#注入面
    def 两侧登记():#等两侧洞出现后同一笔事务登记
        '两次登记做成一笔事务性 effect'
        yield 上下文.slots.register({#登记主屏无渲染占用方
            'name':'conversation.hero.workspace.directoryFlow','inject':注入面,#主屏槽名与注入面
        },原生目录流)#主屏占用方组件
        yield 上下文.slots.register({#登记侧栏无渲染占用方
            'name':'sidebar.workspaces.directoryFlow','inject':注入面,#侧栏槽名与注入面
        },原生目录流)#侧栏占用方组件
    def 等侧栏():#等侧栏洞
        '嵌套 inject 内层'
        return 上下文.slots.inject('sidebar.workspaces.directoryFlow',两侧登记)#内层
    上下文.slots.inject('conversation.hero.workspace.directoryFlow',等侧栏)#外层

inject=依赖#框架槽
apply=应用#框架槽
