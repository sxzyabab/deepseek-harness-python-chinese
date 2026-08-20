"""侧栏工作区浏览区：分区标题、搜索、分组/扁平列表、对话框与添加流。

对齐上游 `ui-workspace/src/client/WorkspaceBrowser.tsx`。
宽态渲染完整浏览区；轨态渲染搜索/添加两枚区头控件并请求外壳展开。
添加流与错误对话框同包直连 `工作区挑选流`。公开面仅中文名。
"""
import time#相对时间 now
from .树 import 取字段,未分组键,派生分组,派生扁平,派生检索结果#树派生
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

def 调和会话顺序(会话标识们,已存):#调和已存顺序与当前账本
    """接受已存顺序，未知键跳过，新成员追加到末尾。"""
    if 已存 is None:#无已存
        return list(会话标识们)#原样拷贝
    按标识={标识:标识 for 标识 in 会话标识们}#id 集
    有序=[]#结果
    已纳入=set()#已纳入
    for 键 in 已存:#先走已存
        标识=按标识.get(键)#查
        if 标识 is None or 键 in 已纳入:#未知或重复
            continue#跳过
        有序.append(标识)#追加
        已纳入.add(键)#记下
    for 标识 in 会话标识们:#再收新成员
        if 标识 in 已纳入:#已有
            continue#跳过
        有序.append(标识)#追加
    return 有序#调和后顺序

def 比较会话近因(甲,乙,按标识):#近因比较
    """最新在前，id 决胜。"""
    甲时=取字段(按标识.get(甲) if isinstance(按标识,dict) else None,'updatedAt')#甲时间
    乙时=取字段(按标识.get(乙) if isinstance(按标识,dict) else None,'updatedAt')#乙时间
    if 甲时 is None:#缺席
        甲时=float('-inf')#负无穷
    if 乙时 is None:#缺席
        乙时=float('-inf')#负无穷
    if 乙时!=甲时:#时间不同
        return 乙时-甲时#新的在前
    return -1 if 甲<乙 else 1#id 决胜

def 下一会话顺序账本(会话标识们,先前顺序,先前更新时间,列表,排序方式,按近因排序):#调和并套提升政策
    """调和一份可编辑顺序账本并套用活动提升政策。"""
    顺序=调和会话顺序(会话标识们,先前顺序)#先调和
    按标识=取字段(列表,'byId') or {}#摘要表
    if 按近因排序:#进入最近更新时全量时间排序
        顺序=sorted(顺序,key=lambda 标识:(-取字段(按标识.get(标识) if isinstance(按标识,dict) else None,'updatedAt',float('-inf')),标识))#近因
    elif 排序方式=='updated':#活动提升
        提升=[]#新活动
        for 标识 in 会话标识们:#逐会话
            会话=按标识.get(标识) if isinstance(按标识,dict) else None#摘要
            if 会话 is None:#缺席
                continue#跳过
            先前=先前更新时间.get(标识) if 先前更新时间 else None#先前时间戳
            if 先前 is None or 取字段(会话,'updatedAt')>先前:#新或变新
                提升.append(标识)#收入提升
        提升=sorted(提升,key=lambda 标识:(-取字段(按标识.get(标识) if isinstance(按标识,dict) else None,'updatedAt',float('-inf')),标识))#近因排提升
        if len(提升)>0:#有提升
            提升集=set(提升)#集合
            顺序=提升+[标识 for 标识 in 顺序 if 标识 not in 提升集]#提升置顶
    更新时间={}#新时间戳表
    for 标识 in 会话标识们:#逐会话
        会话=按标识.get(标识) if isinstance(按标识,dict) else None#摘要
        if 会话 is not None:#有摘要
            更新时间[标识]=取字段(会话,'updatedAt')#记下
    顺序变=先前顺序 is None or len(顺序)!=len(先前顺序) or any(顺序[下标]!=先前顺序[下标] for 下标 in range(len(顺序)))#顺序变
    时间变=len(更新时间)!=len(先前更新时间 or {}) or any(更新时间.get(标识)!=(先前更新时间 or {}).get(标识) for 标识 in 更新时间)#时间变
    return {'order':顺序,'updatedAt':更新时间,'changed':顺序变 or 时间变}#账本结果

