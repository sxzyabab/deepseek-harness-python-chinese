import os
from ...ui_基础界面组件.icons import 图标下箭头描边常规
from ...ui_基础界面组件.菜单 import 菜单
from ...ui_基础界面组件.风险确认 import 风险确认
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .文案 import 中文,访问中文
from .呈现 import 完全权限预设,展示权限预设

__all__=['权限行']

样式模块='permission-row'

def 设置文案(键):
    '新会话权限设置的中文表。显示不走英文表'
    return 中文[键]

def 元素(文档,标签,类名):
    '造一个挂了权限行样式模块的节点'
    节点=文档.createElement(标签)
    节点.className=类名
    return 标样式模块(节点,样式模块)

class 权限行:
    '新会话默认权限。宿主没有这项设置时不占画面'
    def __new__(类,属性):
        '槽位把组件当函数调用，返回这一行的节点'
        自身=object.__new__(类)
        自身.属性=属性
        自身.打开=False
        自身.已认=False
        自身.确认完全=False
        自身.根=None
        自身.菜单=None
        自身.已订=False
        自身.已请求加载=False
        自身.退订表=[]
        自身.绘制中=False
        自身.待重画=False
        return 自身.渲染()

    def 选项标签(自身,选项):
        '内置预设用设置行中文。宿主改过的名字保持展示名'
        return 展示权限预设(选项['id'],选项['label'],设置文案)

    def 渲染(自身):
        '画出标题、说明和预设菜单。快照变了换掉旧节点'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(文档,'权限行样式',os.path.join(os.path.dirname(__file__),'权限行.module.css'),样式模块)
            def 取整份(快照):
                '整份设置行快照'
                return 快照
            状态=属性['usePermission'](取整份)
            if 状态['writable'] is not True or 状态['status']=='unavailable':
                自身.打开=False
                自身.已认=False
                自身.确认完全=False
            菜单对象=自身.菜单
            if 菜单对象 is not None:
                for 名 in ('拆外面','拆键','拆锚'):
                    拆=getattr(菜单对象,名,None)
                    if callable(拆):
                        拆()
                表面=getattr(菜单对象,'表面',None)
                if 表面 is not None and getattr(表面,'背板',None) is not None:
                    表面.背板.remove()
                自身.菜单=None
            旧=自身.根
            壳=文档.createElement('div')
            壳.style.display='contents'
            if 状态['status']!='unavailable':
                选中项=None
                for 项 in 状态['options']:
                    if 项['id']==状态['currentValue']:
                        选中项=项
                        break
                忙=状态['status']=='loading' or 状态['status']=='saving' or 自身.确认完全 is True
                if 选中项 is not None:
                    标签=自身.选项标签(选中项)
                elif 忙:
                    标签=中文['loading']
                else:
                    标签=中文['unavailable']
                if 状态['error'] is not None:
                    描述=状态['error']
                else:
                    描述=中文['description']
                行=元素(文档,'div','row')
                字区=元素(文档,'div','rowText')
                标题=元素(文档,'div','title')
                标题.textContent=中文['title']
                说明=元素(文档,'div','desc')
                说明.textContent=描述
                if 状态['error'] is not None:
                    说明.setAttribute('role','alert')
                字区.appendChild(标题)
                字区.appendChild(说明)
                行.appendChild(字区)
                条目表=[]
                for 项 in 状态['options']:
                    条目表.append({'id':项['id'],'label':自身.选项标签(项)})
                箭头=图标下箭头描边常规({'window':窗口,'className':'chevron'})
                标样式模块(箭头,样式模块)
                钮=元素(文档,'button','selector')
                钮.type='button'
                钮.setAttribute('aria-haspopup','menu')
                钮.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
                钮.disabled=忙 is True or 状态['writable'] is not True or len(状态['options'])==0
                钮.textContent=标签
                钮.appendChild(箭头)
                def 点按钮(事件=None):
                    '打开或关上预设菜单'
                    自身.打开=自身.打开 is not True
                    自身.渲染()
                钮.addEventListener('click',点按钮)
                def 关掉():
                    '菜单要求关上'
                    自身.打开=False
                    自身.渲染()
                def 选择(标识):
                    '点一项。还是当前值就只关上。完全权限先确认'
                    自身.打开=False
                    if 标识==状态['currentValue']:
                        自身.渲染()
                        return
                    if 标识==完全权限预设:
                        自身.已认=False
                        自身.确认完全=True
                        自身.渲染()
                        return
                    属性['select'](标识)
                菜单对象=菜单({
                    'window':窗口,
                    'open':自身.打开,
                    'onClose':关掉,
                    'items':条目表,
                    'selectedId':状态['currentValue'],
                    'onSelect':选择,
                    'align':'end',
                    'portal':True,
                    'anchor':钮,
                })
                行.appendChild(菜单对象.渲染())
                自身.菜单=菜单对象
                壳.appendChild(行)
                def 改认(值):
                    '勾选完全权限的风险确认'
                    自身.已认=值 is True
                    自身.渲染()
                def 关确认():
                    '取消完全权限确认'
                    自身.已认=False
                    自身.确认完全=False
                    自身.渲染()
                def 执行确认():
                    '确认后写入完全权限。对话框先关上，写入失败也不把它留在画面上'
                    自身.已认=False
                    自身.确认完全=False
                    try:
                        属性['select'](完全权限预设)
                    finally:
                        自身.渲染()
                确认节点=风险确认({
                    'window':窗口,
                    'open':自身.确认完全,
                    'title':中文['confirm.title'],
                    'description':中文['confirm.description'],
                    'acknowledgeLabel':中文['confirm.acknowledge'],
                    'cancelLabel':中文['confirm.cancel'],
                    'closeLabel':访问中文['close'],
                    'confirmLabel':中文['confirm.enable'],
                    'acknowledged':自身.已认,
                    'disabled':状态['writable'] is not True or 状态['status']=='saving',
                    'onAcknowledgedChange':改认,
                    'onCancel':关确认,
                    'onConfirm':执行确认,
                }).渲染()
                if 确认节点 is not None:
                    壳.appendChild(确认节点)
            自身.根=壳
            if 旧 is not None and 旧.parentNode is not None:
                旧.parentNode.replaceChild(壳,旧)
            if 自身.已订 is not True:
                自身.已订=True
                def 变更(*位置参数):
                    '设置快照变了就重画。节点不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        if 自身.已订:
                            自身.已订=False
                            for 拆 in 自身.退订表:
                                拆()
                            自身.退订表=[]
                        return
                    自身.渲染()
                钩=属性['usePermission']
                订=getattr(钩,'_subscribe',None)
                if callable(订):
                    自身.退订表.append(订(变更))
            if 自身.已请求加载 is not True:
                自身.已请求加载=True
                属性['load']()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
