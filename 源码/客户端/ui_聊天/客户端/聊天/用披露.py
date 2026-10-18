import os
from ....ui_对话.异常 import 注入模块样式文件,标样式模块
from ....ui_基础界面组件.icons import 图标,图标上chevron14,图标下箭头描边常规
from ....ui_基础界面组件.文字闪烁 import 文字闪烁

__all__=['用披露','绑定披露','披露席位','注入聊天样式','画披露行','取钩','真属性','挂节点']

披露模块='disclosure-row'


class 披露席位:
    '一份初始折叠的独立披露，无外部订阅'
    def __init__(自身,世代=0):
        '记下重置世代'
        自身.世代=世代
        自身.展开世代=None

    def 是否展开(自身):
        '当前世代是否展开'
        return 自身.展开世代==自身.世代

    def 设展开(自身,打开):
        '显式开合'
        自身.展开世代=自身.世代 if 打开 else None

    def 切换(自身):
        '在开合之间切换'
        自身.展开世代=None if 自身.展开世代==自身.世代 else 自身.世代

    def 快照(自身):
        '给渲染读的开合'
        return {'expanded':自身.是否展开(),'setExpanded':自身.设展开,'toggle':自身.切换}


def 用披露(世代=0):
    '铸造披露席位'
    return 披露席位(世代)


def 读重置世代(重置源):
    '对象走 getSnapshot；外部字典源走同名键'
    if 重置源 is None:
        return 0
    取=getattr(重置源,'getSnapshot',None)
    if callable(取):
        世代=取()
        return 0 if 世代 is None else 世代
    if isinstance(重置源,dict):
        函数=重置源.get('getSnapshot')
        if callable(函数):
            世代=函数()
            return 0 if 世代 is None else 世代
    return 0


def 绑定披露(重置源):
    '到组件调用前不订阅；每次调用读当前重置世代'
    def 用已绑披露():
        '按重置源世代铸造席位'
        return 用披露(读重置世代(重置源))
    return 用已绑披露


def 注入聊天样式(文档,模块,文件名):
    '把同目录的官方模块样式插进文档'
    注入模块样式文件(文档,'ui-chat-'+模块,os.path.join(os.path.dirname(__file__),文件名),模块)


def 注入披露样式(文档):
    '共享披露行的模块样式'
    路径=os.path.normpath(os.path.join(os.path.dirname(__file__),'..','..','..','ui_基础界面组件','披露行.module.css'))
    注入模块样式文件(文档,'ui-chat-disclosure-row',路径,披露模块)


def 取钩(属性,名):
    '钩子可能直接在属性上，也可能在 hooks 里'
    if isinstance(属性,dict) and callable(属性.get(名)):
        return 属性[名]
    钩=属性.get('hooks') if isinstance(属性,dict) else None
    if isinstance(钩,dict) and callable(钩.get(名)):
        return 钩[名]
    return None


def 真属性(节点,名,值):
    '真就写成 true，假和空去掉'
    if 值 is True:
        节点.setAttribute(名,'true')
    elif 值 is False or 值 is None:
        节点.removeAttribute(名)
    else:
        节点.setAttribute(名,str(值))


def 空属性(节点,名,要):
    '要的时候写成空串，不要就拿掉'
    if 要:
        节点.setAttribute(名,'')
    else:
        节点.removeAttribute(名)


def 挂节点(父,节点):
    '节点、组件或一串子节点挂到父上'
    if 节点 is None or 父 is None:
        return
    if isinstance(节点,(list,tuple)):
        for 子 in 节点:
            挂节点(父,子)
        return
    if hasattr(节点,'tagName'):
        父.appendChild(节点)
        return
    if hasattr(节点,'渲染'):
        根=节点.渲染()
        if 根 is not None and hasattr(根,'tagName'):
            父.appendChild(根)


def 画图标(窗口,名):
    '按图标表的名字画出 svg'
    return 图标(名,{'window':窗口})


