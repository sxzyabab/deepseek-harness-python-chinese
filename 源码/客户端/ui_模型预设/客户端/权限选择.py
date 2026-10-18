import os
from ...ui_基础界面组件.icons import 图标下箭头描边常规
from ...ui_基础界面组件.权限图标 import (
    权限只读常规,
    权限工作区写常规,
    权限完全访问常规,
    权限自动审阅常规,
)
from ...ui_基础界面组件.菜单 import 菜单
from ...ui_基础界面组件.风险确认 import 风险确认
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .文案 import 访问中文
from .呈现 import 完全权限预设,自动审查预设,展示权限预设

__all__=['权限选择']

样式模块='permission-select'

权限字形表={
    'read-only':权限只读常规,
    'workspace-write':权限工作区写常规,
    完全权限预设:权限完全访问常规,
    自动审查预设:权限自动审阅常规,
}

def 访问文案(键):
    '当前会话权限中文表。显示不走英文表'
    return 访问中文[键]

def 权限字形(值,窗口):
    '设计集内的权限图标。集外的宿主预设没有图标'
    造=权限字形表[值] if 值 in 权限字形表 else None
    if 造 is None:
        return None
    return 造({'window':窗口})

def 权限标签(值,名称):
    '自动审查用中文表，其余内置预设走产品标签'
    if 值==自动审查预设:
        return 访问中文['auto.label']
    return 展示权限预设(值,名称,访问文案)

def 元素(文档,标签,类名):
    '造一个挂了权限选择样式模块的节点'
    节点=文档.createElement(标签)
    节点.className=类名
    return 标样式模块(节点,样式模块)

