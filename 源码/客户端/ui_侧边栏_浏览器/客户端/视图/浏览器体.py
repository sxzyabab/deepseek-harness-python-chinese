from uuid import uuid4
import pywebbridge
from ....ui_基础界面组件.icons import (
    图标左chevron14,
    图标右chevron14,
    图标刷新16,
    图标链接16,
    图标右上14,
)
from ....ui_基础界面组件.按钮 import 按钮
from ....ui_基础界面组件.提示泡 import 提示泡
from ..文案 import 中文
from ..浏览器.帧 import 空浏览器帧
from ..浏览器.浏览器持久化 import 当前浏览器目标
from .浏览器呈现形式 import 取窗口,确保浏览器样式,标浏览器

__all__=['浏览器体']

空帧=空浏览器帧()
盾牌路径='M6.80132 2.14853C7.70663 1.80917 8.70422 1.80919 9.60952 2.14859L14.1296 3.84317V7.11961C14.1296 11.6089 10.7615 13.5975 8.20543 14.5779C5.64931 13.5975 2.28052 11.6089 2.28052 7.11961V3.84317L6.80132 2.14853Z'
沙箱勾路径='M12.1654 5.7552L8.9447 9.41475C8.73044 9.65816 8.53628 9.8804 8.35774 10.0423C8.1713 10.2114 7.94235 10.3717 7.64016 10.4254C7.48207 10.4535 7.32 10.4552 7.16151 10.4294C6.85843 10.3801 6.62728 10.2223 6.43836 10.0559C6.25752 9.89653 6.06037 9.67732 5.84264 9.43705L4.72925 8.20897L5.63557 7.38707L6.74897 8.61594C6.98603 8.87755 7.12974 9.03533 7.24673 9.13839C7.31033 9.19443 7.34485 9.21476 7.35823 9.22122C7.38068 9.22484 7.40352 9.22515 7.42593 9.22122C7.40522 9.22502 7.42893 9.23294 7.53583 9.136C7.65132 9.03126 7.79316 8.87139 8.02643 8.60638L11.2479 4.94763L12.1654 5.7552Z'
沙箱叉路径='M10.6074 4.40278L8.00975 6.99973L10.6074 9.59739L9.59736 10.6074L6.9997 8.00978L4.40274 10.6074L3.3927 9.59739L5.98966 6.99973L3.3927 4.40278L4.40274 3.39273L6.9997 5.98969L9.59736 3.39273L10.6074 4.40278Z'


def 拼类(*段):
    '丢掉空类名后用空格接上'
    留下=[]
    for 段名 in 段:
        if isinstance(段名,str) and 段名!='':
            留下.append(段名)
    return ' '.join(留下)


