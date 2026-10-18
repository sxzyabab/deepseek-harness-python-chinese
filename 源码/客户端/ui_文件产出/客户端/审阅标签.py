'一轮改动的审阅页：选一个文件，看单栏或左右对比'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import (
    描边图标,图标下箭头描边常规,图标不换行填充常规,图标换行填充常规,图标检视12,
)
from ...ui_基础界面组件.菜单 import 菜单
from ...ui_基础界面组件.路径标签 import 路径标签
from ...ui_基础界面组件.提示泡 import 提示泡
from ....工具.工作区路径 import 文件地址为
from ..改动 import 已改文件网址,改动对比网址,改动摘要网址,解析改动审阅地址
from .产出文件 import 产出文件
from .文案 import 中文,填入

__all__=['审阅标签']

样式模块='ReviewTab'
对比样式='FileDiff'
样式路径=os.path.join(os.path.dirname(__file__),'审阅标签.module.css')
对比样式路径=os.path.join(os.path.dirname(__file__),'产出文件.module.css')


def 确保样式(文档):
    '审阅页和对比样式各插一次'
    注入模块样式文件(文档,'dsh-review-tab',样式路径,样式模块)
    注入模块样式文件(文档,'dsh-file-diff',对比样式路径,对比样式)


def 元素(文档,标签,类名=None,模块=None):
    '带官方类名。模块缺省是审阅页'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块 if 模块 is None else 模块)


def 分组(数):
    '按 en-US 给行数加千分位'
    return format(int(数),',')


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


class 审阅计数:
    '一个文件的二进制、过大，或增减行数'
    def __init__(自身,属性):
        '记下文件'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '按文件种类画'
        文档=自身.属性['window'].document
        文件=自身.属性['file']
        if 文件.get('binary') is True:
            节点=元素(文档,'span','label')
            节点.textContent=中文['changes.binary']
            自身.根=节点
            return 节点
        if 文件.get('oversized') is True:
            节点=元素(文档,'span','label')
            节点.textContent=中文['changes.oversized']
            自身.根=节点
            return 节点
        盒=文档.createDocumentFragment()
        增=元素(文档,'span','added')
        增.textContent=填入(中文['changes.added'],{'count':分组(文件.get('added') or 0)})
        删=元素(文档,'span','deleted')
        删.textContent=填入(中文['changes.deleted'],{'count':分组(文件.get('deleted') or 0)})
        盒.appendChild(增)
        盒.appendChild(删)
        自身.根=盒
        return 盒


