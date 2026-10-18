'可搜索、可编辑的快捷键速查，以及通用设置里的入口'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标关闭描边常规
from ...ui_基础界面组件.快捷键 import 快捷键
from ...ui_基础界面组件.按名排序 import 按名排序
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.吐司 import 吐司
from ...ui_基础界面组件.模态层 import 使用模态层,是否在模态后
from ...ui_基础界面组件.焦点 import 无轮廓聚焦
from .反馈 import 快捷键失败,快捷键读取失败
from .图标 import 快捷键图标
from .编辑器 import 快捷键编辑器,确保样式

__all__=['快捷键设置行','快捷键速查']

样式模块='shortcuts-reference'
模态模块='modal'
图形命名空间='http://www.w3.org/2000/svg'
模态样式路径=os.path.join(os.path.dirname(__file__),'..','..','ui_基础界面组件','模态.module.css')
核心动作顺序={
    'shortcuts.open':0,
    'session.new':1,
    'sidebar.left.toggle':2,
    'session.search':3,
    'workspace.add':4,
    'session.rename':5,
    'session.fork':6,
    'session.archive':7,
    'settings.open':8,
    'fontSize.increase':9,
    'fontSize.decrease':10,
    'workspace.openLocal':11,
    'sidebar.right.toggle':12,
    'workspace.files':13,
    'browser.new':14,
    'terminal.new':15,
    'pane.split':16,
    'pane.fullscreen.toggle':17,
    'page.refresh':18,
    'page.close':19,
}
组名={
    'application':'应用操作',
    'input':'消息输入',
    'menus':'菜单与弹层',
    'approval':'审批区域',
}
搜索路径=(
    'M10.28 5.86536C10.28 3.41381 8.29245 1.42644 5.84094 1.42627C3.38929 1.42627 1.40186 3.4137 1.40186 5.86536C1.40203 8.31686 3.38939 10.3044 5.84094 10.3044C8.29234 10.3043 10.2799 8.31676 10.28 5.86536ZM11.4174 5.86536C11.4172 8.94498 8.92057 11.4416 5.84094 11.4418C2.76117 11.4418 0.263843 8.94509 0.263672 5.86536C0.263672 2.78548 2.76106 0.288086 5.84094 0.288086C8.92067 0.288258 11.4174 2.78559 11.4174 5.86536Z',
    'M13.7372 12.9078L12.9323 13.7127L9.9732 10.7536L10.7781 9.94867L13.7372 12.9078Z',
)
刷新路径=(
    'M14.5001 8C14.5 9.28552 14.1188 10.5422 13.4045 11.611C12.6903 12.6799 11.6752 13.5129 10.4875 14.0049C9.29982 14.4968 7.99295 14.6255 6.73212 14.3747C5.4713 14.124 4.31314 13.505 3.4041 12.596C2.49514 11.687 1.87614 10.5288 1.62537 9.26798C1.37459 8.00716 1.50331 6.70028 1.99525 5.51261C2.48719 4.32494 3.32025 3.30981 4.3891 2.59557C5.45795 1.88134 6.71458 1.50008 8.0001 1.5C9.9001 1.5 11.7001 2.3 13.0001 3.6L14.5001 5.1',
    'M14.4999 1.5V5.1H10.8999',
)

def 原样(值):
    '钩子选择器原样返回快照'
    return 值

def 取窗(属性):
    '有传入窗口就用它，否则用当前页'
    if 'window' in 属性:
        return 属性['window']
    return 取握手窗口()

def 订上(属性,名字列,回调):
    '给还在的钩子登记重画'
    退=[]
    for 名 in 名字列:
        if 名 not in 属性:
            continue
        钩=属性[名]
        if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
            退.append(钩._subscribe(回调))
    return 退

def 建(文档,标签,类名=None):
    '造一个挂了参考样式的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    标样式模块(节点,样式模块)
    return 节点

def 模态节点(文档,标签,类名):
    '造一个挂了模态样式的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    标样式模块(节点,模态模块)
    return 节点

