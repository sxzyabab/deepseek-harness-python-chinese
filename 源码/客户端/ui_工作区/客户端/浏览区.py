from nicegui import ui as 界面
from ....基础设施.通用工具 import 当前毫秒
from ..异常 import 页面失败文案
from .树 import (#树派生
    未分组键,
    按近因排序,
    调和手动顺序,
    钉住当前空白,
    可见会话标识,
    派生分组,
    派生扁平,
    派生检索结果,
)#树导出结束
from .存储 import 扁平会话顺序键#扁平账本键
from .行.行 import 项目行,会话行,检索结果行#行组件
from .选择器 import 工作区挑选流#添加流程

__all__=[#仅中文公开名
    '工作区浏览区',
    '消毒检索查询',
    '调和会话顺序',
    '下一会话顺序账本',
    '展开滑动毫秒',
    '检索防抖毫秒',
    '检索查询最大码元',
    '折叠会话上限',
    '样式表',
]#公开面结束

展开滑动毫秒=300#轨到宽的滑动时长
检索防抖毫秒=250#击键到宿主正文检索的停顿
检索查询最大码元=500#session.search 线路上限（UTF-16 码元）
折叠会话上限=5#每组默认可见会话数

样式表='''#对齐 WorkspaceBrowser.module.css
.root{--dsh-session-list-scrollbar-offset:2px;flex:1;min-height:0;display:flex;flex-direction:column;box-sizing:border-box;padding-right:var(--dsh-sidebar-inline-padding,12px)}
.root.rail{padding-right:0}
.sectionHeader{flex:none;display:flex;align-items:center;justify-content:flex-end;gap:4px;height:36px;padding-left:4px;margin-bottom:4px;box-sizing:border-box;border-radius:var(--dsw-radius-md);overflow:hidden;color:var(--dsw-alias-label-tertiary)}
.root:not(.rail) .sectionHeader{margin-top:2px;margin-right:-4px}
.sectionLabel{flex:none;max-width:45%;min-width:0;overflow:hidden;white-space:nowrap;line-height:20px;font-size:14px;font-weight:400}
.sectionLabelHidden{max-width:0;margin-right:-4px;opacity:0;transform:translateX(-4px);visibility:hidden}
.searchInput{flex:1;min-width:0;height:28px;padding:0 8px;border:none;border-radius:var(--dsw-radius-sm);background:var(--dsw-alias-bg-module-platform);color:var(--dsw-alias-label-primary);font-size:13px}
.listArea{flex:1;min-height:0;margin-right:2px;overflow:auto;scrollbar-gutter:stable}
.empty{padding:12px;color:var(--dsw-alias-label-tertiary);font-size:13px}
.sessionOverflowButton{display:block;width:100%;padding:4px 8px;border:none;background:transparent;color:var(--dsw-alias-state-business-primary);cursor:pointer;text-align:left}
.renameError{color:var(--dsw-alias-state-error-primary);font-size:12px;line-height:18px}
.iconButton{flex:none;display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border:none;border-radius:var(--dsw-radius-sm);padding:0;background:transparent;cursor:pointer;color:var(--dsw-alias-label-secondary)}
.iconButton:hover{background:var(--dsw-alias-interactive-bg-hover)}
.workspace-browser{display:flex;flex-direction:column;min-width:0;width:100%}
.区头{width:100%;align-items:center;justify-content:space-between;flex-wrap:nowrap;min-height:36px}
.区头题{flex:1 1 auto;min-width:0}
button.q-btn.浏览钮{width:28px !important;height:28px !important;min-height:28px !important;padding:0 !important;background:transparent !important;color:var(--dsw-alias-label-primary,#111827) !important;box-shadow:none !important}
'''#样式表结束

样式已登记=False

def 登记样式():
    '同一段浏览区样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表, shared=True)
    样式已登记=True

def 消毒检索查询(值):#守住 session.search 线路契约
    '去掉 NUL，截到 500 个 UTF-16 码元且不拆代理对'
    无空=值.replace('\0','')#去 NUL
    if len(无空)<=检索查询最大码元:#未超
        return 无空#原样
    末=检索查询最大码元#截断点
    前=ord(无空[末-1])#截断前一码元
    后=ord(无空[末]) if 末<len(无空) else 0#截断处码元
    if 0xD800<=前<=0xDBFF and 0xDC00<=后<=0xDFFF:#高代理+低代理
        末-=1#不拆对
    return 无空[:末]#截断

def 切换成员(列表,键):#不可变成员切换
    '展开数组的成员开关'
    if 键 in 列表:#已有则去掉
        return [项 for 项 in 列表 if 项!=键]#去掉
    return list(列表)+[键]#追加

def 调和会话顺序(会话标识列表,已存):#调和已存顺序与当前账本
    '接受已存顺序，未知键跳过，新成员追加到末尾'
    if 已存 is None:#无已存
        return list(会话标识列表)#原样拷贝
    有序=[]#结果
    已纳入=set()#已纳入
    集=set(会话标识列表)#id 集
    for 键 in 已存:#先走已存
        if 键 not in 集 or 键 in 已纳入:#未知或重复
            continue#跳过
        有序.append(键)#追加
        已纳入.add(键)
    for 标识 in 会话标识列表:#再收新成员
        if 标识 in 已纳入:#已有
            continue#跳过
        有序.append(标识)#追加
    return 有序#调和后顺序

