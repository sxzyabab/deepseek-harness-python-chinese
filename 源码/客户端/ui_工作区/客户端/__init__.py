'工作区插件的浏览器半。登记浏览区、选择器、行动作和提示'
from ...ui_基础界面组件.剪贴板 import 写剪贴板
from ...存储 import 创建快照存储
from ..异常 import 错误名
from . import 文案
from . import 导航
from . import 快捷键
from . import 存储
from . import 树
from . import 置顶顺序
from . import 选择器
from . import 约定
from . import 浮动提示
from . import 会话动作
from . import 行
from .文案 import 中文,英文,填入
from .会话动作.派生 import 派生
from .约定.槽位 import 菜单打开状态工厂

__all__=[
    '文案','导航','快捷键','存储','树','置顶顺序','选择器','约定','浮动提示','会话动作','行',
    '依赖','应用',
]

依赖=['slots','sessions','workspaces','locale','remote','remote.directoryPicker','layout','shortcuts','remoteAccess']
命名空间='workspace'#词典命名空间保持英文

def 应用(上下文,配置=None):
    '槽位声明到了再登记浏览区、行动作、对话框、提示和选择器'
    会话=上下文.获取服务('sessions')#会话
    工作区=上下文.获取服务('workspaces')#工作区
    视图句柄=存储.创建工作区查看存储()#查看存储
    视图实例=视图句柄.create()#这一份实例
    def 创建同一份():
        '浏览区和提示共用这一份查看存储'
        return 视图实例#同一份
    视图存储=存储句柄一样(视图句柄,创建同一份)#登记用的句柄
    行提示=创建快照存储(None)#当前提示
    序号=[0]#提示序号
    def 通知(提示):
        '换一条提示。序号变了，保持时间重新算'
        序号[0]=序号[0]+1#下一号
        行提示.set({**提示,'seq':序号[0]})#写入
    控制=快捷键.创建工作区快捷控制()#快捷请求
    界面工作区=导航.工作区界面服务(
        上下文,上下文.remote.directoryPicker,工作区,会话,视图实例.actions,通知,
    )#导航
    def 工作区访问(工作区号,动作=None):
        '这个工作区能不能做这个动作。渲染器若只传工作区号，动作空时没有源'
        if 动作 is None:#没有动作
            return None#没有源
        return 上下文.remoteAccess.来源('workspace',工作区号,动作)#源
    上下文.slots.provideRoot({
        'hooks':{'workspaces':工作区.list},#工作区列表
        'keyedHooks':{'workspaceAccess':工作区访问},#按工作区
    })#根钩子
    def 登记词典():
        '登记中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-workspace: dictionaries')#词典
    def 检索会话(查询,信号):
        '失败抛出宿主说明'
        结果=会话.search(查询,信号)#检索
        if hasattr(结果,'然后') or hasattr(结果,'then'):#期约
            结果=导航.取同步结果(结果)#取出
        if not isinstance(结果,dict) or not 结果.get('ok'):#失败
            错=结果.get('error') if isinstance(结果,dict) else None#错误
            消息=错.get('message') if isinstance(错,dict) else getattr(错,'message','')#说明
            raise RuntimeError(消息)#抛出
        return 结果.get('value')#命中
    def 流源(洞名):
        '这个目录流洞有没有被填上'
        def 快照():
            '有条目就是占用'
            return len(上下文.slots.entries(洞名))>0#占用
        def 订阅(监听):
            '洞变化'
            return 上下文.slots.subscribe(洞名,监听)#退订
        return {'getSnapshot':快照,'subscribe':订阅}#源
    浏览流=流源('sidebar.workspaces.directoryFlow')#侧栏
    def 宿主快照():
        '当前宿主事实。上游读 remote.$host'
        return getattr(上下文.remote,'$host',None)#宿主
    def 宿主订阅(监听):
        '连接重置'
        return 上下文.on('connection/reset',监听)#订
    宿主={'getSnapshot':宿主快照,'subscribe':宿主订阅}#宿主
    挑选流=流源('conversation.hero.workspace.directoryFlow')#英雄
    def 打开会话(会话号):
        '打开这一条'
        界面工作区.openSession(会话号)#打开
    def 投影置顶(快照):
        '置顶号的集合'
        return set(快照.get('pinnedSessionIds') or [])#集合
    def 投影归档(快照):
        '归档号的集合'
        return set(快照.get('archivedSessionIds') or [])#集合
    def 投影改名(状态):
        '当前改名请求'
        return 状态.get('renameTarget')#请求
    置顶集=派生(工作区.list,投影置顶)#置顶
    归档集=派生(工作区.list,投影归档)#归档
    改名请求=派生(控制['state'],投影改名)#改名
    归档请求=创建快照存储(None)#停止并归档的确认
    def 取消归档(会话号):
        '撤销归档。失败只记日志'
        try:#取消
            界面工作区.unarchiveSession(会话号)#取消
        except Exception as 原因:#失败
            print('session unarchive rejected:',原因)#日志
    def 改名会话(会话号,标题):
        '经引用改标题'
        def 改(引用):
            '绑定上改名'
            结果=引用.binding.session.rename(标题)#改名
            if isinstance(结果,dict) and not 结果.get('ok'):#被拒
                错=结果.get('error') or {}#错误
                raise RuntimeError(错.get('message') if isinstance(错,dict) else str(错))#抛出
            return 结果#结果
        会话.using(会话号,{'source':'workspaceOperation'},改)#占用
    def 置顶注入():
        '置顶菜单和按钮'
        def 置顶(会话号):
            '失败发提示'
            try:#置顶
                界面工作区.pinSession(会话号)#置顶
            except Exception:#失败
                通知({'kind':'pinFailed'})#提示
        def 取消置顶(会话号):
            '失败发提示'
            try:#取消
                界面工作区.unpinSession(会话号)#取消
            except Exception:#失败
                通知({'kind':'unpinFailed'})#提示
        return {'hooks':{'pinned':置顶集,'archived':归档集},'pinSession':置顶,'unpinSession':取消置顶}#注入
    def 归档注入():
        '归档。运行中的工作先问要不要停'
        def 归档(会话号):
            '成功发可撤销的提示。运行中则打开确认'
            try:#归档
                界面工作区.archiveSession(会话号)#归档
                通知({'kind':'archived','sessionId':会话号})#已归档
            except Exception as 原因:#失败
                活动=None#运行中的工作
                if 错误名(原因)=='WorkspaceArchiveError':#归档被拒
                    远程=getattr(原因,'rpcError',None)#远程
                    码=远程.get('code') if isinstance(远程,dict) else getattr(远程,'code',None)#码
                    细节=远程.get('details') if isinstance(远程,dict) else getattr(远程,'details',None)#细节
                    if 码=='workspace/session-active' and isinstance(细节,dict):#还在跑
                        活动=细节.get('activity')#工作
                if 活动 is None:#其它失败
                    print('session archive rejected:',原因)#日志
                    return#停
                摘要=会话.list.getSnapshot()['byId'].get(会话号) or {}#摘要
                显示=摘要.get('displayTitle') or 会话号#标题
                归档请求.set({'sessionId':会话号,'displayTitle':显示,'activity':活动})#确认
        return {'hooks':{'archived':归档集},'archiveSession':归档,'unarchiveSession':取消归档}#注入
    归档面=归档注入()#快捷键和菜单共用这一次的归档函数
    def 报告分叉失败(原因):
        '快捷键分叉失败'
        通知({'kind':'shortcutForkFailed','reason':原因})#提示
    快捷键.安装工作区快捷键(上下文,界面工作区,控制,归档面['archiveSession'],报告分叉失败)#命令
    def 确认注入():
        '停止并归档对话框'
        def 结束():
            '关掉确认'
            归档请求.set(None)#清
        def 停止并归档(会话号):
            '先停再归档，然后提示'
            界面工作区.archiveSession(会话号,{'stopActivity':True})#归档
            通知({'kind':'stoppedAndArchived','sessionId':会话号})#提示
        return {'hooks':{'archiveRequest':归档请求},'settleSessionArchive':结束,'stopAndArchiveSession':停止并归档}#注入
    def 分叉注入():
        '分叉。需要迁移时提示先打开原会话'
        def 分叉(会话号):
            '不自动迁移'
            def 创建了(子号):
                '记一次侧栏分叉'
                分析=上下文.获取服务('productAnalytics',False)#分析
                if 分析 is not None:#有
                    分析.track('branch_session_click',{'session_id':子号,'parent_session_id':会话号,'click_position':'sidebar'})#事件
            try:#分叉
                界面工作区.forkSession(会话号,创建了,{'allowMigration':False})#分叉
            except Exception as 错误:#失败
                远程=getattr(错误,'rpcError',None)#远程
                码=远程.get('code') if isinstance(远程,dict) else getattr(远程,'code',None)#码
                if 错误名(错误)=='SessionForkError' and 码=='session/migration-required':#要先迁移
                    通知({'kind':'forkRequiresOpen','sessionId':会话号})#提示
        return {'forkSession':分叉}#注入
    def 会话号注入():
        '复制会话号'
        def 复制(会话号):
            '按剪贴板结果发提示'
            已复制=写剪贴板(会话号)#写入
            通知({'kind':'sessionIdCopied' if 已复制 else 'sessionIdCopyFailed'})#提示
        return {'copySessionId':复制}#注入
    def 改名注入():
        '菜单只提出改名'
        return {'requestSessionRename':控制['rename']}#注入
    def 改名框注入():
        '对话框执行改名'
        return {'hooks':{'renameRequest':改名请求},'settleSessionRename':控制['closeRename'],'renameSession':改名会话}#注入
    def 打开分叉源(会话号):
        '归档的原会话不能打开'
        if 会话号 in (工作区.list.getSnapshot().get('archivedSessionIds') or []):#已归档
            通知({'kind':'archivedNotOpenable'})#提示
            return#停
        打开会话(会话号)#打开
    def 显示已归档():
        '筛选改成显示已归档'
        视图实例.actions['setArchivedFilter']('show')#筛选
    提示动作={'undoArchive':取消归档,'showArchived':显示已归档,'openForkSource':打开分叉源}#提示动作
    登记提示(上下文,视图存储,提示动作)#提示
    def 提示注入():
        '浮层上的提示'
        def 收起():
            '拿掉提示'
            行提示.set(None)#清
        return {'hooks':{'toast':行提示},'dismissToast':收起}#注入
    def 浏览注入(*位置参数):
        '浏览区能做的事。槽位会把存储动作传进来'
        def 重命名工作区(工作区号,标题):
            '改工作区名'
            return 工作区.rename(工作区号,标题)#改名
        def 删除工作区(工作区号):
            '删登记'
            return 工作区.delete(工作区号)#删除
        def 插到前面(工作区号,锚=None):
            '调整顺序'
            return 工作区.insertBefore(工作区号,锚)#插入
        def 取消归档一条(会话号):
            '搜索结果上的恢复'
            return 界面工作区.unarchiveSession(会话号)#恢复
        def 不能打开():
            '点了归档行'
            通知({'kind':'archivedNotOpenable'})#提示
        def 开始(工作区号=None,选项=None):
            '新建或复用会话'
            界面工作区.startSession(工作区号,选项)#开始
        def 创建(输入):
            '把目录登记成工作区'
            return 工作区.create(输入)#创建
        return {
            'startSession':开始,
            'open':打开会话,
            'searchSessions':检索会话,
            'searchResultLimit':会话.searchResultLimit,
            'requestSessionRename':控制['rename'],
            'notifyArchivedNotOpenable':不能打开,
            'renameWorkspace':重命名工作区,
            'deleteWorkspace':删除工作区,
            'insertWorkspaceBefore':插到前面,
            'unarchiveSession':取消归档一条,
            'createWorkspace':创建,
            'requestSearch':控制['search'],
            'requestAddWorkspace':控制['add'],
            'closeAddWorkspace':控制['closeAdd'],
            'setDirectoryBusy':控制['directoryBusy'],
            'hooks':{
                'directoryFlow':浏览流,
                'hostInfo':宿主,
                'workspaceShortcuts':控制['state'],
                'shortcuts':上下文.shortcuts.catalog,
            },
        }#注入
    def 挑选注入():
        '选择器只创建工作区'
        def 创建工作区(输入):
            '把挑到的目录登记成工作区'
            return 工作区.create(输入)#创建
        return {'createWorkspace':创建工作区,'hooks':{'directoryFlow':挑选流}}#注入
    def 登记浏览区():
        '侧栏浏览区，并声明它的子洞'
        return 上下文.slots.register({
            'name':'sidebar.workspaces',
            'children':{
                'sidebar.workspaces.directoryFlow':{'kind':'single','scope':'root'},
                'sidebar.workspaces.session.menu.item':{
                    'kind':'list','scope':'root',
                    'inject':{'hooks':{'menuOpenState':菜单打开状态工厂,'shortcuts':上下文.shortcuts.catalog}},
                },
                'sidebar.workspaces.session.row.action':{'kind':'list','scope':'root'},
                'sidebar.session.row.leading':{'kind':'list','scope':'root'},
                'sidebar.session.row.hover':{'kind':'list','scope':'root'},
            },
            'store':视图存储,
            'inject':浏览注入,
            'locale':命名空间,
        },行.浏览区.工作区浏览区组件)#浏览区
    上下文.slots.inject('sidebar.workspaces',登记浏览区)#等声明
    def 登记菜单项():
        '菜单里的置顶、改名、分叉、归档、复制号'
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.menu.item','id':'pin','order':100,'locale':命名空间,'inject':置顶注入},会话动作.置顶会话.置顶会话菜单项组件)#置顶
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.menu.item','id':'rename','order':200,'locale':命名空间,'inject':改名注入},会话动作.重命名会话.重命名会话菜单项组件)#改名
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.menu.item','id':'fork','order':300,'locale':命名空间,'inject':分叉注入},会话动作.分叉会话.分叉会话菜单项组件)#分叉
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.menu.item','id':'archive','order':400,'locale':命名空间,'inject':归档注入},会话动作.归档会话.归档会话菜单项组件)#归档
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.menu.item','id':'session-id','order':450,'locale':命名空间,'inject':会话号注入},会话动作.会话标识.会话标识菜单项组件)#复制号
    上下文.slots.inject('sidebar.workspaces.session.menu.item',登记菜单项)#等声明
    def 登记行按钮():
        '行尾的归档和置顶'
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.row.action','id':'archive','order':100,'locale':命名空间,'inject':归档注入},会话动作.归档会话.归档会话行按钮组件)#归档
        yield 上下文.slots.register({'name':'sidebar.workspaces.session.row.action','id':'pin','order':200,'locale':命名空间,'inject':置顶注入},会话动作.置顶会话.置顶会话行按钮组件)#置顶
    上下文.slots.inject('sidebar.workspaces.session.row.action',登记行按钮)#等声明
    def 登记浮层():
        '改名、停止归档和提示都在全框浮层里'
        yield 上下文.slots.register({'name':'shell.overlay','id':'workspace.session-rename','locale':命名空间,'inject':改名框注入},会话动作.重命名会话.会话重命名对话框组件)#改名
        yield 上下文.slots.register({'name':'shell.overlay','id':'workspace.session-archive','locale':命名空间,'inject':确认注入},会话动作.归档会话.会话归档确认对话框组件)#归档确认
        yield 上下文.slots.register({
            'name':'shell.overlay','id':'workspace.row-toast','inject':提示注入,
            'children':{'workspace.toast':{'kind':'keyed','scope':'root'}},
        },会话动作.行动作提示.行动作提示组件)#提示
    上下文.slots.inject('shell.overlay',登记浮层)#等声明
    def 登记选择器():
        '对话空态的工作区选择'
        return 上下文.slots.register({
            'name':'conversation.hero.workspace',
            'children':{'conversation.hero.workspace.directoryFlow':{'kind':'single','scope':'root'}},
            'inject':挑选注入,
            'locale':命名空间,
        },选择器.工作区选择器组件)#选择器
    上下文.slots.inject('conversation.hero.workspace',登记选择器)#等声明

