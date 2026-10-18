'文件和目录共用的分体按钮：默认动作、应用菜单、这一次失败的提示。'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块
from ...ui_基础界面组件.菜单 import 菜单
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.吐司 import 吐司
from ...ui_基础界面组件.icons import (
    图标下chevron14,
    图标开文件夹线16,
    图标右上16,
    图标警告16,
)
from .文案 import 中文
from .控制器 import 等到

__all__=['套应用','应用图标','打开目标按钮']

样式路径=os.path.join(os.path.dirname(__file__),'打开目标按钮.module.css')
样式模块='OpenTargetButton'


def 套应用(模板,应用名):
    '把文案里的 {app} 换成应用名'
    return 模板.replace('{app}',应用名)


class 应用图标:
    '一张应用图。加载失败就换成右上箭头'
    def __init__(自身,窗口,源,尺寸=14):
        '记下地址和边长'
        自身.窗口=窗口
        自身.源=源
        自身.尺寸=尺寸
        自身.已失败=False
        自身.根=None

    def 标记失败(自身,事件):
        '这张图加载失败'
        if 自身.已失败:
            return
        自身.已失败=True
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        新=自身.渲染()
        if 父 is not None and 旧 is not None and 旧 is not 新:
            父.replaceChild(新,旧)

    def 渲染(自身):
        '真图或右上箭头'
        if 自身.源 is None or 自身.已失败:
            自身.根=图标右上16({'window':自身.窗口,'size':自身.尺寸})
            return 自身.根
        文档=自身.窗口.document
        图=文档.createElement('img')
        图.className='appIcon'
        标样式模块(图,样式模块)
        图.setAttribute('src',自身.源)
        图.setAttribute('alt','')
        图.setAttribute('width',str(自身.尺寸))
        图.setAttribute('height',str(自身.尺寸))
        图.setAttribute('draggable','false')
        图.addEventListener('error',自身.标记失败)
        自身.根=图
        return 图


