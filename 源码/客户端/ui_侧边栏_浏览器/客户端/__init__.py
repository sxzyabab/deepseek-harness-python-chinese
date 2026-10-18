from ...模块.客户端.通告 import 取握手窗口
import threading
from ...存储 import 声明存储
from ...ui_侧边栏_右侧.客户端.约定.槽位 import 席名右侧签正文,席名右侧签标题
from .文案 import 中文,英文
from .定义 import 浏览器种类,浏览器标识,浏览器向导图
from .页表 import 创建内嵌帧页
from .视图.浏览器体 import 浏览器体
from .视图.浏览器标题 import 浏览器标题
from .浏览器.控制 import 浏览器控制器
from .electron.electron网页视图实现 import electron网页视图实现
from .electron.electron网页视图呈现形式 import electron网页视图呈现形式
from . import (
    文案,
    定义,
    页表,
    浏览器,
    视图,
    electron,
)

__all__=[
    '文案','定义','页表','浏览器','视图','electron',
    '命名空间','依赖','应用',
]

命名空间='sidebarBrowser'
依赖=['slots','locale','sidebarRight','sidebarRightTabs']


def 应用(上下文,配置=None):
    '登记浏览器类型、中英文案、快捷键、正文和标题'
    打开的签=上下文.sidebarRight.打开标签
    载体=getattr(取握手窗口(),'dshDesktop',None)
    桌面=None
    if 载体 is not None and getattr(载体,'protocolVersion',None)==1:
        桌面=getattr(载体,'browser',None)

    def 装快捷键(快捷上下文):
        'shortcuts 就绪后登记新浏览器页命令'
        def 登记():
            '命令名用中文表原文'
            def 标签():
                '命令名称'
                return 中文['guide.title']

            def 解析(面):
                '没有当前会话就挡住，否则从目标打开浏览器页'
                if isinstance(面,dict):
                    元素=面.get('target')
                else:
                    元素=面.target
                目标=上下文.sidebarRight.命令目标(元素)
                if 目标 is None:
                    return {'status':'blocked','reason':中文['shortcut.noSession']}

                def 跑():
                    '从当前目标打开浏览器页'
                    上下文.sidebarRight.从目标打开标签('browser',目标)

                return {'status':'handled','run':跑}

            return 快捷上下文.shortcuts.register({
                'id':'browser.new',
                'label':标签,
                'aliases':['browser','new browser tab'],
                'defaults':{
                    'desktop:macos':{'code':'KeyT','modifiers':['primary']},
                    'desktop:windows':{'code':'KeyT','modifiers':['primary']},
                    'desktop:linux':{'code':'KeyT','modifiers':['primary']},
                    'web:macos':{'code':'KeyT','modifiers':['primary','alt']},
                    'web:windows':{'code':'KeyT','modifiers':['primary','alt']},
                },
                'regions':['page','editable','terminal'],
                'modals':[],
                'resolve':解析,
            })

        return 快捷上下文.副作用(登记,'ui-sidebar-browser: shortcut')

    上下文.inject(['shortcuts'],装快捷键)

    def 初始状态():
        '每个会话一份空的标签表'
        return {'byTab':{}}

    def 替换(草稿,标签标识,状态):
        '写入这一标签的导航记录'
        草稿['byTab'][标签标识]=状态

    def 遗忘(草稿,标签标识):
        '丢掉这一标签，其它标签留下'
        按标签={}
        for 标识,状态 in list(草稿['byTab'].items()):
            if 标识!=标签标识:
                按标签[标识]=状态
        草稿['byTab']=按标签

    存储句柄=声明存储({
        'init':初始状态,
        'persist':'dsh.sidebar-browser.v1',
        'actions':{'replace':替换,'forget':遗忘},
    })

    def 登记词典():
        '留下中英文案表。界面显示不读英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})

    上下文.副作用(登记词典,'ui-sidebar-browser.copy')

    def 登记类型():
        '登记 browser 类型。桌面宾客在隐藏时仍保留挂载'
        def 类型名():
            '标签类型名'
            return 中文['type.label']

        def 向导名():
            '向导标题'
            return 中文['guide.title']

        def 向导说明():
            '向导说明'
            return 中文['guide.description']

        return 上下文.sidebarRightTabs.登记({
            'id':浏览器标识,
            'kind':浏览器种类,
            'multiple':True,
            'priority':'builtin',
            'keepMounted':桌面 is not None,
            'title':类型名,
            'guide':[{
                'id':'new',
                'commandId':'browser.new',
                'order':30,
                'title':向导名,
                'description':向导说明,
                'icon':浏览器向导图,
            }],
        })

    上下文.副作用(登记类型,'ui-sidebar-browser.type')

    def 装帧(范围,按会话取页):
        '按会话持有页表，并把正文登记进右侧签'
        会话表={}

        def 寿命():
            '卸插件时拆掉这一作用域里的页'
            def 拆帧():
                '拆掉已建的页'
                待办=list(会话表.values())
                会话表.clear()
                for 面 in 待办:
                    面['dispose']()

            return 拆帧

        范围.副作用(寿命,'ui-sidebar-browser.frames')

        def 挂正文():
            '正文进带键席'
            def 登记():
                '登记 browser 正文'
                def 注入(会话标识,动作):
                    '同一会话复用页表，只重绑存储动作'
                    已有=会话表.get(会话标识)
                    if 已有 is not None:
                        已有['rebind'](动作)
                        return 已有
                    造页=按会话取页(会话标识)
                    页表={}
                    当前动作={'值':动作}

                    def 取控制器(标识):
                        '按标签取出控制器'
                        持有=页表.get(标识)
                        if 持有 is None:
                            return None
                        return 持有['controller']

                    def 签仍打开(标签标识):
                        '布局里还有这张签才算打开'
                        快照=打开的签.getSnapshot()
                        for 签 in 快照:
                            if 签.get('sessionId')==会话标识 and 签.get('tabId')==标签标识:
                                return True
                        return False

                    def 浏览器状态(键):
                        '给键控钩子读这一签的控制器'
                        return 取控制器(键)

                    def 挂载(请求):
                        '提交容器后建或复用控制器，并订上界面重画'
                        标签标识=请求['tabId']
                        信号=请求['signal']
                        if getattr(信号,'aborted',False):
                            def 空收起():
                                '已经中止，没有可摘的附着'
                                return None
                            return 空收起
                        持有=页表.get(标签标识)
                        if 持有 is None or 持有['signal'] is not 信号:
                            if 持有 is not None:
                                持有['signal'].removeEventListener('abort',持有['forget'])
                                持有['controller'].拆除()

                            def 遗忘(标识=标签标识):
                                '插件卸载也会中止。只有布局拿掉这张签才删保存的导航'
                                if 标识 in 页表:
                                    del 页表[标识]
                                if not 签仍打开(标识):
                                    当前动作['值']['forget'](标识)

                            控制器=浏览器控制器({
                                'tabId':标签标识,
                                'signal':信号,
                                'applicationOrigin':请求['applicationOrigin'],
                                'initial':请求.get('initial'),
                                'actions':当前动作['值'],
                                'createPage':造页,
                                'openTab':请求['openTab'],
                            })
                            持有={'signal':信号,'controller':控制器,'forget':遗忘}
                            页表[标签标识]=持有
                            信号.addEventListener('abort',遗忘,{'once':True})
                        隐藏=持有['controller'].挂载(请求['viewportId'])
                        持有['controller'].开始(请求.get('initialUrl'))
                        变更=请求.get('onChange')
                        退订=None
                        if callable(变更):
                            退订=持有['controller'].subscribe(变更)

                        def 收起():
                            '结束这次物理附着，不关掉标签'
                            if callable(退订):
                                退订()
                            隐藏()

                        return 收起

                    def 拆除():
                        '拆掉这一会话里的全部页'
                        待办=list(页表.values())
                        页表.clear()
                        for 持有 in 待办:
                            持有['signal'].removeEventListener('abort',持有['forget'])
                            持有['controller'].拆除()

                    def 重绑(新动作):
                        '之后的检查点写到新的会话绑定'
                        当前动作['值']=新动作
                        for 持有 in 页表.values():
                            持有['controller'].重绑(新动作)

                    def 加载地址(标识,值):
                        '校验并加载这一签的地址'
                        控制器=取控制器(标识)
                        if 控制器 is not None:
                            控制器.加载地址(值)

                    def 恢复(标识):
                        '恢复这一签保存的地址'
                        控制器=取控制器(标识)
                        if 控制器 is not None:
                            控制器.恢复()

                    def 后退(标识):
                        '这一签后退'
                        控制器=取控制器(标识)
                        if 控制器 is not None:
                            控制器.后退()

                    def 前进(标识):
                        '这一签前进'
                        控制器=取控制器(标识)
                        if 控制器 is not None:
                            控制器.前进()

                    def 刷新(标识):
                        '恢复保存的地址，或重载已经打开的页'
                        控制器=取控制器(标识)
                        if 控制器 is not None:
                            控制器.刷新()

                    def 设沙箱(标识,启用):
                        '应用这一签的嵌入沙箱开关'
                        控制器=取控制器(标识)
                        if 控制器 is not None:
                            控制器.设沙箱(启用)

                    面={
                        'keyedHooks':{'browserState':浏览器状态},
                        'mount':挂载,
                        'dispose':拆除,
                        'rebind':重绑,
                        'loadUrl':加载地址,
                        'restore':恢复,
                        'goBack':后退,
                        'goForward':前进,
                        'reload':刷新,
                        'setSandbox':设沙箱,
                    }
                    会话表[会话标识]=面
                    return 面

                return 范围.slots.register({
                    'name':席名右侧签正文,
                    'key':浏览器标识,
                    'locale':命名空间,
                    'store':存储句柄,
                    'inject':注入,
                },浏览器体)

            return 范围.slots.inject(席名右侧签正文,登记)

        范围.副作用(挂正文,'ui-sidebar-browser.body')

    if 桌面 is None:
        def 取内嵌页(会话标识):
            '网页壳不按会话分提供方'
            return 创建内嵌帧页

        装帧(上下文,取内嵌页)
    else:
        def 等桌面(范围):
            '工作区服务就绪后，用 Electron 宾客装页'
            列表源=范围.workspaces.list

            def 取电子页(会话标识):
                '这一会话的页工厂。存储账户等列表就绪后再定'
                def 工作区账户(信号):
                    '等工作区列表就绪，再用规范工作目录做存储账户'
                    if 信号.aborted:
                        原因=getattr(信号,'reason',None)
                        if isinstance(原因,BaseException):
                            raise 原因
                        raise RuntimeError('aborted' if 原因 is None else str(原因))
                    if 列表源.getSnapshot()['phase']!='ready':
                        门=threading.Event()
                        箱={'错误':None}
                        退订=[None]

                        def 停止():
                            '摘掉列表订阅'
                            函数=退订[0]
                            退订[0]=None
                            if 函数 is not None:
                                函数()

                        def 中止了():
                            '列表还没就绪就被取消'
                            停止()
                            箱['错误']=getattr(信号,'reason',None)
                            门.set()

                        def 变更():
                            '就绪后继续'
                            if 列表源.getSnapshot()['phase']!='ready':
                                return
                            停止()
                            信号.removeEventListener('abort',中止了)
                            门.set()

                        退订[0]=列表源.subscribe(变更)
                        信号.addEventListener('abort',中止了,{'once':True})
                        if 列表源.getSnapshot()['phase']=='ready':
                            停止()
                            信号.removeEventListener('abort',中止了)
                        else:
                            门.wait()
                        if 箱['错误'] is not None or 信号.aborted:
                            错误=箱['错误']
                            if isinstance(错误,BaseException):
                                raise 错误
                            raise RuntimeError('aborted' if 错误 is None else str(错误))
                    if 信号.aborted:
                        raise RuntimeError('aborted')
                    工作区=None
                    for 项 in 列表源.getSnapshot()['items']:
                        for 标识 in 项['sessionIds']:
                            if 标识==会话标识:
                                工作区=项
                                break
                        if 工作区 is not None:
                            break
                    if 工作区 is None:
                        return 'session:'+str(会话标识)
                    return 'cwd:'+str(工作区['path'])

                def 造页(选项):
                    '组装空闲的 Electron 页。宾客等到挂载和导航再创建'
                    帧盒=[None]

                    def 已挂():
                        '容器挂上后附着宾客'
                        帧盒[0].挂上()

                    def 已卸():
                        '容器拿走前脱离宾客'
                        帧盒[0].脱离()

                    呈现=electron网页视图呈现形式({'mounted':已挂,'unmounted':已卸})
                    帧=electron网页视图实现(选项,桌面,工作区账户,呈现)
                    帧盒[0]=帧
                    return {'frame':帧,'presentation':呈现}

                return 造页

            装帧(范围,取电子页)

        上下文.inject(['workspaces'],等桌面)

    def 挂标题():
        '芯片标题进带键席'
        def 登记标题():
            '登记 browser 标题'
            return 上下文.slots.register({
                'name':席名右侧签标题,
                'key':浏览器标识,
                'store':存储句柄,
            },浏览器标题)

        return 上下文.slots.inject(席名右侧签标题,登记标题)

    上下文.副作用(挂标题,'ui-sidebar-browser.title')


inject=依赖
apply=应用
