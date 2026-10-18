from ...模块.客户端.通告 import 取握手窗口
import pywebbridge
from . import 流#无渲染原生目录流

__all__=['流','依赖','应用']

依赖=['slots','uiWorkspace']#槽位注册表与工作区界面服务

def 应用(上下文,配置=None):
    '桌面桥在就用它的 pick，否则用宿主的 pickDirectory。两个 directory-flow 洞声明齐了，再同一笔事务各登记一份占用者'
    窗口=取握手窗口()#页面全局，对应 globalThis
    桌面=窗口['__DSH_DIRECTORY_PICKER__']#桌面预加载放上的选择器
    未定义=pywebbridge.基础.undefined#属性不存在时读到的值
    if 桌面 is 未定义:#没有桌面桥
        def 挑选():
            '打开宿主的单目录选择器'
            return 上下文.uiWorkspace.pickDirectory()#宿主
    else:#有桌面桥
        def 挑选():
            '打开桌面桥的单目录选择器，不走宿主'
            return 桌面.pick()#桌面
    def 注入面():
        '两个洞共用。只有 pick'
        return {'pick':挑选}#注入面
    def 等侧栏():
        '英雄洞出现之后再等侧栏洞。两边都在才安装这一对'
        def 两侧登记():
            '两次登记是一笔事务，任一失败就整笔撤回'
            英雄占用=流.原生目录流()#英雄洞一份状态
            侧栏占用=流.原生目录流()#侧栏洞一份状态
            拆英雄=上下文.slots.register({'name':'conversation.hero.workspace.directoryFlow','inject':注入面},英雄占用)#英雄拆除器
            拆侧栏=上下文.slots.register({'name':'sidebar.workspaces.directoryFlow','inject':注入面},侧栏占用)#侧栏拆除器
            def 卸英雄():
                '登记撤下时丢掉还在飞的结算，并卸掉登记'
                英雄占用.卸下()#标死
                拆英雄()#卸登记
            def 卸侧栏():
                '登记撤下时丢掉还在飞的结算，并卸掉登记'
                侧栏占用.卸下()#标死
                拆侧栏()#卸登记
            yield 卸英雄#英雄拆除器
            yield 卸侧栏#侧栏拆除器
        return 上下文.slots.inject('sidebar.workspaces.directoryFlow',两侧登记)#等侧栏洞
    上下文.slots.inject('conversation.hero.workspace.directoryFlow',等侧栏)#等英雄洞

inject=依赖#装载器读的依赖名
apply=应用#装载器读的入口名