def 存储句柄一样(原句柄,创建):
    '规格仍是原句柄的，create 总返回已经造好的那一份'
    class 句柄:
        '登记时不要再造第二份'
        def __init__(自身):
            '记下规格和工厂'
            自身.spec=原句柄.spec#规格
            自身.create=创建#工厂
    return 句柄()#句柄

def 登记提示(上下文,视图存储,动作):
    '每种提示只提供展示字段。归档提示还能切到显示已归档'
    def 筛选动作(文案,收起):
        '或，筛选已归档会话'
        def 点():
            '收起并显示已归档'
            收起()#收起
            动作['showArchived']()#筛选
        return {'prefix':中文['toast.archivedOr'],'label':中文['toast.archivedFilter'],'onClick':点}#动作
    上下文.slots.registerFactory({'name':'workspace.toast.content','scope':'root'},浮动提示.浮动提示.工作区提示组件)#工厂
    def 登记():
        '按 kind 登记'
        def 一条(键,展示):
            '一种提示'
            def 注入():
                '展示函数'
                return {'display':展示}#注入
            return 上下文.slots.register({'name':'workspace.toast','key':键,'locale':命名空间,'inject':注入},浮动提示.浮动提示.提示条目组件)#登记
        def 复制成功(通知,文案,收起=None):
            'Session ID 已复制'
            return {'text':中文['toast.sessionIdCopied'],'tone':'success'}#成功
        def 复制失败(通知,文案,收起=None):
            '复制失败'
            return {'text':中文['toast.sessionIdCopyFailed'],'tone':'warning'}#警告
        def 置顶失败(通知,文案,收起=None):
            '置顶失败'
            return {'text':中文['toast.pinFailed'],'tone':'warning'}#警告
        def 取消置顶失败(通知,文案,收起=None):
            '取消置顶失败'
            return {'text':中文['toast.unpinFailed'],'tone':'warning'}#警告
        def 不能打开(通知,文案,收起=None):
            '归档的不能打开'
            return {'text':中文['toast.archivedNotOpenable'],'tone':'warning'}#警告
        def 默认失败(通知,文案,收起=None):
            '默认工作区没建成'
            return {'text':中文['defaultWorkspace.failed'],'tone':'warning'}#警告
        def 分叉失败(通知,文案,收起=None):
            '没有完成的轮次，或分叉失败'
            键='shortcut.noCompletedTurn' if 通知.get('reason')=='unavailable' else 'shortcut.forkFailed'#键
            return {'text':中文[键],'tone':'plain'}#普通
        def 创建失败(通知,文案,收起=None):
            '带上失败说明'
            return {'text':填入(中文['toast.createFailed'],{'message':通知.get('message')}),'tone':'warning','holdMs':6000}#警告
        def 要打开原会话(通知,文案,收起=None):
            '先打开原会话'
            def 点():
                '收起并打开'
                if 收起 is not None:#有
                    收起()#收起
                动作['openForkSource'](通知.get('sessionId'))#打开
            return {'text':中文['toast.forkRequiresOpen'],'tone':'warning','holdMs':6000,'actions':[{'label':中文['toast.openForkSource'],'onClick':点}]}#动作
        def 已归档(通知,文案,收起=None):
            '可撤销'
            def 点():
                '撤销'
                if 收起 is not None:#有
                    收起()#收起
                动作['undoArchive'](通知.get('sessionId'))#撤销
            return {'text':中文['toast.archived'],'tone':'success','holdMs':6000,'actions':[{'label':中文['toast.archivedUndo'],'onClick':点}]}#动作
        def 已停止(通知,文案,收起=None):
            '停止并归档后可撤销'
            def 点():
                '撤销'
                if 收起 is not None:#有
                    收起()#收起
                动作['undoArchive'](通知.get('sessionId'))#撤销
            return {'text':中文['toast.stoppedAndArchived'],'tone':'success','holdMs':6000,'actions':[{'label':中文['toast.archivedUndo'],'onClick':点}]}#动作
        def 归档注入展示():
            '展示加筛选动作'
            return {'display':已归档,'filterAction':筛选动作}#注入
        def 停止注入展示():
            '展示加筛选动作'
            return {'display':已停止,'filterAction':筛选动作}#注入
        yield 一条('sessionIdCopied',复制成功)#复制成功
        yield 一条('sessionIdCopyFailed',复制失败)#复制失败
        yield 一条('pinFailed',置顶失败)#置顶失败
        yield 一条('unpinFailed',取消置顶失败)#取消失败
        yield 一条('archivedNotOpenable',不能打开)#不能打开
        yield 一条('defaultWorkspaceFailed',默认失败)#默认工作区
        yield 一条('shortcutForkFailed',分叉失败)#分叉失败
        yield 一条('createFailed',创建失败)#创建失败
        yield 一条('forkRequiresOpen',要打开原会话)#要打开
        yield 上下文.slots.register({'name':'workspace.toast','key':'archived','locale':命名空间,'store':视图存储,'inject':归档注入展示},浮动提示.浮动提示.归档提示条目组件)#已归档
        yield 上下文.slots.register({'name':'workspace.toast','key':'stoppedAndArchived','locale':命名空间,'store':视图存储,'inject':停止注入展示},浮动提示.浮动提示.归档提示条目组件)#已停止
    上下文.slots.inject('workspace.toast',登记)#等提示槽

inject=依赖#框架槽
apply=应用#框架槽
