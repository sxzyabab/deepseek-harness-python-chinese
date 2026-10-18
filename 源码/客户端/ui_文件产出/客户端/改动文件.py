'一轮改动：单文件卡片，或多文件抬头加折叠列表'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 描边图标,图标下箭头描边常规
from ...ui_基础界面组件.文件类型图标 import 文件类型图标
from ...ui_基础界面组件.悬停卡 import 悬停卡
from ....工具.工作区路径 import 解析工作区路径
from ..改动 import 改动对比网址
from ..已呈现 import 路径末段
from .产出文件 import 产出文件
from .文案 import 中文,填入

__all__=['改动文件']

样式模块='ChangedFiles'
对比样式='FileDiff'
样式路径=os.path.join(os.path.dirname(__file__),'改动文件.module.css')
对比样式路径=os.path.join(os.path.dirname(__file__),'产出文件.module.css')
折叠行数=4
标识盒=[0]


def 确保样式(文档):
    '改动卡和预览里的对比样式各插一次'
    注入模块样式文件(文档,'dsh-changed-files',样式路径,样式模块)
    注入模块样式文件(文档,'dsh-file-diff',对比样式路径,对比样式)


def 元素(文档,标签,类名=None,模块=None):
    '带官方类名。模块缺省是改动卡'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块 if 模块 is None else 模块)


def 分组(数):
    '按 en-US 给行数加千分位'
    return format(int(数),',')


def 上箭头(窗口):
    '上游 IconChevronUpOutlineRegular。基础界面组件还没有这个公开函数'
    return 描边图标({'window':窗口,'size':14},'0 0 16 16',[
        'M12 10L8.70711 6.70711C8.31658 6.31658 7.68342 6.31658 7.29289 6.70711L4 10',
    ],14,1)


class 改动计数:
    '增加和删除的行数'
    def __init__(自身,属性):
        '记下行数'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '两个相邻的数字'
        文档=自身.属性['window'].document
        盒=文档.createDocumentFragment()
        增=元素(文档,'span','added')
        增.textContent=填入(中文['changes.added'],{'count':分组(自身.属性.get('added') or 0)})
        删=元素(文档,'span','deleted')
        删.textContent=填入(中文['changes.deleted'],{'count':分组(自身.属性.get('deleted') or 0)})
        盒.appendChild(增)
        盒.appendChild(删)
        自身.根=盒
        return 盒


class 改动文件预览:
    '悬停卡打开时才读对比'
    def __init__(自身,属性):
        '记下坐标'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.对比=None
        自身.绘制中=False
        自身.待重画=False
        自身.已订=False
        自身.退订=None

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '路径在抬头，下面是对比'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            网址=改动对比网址(属性['sessionId'],属性['seq'],属性['index'])

            def 选对比(值,网址=网址):
                '这一份对比'
                if not isinstance(值,dict):
                    return None
                return 值.get(网址)

            用对比=属性.get('useChangesDiff')
            状态=用对比(选对比) if callable(用对比) else None
            if 状态 is None and callable(属性.get('loadChangesDiff')):
                属性['loadChangesDiff'](属性['sessionId'],属性['seq'],属性['index'])
                if callable(用对比):
                    状态=用对比(选对比)
            if 自身.根 is None:
                自身.根=元素(文档,'div','preview')
                自身.根.setAttribute('data-changes-hover-preview','')
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
            内=元素(文档,'div','root',对比样式)
            头=元素(文档,'div','header',对比样式)
            路径=元素(文档,'span','previewPath')
            路径.setAttribute('data-changes-preview-path','')
            路径.textContent=属性.get('display') or ''
            头.appendChild(路径)
            内.appendChild(头)
            if 自身.对比 is None:
                自身.对比=产出文件({'window':窗口})

            def 重试(属性=属性):
                '再读这一份对比'
                读=属性.get('loadChangesDiff')
                if callable(读):
                    读(属性['sessionId'],属性['seq'],属性['index'])

            自身.对比.更新({
                'window':窗口,
                'state':状态,
                'split':False,
                'wrap':False,
                'retry':重试,
            })
            内.appendChild(自身.对比.渲染())
            自身.根.appendChild(内)
            if not 自身.已订 and callable(getattr(用对比,'_subscribe',None)):
                def 变更():
                    '对比到了就重画'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                自身.退订=用对比._subscribe(变更)
                自身.已订=True
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根


