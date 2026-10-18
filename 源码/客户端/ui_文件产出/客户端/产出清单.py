'收口回合上的改动卡和已声明文件'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 描边图标,图标下箭头描边常规
from ...ui_基础界面组件.按钮 import 按钮
from ..改动 import 改动摘要网址
from ..已呈现 import 已呈现文件网址
from .改动文件 import 改动文件
from .已呈现文件卡 import 已呈现文件卡
from .回合产出 import 收口改动,收口已呈现
from .文案 import 中文,填入

__all__=['选出交付物','产出清单尾','产出清单']

样式模块='Deliverables'
样式路径=os.path.join(os.path.dirname(__file__),'产出清单.module.css')
折叠已呈现上限=4


def 确保样式(文档):
    '交付清单样式只插一次'
    注入模块样式文件(文档,'dsh-deliverables',样式路径,样式模块)


def 元素(文档,标签,类名=None):
    '带官方类名和样式模块'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)


def 上箭头(窗口):
    '上游 IconChevronUpOutlineRegular。基础界面组件还没有这个公开函数'
    return 描边图标({'window':窗口,'size':14},'0 0 16 16',[
        'M12 10L8.70711 6.70711C8.31658 6.31658 7.68342 6.31658 7.29289 6.70711L4 10',
    ],14,1)


def 选出交付物(所有者):
    '有改动宣告或已声明文件才出现'
    改动=收口改动(所有者)
    已呈现=收口已呈现(所有者)
    if 改动 is None and len(已呈现)==0:
        return None
    return {'changes':改动,'presented':已呈现}


def 订(钩,回调):
    '钩子有订阅才订上'
    订源=getattr(钩,'_subscribe',None)
    if not callable(订源):
        return None
    return 订源(回调)


def 挂上(父,节点):
    '节点或带渲染的界面'
    if 节点 is None:
        return
    if isinstance(节点,(list,tuple)):
        for 项 in 节点:
            挂上(父,项)
        return
    if hasattr(节点,'tagName'):
        父.appendChild(节点)
        return
    if hasattr(节点,'渲染'):
        画出=节点.渲染()
        if 画出 is not None and hasattr(画出,'tagName'):
            父.appendChild(画出)