class 权限选择:
    '撰写器上的当前会话权限选择。没有投影或目录时不占画面'
    def __new__(类,属性):
        '槽位把组件当函数调用，返回这一块的节点'
        自身=object.__new__(类)
        自身.属性=属性
        自身.挑选=None
        自身.打开=False
        自身.确认=None
        自身.已认=False
        自身.根=None
        自身.菜单=None
        自身.已订=False
        自身.退订表=[]
        自身.绘制中=False
        自身.待重画=False
        return 自身.渲染()

    def 提交(自身,标识):
        '记下正在提交的项。命令返回或失败后清掉，失败不往外抛'
        自身.挑选=标识
        自身.渲染()
        try:
            自身.属性['select'](标识)
        except Exception as 提交错误:
            '切换失败不往外抛，下面退出提交中'
            提交错误=提交错误
        自身.挑选=None
        自身.渲染()

    def 渲染(自身):
        '按当前投影、目录和确认态画出触发器。快照变了换掉旧节点'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(文档,'权限选择样式',os.path.join(os.path.dirname(__file__),'权限选择.module.css'),样式模块)
            def 取目录值(状态):
                '目录快照里的完整目录'
                return 状态['value']
            目录值=属性['usePermissionCatalog'](取目录值)
            选取=属性['useProjection']('permissions')
            锁定=属性['locked'] if 'locked' in 属性 else None
            确认还在=False
            if 自身.确认 is not None and 目录值 is not None:
                for 项 in 目录值['options']:
                    if 项['value']==自身.确认:
                        确认还在=True
                        break
            保持=锁定 is not True and 选取 is not None and 目录值 is not None and (自身.确认 is None or 确认还在 is True)
            if 保持 is not True:
                自身.打开=False
                自身.已认=False
                自身.确认=None
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
            if 选取 is not None and 目录值 is not None:
                忙=自身.挑选 is not None or 自身.确认 is not None
                当前值=选取['currentValue']
                if 自身.挑选 is not None:
                    挑中=False
                    for 项 in 目录值['options']:
                        if 项['value']==自身.挑选:
                            挑中=True
                            break
                    if 挑中:
                        当前值=自身.挑选
                当前=None
                for 项 in 目录值['options']:
                    if 项['value']==当前值:
                        当前=项
                        break
                if 当前 is None:
                    当前标签=权限标签(当前值,当前值)
                    说明=None
                else:
                    当前标签=权限标签(当前['value'],当前['name'])
                    if 当前['value']==自动审查预设:
                        说明=访问中文['auto.description']
                    elif 'description' in 当前 and 当前['description'] is not None:
                        说明=当前['description']
                    else:
                        说明=None
                条目表=[]
                for 项 in 目录值['options']:
                    标签=权限标签(项['value'],项['name'])
                    if 项['value']==自动审查预设:
                        显示=标签+' '+访问中文['auto.badge']
                    else:
                        显示=标签
                    条目={'id':项['value'],'label':显示}
                    图标=权限字形(项['value'],窗口)
                    if 图标 is not None:
                        条目['icon']=图标
                    条目表.append(条目)
                钮=元素(文档,'button','trigger')
                钮.type='button'
                钮.setAttribute('aria-label','访问模式，当前：'+当前标签)
                if 说明 is not None:
                    钮.title=说明
                钮.disabled=锁定 is True or 忙 is True
                def 点触发(事件=None):
                    '打开或关上菜单'
                    自身.打开=自身.打开 is not True
                    自身.渲染()
                钮.addEventListener('click',点触发)
                字形=权限字形(当前值,窗口)
                if 字形 is not None:
                    图标盒=元素(文档,'span','triggerIcon')
                    图标盒.setAttribute('aria-hidden','true')
                    图标盒.appendChild(字形)
                    钮.appendChild(图标盒)
                字=元素(文档,'span','triggerLabel')
                字.textContent=当前标签
                钮.appendChild(字)
                箭头类='chevron'
                if 自身.打开:
                    箭头类=箭头类+' chevronOpen'
                箭头盒=元素(文档,'span',箭头类)
                箭头盒.setAttribute('aria-hidden','true')
                箭头盒.appendChild(图标下箭头描边常规({'window':窗口}))
                钮.appendChild(箭头盒)
                def 关掉():
                    '菜单要求关上'
                    自身.打开=False
                    自身.渲染()
                def 选择(标识):
                    '点一项。还是当前值就只关上。完全权限和自动审查先确认'
                    自身.打开=False
                    if 标识==选取['currentValue']:
                        自身.渲染()
                        return
                    if 标识==完全权限预设 or 标识==自动审查预设:
                        自身.已认=False
                        自身.确认=标识
                        自身.渲染()
                        return
                    自身.提交(标识)
                菜单对象=菜单({
                    'window':窗口,
                    'open':自身.打开,
                    'items':条目表,
                    'selectedId':当前值,
                    'onSelect':选择,
                    'onClose':关掉,
                    'side':'top',
                    'portal':True,
                    'anchor':钮,
                })
                壳.appendChild(菜单对象.渲染())
                自身.菜单=菜单对象
                if 自身.确认 is not None:
                    自动=自身.确认==自动审查预设
                    if 自动:
                        标题=访问中文['auto.confirm.title']
                        确认说明=访问中文['auto.confirm.description']
                        已知=访问中文['auto.confirm.acknowledge']
                        启用=访问中文['auto.confirm.enable']
                    else:
                        标题=访问中文['confirm.title']
                        确认说明=访问中文['confirm.description']
                        已知=访问中文['confirm.acknowledge']
                        启用=访问中文['confirm.enable']
                    def 改认(值):
                        '勾选风险确认'
                        自身.已认=值 is True
                        自身.渲染()
                    def 关确认():
                        '取消风险确认'
                        自身.已认=False
                        自身.确认=None
                        自身.渲染()
                    def 执行确认():
                        '确认后提交这一项'
                        标识=自身.确认
                        自身.已认=False
                        自身.确认=None
                        自身.提交(标识)
                    确认节点=风险确认({
                        'window':窗口,
                        'open':True,
                        'title':标题,
                        'description':确认说明,
                        'acknowledgeLabel':已知,
                        'cancelLabel':访问中文['confirm.cancel'],
                        'closeLabel':访问中文['close'],
                        'confirmLabel':启用,
                        'acknowledged':自身.已认,
                        'disabled':锁定 is True,
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
                    '目录或投影变了就重画。节点不在页面上就退订'
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
                for 名 in ('usePermissionCatalog','useProjection'):
                    钩=属性[名] if 名 in 属性 else None
                    订=getattr(钩,'_subscribe',None)
                    if callable(订):
                        自身.退订表.append(订(变更))
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