def 近因标识键(按标识,标识):#近因排序键
    '(-updatedAt, id)；摘要必在表内'
    时=按标识[标识]['updatedAt'] if 标识 in 按标识 else 0#纪元毫秒
    return (-时,标识)#新的在前

def 下一会话顺序账本(会话标识列表,先前顺序,先前更新时间,列表,排序方式,按近因排序):#调和并套提升政策
    '调和一份可编辑顺序账本并套用活动提升政策'
    顺序=调和会话顺序(会话标识列表,先前顺序)#先调和
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    def 标识近因(标识):#近因键
        '闭包按标识'
        return 近因标识键(按标识,标识)#键
    if 按近因排序:#进入最近更新时全量时间排序
        顺序=sorted(顺序,key=标识近因)#近因
    elif 排序方式=='updated':#活动提升
        提升=[]#新活动
        for 标识 in 会话标识列表:#逐会话
            if 标识 not in 按标识:#缺席
                continue#跳过
            会话=按标识[标识]#摘要
            先前=先前更新时间[标识] if 先前更新时间 is not None and 标识 in 先前更新时间 else None#先前时间戳
            if 先前 is None or 会话['updatedAt']>先前:#新或变新
                提升.append(标识)#收入提升
        提升=sorted(提升,key=标识近因)#近因排提升
        if len(提升)>0:
            提升集=set(提升)#集合
            顺序=提升+[标识 for 标识 in 顺序 if 标识 not in 提升集]#提升置顶
    更新时间={}#新时间戳表
    for 标识 in 会话标识列表:#逐会话
        if 标识 in 按标识:
            更新时间[标识]=按标识[标识]['updatedAt']
    先前时间=先前更新时间 if 先前更新时间 is not None else {}#先前
    顺序变=先前顺序 is None or len(顺序)!=len(先前顺序) or any(顺序[下标]!=先前顺序[下标] for 下标 in range(len(顺序)))#顺序变
    时间变=len(更新时间)!=len(先前时间) or any(更新时间[标识]!=(先前时间[标识] if 标识 in 先前时间 else None) for 标识 in 更新时间)#时间变
    return {'order':顺序,'updatedAt':更新时间,'changed':顺序变 or 时间变}#账本结果