def 清空子(节点):
    '拆掉全部子节点'
    while 节点.firstChild is not None:
        节点.removeChild(节点.firstChild)

def 画矢量(文档,路径列,类名,宽,高,视图,描边):
    '画出不进辅助技术的矢量'
    图=文档.createElementNS(图形命名空间,'svg')
    图.setAttribute('width',str(宽))
    图.setAttribute('height',str(高))
    图.setAttribute('viewBox',视图)
    图.setAttribute('fill','none')
    图.setAttribute('aria-hidden','true')
    if 描边:
        图.setAttribute('stroke-width','1')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    标样式模块(图,样式模块)
    for 数据 in 路径列:
        划=文档.createElementNS(图形命名空间,'path')
        划.setAttribute('d',数据)
        if 描边:
            划.setAttribute('stroke','currentColor')
        else:
            划.setAttribute('fill','currentColor')
        图.appendChild(划)
    return 图

def 键帽(文档,窗口,键列,类名):
    '外层用参考样式做键帽，内层用共享快捷键'
    外=建(文档,'span',类名)
    外.style.display='inline-flex'
    外.style.alignItems='center'
    内=快捷键({'window':窗口,'keys':键列}).渲染()
    if 内 is not None:
        内.style.color='inherit'
        外.appendChild(内)
    return 外

def 画对话框(文档,窗口,选项):
    '画出罩层和卡片。无头时子节点直接放进卡片'
    注入模块样式文件(文档,'快捷键模态样式',模态样式路径,模态模块)
    根=模态节点(文档,'div','root')
    根.setAttribute('role','presentation')
    罩=模态节点(文档,'div','mask')
    罩.setAttribute('aria-hidden','true')
    def 点罩(事件):
        '点遮罩走关闭'
        选项['onClose']()
    罩.addEventListener('click',点罩)
    根.appendChild(罩)
    无头=选项['headless'] is True
    if 无头:
        卡片=建(文档,'div','dialog')
        卡片.style.position='relative'
        卡片.style.zIndex='1'
        卡片.style.display='flex'
        卡片.style.flexDirection='column'
        卡片.style.overflow='hidden'
        卡片.style.border='0'
        卡片.style.background='var(--dsw-alias-bg-layer-2)'
    else:
        卡片=模态节点(文档,'div','dialog')
    卡片.tabIndex=-1
    卡片.setAttribute('role','dialog')
    卡片.setAttribute('aria-modal','true')
    卡片.setAttribute('aria-label',选项['title'])
    if 'shortcutModal' in 选项 and 选项['shortcutModal'] is not None:
        卡片.setAttribute('data-shortcut-modal',选项['shortcutModal'])
    if 无头:
        子=选项['children'] if 'children' in 选项 else None
        if 子 is not None:
            卡片.appendChild(子)
    else:
        内容=模态节点(文档,'div','content')
        头=模态节点(文档,'div','header')
        题=模态节点(文档,'h2','title')
        题.textContent=选项['title']
        头.appendChild(题)
        关=模态节点(文档,'button','close')
        关.type='button'
        关.setAttribute('aria-label',选项['closeLabel'])
        关.appendChild(图标关闭描边常规({'window':窗口,'size':14}))
        def 点关(事件):
            '点关闭'
            选项['onClose']()
        关.addEventListener('click',点关)
        头.appendChild(关)
        内容.appendChild(头)
        说明=选项['description'] if 'description' in 选项 else None
        if isinstance(说明,str) and 说明!='':
            述=模态节点(文档,'p','description')
            述.textContent=说明
            内容.appendChild(述)
        子=选项['children'] if 'children' in 选项 else None
        if 子 is not None:
            体=模态节点(文档,'div','body')
            体.appendChild(子)
            内容.appendChild(体)
        卡片.appendChild(内容)
        脚=选项['footer'] if 'footer' in 选项 else None
        if 脚 is not None:
            卡片.appendChild(脚)
    根.appendChild(卡片)
    return 根,卡片

