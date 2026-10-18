from ...模块.客户端.通告 import 取握手窗口
import os
import re
from ....基础设施.通用工具 import 启动守护线程
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import (
    图标刷新16,
    图标暂停16,
    图标播放16,
    图标开文件夹16,
    图标关文件夹16,
)
from ...ui_基础界面组件.文件类型图标 import 文件类型图标,分类文件类型
from ...ui_基础界面组件.提示泡 import 提示泡
from ....工具.工作区路径 import 文件地址为,路径展示拆分
from .文案 import 中文
from .目录节点 import 已中止

__all__=['失败行','文件体','条目','层级','挂上文件体','样式模块']

样式模块='files'
_数字段=re.compile(r'([0-9]+)',re.ASCII)
_按标签={}
_播种中=set()

def _排序键(项):
    '目录在前。名称按数字段比较，使 file2 排在 file10 前'
    段=[]
    for 部 in _数字段.split(项['name']):
        if 部=='':
            continue
        if 部.isdigit():
            段.append((1,int(部)))
        else:
            段.append((0,部.casefold()))
    组=0 if 项['type']=='directory' else 1
    return (组,段)

def _失败码(失败):
    'RemoteFailure 的 code。对象或 dict 都行'
    if isinstance(失败,dict):
        return 失败['code'] if 'code' in 失败 else None
    return getattr(失败,'code',None)

def 失败行(失败):
    '用目录口吻说明为什么列不出'
    码=_失败码(失败)
    if 码=='workspace-file/not-found':
        return 中文['error.notFound']
    if 码=='workspace-file/outside-workspace':
        return 中文['error.outsideWorkspace']
    if 码=='workspace-file/not-directory':
        return 中文['error.notDirectory']
    if isinstance(失败,dict):
        消息=失败['message'] if 'message' in 失败 else ''
    elif hasattr(失败,'message'):
        消息=失败.message
    else:
        消息=str(失败)
    return 中文['error.unavailable'].replace('{message}',str(消息))

def 挂槽(容器,结果):
    '把槽位出口里的节点挂进容器'
    if 结果 is None:
        return
    if getattr(结果,'tagName',None) is not None or getattr(结果,'nodeType',None) is not None:
        容器.appendChild(结果)
        return
    if isinstance(结果,(list,tuple)):
        for 项 in 结果:
            挂槽(容器,项)
        return
    if isinstance(结果,dict):
        for 键 in ('content','body','children'):
            if 键 in 结果:
                挂槽(容器,结果[键])
        if 'items' in 结果 and isinstance(结果['items'],(list,tuple)):
            for 项 in 结果['items']:
                挂槽(容器,项)

def _图标(窗,函数,类名):
    '画出共享图标，并套上本模块的类'
    标=函数({'window':窗,'className':类名})
    if 标 is not None:
        标样式模块(标,样式模块)
    return 标

class 层级:
    '一个目录下的说明和子行'
    def __init__(自身,路径,状态,窗,组件):
        '记下这一级的绝对路径和当前树'
        自身.路径=路径
        自身.状态=状态
        自身.窗=窗
        自身.组件=组件

    def _说明(自身,列表,种类,文本,码=None):
        '挂一行说明'
        行=模块节点(自身.窗.document,'li',样式模块,'note')
        行.setAttribute('data-files-row',种类)
        if 码 is not None:
            行.setAttribute('data-files-code',str(码))
        行.textContent=文本
        列表.appendChild(行)

    def 渲染(自身,列表):
        '把这一级挂进 ul'
        级表=自身.状态['levels']
        级=级表[自身.路径] if 自身.路径 in 级表 else None
        if 级 is None or 级['kind']=='loading':
            自身._说明(列表,'loading',中文['loading'])
            return
        if 级['kind']=='failed':
            自身._说明(列表,'failed',失败行(级['failure']),_失败码(级['failure']))
            return
        if 'failure' in 级 and 级['failure'] is not None:
            自身._说明(列表,'failed',失败行(级['failure']))
        条目列表=sorted(级['level']['entries'],key=_排序键)
        if len(条目列表)==0:
            自身._说明(列表,'empty',中文['empty'])
        for 项 in 条目列表:
            列表.appendChild(条目(自身.路径,项,自身.状态,自身.窗,自身.组件).渲染())
        if 级['level']['truncated'] is True:
            自身._说明(列表,'truncated',中文['truncated'])