class 工作区浏览区:#侧栏浏览区
    """宽态完整浏览器；轨道态两枚区头控件请求外壳展开。"""
    def __init__(自身,属性):#浏览区 props
        """记下注入动作、store、文案与外壳份额。"""
        自身.属性=属性#完整 props
        自身.翻译=取字段(属性,'t')#文案
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

    def 读仓库(自身):#浏览 store 快照
        """读 useStore 或 store 快照。"""
        属性=自身.属性#props
        读=取字段(属性,'useStore')#钩
        if 读 is not None:#有钩
            return 读(lambda 状态:状态)#快照
        存储=取字段(属性,'store')#句柄
        if 存储 is None:#无
            return {'groupBy':'workspace','orderBy':'updated','groupExpansion':{},'sessionOrderByAccount':{},'sessionUpdatedAtByAccount':{}}#默认
        快照=取字段(存储,'getSnapshot')#方法
        if callable(快照):#有
            return 快照()#读
        return 存储 if isinstance(存储,dict) else {}#映射

    def 读动作(自身):#store 动作
        """优先 props.actions，其次 store.actions / storeActions。"""
        属性=自身.属性#props
        动作=取字段(属性,'actions') or 取字段(属性,'storeActions')#直接注入
        if 动作 is not None:#有
            return 动作#返回
        存储=取字段(属性,'store')#句柄
        return 取字段(存储,'actions') if 存储 is not None else None#嵌套

    def 同步顺序账本(自身,列表,工作区们,归档):#对齐上游 SessionTree/FlatList effect
        """按 orderBy 调和各账本顺序并写回 store。"""
        动作=自身.读动作()#动作
        if 动作 is None or not callable(取字段(动作,'syncSessionOrderAccount')):#无写口
            return#停
        相位=取字段(列表,'phase')#列表相位
        if 相位 is not None and 相位!='ready':#未就绪
            return#停
        仓库=自身.读仓库()#当前
        排序=取字段(仓库,'orderBy') or 'updated'#排序
        切到近因=自身.先前排序方式 is not None and 自身.先前排序方式!='updated' and 排序=='updated'#切入 updated
        自身.先前排序方式=排序#记下
        顺序表=取字段(仓库,'sessionOrderByAccount') or {}#顺序
        时间表=取字段(仓库,'sessionUpdatedAtByAccount') or {}#时间
        已记账=set()#工作区已占会话
        for 区 in 工作区们:#逐区
            for 标识 in 取字段(区,'sessionIds') or []:#成员
                已记账.add(标识)#记下
        未分组=[标识 for 标识 in 取字段(列表,'ids') or [] if 取字段(取字段(列表,'byId'),标识) is not None and 标识 not in 已记账]#松散
        账本们=[]#待同步
        for 区 in 工作区们:#工作区账本
            键=取字段(区,'workspaceId')#工作区 id
            if 键 is None:#缺 id
                continue#跳过
            账本们.append({'key':键,'sessionIds':[标识 for 标识 in 取字段(区,'sessionIds') or [] if 取字段(取字段(列表,'byId'),标识) is not None]})#追加
        账本们.append({'key':未分组键,'sessionIds':未分组})#未分组
        账本们.append({'key':扁平会话顺序键,'sessionIds':[取字段(行,'id') for 行 in 派生扁平(列表,归档)]})#扁平账本
        for 账本 in 账本们:#逐账本
            键=取字段(账本,'key')#键
            下一=下一会话顺序账本(取字段(账本,'sessionIds') or [],顺序表.get(键),时间表.get(键) or {},列表,排序,排序=='updated' and (顺序表.get(键) is None or 切到近因))#下一账本
            if 取字段(下一,'changed'):#有变
                取字段(动作,'syncSessionOrderAccount')(仓库,键,[标识 for 标识 in 取字段(下一,'order')],取字段(下一,'updatedAt'))#写回

    def 渲染查看选项(自身,分组方式,排序方式):#分组/排序菜单
        """对齐上游 ViewOptionsMenu。"""
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

    def 渲染对话框们(自身):#重命名/删除
        """浏览器自有对话框，避免行卸载带走确认态。"""
        重命名阻=自身.重命名中 or 自身.重命名草稿.strip()=='' or 自身.重命名目标 is None or 自身.重命名草稿.strip()==取字段(自身.重命名目标,'currentTitle')#阻塞
        会话阻=自身.会话重命名中 or 自身.会话重命名草稿.strip()=='' or 自身.会话重命名目标 is None#会话阻塞（允许确认当前标题）
        return [#对话框列表
            {'type':'Modal','open':自身.重命名目标 is not None,'onClose':'rename-close','title':自身.翻译('rename.workspace.title'),'children':[{'type':'input','class':'renameInput','value':自身.重命名草稿,'aria-label':自身.翻译('field.workspaceName'),'onChange':'rename-draft'},{'type':'div','class':'renameError','role':'alert','children':[自身.重命名错误]} if 自身.重命名错误 else None],'footer':[{'type':'Button','variant':'outline','disabled':自身.重命名中,'onClick':'rename-close','label':自身.翻译('cancel')},{'type':'Button','variant':'primary','disabled':重命名阻,'onClick':'rename-confirm','label':自身.翻译('rename')}]},#工作区重命名
            {'type':'Modal','open':自身.会话重命名目标 is not None,'onClose':'session-rename-close','title':自身.翻译('rename.session.title'),'children':[{'type':'input','class':'renameInput','value':自身.会话重命名草稿,'aria-label':自身.翻译('field.sessionName'),'onChange':'session-rename-draft'},{'type':'div','class':'renameError','role':'alert','children':[自身.会话重命名错误]} if 自身.会话重命名错误 else None],'footer':[{'type':'Button','variant':'outline','disabled':自身.会话重命名中,'onClick':'session-rename-close','label':自身.翻译('cancel')},{'type':'Button','variant':'primary','disabled':会话阻,'onClick':'session-rename-confirm','label':自身.翻译('rename')}]},#会话重命名
            {'type':'Modal','open':自身.删除目标 is not None,'onClose':'delete-close','title':自身.翻译('delete.workspace'),'description':自身.翻译('delete.desc',{'name':取字段(自身.删除目标,'title')}) if 自身.删除目标 else None,'children':[{'type':'div','class':'deleteStatus','role':'status','children':[自身.翻译('delete.pending')]} if 自身.删除中 else None,{'type':'div','class':'renameError','role':'alert','children':[自身.删除错误]} if 自身.删除错误 else None],'footer':[{'type':'Button','variant':'outline','disabled':自身.删除中,'onClick':'delete-close','label':自身.翻译('cancel')},{'type':'Button','variant':'outline','class':'deleteAction','disabled':自身.删除中,'onClick':'delete-confirm','label':自身.翻译('delete.workspace')}]},#删除
        ]#列表结束

    def 渲染(自身):#结构树
        """返回浏览区结构树。"""
        属性=自身.属性#props
        宽=取字段(属性,'wide',True)#宽态
        用会话=取字段(属性,'useSessions')#会话钩
        用工作区=取字段(属性,'useWorkspaces')#工作区钩
        列表=用会话(lambda 状态:状态) if 用会话 else {'ids':[],'byId':{},'current':None}#会话列表
        工作区快照=用工作区(lambda 状态:状态) if 用工作区 else {'items':[],'archivedSessionIds':[]}#工作区
        工作区们=取字段(工作区快照,'items') or []#列表
        归档=取字段(工作区快照,'archivedSessionIds') or []#归档 id
        仓库=自身.读仓库()#查看态
        自身.同步顺序账本(列表,工作区们,归档)#调和账本
        if 自身.删除已提交标识 is not None and not any(取字段(区,'workspaceId')==自身.删除已提交标识 for 区 in 工作区们):#删除投影已落地
            自身.删除中=False#清
            自身.删除已提交标识=None#清
            自身.删除目标=None#关
        目录流可用=取字段(属性,'useDirectoryFlow')(lambda 占用:占用) if 取字段(属性,'useDirectoryFlow') else False#添加入口
        if not 宽:#轨态
            return {#轨
                'type':'div','class':'root rail',#根
                'children':[#子
                    {'type':'div','class':'search','children':[{'type':'button','class':'searchButton','aria-label':自身.翻译('search.sessions.aria'),'onClick':'rail-search'}]},#搜索
                    {'type':'button','class':'iconButton','aria-label':自身.翻译('workspace.add'),'onClick':'rail-add'} if 目录流可用 else None,#添加
                    工作区挑选流({#添加流
                        't':自身.翻译,'open':自身.添加开,'useWorkspaces':用工作区,'createWorkspace':取字段(属性,'createWorkspace'),#基础
                        'useDirectoryFlow':取字段(属性,'useDirectoryFlow'),#占用
                        'renderDirectoryFlow':lambda 主人:取字段(属性,'renderSlot')('sidebar.workspaces.directoryFlow',主人) if 取字段(属性,'renderSlot') else None,#孔
                        'onPick':lambda 标识:(setattr(自身,'添加开',False),取字段(属性,'startSession')(标识)),#挑中
                        'onClose':lambda:setattr(自身,'添加开',False),'addOnly':True,'side':'right',#关闭
                    }).渲染(),#流
                ],#子结束
            }#轨结束
        展开键=[键 for 键,开 in (取字段(仓库,'groupExpansion') or {}).items() if 开]#已展开
        视图={'expandedGroups':展开键,'ungroupedOrder':取字段(取字段(仓库,'sessionOrderByAccount'),未分组键)}#树视图
        查询=自身.清洗查询().strip()#非空白查询
        现在=int(time.time()*1000)#当前毫秒
        分组方式=取字段(仓库,'groupBy') or 'workspace'#分组
        排序方式=取字段(仓库,'orderBy') or 'updated'#排序
        if 查询!='':#检索模式
            结果=派生检索结果(列表,工作区们,查询,归档,自身.正文结果,取字段(属性,'searchResultLimit') or 20)#合并检索
            行们=[检索结果行(项,lambda 标识=取字段(项,'id'):取字段(属性,'open')(标识),自身.翻译).渲染() for 项 in 取字段(结果,'items') or []]#检索行
            树子=行们 if 行们 else [{'type':'div','class':'empty','children':[自身.翻译('search.noMatches')]}]#空态
            if 自身.检索中:#进行中
                树子.insert(0,{'type':'div','class':'searchStatus','role':'status','children':[自身.翻译('search.pending')]})#挂起
            if 自身.检索警告:#内容检索失败
                树子.insert(0,{'type':'div','class':'searchWarning','role':'status','children':[自身.翻译('search.unavailable')]})#警告
            if 取字段(结果,'hasMore'):#截断提示
                树子.append({'type':'div','class':'searchStatus','children':[自身.翻译('search.hasMore',{'n':取字段(属性,'searchResultLimit') or 20})]})#提示
            列表体={'type':'div','class':'treeBody wide','children':[{'type':'div','class':'list','role':'tree','aria-label':自身.翻译('search.results.aria'),'children':树子},{'type':'span','class':'fade'}]}#检索体
        elif 分组方式=='flat':#扁平
            扁基=派生扁平(列表,归档)#扁平行
            扁序=调和会话顺序([取字段(行,'id') for 行 in 扁基],取字段(取字段(仓库,'sessionOrderByAccount'),扁平会话顺序键))#本地序
            按标识={取字段(行,'id'):行 for 行 in 扁基}#索引
            扁=[按标识[标识] for 标识 in 扁序 if 标识 in 按标识]#有序
            树子=[会话行(项,lambda 标识=取字段(项,'id'):取字段(属性,'open')(标识),{'rename':lambda 标识=取字段(项,'id'),标题=取字段(项,'title'):自身.开会话重命名(标识,标题),'archive':lambda 标识=取字段(项,'id'):自身.归档会话(标识),'fork':取字段(属性,'forkSession')},自身.翻译,现在).渲染() for 项 in 扁] or [{'type':'div','class':'empty','children':[自身.翻译('empty.none')]}]#行或空
            列表体={'type':'div','class':'treeBody wide','children':[{'type':'div','class':'list flatList','role':'tree','aria-label':自身.翻译('section.sessions'),'children':树子},{'type':'span','class':'fade'}]}#扁平体
        else:#按工作区分组
            有序工作区=[]#带本地序的工作区
            for 区 in 工作区们:#逐区
                序=调和会话顺序(取字段(区,'sessionIds') or [],取字段(取字段(仓库,'sessionOrderByAccount'),取字段(区,'workspaceId')))#序
                拷=dict(区) if isinstance(区,dict) else {'workspaceId':取字段(区,'workspaceId'),'title':取字段(区,'title'),'sessionIds':取字段(区,'sessionIds')}#拷贝
                拷['sessionIds']=序#写入
                有序工作区.append(拷)#追加
            组们=派生分组(列表,有序工作区,归档,视图)#分组
            树子=[]#树节点
            if len(组们)==0:#空
                树子.append({'type':'div','class':'empty','children':[自身.翻译('empty.none')]})#空
            for 组 in 组们:#逐组
                键=取字段(组,'key')#组键
                树子.append(项目行(组,lambda 键=键:自身.切换分组(键),lambda 标识=取字段(组,'workspaceId'):(自身.设分组展开(键,True),取字段(属性,'startSession')(标识)),{'rename':lambda 标识=取字段(组,'workspaceId'),标题=取字段(组,'label'):自身.开重命名(标识,标题),'delete':lambda 标识=取字段(组,'workspaceId'),标题=取字段(组,'label'):自身.开删除(标识,标题)} if 取字段(组,'workspaceId') is not None else None,自身.翻译).渲染())#头行
                if 取字段(组,'expanded'):#展开
                    会话们=取字段(组,'sessions') or []#会话
                    溢出=键 in 自身.本地展开其余#本地溢出
                    可见=会话们 if 溢出 or len(会话们)<=折叠会话上限 else 会话们[:折叠会话上限]#截断
                    for 项 in 可见:#会话行
                        树子.append(会话行(项,lambda 标识=取字段(项,'id'):取字段(属性,'open')(标识),{'rename':lambda 标识=取字段(项,'id'),标题=取字段(项,'title'):自身.开会话重命名(标识,标题),'archive':lambda 标识=取字段(项,'id'):自身.归档会话(标识),'fork':取字段(属性,'forkSession')},自身.翻译,现在).渲染())#行
                    if len(会话们)>折叠会话上限:#展开其余
                        树子.append({'type':'button','class':'sessionOverflowButton','aria-expanded':溢出,'onClick':('overflow',键),'children':[自身.翻译('sessions.collapse') if 溢出 else 自身.翻译('sessions.expand',{'n':len(会话们)-折叠会话上限})]})#控件
            列表体={'type':'div','class':'treeBody wide','children':[{'type':'div','class':'list','role':'tree','aria-label':自身.翻译('section.sessions'),'children':树子},{'type':'span','class':'fade'}]}#分组体
        挑选=工作区挑选流({#添加流程
            't':自身.翻译,#文案
            'open':自身.添加开,#开关
            'useWorkspaces':用工作区,#工作区钩
            'createWorkspace':取字段(属性,'createWorkspace'),#创建
            'useDirectoryFlow':取字段(属性,'useDirectoryFlow'),#占用
            'renderDirectoryFlow':lambda 主人:取字段(属性,'renderSlot')('sidebar.workspaces.directoryFlow',主人) if 取字段(属性,'renderSlot') else None,#孔
            'onPick':lambda 标识:(setattr(自身,'添加开',False),取字段(属性,'startSession')(标识)),#挑中后开会话
            'onClose':lambda:setattr(自身,'添加开',False),#关闭
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
                *自身.渲染对话框们(),#对话框
            ],#子结束
        }#根结束

    def 设分组展开(自身,键,展开):#写 groupExpansion
        """写 store 的分组展开。"""
        动作=自身.读动作()#动作
        if 动作 is None or not callable(取字段(动作,'setGroupExpanded')):#无
            return#停
        取字段(动作,'setGroupExpanded')(自身.读仓库(),键,展开)#写入

    def 切换分组(自身,键):#翻转分组展开
        """写回 store 的 groupExpansion。"""
        仓库=自身.读仓库()#当前
        当前=bool(取字段(取字段(仓库,'groupExpansion'),键))#当前展开
        if 当前:#收起时清本地溢出
            自身.本地展开其余=[项 for 项 in 自身.本地展开其余 if 项!=键]#去掉
        动作=自身.读动作()#动作
        if 动作 is None or not callable(取字段(动作,'setGroupExpanded')):#无
            return#停
        取字段(动作,'setGroupExpanded')(仓库,键,not 当前)#翻转

    def 开重命名(自身,工作区标识,当前标题):#打开工作区重命名
        """记下重命名目标。"""
        if 工作区标识 is None:#未分组
            return#停
        自身.重命名目标={'workspaceId':工作区标识,'currentTitle':当前标题}#目标
        自身.重命名草稿=当前标题#草稿
        自身.重命名错误=None#清错

    def 开删除(自身,工作区标识,标题):#打开删除确认
        """记下删除目标。"""
        if 工作区标识 is None:#未分组
            return#停
        自身.删除目标={'workspaceId':工作区标识,'title':标题}#目标
        自身.删除错误=None#清错

    def 开会话重命名(自身,会话标识,当前标题):#打开会话重命名
        """记下会话重命名目标。"""
        自身.会话重命名目标={'sessionId':会话标识,'currentTitle':当前标题}#目标
        自身.会话重命名草稿=当前标题#草稿
        自身.会话重命名错误=None#清错

    def 归档会话(自身,会话标识):#无对话框归档
        """直接提交归档；失败只诊断。"""
        归档=取字段(自身.属性,'archiveSession')#注入
        if 归档 is None:#无
            return#停
        try:#提交
            结果=归档(会话标识)#调用
            if hasattr(结果,'等待'):#承诺
                结果.等待()#等待
        except Exception:#失败
            pass#与上游一样非致命

    def 触发正文检索(自身):#防抖宿主检索
        """非空白查询经防抖调用 searchSessions。"""
        查询=自身.清洗查询().strip()#查询
        搜索=取字段(自身.属性,'searchSessions')#注入检索
        if 查询=='' or 搜索 is None:#无需
            自身.正文结果={'items':[],'hasMore':False}#清空
            自身.检索警告=None#清警告
            自身.检索中=False#清
            return#停
        自身.检索中=True#标记
        try:#请求
            结果=搜索(查询,None)#检索
            if hasattr(结果,'等待'):#承诺
                结果=结果.等待()#等待
            自身.正文结果=结果 if 结果 is not None else {'items':[],'hasMore':False}#写入
            自身.检索警告=None#成功
        except Exception:#内容检索失败
            自身.检索警告='unavailable'#警告
            自身.正文结果={'items':[],'hasMore':False}#仅本地匹配
        自身.检索中=False#结束

    def 处理动作(自身,动作,载荷=None):#分发交互
        """搜索、添加、查看选项、对话框与溢出。"""
        属性=自身.属性#props
        动作集=自身.读动作()#store 动作
        if 动作=='rail-search':#轨搜索
            展开=取字段(属性,'expandSidebar')#请求扩宽
            if callable(展开):#有
                展开()#扩宽
            自身.检索展开=True#开检索
            return#已处理
        if 动作=='rail-add':#轨添加
            展开=取字段(属性,'expandSidebar')#请求扩宽
            if callable(展开):#有
                展开()#扩宽
            自身.添加开=True#开流
            return#已处理
        if 动作=='search-open':#展开搜索
            自身.添加开=False#关添加
            自身.检索展开=True#开
            return#已处理
        if 动作=='search-clear':#清除搜索
            自身.查询=''#清
            自身.检索展开=False#收
            自身.触发正文检索()#清正文
            return#已处理
        if 动作=='search':#改查询
            自身.查询=消毒检索查询(载荷 if 载荷 is not None else '')#写入
            自身.触发正文检索()#防抖检索
            return#已处理
        if 动作=='search-key' and 载荷=='Escape':#Escape
            自身.查询=''#清
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
            if 载荷 in ('workspace','flat') and 动作集 is not None and callable(取字段(动作集,'setGroupBy')):#分组
                取字段(动作集,'setGroupBy')(自身.读仓库(),载荷)#写
            elif 载荷 in ('manual','updated') and 动作集 is not None and callable(取字段(动作集,'setOrderBy')):#排序
                取字段(动作集,'setOrderBy')(自身.读仓库(),载荷)#写
            自身.查看选项开=False#关
            return#已处理
        if isinstance(动作,tuple) and 动作[0]=='overflow':#展开其余
            自身.本地展开其余=切换成员(自身.本地展开其余,动作[1])#切换
            return#已处理
        if 动作=='rename-draft':#重命名草稿
            自身.重命名草稿=载荷 if 载荷 is not None else ''#写
            自身.重命名错误=None#清
            return#已处理
        if 动作=='rename-close':#关重命名
            if 自身.重命名中:#进行中
                return#拒
            自身.重命名目标=None#清
            自身.重命名错误=None#清
            return#已处理
        if 动作=='rename-confirm':#确认重命名
            if 自身.重命名目标 is None or 自身.重命名中:#无效
                return#停
            标题=自身.重命名草稿.strip()#修剪
            if 标题=='' or 标题==取字段(自身.重命名目标,'currentTitle'):#无变
                return#停
            改名=取字段(属性,'renameWorkspace')#注入
            if 改名 is None:#无
                return#停
            自身.重命名中=True#忙
            try:#提交
                结果=改名(取字段(自身.重命名目标,'workspaceId'),标题)#调用
                if hasattr(结果,'等待'):#承诺
                    结果.等待()#等待
                自身.重命名目标=None#关
                自身.重命名错误=None#清
            except Exception as 原因:#失败
                自身.重命名错误=str(原因)#文案
            自身.重命名中=False#闲
            return#已处理
        if 动作=='session-rename-draft':#会话草稿
            自身.会话重命名草稿=载荷 if 载荷 is not None else ''#写
            自身.会话重命名错误=None#清
            return#已处理
        if 动作=='session-rename-close':#关会话重命名
            if 自身.会话重命名中:#忙
                return#拒
            自身.会话重命名目标=None#清
            自身.会话重命名错误=None#清
            return#已处理
        if 动作=='session-rename-confirm':#确认会话重命名
            if 自身.会话重命名目标 is None or 自身.会话重命名中:#无效
                return#停
            标题=自身.会话重命名草稿.strip()#修剪
            if 标题=='':#空
                return#停
            改名=取字段(属性,'renameSession')#注入
            if 改名 is None:#无
                return#停
            自身.会话重命名中=True#忙
            try:#提交
                结果=改名(取字段(自身.会话重命名目标,'sessionId'),标题)#调用
                if hasattr(结果,'等待'):#承诺
                    结果.等待()#等待
                自身.会话重命名目标=None#关
                自身.会话重命名错误=None#清
            except Exception as 原因:#失败
                自身.会话重命名错误=str(原因)#文案
            自身.会话重命名中=False#闲
            return#已处理
        if 动作=='delete-close':#关删除
            if 自身.删除中:#忙
                return#拒
            自身.删除目标=None#清
            自身.删除错误=None#清
            return#已处理
        if 动作=='delete-confirm':#确认删除
            if 自身.删除目标 is None or 自身.删除中:#无效
                return#停
            删除=取字段(属性,'deleteWorkspace')#注入
            if 删除 is None:#无
                return#停
            自身.删除中=True#忙
            自身.删除错误=None#清
            try:#提交
                结果=删除(取字段(自身.删除目标,'workspaceId'))#调用
                if hasattr(结果,'等待'):#承诺
                    结果.等待()#等待
                自身.删除已提交标识=取字段(自身.删除目标,'workspaceId')#等投影
            except Exception as 原因:#失败
                自身.删除中=False#闲
                自身.删除错误=str(原因)#文案
            return#已处理
