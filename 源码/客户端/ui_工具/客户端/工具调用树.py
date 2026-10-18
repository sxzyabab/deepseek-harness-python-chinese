import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .调用模型 import 工具行模型
from .回退工具卡 import 回退工具卡

__all__=['工具调用','工具调用枝','工具调用树']

样式模块='dsh-tool-tree'

def 确保样式(文档):
    '调用树样式只插一次'
    注入模块样式文件(
        文档,
        'dsh-tool-tree',
        os.path.join(os.path.dirname(__file__),'工具调用树.module.css'),
        样式模块,
    )

def 元素(文档,标签,类名):
    '带样式模块的节点'
    节点=文档.createElement(标签)
    节点.className=类名
    标样式模块(节点,样式模块)
    return 节点

def 调用阶段(块):
    '结果、准备中或已开始'
    if 'kind' in 块:
        return {'phase':'result','block':块}
    if 块.get('phase')=='preparing':
        return {'phase':'preparing','block':块}
    return {'phase':'start','block':块}

def 调用名(调用):
    '从当前阶段取线上工具名'
    if 调用['phase']=='result':
        头=调用['block'].get('call')
        if isinstance(头,dict) and isinstance(头.get('name'),str):
            return 头['name']
        return ''
    名称=调用['block'].get('name')
    if isinstance(名称,str):
        return 名称
    return ''

class 工具调用:
    '一次调用。有登记走槽，自动拒绝或没有登记走回退卡'
    def __new__(类,属性):
        '画出这一次调用'
        自身=object.__new__(类)
        自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '槽或回退，子节点跟在后面'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        调用=属性['call']
        调用标识=属性['callId']
        工具名=属性['toolName']
        检视=属性.get('inspectCall')
        def 查看():
            '打开这一次调用的轨迹'
            if 检视 is not None:
                检视(调用标识)
        属主={
            'callId':调用标识,
            'toolName':工具名,
            'phase':调用['phase'],
            'block':调用['block'],
            'openFile':属性.get('openFile'),
            'cwd':属性.get('cwd'),
            'home':属性.get('home'),
            'loadImage':属性.get('loadImage'),
            'useDisclosure':属性['useDisclosure'],
            'window':窗口,
            'inspect':None if 检视 is None else 查看,
        }
        拒绝=False
        if 调用['phase']=='result':
            拒绝=工具行模型(工具名,调用['block'])['autoReviewDenial'] is not None
        根=元素(文档,'div','callRow')
        根.setAttribute('data-chat-anchor-key','call:'+调用标识)
        根.setAttribute('data-chat-call-id',调用标识)
        if 拒绝:
            根.appendChild(回退工具卡(属主))
        else:
            渲染槽=属性['renderSlot']
            回退=回退工具卡(属主)
            画出=渲染槽('tool.call.toolview',属主,{
                'entryKey':工具名,
                'fallback':回退,
            })
            if hasattr(画出,'tagName'):
                根.appendChild(画出)
            elif 画出 is not None:
                根.appendChild(回退)
        子=属性.get('children')
        if hasattr(子,'tagName'):
            根.appendChild(子)
        return 根

class 工具调用枝:
    '一次调用及其子调用'
    def __new__(类,属性):
        '递归画子调用'
        自身=object.__new__(类)
        自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '非准备中且有子调用时缩进画出'
        属性=自身.属性
        调用=调用阶段(属性['block'])
        子节点=None
        if 调用['phase']!='preparing' and len(调用['block'].get('subCalls') or [])>0:
            窗口=属性['window']
            确保样式(窗口.document)
            盒=元素(窗口.document,'div','subCalls')
            盒.setAttribute('data-subcalls','')
            for 子块 in 调用['block']['subCalls']:
                盒.appendChild(工具调用枝({
                    'window':窗口,
                    'renderSlot':属性['renderSlot'],
                    'block':子块,
                    'cwd':属性.get('cwd'),
                    'home':属性.get('home'),
                    'openFile':属性.get('openFile'),
                    'inspectCall':属性.get('inspectCall'),
                    'useDisclosure':属性['useDisclosure'],
                    'loadImage':属性.get('loadImage'),
                }))
            子节点=盒
        return 工具调用({
            'window':属性['window'],
            'renderSlot':属性['renderSlot'],
            'callId':调用['block']['callId'],
            'toolName':调用名(调用),
            'call':调用,
            'openFile':属性.get('openFile'),
            'cwd':属性.get('cwd'),
            'home':属性.get('home'),
            'inspectCall':属性.get('inspectCall'),
            'useDisclosure':属性['useDisclosure'],
            'loadImage':属性.get('loadImage'),
            'children':子节点,
        })

def 取家目录(信息):
    '宿主家目录。选择器交给 useHostInfo'
    if isinstance(信息,dict):
        return 信息.get('home')
    return getattr(信息,'home',None)

class 工具调用树:
    '一根工具调用及其递归子调用'
    def __new__(类,属性):
        '取宿主家目录后交给枝'
        家=None
        if 'useHostInfo' in 属性 and 属性['useHostInfo'] is not None:
            家=属性['useHostInfo'](取家目录)
        节点=属性['node']
        return 工具调用枝({
            'window':属性['window'],
            'renderSlot':属性['renderSlot'],
            'block':节点['data']['root'],
            'cwd':属性.get('cwd'),
            'home':家,
            'openFile':属性.get('openFile'),
            'inspectCall':属性.get('inspectCall'),
            'useDisclosure':属性['useDisclosure'],
            'loadImage':属性.get('loadImage'),
        })