class 条目:
    '一行。目录可展开，文件可打开，其它类型只展示'
    def __init__(自身,父路径,项,状态,窗,组件):
        '记下父路径和这一条'
        自身.父路径=父路径
        自身.项=项
        自身.状态=状态
        自身.窗=窗
        自身.组件=组件

    def 渲染(自身):
        '返回 li'
        文档=自身.窗.document
        路径=re.sub(r'[/\\]+$','',自身.父路径)+'/'+自身.项['name']
        类型=自身.项['type']
        行=模块节点(文档,'li',样式模块,'item')
        行.setAttribute('data-files-path',路径)
        if 类型=='directory':
            行.setAttribute('data-files-entry','directory')
            展开=路径 in 自身.状态['expanded']
            钮=模块节点(文档,'button',样式模块,'row')
            钮.setAttribute('type','button')
            钮.setAttribute('aria-expanded','true' if 展开 else 'false')
            def 点(事件,父=自身.父路径,路=路径):
                '展开或收起这个目录'
                自身.组件.切换目录(父,路)
            钮.addEventListener('click',点)
            函数=图标开文件夹16 if 展开 else 图标关文件夹16
            标=_图标(自身.窗,函数,'icon')
            if 标 is not None:
                钮.appendChild(标)
            名=模块节点(文档,'span',样式模块,'name')
            名.textContent=自身.项['name']
            钮.appendChild(名)
            行.appendChild(钮)
            if 展开:
                下级=模块节点(文档,'ul',样式模块,'level')
                层级(路径,自身.状态,自身.窗,自身.组件).渲染(下级)
                行.appendChild(下级)
            return 行
        if 类型=='file':
            行.setAttribute('data-files-entry','file')
            钮=模块节点(文档,'button',样式模块,'row')
            钮.setAttribute('type','button')
            def 点(事件,路=路径):
                '打开这个文件'
                自身.组件.打开文件(路)
            钮.addEventListener('click',点)
            图标=文件类型图标({
                'window':自身.窗,
                'kind':分类文件类型(自身.项['name']),
                'size':16,
                'className':'fileIcon',
            }).渲染()
            if 图标 is not None:
                标样式模块(图标,样式模块)
                钮.appendChild(图标)
            名=模块节点(文档,'span',样式模块,'name')
            名.textContent=自身.项['name']
            钮.appendChild(名)
            行.appendChild(钮)
            return 行
        行.setAttribute('data-files-entry','other')
        壳=模块节点(文档,'span',样式模块,'row other')
        壳.setAttribute('aria-disabled','true')
        壳.setAttribute('title',中文['entry.other'])
        名=模块节点(文档,'span',样式模块,'name')
        名.textContent=自身.项['name']
        壳.appendChild(名)
        行.appendChild(壳)
        return 行

