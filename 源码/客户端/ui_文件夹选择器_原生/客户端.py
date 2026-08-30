"""原生选目录后端的浏览器半边。

用无渲染占用方填上 ui-workspace 的两个 directory-flow 洞；每次 open 都去驱动 host.pickDirectory，并把唯一结果经拥有方会话回报。

对齐上游 `ui-directory-picker-native/src/client/index.ts`。公开面仅中文名。
"""
from .流 import 原生目录流#无渲染原生选目录占用方

__all__=['注入','应用','原生目录流']#仅中文公开名

注入=['slots','workspaces']#槽位注册表与工作区服务

def 应用(上下文):#安装原生选目录浏览器半边
    """经 slots.inject 把无渲染的原生流程登记进两个 directory-flow 洞。"""
    def 注入面():#绑定 host.pickDirectory
        """本流驱动的线上调用。"""
        def 挑选():#打开原生单目录选择器
            """请本地 Host 打开其原生单目录选择器。"""
            return 上下文.workspaces.pickDirectory()#挑选
        return {'pick':挑选}#注入面
    def 两侧登记():#等两侧洞出现后同一笔事务登记
        """两次登记做成一笔事务性 effect。"""
        yield 上下文.slots.register({#登记主屏无渲染占用方
            'name':'conversation.hero.workspace.directoryFlow','inject':注入面,#主屏槽名与注入面
        },原生目录流)#主屏占用方组件
        yield 上下文.slots.register({#登记侧栏无渲染占用方
            'name':'sidebar.workspaces.directoryFlow','inject':注入面,#侧栏槽名与注入面
        },原生目录流)#侧栏占用方组件
    def 等侧栏():#等侧栏洞
        """嵌套 inject 内层。"""
        return 上下文.slots.inject('sidebar.workspaces.directoryFlow',两侧登记)#内层
    上下文.slots.inject('conversation.hero.workspace.directoryFlow',等侧栏)#外层
