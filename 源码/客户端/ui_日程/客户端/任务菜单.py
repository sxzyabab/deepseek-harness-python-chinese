'任务页自己的下拉菜单。时区搜索框靠 data-menu-field 接手键盘'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.锚定位置 import 使用锚定位置
from ...ui_基础界面组件.点外关闭 import 点外关闭
from ...ui_基础界面组件.icons import 图标勾描边常规

__all__=['任务菜单']

样式模块='task-menu'

def 确保样式(文档):
    '任务菜单样式只插一次'
    注入模块样式文件(文档,'日程任务菜单样式',os.path.join(os.path.dirname(__file__),'任务菜单.module.css'),样式模块)

def 是分隔(项):
    '分组线'
    return isinstance(项,dict) and 项.get('type')=='separator'

def 是标题(项):
    '不可点的小标题'
    return isinstance(项,dict) and 项.get('type')=='label'

class 任务菜单:
    '锚点旁边的菜单。传送到 body 时固定定位'
    def __init__(自身,属性):
        '先只留锚'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.列表=None
        自身.拆位置=None
        自身.拆外面=None
        自身.拆键=None
        自身.已开=False

    def 渲染(自身,属性=None):
        '打开时挂列表，关掉时拆掉'
        if 属性 is not None:
            自身.属性=属性
        属性=自身.属性
        窗口=属性.get('window') or 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if 自身.根 is None:
            根=文档.createElement('span')
            根.className='root'
            标样式模块(根,样式模块)
            额外=属性.get('className')
            if isinstance(额外,str) and 额外!='':
                根.className='root '+额外
            自身.根=根
        锚=属性.get('anchor')
        if 锚 is not None and 锚.parentNode is not 自身.根:
            自身.根.appendChild(锚)
        打开=属性.get('open') is True
        if not 打开:
            自身.拆开()
            自身.已开=False
            return 自身.根
        if 自身.列表 is None:
            自身.挂列表(文档,窗口)
        自身.填行(文档,窗口)
        自身.已开=True
        return 自身.根

    def 拆开(自身):
        '卸掉列表、定位和键盘'
        if callable(自身.拆位置):
            自身.拆位置()
            自身.拆位置=None
        if callable(自身.拆外面):
            自身.拆外面()
            自身.拆外面=None
        if callable(自身.拆键):
            自身.拆键()
            自身.拆键=None
        if 自身.列表 is not None and 自身.列表.parentNode is not None:
            自身.列表.parentNode.removeChild(自身.列表)
        自身.列表=None

    def 挂列表(自身,文档,窗口):
        '传送时挂到 body'
        属性=自身.属性
        列表=文档.createElement('div')
        类名='list scrollable'
        if 属性.get('portal') is True:
            类名=类名+' portal'
        if 属性.get('align')=='end' and 属性.get('portal') is not True:
            类名=类名+' alignEnd'
        额外=属性.get('listClassName')
        if isinstance(额外,str) and 额外!='':
            类名=类名+' '+额外
        列表.className=类名
        标样式模块(列表,样式模块)
        列表.setAttribute('role','menu')
        if 属性.get('portal') is True:
            列表.style.visibility='hidden'
            列表.style.left='0px'
            列表.style.top='0px'
            文档.body.appendChild(列表)
            自身.拆位置=使用锚定位置({
                'open':True,'anchor':自身.根,'panel':列表,'window':窗口,
                'align':属性.get('align') or 'start','gap':4,'margin':12,
            })
        else:
            自身.根.appendChild(列表)
        def 置关(打开):
            '点外面关掉'
            if 打开 is False and callable(属性.get('onClose')):
                属性['onClose']()
        自身.拆外面=点外关闭(自身.根,True,置关,列表)
        def 按键(事件):
            'Escape 关掉。上下在可用行之间走'
            if 事件.key=='Escape':
                if callable(属性.get('onClose')):
                    属性['onClose']()
                钮=自身.根.querySelector('button:not(:disabled)')
                if 钮 is not None:
                    钮.focus()
                return
            if 事件.key not in ('ArrowDown','ArrowUp','Home','End'):
                return
            按钮=列表.querySelectorAll('button:not(:disabled)')
            if 按钮 is None or len(按钮)==0:
                return
            事件.preventDefault()
            当前=文档.activeElement
            序=0
            找到=-1
            for 钮 in 按钮:
                if 钮 is 当前:
                    找到=序
                序=序+1
            if 事件.key=='Home':
                下一=0
            elif 事件.key=='End':
                下一=len(按钮)-1
            elif 找到<0:
                下一=0 if 事件.key=='ArrowDown' else len(按钮)-1
            else:
                步=1 if 事件.key=='ArrowDown' else -1
                下一=(找到+步)%len(按钮)
            按钮[下一].focus()
        文档.addEventListener('keydown',按键)
        def 拆键():
            '卸掉这次的键盘'
            文档.removeEventListener('keydown',按键)
        自身.拆键=拆键
        自身.列表=列表

    def 填行(自身,文档,窗口):
        '按条目重画行'
        列表=自身.列表
        while 列表.firstChild is not None:
            列表.removeChild(列表.firstChild)
        头=自身.属性.get('header')
        if 头 is not None:
            盒=文档.createElement('div')
            盒.className='header'
            标样式模块(盒,样式模块)
            盒.setAttribute('role','presentation')
            if hasattr(头,'tagName'):
                盒.appendChild(头)
            列表.appendChild(盒)
            字段=盒.querySelector('[data-menu-field]')
            if 字段 is not None:
                字段.focus()
        视口=文档.createElement('div')
        视口.className='viewport'
        标样式模块(视口,样式模块)
        视口.setAttribute('role','presentation')
        选中=自身.属性.get('selectedId')
        for 项 in 自身.属性.get('items') or []:
            if 是分隔(项):
                线=文档.createElement('div')
                线.className='separator'
                标样式模块(线,样式模块)
                线.setAttribute('role','separator')
                视口.appendChild(线)
                continue
            if 是标题(项):
                题=文档.createElement('div')
                题.className='label'
                标样式模块(题,样式模块)
                题.setAttribute('role','presentation')
                题.textContent=项.get('text') or ''
                视口.appendChild(题)
                continue
            包=文档.createElement('div')
            包.className='itemWrap'
            标样式模块(包,样式模块)
            钮=文档.createElement('button')
            钮.type='button'
            钮.setAttribute('role','menuitem')
            类名='item'
            if 项.get('id')==选中:
                类名=类名+' selected'
            if 项.get('danger') is True:
                类名=类名+' danger'
            钮.className=类名
            标样式模块(钮,样式模块)
            钮.disabled=项.get('disabled') is True
            if 项.get('icon') is not None and hasattr(项.get('icon'),'tagName'):
                图标盒=文档.createElement('span')
                图标盒.className='itemIcon'
                标样式模块(图标盒,样式模块)
                图标盒.appendChild(项['icon'])
                钮.appendChild(图标盒)
            字=文档.createElement('span')
            字.className='itemLabel'
            标样式模块(字,样式模块)
            标签=项.get('label')
            字.textContent='' if 标签 is None else str(标签)
            钮.appendChild(字)
            if 项.get('id')==选中:
                勾=图标勾描边常规({'window':窗口,'className':'check'})
                if 勾 is not None:
                    钮.appendChild(勾)
            def 点(事件,标识=项.get('id')):
                '选中这一行'
                事件.stopPropagation()
                if callable(自身.属性.get('onSelect')):
                    自身.属性['onSelect'](标识)
            钮.addEventListener('click',点)
            包.appendChild(钮)
            视口.appendChild(包)
        列表.appendChild(视口)

    def __call__(自身,属性=None):
        '再画'
        return 自身.渲染(属性)