class 产出清单:
    '改动卡，以及已声明文件和它们的打开状态'
    def __init__(自身,属性):
        '记下匹配结果'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.展开=False
        自身.绘制中=False
        自身.待重画=False
        自身.已订=False
        自身.退订=[]
        自身.改动卡=None
        自身.文件卡={}

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '宿主还提供摘要并且里面有文件才画改动卡'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            匹配=属性['matched']
            会话标识=属性.get('sessionId')

            def 原样(值):
                '整份快照'
                return 值

            def 工作目录(状态,会话标识=会话标识):
                '这一会话的 cwd'
                if not isinstance(状态,dict):
                    return None
                按号=状态.get('byId')
                if not isinstance(按号,dict):
                    return None
                会话=按号.get(会话标识)
                if not isinstance(会话,dict):
                    return None
                return 会话.get('cwd')

            用差异开关=属性.get('useShowCodeDiff')
            用会话=属性.get('useSessions')
            用打开=属性.get('usePresentedOpen')
            用宿主=属性.get('usePresentedHost')
            用摘要=属性.get('useChangesSummary')
            显示差异=用差异开关(原样) if callable(用差异开关) else False
            目录=用会话(工作目录) if callable(用会话) else None
            打开态=用打开(原样) if callable(用打开) else {}
            宿主=用宿主(原样) if callable(用宿主) else None
            if not isinstance(打开态,dict):
                打开态={}
            宣告=匹配.get('changes') if 显示差异 else None

            def 选摘要(值,宣告=宣告,会话标识=会话标识):
                '这一宣告的摘要'
                if 宣告 is None or not isinstance(值,dict):
                    return None
                return 值.get(改动摘要网址(会话标识,宣告['seq']))

            摘要=用摘要(选摘要) if callable(用摘要) else None
            if 宣告 is not None and 摘要 is None and callable(属性.get('loadChangesSummary')):
                属性['loadChangesSummary'](会话标识,宣告['seq'])
                if callable(用摘要):
                    摘要=用摘要(选摘要)
            改动=None
            if 宣告 is not None and isinstance(摘要,dict) and isinstance(摘要.get('files'),list) and len(摘要['files'])>0:
                改动={'seq':宣告['seq'],**摘要}
            if 宿主 is None and callable(属性.get('reloadPresentedHost')):
                属性['reloadPresentedHost']()
                if callable(用宿主):
                    宿主=用宿主(原样)
            已呈现=匹配.get('presented') or []
            可折=len(已呈现)>折叠已呈现上限
            可见=已呈现[:折叠已呈现上限] if 可折 and not 自身.展开 else 已呈现
            if 自身.根 is None:
                自身.根=文档.createElement('div')
                自身.根.style.display='contents'
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
            if 改动 is not None:
                if 自身.改动卡 is None:
                    自身.改动卡=改动文件({'window':窗口})
                def 打开审阅(下标,改动=改动,会话标识=会话标识,打开=属性.get('openChangesReview')):
                    '右侧边栏打开这一轮，并落到这个下标'
                    if callable(打开):
                        打开({'sessionId':会话标识,'seq':改动['seq'],'turn':改动['turn']},下标)
                自身.改动卡.更新({
                    'window':窗口,
                    'changes':改动,
                    'cwd':目录,
                    'sessionId':会话标识,
                    'useChangesDiff':属性.get('useChangesDiff'),
                    'loadChangesDiff':属性.get('loadChangesDiff'),
                    'openReview':打开审阅,
                })
                自身.根.appendChild(自身.改动卡.渲染())
            if len(已呈现)>0:
                盒=元素(文档,'div','root')
                if 改动 is not None:
                    盒.setAttribute('data-after-changes','true')
                if 宿主=='error':
                    状态行=元素(文档,'div','hostStatus')
                    字=文档.createElement('span')
                    字.textContent=中文['presented.hostError']
                    状态行.appendChild(字)

                    def 重读宿主(重读=属性.get('reloadPresentedHost')):
                        '再读桌面信息'
                        if callable(重读):
                            重读()

                    状态行.appendChild(按钮({
                        'window':窗口,
                        'size':'sm',
                        'onClick':重读宿主,
                        'children':中文['presented.retry'],
                    }).渲染())
                    盒.appendChild(状态行)
                elif 宿主 is not None and 宿主!='error' and not 宿主.get('available'):
                    不可用=元素(文档,'span','hostStatus')
                    不可用.textContent=中文['presented.unavailable']
                    盒.appendChild(不可用)
                行=元素(文档,'div','presented')
                行.setAttribute('data-presented-files-row','')
                if len(已呈现)==1:
                    行.setAttribute('data-single','true')
                留着=set()
                for 文件 in 可见:
                    键=str(文件['seq'])+':'+str(文件['index'])
                    留着.add(键)
                    网址=已呈现文件网址(会话标识,文件['seq'],文件['index'])
                    阶段=打开态.get(网址)
                    if 键 not in 自身.文件卡:
                        自身.文件卡[键]=已呈现文件卡({'window':窗口})
                    渲染槽=属性.get('renderSlot')
                    动作=None
                    if callable(渲染槽):
                        def 做动作(动作名,应用=None,文件=文件,打开=属性.get('openPresented'),会话标识=会话标识):
                            '打开或揭示这一份'
                            if callable(打开):
                                return 打开(会话标识,文件['seq'],文件['index'],动作名,应用)
                            return None
                        动作=渲染槽('deliverables.file.actions',{
                            'actionUrl':网址,
                            'available':宿主 is not None and 宿主!='error' and bool(宿主.get('available')),
                            'pending':阶段=='opening' or 阶段=='revealing',
                            'onAction':做动作,
                        })

                    def 预览(文件=文件,打开文件=属性.get('openFile')):
                        '侧栏打开这个路径'
                        if callable(打开文件):
                            打开文件(文件['path'])

                    卡=自身.文件卡[键]
                    卡.更新({
                        'window':窗口,
                        'file':文件,
                        'cwd':目录,
                        'phase':阶段,
                        'host':None if 宿主=='error' else 宿主,
                        'onPreview':预览,
                        'actions':动作,
                    })
                    行.appendChild(卡.渲染())
                for 键 in list(自身.文件卡):
                    if 键 not in 留着:
                        旧卡=自身.文件卡.pop(键)
                        if 旧卡.根 is not None:
                            旧卡.根.remove()
                盒.appendChild(行)
                if 可折:
                    折=元素(文档,'button','toggle')
                    折.setAttribute('type','button')
                    折.setAttribute('aria-expanded','true' if 自身.展开 else 'false')
                    if 自身.展开:
                        折.setAttribute('aria-label',填入(中文['presented.collapseAria'],{'count':len(已呈现)}))
                    else:
                        折.setAttribute('aria-label',填入(中文['presented.expandAria'],{'count':len(已呈现)}))

                    def 点折(事件):
                        '展开或收起交付文件'
                        自身.展开=not 自身.展开
                        自身.渲染()

                    折.addEventListener('click',点折)
                    字=文档.createElement('span')
                    if 自身.展开:
                        字.textContent=中文['presented.collapse']
                        折.appendChild(字)
                        折.appendChild(上箭头(窗口))
                    else:
                        字.textContent=填入(中文['presented.all'],{'count':len(已呈现)})
                        折.appendChild(字)
                        折.appendChild(图标下箭头描边常规({'window':窗口}))
                    盒.appendChild(折)
                自身.根.appendChild(盒)
            if not 自身.已订:
                def 变更():
                    '快照变了就重画'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 钩 in (用差异开关,用会话,用打开,用宿主,用摘要,属性.get('useChangesDiff')):
                    退=订(钩,变更)
                    if 退 is not None:
                        自身.退订.append(退)
                自身.已订=True
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根


活清单={}


class 产出清单尾:
    '回合尾登记的入口。没有改动也没有交付文件就不画'
    def __new__(类,属性):
        '同一会话同一序号复用清单，展开状态还在'
        属性=属性 if isinstance(属性,dict) else {}
        匹配=选出交付物(属性)
        键=str(属性.get('sessionId'))+':'+str(属性.get('seq'))
        if 匹配 is None:
            旧=活清单.pop(键,None)
            if 旧 is not None and 旧.根 is not None and 旧.根.parentNode is not None:
                旧.根.remove()
            return None
        已有=活清单.get(键)
        if 已有 is not None:
            已有.更新({**属性,'matched':匹配})
            return 已有.渲染()
        清单=产出清单({**属性,'matched':匹配})
        活清单[键]=清单
        return 清单.渲染()