class 审阅标签:
    '文件选择器后面的对比，或还在读、已经没有的占位'
    def __new__(类,属性):
        '画出这一页并返回根节点'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.对比=None
        自身.菜单开=False
        自身.绘制中=False
        自身.待重画=False
        自身.已订=False
        自身.退订=[]
        自身.信号=None
        自身.遗忘=None
        return 自身.渲染()

    def 渲染(自身):
        '选中文件的对比'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            用签=属性.get('useTabInfo')
            信息=用签() if callable(用签) else {}
            签=信息.get('tab') if isinstance(信息,dict) else None
            if not isinstance(签,dict):
                raise Exception('ui-deliverables: not a review address ""')
            导航=签.get('navigation') if isinstance(签.get('navigation'),dict) else {}
            坐标=解析改动审阅地址(签.get('contentId'))
            if 坐标 is None:
                raise Exception('ui-deliverables: not a review address "'+str(签.get('contentId'))+'"')
            序号=坐标['seq']
            会话标识=属性.get('sessionId')

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

            def 原样(值):
                '整份快照'
                return 值

            def 选摘要(值,会话标识=会话标识,序号=序号):
                '这一宣告的摘要'
                if not isinstance(值,dict):
                    return None
                return 值.get(改动摘要网址(会话标识,序号))

            用会话=属性.get('useSessions')
            用摘要=属性.get('useChangesSummary')
            用存储=属性.get('useStore')
            用宿主=属性.get('usePresentedHost')
            用对比=属性.get('useChangesDiff')
            用打开=属性.get('usePresentedOpen')
            目录=用会话(工作目录) if callable(用会话) else None
            摘要=用摘要(选摘要) if callable(用摘要) else None
            签标识=签.get('id')

            def 选桶(状态,签标识=签标识):
                '这张签的查看状态'
                if not isinstance(状态,dict):
                    return None
                按签=状态.get('byTab')
                if not isinstance(按签,dict):
                    return None
                return 按签.get(签标识)

            桶=用存储(选桶) if callable(用存储) else None
            宿主=用宿主(原样) if callable(用宿主) else None
            动作=属性.get('actions') if isinstance(属性.get('actions'),dict) else {}
            if 桶 is None or 桶.get('navigated')!=导航.get('revision'):
                参数=导航.get('params') if isinstance(导航.get('params'),dict) else {}
                导航下标=参数.get('index')
                if not isinstance(导航下标,int) or isinstance(导航下标,bool) or 导航下标<0:
                    导航下标=桶.get('index') if isinstance(桶,dict) else 0
                if callable(动作.get('navigated')):
                    动作['navigated'](签标识,导航.get('revision'),导航下标)
                    if callable(用存储):
                        桶=用存储(选桶)
            信号=签.get('signal')
            if 信号 is not None and 信号 is not 自身.信号:
                if 自身.信号 is not None and 自身.遗忘 is not None:
                    自身.信号.removeEventListener('abort',自身.遗忘)

                def 遗忘(签标识=签标识,动作=动作):
                    '签没了就丢掉查看状态'
                    if callable(动作.get('forget')):
                        动作['forget'](签标识)

                自身.遗忘=遗忘
                自身.信号=信号
                信号.addEventListener('abort',遗忘,{'once':True})
            if 摘要 is None and callable(属性.get('loadChangesSummary')):
                属性['loadChangesSummary'](会话标识,序号)
                if callable(用摘要):
                    摘要=用摘要(选摘要)
            if 宿主 is None and callable(属性.get('reloadPresentedHost')):
                属性['reloadPresentedHost']()
                if callable(用宿主):
                    宿主=用宿主(原样)
            文件表=摘要['files'] if isinstance(摘要,dict) and isinstance(摘要.get('files'),list) else []
            下标=0
            if isinstance(桶,dict) and isinstance(桶.get('index'),int) and 桶['index']<len(文件表):
                下标=桶['index']
            文件=文件表[下标] if 下标<len(文件表) else None

            def 选对比(值,文件=文件,会话标识=会话标识,序号=序号,下标=下标):
                '选中文件的对比'
                if 文件 is None or not isinstance(值,dict):
                    return None
                return 值.get(改动对比网址(会话标识,序号,下标))

            def 选阶段(值,文件=文件,会话标识=会话标识,序号=序号,下标=下标):
                '选中文件的打开阶段'
                if 文件 is None or not isinstance(值,dict):
                    return None
                return 值.get(已改文件网址(会话标识,序号,下标))

            对比态=用对比(选对比) if callable(用对比) else None
            if 文件 is not None and 对比态 is None and callable(属性.get('loadChangesDiff')):
                属性['loadChangesDiff'](会话标识,序号,下标)
                if callable(用对比):
                    对比态=用对比(选对比)
            阶段=用打开(选阶段) if callable(用打开) else None
            左右=isinstance(桶,dict) and 桶.get('split') is True
            换行=isinstance(桶,dict) and 桶.get('wrap') is True
            可原生=宿主 is not None and 宿主!='error' and bool(宿主.get('available')) and 阶段!='nativeUnavailable'
            if 摘要 is None or 摘要=='loading':
                摘要态='loading'
            elif 摘要=='missing':
                摘要态='missing'
            else:
                摘要态='ready'
            if 自身.根 is None:
                自身.根=元素(文档,'div','root')
                自身.根.setAttribute('data-changes-review','')
            内=元素(文档,'div','root',对比样式)
            内.style.height='100%'
            自身.根.setAttribute('data-review-state',摘要态)
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
            头=元素(文档,'div','header',对比样式)
            if 文件 is None:
                标=元素(文档,'span','selectorLabel')
                标.textContent=填入(中文['review.title'],{'turn':str(坐标['turn'])})
                头.appendChild(标)
            else:
                def 关菜单():
                    '关掉文件菜单'
                    自身.菜单开=False
                    自身.渲染()

                def 点选择(事件):
                    '打开或关掉文件菜单'
                    自身.菜单开=not 自身.菜单开
                    自身.渲染()

                选择钮=元素(文档,'button','selectorButton')
                选择钮.setAttribute('type','button')
                选择钮.setAttribute('aria-haspopup','menu')
                选择钮.setAttribute('aria-expanded','true' if 自身.菜单开 else 'false')
                选择钮.setAttribute('aria-label',中文['review.selectFile'])
                选择钮.setAttribute('title',文件.get('display') or '')
                选择钮.setAttribute('data-review-file',文件.get('path') or '')
                选择钮.addEventListener('click',点选择)
                选择钮.appendChild(路径标签({'window':窗口,'path':文件.get('display') or ''}).渲染())
                选择钮.appendChild(图标下箭头描边常规({'window':窗口,'size':12}))
                条目=[]
                序号项=0
                for 一项 in 文件表:
                    if 一项.get('binary') is True:
                        计数文=中文['changes.binary']
                    elif 一项.get('oversized') is True:
                        计数文=中文['changes.oversized']
                    else:
                        计数文=填入(中文['changes.added'],{'count':分组(一项.get('added') or 0)})+' '+填入(中文['changes.deleted'],{'count':分组(一项.get('deleted') or 0)})
                    条目.append({'id':str(序号项),'label':(一项.get('display') or '')+'  '+计数文})
                    序号项+=1

                def 选中(标识,动作=动作,签标识=签标识):
                    '换成菜单里的文件'
                    if callable(动作.get('selected')):
                        动作['selected'](签标识,int(标识))
                    自身.菜单开=False
                    自身.渲染()

                菜单根=菜单({
                    'window':窗口,
                    'className':'selector',
                    'open':自身.菜单开,
                    'autoFocus':True,
                    'portal':True,
                    'align':'start',
                    'dense':True,
                    'onClose':关菜单,
                    'anchor':选择钮,
                    'items':条目,
                    'selectedId':str(下标),
                    'onSelect':选中,
                }).渲染()
                标样式模块(菜单根,样式模块)
                头.appendChild(菜单根)
            if 文件 is not None:
                计数=元素(文档,'span','counts')
                计数.appendChild(审阅计数({'window':窗口,'file':文件}).渲染())
                头.appendChild(计数)
            工具=元素(文档,'span','tools')

            def 点左右(事件,动作=动作,签标识=签标识):
                '左右和单栏对调'
                if callable(动作.get('toggledSplit')):
                    动作['toggledSplit'](签标识)

            def 点换行(事件,动作=动作,签标识=签标识):
                '换行开关'
                if callable(动作.get('toggledWrap')):
                    动作['toggledWrap'](签标识)

            左右钮=元素(文档,'button','tool')
            左右钮.setAttribute('type','button')
            左右钮.setAttribute('aria-pressed','true' if 左右 else 'false')
            左右钮.setAttribute('aria-label',中文['review.splitAria'])
            左右钮.setAttribute('data-review-tool','split')
            左右钮.addEventListener('click',点左右)
            对比图=描边图标({
                'window':窗口,
                'className':'compareIcon',
            },'0 0 16 16',[
                'M6 1.5H2.5C1.94772 1.5 1.5 1.94772 1.5 2.5V13.5C1.5 14.0523 1.94772 14.5 2.5 14.5H6C6.55228 14.5 7 14.0523 7 13.5V2.5C7 1.94772 6.55228 1.5 6 1.5Z',
                'M13.5 1.5H10C9.44772 1.5 9 1.94772 9 2.5V13.5C9 14.0523 9.44772 14.5 10 14.5H13.5C14.0523 14.5 14.5 14.0523 14.5 13.5V2.5C14.5 1.94772 14.0523 1.5 13.5 1.5Z',
            ],16,1)
            标样式模块(对比图,样式模块)
            左右钮.appendChild(对比图)
            工具.appendChild(提示泡({
                'window':窗口,
                'label':中文['review.unified'] if 左右 else 中文['review.split'],
                'side':'bottom',
                'delayMs':500,
                'children':左右钮,
            }).渲染())
            换行钮=元素(文档,'button','tool')
            换行钮.setAttribute('type','button')
            换行钮.setAttribute('aria-pressed','true' if 换行 else 'false')
            换行钮.setAttribute('aria-label',中文['review.wrapAria'])
            换行钮.setAttribute('data-review-tool','wrap')
            换行钮.addEventListener('click',点换行)
            if 换行:
                换行钮.appendChild(图标不换行填充常规({'window':窗口}))
            else:
                换行钮.appendChild(图标换行填充常规({'window':窗口}))
            工具.appendChild(提示泡({
                'window':窗口,
                'label':中文['review.nowrap'] if 换行 else 中文['review.wrap'],
                'side':'bottom',
                'delayMs':500,
                'children':换行钮,
            }).渲染())
            if 文件 is not None:
                def 点打开(事件,签=签,会话标识=会话标识,目录=目录,文件=文件):
                    '在侧栏打开整个文件'
                    签动作=签.get('actions') if isinstance(签.get('actions'),dict) else {}
                    打开资源=签动作.get('openResource')
                    if callable(打开资源):
                        打开资源(文件地址为(会话标识,目录,文件.get('path') or ''))

                打开钮=元素(文档,'button','tool')
                打开钮.setAttribute('type','button')
                打开钮.setAttribute('aria-label',填入(中文['review.openFileAria'],{'name':文件.get('display') or ''}))
                打开钮.setAttribute('data-review-tool','open-file')
                打开钮.addEventListener('click',点打开)
                打开钮.appendChild(图标检视12({'window':窗口}))
                工具.appendChild(提示泡({
                    'window':窗口,
                    'label':中文['review.openFile'],
                    'side':'bottom',
                    'delayMs':500,
                    'children':打开钮,
                }).渲染())
                渲染槽=属性.get('renderSlot')
                if callable(渲染槽):
                    def 做动作(动作名,应用=None,打开=属性.get('openChanged'),会话标识=会话标识,序号=序号,下标=下标):
                        '打开或揭示这个已改文件'
                        if callable(打开):
                            return 打开(会话标识,序号,下标,动作名,应用)
                        return None
                    挂上(工具,渲染槽('deliverables.review.file.actions',{
                        'actionUrl':已改文件网址(会话标识,序号,下标),
                        'available':可原生,
                        'pending':阶段=='opening' or 阶段=='revealing',
                        'onAction':做动作,
                    }))
            头.appendChild(工具)
            内.appendChild(头)
            if 摘要态=='loading':
                占位=元素(文档,'p','status',对比样式)
                占位.setAttribute('role','status')
                占位.textContent=中文['diff.loading']
                内.appendChild(占位)
            elif 摘要态=='missing':
                占位=元素(文档,'p','status',对比样式)
                占位.textContent=中文['diff.missing']
                内.appendChild(占位)
            if 文件 is not None:
                if 自身.对比 is None:
                    自身.对比=产出文件({'window':窗口})

                def 重试(读=属性.get('loadChangesDiff'),会话标识=会话标识,序号=序号,下标=下标):
                    '再读这一份对比'
                    if callable(读):
                        读(会话标识,序号,下标)

                自身.对比.更新({
                    'window':窗口,
                    'state':对比态,
                    'split':左右,
                    'wrap':换行,
                    'retry':重试,
                })
                内.appendChild(自身.对比.渲染())
            自身.根.appendChild(内)
            if not 自身.已订:
                def 变更():
                    '快照变了就重画'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 钩 in (用签,用会话,用摘要,用存储,用宿主,用对比,用打开):
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
