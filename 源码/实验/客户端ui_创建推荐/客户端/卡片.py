'create_personalized_page 的正文：位置、进度、保留、撤销和恢复'
import os
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ....客户端.ui_基础界面组件.按钮 import 按钮
from ....客户端.ui_基础界面组件.菜单 import 菜单
from ....客户端.ui_基础界面组件.提示泡 import 提示泡
from ....客户端.ui_基础界面组件.icons import 图标下箭头描边常规,图标警告16

__all__=['页面卡片正文']

样式模块='creation-card'
槽位=('sidebar-right','page','sidebar-left')
位置项=('sidebar-right','page','sidebar-left','custom')
应用结果=('applied','restart-required','overridden','failed','cancelled')
阶段键=(
    'dismissed','replaced','creating','installing','cancelled','installed','kept',
    'removed','failed','interrupted','unconfirmed',
)
原因键表=(
    'unknown','access-denied','not-live-root','closing','unavailable',
    'invalid-location','read-only','source-missing',
)
应用文案={
    'restart-required':'restart-required',
    'overridden':'overridden',
    'failed':'applicationFailed',
    'cancelled':'applicationCancelled',
}
编号={'n':0}


def 下一编号(前缀):
    '这一张卡片上的控件标识'
    编号['n']=编号['n']+1
    return 前缀+'-'+str(编号['n'])


def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()


def 确保样式(文档):
    '把创建卡片样式模块插进文档'
    注入模块样式文件(
        文档,
        '创建推荐卡片样式',
        os.path.join(os.path.dirname(__file__),'卡片.module.css'),
        样式模块,
    )


def 建(文档,标签名,类名):
    '造出带官方类名和样式模块标记的节点'
    return 模块节点(文档,标签名,样式模块,类名)


def 挂上(父,节点):
    '节点或组件挂到父节点'
    if 节点 is None or 父 is None:
        return None
    if hasattr(节点,'tagName'):
        标样式模块(节点,样式模块)
        父.appendChild(节点)
        return 节点
    if hasattr(节点,'渲染'):
        画出=节点.渲染()
        if 画出 is not None and hasattr(画出,'tagName'):
            标样式模块(画出,样式模块)
            父.appendChild(画出)
        return 画出
    if isinstance(节点,(list,tuple)):
        for 项 in 节点:
            挂上(父,项)
    return None


def 换根(自身,新根):
    '已经在页面上就替换'
    旧=自身.根
    if 旧 is not None and 旧.parentNode is not None and 旧 is not 新根:
        旧.parentNode.replaceChild(新根,旧)
    自身.根=新根
    return 新根


def 键于(键表,值):
    '值在文案键里才返回它'
    if 值 in 键表:
        return 值
    return None


def 解析详情(值):
    'slot 必须是三个预设之一。initialContent 可缺'
    if not isinstance(值,dict) or 值.get('slot') not in 槽位:
        return None
    if 'initialContent' in 值 and 值['initialContent'] is not None and not isinstance(值['initialContent'],str):
        return None
    return 值


def 解析数据(值):
    '已记录的位置、自定义说明、包名和应用结果'
    if not isinstance(值,dict) or 值.get('slot') not in 槽位:
        return None
    if 'customLocation' in 值 and 值['customLocation'] is not None and not isinstance(值['customLocation'],str):
        return None
    if 'bundleName' in 值 and 值['bundleName'] is not None and not isinstance(值['bundleName'],str):
        return None
    if 'application' in 值 and 值['application'] is not None and 值['application'] not in 应用结果:
        return None
    return 值


class 位置选择:
    '四个位置。菜单打开时才展开'
    def __init__(自身,属性=None):
        '默认收起'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.根=None

    def 更新(自身,属性):
        '换当前值和是否禁用'
        自身.属性=属性

    def 点锚(自身,事件=None):
        '开关菜单'
        自身.打开=not 自身.打开
        自身.渲染()

    def 关闭(自身,事件=None):
        '点外或 Escape 收起'
        自身.打开=False
        自身.渲染()

    def 选中(自身,标识):
        '选中后收起，并告诉正文'
        自身.打开=False
        自身.属性['onChange'](标识)
        自身.渲染()

    def 渲染(自身):
        '锚上是当前文案。菜单项带一行说明'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        译=属性['t']
        值=属性.get('value')
        禁用=属性.get('disabled') is True
        箭头=图标下箭头描边常规({'window':窗口,'size':14})
        锚=按钮({
            'window':窗口,
            'variant':'outline',
            'size':'sm',
            'disabled':禁用,
            'className':'locationButton',
            'children':[译(值),箭头],
            'onClick':自身.点锚,
        }).渲染()
        标样式模块(锚,样式模块)
        锚.setAttribute('aria-label',译('location')+': '+译(值))
        锚.setAttribute('aria-haspopup','menu')
        锚.setAttribute('aria-expanded','true' if 自身.打开 and not 禁用 else 'false')
        条目=[]
        for 标识 in 位置项:
            选项=建(文档,'span','locationOption')
            名=文档.createElement('span')
            名.textContent=译(标识)
            提示=文档.createElement('span')
            提示.textContent=译(标识+'Hint')
            选项.appendChild(名)
            选项.appendChild(提示)
            条目.append({'id':标识,'label':选项})
        return 换根(自身,菜单({
            'window':窗口,
            'open':自身.打开 and not 禁用,
            'portal':True,
            'autoFocus':True,
            'compact':True,
            'listClassName':'locationMenu',
            'selectedId':值,
            'onClose':自身.关闭,
            'onSelect':自身.选中,
            'items':条目,
            'anchor':锚,
        }).渲染())


