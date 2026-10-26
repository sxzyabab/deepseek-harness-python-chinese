'收起的会话视图、能到达时的插件发现，以及创造草稿'
import os
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标Cordis插件14,图标勾描边常规,图标加号16
from ...ui_基础界面组件.菜单 import 样式表 as 菜单样式表
from .文案 import 中文句

__all__=['入口菜单内容']

样式模块='entry-menu'

def 确保样式(文档):
    '菜单行样式和本页样式模块都要在'
    if 文档.getElementById('菜单样式') is None:
        样式=文档.createElement('style')
        样式.id='菜单样式'
        样式.textContent=菜单样式表
        文档.head.appendChild(样式)
    注入模块样式文件(
        文档,
        '入口菜单样式',
        os.path.join(os.path.dirname(__file__),'入口菜单.module.css'),
        样式模块,
    )

def 建(文档,标签,类名=None):
    '造一个挂了官方类名的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)

def 画图标(窗口,工厂,尺寸):
    '按边长画一枚已有图标'
    return 工厂({'window':窗口,'size':尺寸})

class 入口菜单内容:
    '先画收起的会话视图，再画发现和创造。不提供固定或排序'
    def __init__(自身,属性):
        '记下区域、回调和文案，并画出'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染时重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '会话区域才列出收起的视图。浏览一行只在导航服务在场时出现'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        def 取在场(值):
            '导航服务是否在场'
            return 值
        可浏览=False
        if 'usePluginNavigation' in 属性 and 属性['usePluginNavigation'] is not None:
            可浏览=属性['usePluginNavigation'](取在场) is True
            if 自身.已订 is not True and hasattr(属性['usePluginNavigation'],'_subscribe'):
                def 重画():
                    '在场状态变了就重画'
                    自身.渲染()
                属性['usePluginNavigation']._subscribe(重画)
                自身.已订=True
        区域=属性.get('region')
        入口列=属性.get('entries') or []
        if 区域!='conversation':
            入口列=[]
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
        根=文档.createElement('div')
        根.style.display='contents'
        for 条目 in 入口列:
            行=文档.createElement('button')
            行.type='button'
            行.setAttribute('role','menuitem')
            行.className='菜单项'
            if 条目.get('active') is True:
                行.setAttribute('aria-current','page')
            名盒=建(文档,'span','entryName')
            题=建(文档,'span','entryTitle')
            题.textContent='' if 条目.get('label') is None else str(条目['label'])
            名盒.appendChild(题)
            if 条目.get('active') is True:
                勾=画图标(窗口,图标勾描边常规,16)
                if 勾 is not None:
                    勾.classList.add('activeMark')
                    标样式模块(勾,样式模块)
                    名盒.appendChild(勾)
            行.appendChild(名盒)
            标识=条目.get('id')
            def 点入口(事件=None,标识=标识):
                '先关上菜单，再打开这个视图'
                if 属性.get('onDismiss') is not None:
                    属性['onDismiss']()
                if 属性.get('onOpen') is not None:
                    属性['onOpen'](标识)
            行.addEventListener('click',点入口)
            根.appendChild(行)
        if 可浏览:
            if len(入口列)>0:
                隔=文档.createElement('div')
                隔.className='菜单隔'
                隔.setAttribute('role','separator')
                根.appendChild(隔)
            浏览=文档.createElement('button')
            浏览.type='button'
            浏览.setAttribute('role','menuitem')
            浏览.className='菜单项'
            图=画图标(窗口,图标Cordis插件14,16)
            if 图 is not None:
                浏览.appendChild(图)
            字=文档.createElement('span')
            字.textContent=中文句('install')
            浏览.appendChild(字)
            def 点浏览(事件=None):
                '先关上菜单，再打开插件列表'
                if 属性.get('onDismiss') is not None:
                    属性['onDismiss']()
                if 属性.get('browsePlugins') is not None:
                    属性['browsePlugins']()
            浏览.addEventListener('click',点浏览)
            根.appendChild(浏览)
        if 可浏览 is not True and len(入口列)>0:
            隔=文档.createElement('div')
            隔.className='菜单隔'
            隔.setAttribute('role','separator')
            根.appendChild(隔)
        创造=文档.createElement('button')
        创造.type='button'
        创造.setAttribute('role','menuitem')
        创造.className='菜单项'
        加=画图标(窗口,图标加号16,16)
        if 加 is not None:
            创造.appendChild(加)
        创造字=文档.createElement('span')
        创造字.textContent=中文句('create')
        创造.appendChild(创造字)
        def 点创造(事件=None):
            '先关上菜单，再准备创造草稿'
            if 属性.get('onDismiss') is not None:
                属性['onDismiss']()
            if 属性.get('createPlugin') is not None:
                属性['createPlugin']()
        创造.addEventListener('click',点创造)
        根.appendChild(创造)
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
