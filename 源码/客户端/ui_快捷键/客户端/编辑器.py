'行内物理键录制，并按用户核对过的修订保存'
from ...模块.客户端.通告 import 取握手窗口
import os
import re
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.焦点 import 无轮廓聚焦
from ...ui_基础界面组件.快捷键 import 快捷键
from ...ui_基础界面组件.键盘合成 import 观察合成
from .反馈 import 快捷键失败,快捷键读取失败
from .文案 import 中文

__all__=['快捷键编辑器','确保样式']

样式模块='shortcuts-reference'
样式路径=os.path.join(os.path.dirname(__file__),'参考.module.css')
图形命名空间='http://www.w3.org/2000/svg'
修饰码=re.compile(r'^(Control|Alt|Shift|Meta)(Left|Right)$')
元键=re.compile(r'^Meta(Left|Right)$')
左右后缀=re.compile(r'(Left|Right)$')

def 原样(值):
    '钩子选择器原样返回快照'
    return 值

def 确保样式(文档):
    '快捷键参考样式只插一次'
    注入模块样式文件(文档,'快捷键参考样式',样式路径,样式模块)

def 建(文档,标签,类名=None):
    '造一个挂了参考样式的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    标样式模块(节点,样式模块)
    return 节点

class 快捷键编辑器:
    '对着用户核对过的配置保存松开的物理组合。失败留下草稿，可以再录'
    def __init__(自身,属性):
        '记下命令和录键态，并开始听键盘'
        自身.属性=属性
        配置=属性['useConfig'](原样)
        自身.修订=配置['revision']
        自身.候选=None
        自身.已捕获=False
        自身.忙=False
        自身.原生就绪=属性['runtime']=='web'
        自身.消息=''
        自身.重试=None
        自身.已拆=False
        自身.写入中=False
        自身.按住=set()
        自身.待定=None
        自身.已死=False
        自身.已拦=False
        自身.录钮=None
        自身.根=None
        自身.父=属性['parent'] if 'parent' in 属性 else None
        自身.描述标识='shortcut-edit-'+str(id(自身))
        自身.合成=None
        自身.已听=False
        自身.换代中=False
        自身.已送焦=False
        自身.按键中=False
        自身.窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        自身.启用()

    def 桌面和弦(自身):
        '桌面 macOS 和 Windows 用和弦录制'
        运行时=自身.属性['runtime']
        平台=自身.属性['platform']
        return 运行时=='desktop' and (平台=='macos' or 平台=='windows')

    def 过期(自身):
        '草稿修订落后于当前配置'
        配置=自身.属性['useConfig'](原样)
        return 自身.修订!=配置['revision']

    def 报告(自身,文本):
        '写下失败句并交给速查吐司'
        自身.消息=文本
        自身.属性['onError'](文本)
        if 自身.已拆 or 自身.换代中:
            return
        自身.渲染()

    def 重置缓冲(自身):
        '清掉还没松开的和弦，不改已经显示的候选'
        自身.待定=None
        自身.按住.clear()
        自身.已拦=False
        自身.已死=False

    def 保存(自身,操作,已核修订=None):
        '串行写入。保存成功就交给关闭，失败留下可重试的草稿'
        if 自身.写入中:
            return
        if 已核修订 is None:
            已核修订=自身.修订
        自身.写入中=True
        自身.忙=True
        自身.渲染()
        结果=自身.属性['edit'](操作,已核修订)
        if 自身.已拆:
            return
        自身.写入中=False
        自身.忙=False
        if 结果['status']=='saved':
            自身.属性['onSaved']()
            return
        if 操作['type']=='set':
            自身.重试=操作['binding']
        else:
            自身.重试=None
        目录=list(自身.属性['useCatalog'](原样))
        固定=list(自身.属性['useFixedCatalog'](原样))
        自身.报告(快捷键失败(结果,目录+固定,自身.属性['runtime']))

    def 捕获(自身,绑定,标识):
        '校验冲突和修订后再保存'
        自身.候选=绑定
        自身.已捕获=True
        自身.重试=None
        描述=自身.属性['describeBinding'](绑定)
        目录=list(自身.属性['useCatalog'](原样))
        固定=list(自身.属性['useFixedCatalog'](原样))
        全部=目录+固定
        冲突名=[]
        for 值 in 描述['conflicts']:
            if 值==标识:
                continue
            名=值
            for 行 in 全部:
                if 行['id']==值:
                    名=行['label']
                    break
            冲突名.append(名)
        if 描述['issue'] is not None:
            议题=描述['issue']
            自身.报告(中文[议题] if 议题 in 中文 else 议题)
            return
        if len(冲突名)>0:
            自身.报告('已被「'+', '.join(冲突名)+'」占用')
            return
        if 自身.过期():
            自身.重试=绑定
            自身.报告('快捷键配置或可用命令已更新。请核对最新键位后再保存。')
            return
        配置=自身.属性['useConfig'](原样)
        if 配置['status']!='ready':
            if 配置['status']=='loading':
                自身.报告('快捷键尚未准备好，请稍后重试。')
            else:
                自身.报告(快捷键读取失败(配置,自身.属性['runtime']))
            return
        自身.保存({'type':'set','id':标识,'binding':绑定})

    def 按下(自身,事件):
        '捕获阶段记录物理键。Esc 退出，修饰键只更新和弦'
        if 自身.已拆:
            return
        自身.按键中=True
        try:
            桌面=自身.桌面和弦()
            文档=自身.窗口.document
            if 自身.合成['guards'](事件) or 事件.getModifierState('AltGraph'):
                if 桌面:
                    自身.重置缓冲()
                return
            在录钮=文档.activeElement is 自身.录钮
            无修饰=not 事件.ctrlKey and not 事件.altKey and not 事件.metaKey and not 事件.shiftKey
            if (not 桌面 or not 在录钮) and 事件.key=='Escape' and 无修饰:
                事件.preventDefault()
                事件.stopPropagation()
                if not 事件.repeat and not 自身.写入中:
                    自身.属性['onClose']()
                return
            平台=自身.属性['platform']
            命令死键=(自身.属性['runtime']=='web' and 平台=='macos' and 在录钮
                and 事件.code=='KeyN' and 事件.metaKey and 事件.altKey
                and not 事件.ctrlKey and not 事件.shiftKey)
            if 事件.key=='Dead' and not 命令死键:
                if 桌面:
                    自身.重置缓冲()
                自身.已死=True
                return
            if 自身.已死:
                自身.已死=False
                return
            对照={
                'control':事件.ctrlKey,
                'alt':事件.altKey,
                'shift':事件.shiftKey,
                'meta':事件.metaKey,
            }
            修饰=[]
            for 名 in ('control','alt','shift','meta'):
                if 对照[名]:
                    修饰.append(名)
            录制制表=桌面 or ((平台=='macos' or 平台=='windows') and len(修饰)>=3)
            if not 在录钮 or (事件.key=='Tab' and not 录制制表):
                return
            事件.preventDefault()
            事件.stopPropagation()
            if 自身.写入中 or 事件.repeat:
                return
            if 修饰码.match(事件.code):
                if 桌面 and 自身.待定 is not None:
                    自身.重置缓冲()
                    自身.候选=None
                    自身.已捕获=False
                    自身.渲染()
                return
            if 桌面:
                自身.按住.add(事件.code)
                if 自身.已拦:
                    return
                if len(自身.按住)>2:
                    自身.已拦=True
                    自身.待定=None
                    自身.报告('最多同时按下两个非修饰键。请松开后重试。')
                    return
            try:
                其余=[]
                if 桌面:
                    for 码 in 自身.按住:
                        if 码!=事件.code:
                            其余.append(码)
                候选={'code':事件.code,'modifiers':修饰}
                if len(其余)>0:
                    候选['secondCode']=其余[0]
                自身.待定=自身.属性['describeBinding'](候选)['binding']
                自身.候选=自身.待定
                自身.已捕获=桌面
                自身.消息=''
                自身.重试=None
                自身.渲染()
            except Exception as 描述错误:
                '这个物理键不能描述成绑定'
                丢弃=描述错误
                自身.已拦=桌面
                自身.待定=None
                自身.报告('暂不支持这个按键。')
        finally:
            自身.按键中=False

    def 抬起(自身,事件):
        '松开时提交已经录到的组合'
        if 自身.已拆:
            return
        自身.按键中=True
        try:
            自身.按住.discard(事件.code)
            桌面=自身.桌面和弦()
            文档=自身.窗口.document
            if 桌面 and 文档.activeElement is 自身.录钮:
                事件.preventDefault()
                事件.stopPropagation()
            待定=自身.待定
            是这条=False
            if 待定 is not None:
                if 待定['code']==事件.code or 待定.get('secondCode')==事件.code:
                    是这条=True
                else:
                    码名=左右后缀.sub('',事件.code).lower()
                    for 修饰名 in 待定['modifiers']:
                        if 修饰名==码名:
                            是这条=True
            绑定=待定 if 是这条 else None
            if 绑定 is not None:
                自身.待定=None
                自身.已拦=桌面
            平台=自身.属性['platform']
            if 桌面 and (len(自身.按住)==0 or (平台=='macos' and 元键.match(事件.code) is not None)):
                自身.按住.clear()
                自身.已拦=False
            if 绑定 is None:
                return
            自身.捕获(绑定,自身.属性['target']['id'])
        finally:
            自身.按键中=False

    def 窗口失焦(自身,事件=None):
        '窗口或合成开始时清掉桌面和弦。换节点和录键过程中的失焦不算'
        if 自身.换代中 or 自身.已拆 or 自身.按键中:
            return
        自身.重置缓冲()
        if 自身.桌面和弦():
            自身.候选=None
            自身.已捕获=False
            自身.渲染()

    def 焦点进入(自身,事件):
        '焦点离开录键钮时，桌面和弦作废'
        if 自身.已拆:
            return
        文档=自身.窗口.document
        if 文档.activeElement is not 自身.录钮:
            自身.窗口失焦()

    def 录钮失焦(自身,事件):
        '换节点造成的失焦不算用户离开'
        if 自身.换代中 or 自身.已拆:
            return
        if 事件.target is not 自身.录钮:
            return
        自身.重置缓冲()

    def 启用(自身):
        '打开录键保护并听文档键盘'
        if 自身.已听:
            return
        文档=自身.窗口.document
        窗口=自身.窗口
        try:
            自身.属性['recording'](True)
            if not 自身.已拆:
                自身.原生就绪=True
        except Exception as 录键错误:
            '桌面录键保护没打开'
            丢弃=录键错误
            if not 自身.已拆:
                自身.报告('无法启用桌面录键保护，请关闭后重试。')
        自身.合成=观察合成(文档)
        文档.addEventListener('keydown',自身.按下,True)
        文档.addEventListener('keyup',自身.抬起,True)
        窗口.addEventListener('blur',自身.窗口失焦)
        if 自身.桌面和弦():
            文档.addEventListener('focusin',自身.焦点进入,True)
            文档.addEventListener('compositionstart',自身.窗口失焦,True)
        自身.已听=True

    def 拆除(自身):
        '卸键盘、合成观察，并关掉录键保护'
        if 自身.已拆:
            return
        自身.已拆=True
        文档=自身.窗口.document
        窗口=自身.窗口
        if 自身.合成 is not None:
            自身.合成['dispose']()
            自身.合成=None
        if 自身.已听:
            文档.removeEventListener('keydown',自身.按下,True)
            文档.removeEventListener('keyup',自身.抬起,True)
            窗口.removeEventListener('blur',自身.窗口失焦)
            文档.removeEventListener('focusin',自身.焦点进入,True)
            文档.removeEventListener('compositionstart',自身.窗口失焦,True)
            自身.已听=False
        try:
            自身.属性['recording'](False)
        except Exception as 收尾错误:
            '所属窗口可能已经关掉'
            丢弃=收尾错误
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None

    def 点恢复(自身,事件):
        '把这条命令恢复成默认'
        自身.保存({'type':'reset','id':自身.属性['target']['id']})

    def 点清除(自身,事件):
        '去掉这条命令的快捷键'
        自身.保存({'type':'set','id':自身.属性['target']['id'],'binding':None})

    def 点核对(自身,事件):
        '接受当前配置修订，清掉过期提示'
        配置=自身.属性['useConfig'](原样)
        自身.修订=配置['revision']
        自身.消息=''
        自身.渲染()

    def 点重试(自身,事件):
        '用上次没写成的组合再试一次'
        if 自身.重试 is None:
            return
        自身.捕获(自身.重试,自身.属性['target']['id'])

    def 点录(自身,事件):
        '清空缓冲，准备再录'
        if 自身.写入中:
            return
        自身.重置缓冲()
        自身.已捕获=False
        自身.消息=''
        自身.重试=None
        自身.渲染()

    def 帮助文(自身):
        '没有错误时，按平台给出录键说明'
        if 自身.消息!='':
            return 自身.消息
        if 自身.桌面和弦():
            return ''
        运行时=自身.属性['runtime']
        平台=自身.属性['platform']
        if 运行时!='web':
            return '松开组合键即保存。Tab 切换操作，Esc 退出录键。'
        if 平台=='windows':
            return '可设置 Ctrl+/、Ctrl+,、Ctrl+Alt+按键或 Ctrl+Shift+按键。也支持三个或四个不同修饰键的组合。浏览器或系统占用的组合可能无法送达页面。'
        if 平台=='macos':
            return '可设置 Command+/、Command+,、Command+反斜杠、Control+反引号、Command+Option+按键或 Command+Shift+按键。也支持三个或四个不同修饰键的组合。浏览器或系统占用的组合可能无法送达页面。'
        return '浏览器可用组合：Mod+/、Mod+Shift+,、Mod+Shift+.。Mod 在 Mac 上为 Command，其他系统为 Ctrl。'

    def 挂入(自身,父):
        '父列表换了节点之后，把编辑器画进新的格子'
        自身.父=父
        自身.渲染()

    def 渲染(自身):
        '画出恢复、移除和录键。过期时先核对再保存'
        if 自身.已拆:
            return 自身.根
        窗口=自身.窗口
        文档=窗口.document
        确保样式(文档)
        要回=自身.按键中 or (自身.录钮 is not None and 文档.activeElement is 自身.录钮)
        配置=自身.属性['useConfig'](原样)
        目标=自身.属性['target']
        只读=自身.忙 or 自身.过期() or 配置['status']!='ready'
        自身.换代中=True
        try:
            if 自身.根 is not None:
                自身.根.remove()
            根=建(文档,'div','inlineEditor')
            根.setAttribute('role','group')
            根.setAttribute('aria-label',目标['label'])
            根.setAttribute('data-shortcut-modal','shortcut-edit')
            根.setAttribute('aria-busy','true' if 自身.忙 else 'false')
            控件=建(文档,'div','inlineControls')
            恢复=建(文档,'button','inlineAction')
            恢复.type='button'
            恢复.disabled=只读
            恢复.textContent='恢复默认'
            恢复.addEventListener('click',自身.点恢复)
            控件.appendChild(恢复)
            if 目标['binding'] is not None:
                清除=建(文档,'button','inlineAction')
                清除.type='button'
                清除.disabled=只读
                清除.textContent='移除'
                清除.addEventListener('click',自身.点清除)
                控件.appendChild(清除)
            录类='recorder'
            if 自身.消息!='':
                录类=录类+' invalid'
            录=建(文档,'button',录类)
            录.type='button'
            录.disabled=not 自身.原生就绪
            录.setAttribute('aria-disabled','true' if 自身.忙 or not 自身.原生就绪 else 'false')
            录.setAttribute('aria-label','按下快捷键')
            录.setAttribute('aria-invalid','true' if 自身.消息!='' else 'false')
            录.setAttribute('aria-describedby',自身.描述标识)
            录.addEventListener('blur',自身.录钮失焦)
            录.addEventListener('click',自身.点录)
            if 自身.已捕获 and 自身.消息=='':
                键列=自身.属性['describeBinding'](自身.候选)['keys']
                外=建(文档,'span','recorded')
                外.style.display='inline-flex'
                外.style.alignItems='center'
                内=快捷键({'window':窗口,'keys':键列}).渲染()
                if 内 is not None:
                    内.style.color='inherit'
                    外.appendChild(内)
                录.appendChild(外)
            else:
                录.textContent='按下快捷键'
            控件.appendChild(录)
            根.appendChild(控件)
            说明=建(文档,'span','srOnly')
            说明.id=自身.描述标识
            说明.textContent=自身.帮助文()
            根.appendChild(说明)
            if 自身.过期():
                核对区=建(文档,'div','review')
                提示=建(文档,'span')
                提示.textContent='快捷键配置或可用命令已更新。请核对最新键位后再保存。'
                核对=建(文档,'button','inlineAction')
                核对.type='button'
                核对.disabled=自身.忙
                核对.textContent='已核对最新配置'
                核对.addEventListener('click',自身.点核对)
                核对区.appendChild(提示)
                核对区.appendChild(核对)
                根.appendChild(核对区)
            if 自身.重试 is not None and not 自身.过期():
                重试=建(文档,'button','inlineAction')
                重试.type='button'
                重试.disabled=只读
                重试.textContent='重试保存'
                重试.addEventListener('click',自身.点重试)
                根.appendChild(重试)
            自身.录钮=录
            自身.根=根
            if 自身.父 is not None:
                自身.父.appendChild(根)
        finally:
            自身.换代中=False
        if 自身.原生就绪 and 自身.录钮 is not None and 自身.录钮.parentNode is not None and not 自身.已送焦:
            自身.已送焦=True
            无轮廓聚焦(自身.录钮)
        elif 要回 and 自身.录钮 is not None:
            自身.录钮.focus()
        return 自身.根