class 快捷键设置行:
    '通用设置里打开速查的那一行'
    def __init__(自身,属性):
        '记下渲染器交来的属性并画出这一行'
        自身.属性=属性
        自身.根=None
        自身.提示=None
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.已拆=False
        自身.曾挂上=False
        自身.窗口=取窗(属性)
        自身.退订=订上(属性,['useCatalog'],自身.变更)
        自身.渲染()

    def 变更(自身):
        '目录变了就重画。行已经不在页面上就拆掉'
        if 自身.已拆:
            return
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 拆除(自身):
        '退订并卸掉提示'
        if 自身.已拆:
            return
        自身.已拆=True
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        if 自身.提示 is not None and 自身.提示.卸 is not None:
            自身.提示.卸()
            自身.提示=None

    def 渲染(自身):
        '标题、说明，以及打开速查的按钮'
        if 自身.已拆:
            return 自身.根
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=自身.窗口
            文档=窗口.document
            确保样式(文档)
            if 自身.根 is not None and 自身.根.parentNode is not None:
                自身.曾挂上=True
            elif 自身.曾挂上:
                自身.拆除()
                return 自身.根
            def 找打开(行表):
                '找出打开速查的命令'
                for 行 in 行表:
                    if 行['id']=='shortcuts.open':
                        return 行
                return None
            快捷=属性['useCatalog'](找打开)
            if 自身.提示 is not None and 自身.提示.卸 is not None:
                自身.提示.卸()
                自身.提示=None
            父=None
            if 自身.根 is not None:
                父=自身.根.parentNode
                自身.根.remove()
            行=建(文档,'div','setting')
            文=建(文档,'div','settingText')
            题=建(文档,'div','settingTitle')
            题.textContent='快捷键'
            述=建(文档,'p','settingDescription')
            述.textContent='查看和编辑当前可用的快捷键和输入操作'
            文.appendChild(题)
            文.appendChild(述)
            行.appendChild(文)
            钮=建(文档,'button','button')
            钮.type='button'
            钮.setAttribute('aria-label','编辑快捷键')
            钮.textContent='编辑快捷键'
            if 快捷 is not None and 快捷['aria'] is not None:
                钮.setAttribute('aria-keyshortcuts',快捷['aria'])
            def 点开(事件):
                '打开速查'
                属性['actions']['open']()
            钮.addEventListener('click',点开)
            有键=快捷 is not None and len(快捷['keys'])>0
            自身.提示=提示泡({
                'window':窗口,
                'label':'全局唤起查看',
                'shortcutKeys':快捷['keys'] if 有键 else [],
                'disabled':not 有键,
                'children':钮,
            })
            锚=自身.提示.渲染()
            行.appendChild(锚)
            自身.根=行
            if 父 is not None:
                父.appendChild(行)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