def 画披露行(文档,属性):
    '上游披露行的头和受控正文。聊天类名和披露类名分属两个样式模块'
    窗口=属性['window']
    注入披露样式(文档)
    打开=属性.get('open') is True
    可展=属性.get('expandable') is True
    行展开=可展 and 属性.get('expandOnRowClick') is True
    预览箭头=属性.get('previewChevron',可展) is not False
    保持=属性.get('keepContentWhenOpen') is True
    根=文档.createElement('div')
    根.className=属性.get('className') or 'root'
    聊天模块=属性.get('样式模块')
    if isinstance(聊天模块,str) and 聊天模块!='':
        标样式模块(根,聊天模块)
    else:
        标样式模块(根,披露模块)
    根.style.cssText='display:flex;flex-direction:column;width:100%;min-width:0'
    真属性(根,'data-open',打开)
    头=文档.createElement('div')
    头.className='header'
    标样式模块(头,披露模块)
    头.setAttribute('data-disclosure-header','')
    if 属性.get('headerAccessory') is not None:
        头.setAttribute('data-has-accessory','true')
    行=文档.createElement('div')
    行类='row'
    if isinstance(属性.get('rowClassName'),str) and 属性['rowClassName']!='':
        行类=行类+' '+属性['rowClassName']
    行.className=行类
    标样式模块(行,披露模块)
    行.setAttribute('data-disclosure-row','')
    if 行展开:
        行.setAttribute('data-expandable','true')
        行.setAttribute('role','button')
        行.setAttribute('tabIndex','0')
        行.setAttribute('aria-expanded','true' if 打开 else 'false')
    前导类='leading'
    if isinstance(属性.get('leadingClassName'),str) and 属性['leadingClassName']!='':
        前导类=前导类+' '+属性['leadingClassName']
    if 可展 and not 行展开:
        前导=文档.createElement('button')
        前导.type='button'
        前导.setAttribute('aria-label',属性.get('title') or '')
        前导.setAttribute('aria-expanded','true' if 打开 else 'false')
    else:
        前导=文档.createElement('span')
    前导.className=前导类
    标样式模块(前导,披露模块)
    if 打开:
        箭头=图标上chevron14({'window':窗口,'className':属性.get('chevronClassName') or ''})
        if 箭头 is not None:
            前导.appendChild(箭头)
    elif 预览箭头:
        闲=文档.createElement('span')
        闲.className='iconIdle'
        标样式模块(闲,披露模块)
        挂节点(闲,属性.get('icon'))
        前导.appendChild(闲)
        悬=图标下箭头描边常规({'window':窗口,'className':'chevronHover'})
        if 悬 is not None:
            if isinstance(属性.get('chevronClassName'),str) and 属性['chevronClassName']!='':
                悬.className=悬.className+' '+属性['chevronClassName']
            标样式模块(悬,披露模块)
            前导.appendChild(悬)
    else:
        挂节点(前导,属性.get('icon'))
    行.appendChild(前导)
    闪=文字闪烁({
        'window':窗口,
        'active':属性.get('running') is True,
        'className':属性.get('contentClassName'),
        'contentClassName':属性.get('contentLayoutClassName'),
        'children':None,
    })
    闪根=闪.渲染()
    题=文字闪烁({
        'window':窗口,
        'children':属性.get('title') or '',
        'className':'title'+((' '+属性['titleClassName']) if isinstance(属性.get('titleClassName'),str) and 属性['titleClassName']!='' else ''),
    })
    题根=题.渲染()
    if 题根 is not None:
        标样式模块(题根,披露模块)
        闪根.appendChild(题根)
    if 保持 or not 打开:
        挂节点(闪根,属性.get('collapsedContent'))
    行.appendChild(闪根)
    头.appendChild(行)
    挂节点(头,属性.get('headerAccessory'))
    根.appendChild(头)
    if 打开:
        挂节点(根,属性.get('children'))

    def 切换(事件=None):
        '点行或前导按钮都走同一回调'
        if 事件 is not None and hasattr(事件,'stopPropagation') and 事件.currentTarget is 前导 and 行展开 is False:
            事件.stopPropagation()
        回调=属性.get('onToggle')
        if callable(回调):
            回调()

    def 键盘(事件):
        '整行可展开时，回车和空格也切换'
        if not 行展开:
            return
        键=getattr(事件,'key',None)
        if 键!='Enter' and 键!=' ':
            return
        if hasattr(事件,'preventDefault'):
            事件.preventDefault()
        切换(事件)

    if 行展开:
        行.addEventListener('click',切换)
        行.addEventListener('keydown',键盘)
    elif 可展:
        前导.addEventListener('click',切换)
    return 根
