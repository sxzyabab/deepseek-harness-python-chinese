from . import 文案,定义,存储,目录节点,文件体,文件标题
from ...存储 import 声明存储
from ....类型化远程调用.协议.异常 import 远程错误
from ....基础设施.通用工具 import 启动守护线程,获取内部数据

__all__=['依赖','应用','文案','定义','存储','目录节点','文件体','文件标题']

依赖=['slots','locale','sidebarRightTabs','sidebarRight','remote','remote.workspaceFiles']

def 应用(上下文,配置=None):
    '登记 files 类型、词典、快捷键，再挂正文和芯片标题'
    def 登记快捷键(快捷上下文):
        'shortcuts 就绪后登记工作区文件命令'
        def 登记():
            '命令的可见名称用中文表原文'
            def 标签():
                '命令名称'
                return 文案.中文['guide.title']
            def 解析(面):
                '没有当前会话就挡住，否则打开文件页'
                if isinstance(面,dict):
                    元素=面['target'] if 'target' in 面 else None
                else:
                    元素=面.target
                目标=上下文.sidebarRight.commandTarget(元素)
                if 目标 is None:
                    return {'status':'blocked','reason':文案.中文['shortcut.noSession']}
                def 跑():
                    '从当前目标打开文件页'
                    上下文.sidebarRight.openTabFromTarget('files',目标)
                return {'status':'handled','run':跑}
            return 快捷上下文.shortcuts.register({
                'id':'workspace.files',
                'label':标签,
                'aliases':['workspace files','files'],
                'defaults':{
                    'desktop:macos':{'code':'KeyP','modifiers':['primary']},
                    'desktop:windows':{'code':'KeyP','modifiers':['primary']},
                    'desktop:linux':{'code':'KeyP','modifiers':['primary']},
                    'web:macos':{'code':'KeyP','modifiers':['primary','alt']},
                    'web:windows':{'code':'KeyP','modifiers':['primary','alt']},
                },
                'regions':['page','editable','terminal'],
                'modals':[],
                'resolve':解析,
            })
        return 快捷上下文.副作用(登记,'ui-sidebar-files: shortcut')
    上下文.inject(['shortcuts'],登记快捷键)
    def 类型名():
        '页签类型名'
        return 文案.中文['type.label']
    def 向导名():
        '向导标题'
        return 文案.中文['guide.title']
    def 向导说明():
        '向导说明'
        return 文案.中文['guide.description']
    def 登记类型():
        '登记 files 类型。向导图标用上游文件夹页字形'
        return 上下文.sidebarRightTabs.register({
            'id':定义.文件标识,
            'kind':'files',
            'priority':'builtin',
            'title':类型名,
            'guide':[{
                'id':'workspace',
                'commandId':'workspace.files',
                'order':10,
                'title':向导名,
                'description':向导说明,
                'icon':定义.引导文件标记,
            }],
        })
    上下文.副作用(登记类型,'ui-sidebar-files: files type')
    def 登记词典():
        '留下中英文案表。界面显示不读英文表'
        return 上下文.locale.register('sidebarFiles',{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-sidebar-files: dictionaries')
    存储句柄=声明存储({
        'init':存储.初值,
        'actions':{
            'autoRefresh':存储.自动刷新,
            'start':存储.启动,
            'loading':存储.加载中,
            'loaded':存储.已加载,
            'failed':存储.已失败,
            'toggled':存储.已切换,
            'scrolled':存储.已滚动,
            'reset':存储.重置,
            'forget':存储.遗忘,
        },
    })
    def 注入面(会话标识,动作):
        '按会话绑上列举、监视和目录树'
        代次表={}
        根表={}
        def 加载(标签标识,路径,信号):
            '列这一级。更新的请求或记录已结束则不写'
            if 目录节点.已中止(信号):
                return None
            按路径=代次表[标签标识] if 标签标识 in 代次表 else {}
            代次表[标签标识]=按路径
            代次=(按路径[路径] if 路径 in 按路径 else 0)+1
            按路径[路径]=代次
            动作['loading'](标签标识,路径)
            结果=上下文.remote.workspaceFiles.list(会话标识,路径,信号)
            if 结果['ok']:
                值=结果['value']
                结算={'ok':True,'value':{'entries':值['entries'],'truncated':值['truncated']}}
            else:
                结算=结果
            现行=代次表[标签标识] if 标签标识 in 代次表 else None
            if 目录节点.已中止(信号) or 现行 is None or 现行.get(路径)!=代次:
                return None
            if 结算['ok']:
                动作['loaded'](标签标识,路径,结算['value'])
                return 结算['value']
            动作['failed'](标签标识,路径,结算['error'])
            return None
        def 监视本标签(路径,寿命):
            '观察这一目录，交出 ready 或 change'
            if 目录节点.已中止(寿命):
                return
            远程=上下文.remote
            def 开口(代寿命):
                '打开这一代变更流'
                return 远程.workspaceFiles.changes(会话标识,路径,代寿命)
            def 已结束(_已接受=None):
                '流结束时的错误'
                return Exception('Directory watch ended: '+路径)
            流=获取内部数据(远程,'stream')({
                'name':'directory '+路径,
                'open':开口,
                'ended':已结束,
            })
            def 等中止():
                '记录结束时拆掉流'
                寿命.wait()
                流.dispose()
            启动守护线程(等中止)
            try:
                for 条目 in 流:
                    if 目录节点.已中止(寿命):
                        return
                    值=条目.value
                    if 值['kind']=='ready':
                        条目.accept()
                    yield 值['kind']
            finally:
                流.dispose()
        def 刷新(标签标识):
            '重读已打开的目录'
            根=根表.get(标签标识)
            if 根 is not None:
                根.刷新树()
        def 设自动(标签标识,启用):
            '改自动刷新，不关掉监视'
            动作['autoRefresh'](标签标识,启用)
            根=根表.get(标签标识)
            if 根 is not None:
                根.设自动(启用)
        def 启动(标签标识,根,信号):
            '播种这一标签的树并打开根目录'
            动作['start'](标签标识,根)
            def 清理():
                '关掉监视，清掉代次，忘掉桶'
                节点=根表.get(标签标识)
                if 节点 is not None:
                    节点.关闭()
                if 标签标识 in 根表:
                    del 根表[标签标识]
                if 标签标识 in 代次表:
                    del 代次表[标签标识]
                动作['forget'](标签标识)
            if 目录节点.已中止(信号):
                清理()
            else:
                def 等结束():
                    '信号置位后清理'
                    信号.wait()
                    清理()
                启动守护线程(等结束)
            def 加载路径(路径,寿命):
                '这一标签的列举'
                return 加载(标签标识,路径,寿命)
            def 失败路径(路径,错误):
                '监视失败写成远程错误。记录已结束则不写'
                if 目录节点.已中止(信号):
                    return
                if isinstance(错误,BaseException):
                    消息=错误.message if hasattr(错误,'message') else str(错误)
                else:
                    消息=str(错误)
                动作['failed'](标签标识,路径,远程错误('gateway/internal',消息,{}))
            根表[标签标识]=目录节点.目录节点(
                根,加载路径,监视本标签,失败路径,信号,
            ).打开()
        def 对外加载(标签标识,路径,信号):
            '再列一级。调用方不等待'
            启动守护线程(加载,标签标识,路径,信号)
        def 切换(标签标识,父路径,路径,展开表,信号):
            '展开或折叠。祖先还在还原时保留意图'
            if 目录节点.已中止(信号):
                return
            根=根表.get(标签标识)
            if 根 is None:
                return
            父=根.查找(父路径)
            if 父 is None and 父路径 not in 展开表:
                return
            正在折叠=路径 in 展开表
            if 正在折叠:
                下一=[值 for 值 in 展开表 if 值!=路径]
            else:
                下一=list(展开表)+[路径]
            根.设展开(下一)
            if 正在折叠:
                if 父 is not None:
                    父.折叠(路径)
            else:
                if 父 is not None:
                    父.展开(路径,下一)
            动作['toggled'](标签标识,路径)
        return {
            'refresh':刷新,
            'setAutoRefresh':设自动,
            'start':启动,
            'load':对外加载,
            'toggle':切换,
        }
    def 挂正文():
        '正文进带键席位'
        def 登记正文():
            '登记 files 正文'
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab',
                'key':定义.文件标识,
                'locale':'sidebarFiles',
                'store':存储句柄,
                'inject':注入面,
                'children':{
                    'sidebar.right.tab.files.actions':{'kind':'list','scope':'session'},
                },
            },文件体.挂上文件体)
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)
    上下文.副作用(挂正文,'ui-sidebar-files: files tab body')
    def 挂标题():
        '芯片标题进带键席位'
        def 登记标题():
            '登记 files 芯片标题'
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab.title',
                'key':定义.文件标识,
            },文件标题.挂上文件标题)
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)
    上下文.副作用(挂标题,'ui-sidebar-files: files tab title')

inject=依赖
apply=应用