class 页面卡片正文:
    '位置、进度、保留、撤销和恢复'
    def __init__(自身,属性=None):
        '选择和错误先空着。说明是否收起跟存储走'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.选中=None
        自身.自定义=None
        自身.信息=None
        自身.待定=None
        自身.错误=None
        自身.根=None
        自身.退订=None
        自身.位置=None
        自身.创建按钮=None
        自身.信息标识=下一编号('creation-info')
        自身.自定义标识=下一编号('creation-custom')
        仓=自身.属性.get('infoDismissed')
        if 仓 is not None and callable(getattr(仓,'subscribe',None)):
            def 变了():
                '存储变了就重画'
                自身.渲染()
            自身.退订=仓.subscribe(变了)
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换卡片份额。选择和说明偏好留在这一张上'
        旧仓=自身.属性.get('infoDismissed')
        自身.属性=属性
        if 'infoDismissed' not in 属性 and 旧仓 is not None:
            自身.属性['infoDismissed']=旧仓

    def 拆除(自身):
        '卸掉说明偏好的监听'
        if callable(自身.退订):
            自身.退订()
        自身.退订=None

    def 设选中(自身,值):
        '改位置'
        自身.选中=值
        自身.渲染()

    def 点信息(自身,事件=None):
        '打开或收起消耗说明。收起时记住'
        属性=自身.属性
        下一=not 自身.当前说明开()
        自身.信息=下一
        if not 下一 and 属性.get('infoDismissed') is not None:
            属性['infoDismissed'].set(True)
        自身.渲染()

    def 改自定义(自身,事件=None):
        '手写位置。最多 1000 字由输入框卡住'
        if 事件 is None:
            return
        目标=getattr(事件,'target',None)
        自身.自定义='' if 目标 is None else str(getattr(目标,'value',''))
        if 自身.创建按钮 is not None:
            自身.创建按钮.disabled=自身.待定 is not None or 自身.自定义.strip()==''

    def 当前说明开(自身):
        '用户没动过时：还能创建且没记住已读，就展开'
        if 自身.信息 is not None:
            return 自身.信息
        return 自身.可创建() and not 自身.已记住()

    def 已记住(自身):
        '这个浏览器已经收起过说明'
        仓=自身.属性.get('infoDismissed')
        if 仓 is None:
            return False
        return 仓.getSnapshot() is True

    def 可创建(自身):
        '还没开始，或取消、失败、中断、未确认，才提供创建'
        决定=自身.属性.get('decision')
        if 决定 is None:
            return True
        阶段=决定.get('phase') if isinstance(决定,dict) else None
        return 阶段 in ('cancelled','failed','interrupted','unconfirmed')

    def 跑(自身,动词):
        '回复丢失时标运输错误。丢失不等于这次失败'
        自身.待定=动词
        自身.错误=None
        if 动词 in ('create','dismiss'):
            仓=自身.属性.get('infoDismissed')
            if 仓 is not None:
                仓.set(True)
            自身.信息=False
        位置=自身.当前自定义()
        槽=自身.当前槽()
        放置={'slot':槽}
        if 位置=='custom':
            放置['customLocation']=自身.当前手写().strip()
        载荷=放置 if 动词 in ('create','dismiss') else None
        try:
            结果=自身.属性['act'](动词,载荷)
            if 结果 is None:
                自身.错误='transport'
            elif isinstance(结果,dict) and 结果.get('status') in ('refused','unconfirmed'):
                自身.错误=键于(原因键表,结果.get('reason'))
                if 自身.错误 is None:
                    自身.错误='unavailable'
        except Exception as 丢失:
            丢失=None
            自身.错误='transport'
        自身.待定=None
        自身.渲染()

    def 当前数据(自身):
        '已记录数据。解析失败就当没有'
        决定=自身.属性.get('decision')
        if not isinstance(决定,dict):
            return None
        return 解析数据(决定.get('data'))

    def 当前详情(自身):
        '提案详情。不合法就整张只留摘要'
        提案=自身.属性.get('proposal')
        if not isinstance(提案,dict):
            return None
        return 解析详情(提案.get('details'))

    def 当前槽(自身):
        '选了预设就用预设。否则用已记录或提案里的槽'
        if 自身.选中 is not None and 自身.选中!='custom':
            return 自身.选中
        数据=自身.当前数据()
        if isinstance(数据,dict):
            return 数据.get('slot')
        详情=自身.当前详情()
        if isinstance(详情,dict):
            return 详情.get('slot')
        return None

    def 当前自定义(自身):
        '用户选过就用选择。已记录自定义说明时是 custom'
        if 自身.选中 is not None:
            return 自身.选中
        数据=自身.当前数据()
        if isinstance(数据,dict) and 数据.get('customLocation') is not None:
            return 'custom'
        return 自身.当前槽()

    def 当前手写(自身):
        '草稿优先，否则用已记录的自定义说明'
        if 自身.自定义 is not None:
            return 自身.自定义
        数据=自身.当前数据()
        if isinstance(数据,dict) and isinstance(数据.get('customLocation'),str):
            return 数据['customLocation']
        return ''

    def 点动词(自身,动词):
        '按钮点击入口'

        def 点(事件=None):
            '跑这一动词'
            自身.跑(动词)

        return 点

    def 渲染(自身):
        '详情不合法时只留框架给的摘要'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        译=属性['t']
        自身.创建按钮=None
        详情=自身.当前详情()
        根=建(文档,'div',None)
        if 详情 is None:
            体=建(文档,'div','body')
            挂上(体,属性.get('summary'))
            根.appendChild(体)
            return 换根(自身,根)
        数据=自身.当前数据()
        决定=属性.get('decision') if isinstance(属性.get('decision'),dict) else None
        阶段=None if 决定 is None else 键于(阶段键,决定.get('phase'))
        忙=自身.待定 is not None
        位置=自身.当前自定义()
        槽=自身.当前槽()
        手写=自身.当前手写()
        可创建=自身.可创建()
        说明开=自身.当前说明开()
        已安装=阶段 in ('installed','kept')
        头=建(文档,'header','header')
        标题=建(文档,'span','heading')
        标题.appendChild(文档.createTextNode(译('heading')))
        信息按钮=按钮({
            'window':窗口,
            'variant':'ghost',
            'size':'sm',
            'className':'infoButton',
            'children':图标警告16({'window':窗口,'size':14}),
            'onClick':自身.点信息,
        }).渲染()
        标样式模块(信息按钮,样式模块)
        信息按钮.setAttribute('aria-label',译('creationInfo'))
        信息按钮.setAttribute('aria-expanded','true' if 说明开 else 'false')
        信息按钮.setAttribute('aria-controls',自身.信息标识)
        泡=提示泡({
            'window':窗口,
            'label':译('creationInfo'),
            'side':'top',
            'portal':True,
            'disabled':说明开,
            'children':信息按钮,
        }).渲染()
        标题.appendChild(泡)
        头.appendChild(标题)
        if 阶段 is not None:
            阶段文=建(文档,'span','phase')
            阶段文.setAttribute('role','status')
            阶段文.setAttribute('data-phase',阶段)
            阶段文.textContent=译(阶段)
            头.appendChild(阶段文)
        根.appendChild(头)
        if 说明开:
            说明=建(文档,'div','info')
            说明.id=自身.信息标识
            说明.setAttribute('role','note')
            for 键,强调 in (('creationMethod',False),('creationCost',True),('creationBackground',False)):
                段=文档.createElement('p')
                if 强调:
                    强=文档.createElement('strong')
                    强.textContent=译(键)
                    段.appendChild(强)
                else:
                    段.textContent=译(键)
                说明.appendChild(段)
            if isinstance(数据,dict) and 数据.get('bundleName') is not None:
                保留段=文档.createElement('p')
                保留段.textContent=译('sourceRetained')
                说明.appendChild(保留段)
            根.appendChild(说明)
        体=建(文档,'div','body')
        挂上(体,属性.get('summary'))
        if isinstance(详情.get('initialContent'),str):
            内容=建(文档,'div','content')
            标签=建(文档,'span','contentLabel')
            标签.textContent=译('initialContent')
            内容.appendChild(标签)
            折叠类=属性.get('Folded')
            if 折叠类 is not None:
                折叠=折叠类({
                    'window':窗口,
                    'text':详情['initialContent'],
                    'expandLabel':译('expandContent'),
                    'collapseLabel':译('collapseContent'),
                })
                挂上(内容,折叠)
            体.appendChild(内容)
        if isinstance(数据,dict) and 数据.get('application') not in (None,'applied') and 阶段!='failed':
            应用状态=建(文档,'p','status')
            应用状态.setAttribute('role','status')
            应用状态.textContent=译(应用文案[数据['application']])
            体.appendChild(应用状态)
        if 自身.错误 is not None:
            警报=建(文档,'p','status')
            警报.setAttribute('role','alert')
            警报.textContent=译(自身.错误)
            体.appendChild(警报)
        if 可创建:
            控件=建(文档,'div','controls')
            行=建(文档,'div','locationRow')
            位置标签=建(文档,'span','locationLabel')
            位置标签.textContent=译('location')
            行.appendChild(位置标签)
            if 自身.位置 is None:
                自身.位置=位置选择({
                    'window':窗口,'value':位置,'disabled':忙,'onChange':自身.设选中,'t':译,
                })
            else:
                自身.位置.更新({
                    'window':窗口,'value':位置,'disabled':忙,'onChange':自身.设选中,'t':译,
                })
            挂上(行,自身.位置)
            控件.appendChild(行)
            if 位置=='custom':
                自定义盒=建(文档,'div','customLocation')
                自定义标签=建(文档,'label','locationLabel')
                自定义标签.setAttribute('for',自身.自定义标识)
                自定义标签.textContent=译('customLabel')
                输入=文档.createElement('textarea')
                输入.id=自身.自定义标识
                输入.value=手写
                输入.rows=2
                输入.maxLength=1000
                输入.disabled=忙
                输入.placeholder=译('customPlaceholder')
                输入.addEventListener('input',自身.改自定义)
                自定义盒.appendChild(自定义标签)
                自定义盒.appendChild(输入)
                控件.appendChild(自定义盒)
            脚=建(文档,'footer','footer')
            动作=建(文档,'div','actions')
            忽略=按钮({
                'window':窗口,'variant':'ghost','size':'sm','disabled':忙,
                'children':译('dismiss'),'onClick':自身.点动词('dismiss'),
            }).渲染()
            创建文='starting' if 自身.待定=='create' else ('create' if 决定 is None else 'retry')
            不能创建=忙 or (位置=='custom' and 手写.strip()=='')
            创建=按钮({
                'window':窗口,'variant':'primary','size':'sm','disabled':不能创建,
                'children':译(创建文),'onClick':自身.点动词('create'),
            }).渲染()
            标样式模块(忽略,样式模块)
            标样式模块(创建,样式模块)
            自身.创建按钮=创建
            动作.appendChild(忽略)
            动作.appendChild(创建)
            脚.appendChild(动作)
            控件.appendChild(脚)
            体.appendChild(控件)
        else:
            说明行=建(文档,'p','description')
            位置文=数据.get('customLocation') if isinstance(数据,dict) and 数据.get('customLocation') is not None else 译(槽)
            说明行.textContent=译('location')+' · '+str(位置文)
            体.appendChild(说明行)
        if 阶段=='creating':
            取消脚=建(文档,'footer','footer')
            取消文='cancelling' if 自身.待定=='cancel' else 'cancel'
            取消=按钮({
                'window':窗口,'variant':'ghost','size':'sm','disabled':忙,
                'children':译(取消文),'onClick':自身.点动词('cancel'),
            }).渲染()
            标样式模块(取消,样式模块)
            取消脚.appendChild(取消)
            体.appendChild(取消脚)
        if 已安装:
            安装脚=建(文档,'footer','footer')
            范围=建(文档,'span','scope')
            范围.textContent=译('scope')
            安装脚.appendChild(范围)
            安装动作=建(文档,'div','actions')
            撤销=按钮({
                'window':窗口,'variant':'ghost','size':'sm','disabled':忙,
                'children':译('undo'),'onClick':自身.点动词('undo'),
            }).渲染()
            标样式模块(撤销,样式模块)
            安装动作.appendChild(撤销)
            if 阶段!='kept':
                保留=按钮({
                    'window':窗口,'variant':'primary','size':'sm','disabled':忙,
                    'children':译('keep'),'onClick':自身.点动词('keep'),
                }).渲染()
                标样式模块(保留,样式模块)
                安装动作.appendChild(保留)
            安装脚.appendChild(安装动作)
            体.appendChild(安装脚)
        if 阶段=='removed':
            恢复脚=建(文档,'footer','footer')
            恢复动作=建(文档,'div','actions')
            恢复文='restoring' if 自身.待定=='restore' else 'restore'
            恢复=按钮({
                'window':窗口,'variant':'primary','size':'sm','disabled':忙,
                'children':译(恢复文),'onClick':自身.点动词('restore'),
            }).渲染()
            标样式模块(恢复,样式模块)
            恢复动作.appendChild(恢复)
            恢复脚.appendChild(恢复动作)
            体.appendChild(恢复脚)
        根.appendChild(体)
        return 换根(自身,根)