class 改动文件:
    '抬头打开审阅。单文件只留抬头，多文件可折叠'
    def __init__(自身,属性):
        '记下摘要'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.展开=False
        自身.绘制中=False
        自身.待重画=False
        标识盒[0]+=1
        自身.路径标识='改动路径-'+str(标识盒[0])

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '单文件或列表'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            改动=属性['changes']
            文件表=改动.get('files') or []
            单文件=文件表[0] if 改动.get('total')==1 and len(文件表)>0 else None
            可折=len(文件表)>折叠行数
            行表=文件表[:折叠行数] if 可折 and not 自身.展开 else 文件表
            if 自身.根 is None:
                自身.根=元素(文档,'div','card')
                自身.根.setAttribute('data-changed-files','')
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
            if 单文件 is None:
                自身.根.removeAttribute('data-single')
            else:
                自身.根.setAttribute('data-single','true')

            def 打开(下标,打开审阅=属性.get('openReview')):
                '打开这一轮审阅并定位到这个文件'
                def 点击(事件):
                    '交给审阅'
                    if callable(打开审阅):
                        打开审阅(下标)
                return 点击

            def 抬头(无障碍,描述标识):
                '卡片抬头'
                钮=元素(文档,'button','header')
                钮.setAttribute('type','button')
                钮.setAttribute('aria-label',无障碍)
                if 描述标识 is not None:
                    钮.setAttribute('aria-describedby',描述标识)
                钮.addEventListener('click',打开(0))
                砖=元素(文档,'span','tile')
                if 单文件 is None:
                    砖.appendChild(文件类型图标({'window':窗口,'kind':'code','size':20}).渲染())
                else:
                    砖.appendChild(文件类型图标({'window':窗口,'path':单文件['path'],'size':20}).渲染())
                钮.appendChild(砖)
                题组=元素(文档,'span','titles')
                题=元素(文档,'span','title')
                if 单文件 is None:
                    题.textContent=填入(中文['changes.title'],{'count':str(改动.get('total') or 0)})
                else:
                    题.textContent=填入(中文['changes.singleTitle'],{'name':路径末段(单文件['path'])})
                统计=元素(文档,'span','stat')
                数盒=元素(文档,'span','statCounts')
                if 单文件 is not None and 单文件.get('binary') is True:
                    数盒.textContent=中文['changes.binary']
                elif 单文件 is not None and 单文件.get('oversized') is True:
                    数盒.textContent=中文['changes.oversized']
                else:
                    数盒.appendChild(改动计数({
                        'window':窗口,
                        'added':改动.get('added') or 0,
                        'deleted':改动.get('deleted') or 0,
                    }).渲染())
                提示=元素(文档,'span','previewHint')
                提示.textContent=中文['presented.preview']
                统计.appendChild(数盒)
                统计.appendChild(提示)
                题组.appendChild(题)
                题组.appendChild(统计)
                钮.appendChild(题组)
                return 钮

            if 单文件 is None:
                自身.根.appendChild(抬头(中文['changes.openReview'],None))
                列表=元素(文档,'ul','list')
                下标=0
                for 文件 in 行表:
                    项=文档.createElement('li')
                    描述标识=自身.路径标识+'-'+str(下标)
                    行钮=元素(文档,'button','row')
                    行钮.setAttribute('type','button')
                    行钮.setAttribute('aria-label',填入(中文['changes.viewDiff'],{'name':文件.get('display') or ''}))
                    行钮.setAttribute('aria-describedby',描述标识)
                    行钮.addEventListener('click',打开(下标))
                    路径=元素(文档,'span','path')
                    路径.textContent=文件.get('display') or ''
                    计数=元素(文档,'span','counts')
                    if 文件.get('binary') is True:
                        计数.textContent=中文['changes.binary']
                    elif 文件.get('oversized') is True:
                        计数.textContent=中文['changes.oversized']
                    else:
                        计数.appendChild(改动计数({
                            'window':窗口,
                            'added':文件.get('added') or 0,
                            'deleted':文件.get('deleted') or 0,
                        }).渲染())
                    行钮.appendChild(路径)
                    行钮.appendChild(计数)
                    预览=改动文件预览({
                        'window':窗口,
                        'sessionId':属性.get('sessionId'),
                        'seq':改动.get('seq'),
                        'index':下标,
                        'display':解析工作区路径(属性.get('cwd'),文件.get('path') or ''),
                        'useChangesDiff':属性.get('useChangesDiff'),
                        'loadChangesDiff':属性.get('loadChangesDiff'),
                    })
                    项.appendChild(悬停卡({
                        'window':窗口,
                        'variant':'preview',
                        'widthAnchorRef':自身.根,
                        'openDelayMs':500,
                        'anchor':行钮,
                        'content':预览,
                    }).渲染())
                    隐藏=元素(文档,'span')
                    隐藏.id=描述标识
                    隐藏.hidden=True
                    隐藏.textContent=解析工作区路径(属性.get('cwd'),文件.get('path') or '')
                    项.appendChild(隐藏)
                    列表.appendChild(项)
                    下标+=1
                自身.根.appendChild(列表)
            else:
                预览=改动文件预览({
                    'window':窗口,
                    'sessionId':属性.get('sessionId'),
                    'seq':改动.get('seq'),
                    'index':0,
                    'display':解析工作区路径(属性.get('cwd'),单文件.get('path') or ''),
                    'useChangesDiff':属性.get('useChangesDiff'),
                    'loadChangesDiff':属性.get('loadChangesDiff'),
                })
                自身.根.appendChild(悬停卡({
                    'window':窗口,
                    'variant':'preview',
                    'widthAnchorRef':自身.根,
                    'openDelayMs':500,
                    'anchor':抬头(填入(中文['changes.viewDiff'],{'name':单文件.get('display') or ''}),自身.路径标识),
                    'content':预览,
                }).渲染())
                隐藏=元素(文档,'span')
                隐藏.id=自身.路径标识
                隐藏.hidden=True
                隐藏.textContent=解析工作区路径(属性.get('cwd'),单文件.get('path') or '')
                自身.根.appendChild(隐藏)
            if 可折:
                折=元素(文档,'button','toggle')
                折.setAttribute('type','button')
                折.setAttribute('aria-expanded','true' if 自身.展开 else 'false')
                if 自身.展开:
                    折.setAttribute('aria-label',填入(中文['changes.collapseAria'],{'count':str(len(文件表))}))
                else:
                    折.setAttribute('aria-label',填入(中文['changes.expandAria'],{'count':str(len(文件表))}))

                def 点折(事件):
                    '展开或收起文件列表'
                    自身.展开=not 自身.展开
                    自身.渲染()

                折.addEventListener('click',点折)
                字=文档.createElement('span')
                if 自身.展开:
                    字.textContent=中文['changes.collapse']
                    折.appendChild(字)
                    折.appendChild(上箭头(窗口))
                else:
                    字.textContent=填入(中文['changes.all'],{'count':str(len(文件表))})
                    折.appendChild(字)
                    折.appendChild(图标下箭头描边常规({'window':窗口}))
                自身.根.appendChild(折)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
