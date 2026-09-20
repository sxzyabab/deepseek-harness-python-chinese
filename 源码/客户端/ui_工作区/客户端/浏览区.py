import time#相对时间 now
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

样式表='''#对齐 WorkspaceBrowser.module.css 核心结构类；完整样式见 浏览区.module.css
.root{display:flex;flex-direction:column;min-height:0;height:100%}
.sectionHeader{display:flex;align-items:center;gap:4px;height:36px;flex:none}
.sectionLabel{font-size:14px;font-weight:510;flex:none}
.searchInput{flex:1;min-width:0;height:32px;padding:0 8px;border:1px solid var(--dsw-alias-border-l2);border-radius:8px;background:var(--dsw-alias-bg-module-platform)}
.listArea{flex:1;min-height:0;overflow:auto}
.empty{padding:12px;color:var(--dsw-alias-label-tertiary);font-size:13px}
.sessionOverflowButton{display:block;width:100%;padding:4px 8px;border:none;background:transparent;color:var(--dsw-alias-state-business-primary);cursor:pointer;text-align:left}
.renameError{color:var(--dsw-alias-state-error-primary);font-size:12px;line-height:18px}
'''#样式表结束

def 消毒检索查询(值):#守住 session.search 线路契约
    """去掉 NUL，截到 500 个 UTF-16 码元且不拆代理对。"""
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
    """展开数组的成员开关。"""
    if 键 in 列表:#已有则去掉
        return [项 for 项 in 列表 if 项!=键]#去掉
    return list(列表)+[键]#追加

def 调和会话顺序(会话标识列表,已存):#调和已存顺序与当前账本
    """接受已存顺序，未知键跳过，新成员追加到末尾。"""
    if 已存 is None:#无已存
        return list(会话标识列表)#原样拷贝
    有序=[]#结果
    已纳入=set()#已纳入
    集=set(会话标识列表)#id 集
    for 键 in 已存:#先走已存
        if 键 not in 集 or 键 in 已纳入:#未知或重复
            continue#跳过
        有序.append(键)#追加
        已纳入.add(键)#记下
    for 标识 in 会话标识列表:#再收新成员
        if 标识 in 已纳入:#已有
            continue#跳过
        有序.append(标识)#追加
    return 有序#调和后顺序

def 近因标识键(按标识,标识):#近因排序键
    """(-updatedAt, id)；摘要必在表内。"""
    时=按标识[标识]['updatedAt'] if 标识 in 按标识 else 0#纪元毫秒
    return (-时,标识)#新的在前

def 下一会话顺序账本(会话标识列表,先前顺序,先前更新时间,列表,排序方式,按近因排序):#调和并套提升政策
    """调和一份可编辑顺序账本并套用活动提升政策。"""
    顺序=调和会话顺序(会话标识列表,先前顺序)#先调和
    按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要表
    def 标识近因(标识):#近因键
        """闭包按标识。"""
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
        if len(提升)>0:#有提升
            提升集=set(提升)#集合
            顺序=提升+[标识 for 标识 in 顺序 if 标识 not in 提升集]#提升置顶
    更新时间={}#新时间戳表
    for 标识 in 会话标识列表:#逐会话
        if 标识 in 按标识:#有摘要
            更新时间[标识]=按标识[标识]['updatedAt']#记下
    先前时间=先前更新时间 if 先前更新时间 is not None else {}#先前
    顺序变=先前顺序 is None or len(顺序)!=len(先前顺序) or any(顺序[下标]!=先前顺序[下标] for 下标 in range(len(顺序)))#顺序变
    时间变=len(更新时间)!=len(先前时间) or any(更新时间[标识]!=(先前时间[标识] if 标识 in 先前时间 else None) for 标识 in 更新时间)#时间变
    return {'order':顺序,'updatedAt':更新时间,'changed':顺序变 or 时间变}#账本结果

