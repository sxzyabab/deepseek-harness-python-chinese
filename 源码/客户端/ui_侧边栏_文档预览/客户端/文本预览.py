from ...模块.客户端.通告 import 取握手窗口
import os
from ....工具.工作区路径 import 路径展示拆分
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标刷新14,图标刷新16,图标暂停16,图标播放16
from ...ui_基础界面组件.文件类型图标 import 分类文件类型,文件类型图标
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.菜单 import 菜单
from .文案 import 中文,套入
from .失败行 import 失败行,空失败办法
from .远程过程调用 import 宿主文件
from .文档.注册表 import 匹配文档预览,二进制文档路径
from .文档.不可预览 import 不可预览二进制路径
from .文本 import 纯文本体标识
from .文本.行 import 已载页,最后一行,滚到行
from .加载指示器 import 加载指示器

__all__=['文本预览']

样式模块='text-preview'
不换行路径=(
    'M2 15H1V1H2V15Z',
    'M12.3535 7.64645C12.5487 7.84171 12.5487 8.15829 12.3535 8.35355L9.85352 10.8535L9.14648 10.1465L10.793 8.5H3.5V7.5H10.793L9.14648 5.85352L9.85352 5.14648L12.3535 7.64645Z',
    'M15 15H14V1H15V15Z',
)
换行路径=(
    'M10.9999 8C10.9999 6.89543 10.1046 6 9 6H4.5V5H9C10.6568 5 11.9999 6.34315 11.9999 8C11.9999 9.65685 10.6568 11 9 11H6.20703L6.85351 11.6465L6.14648 12.3535L4.64652 10.8536C4.45126 10.6583 4.45126 10.3417 4.64652 10.1464L6.14648 8.64648L6.85351 9.35352L6.20703 10H9C10.1046 10 10.9999 9.10457 10.9999 8Z',
    'M2 15H1V1H2V15Z',
    'M15 15H14V1H15V15Z',
)

def 挂上(容器,结果):
    '把槽位出口里的节点挂进容器'
    if 结果 is None:
        return
    if getattr(结果,'nodeType',None) is not None or getattr(结果,'tagName',None) is not None:
        容器.appendChild(结果)
        return
    if isinstance(结果,(list,tuple)):
        for 项 in 结果:
            挂上(容器,项)

def 订(钩子,回调):
    '选择器钩子上挂着的订阅'
    退=getattr(钩子,'_subscribe',None)
    if callable(退):
        return 退(回调)
    return None

def 字形(文档,路径列):
    '换行按钮用的填色字形。共享图标表里没有这两枚'
    段=[]
    for 路径 in 路径列:
        段.append('<path d="'+路径+'" fill="currentColor"></path>')
    标=文档.createElement('span')
    标.innerHTML='<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">'+''.join(段)+'</svg>'
    return 标