class 打开目标按钮:
    '文件和目录用同一套分体按钮。文件的显示位置永远在菜单最后，只有没有应用时才当成默认'
    def __init__(自身,属性=None):
        '记下 props。有窗口就画出按钮'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.菜单开=False
        自身.待定=False
        自身.在飞=False
        自身.代次=0
        自身.要聚焦=False
        自身.横幅=None
        自身.横幅节点=None
        自身.横幅已画=None
        自身.横幅序号=0
        自身.图标表={}
        自身.偏好=None
        自身.揭示默认=False
        自身.窗口=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上新的 props。路径变了就丢掉这一次的菜单和提示'
        旧=自身.属性.get('absolutePath') if isinstance(自身.属性,dict) else None
        自身.属性=属性 if isinstance(属性,dict) else {}
        新=自身.属性.get('absolutePath')
        if 新!=旧:
            自身.代次+=1
            自身.菜单开=False
            自身.待定=False
            自身.在飞=False
            自身.要聚焦=False
            自身.横幅=None
            自身.图标表={}

    def 取图标(自身,源,尺寸):
        '同一地址和边长共用失败状态'
        键=(源,尺寸)
        图标=自身.图标表.get(键)
        if 图标 is None:
            图标=应用图标(自身.窗口,源,尺寸)
            自身.图标表[键]=图标
        else:
            图标.窗口=自身.窗口
            图标.尺寸=尺寸
        return 图标.渲染()

    def 跑(自身,操作):
        '先关上菜单，再执行这一次打开'
        自身.菜单开=False
        自身.行动(操作)

    def 行动(自身,操作):
        '同时只跑一次。失败句子用中文表原文'
        if 自身.在飞:
            return
        自身.在飞=True
        代=自身.代次
        自身.待定=True
        自身.渲染()
        失败=None
        try:
            失败=等到(自身.属性['execute'](操作))
        except Exception:
            失败=None
        if 自身.代次!=代:
            return
        自身.在飞=False
        自身.待定=False
        if 失败=='revealError':
            自身.横幅序号+=1
            自身.横幅={'seq':自身.横幅序号,'text':中文['path.revealError']}
        elif 失败 is not None:
            自身.横幅序号+=1
            自身.横幅={'seq':自身.横幅序号,'text':中文['path.openError']}
        自身.渲染()

    def 按主钮(自身,事件):
        '主钮：没有应用就显示位置，否则打开默认或当前点名的应用'
        偏好=自身.偏好
        if 自身.揭示默认:
            自身.跑({'kind':'reveal'})
            return
        if 偏好 is not None and 偏好['id']!=自身.属性.get('defaultId'):
            自身.跑({'kind':'application','id':偏好['id']})
            return
        自身.跑({'kind':'default'})

    def 按箭头(自身,事件):
        '打开菜单前刷新关联。再点一次关上'
        if 自身.菜单开 is not True:
            刷新=自身.属性.get('refresh')
            if callable(刷新):
                刷新()
            自身.要聚焦=True
        自身.菜单开=自身.菜单开 is not True
        自身.渲染()

    def 选定菜单(自身,标识):
        '菜单项变成显示位置，或打开 id 里点名的应用'
        if 标识=='reveal':
            自身.跑({'kind':'reveal'})
            return
        自身.跑({'kind':'application','id':str(标识)[4:]})

    def 关菜单(自身):
        '菜单要求关闭'
        if 自身.菜单开 is not True:
            return
        自身.菜单开=False
        自身.渲染()

    def 关掉这条(自身,序号):
        '只关掉这一次提示。更晚的提示留着'
        if 自身.横幅 is None or 自身.横幅['seq']!=序号:
            return
        自身.横幅=None
        if 自身.横幅节点 is not None:
            自身.横幅节点.remove()
            自身.横幅节点=None
        自身.渲染()

    def 渲染(自身):
        '画出分体按钮、菜单和失败提示'
        属性=自身.属性
        窗口=属性['window']
        自身.窗口=窗口
        文档=窗口.document
        注入模块样式文件(文档,'打开目标按钮样式',样式路径,样式模块)
        种类=属性['kind']
        应用表=属性['applications'] if isinstance(属性.get('applications'),list) else list(属性.get('applications') or [])
        显眼=属性.get('prominent') is True
        边=18 if 显眼 else 13
        偏好=None
        for 应用 in 应用表:
            if 应用['id']==属性.get('defaultId'):
                偏好=应用
                break
        if 种类=='file' and 偏好 is None and len(应用表)>0:
            偏好=应用表[0]
        自身.偏好=偏好
        禁用=自身.待定 or 属性.get('busy') is True or 属性.get('loading') is True
        文件额外=1 if 种类=='file' else 0
        有菜单=属性.get('loading') is True or bool(属性.get('failed')) or (len(应用表)+文件额外)>1
        揭示默认=种类=='file' and 偏好 is None and 属性.get('loading') is not True
        自身.揭示默认=揭示默认
        if 偏好 is None:
            主标签=中文['path.reveal']
        else:
            主标签=套应用(中文['open.title'],偏好['name'])
        快捷=属性.get('shortcut')
        提示=主标签
        快捷属性=None
        if isinstance(快捷,dict):
            键表=快捷.get('keys')
            if isinstance(键表,(list,tuple)) and len(键表)>0:
                提示=提示+' '+' '.join(str(键) for 键 in 键表)
            快捷属性=快捷.get('aria')
        文件紧凑=种类=='file' and 显眼 is not True
        if 属性.get('loading') is True and 偏好 is None:
            图标节点=模块节点(文档,'span',样式模块,'skeleton')
            图标节点.setAttribute('data-open-target-skeleton','')
            图标节点.setAttribute('aria-hidden','true')
            图标节点.style.setProperty('width',str(边)+'px')
            图标节点.style.setProperty('height',str(边)+'px')
        elif 揭示默认:
            图标节点=图标开文件夹线16({'window':窗口,'size':边})
        else:
            源=None if 偏好 is None else 偏好.get('icon')
            图标节点=自身.取图标(源,边)
        主钮=模块节点(文档,'button',样式模块,'main')
        主钮.type='button'
        主钮.disabled=禁用
        if 显眼 is not True:
            主钮.setAttribute('aria-label',主标签)
        if isinstance(快捷属性,str) and 快捷属性!='':
            主钮.setAttribute('aria-keyshortcuts',快捷属性)
        if 文件紧凑:
            主钮.setAttribute('data-open-path-open','')
        if 显眼:
            主钮.setAttribute('data-open-path-unpreviewable','')
        主钮.addEventListener('click',自身.按主钮)
        主钮.appendChild(图标节点)
        if 显眼:
            if 揭示默认:
                主钮.appendChild(文档.createTextNode(中文['path.reveal']))
            else:
                主钮.appendChild(文档.createTextNode(中文['path.open']))
        泡=提示泡({
            'window':窗口,
            'side':'bottom',
            'label':提示,
            'children':主钮,
        }).渲染()
        分=模块节点(文档,'div',样式模块,'split')
        分.setAttribute('data-open-target',种类)
        分.setAttribute('data-size','large' if 显眼 else 'compact')
        分.setAttribute('data-state','busy' if 禁用 else 'idle')
        if 文件紧凑:
            分.setAttribute('data-open-path','')
        分.appendChild(泡)
        if 有菜单:
            箭头尺寸=14 if 显眼 else 10
            箭头钮=模块节点(文档,'button',样式模块,'chevron')
            箭头钮.type='button'
            箭头钮.disabled=禁用
            箭头钮.setAttribute('aria-haspopup','menu')
            箭头钮.setAttribute('aria-expanded','true' if 自身.菜单开 and 禁用 is False else 'false')
            箭头钮.setAttribute('aria-label',中文['path.more'])
            if 文件紧凑:
                箭头钮.setAttribute('data-open-path-more','')
            箭头钮.addEventListener('click',自身.按箭头)
            箭头钮.appendChild(图标下chevron14({'window':窗口,'size':箭头尺寸}))
            分.appendChild(箭头钮)
        条目=[]
        for 应用 in 应用表:
            if 偏好 is not None and 应用['id']==偏好['id']:
                标签=套应用(中文['path.appDefault'],应用['name'])
            else:
                标签=应用['name']
            条目.append({'id':'app:'+应用['id'],'label':标签})
        if 属性.get('failed'):
            条目.append({
                'id':'unavailable',
                'label':中文['path.appsError'],
                'disabled':True,
            })
        脚=[]
        if 种类=='file':
            if 揭示默认:
                脚标签=套应用(中文['path.appDefault'],中文['path.reveal'])
            else:
                脚标签=中文['path.reveal']
            脚.append({'id':'reveal','label':脚标签})
        菜单开=自身.菜单开 is True and 禁用 is False and 有菜单 is True
        菜单根=菜单({
            'window':窗口,
            'className':'menuAnchor',
            'open':菜单开,
            'align':'end',
            'items':条目,
            'footer':脚,
            'onSelect':自身.选定菜单,
            'onClose':自身.关菜单,
            'anchor':分,
        }).渲染()
        菜单根.setAttribute('data-dsh-css',样式模块)
        if 菜单开:
            列=菜单根.querySelector('.菜单列')
            if 列 is not None:
                钮表=列.querySelectorAll('button')
                序号=0
                for 应用 in 应用表:
                    if 序号>=len(钮表):
                        break
                    图=自身.取图标(应用.get('icon'),14)
                    钮表[序号].insertBefore(图,钮表[序号].firstChild)
                    序号+=1
                if 属性.get('failed'):
                    序号+=1
                if 种类=='file' and 序号<len(钮表):
                    钮表[序号].insertBefore(
                        图标开文件夹线16({'window':窗口}),
                        钮表[序号].firstChild,
                    )
                if 自身.要聚焦:
                    首=列.querySelector('button:not([disabled])')
                    if 首 is not None:
                        首.focus()
                    自身.要聚焦=False
        if 自身.横幅节点 is not None and 自身.横幅节点.parentNode is not None:
            自身.横幅节点.remove()
        提示节点=None
        if 自身.横幅 is not None:
            序号=自身.横幅['seq']
            if 自身.横幅节点 is None or 自身.横幅已画!=序号:
                if 自身.横幅节点 is not None:
                    自身.横幅节点.remove()

                def 完成(序号=序号):
                    '这条提示的时间到了'
                    自身.关掉这条(序号)

                条=吐司({
                    'window':窗口,
                    'text':自身.横幅['text'],
                    'onDone':完成,
                }).渲染()
                条.insertBefore(图标警告16({'window':窗口,'size':16}),条.firstChild)
                自身.横幅节点=条
                自身.横幅已画=序号
            提示节点=自身.横幅节点
        else:
            自身.横幅节点=None
            自身.横幅已画=None
        旧=自身.根
        壳=文档.createElement('div')
        壳.style.setProperty('display','contents')
        壳.appendChild(菜单根)
        if 提示节点 is not None:
            壳.appendChild(提示节点)
        if 旧 is not None and getattr(旧,'parentNode',None) is not None:
            旧.parentNode.replaceChild(壳,旧)
        elif 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(壳)
        自身.根=壳
        return 壳

    def __call__(自身,属性=None):
        '再次交给槽位时刷新'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