class 浏览器体:
    '地址栏、导航按钮和页面容器。具体页面由呈现接进视口'
    按标签={}

    def __new__(类,属性=None):
        '同一张签复用一份界面，返回根节点'
        信息=属性['useTabInfo']()
        标识=信息['tab']['id']
        已有=类.按标签.get(标识)
        if 已有 is not None:
            已有.属性=属性
            已有.渲染()
            return 已有.根
        自身=object.__new__(类)
        自身.标签标识=标识
        自身.__init__(属性)
        类.按标签[标识]=自身
        return 自身.根

    def __init__(自身,属性):
        '记下第一次看到的保存记录和打开地址，再画出'
        自身.属性=属性
        自身.窗口=取窗口(属性)
        自身.文档=自身.窗口.document
        自身.视口标识='sidebar-browser-'+uuid4().hex
        自身.根=None
        自身.绘制中=False
        自身.待重画=False
        自身.已写修订=None
        自身.挂载键=None
        自身.卸挂载=None
        自身.挂载代=0
        自身.定时=None
        自身.已绑动作=None
        自身.已绑标识=None
        自身.外部址=None
        自身.沙箱值=None
        信息=属性['useTabInfo']()
        签=信息['tab']

        def 取保存(状态):
            '这一签已保存的导航'
            按签=状态.get('byTab') if isinstance(状态,dict) else None
            if not isinstance(按签,dict):
                return None
            return 按签.get(自身.标签标识)

        自身.初态=属性['useStore'](取保存)
        导航=签.get('navigation') if isinstance(签,dict) else None
        参数=导航.get('params') if isinstance(导航,dict) else None
        自身.初址=参数.get('url') if isinstance(参数,dict) else None
        信号=签.get('signal')

        def 签结束():
            '这张签结束就放下界面'
            浏览器体.按标签.pop(自身.标签标识,None)
            if 自身.定时 is not None:
                自身.窗口.clearTimeout(自身.定时)
                自身.定时=None
            if callable(自身.卸挂载):
                卸=自身.卸挂载
                自身.卸挂载=None
                卸()

        if 信号 is not None and hasattr(信号,'addEventListener'):
            信号.addEventListener('abort',签结束,{'once':True})
        自身.渲染()

    def 渲染(自身):
        '按当前帧状态更新工具栏和提示。视口节点保持不动'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            确保浏览器样式(自身.文档)
            if 自身.根 is None:
                自身.建骨架()
            信息=自身.属性['useTabInfo']()
            签=信息['tab']
            自身.绑定刷新(签)
            状态=None
            用状态=自身.属性.get('useBrowserState')
            if callable(用状态):
                状态=用状态(签['id'])
            帧=空帧 if 状态 is None or 状态.get('frame') is None else 状态['frame']
            if 状态 is None:
                恢复目标=当前浏览器目标(自身.初态)
            else:
                恢复目标=状态.get('restoreTarget')
            目标=帧.get('target') if 帧.get('target') is not None else 恢复目标
            自身.同步地址(目标,0 if 状态 is None else 状态.get('addressRevision') or 0)
            自身.更新工具栏(签,帧,目标,恢复目标,状态)
            自身.安排挂载(签)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 建骨架(自身):
        '造出工具栏、地址栏和视口。条件块先留空位'
        文档=自身.文档
        根=文档.createElement('div')
        标浏览器(根,'root')
        表单=文档.createElement('form')
        标浏览器(表单,'toolbar')

        def 提交(事件):
            '阻止表单跳转，把地址栏里的字交给加载'
            事件.preventDefault()
            自身.属性['loadUrl'](自身.标签标识,自身.地址.value)

        表单.addEventListener('submit',提交)
        自身.后退钮=自身.工具钮(中文['back'],图标左chevron14)
        自身.前进钮=自身.工具钮(中文['forward'],图标右chevron14)
        自身.刷新钮=自身.工具钮(中文['reload'],图标刷新16)
        自身.提示文=None
        自身.提示=None
        地址盒=文档.createElement('div')
        标浏览器(地址盒,'addressBox')
        地址=文档.createElement('input')
        标浏览器(地址,'address')
        地址.setAttribute('aria-label',中文['address.placeholder'])
        地址.setAttribute('placeholder',中文['address.placeholder'])
        地址.setAttribute('spellcheck','false')
        已变=文档.createElement('span')
        标浏览器(已变,'addressChanged')
        已变.textContent=中文['address.changed']
        已变.hidden=True
        前往=自身.工具钮(中文['go'],图标链接16)
        前往.type='submit'
        标浏览器(前往,拼类('tool','addressGo'))
        地址盒.appendChild(地址)
        地址盒.appendChild(已变)
        地址盒.appendChild(前往)
        自身.外部钮=自身.工具钮(中文['external'],None)
        外图=图标右上14({'window':自身.窗口,'size':14})
        if 外图 is not None:
            自身.外部钮.appendChild(外图)

        def 打开外部(事件):
            '用系统浏览器打开当前已知地址'
            if 自身.外部址 is not None:
                自身.窗口.open(自身.外部址,'_blank','noopener,noreferrer')

        自身.外部钮.addEventListener('click',打开外部)
        表单.appendChild(自身.后退钮)
        表单.appendChild(自身.前进钮)
        表单.appendChild(自身.刷新钮)
        表单.appendChild(地址盒)
        表单.appendChild(自身.外部钮)
        内容=文档.createElement('div')
        标浏览器(内容,'content')
        视口=文档.createElement('div')
        视口.id=自身.视口标识
        标浏览器(视口,'viewport')
        视口.setAttribute('aria-label',中文['type.label'])
        内容.appendChild(视口)
        根.appendChild(表单)
        根.appendChild(内容)
        自身.根=根
        自身.表单=表单
        自身.地址=地址
        自身.已变=已变
        自身.内容=内容
        自身.视口=视口
        自身.沙箱钮=None
        自身.沙箱图=None
        自身.警告=None
        自身.加载失败=None
        自身.地址失败=None
        自身.恢复区=None
        自身.占位=None
        自身.限制=None

    def 工具钮(自身,文案,图标):
        '工具栏上的图标按钮'
        钮=自身.文档.createElement('button')
        钮.type='button'
        标浏览器(钮,'tool')
        钮.setAttribute('aria-label',文案)
        钮.setAttribute('title',文案)
        if 图标 is not None:
            图=图标({'window':自身.窗口})
            if 图 is not None:
                钮.appendChild(图)
        return 钮

    def 绑定刷新(自身,签):
        '把侧栏的刷新命令接到这一页'
        动作=签.get('actions')
        if 动作 is None or not callable(动作.get('bindCommands')):
            return
        if 自身.已绑动作 is 动作 and 自身.已绑标识==签['id']:
            return

        def 刷新命令(标识=签['id']):
            '重载或恢复这一页'
            自身.属性['reload'](标识)

        动作['bindCommands']({'refresh':刷新命令})
        自身.已绑动作=动作
        自身.已绑标识=签['id']

    def 同步地址(自身,目标,修订):
        '修订变了才把地址写进输入框。框里的字在此之前留在浏览器'
        if 自身.已写修订==修订:
            return
        网址=''
        if 目标 is not None and 目标.get('url') is not None:
            网址=目标['url']
        elif isinstance(自身.初址,str):
            网址=自身.初址
        自身.地址.value=网址
        自身.已写修订=修订

    def 更新工具栏(自身,签,帧,目标,恢复目标,状态):
        '刷新按钮可用性、失败句和恢复区'
        未知=帧.get('address')=='unknown'
        标浏览器(自身.地址,拼类('address','addressUnknown' if 未知 else ''))
        自身.已变.hidden=not 未知
        自身.后退钮.disabled=not 帧.get('canGoBack')
        自身.前进钮.disabled=not 帧.get('canGoForward')
        快捷=签.get('refreshShortcut') if isinstance(签,dict) else None
        提示文=中文['reload']
        if isinstance(快捷,dict) and 快捷.get('keys'):
            提示文=提示文+' '+' '.join(str(键) for 键 in 快捷['keys'])
        if isinstance(快捷,dict) and 快捷.get('aria'):
            自身.刷新钮.setAttribute('aria-keyshortcuts',快捷['aria'])
        else:
            自身.刷新钮.removeAttribute('aria-keyshortcuts')
        自身.刷新钮.disabled=目标 is None or 自身.挂载代==0
        自身.放提示(提示文)
        自身.外部址=None if 未知 or 目标 is None else 目标.get('url')
        自身.外部钮.disabled=自身.外部址 is None
        已沙箱=帧.get('sandboxEnabled')
        自身.放沙箱(已沙箱)
        if 已沙箱 is False:
            自身.确保警告()
            自身.警告.hidden=False
        elif 自身.警告 is not None:
            自身.警告.hidden=True
        错误=帧.get('error')
        if 错误 is not None:
            自身.确保加载失败()
            if 错误.get('code') is not None and 错误.get('description') is not None:
                文=中文['load.failed.detail']
                文=文.replace('{code}',str(错误['code']))
                文=文.replace('{description}',str(错误['description']))
            else:
                文=中文['load.failed']
            自身.加载失败.textContent=文
            自身.加载失败.hidden=False
        elif 自身.加载失败 is not None:
            自身.加载失败.hidden=True
        失败=None if 状态 is None else 状态.get('addressFailure')
        if 失败 is not None:
            自身.确保地址失败()
            自身.地址失败.textContent=中文['error.'+失败]
            自身.地址失败.hidden=False
        elif 自身.地址失败 is not None:
            自身.地址失败.hidden=True
        if 帧.get('loading'):
            自身.内容.setAttribute('aria-busy','true')
        else:
            自身.内容.removeAttribute('aria-busy')
        if 恢复目标 is not None:
            自身.确保恢复()
            自身.恢复标题.textContent=恢复目标.get('title') or ''
            自身.恢复地址.textContent=恢复目标.get('url') or ''
            自身.恢复钮.disabled=自身.挂载代==0
            自身.恢复区.hidden=False
        elif 自身.恢复区 is not None:
            自身.恢复区.hidden=True
        显示占位=恢复目标 is None and 错误 is None and (目标 is None or 帧.get('loading'))
        if 显示占位:
            自身.确保占位()
            自身.占位文.textContent=中文['start'] if 目标 is None else 中文['loading']
            自身.占位.hidden=False
        elif 自身.占位 is not None:
            自身.占位.hidden=True
        if 未知:
            自身.确保限制()
            自身.限制.hidden=False
        elif 自身.限制 is not None:
            自身.限制.hidden=True

        def 点后退(事件):
            '后退'
            自身.属性['goBack'](自身.标签标识)

        def 点前进(事件):
            '前进'
            自身.属性['goForward'](自身.标签标识)

        def 点刷新(事件):
            '刷新'
            自身.属性['reload'](自身.标签标识)

        if not getattr(自身,'_已接点击',False):
            自身.后退钮.addEventListener('click',点后退)
            自身.前进钮.addEventListener('click',点前进)
            自身.刷新钮.addEventListener('click',点刷新)
            自身._已接点击=True

    def 放提示(自身,提示文):
        '刷新按钮外包一层提示。文案变了就换掉外壳'
        if 自身.提示 is not None and 自身.提示文==提示文:
            return
        if 自身.提示 is not None:
            自身.提示.remove()
        泡=提示泡({
            'window':自身.窗口,
            'label':提示文,
            'side':'bottom',
            'children':自身.刷新钮,
        })
        自身.提示=泡.渲染()
        自身.提示文=提示文
        自身.表单.insertBefore(自身.提示,自身.地址.parentNode)

    def 放沙箱(自身,已沙箱):
        '只有载体提供沙箱开关时才显示'
        if 已沙箱 is None:
            if 自身.沙箱钮 is not None:
                自身.沙箱钮.remove()
                自身.沙箱钮=None
                自身.沙箱图=None
                自身.沙箱值=None
            return
        if 自身.沙箱钮 is None:
            钮=自身.文档.createElement('button')
            钮.type='button'

            def 点沙箱(事件):
                '在开和关之间切换'
                自身.属性['setSandbox'](自身.标签标识,not 自身.沙箱值)

            钮.addEventListener('click',点沙箱)
            自身.表单.appendChild(钮)
            自身.沙箱钮=钮
        if 自身.沙箱值 is 已沙箱:
            return
        文=中文['sandbox.disable'] if 已沙箱 else 中文['sandbox.enable']
        标浏览器(自身.沙箱钮,拼类('tool','' if 已沙箱 else 'sandboxOff'))
        自身.沙箱钮.setAttribute('aria-label',文)
        自身.沙箱钮.setAttribute('title',文)
        自身.沙箱钮.setAttribute('aria-pressed','false' if 已沙箱 else 'true')
        if 自身.沙箱图 is not None:
            自身.沙箱图.remove()
        图=自身.文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('width','15')
        图.setAttribute('height','15')
        图.setAttribute('viewBox','0 0 16 16')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        盾=自身.文档.createElementNS('http://www.w3.org/2000/svg','path')
        盾.setAttribute('d',盾牌路径)
        盾.setAttribute('stroke','currentColor')
        盾.setAttribute('stroke-width','1')
        盾.setAttribute('stroke-linejoin','round')
        图.appendChild(盾)
        记=自身.文档.createElementNS('http://www.w3.org/2000/svg','path')
        if 已沙箱:
            记.setAttribute('d',沙箱勾路径)
        else:
            记.setAttribute('d',沙箱叉路径)
            记.setAttribute('transform','translate(1.2 0.8)')
        记.setAttribute('fill','currentColor')
        图.appendChild(记)
        自身.沙箱图=图
        自身.沙箱钮.appendChild(图)
        自身.沙箱值=已沙箱

    def 确保警告(自身):
        '沙箱关闭时的说明'
        if 自身.警告 is not None:
            return
        警告=自身.文档.createElement('div')
        标浏览器(警告,'sandboxWarning')
        警告.setAttribute('role','status')
        警告.textContent=中文['sandbox.warning']
        自身.根.insertBefore(警告,自身.内容)
        自身.警告=警告

    def 确保加载失败(自身):
        '页面加载失败'
        if 自身.加载失败 is not None:
            return
        条=自身.文档.createElement('div')
        标浏览器(条,'failure')
        条.setAttribute('role','status')
        自身.根.insertBefore(条,自身.内容)
        自身.加载失败=条

    def 确保地址失败(自身):
        '地址校验失败'
        if 自身.地址失败 is not None:
            return
        条=自身.文档.createElement('div')
        标浏览器(条,'failure')
        条.setAttribute('role','alert')
        自身.根.insertBefore(条,自身.内容)
        自身.地址失败=条

    def 确保恢复(自身):
        '上次打开的页面，等用户确认再恢复'
        if 自身.恢复区 is not None:
            return
        区=自身.文档.createElement('section')
        标浏览器(区,'restore')
        区.setAttribute('aria-label',中文['restore.previous'])
        标=自身.文档.createElement('p')
        标浏览器(标,'restoreLabel')
        标.textContent=中文['restore.previous']
        题=自身.文档.createElement('p')
        标浏览器(题,'restoreTitle')
        址=自身.文档.createElement('p')
        标浏览器(址,'restoreUrl')

        def 点恢复():
            '恢复保存的页面'
            自身.属性['restore'](自身.标签标识)

        钮=按钮({
            'window':自身.窗口,
            'variant':'primary',
            'size':'sm',
            'onClick':点恢复,
            'children':中文['restore.action'],
        }).渲染()
        区.appendChild(标)
        区.appendChild(题)
        区.appendChild(址)
        区.appendChild(钮)
        自身.内容.appendChild(区)
        自身.恢复区=区
        自身.恢复标题=题
        自身.恢复地址=址
        自身.恢复钮=钮

    def 确保占位(自身):
        '还没地址或正在打开时的说明'
        if 自身.占位 is not None:
            return
        层=自身.文档.createElement('div')
        标浏览器(层,'placeholder')
        文=自身.文档.createElement('div')
        标浏览器(文,'start')
        层.appendChild(文)
        自身.内容.appendChild(层)
        自身.占位=层
        自身.占位文=文

    def 确保限制(自身):
        '载体读不到新地址时的说明'
        if 自身.限制 is not None:
            return
        条=自身.文档.createElement('p')
        标浏览器(条,'limit')
        条.textContent=中文['address.unknown']
        自身.根.appendChild(条)
        自身.限制=条

    def 安排挂载(自身,签):
        '依赖变了就在这一轮把节点放进文档后再附着'
        键=(
            id(自身.属性.get('mount')),
            签['id'],
            id(签.get('signal')),
            id(签.get('actions')),
            id(自身.属性.get('actions')),
            自身.视口标识,
        )
        if 自身.挂载键==键:
            return
        自身.挂载键=键
        if 自身.定时 is not None:
            自身.窗口.clearTimeout(自身.定时)

        def 稍后(这次=键,这签=签):
            '父级挂上根节点之后再查找视口'
            if 自身.挂载键!=这次:
                return
            自身.定时=None
            自身.执行挂载(这签)

        自身.定时=自身.窗口.setTimeout(稍后,0)

    def 执行挂载(自身,签):
        '把视口交给控制器，并在状态变化时重画'
        if callable(自身.卸挂载):
            卸=自身.卸挂载
            自身.卸挂载=None
            卸()

        def 打开(地址):
            '从这一页再开一个浏览器页'
            签['actions']['openTab']('browser',{'params':{'url':地址},'revealIfOpened':False})

        def 变更():
            '控制器状态变了就重画'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()

        自身.卸挂载=自身.属性['mount']({
            'tabId':签['id'],
            'signal':签['signal'],
            'viewportId':自身.视口标识,
            'applicationOrigin':自身.窗口.location.origin,
            'initial':自身.初态,
            'initialUrl':自身.初址,
            'openTab':打开,
            'onChange':变更,
        })
        自身.挂载代=自身.挂载代+1
        自身.渲染()
