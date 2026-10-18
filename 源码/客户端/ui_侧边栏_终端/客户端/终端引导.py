from ...模块.客户端.通告 import 取握手窗口
import os
import threading
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.菜单 import 菜单
from .终端图标 import 终端作品

__all__=['终端引导']

样式路径=os.path.join(os.path.dirname(__file__),'终端引导.module.css')
样式模块='TerminalGuide'

class 终端引导:
    '卡片启动记住的壳，菜单另选壳'
    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.尝试=0
        自身.菜单={'phase':'loading'}
        自身.载过=None
        自身.寿命=None
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保加载(自身):
        '菜单打开时读取壳列表。关上或重试会中止上一次'
        if 自身.打开 is not True:
            if 自身.寿命 is not None:
                自身.寿命.set()
                自身.寿命=None
            自身.载过=None
            return
        标记=(自身.尝试,id(自身.属性.get('loadShells')))
        if 自身.载过==标记:
            return
        自身.载过=标记
        if 自身.寿命 is not None:
            自身.寿命.set()
        自身.寿命=threading.Event()
        这次=自身.寿命
        try:
            结果=自身.属性['loadShells'](这次)
        except Exception as 错误:
            if 这次.is_set():
                return
            自身.菜单={'phase':'failed','message':str(错误)}
            return
        if 这次.is_set():
            return
        自身.菜单={'phase':'ready','choices':结果}

    def 渲染(自身):
        '主按钮打开终端，标题旁是壳菜单'
        自身.确保加载()
        属性=自身.属性
        if isinstance(属性,dict) and 属性.get('window') is not None:
            窗=属性['window']
        else:
            窗=取握手窗口()
        文档=窗.document
        注入模块样式文件(文档,'终端引导样式',样式路径,样式模块)
        if 自身.根 is None:
            自身.根=模块节点(文档,'div',样式模块,'entry')
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        标题=属性['title'] if isinstance(属性.get('title'),str) else ''
        说明=属性['description'] if isinstance(属性.get('description'),str) else None
        种类=属性['kind'] if 'kind' in 属性 else ''
        自身.根.setAttribute('data-sidebar-right-guide-entry',str(种类))
        尺寸=22 if 说明 is None else 26
        无障碍=标题 if 说明 is None else 标题+' '+说明

        def 挑快捷(条目表):
            '新建终端这条快捷键'
            for 条 in 条目表:
                if 条['id']=='terminal.new':
                    return 条
            return None

        快捷=属性['useShortcuts'](挑快捷)
        签=属性['useTabInfo']()['tab']

        def 开终端():
            '替换当前页签为终端'
            签['actions']['openTab']('terminal',{'replaceTab':True})

        主=按钮({
            'window':窗,
            'variant':'ghost',
            'className':'main',
            'onClick':开终端,
        }).渲染()
        标样式模块(主,样式模块)
        主.setAttribute('aria-label',无障碍)
        if 快捷 is not None and isinstance(快捷.get('aria'),str) and 快捷['aria']!='':
            主.setAttribute('aria-keyshortcuts',快捷['aria'])
        自身.根.appendChild(主)
        标=模块节点(文档,'span',样式模块,'icon')
        标.setAttribute('aria-hidden','true')
        标.appendChild(终端作品(窗,尺寸,None))
        自身.根.appendChild(标)
        文=模块节点(文档,'span',样式模块,'text')
        题行=模块节点(文档,'span',样式模块,'titleRow')
        题=模块节点(文档,'span',样式模块,'title')
        题.setAttribute('aria-hidden','true')
        题.textContent=标题
        题行.appendChild(题)
        阶段=自身.菜单.get('phase')
        选中=None
        if 阶段=='ready' and isinstance(自身.菜单.get('choices'),dict):
            选择=自身.菜单['choices']
            壳表=选择['shells'] if isinstance(选择.get('shells'),list) else []
            项=[]
            for 壳 in 壳表:
                项.append({'id':壳['path'],'label':壳['name']})
            选中=选择.get('selectedShell')
        elif 阶段=='loading':
            项=[{'id':'loading','label':'正在读取 Shell…','disabled':True}]
        else:
            消息=自身.菜单['message'] if isinstance(自身.菜单.get('message'),str) else ''
            项=[
                {'id':'error','label':'终端错误：'+消息,'disabled':True},
                {'id':'retry','label':'重试'},
            ]
        if len(项)==0:
            项=[{'id':'empty','label':'没有可用的 Shell','disabled':True}]

        def 切换():
            '打开时先回到读取中'
            自身.菜单={'phase':'loading'}
            自身.打开=自身.打开 is not True
            自身.渲染()

        def 关上():
            '关上菜单'
            自身.打开=False
            自身.渲染()

        def 选中路径(路径):
            '失败则重试。否则记住壳并打开终端'
            if 自身.菜单.get('phase')=='failed':
                自身.菜单={'phase':'loading'}
                自身.尝试=自身.尝试+1
                自身.载过=None
                自身.渲染()
                return
            属性['selectShell'](路径)
            自身.打开=False
            签['actions']['openTab']('terminal',{'replaceTab':True,'params':{'shellPath':路径}})
            自身.渲染()

        触发=按钮({
            'window':窗,
            'variant':'ghost',
            'size':'sm',
            'className':'trigger',
            'onClick':切换,
        }).渲染()
        标样式模块(触发,样式模块)
        触发.setAttribute('aria-label','选择 Shell')
        触发.setAttribute('aria-haspopup','menu')
        触发.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        箭头=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        箭头.setAttribute('width','16')
        箭头.setAttribute('height','16')
        箭头.setAttribute('viewBox','0 0 16 16')
        箭头.setAttribute('fill','none')
        箭头.setAttribute('stroke-width','1')
        箭头.setAttribute('aria-hidden','true')
        折=文档.createElementNS('http://www.w3.org/2000/svg','path')
        折.setAttribute('d','M4 6L7.29289 9.29289C7.68342 9.68342 8.31658 9.68342 8.70711 9.29289L12 6')
        折.setAttribute('stroke','currentColor')
        箭头.appendChild(折)
        触发.appendChild(箭头)
        层=菜单({
            'window':窗,
            'open':自身.打开,
            'align':'end',
            'className':'menu',
            'items':项,
            'selectedId':选中,
            'onClose':关上,
            'onSelect':选中路径,
            'anchor':触发,
        }).渲染()
        标样式模块(层,样式模块)
        题行.appendChild(层)
        文.appendChild(题行)
        if 说明 is not None:
            述=模块节点(文档,'span',样式模块,'description')
            述.setAttribute('aria-hidden','true')
            述.textContent=说明
            文.appendChild(述)
        自身.根.appendChild(文)
        if 快捷 is not None and isinstance(快捷.get('keys'),(list,tuple)) and len(快捷['keys'])>0:
            捷=模块节点(文档,'span',样式模块,'shortcut')
            for 键 in 快捷['keys']:
                帽=文档.createElement('kbd')
                帽.setAttribute('class','separator' if 键=='+' else 'key')
                帽.textContent=str(键)
                捷.appendChild(帽)
            自身.根.appendChild(捷)
        父=属性.get('parent')
        if 父 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)
        return 自身

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