class 文件体:
    '会话工作区根和已经打开的下级'
    def __init__(自身,属性):
        '记下 props。槽位入口再调用渲染'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.滚动顶=0
        自身.释放命令=None
        自身.已播种=False
        自身.标签标识=None
        自身.信号=None
        自身.树=None
        自身.会话标识=None
        自身.标签动作=None

    def 更新(自身,属性):
        '换上一份 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 卸下(自身):
        '离开前把滚动写回存储，并放开命令'
        if 自身.已播种 and 自身.信号 is not None and not 已中止(自身.信号):
            自身.属性['actions']['scrolled'](自身.标签标识,自身.滚动顶)
        if 自身.释放命令 is not None:
            自身.释放命令()
            自身.释放命令=None
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None

    def 切换目录(自身,父路径,路径):
        '展开或折叠交给面'
        自身.属性['toggle'](自身.标签标识,父路径,路径,自身.树['expanded'],自身.信号)

    def 打开文件(自身,路径):
        '用树根拼会话文件地址并打开'
        地址=文件地址为(自身.会话标识,自身.树['root'],路径)
        自身.标签动作['openResource'](地址)

    def 重新读取(自身):
        '按展开集重新列举，不收起目录'
        自身.属性['refresh'](自身.标签标识)

    def 交出(自身,节点):
        '记下根。调用方给了 parent 就挂上去'
        自身.根=节点
        if 节点 is not None and 'parent' in 自身.属性:
            自身.属性['parent'].appendChild(节点)
        return 节点

    def 画路径(自身,文档,路径):
        '根路径。悬停可见整段，溢出时标上裁剪'
        拆=路径展示拆分(路径)
        外=模块节点(文档,'span',样式模块,'path')
        外.setAttribute('title',路径)
        外.setAttribute('data-path-label','')
        外.setAttribute('data-files-path','true')
        内=模块节点(文档,'span',样式模块,'text')
        if 拆['directory']!='':
            目录=模块节点(文档,'span',样式模块,'directory')
            目录.textContent=拆['directory']
            内.appendChild(目录)
        名=模块节点(文档,'span',样式模块,'name')
        名.textContent=拆['name']
        内.appendChild(名)
        外.appendChild(内)
        def 核对(事件=None):
            '内层比外层宽时标上 data-path-clipped'
            if 内.offsetWidth>外.clientWidth:
                外.setAttribute('data-path-clipped','')
            else:
                外.removeAttribute('data-path-clipped')
        核对()
        观察类=getattr(自身.窗,'ResizeObserver',None)
        if 观察类 is not None:
            观察=观察类(核对)
            观察.observe(外)
            观察.observe(内)
        return 外

    def 渲染(自身):
        '无工作目录给说明。树还没有则先播种，避免先闪空目录'
        属性=自身.属性
        窗=属性['window'] if 'window' in 属性 else 取握手窗口()
        自身.窗=窗
        文档=窗.document
        注入模块样式文件(
            文档,
            '文件体样式',
            os.path.join(os.path.dirname(__file__),'文件体.module.css'),
            样式模块,
        )
        信息=属性['useTabInfo']()
        签=信息['tab']
        标签标识=签['id']
        信号=签['signal']
        标签动作=签['actions']
        会话标识=属性['sessionId']
        def 取工作目录(会话表):
            '当前会话的工作目录。没有则为 None'
            按=会话表['byId'] if isinstance(会话表,dict) and 'byId' in 会话表 else {}
            行=按[会话标识] if 会话标识 in 按 else None
            if isinstance(行,dict) and 'cwd' in 行:
                return 行['cwd']
            return None
        工作目录=属性['useSessions'](取工作目录)
        def 取树(库):
            '这一标签的树。还没播种是 None'
            按=库['byTab']
            if 标签标识 not in 按:
                return None
            return 按[标签标识]
        状态=属性['useStore'](取树)
        旧=_按标签.get(标签标识)
        if 旧 is not None:
            旧.卸下()
        _按标签[标签标识]=自身
        自身.标签标识=标签标识
        自身.信号=信号
        自身.会话标识=会话标识
        自身.标签动作=标签动作
        自身.树=状态
        自身.已播种=状态 is not None
        if 状态 is not None:
            _播种中.discard(标签标识)
        def 刷新命令():
            '命令面板或快捷键触发的重新读取'
            属性['refresh'](标签标识)
        自身.释放命令=标签动作['bindCommands']({'refresh':刷新命令})
        if 状态 is None and 工作目录 is not None and not 已中止(信号) and 标签标识 not in _播种中:
            _播种中.add(标签标识)
            def 播种(标识=标签标识,目录=工作目录,寿=信号,起=属性['start']):
                '渲染返回后再播种，避免写存储时重入这一次绘制'
                起(标识,目录,寿)
            启动守护线程(播种)
        if 工作目录 is None:
            根=模块节点(文档,'div',样式模块,'status')
            根.setAttribute('data-files-state','no-workspace')
            段=模块节点(文档,'p',样式模块,'statusLine')
            段.textContent=中文['noWorkspace']
            根.appendChild(段)
            return 自身.交出(根)
        if 状态 is None:
            自身.根=None
            return None
        快捷=签['refreshShortcut'] if 'refreshShortcut' in 签 else None
        键=None
        无障碍=None
        if isinstance(快捷,dict):
            键=快捷['keys'] if 'keys' in 快捷 else None
            无障碍=快捷['aria'] if 'aria' in 快捷 else None
        根=模块节点(文档,'div',样式模块,'root')
        根.setAttribute('data-files-state','tree')
        根.setAttribute('data-files-root',状态['root'])
        头=模块节点(文档,'div',样式模块,'header')
        头.appendChild(自身.画路径(文档,状态['root']))
        藏=文档.createElement('span')
        藏.hidden=True
        自动钮=模块节点(文档,'button',样式模块,'tool')
        自动钮.setAttribute('type','button')
        自动钮.setAttribute('aria-label',中文['autoRefresh'])
        自动钮.setAttribute('aria-pressed','true' if 状态['autoRefresh'] else 'false')
        自动钮.setAttribute('data-files-auto-refresh','true')
        自动文='autoRefresh.disable' if 状态['autoRefresh'] else 'autoRefresh.enable'
        自动钮.setAttribute('title',中文[自动文])
        def 点自动(事件):
            '切换自动刷新'
            属性['setAutoRefresh'](标签标识,not 状态['autoRefresh'])
        自动钮.addEventListener('click',点自动)
        自动标=_图标(窗,图标暂停16 if 状态['autoRefresh'] else 图标播放16,'')
        if 自动标 is not None:
            自动钮.appendChild(自动标)
        藏.appendChild(自动钮)
        头.appendChild(藏)
        重读钮=模块节点(文档,'button',样式模块,'tool')
        重读钮.setAttribute('type','button')
        重读钮.setAttribute('aria-label',中文['reload'])
        重读钮.setAttribute('data-files-reload','true')
        if 无障碍 is not None:
            重读钮.setAttribute('aria-keyshortcuts',无障碍)
        def 点重读(事件):
            '重新读取'
            自身.重新读取()
        重读钮.addEventListener('click',点重读)
        重读标=_图标(窗,图标刷新16,'')
        if 重读标 is not None:
            重读钮.appendChild(重读标)
        泡=提示泡({
            'window':窗,
            'label':中文['reload'],
            'side':'bottom',
            'shortcutKeys':键,
            'delayMs':500,
            'children':重读钮,
        })
        头.appendChild(泡.渲染())
        挂槽(头,属性['renderSlot']('sidebar.right.tab.files.actions',{
            'absolutePath':状态['root'],
        }))
        根.appendChild(头)
        体=模块节点(文档,'div',样式模块,'body')
        体.setAttribute('data-files-body','true')
        def 滚动(事件):
            '先记在节点上。卸下时再写进存储'
            自身.滚动顶=事件.currentTarget.scrollTop
        体.addEventListener('scroll',滚动)
        体.scrollTop=状态['scrollTop']
        自身.滚动顶=体.scrollTop
        列表=模块节点(文档,'ul',样式模块,'level')
        层级(状态['root'],状态,窗,自身).渲染(列表)
        体.appendChild(列表)
        根.appendChild(体)
        return 自身.交出(根)

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 挂上文件体(属性):
    '槽位入口。返回这一次画出的节点'
    return 文件体(属性).渲染()