class 文本预览:
    '右侧文本标签正文：路径、查看器、换行、重载，以及读到的内容或失败'
    def __init__(自身,属性=None):
        '记下 props。键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.绘制中=False
        自身.待重画=False
        自身.菜单开=False
        自身.滚动口=None
        自身.退订=[]
        自身.已订=False
        if 'useTabInfo' in 自身.属性 and 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 画路径(自身,文档,路径):
        '目录淡、文件名亮。悬停可见整段。共享路径标签尚未迁入时按同样结构画'
        拆=路径展示拆分(路径)
        外=模块节点(文档,'span',样式模块,'path')
        外.setAttribute('title',路径)
        外.setAttribute('data-path-label','')
        外.setAttribute('data-textpreview-path','')
        内=文档.createElement('span')
        if 拆['directory']!='':
            目录=文档.createElement('span')
            目录.textContent=拆['directory']
            内.appendChild(目录)
        名=文档.createElement('span')
        名.textContent=拆['name']
        内.appendChild(名)
        外.appendChild(内)
        def 核对(事件=None):
            '内层比外层宽时标上裁剪'
            if 内.offsetWidth>外.clientWidth:
                外.setAttribute('data-path-clipped','')
            else:
                外.removeAttribute('data-path-clipped')
        核对()
        观察类=getattr(文档.defaultView,'ResizeObserver',None)
        if 观察类 is not None:
            观察=观察类(核对)
            观察.observe(外)
            观察.observe(内)
        return 外

    def 渲染(自身):
        '拆掉旧树再画。读取和自动刷新写存储时先记下，画完再重入'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        写过=False
        try:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            属性=自身.属性
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
            文档=窗口.document
            注入模块样式文件(
                文档,
                '文本预览样式',
                os.path.join(os.path.dirname(__file__),'文本预览.module.css'),
                样式模块,
            )
            信息=属性['useTabInfo']()
            签=信息['tab']
            导航=签['navigation']
            信号=签['signal']
            元=属性['useResource'](签['contentId'])
            能读=元.get('status')!='none'
            文件=宿主文件(签['contentId'])
            def 取桶(快照):
                '这一标签的桶。还没有是 None'
                按=快照['byTab'] if isinstance(快照,dict) and 'byTab' in 快照 else {}
                return 按[签['id']] if 签['id'] in 按 else None
            状态=属性['useStore'](取桶)
            def 全量(值):
                '整份实现名单'
                return 值
            定义列表=属性['useDocumentPreviews'](全量)
            if 定义列表 is None:
                定义列表=[]
            不可看=不可预览二进制路径(文件['path'])
            匹配=匹配文档预览(定义列表,文件['path'])
            if len(匹配)>0 and 二进制文档路径(定义列表,文件['path']):
                候选=匹配
            elif len(匹配)==0 and 不可看:
                候选=匹配
            else:
                回落=None
                for 定义 in 定义列表:
                    if 定义['id']==纯文本体标识:
                        回落=定义
                        break
                候选=list(匹配) if 回落 is None else list(匹配)+[回落]
            选中=None
            显式=状态.get('rendererId') if isinstance(状态,dict) else None
            for 项 in 候选:
                if 项['id']==显式:
                    选中=项
                    break
            if 选中 is None and len(候选)>0:
                选中=候选[0]
            模式=选中['loading'] if 选中 is not None else None
            内容渲染器=选中['id'] if 模式=='renderer' and 选中 is not None else None
            状态模式=状态.get('mode','text-pages') if isinstance(状态,dict) else None
            已有渲染器=状态.get('contentRendererId') if isinstance(状态,dict) else None
            当前=状态 if isinstance(状态,dict) and 状态模式==模式 and 已有渲染器==内容渲染器 else None
            元值=元.get('value') if isinstance(元,dict) else None
            观察版本=元值.get('version') if isinstance(元值,dict) else None
            绝对=元值.get('absolutePath') if isinstance(元值,dict) else None
            if 绝对 is None and isinstance(当前,dict) and isinstance(当前.get('complete'),dict):
                绝对=当前['complete'].get('absolutePath')
            展示路径=绝对 if isinstance(绝对,str) else 文件['path']
            文件主={'absolutePath':绝对} if isinstance(绝对,str) else None
            参数=导航.get('params') if isinstance(导航,dict) else None
            行号=参数['line'] if isinstance(参数,dict) and 'line' in 参数 else None
            页表=当前['pages'] if isinstance(当前,dict) and 'pages' in 当前 else {}
            已载=已载页(页表)
            载到=最后一行(已载)
            if 模式=='renderer':
                有内容=isinstance(当前,dict) and 当前.get('version') is not None
            else:
                有内容=len(已载)>0 or (isinstance(当前,dict) and 当前.get('complete') is not None)
            动作=属性['actions']
            def 设空():
                '换实现时清掉上一份依赖'
                属性['setResources'](签['id'],[签['contentId']],信号)
            选中标识=选中['id'] if 选中 is not None else None
            设键=(签['id'],选中标识,签['contentId'])
            if getattr(自身,'上次设资源',None)!=设键:
                自身.上次设资源=设键
                设空()
            已开始=当前 is not None
            if not 已开始 and 能读 and 模式 is not None and 选中 is not None:
                写过=True
                if 模式=='text-pages':
                    属性['loadPage'](签['id'],文件,1,信号,观察版本)
                elif 模式=='bytes-complete':
                    属性['loadAll'](签['id'],文件,信号,观察版本)
                else:
                    属性['prepareRenderer'](签['id'],信号,选中['id'],观察版本)
            def 渲染器重载():
                '作废当前修订并让渲染器再加载'
                if 能读 and 选中 is not None:
                    属性['prepareRenderer'](签['id'],信号,选中['id'],观察版本,True)
            def 重载():
                '按当前模式重读'
                if not 能读:
                    return
                if 模式=='text-pages':
                    属性['reloadPages'](签['id'],文件,信号,观察版本)
                elif 模式=='bytes-complete':
                    属性['reloadAll'](签['id'],文件,信号,观察版本)
                else:
                    渲染器重载()
            版本变了=False
            if isinstance(当前,dict) and 当前.get('version') is not None and 观察版本 is not None:
                if 观察版本!=当前.get('version') and 观察版本!=当前.get('observedVersion'):
                    版本变了=True
            if isinstance(状态,dict) and 状态.get('resourcesDirty') is True:
                版本变了=True
            在载=isinstance(当前,dict) and 当前.get('loading') is True
            自动=isinstance(状态,dict) and 状态.get('autoRefresh') is True
            if 自动 and 版本变了 and 当前 is not None and not 在载 and 元.get('status')=='live':
                写过=True
                重载()
            if 签.get('actions') is not None and 'bindCommands' in 签['actions']:
                签['actions']['bindCommands']({'refresh':重载})
            if 选中 is None and 不可看:
                自身.根=自身.画不可预览(文档,窗口,签,展示路径,文件主)
            elif 状态 is None or 选中 is None:
                自身.根=自身.画等待(文档,窗口,元)
            else:
                自身.根=自身.画正文(
                    文档,窗口,签,信号,文件,状态,当前,选中,候选,模式,展示路径,文件主,
                    已载,载到,有内容,行号,能读,元,观察版本,版本变了,重载,渲染器重载,动作,
                )
            if 'parent' in 属性 and 属性['parent'] is not None and 自身.根 is not None:
                属性['parent'].appendChild(自身.根)
            if not 自身.已订:
                def 变更():
                    '快照变了就重画。节点已经不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        for 退 in 自身.退订:
                            if 退 is not None:
                                退()
                        自身.退订=[]
                        自身.已订=False
                        return
                    自身.渲染()
                for 钩名 in ('useTabInfo','useResource','useStore','useDocumentPreviews'):
                    if 钩名 in 属性:
                        自身.退订.append(订(属性[钩名],变更))
                自身.已订=True
        finally:
            自身.绘制中=False
        if 写过 or 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画等待(自身,文档,窗口,元):
        '还没有桶，或还没选出实现'
        根=模块节点(文档,'div',样式模块,'status')
        根.setAttribute('data-textpreview-state','loading')
        if 元.get('status')=='none':
            行=模块节点(文档,'p',样式模块,'statusLine')
            行.textContent=中文['resourceUnavailable']
            根.appendChild(行)
        else:
            根.appendChild(加载指示器({'window':窗口,'label':中文['loading']}).渲染())
        return 根

    def 画不可预览(自身,文档,窗口,签,展示路径,文件主):
        '已知二进制、没有实现。只留路径、说明，以及交给宿主的动作'
        根=模块节点(文档,'div',样式模块,'preview')
        根.setAttribute('data-textpreview-state','unsupported')
        根.setAttribute('data-textpreview-url',签['contentId'])
        头=模块节点(文档,'div',样式模块,'header')
        头.appendChild(自身.画路径(文档,展示路径))
        if 文件主 is not None:
            挂上(头,自身.属性['renderSlot']('sidebar.right.tab.document.actions',文件主))
        根.appendChild(头)
        体=模块节点(文档,'div',样式模块,'body')
        体.setAttribute('data-textpreview-body','')
        空=模块节点(文档,'div',样式模块,'empty')
        空.setAttribute('data-textpreview-unsupported','')
        名=路径展示拆分(展示路径)['name']
        图=文件类型图标({'window':窗口,'kind':分类文件类型(名),'size':36,'className':'emptyIcon'}).渲染()
        标样式模块(图,样式模块)
        空.appendChild(图)
        行=模块节点(文档,'p',样式模块,'emptyLine')
        行.textContent=中文['unsupportedFile']
        空.appendChild(行)
        if 文件主 is not None:
            挂上(空,自身.属性['renderSlot']('sidebar.right.tab.document.unpreviewable',文件主))
        体.appendChild(空)
        根.appendChild(体)
        return 根

    def 画正文(自身,文档,窗口,签,信号,文件,状态,当前,选中,候选,模式,展示路径,文件主,已载,载到,有内容,行号,能读,元,观察版本,版本变了,重载,渲染器重载,动作):
        '有实现时的顶栏和正文'
        属性=自身.属性
        根=模块节点(文档,'div',样式模块,'preview')
        根.setAttribute('data-textpreview-state','text')
        根.setAttribute('data-textpreview-url',签['contentId'])
        根.setAttribute('data-document-preview',选中['id'])
        元失败=元.get('failure')
        if 元失败 is not None and 有内容:
            条=模块节点(文档,'p',样式模块,'changed')
            条.setAttribute('data-textpreview-meta-failed',str(元失败.get('code') if isinstance(元失败,dict) else ''))
            字=文档.createElement('span')
            字.textContent=失败行(元失败)
            条.appendChild(字)
            钮=模块节点(文档,'button',样式模块,'action')
            钮.type='button'
            钮.setAttribute('data-textpreview-reload-now','')
            钮.textContent=中文['reloadNow']
            def 点重载(事件):
                '元数据失败时重读'
                重载()
            钮.addEventListener('click',点重载)
            条.appendChild(钮)
            根.appendChild(条)
        elif 版本变了:
            条=模块节点(文档,'p',样式模块,'changed')
            条.setAttribute('data-textpreview-changed','')
            字=文档.createElement('span')
            字.textContent=中文['changed']
            条.appendChild(字)
            钮=模块节点(文档,'button',样式模块,'action')
            钮.type='button'
            钮.setAttribute('data-textpreview-reload-now','')
            钮.textContent=中文['reloadNow']
            def 点变更(事件):
                '文件已更新时重读'
                重载()
            钮.addEventListener('click',点变更)
            条.appendChild(钮)
            根.appendChild(条)
        头=模块节点(文档,'div',样式模块,'header')
        头.appendChild(自身.画路径(文档,展示路径))
        if len(候选)>1:
            def 切换菜单(事件=None):
                '打开或关上查看器菜单'
                自身.菜单开=not 自身.菜单开
                自身.渲染()
            def 选了(标识):
                '记下显式查看器并关上菜单'
                动作['selected'](签['id'],标识)
                自身.菜单开=False
            def 关上():
                '菜单自己关上'
                自身.菜单开=False
                自身.渲染()
            锚=模块节点(文档,'button',样式模块,'tool viewerTool')
            锚.type='button'
            锚.setAttribute('aria-label',中文['openWith'])
            锚.setAttribute('title',选中['title']())
            锚.setAttribute('data-document-viewer-menu','')
            锚.textContent=选中['title']()
            锚.addEventListener('click',切换菜单)
            条目=[]
            for 项 in 候选:
                条目.append({'id':项['id'],'label':项['title']()})
            头.appendChild(菜单({
                'window':窗口,
                'open':自身.菜单开,
                'anchor':锚,
                'items':条目,
                'selectedId':选中['id'],
                'onSelect':选了,
                'onClose':关上,
                'align':'end',
                'portal':True,
                'dense':True,
            }).渲染())
        if 选中.get('wrap') is True:
            换行开=状态.get('wrap') is True
            换行钮=模块节点(文档,'button',样式模块,'tool')
            换行钮.type='button'
            换行钮.setAttribute('aria-pressed','true' if 换行开 else 'false')
            换行钮.setAttribute('aria-label',中文['wrap.aria'])
            换行钮.setAttribute('data-textpreview-tool','wrap')
            换行钮.appendChild(字形(文档,不换行路径 if 换行开 else 换行路径))
            def 点换行(事件):
                '切换换行'
                动作['toggledWrap'](签['id'])
            换行钮.addEventListener('click',点换行)
            头.appendChild(提示泡({
                'window':窗口,
                'label':中文['wrap.disable'] if 换行开 else 中文['wrap.enable'],
                'side':'bottom',
                'delayMs':500,
                'children':换行钮,
            }).渲染())
        内容=自身.编内容(模式,当前,已载,渲染器重载,动作,签)
        if 内容 is not None:
            挂上(头,属性['renderSlot'](
                'sidebar.right.tab.document.action',
                {'content':内容},
                {'entryKey':选中['id'],'hookContext':属性['useTabInfo']},
            ))
        藏=文档.createElement('span')
        藏.hidden=True
        自动开=状态.get('autoRefresh') is True
        自动钮=模块节点(文档,'button',样式模块,'tool')
        自动钮.type='button'
        自动钮.setAttribute('aria-label',中文['autoRefresh'])
        自动钮.setAttribute('aria-pressed','true' if 自动开 else 'false')
        自动钮.setAttribute('data-textpreview-tool','auto-refresh')
        自动钮.appendChild((图标暂停16 if 自动开 else 图标播放16)({'window':窗口}))
        def 点自动(事件):
            '切换自动刷新'
            动作['toggledAutoRefresh'](签['id'])
        自动钮.addEventListener('click',点自动)
        藏.appendChild(提示泡({
            'window':窗口,
            'label':中文['autoRefresh.disable'] if 自动开 else 中文['autoRefresh.enable'],
            'side':'bottom',
            'delayMs':500,
            'children':自动钮,
        }).渲染())
        头.appendChild(藏)
        重载钮=模块节点(文档,'button',样式模块,'tool')
        重载钮.type='button'
        重载钮.setAttribute('aria-label',中文['reload'])
        重载钮.setAttribute('data-textpreview-tool','reload')
        快捷=签.get('refreshShortcut') if isinstance(签,dict) else None
        if isinstance(快捷,dict) and 'aria' in 快捷:
            重载钮.setAttribute('aria-keyshortcuts',快捷['aria'])
        重载钮.appendChild(图标刷新16({'window':窗口}))
        def 点工具重载(事件):
            '工具栏重读'
            重载()
        重载钮.addEventListener('click',点工具重载)
        提示文=中文['reload']
        if isinstance(快捷,dict) and 'keys' in 快捷:
            提示文=中文['reload']
        头.appendChild(提示泡({
            'window':窗口,
            'label':提示文,
            'shortcutKeys':快捷.get('keys') if isinstance(快捷,dict) else None,
            'side':'bottom',
            'delayMs':500,
            'children':重载钮,
        }).渲染())
        if 文件主 is not None:
            挂上(头,属性['renderSlot']('sidebar.right.tab.document.actions',文件主))
        根.appendChild(头)
        体类='body wrap' if 状态.get('wrap') is True else 'body'
        体=模块节点(文档,'div',样式模块,体类)
        体.setAttribute('data-textpreview-body','')
        if 状态.get('wrap') is True:
            体.setAttribute('data-textpreview-wrap','')
        自身.滚动口=体
        def 绑滚动口(节点):
            '渲染器交回自己的滚动口。空则回到共享正文'
            下个=节点 if 节点 is not None else 体
            自身.滚动口=下个
            if 下个 is not None and isinstance(状态,dict):
                下个.scrollTop=状态.get('scrollTop') or 0
        if 模式!='renderer' and not 有内容 and (当前 is None or 当前.get('failure') is None):
            体.appendChild(加载指示器({'window':窗口,'label':中文['loading']}).渲染())
        if 内容 is not None:
            回退=模块节点(文档,'p',样式模块,'statusLine')
            回退.textContent=套入(中文['rendererUnavailable'],{'name':选中['title']()})
            def 加地址(地址):
                '观察渲染器新读到的文件'
                属性['addResource'](签['id'],地址,信号)
            def 设地址(地址列表):
                '换成渲染器这一轮的依赖，并带上文档自己'
                属性['setResources'](签['id'],[签['contentId']]+list(地址列表),信号)
            挂上(体,属性['renderSlot'](
                'sidebar.right.tab.document',
                {
                    'resourceAddress':签['contentId'],
                    'content':内容,
                    'wrap':状态.get('wrap') is True,
                    'scrollportRef':绑滚动口,
                    'addResource':加地址,
                    'setResources':设地址,
                    'window':窗口,
                },
                {'entryKey':选中['id'],'hookContext':属性['useTabInfo'],'fallback':回退},
            ))
        失败=当前.get('failure') if isinstance(当前,dict) else None
        if 失败 is not None:
            if 有内容:
                行=模块节点(文档,'p',样式模块,'statusLine')
                行.setAttribute('data-textpreview-failed',str(失败.get('code') if isinstance(失败,dict) else ''))
                字=文档.createElement('span')
                字.textContent=失败行(失败)
                行.appendChild(字)
                再=模块节点(文档,'button',样式模块,'action')
                再.type='button'
                再.setAttribute('data-textpreview-retry','')
                再.textContent=中文['retry']
                def 点再读(事件):
                    '失败后读下一页'
                    自身.读下一页(能读,当前,属性,签,文件,信号,载到,观察版本)
                再.addEventListener('click',点再读)
                行.appendChild(再)
                体.appendChild(行)
            else:
                空=模块节点(文档,'div',样式模块,'empty')
                空.setAttribute('data-textpreview-failed',str(失败.get('code') if isinstance(失败,dict) else ''))
                名=路径展示拆分(展示路径)['name']
                图=文件类型图标({'window':窗口,'kind':分类文件类型(名),'size':36,'className':'emptyIcon'}).渲染()
                标样式模块(图,样式模块)
                空.appendChild(图)
                字=模块节点(文档,'p',样式模块,'emptyLine')
                字.textContent=失败行(失败)
                空.appendChild(字)
                办法=空失败办法(失败)
                if 办法=='open' and 文件主 is not None:
                    挂上(空,属性['renderSlot']('sidebar.right.tab.document.unpreviewable',文件主))
                if 办法=='retry':
                    再=模块节点(文档,'button',样式模块,'retry')
                    再.type='button'
                    再.setAttribute('data-textpreview-retry','')
                    再.appendChild(图标刷新14({'window':窗口}))
                    再.appendChild(文档.createTextNode(中文['retry']))
                    def 点空重试(事件):
                        '空正文时重读'
                        重载()
                    再.addEventListener('click',点空重试)
                    空.appendChild(再)
                体.appendChild(空)
        if 模式=='text-pages' and 当前 is not None and len(已载)>0 and 当前.get('eof') is not True and 当前.get('failure') is None:
            更多=模块节点(文档,'button',样式模块,'more')
            更多.type='button'
            更多.disabled=当前.get('loading') is True
            更多.setAttribute('data-textpreview-more','')
            if 当前.get('loading') is True:
                更多.appendChild(加载指示器({'window':窗口,'label':中文['loading'],'inline':True}).渲染())
            else:
                更多.textContent=中文['loadMore']
            def 点更多(事件):
                '加载更多'
                自身.读下一页(能读,当前,属性,签,文件,信号,载到,观察版本)
            更多.addEventListener('click',点更多)
            体.appendChild(更多)
        def 滚动(事件):
            '记下滚动。文本模式贴底时读下一页'
            口=自身.滚动口
            if 口 is None or 事件.target!=口:
                return
            动作['scrolled'](签['id'],口.scrollTop)
            if 模式=='text-pages' and (当前 is None or 当前.get('failure') is None) and 口.clientHeight>0:
                if 口.scrollTop+口.clientHeight>=口.scrollHeight-1:
                    自身.读下一页(能读,当前,属性,签,文件,信号,载到,观察版本)
        体.addEventListener('scroll',滚动,True)
        if 有内容:
            体.scrollTop=状态.get('scrollTop') or 0
        自身.应答导航(体,当前,导航,行号,模式,载到,能读,属性,签,文件,信号,观察版本,动作)
        根.appendChild(体)
        return 根

    def 读下一页(自身,能读,当前,属性,签,文件,信号,载到,观察版本):
        '文本模式还没到文件尾时读下一页'
        if not 能读 or 当前 is None or 当前.get('loading') or 当前.get('eof'):
            return
        属性['loadPage'](签['id'],文件,载到+1,信号,观察版本)

    def 编内容(自身,模式,当前,已载,渲染器重载,动作,签):
        '交给文档槽的内容。渲染器模式带上这一修订的完成和失败'
        if 模式=='renderer':
            if 当前 is None:
                return None
            修订=当前['loadRevision']
            def 失败了():
                '这一修订加载失败'
                动作['rendererFailed'](签['id'],修订)
            def 载好(版本):
                '这一修订显示的源版本'
                动作['rendered'](签['id'],修订,版本)
            return {'kind':'renderer','revision':修订,'reload':渲染器重载,'failed':失败了,'loaded':载好}
        if 模式=='bytes-complete':
            if 当前 is None or 当前.get('complete') is None:
                return None
            return {'kind':'bytes','data':当前['complete']['data']}
        if 当前 is None or len(已载)==0:
            return None
        段=[]
        for 页 in 已载:
            if 页['lines']>0:
                段.append(页['text'])
        return {'kind':'text','pages':已载,'text':'\n'.join(段),'eof':当前.get('eof') is True}

    def 应答导航(自身,体,当前,导航,行号,模式,载到,能读,属性,签,文件,信号,观察版本,动作):
        '还没应答的导航：够不着就继续读，够得着就滚过去'
        if 当前 is None:
            return
        修订=导航.get('revision') if isinstance(导航,dict) else None
        if 当前.get('revision')==修订:
            return
        if 行号 is None or 模式!='text-pages':
            动作['navigated'](签['id'],修订)
            return
        if 行号>载到 and 当前.get('eof') is not True:
            if not 当前.get('loading') and 当前.get('failure') is None and 能读:
                属性['loadPage'](签['id'],文件,载到+1,信号,观察版本)
            return
        口=自身.滚动口 if 自身.滚动口 is not None else 体
        落到=滚到行(口,行号)
        if not 落到 and 行号<=载到:
            return
        动作['navigated'](签['id'],修订)
        动作['scrolled'](签['id'],口.scrollTop)

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