class 工作区浏览区:#侧栏浏览区
    """宽态完整浏览器；轨道态两枚区头控件请求外壳展开。"""
    def __init__(自身,属性):#浏览区 props
        """记下注入动作、store、文案与外壳份额。"""
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

    def 清洗查询(自身):#当前清洗后查询
        """返回线路安全查询。"""
        return 消毒检索查询(自身.查询)#清洗

    def 读快照(自身):#浏览 store 快照
        """读 useStore 或 store 快照。"""
        属性=自身.属性#props
        读=属性['useStore'] if 'useStore' in 属性 else None#钩
        if 读 is not None:#有钩
            def 原样(状态):#选择器身份
                """整表。"""
                return 状态#快照
            return 读(原样)#快照
        存储=属性['store'] if 'store' in 属性 else None#句柄
        if 存储 is None:#无
            return {'groupBy':'workspace','orderBy':'updated','groupExpansion':{},'sessionOrderByAccount':{}}#默认
        return 存储.getSnapshot()#读

    def 读动作(自身):#store 动作
        """优先 props.actions，其次 store.actions。"""
        属性=自身.属性#props
        if 'actions' in 属性 and 属性['actions'] is not None:#直接注入
            return 属性['actions']#返回
        存储=属性['store'] if 'store' in 属性 else None#句柄
        if 存储 is None:#无
            return None#无
        return 存储.actions#存储对象的动作面

    def 同步顺序账本(自身,列表,工作区列表,归档):
        """按 orderBy 调和各账本顺序并写回 store。"""
        动作=自身.读动作()#动作
        if 动作 is None or 'syncSessionOrders' not in 动作:#无写口
            return#停
        相位=列表['phase'] if 'phase' in 列表 else None#列表相位
        if 相位 is not None and 相位!='ready':#未就绪
            return#停
        快照=自身.读快照()#当前
        排序=快照['orderBy'] if 'orderBy' in 快照 and 快照['orderBy'] is not None else 'updated'#排序
        if 排序!='manual':#近因模式不写手动账本
            return#停
        顺序表=快照['sessionOrderByAccount'] if 'sessionOrderByAccount' in 快照 and 快照['sessionOrderByAccount'] is not None else {}#顺序
        按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要
        当前=列表['current'] if 'current' in 列表 else None#当前
        当前空白=当前 if 当前 is not None and 当前 in 按标识 and 按标识[当前]['blank'] is True else None#选中空白
        已记账=set()#工作区已占会话
        for 区 in 工作区列表:#逐区
            账本=区['sessionIds'] if 'sessionIds' in 区 and 区['sessionIds'] is not None else []#成员
            for 标识 in 账本:#成员
                已记账.add(标识)#记下
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
            if 已存 is None or len(已存)!=len(标识列) or any(标识列[下标]!=已存[下标] for 下标 in range(len(标识列))):#有变
                变更[键]=list(标识列)#记下
        if len(变更)>0:#有变
            动作['syncSessionOrders'](快照,变更)#写回

    def 渲染查看选项(自身,分组方式,排序方式):#分组/排序菜单
        """查看选项菜单。"""
        return {#锚点 + 菜单
            'type':'fragment','children':[#子
                {'type':'button','class':'iconButton wide','aria-label':自身.翻译('viewOptions.label'),'onClick':'view-toggle'},#锚点
                {'type':'Menu','open':自身.查看选项开,'align':'end','dense':True,'portal':True,#菜单
                 'selectedIds':[分组方式,排序方式],#当前
                 'items':[#项
                     {'type':'label','id':'group-by','text':自身.翻译('groupBy.label')},#分组标签
                     {'id':'workspace','label':自身.翻译('groupBy.workspace')},#按工作区
                     {'id':'flat','label':自身.翻译('groupBy.flat')},#扁平
                     {'type':'separator','id':'order-by-separator'},#分隔
                     {'type':'label','id':'order-by','text':自身.翻译('orderBy.label')},#排序标签
                     {'id':'manual','label':自身.翻译('orderBy.manual')},#手动
                     {'id':'updated','label':自身.翻译('orderBy.updated')},#活动
                 ],#项结束
                 'onSelect':'view-option','onClose':'view-close',#回调
                },#菜单结束
            ],#子结束
        }#片段结束

    def 渲染对话框(自身):#重命名/删除
        """浏览器自有对话框，避免行卸载带走确认态。"""
        当前标题=自身.重命名目标['currentTitle'] if 自身.重命名目标 is not None else None#当前标题
        重命名阻=自身.重命名中 or 自身.重命名草稿.strip()=='' or 自身.重命名目标 is None or 自身.重命名草稿.strip()==当前标题#阻塞
        会话阻=自身.会话重命名中 or 自身.会话重命名草稿.strip()=='' or 自身.会话重命名目标 is None#会话阻塞（允许确认当前标题）
        删除名=自身.删除目标['title'] if 自身.删除目标 is not None else None#删除名
        return [#对话框列表
            {'type':'Modal','open':自身.重命名目标 is not None,'onClose':'rename-close','title':自身.翻译('rename.workspace.title'),'children':[{'type':'input','class':'renameInput','value':自身.重命名草稿,'aria-label':自身.翻译('field.workspaceName'),'onChange':'rename-draft'},{'type':'div','class':'renameError','role':'alert','children':[自身.重命名错误]} if 自身.重命名错误 else None],'footer':[{'type':'Button','variant':'outline','disabled':自身.重命名中,'onClick':'rename-close','label':自身.翻译('cancel')},{'type':'Button','variant':'primary','disabled':重命名阻,'onClick':'rename-confirm','label':自身.翻译('rename')}]},#工作区重命名
            {'type':'Modal','open':自身.会话重命名目标 is not None,'onClose':'session-rename-close','title':自身.翻译('rename.session.title'),'children':[{'type':'input','class':'renameInput','value':自身.会话重命名草稿,'aria-label':自身.翻译('field.sessionName'),'onChange':'session-rename-draft'},{'type':'div','class':'renameError','role':'alert','children':[自身.会话重命名错误]} if 自身.会话重命名错误 else None],'footer':[{'type':'Button','variant':'outline','disabled':自身.会话重命名中,'onClick':'session-rename-close','label':自身.翻译('cancel')},{'type':'Button','variant':'primary','disabled':会话阻,'onClick':'session-rename-confirm','label':自身.翻译('rename')}]},#会话重命名
            {'type':'Modal','open':自身.删除目标 is not None,'onClose':'delete-close','title':自身.翻译('delete.workspace'),'description':自身.翻译('delete.desc',{'name':删除名}) if 自身.删除目标 is not None else None,'children':[{'type':'div','class':'deleteStatus','role':'status','children':[自身.翻译('delete.pending')]} if 自身.删除中 else None,{'type':'div','class':'renameError','role':'alert','children':[自身.删除错误]} if 自身.删除错误 else None],'footer':[{'type':'Button','variant':'outline','disabled':自身.删除中,'onClick':'delete-close','label':自身.翻译('cancel')},{'type':'Button','variant':'outline','class':'deleteAction','disabled':自身.删除中,'onClick':'delete-confirm','label':自身.翻译('delete.workspace')}]},#删除
        ]#列表结束

    def 渲目录流(自身,主人):#侧栏目录流孔
        """sidebar.workspaces.directoryFlow。"""
        渲=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#槽
        if 渲 is None:#无
            return None#无
        return 渲('sidebar.workspaces.directoryFlow',主人)#孔

    def 挑中添加(自身,标识):#挑中后开会话
        """关弹出并开会话。"""
        自身.添加开=False#关
        自身.属性['startSession'](标识)#开

    def 关添加(自身):#关闭添加流
        """关弹出。"""
        自身.添加开=False#关

    def 造打开会话(自身,标识):#打开该会话
        """闭包。"""
        def 打开():#点击
            """open。"""
            自身.属性['open'](标识)#打开
        return 打开#回调

    def 造会话动作(自身,项):#行菜单
        """重命名/归档/分叉。"""
        标识=项['id']#id
        标题=项['title']#标题
        def 重命名():#重命名
            """开会话重命名。"""
            自身.开会话重命名(标识,标题)#开
        def 归档():#归档
            """归档会话。"""
            自身.归档会话(标识)#归档
        return {'rename':重命名,'archive':归档,'fork':自身.属性['forkSession'] if 'forkSession' in 自身.属性 else None}#动作

    def 渲染(自身):#结构树
        """返回浏览区结构树。"""
        属性=自身.属性#props
        宽=bool(属性['wide']) if 'wide' in 属性 else True#宽态
        用会话=属性['useSessions'] if 'useSessions' in 属性 else None#会话钩
        用工作区=属性['useWorkspaces'] if 'useWorkspaces' in 属性 else None#工作区钩
        def 原样(状态):#选择器身份
            """整表。"""
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
            """原样。"""
            return 占用#占用
        目录流可用=用目录流(选占用) if 用目录流 is not None else False#添加入口
        if not 宽:#轨态
            return {#轨
                'type':'div','class':'root rail',#根
                'children':[#子
                    {'type':'div','class':'search','children':[{'type':'button','class':'searchButton','aria-label':自身.翻译('search.sessions.aria'),'onClick':'rail-search'}]},#搜索
                    {'type':'button','class':'iconButton','aria-label':自身.翻译('workspace.add'),'onClick':'rail-add'} if 目录流可用 else None,#添加
                    工作区挑选流({#添加流
                        't':自身.翻译,'open':自身.添加开,'useWorkspaces':用工作区,'createWorkspace':属性['createWorkspace'] if 'createWorkspace' in 属性 else None,#基础
                        'useDirectoryFlow':用目录流,#占用
                        'renderDirectoryFlow':自身.渲目录流,#孔
                        'onPick':自身.挑中添加,#挑中
                        'onClose':自身.关添加,'addOnly':True,'side':'right',#关闭
                    }).渲染(),#流
                ],#子结束
            }#轨结束
        展开表=快照['groupExpansion'] if 'groupExpansion' in 快照 and 快照['groupExpansion'] is not None else {}#展开
        展开键=[键 for 键,开 in 展开表.items() if 开]#已展开
        账本序=快照['sessionOrderByAccount'] if 'sessionOrderByAccount' in 快照 else None#账本序
        未分组序=账本序[未分组键] if 账本序 is not None and 未分组键 in 账本序 else None#未分组
        视图={'expandedGroups':展开键,'ungroupedOrder':未分组序}#树视图
        查询=自身.清洗查询().strip()#非空白查询
        现在=int(time.time()*1000)#纪元毫秒
        分组方式=快照['groupBy'] if 'groupBy' in 快照 and 快照['groupBy'] is not None else 'workspace'#分组
        排序方式=快照['orderBy'] if 'orderBy' in 快照 and 快照['orderBy'] is not None else 'updated'#排序
        检索上限=属性['searchResultLimit'] if 'searchResultLimit' in 属性 and 属性['searchResultLimit'] is not None else 20#上限
        if 查询!='':#检索模式
            结果=派生检索结果(列表,工作区列表,查询,归档,{},自身.正文结果,检索上限)#合并检索
            项列表=结果['items'] if 'items' in 结果 and 结果['items'] is not None else []#项
            行列表=[检索结果行(项,自身.造打开会话(项['id']),自身.翻译).渲染() for 项 in 项列表]#检索行
            树子=行列表 if len(行列表)>0 else [{'type':'div','class':'empty','children':[自身.翻译('search.noMatches')]}]#空态
            if 自身.检索中:#进行中
                树子.insert(0,{'type':'div','class':'searchStatus','role':'status','children':[自身.翻译('search.pending')]})#挂起
            if 自身.检索警告:#内容检索失败
                树子.insert(0,{'type':'div','class':'searchWarning','role':'status','children':[自身.翻译('search.unavailable')]})#警告
            if 结果['hasMore']:#截断提示
                树子.append({'type':'div','class':'searchStatus','children':[自身.翻译('search.hasMore',{'n':检索上限})]})#提示
            列表体={'type':'div','class':'treeBody wide','children':[{'type':'div','class':'list','role':'tree','aria-label':自身.翻译('search.results.aria'),'children':树子},{'type':'span','class':'fade'}]}#检索体
        elif 分组方式=='flat':#扁平
            扁成员=可见会话标识(列表,归档)#扁平可见
            按标识=列表['byId'] if 'byId' in 列表 and 列表['byId'] is not None else {}#摘要
            扁账本=账本序[扁平会话顺序键] if 账本序 is not None and 扁平会话顺序键 in 账本序 else None#扁平序
            扁基底=按近因排序(扁成员,按标识) if 排序方式=='updated' else 调和手动顺序(扁成员,扁账本,按标识)#基底
            当前=列表['current'] if 'current' in 列表 else None#当前
            当前空白=当前 if 当前 is not None and 当前 in 按标识 and 按标识[当前]['blank'] is True and 当前 in 扁成员 else None#选中空白
            扁序=钉住当前空白(扁基底,当前空白)#钉住
            扁=派生扁平(列表,扁序,{})#扁平行
            树子=[会话行(项,自身.造打开会话(项['id']),自身.造会话动作(项),自身.翻译,现在).渲染() for 项 in 扁]#行
            if len(树子)==0:#空
                树子=[{'type':'div','class':'empty','children':[自身.翻译('empty.none')]}]#空
            列表体={'type':'div','class':'treeBody wide','children':[{'type':'div','class':'list flatList','role':'tree','aria-label':自身.翻译('section.sessions'),'children':树子},{'type':'span','class':'fade'}]}#扁平体
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
                树子.append({'type':'div','class':'empty','children':[自身.翻译('empty.none')]})#空
            for 组 in 组列表:#逐组
                键=组['key']#组键
                def 造切换(组键):#切换展开
                    """闭包。"""
                    def 切换():#点击
                        """翻转。"""
                        自身.切换分组(组键)#翻转
                    return 切换#回调
                def 造创建(组键,工作区标识):#新建会话
                    """闭包。"""
                    def 创建():#点击
                        """展开并开会话。"""
                        自身.设分组展开(组键,True)#展开
                        自身.属性['startSession'](工作区标识)#开
                    return 创建#回调
                组动作=None#重命名/删除
                if 组['workspaceId'] is not None:#真实工作区
                    区标识=组['workspaceId']#id
                    区标签=组['label']#标签
                    def 造重命名(某标识,某标题):#重命名
                        """闭包。"""
                        def 重命名():#点击
                            """开重命名。"""
                            自身.开重命名(某标识,某标题)#开
                        return 重命名#回调
                    def 造删除(某标识,某标题):#删除
                        """闭包。"""
                        def 删除():#点击
                            """开删除。"""
                            自身.开删除(某标识,某标题)#开
                        return 删除#回调
                    组动作={'rename':造重命名(区标识,区标签),'delete':造删除(区标识,区标签)}#动作
                树子.append(项目行(组,造切换(键),造创建(键,组['workspaceId']),组动作,自身.翻译).渲染())#头行
                if 组['expanded']:#展开
                    会话列表=组['sessions'] if 'sessions' in 组 and 组['sessions'] is not None else []#会话
                    溢出=键 in 自身.本地展开其余#本地溢出
                    可见=会话列表 if 溢出 or len(会话列表)<=折叠会话上限 else 会话列表[:折叠会话上限]#截断
                    for 项 in 可见:#会话行
                        树子.append(会话行(项,自身.造打开会话(项['id']),自身.造会话动作(项),自身.翻译,现在).渲染())#行
                    if len(会话列表)>折叠会话上限:#展开其余
                        树子.append({'type':'button','class':'sessionOverflowButton','aria-expanded':溢出,'onClick':('overflow',键),'children':[自身.翻译('sessions.collapse') if 溢出 else 自身.翻译('sessions.expand',{'n':len(会话列表)-折叠会话上限})]})#控件
            列表体={'type':'div','class':'treeBody wide','children':[{'type':'div','class':'list','role':'tree','aria-label':自身.翻译('section.sessions'),'children':树子},{'type':'span','class':'fade'}]}#分组体
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
        return {#根
            'type':'div','class':'root',#根
            'children':[#子
                {'type':'div','class':'sectionHeader','children':[#区头
                    {'type':'span','class':('sectionLabel sectionLabelHidden' if 自身.检索展开 else 'sectionLabel'),'children':[区头标题]},#标题
                    {'type':'div','class':('searchSlot searchSlotExpanded' if 自身.检索展开 else 'searchSlot'),'children':[#搜索槽
                        {'type':'div','class':('search searchExpanded' if 自身.检索展开 else 'search'),'onClick':'search-open','children':[#搜索
                            {'type':'button','class':'searchButton','aria-label':自身.翻译('search.sessions.aria'),'aria-expanded':自身.检索展开,'onClick':'search-open'},#钮
                            {'type':'input','class':'searchInput','value':自身.查询,'placeholder':自身.翻译('search.placeholder'),'maxLength':检索查询最大码元,'onChange':'search','onKeyDown':'search-key'},#输入
                            {'type':'button','class':'clearButton','aria-label':自身.翻译('search.clear'),'onClick':'search-clear'} if 自身.检索展开 else None,#清除
                        ]},#搜索结束
                    ]},#槽结束
                    {'type':'div','class':('headerActions headerActionsHidden' if 自身.检索展开 else 'headerActions'),'children':[#动作
                        自身.渲染查看选项(分组方式,排序方式),#查看选项
                        {'type':'button','class':'iconButton','aria-label':自身.翻译('workspace.add'),'onClick':'add'} if 目录流可用 else None,#添加
                    ]},#动作结束
                    挑选.渲染(),#添加流
                ]},#区头结束
                {'type':'div','class':'listArea','children':[列表体]},#列表席
                *自身.渲染对话框(),#对话框
            ],#子结束
        }#根结束

    def 设分组展开(自身,键,展开):#写 groupExpansion
        """写 store 的分组展开。"""
        动作=自身.读动作()#动作
        if 动作 is None or 'setGroupExpanded' not in 动作:#无
            return#停
        动作['setGroupExpanded'](自身.读快照(),键,展开)#写入

    def 切换分组(自身,键):#翻转分组展开
        """写回 store 的 groupExpansion。"""
        快照=自身.读快照()#当前
        展开表=快照['groupExpansion'] if 'groupExpansion' in 快照 and 快照['groupExpansion'] is not None else {}#展开
        当前=bool(展开表[键]) if 键 in 展开表 else False#当前展开
        if 当前:#收起时清本地溢出
            自身.本地展开其余=[项 for 项 in 自身.本地展开其余 if 项!=键]#去掉
        动作=自身.读动作()#动作
        if 动作 is None or 'setGroupExpanded' not in 动作:#无
            return#停
        动作['setGroupExpanded'](快照,键,not 当前)#翻转

    def 开重命名(自身,工作区标识,当前标题):#打开工作区重命名
        """记下重命名目标。"""
        if 工作区标识 is None:#未分组
            return#停
        自身.重命名目标={'workspaceId':工作区标识,'currentTitle':当前标题}#目标
        自身.重命名草稿=当前标题#草稿
        自身.重命名错误=None错

    def 开删除(自身,工作区标识,标题):#打开删除确认
        """记下删除目标。"""
        if 工作区标识 is None:#未分组
            return#停
        自身.删除目标={'workspaceId':工作区标识,'title':标题}#目标
        自身.删除错误=None错

    def 开会话重命名(自身,会话标识,当前标题):#打开会话重命名
        """记下会话重命名目标。"""
        自身.会话重命名目标={'sessionId':会话标识,'currentTitle':当前标题}#目标
        自身.会话重命名草稿=当前标题#草稿
        自身.会话重命名错误=None错

    def 归档会话(自身,会话标识):#无对话框归档
        """直接提交归档；失败只诊断。注入面已等待。"""
        归档=自身.属性['archiveSession'] if 'archiveSession' in 自身.属性 else None#注入
        if 归档 is None:#无
            return#停
        try:#提交
            归档(会话标识)#调用；已等待
        except Exception:#失败；归档 RPC 异常契约未定，故不能换成更窄的 except
            pass#非致命

    def 触发正文检索(自身):#防抖宿主检索
        """非空白查询经防抖调用 searchSessions。注入面已等待。"""
        查询=自身.清洗查询().strip()#查询
        搜索=自身.属性['searchSessions'] if 'searchSessions' in 自身.属性 else None#注入检索
        if 查询=='' or 搜索 is None:#无需
            自身.正文结果={'items':[],'hasMore':False}#清空
            自身.检索警告=None警告
            自身.检索中=False
            return#停
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
        """搜索、添加、查看选项、对话框与溢出。"""
        属性=自身.属性#props
        动作集=自身.读动作()#store 动作
        if 动作=='rail-search':#轨搜索
            展开=属性['expandSidebar'] if 'expandSidebar' in 属性 else None#请求扩宽
            if 展开 is not None:#有
                展开()#扩宽
            自身.检索展开=True#开检索
            return#已处理
        if 动作=='rail-add':#轨添加
            展开=属性['expandSidebar'] if 'expandSidebar' in 属性 else None#请求扩宽
            if 展开 is not None:#有
                展开()#扩宽
            自身.添加开=True#开流
            return#已处理
        if 动作=='search-open':#展开搜索
            自身.添加开=False#关添加
            自身.检索展开=True#开
            return#已处理
        if 动作=='search-clear':#清除搜索
            自身.查询=''
            自身.检索展开=False#收
            自身.触发正文检索()#清正文
            return#已处理
        if 动作=='search':#改查询
            自身.查询=消毒检索查询(载荷 if 载荷 is not None else '')#写入
            自身.触发正文检索()#防抖检索
            return#已处理
        if 动作=='search-key' and 载荷=='Escape':#Escape
            自身.查询=''
            自身.检索展开=False#收
            自身.触发正文检索()#清正文
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
                    """整表。"""
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
                        已记账.add(标识)#记下
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
                return#停
            标题=自身.重命名草稿.strip()#修剪
            if 标题=='' or 标题==自身.重命名目标['currentTitle']:#无变
                return#停
            改名=属性['renameWorkspace'] if 'renameWorkspace' in 属性 else None#注入
            if 改名 is None:#无
                return#停
            自身.重命名中=True#忙
            try:#提交
                改名(自身.重命名目标['workspaceId'],标题)#调用；已等待
                自身.重命名目标=None#关
                自身.重命名错误=None
            except Exception as 原因:#失败；重命名 RPC 异常契约未定，故不能换成更窄的 except
                自身.重命名错误=str(原因)#文案
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
                return#停
            标题=自身.会话重命名草稿.strip()#修剪
            if 标题=='':#空
                return#停
            改名=属性['renameSession'] if 'renameSession' in 属性 else None#注入
            if 改名 is None:#无
                return#停
            自身.会话重命名中=True#忙
            try:#提交
                改名(自身.会话重命名目标['sessionId'],标题)#调用；已等待
                自身.会话重命名目标=None#关
                自身.会话重命名错误=None
            except Exception as 原因:#失败；会话改名 RPC 异常契约未定，故不能换成更窄的 except
                自身.会话重命名错误=str(原因)#文案
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
                return#停
            删除=属性['deleteWorkspace'] if 'deleteWorkspace' in 属性 else None#注入
            if 删除 is None:#无
                return#停
            自身.删除中=True#忙
            自身.删除错误=None
            try:#提交
                删除(自身.删除目标['workspaceId'])#调用；已等待
                自身.删除已提交标识=自身.删除目标['workspaceId']#等投影
            except Exception as 原因:#失败；删除 RPC 异常契约未定，故不能换成更窄的 except
                自身.删除中=False#闲
                自身.删除错误=str(原因)#文案
            return#已处理