class 工作区浏览区:#侧栏浏览区
    '宽态完整浏览器；轨道态两枚区头控件请求外壳展开'
    def __init__(自身,属性):#浏览区 props
        '记下注入动作、store、文案与外壳份额'
        自身.属性=属性#完整 props
        自身.翻译=属性['t']#文案
        自身.查询=''#搜索框
        自身.检索展开=False#检索轨展开
        自身.本地展开其余=[]#临时展开其余的组
        自身.添加开=False#添加流程弹出
        自身.正文结果={'items':[],'hasMore':False}#宿主正文检索
        自身.检索警告=None#内容检索失败警告
        自身.检索中=False#防抖请求中
        自身.重命名目标=None#工作区重命名
        自身.重命名草稿=''#重命名草稿
        自身.重命名中=False#重命名进行中
        自身.重命名错误=None#重命名错误
        自身.会话重命名目标=None#会话重命名
        自身.会话重命名草稿=''#会话重命名草稿
        自身.会话重命名中=False#会话重命名进行中
        自身.会话重命名错误=None#会话重命名错误
        自身.删除目标=None#删除确认
        自身.删除中=False#删除进行中
        自身.删除已提交标识=None#等待投影去掉的 id
        自身.删除错误=None#删除错误
        自身.查看选项开=False#分组/排序菜单
        自身.先前排序方式=None#进入 updated 时全量近因排序判定
        if 't' in 自身.属性:#槽位会给文案
            自身.渲染()#槽位只调用构造，这里就要画

    def 清洗查询(自身):#当前清洗后查询
        '返回线路安全查询'
        return 消毒检索查询(自身.查询)

    def 读快照(自身):#浏览 store 快照
        '读 useStore 或 store 快照'
        属性=自身.属性#props
        读=属性['useStore'] if 'useStore' in 属性 else None#钩
        if 读 is not None:
            def 原样(状态):#选择器身份
                '整表'
                return 状态#快照
            return 读(原样)#快照
        存储=属性['store'] if 'store' in 属性 else None#句柄
        if 存储 is None:#无
            return {'groupBy':'workspace','orderBy':'updated','groupExpansion':{},'sessionOrderByAccount':{}}#默认
        return 存储.getSnapshot()#读

    def 读动作(自身):#store 动作
        '优先 props.actions，其次 store.actions'
        属性=自身.属性#props
        if 'actions' in 属性 and 属性['actions'] is not None:#直接注入
            return 属性['actions']#返回
        存储=属性['store'] if 'store' in 属性 else None#句柄
        if 存储 is None:#无
            return None#无
        return 存储.actions#存储对象的动作面

    def 同步顺序账本(自身,列表,工作区列表,归档):
        '按 orderBy 调和各账本顺序并写回 store'
        动作=自身.读动作()#动作
        if 动作 is None or 'syncSessionOrders' not in 动作:#无写口
            return
        相位=列表['phase'] if 'phase' in 列表 else None#列表相位
        if 相位 is not None and 相位!='ready':#未就绪
            return
        快照=自身.读快照()#当前
        排序=快照['orderBy'] if 'orderBy' in 快照 and 快照['orderBy'] is not None else 'updated'#排序
        if 排序!='manual':#近因模式不写手动账本
            return
        顺序表=快照['sessionOrderByAccount'] if 'sessionOrderByAccount' in 快照 and 快照['sessionOrderByAccount'] is not None else {}#顺序
        按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要
        当前=列表['current'] if 'current' in 列表 else None#当前
        当前空白=当前 if 当前 is not None and 当前 in 按标识 and 按标识[当前]['blank'] is True else None#选中空白
        已记账=set()#工作区已占会话
        for 区 in 工作区列表:#逐区
            账本=区['sessionIds'] if 'sessionIds' in 区 and 区['sessionIds'] is not None else []#成员
            for 标识 in 账本:#成员
                已记账.add(标识)
        标识列表=列表['ids'] if 'ids' in 列表 and 列表['ids'] is not None else []#列表 id
        未分组=[标识 for 标识 in 标识列表 if 标识 in 按标识 and 标识 not in 已记账]#松散
        活动序={}#当前活动顺序
        for 区 in 工作区列表:#工作区账本
            键=区['workspaceId']#工作区 id
            if 键 is None:#缺 id
                continue#跳过
            成员=区['sessionIds'] if 'sessionIds' in 区 and 区['sessionIds'] is not None else []#成员
            已存=顺序表[键] if 键 in 顺序表 else None#已存
            基底=调和手动顺序([标识 for 标识 in 成员 if 标识 in 按标识],已存,按标识)#调和
            空白=当前空白 if 当前空白 is not None and 当前空白 in 成员 else None#本区空白
            活动序[键]=钉住当前空白(基底,空白)#钉住
        未分组已存=顺序表[未分组键] if 未分组键 in 顺序表 else None#未分组已存
        未分组基底=调和手动顺序(未分组,未分组已存,按标识)#调和
        活动序[未分组键]=钉住当前空白(未分组基底,当前空白 if 当前空白 is not None and 当前空白 in 未分组 else None)#钉住
        扁平成员=可见会话标识(列表,归档)#扁平可见
        扁平已存=顺序表[扁平会话顺序键] if 扁平会话顺序键 in 顺序表 else None#扁平已存
        扁平基底=调和手动顺序(扁平成员,扁平已存,按标识)#调和
        活动序[扁平会话顺序键]=钉住当前空白(扁平基底,当前空白 if 当前空白 is not None and 当前空白 in 扁平成员 else None)#钉住
        变更={}#与已存不同的账本
        for 键,标识列 in 活动序.items():#逐账本
            已存=顺序表[键] if 键 in 顺序表 else None#已存
            if 已存 is None or len(已存)!=len(标识列) or any(标识列[下标]!=已存[下标] for 下标 in range(len(标识列))):
                变更[键]=list(标识列)
        if len(变更)>0:
            动作['syncSessionOrders'](快照,变更)#写回

    def 渲染查看选项(自身,分组方式,排序方式,画菜单=True,只菜单=False):
        '画出查看选项。区头里只放按钮，菜单画在区头下面。'
        登记样式()
        def 切换():
            '打开或关闭查看选项'
            自身.处理动作('view-toggle')
        def 关闭():
            '关闭查看选项'
            自身.处理动作('view-close')
        if 只菜单 is not True:
            查看钮=界面.button(on_click=切换).props('flat dense round').classes('浏览钮')
            查看钮.tooltip(自身.翻译('viewOptions.label'))
            with 查看钮:
                界面.icon('tune', size='18px')
        if 画菜单 is not True or not 自身.查看选项开:
            return
        界面.label(自身.翻译('groupBy.label'))
        for 标识,键 in (('workspace','groupBy.workspace'),('flat','groupBy.flat')):
            def 点分组(值=标识):
                '选定分组'
                自身.处理动作('view-option',值)
            钮=界面.button(自身.翻译(键), on_click=点分组)
            if 标识==分组方式:
                钮.props('color=primary')
        界面.separator()
        界面.label(自身.翻译('orderBy.label'))
        for 标识,键 in (('manual','orderBy.manual'),('updated','orderBy.updated')):
            def 点排序(值=标识):
                '选定排序'
                自身.处理动作('view-option',值)
            钮=界面.button(自身.翻译(键), on_click=点排序)
            if 标识==排序方式:
                钮.props('color=primary')
        界面.button(自身.翻译('cancel'), on_click=关闭)

    def 渲染对话框(自身):#重命名/删除
        '画出重命名与删除对话框'
        登记样式()
        if 自身.重命名目标 is not None:
            当前标题=自身.重命名目标['currentTitle']
            重命名阻=自身.重命名中 or 自身.重命名草稿.strip()=='' or 自身.重命名草稿.strip()==当前标题
            def 改工作区名(事件):
                '写入工作区草稿'
                自身.处理动作('rename-draft',事件.value)
            def 关工作区():
                '关闭工作区重命名'
                自身.处理动作('rename-close')
            def 确认工作区():
                '确认工作区重命名'
                自身.处理动作('rename-confirm')
            with 界面.dialog() as 工作区框:
                with 界面.card():
                    界面.label(自身.翻译('rename.workspace.title'))
                    框=界面.input(value=自身.重命名草稿, placeholder=自身.翻译('field.workspaceName'), on_change=改工作区名)
                    if 自身.重命名中:
                        框.disable()
                    if isinstance(自身.重命名错误,str) and 自身.重命名错误!='':
                        界面.label(自身.重命名错误)
                    取消=界面.button(自身.翻译('cancel'), on_click=关工作区)
                    确定=界面.button(自身.翻译('rename'), on_click=确认工作区)
                    if 自身.重命名中:
                        取消.disable()
                    if 重命名阻:
                        确定.disable()
            工作区框.open()
        if 自身.会话重命名目标 is not None:
            会话阻=自身.会话重命名中 or 自身.会话重命名草稿.strip()==''
            def 改会话名(事件):
                '写入会话草稿'
                自身.处理动作('session-rename-draft',事件.value)
            def 关会话():
                '关闭会话重命名'
                自身.处理动作('session-rename-close')
            def 确认会话():
                '确认会话重命名'
                自身.处理动作('session-rename-confirm')
            with 界面.dialog() as 会话框:
                with 界面.card():
                    界面.label(自身.翻译('rename.session.title'))
                    框=界面.input(value=自身.会话重命名草稿, placeholder=自身.翻译('field.sessionName'), on_change=改会话名)
                    if 自身.会话重命名中:
                        框.disable()
                    if isinstance(自身.会话重命名错误,str) and 自身.会话重命名错误!='':
                        界面.label(自身.会话重命名错误)
                    取消=界面.button(自身.翻译('cancel'), on_click=关会话)
                    确定=界面.button(自身.翻译('rename'), on_click=确认会话)
                    if 自身.会话重命名中:
                        取消.disable()
                    if 会话阻:
                        确定.disable()
            会话框.open()
        if 自身.删除目标 is not None:
            删除名=自身.删除目标['title']
            def 关删除():
                '关闭删除'
                自身.处理动作('delete-close')
            def 确认删除():
                '确认删除'
                自身.处理动作('delete-confirm')
            with 界面.dialog() as 删除框:
                with 界面.card():
                    界面.label(自身.翻译('delete.workspace'))
                    界面.label(自身.翻译('delete.desc',{'name':删除名}))
                    if 自身.删除中:
                        界面.label(自身.翻译('delete.pending'))
                    if isinstance(自身.删除错误,str) and 自身.删除错误!='':
                        界面.label(自身.删除错误)
                    取消=界面.button(自身.翻译('cancel'), on_click=关删除)
                    确定=界面.button(自身.翻译('delete.workspace'), on_click=确认删除)
                    if 自身.删除中:
                        取消.disable()
                        确定.disable()
            删除框.open()

    def 渲目录流(自身,主人):#侧栏目录流孔
        'sidebar.workspaces.directoryFlow'
        渲=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#槽
        if 渲 is None:#无
            return None#无
        return 渲('sidebar.workspaces.directoryFlow',主人)#孔

    def 挑中添加(自身,标识):#挑中后开会话
        '关弹出并开会话'
        自身.添加开=False#关
        自身.属性['startSession'](标识)

    def 关添加(自身):#关闭添加流
        '关弹出'
        自身.添加开=False#关

    def 造打开会话(自身,标识):#打开该会话
        '闭包'
        def 打开():#点击
            'open'
            自身.属性['open'](标识)#打开
        return 打开#回调

    def 造会话动作(自身,项):#行菜单
        '重命名/归档/分叉'
        标识=项['id']#id
        标题=项['title']#标题
        def 重命名():#重命名
            '开会话重命名'
            自身.开会话重命名(标识,标题)
        def 归档():#归档
            '归档会话'
            自身.归档会话(标识)#归档
        return {'rename':重命名,'archive':归档,'fork':自身.属性['forkSession'] if 'forkSession' in 自身.属性 else None}#动作

    def 渲染(自身):#结构树
        '返回浏览区结构树'
        属性=自身.属性#props
        宽=bool(属性['wide']) if 'wide' in 属性 else True#宽态
        用会话=属性['useSessions'] if 'useSessions' in 属性 else None#会话钩
        用工作区=属性['useWorkspaces'] if 'useWorkspaces' in 属性 else None#工作区钩
        def 原样(状态):#选择器身份
            '整表'
            return 状态#快照
        列表=用会话(原样) if 用会话 is not None else {'ids':[],'byId':{},'current':None}#会话列表
        工作区快照=用工作区(原样) if 用工作区 is not None else {'items':[],'archivedSessionIds':[]}#工作区
        工作区列表=工作区快照['items'] if 'items' in 工作区快照 and 工作区快照['items'] is not None else []#列表
        归档=工作区快照['archivedSessionIds'] if 'archivedSessionIds' in 工作区快照 and 工作区快照['archivedSessionIds'] is not None else []#归档 id
        快照=自身.读快照()#查看态
        自身.同步顺序账本(列表,工作区列表,归档)#调和账本
        if 自身.删除已提交标识 is not None and not any(区['workspaceId']==自身.删除已提交标识 for 区 in 工作区列表):#删除投影已落地
            自身.删除中=False
            自身.删除已提交标识=None
            自身.删除目标=None#关
        用目录流=属性['useDirectoryFlow'] if 'useDirectoryFlow' in 属性 else None#占用钩
        def 选占用(占用):#占用态
            '原样'
            return 占用#占用
        目录流可用=用目录流(选占用) if 用目录流 is not None else False#添加入口
        if not 宽:#轨态
            登记样式()
            def 轨搜索():
                '展开侧栏并打开搜索'
                自身.处理动作('rail-search')
            def 轨添加():
                '展开侧栏并添加工作区'
                自身.处理动作('rail-add')
            with 界面.column().classes('workspace-rail'):
                搜索钮=界面.button(on_click=轨搜索).props('flat dense round')
                搜索钮.tooltip(自身.翻译('search.sessions.aria'))
                with 搜索钮:
                    界面.icon('search', size='18px')
                if 目录流可用:
                    界面.button(自身.翻译('workspace.add'), on_click=轨添加)
                工作区挑选流({#添加流
                    't':自身.翻译,'open':自身.添加开,'useWorkspaces':用工作区,'createWorkspace':属性['createWorkspace'] if 'createWorkspace' in 属性 else None,#基础
                    'useDirectoryFlow':用目录流,#占用
                    'renderDirectoryFlow':自身.渲目录流,#孔
                    'onPick':自身.挑中添加,#挑中
                    'onClose':自身.关添加,'addOnly':True,'side':'right',#关闭
                }).渲染()
            return
        展开表=快照['groupExpansion'] if 'groupExpansion' in 快照 and 快照['groupExpansion'] is not None else {}#展开
        展开键=[键 for 键,开 in 展开表.items() if 开]#已展开
        账本序=快照['sessionOrderByAccount'] if 'sessionOrderByAccount' in 快照 else None#账本序
        未分组序=账本序[未分组键] if 账本序 is not None and 未分组键 in 账本序 else None#未分组
        视图={'expandedGroups':展开键,'ungroupedOrder':未分组序}#树视图
        查询=自身.清洗查询().strip()#非空白查询
        现在=当前毫秒()#纪元毫秒
        分组方式=快照['groupBy'] if 'groupBy' in 快照 and 快照['groupBy'] is not None else 'workspace'#分组
        排序方式=快照['orderBy'] if 'orderBy' in 快照 and 快照['orderBy'] is not None else 'updated'#排序
        检索上限=属性['searchResultLimit'] if 'searchResultLimit' in 属性 and 属性['searchResultLimit'] is not None else 20#上限
        if 查询!='':#检索模式
            结果=派生检索结果(列表,工作区列表,查询,归档,{},自身.正文结果,检索上限)#合并检索
            项列表=结果['items'] if 'items' in 结果 and 结果['items'] is not None else []#项
            行列表=[检索结果行(项,自身.造打开会话(项['id']),自身.翻译) for 项 in 项列表]#检索行
            树子=行列表 if len(行列表)>0 else [自身.翻译('search.noMatches')]#空态
            if 自身.检索中:#进行中
                树子.insert(0,自身.翻译('search.pending'))#挂起
            if 自身.检索警告:#内容检索失败
                树子.insert(0,自身.翻译('search.unavailable'))#警告
            if 结果['hasMore']:#截断提示
                树子.append(自身.翻译('search.hasMore',{'n':检索上限}))#提示
        elif 分组方式=='flat':#扁平
            扁成员=可见会话标识(列表,归档)#扁平可见
            按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要
            扁账本=账本序[扁平会话顺序键] if 账本序 is not None and 扁平会话顺序键 in 账本序 else None#扁平序
            扁基底=按近因排序(扁成员,按标识) if 排序方式=='updated' else 调和手动顺序(扁成员,扁账本,按标识)#基底
            当前=列表['current'] if 'current' in 列表 else None#当前
            当前空白=当前 if 当前 is not None and 当前 in 按标识 and 按标识[当前]['blank'] is True and 当前 in 扁成员 else None#选中空白
            扁序=钉住当前空白(扁基底,当前空白)#钉住
            扁=派生扁平(列表,扁序,{})#扁平行
            树子=[会话行(项,自身.造打开会话(项['id']),自身.造会话动作(项),自身.翻译,现在) for 项 in 扁]#行
            if len(树子)==0:#空
                树子=[自身.翻译('empty.none')]#空
        else:#按工作区分组
            有序工作区=[]#带本地序的工作区
            按标识组=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要
            当前组=列表['current'] if 'current' in 列表 else None#当前
            当前空白组=当前组 if 当前组 is not None and 当前组 in 按标识组 and 按标识组[当前组]['blank'] is True else None#选中空白
            for 区 in 工作区列表:#逐区
                成员=区['sessionIds'] if 'sessionIds' in 区 and 区['sessionIds'] is not None else []#成员
                区序=账本序[区['workspaceId']] if 账本序 is not None and 区['workspaceId'] in 账本序 else None#序
                基底=按近因排序(成员,按标识组) if 排序方式=='updated' else 调和手动顺序(成员,区序,按标识组)#基底
                空白=当前空白组 if 当前空白组 is not None and 当前空白组 in 成员 else None#本区空白
                拷=dict(区)#拷贝
                拷['sessionIds']=钉住当前空白(基底,空白)#写入
                有序工作区.append(拷)#追加
            组列表=派生分组(列表,有序工作区,归档,{},视图)#分组
            树子=[]#树节点
            if len(组列表)==0:#空
                树子.append(自身.翻译('empty.none'))#空
            for 组 in 组列表:#逐组
                键=组['key']#组键
                def 造切换(组键):#切换展开
                    '闭包'
                    def 切换():#点击
                        '翻转'
                        自身.切换分组(组键)#翻转
                    return 切换#回调
                def 造创建(组键,工作区标识):#新建会话
                    '闭包'
                    def 创建():#点击
                        '展开并开会话'
                        自身.设分组展开(组键,True)#展开
                        自身.属性['startSession'](工作区标识)
                    return 创建#回调
                组动作=None#重命名/删除
                if 组['workspaceId'] is not None:#真实工作区
                    区标识=组['workspaceId']#id
                    区标签=组['label']#标签
                    def 造重命名(某标识,某标题):#重命名
                        '闭包'
                        def 重命名():#点击
                            '开重命名'
                            自身.开重命名(某标识,某标题)
                        return 重命名#回调
                    def 造删除(某标识,某标题):#删除
                        '闭包'
                        def 删除():#点击
                            '开删除'
                            自身.开删除(某标识,某标题)
                        return 删除#回调
                    组动作={'rename':造重命名(区标识,区标签),'delete':造删除(区标识,区标签)}#动作
                树子.append(项目行(组,造切换(键),造创建(键,组['workspaceId']),组动作,自身.翻译))#头行
                if 组['expanded']:#展开
                    会话列表=组['sessions'] if 'sessions' in 组 and 组['sessions'] is not None else []#会话
                    溢出=键 in 自身.本地展开其余#本地溢出
                    可见=会话列表 if 溢出 or len(会话列表)<=折叠会话上限 else 会话列表[:折叠会话上限]#截断
                    for 项 in 可见:#会话行
                        树子.append(会话行(项,自身.造打开会话(项['id']),自身.造会话动作(项),自身.翻译,现在))#行
                    if len(会话列表)>折叠会话上限:#展开其余
                        溢出文=自身.翻译('sessions.collapse') if 溢出 else 自身.翻译('sessions.expand',{'n':len(会话列表)-折叠会话上限})
                        def 点溢出(组键=键):
                            '展开或收起其余会话'
                            自身.处理动作(('overflow',组键))
                        树子.append({'kind':'overflow','label':溢出文,'onClick':点溢出})#控件
        挑选=工作区挑选流({#添加流程
            't':自身.翻译,#文案
            'open':自身.添加开,#开关
            'useWorkspaces':用工作区,#工作区钩
            'createWorkspace':属性['createWorkspace'] if 'createWorkspace' in 属性 else None,#创建
            'useDirectoryFlow':用目录流,#占用
            'renderDirectoryFlow':自身.渲目录流,#孔
            'onPick':自身.挑中添加,#挑中后开会话
            'onClose':自身.关添加,#关闭
            'addOnly':True,#仅添加
            'side':'right',#侧栏方向
        })#流结束
        区头标题=自身.翻译('section.sessions') if 分组方式=='flat' else 自身.翻译('section.workspaces')#区头文案
        登记样式()
        def 开搜索():
            '展开搜索' 
            自身.处理动作('search-open')
        def 改查询(事件):
            '写入查询'
            自身.处理动作('search',事件.value)
        def 按键(事件):
            'Escape 收起搜索'
            参数=事件.args if hasattr(事件,'args') else None
            键名=''
            if isinstance(参数,dict) and 'key' in 参数 and isinstance(参数['key'],str):
                键名=参数['key']
            if 键名!='':
                自身.处理动作('search-key',键名)
        def 清搜索():
            '清空查询'
            自身.处理动作('search-clear')
        def 添加():
            '添加工作区'
            自身.处理动作('add')
        with 界面.column().classes('workspace-browser'):
            with 界面.row().classes('区头'):
                if not 自身.检索展开:
                    界面.label(区头标题).classes('区头题')
                搜索钮=界面.button(on_click=开搜索).props('flat dense round').classes('浏览钮')
                搜索钮.tooltip(自身.翻译('search.sessions.aria'))
                with 搜索钮:
                    界面.icon('search', size='18px')
                自身.渲染查看选项(分组方式,排序方式,画菜单=False)
            if 自身.检索展开:
                框=界面.input(value=自身.查询, placeholder=自身.翻译('search.placeholder'), on_change=改查询)
                框.on('keydown',按键)
                界面.button(自身.翻译('search.clear'), on_click=清搜索)
            自身.渲染查看选项(分组方式,排序方式,只菜单=True)
            if 目录流可用:
                界面.button(自身.翻译('workspace.add'), on_click=添加)
            挑选.渲染()
            with 界面.column().classes('session-list'):
                for 项 in 树子:
                    if hasattr(项,'渲染'):
                        项.渲染()
                    elif isinstance(项,str) and 项!='':
                        界面.label(项)
                    elif isinstance(项,dict) and 'kind' in 项 and 项['kind']=='overflow':
                        界面.button(项['label'], on_click=项['onClick'])
            自身.渲染对话框()

    def 设分组展开(自身,键,展开):#写 groupExpansion
        '写 store 的分组展开'
        动作=自身.读动作()#动作
        if 动作 is None or 'setGroupExpanded' not in 动作:#无
            return
        动作['setGroupExpanded'](自身.读快照(),键,展开)#写入

    def 切换分组(自身,键):#翻转分组展开
        '写回 store 的 groupExpansion'
        快照=自身.读快照()#当前
        展开表=快照['groupExpansion'] if 'groupExpansion' in 快照 and 快照['groupExpansion'] is not None else {}#展开
        当前=bool(展开表[键]) if 键 in 展开表 else False#当前展开
        if 当前:#收起时清本地溢出
            自身.本地展开其余=[项 for 项 in 自身.本地展开其余 if 项!=键]#去掉
        动作=自身.读动作()#动作
        if 动作 is None or 'setGroupExpanded' not in 动作:#无
            return
        动作['setGroupExpanded'](快照,键,not 当前)#翻转

    def 开重命名(自身,工作区标识,当前标题):#打开工作区重命名
        '记下重命名目标'
        if 工作区标识 is None:#未分组
            return
        自身.重命名目标={'workspaceId':工作区标识,'currentTitle':当前标题}#目标
        自身.重命名草稿=当前标题#草稿
        自身.重命名错误=None#清掉上次失败

    def 开删除(自身,工作区标识,标题):#打开删除确认
        '记下删除目标'
        if 工作区标识 is None:#未分组
            return
        自身.删除目标={'workspaceId':工作区标识,'title':标题}#目标
        自身.删除错误=None#清掉上次失败

    def 开会话重命名(自身,会话标识,当前标题):#打开会话重命名
        '记下会话重命名目标'
        自身.会话重命名目标={'sessionId':会话标识,'currentTitle':当前标题}#目标
        自身.会话重命名草稿=当前标题#草稿
        自身.会话重命名错误=None#清掉上次失败

    def 归档会话(自身,会话标识):#无对话框归档
        '直接提交归档。注入面已等待'
        归档=自身.属性['archiveSession'] if 'archiveSession' in 自身.属性 else None#注入
        if 归档 is None:#无
            return
        归档(会话标识)#调用；已等待

    def 触发正文检索(自身):#防抖宿主检索
        '非空白查询经防抖调用 searchSessions。注入面已等待'
        查询=自身.清洗查询().strip()#查询
        搜索=自身.属性['searchSessions'] if 'searchSessions' in 自身.属性 else None#注入检索
        if 查询=='' or 搜索 is None:#无需
            自身.正文结果={'items':[],'hasMore':False}
            自身.检索警告=None#不再提示失败
            自身.检索中=False
            return
        自身.检索中=True#标记
        try:#请求
            结果=搜索(查询,None)#检索；已等待
            自身.正文结果=结果 if 结果 is not None else {'items':[],'hasMore':False}#写入
            自身.检索警告=None#成功
        except Exception:#内容检索失败；检索 RPC 异常契约未定，故不能换成更窄的 except
            自身.检索警告='unavailable'#警告
            自身.正文结果={'items':[],'hasMore':False}#仅本地匹配
        自身.检索中=False#结束

    def 处理动作(自身,动作,载荷=None):#分发交互
        '搜索、添加、查看选项、对话框与溢出'
        属性=自身.属性#props
        动作集=自身.读动作()#store 动作
        if 动作=='rail-search':#轨搜索
            展开=属性['expandSidebar'] if 'expandSidebar' in 属性 else None#请求扩宽
            if 展开 is not None:
                展开()#扩宽
            自身.检索展开=True#开检索
            return#已处理
        if 动作=='rail-add':#轨添加
            展开=属性['expandSidebar'] if 'expandSidebar' in 属性 else None#请求扩宽
            if 展开 is not None:
                展开()#扩宽
            自身.添加开=True#开流
            return#已处理
        if 动作=='search-open':#展开搜索
            自身.添加开=False#关添加
            自身.检索展开=True
            return#已处理
        if 动作=='search-clear':
            自身.查询=''
            自身.检索展开=False#收
            自身.触发正文检索()
            return#已处理
        if 动作=='search':#改查询
            自身.查询=消毒检索查询(载荷 if 载荷 is not None else '')#写入
            自身.触发正文检索()#防抖检索
            return#已处理
        if 动作=='search-key' and 载荷=='Escape':#Escape
            自身.查询=''
            自身.检索展开=False#收
            自身.触发正文检索()
            return#已处理
        if 动作=='add':#添加工作区
            自身.添加开=not 自身.添加开#翻转
            return#已处理
        if 动作=='view-close':#关查看选项
            自身.查看选项开=False#关
            return#已处理
        if 动作=='view-toggle':#翻转查看选项
            自身.查看选项开=not 自身.查看选项开#翻转
            return#已处理
        if 动作=='view-option':#分组/排序
            if 载荷 in ('workspace','flat') and 动作集 is not None and 'setGroupBy' in 动作集:#分组
                动作集['setGroupBy'](自身.读快照(),载荷)#写
            elif 载荷 in ('manual','updated') and 动作集 is not None and 'setOrderBy' in 动作集:#排序
                快照=自身.读快照()#当前
                用会话=属性['useSessions'] if 'useSessions' in 属性 else None#会话钩
                用工作区=属性['useWorkspaces'] if 'useWorkspaces' in 属性 else None#工作区钩
                def 原样(状态):#选择器身份
                    '整表'
                    return 状态#快照
                列表=用会话(原样) if 用会话 is not None else {'ids':[],'byId':{},'current':None}#会话
                工作区快照=用工作区(原样) if 用工作区 is not None else {'items':[],'archivedSessionIds':[]}#工作区
                工作区列表=工作区快照['items'] if 'items' in 工作区快照 and 工作区快照['items'] is not None else []#列表
                归档=工作区快照['archivedSessionIds'] if 'archivedSessionIds' in 工作区快照 and 工作区快照['archivedSessionIds'] is not None else []#归档
                按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要
                当前=列表['current'] if 'current' in 列表 else None#当前
                当前空白=当前 if 当前 is not None and 当前 in 按标识 and 按标识[当前]['blank'] is True else None#选中空白
                顺序表=快照['sessionOrderByAccount'] if 'sessionOrderByAccount' in 快照 and 快照['sessionOrderByAccount'] is not None else {}#已存
                已记账=set()#已占
                活动序={}#展示序
                for 区 in 工作区列表:#逐区
                    成员=区['sessionIds'] if 'sessionIds' in 区 and 区['sessionIds'] is not None else []#成员
                    for 标识 in 成员:#成员
                        已记账.add(标识)
                    键=区['workspaceId']#键
                    已存=顺序表[键] if 键 in 顺序表 else None#已存
                    基底=按近因排序(成员,按标识)#近因展示
                    活动序[键]=钉住当前空白(基底,当前空白 if 当前空白 is not None and 当前空白 in 成员 else None)#钉住
                标识列表=列表['ids'] if 'ids' in 列表 and 列表['ids'] is not None else []#列表 id
                未分组=[标识 for 标识 in 标识列表 if 标识 in 按标识 and 标识 not in 已记账]#松散
                活动序[未分组键]=钉住当前空白(按近因排序(未分组,按标识),当前空白 if 当前空白 is not None and 当前空白 in 未分组 else None)#未分组
                扁平成员=可见会话标识(列表,归档)#扁平
                活动序[扁平会话顺序键]=钉住当前空白(按近因排序(扁平成员,按标识),当前空白 if 当前空白 is not None and 当前空白 in 扁平成员 else None)#扁平
                动作集['setOrderBy'](快照,载荷,活动序)#写
            自身.查看选项开=False#关
            return#已处理
        if isinstance(动作,tuple) and 动作[0]=='overflow':#展开其余
            自身.本地展开其余=切换成员(自身.本地展开其余,动作[1])#切换
            return#已处理
        if 动作=='rename-draft':#重命名草稿
            自身.重命名草稿=载荷 if 载荷 is not None else ''#写
            自身.重命名错误=None
            return#已处理
        if 动作=='rename-close':#关重命名
            if 自身.重命名中:#进行中
                return#拒
            自身.重命名目标=None
            自身.重命名错误=None
            return#已处理
        if 动作=='rename-confirm':#确认重命名
            if 自身.重命名目标 is None or 自身.重命名中:#无效
                return
            标题=自身.重命名草稿.strip()#修剪
            if 标题=='' or 标题==自身.重命名目标['currentTitle']:#无变
                return
            改名=属性['renameWorkspace'] if 'renameWorkspace' in 属性 else None#注入
            if 改名 is None:#无
                return
            自身.重命名中=True#忙
            try:#提交
                改名(自身.重命名目标['workspaceId'],标题)#调用；已等待
                自身.重命名目标=None#关
                自身.重命名错误=None
            except Exception as 原因:#失败；重命名 RPC 异常契约未定，故不能换成更窄的 except
                自身.重命名错误=页面失败文案(原因)
            自身.重命名中=False#闲
            return#已处理
        if 动作=='session-rename-draft':#会话草稿
            自身.会话重命名草稿=载荷 if 载荷 is not None else ''#写
            自身.会话重命名错误=None
            return#已处理
        if 动作=='session-rename-close':#关会话重命名
            if 自身.会话重命名中:#忙
                return#拒
            自身.会话重命名目标=None
            自身.会话重命名错误=None
            return#已处理
        if 动作=='session-rename-confirm':#确认会话重命名
            if 自身.会话重命名目标 is None or 自身.会话重命名中:#无效
                return
            标题=自身.会话重命名草稿.strip()#修剪
            if 标题=='':#空
                return
            改名=属性['renameSession'] if 'renameSession' in 属性 else None#注入
            if 改名 is None:#无
                return
            自身.会话重命名中=True#忙
            try:#提交
                改名(自身.会话重命名目标['sessionId'],标题)#调用；已等待
                自身.会话重命名目标=None#关
                自身.会话重命名错误=None
            except Exception as 原因:#失败；会话改名 RPC 异常契约未定，故不能换成更窄的 except
                自身.会话重命名错误=页面失败文案(原因)
            自身.会话重命名中=False#闲
            return#已处理
        if 动作=='delete-close':#关删除
            if 自身.删除中:#忙
                return#拒
            自身.删除目标=None
            自身.删除错误=None
            return#已处理
        if 动作=='delete-confirm':#确认删除
            if 自身.删除目标 is None or 自身.删除中:#无效
                return
            删除=属性['deleteWorkspace'] if 'deleteWorkspace' in 属性 else None#注入
            if 删除 is None:#无
                return
            自身.删除中=True#忙
            自身.删除错误=None
            try:#提交
                删除(自身.删除目标['workspaceId'])#调用；已等待
                自身.删除已提交标识=自身.删除目标['workspaceId']#等投影
            except Exception as 原因:#失败；删除 RPC 异常契约未定，故不能换成更窄的 except
                自身.删除中=False#闲
                自身.删除错误=页面失败文案(原因)
            return#已处理