class 快捷键速查:
    '打开时显示唯一的速查对话框。核心动作按产品顺序，其余按 id'
    def __init__(自身,属性):
        '记下属性、对话框状态，并订上目录和配置'
        自身.属性=属性
        自身.根=None
        自身.目标=None
        自身.重置修订=None
        自身.忙=False
        自身.吐司=None
        自身.吐司节点=None
        自身.已画吐司=None
        自身.编辑器=None
        自身.绘制中=False
        自身.待重画=False
        自身.已拆=False
        自身.曾挂上=False
        自身.待聚焦=None
        自身.上次焦点=None
        自身.上次空改=None
        自身.层节点=None
        自身.层拆函数=None
        自身.对话框=None
        自身.搜索框=None
        自身.列表=None
        自身.恢复钮=None
        自身.计数=None
        自身.关闭钮=None
        自身.搜索场=None
        自身.清空钮=None
        自身.确认根=None
        自身.确认拆=None
        自身.取消钮=None
        自身.确认钮=None
        自身.退订=[]
        自身.窗口=取窗(属性)
        自身.退订=订上(属性,['useStore','useCatalog','useConfig','useFixedCatalog'],自身.变更)
        自身.渲染()

    def 变更(自身):
        '存储或目录变了就重画。占位已经不在页面上就拆掉'
        if 自身.已拆:
            return
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 通知(自身,文本,错误=False):
        '吐司。同一句错误不抬序号'
        前=自身.吐司
        if 错误 and 前 is not None and 前['error'] is True and 前['text']==文本:
            return
        序号=0 if 前 is None else 前['seq']
        自身.吐司={'text':文本,'error':错误,'seq':序号+1}
        if not 自身.绘制中 and not 自身.已拆:
            自身.渲染()

    def 消吐司(自身):
        '到时去掉吐司'
        自身.吐司=None
        if 自身.吐司节点 is not None:
            自身.吐司节点.remove()
            自身.吐司节点=None
        自身.已画吐司=None

    def 出错(自身,文本):
        '行内编辑的失败句'
        自身.通知(文本,True)

    def 已保存(自身):
        '保存成功：关掉行内编辑并提示已修改'
        自身.目标=None
        if 自身.编辑器 is not None and not 自身.编辑器.已拆:
            自身.编辑器.拆除()
        自身.编辑器=None
        自身.待聚焦='dialog'
        自身.通知('已修改',False)

    def 关编辑器(自身):
        '退出行内编辑，焦点回到对话框'
        自身.目标=None
        if 自身.编辑器 is not None and not 自身.编辑器.已拆:
            自身.编辑器.拆除()
        自身.编辑器=None
        自身.待聚焦='dialog'
        if not 自身.绘制中 and not 自身.已拆:
            自身.渲染()

    def 关速查(自身):
        '忙着就不动。确认优先于编辑器，再关掉对话框'
        if 自身.忙:
            return
        if 自身.重置修订 is not None:
            自身.重置修订=None
            if not 自身.绘制中:
                自身.渲染()
            return
        if 自身.目标 is not None:
            自身.关编辑器()
            return
        自身.属性['actions']['close']()

    def 关确认(自身):
        '不忙时关掉恢复确认'
        if 自身.忙:
            return
        自身.重置修订=None
        自身.待聚焦='reset'
        if not 自身.绘制中 and not 自身.已拆:
            自身.渲染()

    def 持久化(自身,*位置参数):
        '包一层 edit，记下忙'
        自身.忙=True
        if not 自身.绘制中 and not 自身.已拆:
            自身.渲染()
        结果=自身.属性['edit'](*位置参数)
        if not 自身.已拆:
            自身.忙=False
            if not 自身.绘制中:
                自身.渲染()
        return 结果

    def 全部恢复(自身):
        '确认之后恢复当前平台的全部默认键'
        if 自身.重置修订 is None:
            return
        结果=自身.持久化({'type':'reset-all'},自身.重置修订)
        if 自身.已拆:
            return
        if 结果['status']=='saved' or 结果['status']=='stale':
            自身.重置修订=None
        if 结果['status']=='saved':
            自身.通知('已恢复默认快捷键',False)
        elif 结果['status']=='write-failed':
            自身.通知('恢复默认失败。原快捷键已保留，请重试。',True)
        else:
            目录=自身.属性['useCatalog'](原样)
            自身.通知(快捷键失败(结果,目录,自身.属性['runtime']),True)

    def 输入查询(自身,事件):
        '把输入框里刚读到的查询写进存储'
        自身.属性['actions']['search'](事件.target.value)

    def 点清空(自身,事件):
        '清空查询并回到搜索框'
        自身.待聚焦='search'
        自身.属性['actions']['search']('')

    def 点关闭(自身,事件):
        '关闭按钮'
        自身.关速查()

    def 点恢复全部(自身,事件):
        '先聚焦这个按钮，再打开确认'
        事件.currentTarget.focus()
        自身.目标=None
        if 自身.编辑器 is not None and not 自身.编辑器.已拆:
            自身.编辑器.拆除()
        自身.编辑器=None
        配置=自身.属性['useConfig'](原样)
        自身.重置修订=配置['revision']
        if not 自身.绘制中:
            自身.渲染()

    def 按下指针(自身,事件):
        '点在按钮和输入外面就退出行内编辑'
        if 自身.目标 is None or 自身.忙:
            return
        目标=事件.target
        if not hasattr(目标,'closest'):
            return
        if 目标.closest('button, input, a, [contenteditable="true"], [role="group"]') is not None:
            return
        事件.preventDefault()
        自身.关编辑器()

    def 编辑属性(自身,行):
        '交给行内编辑器的命令和回调'
        属性=自身.属性
        return {
            'target':行,
            'onClose':自身.关编辑器,
            'onSaved':自身.已保存,
            'onError':自身.出错,
            'useCatalog':属性['useCatalog'],
            'useConfig':属性['useConfig'],
            'useFixedCatalog':属性['useFixedCatalog'],
            'platform':属性['platform'],
            'runtime':属性['runtime'],
            'edit':自身.持久化,
            'recording':属性['recording'],
            'describeBinding':属性['describeBinding'],
            'window':自身.窗口,
        }

    def 卸壳(自身):
        '卸掉速查罩层和它的键盘层'
        if 自身.层拆函数 is not None:
            自身.层拆函数()
            自身.层拆函数=None
        if 自身.层节点 is not None:
            自身.层节点.remove()
            自身.层节点=None
        自身.对话框=None
        自身.搜索框=None
        自身.列表=None
        自身.恢复钮=None
        自身.计数=None
        自身.关闭钮=None
        自身.搜索场=None
        自身.清空钮=None

    def 卸确认(自身):
        '卸掉恢复确认和它的键盘层'
        if 自身.确认拆 is not None:
            自身.确认拆()
            自身.确认拆=None
        if 自身.确认根 is not None:
            自身.确认根.remove()
            自身.确认根=None
        自身.取消钮=None
        自身.确认钮=None

    def 拆除(自身):
        '退订、卸编辑器、卸两个对话框和吐司'
        if 自身.已拆:
            return
        自身.已拆=True
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        if 自身.编辑器 is not None and not 自身.编辑器.已拆:
            自身.编辑器.拆除()
        自身.编辑器=None
        自身.卸确认()
        自身.卸壳()
        if 自身.吐司节点 is not None:
            自身.吐司节点.remove()
            自身.吐司节点=None

    def 装壳(自身,文档):
        '第一次打开时画出罩层、搜索和页脚。之后只改里面的列表'
        窗口=自身.窗口
        内容=建(文档,'div','contents')
        内容.addEventListener('pointerdown',自身.按下指针,True)
        头=建(文档,'header','header')
        题=建(文档,'h2','title')
        题.textContent='快捷键'
        头.appendChild(题)
        关=建(文档,'button','close')
        关.type='button'
        关.setAttribute('aria-label','关闭快捷键')
        关.appendChild(图标关闭描边常规({'window':窗口,'size':14}))
        关.addEventListener('click',自身.点关闭)
        头.appendChild(关)
        内容.appendChild(头)
        搜索行=建(文档,'div','searchRow')
        场=建(文档,'div','searchField')
        场.setAttribute('role','search')
        场.setAttribute('aria-label','搜索快捷键')
        场.appendChild(画矢量(文档,搜索路径,'searchIcon',14,14,'0 0 14 14',False))
        输入=建(文档,'input','search')
        输入.type='search'
        输入.setAttribute('aria-label','搜索快捷键')
        输入.setAttribute('placeholder','搜索快捷键')
        输入.setAttribute('data-modal-autofocus','')
        输入.addEventListener('input',自身.输入查询)
        场.appendChild(输入)
        搜索行.appendChild(场)
        内容.appendChild(搜索行)
        列表=建(文档,'div','list')
        内容.appendChild(列表)
        页脚=建(文档,'footer','footer')
        恢复=建(文档,'button','resetAll')
        恢复.type='button'
        恢复.appendChild(画矢量(文档,刷新路径,None,12,12,'0 0 16 16',True))
        恢复.appendChild(文档.createTextNode('恢复全部默认'))
        恢复.addEventListener('click',自身.点恢复全部)
        页脚.appendChild(恢复)
        计数=建(文档,'span','modifiedCount')
        页脚.appendChild(计数)
        内容.appendChild(页脚)
        层,对话框=画对话框(文档,窗口,{
            'title':'快捷键',
            'headless':True,
            'shortcutModal':'shortcuts',
            'onClose':自身.关速查,
            'children':内容,
        })
        文档.body.appendChild(层)
        自身.层节点=层
        自身.对话框=对话框
        自身.搜索框=输入
        自身.列表=列表
        自身.恢复钮=恢复
        自身.计数=计数
        自身.关闭钮=关
        自身.搜索场=场
        自身.清空钮=None
        自身.层拆函数=使用模态层(对话框,True,自身.关速查)

    def 填列表(自身,文档,状态,目录,配置,固定目录,已改):
        '按组和搜索结果重画命令行'
        窗口=自身.窗口
        清空子(自身.列表)
        自身.列表.setAttribute('aria-busy','true' if 配置['status']=='loading' else 'false')
        条目=[]
        for 行 in 目录:
            键面=[]
            for 键 in 行['keys']:
                if 键!='+':
                    键面.append(键)
            无障碍='' if 行['aria'] is None else 行['aria']
            名字=list(行['aliases'])
            名字.append('+'.join(键面))
            名字.append(''.join(键面))
            名字.append(无障碍)
            名字.append(无障碍.replace('Meta','Cmd'))
            拷贝=dict(行)
            拷贝['names']=名字
            拷贝['group']='application'
            条目.append(拷贝)
        for 行 in 固定目录:
            拷贝=dict(行)
            拷贝['names']=[行['id'],' '.join(行['keys'])]
            条目.append(拷贝)
        def 排序键(行):
            '停止放最后，然后核心顺序，再按 id'
            停止=1 if 行['id']=='response.stop' else 0
            if 行['id'] in 核心动作顺序:
                序=核心动作顺序[行['id']]
            else:
                序=len(核心动作顺序)
            return (停止,序,行['id'])
        条目.sort(key=排序键)
        扁平=[]
        for 行 in 条目:
            for 名 in 行['names']:
                扁平.append({'name':名,'label':行['label'],'row':行})
        排序=按名排序(扁平,状态['query'].strip())
        匹配=[]
        见过=set()
        for 项 in 排序:
            行=项['row']
            if 行['id'] in 见过:
                continue
            见过.add(行['id'])
            匹配.append(行)
        录焦=False
        if 自身.编辑器 is not None and not 自身.编辑器.已拆 and 文档.activeElement is 自身.编辑器.录钮:
            录焦=True
        见到=False
        for 组 in ('application','input','menus','approval'):
            行组=[]
            for 行 in 匹配:
                if 行['group']==组:
                    行组.append(行)
            if len(行组)==0:
                continue
            区=建(文档,'section')
            区.setAttribute('aria-label',组名[组])
            if 组!='application':
                题=建(文档,'h3','group')
                题.textContent=组名[组]
                区.appendChild(题)
            表=建(文档,'ul','rows')
            for 行 in 行组:
                项=建(文档,'li','row')
                正在编=自身.目标 is not None and 自身.目标['id']==行['id'] and 'modified' in 行
                if 'modified' in 行 and not 正在编:
                    行钮=建(文档,'button','rowButton')
                    行钮.type='button'
                    行钮.setAttribute('aria-label','修改'+行['label']+'快捷键')
                    行钮.disabled=自身.忙 or 配置['status']!='ready'
                    def 点行(事件,当前=行):
                        '进入这一行的录键'
                        自身.目标=当前
                        if 自身.绘制中:
                            自身.待重画=True
                            return
                        自身.渲染()
                    行钮.addEventListener('click',点行)
                    项.appendChild(行钮)
                标签=建(文档,'span','commandLabel')
                标签.textContent=行['label']
                项.appendChild(标签)
                绑定格=建(文档,'span','binding')
                if 'modified' in 行:
                    if 正在编:
                        见到=True
                        if 自身.编辑器 is None or 自身.编辑器.已拆 or 自身.编辑器.属性['target']['id']!=行['id']:
                            if 自身.编辑器 is not None and not 自身.编辑器.已拆:
                                自身.编辑器.拆除()
                            自身.编辑器=快捷键编辑器(自身.编辑属性(行))
                            自身.编辑器.挂入(绑定格)
                        else:
                            自身.编辑器.属性.update(自身.编辑属性(行))
                            if 录焦:
                                自身.编辑器.按键中=True
                            自身.编辑器.挂入(绑定格)
                            自身.编辑器.按键中=False
                    else:
                        动作=建(文档,'span','rowActions')
                        动作.appendChild(快捷键图标(文档,'edit'))
                        绑定格.appendChild(动作)
                        if len(行['keys'])==0:
                            空=建(文档,'span','unbound')
                            空.textContent='暂无快捷键'
                            绑定格.appendChild(空)
                        else:
                            绑定格.appendChild(键帽(文档,窗口,行['keys'],'keyBadge'))
                else:
                    绑定格.appendChild(键帽(文档,窗口,行['keys'],'fixedKeyBadge'))
                项.appendChild(绑定格)
                表.appendChild(项)
            区.appendChild(表)
            自身.列表.appendChild(区)
        if not 见到 and 自身.编辑器 is not None and not 自身.编辑器.已拆:
            自身.编辑器.拆除()
            自身.编辑器=None
        if len(匹配)==0:
            空提示=建(文档,'p','hint')
            空提示.setAttribute('role','status')
            空提示.textContent='没有匹配的快捷键'
            自身.列表.appendChild(空提示)
        可恢复=not 自身.忙 and 配置['status']=='ready' and 已改>0
        自身.恢复钮.disabled=not 可恢复
        自身.关闭钮.disabled=自身.忙
        if 已改>0:
            自身.计数.textContent=str(已改)+' 项已自定义'
            自身.计数.style.display=''
        else:
            自身.计数.textContent=''
            自身.计数.style.display='none'
        if 自身.清空钮 is not None:
            自身.清空钮.remove()
            自身.清空钮=None
        if 状态['query']!='':
            清=建(文档,'button','clearSearch')
            清.type='button'
            清.setAttribute('aria-label','清空搜索')
            清.appendChild(图标关闭描边常规({'window':窗口,'size':10}))
            清.addEventListener('click',自身.点清空)
            自身.搜索场.appendChild(清)
            自身.清空钮=清
        if 自身.搜索框.value!=状态['query']:
            自身.搜索框.value=状态['query']

    def 装确认(自身,文档):
        '画出恢复全部默认的确认'
        窗口=自身.窗口
        取消=按钮({
            'window':窗口,
            'children':'取消',
            'disabled':自身.忙,
            'onClick':自身.关确认,
        })
        确定=按钮({
            'window':窗口,
            'variant':'primary',
            'children':'恢复默认',
            'disabled':自身.忙 or 自身.属性['useConfig'](原样)['status']!='ready',
            'onClick':自身.全部恢复,
        })
        取消钮=取消.渲染()
        确定钮=确定.渲染()
        取消钮.setAttribute('data-modal-autofocus','')
        脚=模态节点(文档,'div','footer')
        脚.appendChild(取消钮)
        脚.appendChild(确定钮)
        层,对话框=画对话框(文档,窗口,{
            'title':'恢复全部默认快捷键？',
            'headless':False,
            'closeLabel':'关闭确认',
            'description':'将恢复当前平台的默认快捷键。你修改或移除的快捷键都会恢复，其他平台不受影响。',
            'onClose':自身.关确认,
            'footer':脚,
        })
        文档.body.appendChild(层)
        自身.确认根=层
        自身.取消钮=取消钮
        自身.确认钮=确定钮
        if 自身.恢复钮 is not None:
            自身.恢复钮.focus()
        自身.确认拆=使用模态层(对话框,True,自身.关确认)

    def 同步确认(自身,文档,配置):
        '确认开着就更新按钮，关了就卸掉'
        if 自身.重置修订 is None:
            if 自身.确认根 is not None:
                自身.卸确认()
            return
        if 自身.确认根 is None:
            自身.装确认(文档)
            return
        自身.取消钮.disabled=自身.忙
        自身.确认钮.disabled=自身.忙 or 配置['status']!='ready'

    def 画吐司(自身,文档):
        '序号变了才换一条吐司'
        窗口=自身.窗口
        if 自身.吐司 is None:
            if 自身.吐司节点 is not None:
                自身.吐司节点.remove()
                自身.吐司节点=None
                自身.已画吐司=None
            return
        if 自身.吐司['seq']==自身.已画吐司:
            return
        if 自身.吐司节点 is not None:
            自身.吐司节点.remove()
        if 自身.吐司['error']:
            种类='error'
            类名='toastError'
        else:
            种类='success'
            类名='toastSuccess'
        图=快捷键图标(文档,种类,类名)
        标样式模块(图,样式模块)
        条=吐司({'window':窗口,'text':自身.吐司['text'],'icon':图,'onDone':自身.消吐司})
        自身.吐司节点=条.渲染()
        自身.已画吐司=自身.吐司['seq']

    def 渲染(自身):
        '打开时维护速查壳，并按最新目录重画列表'
        if 自身.已拆:
            return 自身.根
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=自身.窗口
            文档=窗口.document
            确保样式(文档)
            状态=属性['useStore'](原样)
            目录=属性['useCatalog'](原样)
            配置=属性['useConfig'](原样)
            固定目录=属性['useFixedCatalog'](原样)
            if not 状态['open']:
                自身.重置修订=None
            if 状态['open'] and 配置['status']=='unreadable':
                自身.通知(快捷键读取失败(配置,属性['runtime']),True)
            if 自身.根 is None:
                自身.根=文档.createElement('span')
                自身.根.style.display='contents'
            if 自身.根.parentNode is not None:
                自身.曾挂上=True
            elif 自身.曾挂上:
                自身.拆除()
                return 自身.根
            档案=配置['document']['profiles']
            键名=属性['runtime']+':'+属性['platform']
            if 键名 in 档案 and 档案[键名] is not None:
                已改=len(档案[键名])
            else:
                已改=0
            if not 状态['open']:
                if 自身.编辑器 is not None and not 自身.编辑器.已拆:
                    自身.编辑器.拆除()
                自身.编辑器=None
                自身.卸确认()
                自身.卸壳()
            else:
                if 自身.层节点 is None:
                    自身.装壳(文档)
                自身.填列表(文档,状态,目录,配置,固定目录,已改)
            自身.同步确认(文档,配置)
            自身.画吐司(文档)
            if 自身.对话框 is not None and 自身.搜索框 is not None:
                请求=状态['focusRequest']
                if 请求!=自身.上次焦点:
                    自身.上次焦点=请求
                    if 状态['open'] and not 是否在模态后(自身.搜索框):
                        无轮廓聚焦(自身.搜索框)
                签名=(状态['open'],自身.重置修订,已改)
                if 签名!=自身.上次空改:
                    自身.上次空改=签名
                    if 状态['open'] and 自身.重置修订 is None and 已改==0 and 文档.activeElement is 文档.body:
                        无轮廓聚焦(自身.搜索框)
                if 自身.待聚焦=='search':
                    无轮廓聚焦(自身.搜索框)
                    自身.待聚焦=None
                elif 自身.待聚焦=='reset' and 自身.恢复钮 is not None:
                    无轮廓聚焦(自身.恢复钮)
                    自身.待聚焦=None
                elif 自身.待聚焦=='dialog':
                    无轮廓聚焦(自身.对话框,{'preventScroll':True})
                    自身.待聚焦=None
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
