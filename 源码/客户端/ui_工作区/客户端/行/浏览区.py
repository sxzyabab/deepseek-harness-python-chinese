'侧栏里的工作区浏览区：标题、搜索、分组或扁平列表，以及工作区对话框'
from ....模块.客户端.通告 import 取握手窗口
import json
import os
import time
from ....ui_对话.异常 import 注入模块样式文件,标样式模块
from ....ui_基础界面组件.按钮 import 按钮
from ....ui_基础界面组件.提示泡 import 提示泡
from ....ui_基础界面组件.悬停卡组 import 悬停卡组
from ....ui_基础界面组件.菜单 import 菜单
from ....ui_基础界面组件.模态 import 模态
from ....ui_基础界面组件.icons import 图标
from ..会话动作.派生 import 换上
from ..导航 import 取同步结果
from ..文案 import 中文,填入,取消,关闭
from ..存储 import 扁平会话顺序键
from ..树 import (
    未分组键,派生分组,派生扁平,派生检索结果,按近因排序,拥有分组键,拥有父文件夹,
    钉住当前空白,调和手动顺序,会话成员标识,
)
from ..选择器 import 工作区挑选流,工作区显示标题,默认目录名
from .行 import 拼类,画图标,项目行,会话行,检索结果行
from .动画行 import 动画行

__all__=['工作区浏览区','工作区浏览区组件']

样式模块='workspace-browser'#浏览区样式
展开滑动毫秒=300#轨道展开后再聚焦
搜索等待毫秒=250#停键后再搜
搜索上限码元=500#查询最长
水位基数=5#默认可见条数
水位自动上限=50#自动抬高的上限

def 确保样式(文档):
    '浏览区样式只插一次'
    注入模块样式文件(文档,'工作区浏览区样式',os.path.join(os.path.dirname(__file__),'浏览区.module.css'),样式模块)

def 标(节点):
    '挂上浏览区样式模块'
    if 节点 is not None:#有
        标样式模块(节点,样式模块)#模块
    return 节点#节点

def 净化查询(值):
    '去掉空字符，并按 UTF-16 码元截到协议上限'
    文=值.replace('\0','')#去空字符
    if len(文)<=搜索上限码元:#没超
        return 文#原样
    尾=搜索上限码元#截断点
    末=ord(文[尾-1])#截断处
    下=ord(文[尾]) if 尾<len(文) else 0#下一个
    if 0xD800<=末<=0xDBFF and 0xDC00<=下<=0xDFFF:#拆开了代理对
        尾=尾-1#退一格
    return 文[:尾]#截断

def 水位行(会话列,水位):
    '空白都留，非空白只留水位条'
    计数=0#非空白
    行=[]#可见
    for 会话 in 会话列:#原顺序
        if 会话.get('blank'):#空白
            行.append(会话)#留
            continue#下一条
        计数=计数+1#一条
        if 计数<=水位:#还在水位内
            行.append(会话)#留
    return {'rows':行,'hiddenCount':len(会话列)-len(行)}#可见和隐藏

def 所需水位(会话列,当前,揭示号):
    '进行中、待处理、完成未读、当前或要揭示的行，把水位抬到它'
    下标=0#非空白序号
    需要=0#所需
    for 会话 in 会话列:#原顺序
        if 会话.get('blank'):#空白不计
            continue#跳过
        下标=下标+1#序号
        注目=下标<=水位自动上限 and (
            会话.get('running') or (会话.get('runningSubagentCount') or 0)>0
            or 会话.get('pendingInteraction') is not None or 会话.get('completed') or 会话['id']==当前
        )#自动范围内需要注意
        if 注目 or 会话['id']==揭示号:#要露出来
            需要=下标#抬到这里
    return 需要#水位

def 抬水位(标记,所需):
    '只升不降。没有变化就返回原表'
    抬过=标记#结果
    for 键,水位 in 所需.items():#逐组
        if 水位>(抬过.get(键) or 水位基数):#要更高
            抬过={**抬过,键:水位}#抬
    return 抬过#结果

def 会话拖顺序(顺序,行列表,拖,落在):
    '在完整账本里移动，藏着的成员留在原位'
    源=None#被拖的
    目标=None#落点
    for 行 in 行列表:#找
        if 行['id']==拖['sessionId']:#源
            源=行#记下
        if 行['id']==落在['id']:#目标
            目标=行#记下
    if 源 is None or 目标 is None or 源.get('blank'):#不能
        return None#不改
    if 源.get('pinned')!=拖['pinned'] or 目标.get('pinned')!=拖['pinned'] or 源['id']==目标['id']:#不同段或自己
        return None#不改
    if 源['id'] not in 顺序:#不在账本
        return None#不改
    段=[行 for 行 in 行列表 if 行.get('pinned')==拖['pinned']]#同一段
    源下标=0#源在段里的位置
    找到=False#找到没有
    for 行 in 段:#找位置
        if 行['id']==源['id']:#是它
            找到=True#找到
            break#停
        源下标=源下标+1#下一条
    if not 找到:#没有
        return None#不改
    去掉=[行 for 行 in 段 if 行['id']!=源['id']]#抽出源
    插入=0#插入点
    有目标=False#目标还在
    for 行 in 去掉:#找目标
        if 行['id']==目标['id']:#是它
            有目标=True#有
            break#停
        插入=插入+1#下一条
    if 落在['half']=='after':#放下面
        插入=插入+1#后一位
    if 插入==源下标:#位置没变
        return None#不改
    下一=[标识 for 标识 in 顺序 if 标识!=源['id']]#抽出
    if 目标['id'] not in 下一:#目标不在
        return None#不改
    目标下标=下一.index(目标['id'])#目标位置
    下一.insert(目标下标+(1 if 落在['half']=='after' else 0),源['id'])#插入
    空白=None#当前空白
    for 行 in 行列表:#找空白
        if 行.get('blank'):#空白
            空白=行['id']#号
            break#停
    return 钉住当前空白(下一,空白)#空白仍在最前

def 组半(事件):
    '工作区组的上半或下半'
    矩形=事件.currentTarget.getBoundingClientRect()#矩形
    if 事件.clientY<矩形.top+矩形.height/2:#上半
        return 'before'#上面
    return 'after'#下面

class 视图选项菜单:
    '分组、排序和归档筛选'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.开=False#菜单
        自身.根=None#节点

    def 渲染(自身):
        '打开时画出三组选项'
        属性=自身.属性#属性
        窗口=属性['window']#窗口
        def 关掉():
            '关掉菜单'
            自身.开=False#关
            自身.渲染()#重画
        def 选(标识):
            '写分组、排序或筛选'
            if 标识 in ('workspace','workspace-tree','flat'):#分组
                属性['onGroupPick'](标识)#分组
            elif 标识 in ('manual','updated'):#排序
                属性['onOrderPick'](标识)#排序
            elif 标识=='hide-archived':#隐藏
                属性['onArchivedFilterPick']('default')#默认
            elif 标识=='show-archived':#全部
                属性['onArchivedFilterPick']('show')#显示
            elif 标识=='only-archived':#仅归档
                属性['onArchivedFilterPick']('only')#仅
            自身.开=False#关
            自身.渲染()#重画
        筛选对照={'default':'hide-archived','show':'show-archived','only':'only-archived'}#选中项
        锚=文档按钮(窗口,'viewOptions.label',画图标(窗口,'sliders-16'),lambda 事件: 自身.切换())#按钮
        节点=菜单({
            'window':窗口,
            'open':自身.开,
            'onClose':关掉,
            'items':[
                {'type':'label','id':'group-by','text':中文['groupBy.label']},
                {'id':'workspace','label':中文['groupBy.workspace'],'icon':画图标(窗口,'folder-close-16')},
                {'id':'workspace-tree','label':中文['groupBy.workspaceTree'],'icon':画图标(窗口,'workspace-tree-16')},
                {'id':'flat','label':中文['groupBy.flat'],'icon':画图标(窗口,'flat-list-16')},
                {'type':'separator','id':'order-by-separator'},
                {'type':'label','id':'order-by','text':中文['orderBy.label']},
                {'id':'manual','label':中文['orderBy.manual'],'icon':画图标(窗口,'chevrons-up-down-16')},
                {'id':'updated','label':中文['orderBy.updated'],'icon':画图标(窗口,'clock-16')},
                {'type':'separator','id':'archived-filter-separator'},
                {'type':'label','id':'filter-by','text':中文['filterBy.label']},
                {'id':'hide-archived','label':中文['viewOptions.hideArchived'],'icon':画图标(窗口,'archive-off-16')},
                {'id':'show-archived','label':中文['viewOptions.showArchived'],'icon':画图标(窗口,'queue-14')},
                {'id':'only-archived','label':中文['viewOptions.onlyArchived'],'icon':画图标(窗口,'archive-check-16')},
            ],
            'selectedIds':[属性['groupBy'],属性['orderBy'],筛选对照[属性['archivedFilter']]],
            'onSelect':选,
            'align':'end',
            'dense':True,
            'listClassName':'viewOptionsMenu',
            'portal':True,
            'anchor':锚,
        }).渲染()#菜单
        return 换上(自身,节点)#节点

    def 切换(自身):
        '打开或关掉'
        自身.开=not 自身.开#切换
        自身.渲染()#重画

def 文档按钮(窗口,文案键,图标节点,点击):
    '标题栏上的图标按钮'
    文档=窗口.document#文档
    钮=文档.createElement('button')#按钮
    钮.type='button'#按钮
    钮.className=拼类('iconButton','wide')#类
    标(钮)#模块
    钮.setAttribute('aria-label',中文[文案键])#无障碍
    钮.addEventListener('click',点击)#点击
    if 图标节点 is not None:#有图标
        钮.appendChild(图标节点)#放入
    return 钮#按钮

class 空会话:
    '没有会话。只看归档时给出回到其它会话的按钮'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '图标和一句说明'
        属性=自身.属性#属性
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        仅归档=属性['rowState']['archivedFilter']=='only'#只看归档
        根=文档.createElement('div')#空
        根.className='emptyState'#类
        标(根)#模块
        根.setAttribute('data-row-key','empty')#键
        图=画图标(窗口,'archive-16' if 仅归档 else 'queue-14',24)#图标
        if 图 is not None:#有
            根.appendChild(图)#放入
        字=文档.createElement('div')#说明
        字.textContent=中文['empty.noneArchived'] if 仅归档 else 中文['empty.none']#说明
        根.appendChild(字)#放入
        if 仅归档:#可以回去
            钮=文档.createElement('button')#回去
            钮.type='button'#按钮
            钮.className='emptyAction'#类
            标(钮)#模块
            钮.textContent=中文['empty.viewOthers']#查看其他
            def 点(事件):
                '回到默认筛选'
                属性['onLeaveArchivedOnly']()#回去
            钮.addEventListener('click',点)#点击
            根.appendChild(钮)#放入
        return 换上(自身,根)#节点

class 工作区浏览区:
    '整块浏览区。搜索、对话框和水位都留在这一份上'
    def __init__(自身,属性):
        '记下属性和还没被重画清掉的状态'
        自身.属性=属性#属性
        自身.查询=''#搜索
        自身.搜索展开=False#搜索框
        自身.揭示号=None#要滚到的会话
        自身.远端={'query':'','status':'idle','items':[],'hasMore':False}#内容搜索
        自身.展开后搜索=False#轨道展开后聚焦
        自身.改名目标=None#工作区改名
        自身.改名草稿=''#草稿
        自身.正在改名=False#进行中
        自身.改名错误=None#错误
        自身.改名组合=False#输入法
        自身.删除目标=None#删除
        自身.正在删除=False#进行中
        自身.已提交删除=None#等列表里消失
        自身.删除错误=None#错误
        自身.水位={}#各组水位
        自身.水位动=0#水位变化用来复位动画
        自身.会话拖=None#会话拖
        自身.工作区拖=None#工作区拖
        自身.会话已放=False#这次放下处理过
        自身.工作区已放=False#这次放下处理过
        自身.搜索定时=None#防抖
        自身.搜索中止=None#上一次搜索的中止
        自身.视图菜单=None#视图菜单
        自身.挑选=None#添加流
        自身.加号=None#添加按钮
        自身.搜索输入=None#输入框
        自身.搜索根=None#搜索点击范围
        自身.动画=None#行动画
        自身.正在画=False#防止重入
        自身.根=None#节点
        自身.活动顺序={}#当前各账本顺序
        自身.上次搜索请求=0#快捷键搜索次数

    def 渲染(自身):
        '整块重画'
        if 自身.正在画:#重入
            return 自身.根#当前
        自身.正在画=True#画
        try:#画完放开
            return 自身.画出()#节点
        finally:#放开
            自身.正在画=False#结束

    def 画出(自身):
        '读钩子并画出头、列表和对话框'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        def 原样(值):
            '选择器原样返回'
            return 值#原样
        家=属性['useHostInfo'](lambda 信息: 信息.get('home') if isinstance(信息,dict) else getattr(信息,'home',None))#家目录
        快捷列=属性['useShortcuts'](原样) or []#快捷键目录
        搜索快捷=None#搜索
        添加快捷=None#添加
        新建快捷=None#新建
        for 行 in 快捷列:#找
            if 行.get('id')=='session.search':#搜索
                搜索快捷=行#记下
            elif 行.get('id')=='workspace.add':#添加
                添加快捷=行#记下
            elif 行.get('id')=='session.new':#新建
                新建快捷=行#记下
        快捷状态=属性['useWorkspaceShortcuts'](原样)#打开请求
        列表=属性['useSessions'](原样)#会话
        存储工作区=属性['useWorkspaces'](lambda 状态: 状态.get('items') or [])#工作区
        工作区列=[]#显示标题
        for 工作区 in 存储工作区:#逐个
            拷贝=dict(工作区)#拷贝
            拷贝['title']=工作区显示标题(工作区.get('title'),'默认工作区')#显示名
            工作区列.append(拷贝)#留下
        阶段=属性['useWorkspaces'](lambda 状态: 状态.get('phase'))#阶段
        流状态=属性['useWorkspaces'](lambda 状态: 状态.get('state'))#流
        归档号=属性['useWorkspaces'](lambda 状态: 状态.get('archivedSessionIds') or [])#归档
        置顶号=属性['useWorkspaces'](lambda 状态: 状态.get('pinnedSessionIds') or [])#置顶
        def 占用(值):
            '目录流有没有人'
            return 值 is True#占用
        可添加=属性['useDirectoryFlow'](占用)#可添加
        分组=属性['useStore'](lambda 状态: 状态.get('groupBy'))#分组
        排序=属性['useStore'](lambda 状态: 状态.get('orderBy'))#排序
        归档筛选=属性['useStore'](lambda 状态: 状态.get('archivedFilter') or 'default')#筛选
        展开表=属性['useStore'](lambda 状态: 状态.get('groupExpansion') or {})#展开
        顺序账=属性['useStore'](lambda 状态: 状态.get('sessionOrderByAccount') or {})#手动顺序
        宽=属性.get('wide') is not False#宽
        工作区就绪=阶段=='ready' and 流状态!='loading'#基线到了
        动作=属性['actions']#存储动作
        主号=None#主视图会话
        for 会话 in 列表.get('byId',{}).values():#找
            保留=会话.get('retainedBy') or {}#保留
            if (保留.get('mainView') or 0)>0:#主视图
                主号=会话['id']#这条
                break#停
        当前空白=主号 if 主号 is not None and (列表['byId'].get(主号) or {}).get('blank') else None#空白
        已入账=set()#已进工作区
        for 工作区 in 工作区列:#成员
            for 号 in 工作区.get('sessionIds') or []:#号
                已入账.add(号)#记下
        未分组成员=[号 for 号 in 列表.get('ids') or [] if 列表['byId'].get(号) is not None and 号 not in 已入账]#散落
        序态={'pinnedSessionIds':置顶号,'archivedSessionIds':归档号}#置顶和归档
        行态={**序态,'archivedFilter':归档筛选}#加上筛选
        扁平成员=会话成员标识(列表)#扁平全体
        def 排成员(成员号,账本键):
            '按当前排序得到这一本的顺序，空白在最前'
            if 排序=='updated':#近因
                基=按近因排序(成员号,列表['byId'])#近因
            else:#手动
                基=调和手动顺序(成员号,顺序账.get(账本键),列表['byId'],序态)#调和
            空白=当前空白 if 当前空白 is not None and 当前空白 in 成员号 else None#这一本的空白
            return 钉住当前空白(基,空白)#提前
        有序工作区=[]#带顺序的工作区
        for 工作区 in 工作区列:#逐个
            拷贝=dict(工作区)#拷贝
            拷贝['sessionIds']=排成员(工作区.get('sessionIds') or [],工作区['workspaceId'])#顺序
            有序工作区.append(拷贝)#留下
        有序未分组=排成员(未分组成员,未分组键)#未分组
        有序扁平=排成员(扁平成员,扁平会话顺序键)#扁平
        if 阶段=='ready':#可以丢掉不存在的账本
            动作['retainAccountKeys']([未分组键,扁平会话顺序键]+[项['workspaceId'] for 项 in 工作区列])#保留
        活动顺序={}#当前算出的顺序
        for 工作区 in 有序工作区:#工作区
            活动顺序[工作区['workspaceId']]=工作区['sessionIds']#顺序
        活动顺序[未分组键]=有序未分组#未分组
        活动顺序[扁平会话顺序键]=有序扁平#扁平
        自身.活动顺序=活动顺序#拖放时铺入手动账本
        if 主号 is not None and 工作区就绪 and 分组!='flat':#当前组没有记过展开就展开
            当前组=拥有分组键(有序工作区,主号)#当前组
            if 当前组 not in 展开表:#还没记
                动作['setGroupExpanded'](当前组,True)#展开
        查询=净化查询(自身.查询).strip()#查询
        if 快捷状态.get('searchRequest') not in (None,自身.上次搜索请求) and 快捷状态.get('searchRequest')!=0:#新的搜索命令
            自身.上次搜索请求=快捷状态['searchRequest']#记下
            属性['closeAddWorkspace']()#关掉添加
            自身.搜索展开=True#展开
            if not 宽:#轨道
                自身.展开后搜索=True#等展开
                属性['expandSidebar']()#展开
        根=文档.createElement('div')#根
        根.className=拼类('root',None if 宽 else 'rail')#类
        标(根)#模块
        头=文档.createElement('div')#头
        头.className='sectionHeader'#类
        标(头)#模块
        if 宽:#宽才有标题
            题=文档.createElement('span')#标题
            题.className=拼类('sectionLabel','wide','sectionLabelHidden' if 自身.搜索展开 else None)#类
            标(题)#模块
            题.textContent=中文['section.sessions'] if 分组=='flat' else 中文['section.workspaces']#标题
            头.appendChild(题)#放入
            搜索槽=文档.createElement('div')#搜索槽
            搜索槽.className=拼类('searchSlot','searchSlotExpanded' if 自身.搜索展开 else None)#类
            标(搜索槽)#模块
            搜索=文档.createElement('div')#搜索
            搜索.className=拼类('search','searchExpanded' if 自身.搜索展开 else None)#类
            标(搜索)#模块
            自身.搜索根=搜索#点击范围
            def 点搜索(事件):
                '展开并聚焦'
                属性['closeAddWorkspace']()#关添加
                自身.搜索展开=True#展开
                自身.渲染()#重画
                if 自身.搜索输入 is not None:#有输入
                    自身.搜索输入.focus()#聚焦
            搜索.addEventListener('click',点搜索)#点击
            搜钮=文档.createElement('button')#搜索按钮
            搜钮.type='button'#按钮
            搜钮.className='searchButton'#类
            标(搜钮)#模块
            搜钮.setAttribute('aria-label',中文['search.sessions.aria'])#无障碍
            搜钮.setAttribute('aria-expanded','true' if 自身.搜索展开 else 'false')#展开
            if isinstance(搜索快捷,dict) and 搜索快捷.get('aria'):#快捷键
                搜钮.setAttribute('aria-keyshortcuts',str(搜索快捷['aria']))#组合
            def 点搜(事件):
                '走搜索命令'
                属性['requestSearch']()#请求
            搜钮.addEventListener('click',点搜)#点击
            搜图=画图标(窗口,'search-16',11 if 自身.搜索展开 else 14)#图标
            if 搜图 is not None:#有
                搜钮.appendChild(搜图)#放入
            搜泡=提示泡({
                'window':窗口,'label':'搜索','shortcutKeys':搜索快捷.get('keys') if isinstance(搜索快捷,dict) else None,
                'side':'bottom','delayMs':500,'disabled':自身.搜索展开,'children':搜钮,
            }).渲染()#提示
            if 搜泡 is not None:#有
                搜索.appendChild(搜泡)#放入
            输入=文档.createElement('input')#输入
            输入.className='searchInput'#类
            标(输入)#模块
            输入.type='text'#文本
            输入.placeholder=中文['search.placeholder']#占位
            输入.maxLength=搜索上限码元#上限
            输入.value=自身.查询#查询
            输入.tabIndex=0 if 自身.搜索展开 else -1#展开才可聚焦
            自身.搜索输入=输入#记下
            def 改查询(事件):
                '净化后写入并安排搜索'
                自身.查询=净化查询(事件.target.value)#查询
                自身.安排搜索()#搜索
                自身.渲染()#重画
            def 搜索键(事件):
                'Escape 清空并收起'
                if 事件.key!='Escape':#不是
                    return#停
                自身.查询=''#清空
                自身.搜索展开=False#收起
                自身.安排搜索()#停远端
                自身.渲染()#重画
            输入.addEventListener('input',改查询)#输入
            输入.addEventListener('keydown',搜索键)#键
            搜索.appendChild(输入)#放入
            if 自身.搜索展开:#清除
                清=文档.createElement('button')#清除
                清.type='button'#按钮
                清.className='clearButton'#类
                标(清)#模块
                清.setAttribute('aria-label',中文['search.clear'])#无障碍
                def 点清(事件):
                    '清空并收起'
                    事件.stopPropagation()#不停到搜索
                    自身.查询=''#清空
                    自身.搜索展开=False#收起
                    自身.安排搜索()#停
                    自身.渲染()#重画
                清.addEventListener('click',点清)#点击
                关图=画图标(窗口,'close-fill-14')#关闭
                if 关图 is not None:#有
                    清.appendChild(关图)#放入
                搜索.appendChild(清)#放入
            搜索槽.appendChild(搜索)#放入
            头.appendChild(搜索槽)#放入
        动作条=文档.createElement('div')#动作
        动作条.className=拼类('headerActions','headerActionsHidden' if 宽 and 自身.搜索展开 else None)#类
        标(动作条)#模块
        if 宽:#视图选项
            if 自身.视图菜单 is None:#第一次
                自身.视图菜单=视图选项菜单({'window':窗口})#创建
            自身.视图菜单.属性={
                'window':窗口,
                'groupBy':分组,
                'orderBy':排序,
                'archivedFilter':归档筛选,
                'onGroupPick':动作['setGroupBy'],
                'onOrderPick':lambda 模式,顺序=活动顺序: 动作['setOrderBy'](模式,顺序),
                'onArchivedFilterPick':动作['setArchivedFilter'],
            }#属性
            菜单节点=自身.视图菜单.渲染()#菜单
            if 菜单节点 is not None:#有
                动作条.appendChild(菜单节点)#放入
        if 可添加:#添加
            加=文档.createElement('button')#添加
            加.type='button'#按钮
            加.className='iconButton'#类
            标(加)#模块
            加.setAttribute('aria-label',中文['workspace.add'])#无障碍
            if isinstance(添加快捷,dict) and 添加快捷.get('aria'):#快捷键
                加.setAttribute('aria-keyshortcuts',str(添加快捷['aria']))#组合
            自身.加号=加#锚
            def 点加(事件):
                '打开添加'
                属性['requestAddWorkspace']()#请求
            加.addEventListener('click',点加)#点击
            加图=画图标(窗口,'project-add-16',16 if 宽 else 18)#图标
            if 加图 is not None:#有
                加.appendChild(加图)#放入
            加泡=提示泡({
                'window':窗口,'label':中文['workspace.add'],
                'shortcutKeys':添加快捷.get('keys') if isinstance(添加快捷,dict) else None,
                'side':'bottom','delayMs':500,'children':加,
            }).渲染()#提示
            if 加泡 is not None:#有
                动作条.appendChild(加泡)#放入
        头.appendChild(动作条)#放入
        def 画侧栏流(流主):
            '侧栏目录流'
            return 属性['renderSlot']('sidebar.workspaces.directoryFlow',流主)#洞
        def 选了工作区(工作区号):
            '添加后开一个会话，保留已有草稿'
            属性['closeAddWorkspace']()#关掉
            属性['startSession'](工作区号,{'clearPreviousDraft':False})#开始
        流属性={
            'window':窗口,
            't':属性.get('t'),
            'open':快捷状态.get('addRequested') is True,
            'anchorRef':{'current':自身.加号},
            'useWorkspaces':属性['useWorkspaces'],
            'createWorkspace':属性['createWorkspace'],
            'useDirectoryFlow':属性['useDirectoryFlow'],
            'renderDirectoryFlow':画侧栏流,
            'addOnly':True,
            'onBusyChange':属性['setDirectoryBusy'],
            'side':'right',
            'onPick':选了工作区,
            'onClose':属性['closeAddWorkspace'],
        }#流
        if 自身.挑选 is None:#第一次
            自身.挑选=工作区挑选流(流属性)#创建
        else:#更新
            自身.挑选.属性=流属性#更新
        流节点=自身.挑选.渲染()#流
        if 流节点 is not None:#有
            头.appendChild(流节点)#放入
        根.appendChild(头)#放入
        if not 宽:#轨道上的搜索
            轨搜=文档.createElement('div')#搜索
            轨搜.className='search'#类
            标(轨搜)#模块
            轨钮=文档.createElement('button')#按钮
            轨钮.type='button'#按钮
            轨钮.className='searchButton'#类
            标(轨钮)#模块
            轨钮.setAttribute('aria-label',中文['search.sessions.aria'])#无障碍
            def 点轨(事件):
                '展开侧栏并搜索'
                属性['requestSearch']()#请求
            轨钮.addEventListener('click',点轨)#点击
            轨图=画图标(窗口,'search-16',18)#图标
            if 轨图 is not None:#有
                轨钮.appendChild(轨图)#放入
            轨泡=提示泡({'window':窗口,'label':'搜索','shortcutKeys':搜索快捷.get('keys') if isinstance(搜索快捷,dict) else None,'children':轨钮}).渲染()#提示
            if 轨泡 is not None:#有
                轨搜.appendChild(轨泡)#放入
            根.appendChild(轨搜)#放入
        列表区=文档.createElement('div')#列表座
        列表区.className='listArea'#类
        标(列表区)#模块
        if 宽:#宽才有列表
            if 查询!='':#搜索
                列表区.appendChild(自身.画搜索(窗口,列表,工作区列,归档号,归档筛选,查询,属性))#搜索
            elif 分组=='flat':#扁平
                列表区.appendChild(自身.画扁平(窗口,列表,有序扁平,行态,工作区就绪,分组,排序,归档筛选,属性))#扁平
            else:#分组
                列表区.appendChild(自身.画树(
                    窗口,列表,有序工作区,有序未分组,行态,工作区就绪,分组,排序,归档筛选,
                    展开表,新建快捷,家,属性,
                ))#树
        根.appendChild(列表区)#放入
        根.appendChild(自身.画改名(窗口,工作区列,存储工作区,属性))#改名
        根.appendChild(自身.画删除(窗口,工作区列,属性))#删除
        if 自身.展开后搜索 and 宽 and 自身.搜索输入 is not None:#轨道展开完
            def 聚焦():
                '滑动结束后聚焦'
                if 自身.搜索输入 is not None:#还在
                    自身.搜索输入.focus()#聚焦
                自身.展开后搜索=False#用掉
            窗口.setTimeout(聚焦,展开滑动毫秒)#等滑动
        return 换上(自身,根)#节点

    def 安排搜索(自身):
        '停键后再向宿主要内容命中'
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()#窗口
        if 自身.搜索定时 is not None:#旧定时
            窗口.clearTimeout(自身.搜索定时)#清
            自身.搜索定时=None#空
        if 自身.搜索中止 is not None:#旧请求
            自身.搜索中止.abort()#中止
            自身.搜索中止=None#空
        查询=净化查询(自身.查询).strip()#查询
        if 查询=='':#空
            自身.远端={'query':'','status':'idle','items':[],'hasMore':False}#清空
            自身.揭示号=None#不揭示
            return#停
        自身.揭示号=None#搜索时不揭示
        自身.远端={'query':查询,'status':'loading','items':[],'hasMore':False}#加载
        控制器=窗口.AbortController()#中止
        自身.搜索中止=控制器#记下
        def 到时():
            '发出搜索'
            try:#搜索
                结果=取同步结果(自身.属性['searchSessions'](查询,控制器.signal))#结果
                if 控制器.signal.aborted:#已作废
                    return#丢
                自身.远端={'query':查询,'status':'ready','items':结果.get('items') or [],'hasMore':结果.get('hasMore') is True}#就绪
            except Exception:#失败
                if 控制器.signal.aborted:#作废
                    return#丢
                自身.远端={'query':查询,'status':'error','items':[],'hasMore':False}#错误
            自身.渲染()#重画
        自身.搜索定时=窗口.setTimeout(到时,搜索等待毫秒)#等待

    def 守卫打开(自身,会话号):
        '归档的会话不打开，只提示'
        归档=自身.属性['useWorkspaces'](lambda 状态: 状态.get('archivedSessionIds') or [])#归档
        if 会话号 in 归档:#已归档
            自身.属性['notifyArchivedNotOpenable']()#提示
            return#停
        自身.属性['open'](会话号)#打开

    def 打开搜索结果(自身,会话号):
        '归档只提示。否则收起搜索并滚到那一行'
        归档=自身.属性['useWorkspaces'](lambda 状态: 状态.get('archivedSessionIds') or [])#归档
        if 会话号 in 归档:#已归档
            自身.属性['notifyArchivedNotOpenable']()#提示
            return#停
        自身.揭示号=会话号#要滚到
        自身.查询=''#清空
        自身.搜索展开=False#收起
        自身.属性['open'](会话号)#打开
        自身.渲染()#重画

    def 画搜索(自身,窗口,列表,工作区列,归档号,归档筛选,查询,属性):
        '本地命中加上宿主内容页'
        文档=窗口.document#文档
        def 原样(值):
            '原样'
            return 值#原样
        状态表=属性['useSessionStatus'](原样)#状态
        远端=自身.远端 if 自身.远端.get('query')==查询 else {'query':查询,'status':'loading','items':[],'hasMore':False}#对得上的页
        结果=派生检索结果(列表,工作区列,查询,归档号,归档筛选,状态表,远端,属性['searchResultLimit'])#合并
        面板开=属性['usePanelInfo'](lambda 信息: (信息 or {}).get('activePanelId') is not None)#有面板
        当前=None#当前
        if not 面板开:#对话在前
            for 会话 in 列表.get('byId',{}).values():#找
                if ((会话.get('retainedBy') or {}).get('mainView') or 0)>0:#主视图
                    当前=会话['id']#这条
                    break#停
        体=文档.createElement('div')#体
        体.className=拼类('treeBody','wide')#类
        标(体)#模块
        列=文档.createElement('div')#列表
        列.className='list'#类
        标(列)#模块
        树=文档.createElement('div')#树
        树.className='searchTree'#类
        标(树)#模块
        树.setAttribute('role','tree')#树
        树.setAttribute('aria-label',中文['search.results.aria'])#搜索结果
        for 项 in 结果['items']:#逐条
            节点=检索结果行({
                'window':窗口,'result':项,'currentId':当前,
                'onOpen':自身.打开搜索结果,'onUnarchive':自身.恢复搜索,
            }).渲染()#行
            if 节点 is not None:#有
                树.appendChild(节点)#放入
        列.appendChild(树)#放入
        if 远端.get('status')=='loading':#还在搜
            骨=文档.createElement('div')#骨架
            骨.setAttribute('role','status')#状态
            骨.setAttribute('aria-label',中文['search.pending'])#正在搜索
            条数=[0,1] if len(结果['items'])==0 else [0]#空则两行
            for 号 in 条数:#骨架行
                行=文档.createElement('div')#行
                行.className='skeletonRow'#类
                标(行)#模块
                行.setAttribute('aria-hidden','true')#装饰
                点=文档.createElement('span')#点
                点.className='skeletonDot'#类
                标(点)#模块
                条=文档.createElement('span')#条
                条.className='skeletonBars'#类
                标(条)#模块
                短=文档.createElement('span')#短
                短.className='skeletonBar'#类
                标(短)#模块
                长=文档.createElement('span')#长
                长.className=拼类('skeletonBar','skeletonBarWide')#类
                标(长)#模块
                条.appendChild(短)#放入
                条.appendChild(长)#放入
                行.appendChild(点)#放入
                行.appendChild(条)#放入
                骨.appendChild(行)#放入
            列.appendChild(骨)#放入
        if 远端.get('status')!='loading' and len(结果['items'])==0:#没有
            空=文档.createElement('div')#空
            空.className='empty'#类
            标(空)#模块
            空.textContent=中文['search.noMatches']#无匹配
            列.appendChild(空)#放入
        if 结果.get('hasMore'):#还有
            更多=文档.createElement('div')#提示
            更多.className='searchStatus'#类
            标(更多)#模块
            更多.textContent=填入(中文['search.hasMore'],{'n':属性['searchResultLimit']})#收窄
            列.appendChild(更多)#放入
        体.appendChild(列)#放入
        淡=文档.createElement('span')#淡出
        淡.className='fade'#类
        标(淡)#模块
        体.appendChild(淡)#放入
        return 体#节点

    def 恢复搜索(自身,会话号):
        '搜索结果上的恢复。失败只记日志'
        try:#恢复
            取同步结果(自身.属性['unarchiveSession'](会话号))#恢复
        except Exception as 原因:#失败
            print('session unarchive rejected:',原因)#日志

    def 画扁平(自身,窗口,列表,会话号列,行态,就绪,分组,排序,归档筛选,属性):
        '单列表'
        文档=窗口.document#文档
        def 原样(值):
            '原样'
            return 值#原样
        状态表=属性['useSessionStatus'](原样)#状态
        行列表=派生扁平(列表,会话号列,行态,状态表)#行
        面板开=属性['usePanelInfo'](lambda 信息: (信息 or {}).get('activePanelId') is not None)#面板
        当前=None#当前
        if not 面板开:#对话
            for 会话 in 列表.get('byId',{}).values():#找
                if ((会话.get('retainedBy') or {}).get('mainView') or 0)>0:#主
                    当前=会话['id']#这条
                    break#停
        体=文档.createElement('div')#体
        体.className=拼类('treeBody','wide')#类
        标(体)#模块
        键=['empty'] if len(行列表)==0 else ['session:'+行['id'] for 行 in 行列表]#键
        if 自身.动画 is None:#第一次
            自身.动画=动画行({'window':窗口})#创建
        子=[]#行节点
        if len(行列表)==0:#空
            子.append(空会话({'window':窗口,'rowState':行态,'onLeaveArchivedOnly':lambda: 属性['actions']['setArchivedFilter']('default')}).渲染())#空
        现在=属性.get('now')#时间
        if 现在 is None:#没有
            现在=窗口.Date.now() if hasattr(窗口,'Date') else __import__('time').time()*1000#现在
        for 行 in 行列表:#逐行
            节点=会话行({
                'window':窗口,'node':行,'currentId':当前,'now':现在,
                'onOpen':自身.守卫打开,'onRenameRequest':属性['requestSessionRename'],
                'renderSlot':属性['renderSlot'],
                'onReveal':(lambda 号=行['id']: 自身.确认揭示(号)) if 行['id']==自身.揭示号 else None,
            }).渲染()#行
            if 节点 is not None:#有
                子.append(节点)#留下
        自身.动画.属性={
            'window':窗口,
            'className':拼类('list','flatList'),
            'label':中文['section.sessions'],
            'rowKeys':键,
            'ready':列表.get('phase')=='ready' and 就绪 and 自身.会话拖 is None,
            'resetKey':分组+'/'+排序+'/'+归档筛选,
        }#动画
        列=自身.动画.渲染(子)#列表
        if 列 is not None:#有
            体.appendChild(列)#放入
        淡=文档.createElement('span')#淡
        淡.className='fade'#类
        标(淡)#模块
        体.appendChild(淡)#放入
        return 体#节点

    def 确认揭示(自身,会话号):
        '滚到了就清掉揭示'
        if 自身.揭示号==会话号:#是这次
            自身.揭示号=None#清

    def 画树(自身,窗口,列表,工作区列,未分组号,行态,就绪,分组,排序,归档筛选,展开表,新建快捷,家,属性):
        '按工作区或工作区树'
        文档=窗口.document#文档
        def 原样(值):
            '原样'
            return 值#原样
        状态表=属性['useSessionStatus'](原样)#状态
        面板开=属性['usePanelInfo'](lambda 信息: (信息 or {}).get('activePanelId') is not None)#面板
        当前=None#当前
        if not 面板开:#对话
            for 会话 in 列表.get('byId',{}).values():#找
                if ((会话.get('retainedBy') or {}).get('mainView') or 0)>0:#主
                    当前=会话['id']#这条
                    break#停
        嵌套=分组=='workspace-tree'#树
        父表={}#工作区到父
        if 嵌套:#要嵌套
            路径到号={项['path']:项['workspaceId'] for 项 in 工作区列}#路径
            路径列=list(路径到号.keys())#路径
            for 项 in 工作区列:#逐个
                父路径=拥有父文件夹(项['path'],路径列)#父路径
                父表[项['workspaceId']]=None if 父路径 is None else 路径到号.get(父路径)#父
        祖先=set()#当前会话的祖先
        键=None if 当前 is None else 拥有分组键(工作区列,当前)#当前组
        while 键 is not None:#往上
            键=父表.get(键)#父
            if 键 is not None:#有
                祖先.add(键)#记下
        是祖先=set(父表.values())#谁当过父
        展开键=[]#展开的组
        for 项 in list(工作区列)+[{'workspaceId':未分组键}]:#包括未分组
            组键=项['workspaceId']#键
            if 组键 in 展开表:#显式
                if 展开表[组键]:#展开
                    展开键.append(组键)#留下
            elif 组键 in 是祖先:#默认展开有孩子的
                展开键.append(组键)#留下
        组列=派生分组(列表,工作区列,行态,状态表,{'expandedGroups':展开键,'ungroupedOrder':未分组号})#组
        揭示组=None if 自身.揭示号 is None or not 就绪 else 拥有分组键(工作区列,自身.揭示号)#要揭示的组
        所需={}#各组所需水位
        for 组 in 组列:#逐组
            所需[组['key']]=max(水位基数,所需水位(组['sessions'],当前,自身.揭示号 if 组['key']==揭示组 else None))#所需
        抬过=抬水位(自身.水位,所需)#抬
        if 抬过 is not 自身.水位:#变了
            自身.水位=抬过#记下
        子映射={}#父到子组
        已画=set(组['key'] for 组 in 组列)#画得出的
        for 组 in 组列:#挂父
            父=父表.get(组['key'])#父
            while 父 is not None and 父 not in 已画:#父没画出来
                父=父表.get(父)#再上
            子映射.setdefault(父,[]).append(组)#归父
        键列=[]#动画键
        def 画组(组,深度):
            '一组：头、子工作区、会话和展开其余'
            键列.append('workspace:'+str(组['key']))#头
            水位=自身.水位.get(组['key']) or 水位基数#水位
            基线=水位行(组['sessions'],所需.get(组['key']) or 水位基数)#基线
            可见=水位行(组['sessions'],水位)#可见
            展开完=可见['hiddenCount']==0#没有隐藏
            节=文档.createElement('div')#节
            节.className='groupSection'#类
            标(节)#模块
            节.style.setProperty('--dsh-workspace-indent',str(深度*12)+'px')#缩进
            头=项目行({
                'window':窗口,'group':组,'containsCurrentDescendant':组['key'] in 祖先,
                'home':家,'newShortcut':新建快捷,'onToggle':lambda 键=组['key'],展开=组.get('expanded'): 自身.切换组(键,展开),
                'onCreate':lambda 号=组.get('workspaceId'),键=组['key']: 自身.组内新建(号,键),
                'drag':None if 组.get('workspaceId') is None else {'start':lambda 号=组['workspaceId']: 自身.开始拖工作区(号),'end':自身.结束拖工作区},
                'actions':None if 组.get('workspaceId') is None else {
                    'rename':lambda 号=组['workspaceId'],名=组.get('label'): 自身.请求改名(号,名),
                    'delete':lambda 号=组['workspaceId'],名=组.get('label'): 自身.请求删除(号,名),
                },
            }).渲染()#头
            if 头 is not None:#有
                节.appendChild(头)#放入
            if 组.get('expanded'):#展开才画孩子和会话
                for 子 in 子映射.get(组['key']) or []:#子工作区
                    节.appendChild(画组(子,深度+1))#递归
                现在=窗口.Date.now() if hasattr(窗口,'Date') else __import__('time').time()*1000#现在
                for 会话 in 可见['rows']:#会话
                    键列.append('session:'+会话['id'])#键
                    行节点=会话行({
                        'window':窗口,'node':会话,'currentId':当前,'now':现在,
                        'onOpen':自身.守卫打开,'onRenameRequest':属性['requestSessionRename'],
                        'renderSlot':属性['renderSlot'],
                        'onReveal':(lambda 号=会话['id']: 自身.确认揭示(号)) if 会话['id']==自身.揭示号 and 组['key']==揭示组 else None,
                        'drag':自身.会话拖属性(组['key'],会话,自身.活动顺序.get(组['key']) or [],可见['rows']),
                    }).渲染()#行
                    if 行节点 is not None:#有
                        节.appendChild(行节点)#放入
            if 基线['hiddenCount']>0:#还有折叠的
                键列.append('overflow:'+str(组['key']))#键
                钮=文档.createElement('button')#展开其余
                钮.type='button'#按钮
                钮.className='sessionOverflowButton'#类
                标(钮)#模块
                钮.setAttribute('data-row-key','overflow:'+str(组['key']))#键
                钮.setAttribute('aria-expanded','true' if 展开完 else 'false')#展开
                钮.textContent=中文['sessions.collapse'] if 展开完 else 填入(中文['sessions.expand'],{'n':可见['hiddenCount']})#文案
                def 点水位(事件,键=组['key'],完=展开完,隐藏=可见['hiddenCount'],当前水位=水位):
                    '再露一批，或收回自动水位以上的'
                    if 完:#收起
                        if 键 in 自身.水位:#有抬高
                            del 自身.水位[键]#去掉
                        自身.水位动=自身.水位动+1#复位动画
                    else:#展开
                        自身.水位[键]=float('inf') if 隐藏<=水位基数 else 当前水位+水位基数#再一批或全部
                        自身.水位动=自身.水位动+1#复位
                    自身.渲染()#重画
                钮.addEventListener('click',点水位)#点击
                节.appendChild(钮)#放入
            return 节#节
        体=文档.createElement('div')#体
        体.className=拼类('treeBody','wide')#类
        标(体)#模块
        子节点=[]#行
        if len(组列)==0:#空
            键列.append('empty')#空键
            子节点.append(空会话({'window':窗口,'rowState':行态,'onLeaveArchivedOnly':lambda: 属性['actions']['setArchivedFilter']('default')}).渲染())#空
        for 组 in 子映射.get(None) or []:#根
            子节点.append(画组(组,0))#一组
        if 自身.动画 is None:#第一次
            自身.动画=动画行({'window':窗口})#创建
        自身.动画.属性={
            'window':窗口,
            'className':'list',
            'label':中文['section.sessions'],
            'rowKeys':键列 if len(键列)>0 else ['empty'],
            'ready':列表.get('phase')=='ready' and 就绪 and 自身.会话拖 is None and 自身.工作区拖 is None,
            'resetKey':json.dumps([分组+'/'+排序+'/'+归档筛选,自身.水位动],ensure_ascii=False),
        }#动画
        列=自身.动画.渲染(子节点)#列表
        if 列 is not None:#有
            体.appendChild(列)#放入
        淡=文档.createElement('span')#淡
        淡.className='fade'#类
        标(淡)#模块
        体.appendChild(淡)#放入
        return 体#节点

    def 切换组(自身,键,已展开):
        '展开或收起，并在收起时丢掉子组抬高的水位'
        if 已展开:#要收起
            去掉=[项 for 项 in 自身.水位 if 项==键]#这一组
            for 项 in 去掉:#删
                del 自身.水位[项]#去掉
            自身.水位动=自身.水位动+1#复位
        自身.属性['actions']['setGroupExpanded'](键,not 已展开)#写入
        自身.渲染()#重画

    def 组内新建(自身,工作区号,键):
        '先展开再在这个工作区里新建'
        if 工作区号 is None:#未分组
            return#没有新建
        自身.属性['actions']['setGroupExpanded'](键,True)#展开
        自身.属性['startSession'](工作区号)#新建

    def 会话拖属性(自身,组键,会话,账本顺序,行列表):
        '同一组、同一置顶段才能落'
        拖=自身.会话拖#当前拖
        同组=拖 is not None and 拖['accountKey']==组键#同组
        兼容=同组 and 拖['pinned']==会话.get('pinned')#同段
        def 半(值):
            '空白行只能插在下面'
            if 会话.get('blank'):#空白
                return 'after'#下面
            return 值#原样
        def 开始():
            '开始拖这一行'
            自身.会话已放=False#还没放
            自身.会话拖={'accountKey':组键,'sessionId':会话['id'],'pinned':会话.get('pinned'),'over':None}#记下
        def 经过(哪半):
            '更新插入线'
            if 自身.会话拖 is None:#没有
                return#停
            自身.会话拖={**自身.会话拖,'over':{'id':会话['id'],'half':半(哪半)}}#落点
            自身.渲染()#重画
        def 放下(哪半):
            '提交顺序'
            if 自身.会话拖 is None:#没有
                return#停
            自身.提交会话拖(自身.会话拖,{'id':会话['id'],'half':半(哪半)},账本顺序,行列表)#提交
        def 结束():
            '在最后的线上提交，或取消'
            if 自身.会话拖 is not None and 自身.会话拖.get('over') is not None:#有落点
                自身.提交会话拖(自身.会话拖,自身.会话拖['over'],账本顺序,行列表)#提交
            else:#没有
                自身.会话拖=None#取消
                自身.渲染()#重画
            自身.会话已放=False#复位
        return {'start':开始,'active':兼容,'marker':拖['over']['half'] if 同组 and 拖.get('over') is not None and 拖['over']['id']==会话['id'] else None,'hover':经过,'drop':放下,'end':结束}#拖

    def 提交会话拖(自身,拖,落在,账本顺序,行列表):
        '写入手动顺序。藏着的成员仍留在账本里'
        if 自身.会话已放:#已经处理
            return#停
        自身.会话已放=True#处理过
        自身.会话拖=None#结束
        下一=会话拖顺序(账本顺序 or [],行列表 or [],拖,落在)#新顺序
        if 下一 is not None:#位置变了
            自身.属性['actions']['setSessionOrder'](拖['accountKey'],下一,自身.活动顺序)#写入
        自身.渲染()#重画

    def 开始拖工作区(自身,工作区号):
        '开始拖一个工作区'
        自身.工作区已放=False#还没放
        自身.工作区拖={'workspaceId':工作区号,'over':None}#记下

    def 结束拖工作区(自身):
        '没有落点就取消'
        自身.工作区拖=None#取消
        自身.工作区已放=False#复位
        自身.渲染()#重画

    def 请求改名(自身,工作区号,显示名):
        '对话框用屏幕上的名字做草稿，冲突按存储标题判断'
        存储=自身.属性['useWorkspaces'](lambda 状态: 状态.get('items') or [])#存储
        存名=显示名#默认
        for 项 in 存储:#找
            if 项.get('workspaceId')==工作区号:#是它
                存名=项.get('title') or 显示名#存储标题
                break#停
        自身.改名目标={'workspaceId':工作区号,'storedTitle':存名}#目标
        自身.改名草稿=显示名 or ''#草稿
        自身.改名错误=None#清
        自身.渲染()#重画

    def 请求删除(自身,工作区号,名称):
        '打开删除确认'
        自身.删除目标={'workspaceId':工作区号,'title':名称}#目标
        自身.删除错误=None#清
        自身.渲染()#重画

    def 画改名(自身,窗口,工作区列,存储工作区,属性):
        '工作区改名。和自己以外的显示名冲突就挡住'
        文档=窗口.document#文档
        目标=自身.改名目标#目标
        剪=自身.改名草稿.strip()#去空白
        重复=False#冲突
        if 目标 is not None and 剪!='':#有草稿
            for 项 in 工作区列:#显示名
                if 项['workspaceId']!=目标['workspaceId'] and 项.get('title')==剪:#别的工作区同名
                    重复=True#冲突
                    break#停
        挡住=自身.正在改名 or 剪=='' or 目标 is None or (目标 is not None and 剪==目标.get('storedTitle')) or 重复#不能提交
        def 关掉():
            '进行中不关'
            if 自身.正在改名:#进行中
                return#不关
            自身.改名目标=None#清
            自身.改名错误=None#清
            自身.渲染()#重画
        def 确认():
            '提交存储用的标题'
            if 挡住 or 目标 is None:#不能
                return#停
            自身.正在改名=True#进行中
            自身.改名错误=None#清
            自身.渲染()#重画
            try:#改名
                取同步结果(属性['renameWorkspace'](目标['workspaceId'],剪))#改名
                自身.正在改名=False#结束
                自身.改名目标=None#关掉
            except Exception as 原因:#失败
                自身.正在改名=False#结束
                自身.改名错误=原因.args[0] if isinstance(原因,BaseException) and len(原因.args)>0 else str(原因)#说明
            自身.渲染()#重画
        输入=文档.createElement('input')#名称
        输入.className='renameInput'#类
        标(输入)#模块
        输入.value=自身.改名草稿#草稿
        输入.setAttribute('aria-label',中文['field.workspaceName'])#名称
        输入.setAttribute('data-modal-autofocus','')#聚焦
        输入.disabled=自身.正在改名#进行中
        def 聚焦(事件):
            '选中全文'
            事件.target.select()#选中
        def 改(事件):
            '写草稿'
            自身.改名草稿=事件.target.value#草稿
            自身.改名错误=None#清
            自身.渲染()#重画
        def 组合开始(事件):
            '输入法组合'
            自身.改名组合=True#组合
        def 组合结束(事件):
            '组合结束'
            自身.改名组合=False#结束
        def 键(事件):
            '回车提交'
            if 事件.key=='Enter' and not 自身.改名组合:#提交
                事件.preventDefault()#不换行
                确认()#提交
        输入.addEventListener('focus',聚焦)#聚焦
        输入.addEventListener('input',改)#输入
        输入.addEventListener('compositionstart',组合开始)#组合
        输入.addEventListener('compositionend',组合结束)#结束
        输入.addEventListener('keydown',键)#键
        体=文档.createElement('div')#正文
        体.appendChild(输入)#输入
        if 重复:#冲突
            警=文档.createElement('div')#冲突
            警.className='renameError'#类
            标(警)#模块
            警.setAttribute('role','alert')#提示
            警.textContent=填入(中文['conflict.named'],{'name':剪})#已存在
            体.appendChild(警)#放入
        if 自身.改名错误 is not None:#失败
            败=文档.createElement('div')#错误
            败.className='renameError'#类
            标(败)#模块
            败.setAttribute('role','alert')#提示
            败.textContent=自身.改名错误#说明
            体.appendChild(败)#放入
        取消钮=按钮({'window':窗口,'variant':'outline','disabled':自身.正在改名,'onClick':关掉,'children':取消})#取消
        确认钮=按钮({'window':窗口,'variant':'primary','disabled':挡住,'onClick':确认,'children':中文['rename']})#重命名
        框=模态({
            'window':窗口,'open':目标 is not None,'onClose':关掉,'closeLabel':关闭,
            'title':中文['rename.workspace.title'],'footer':[取消钮,确认钮],'children':体,
        }).渲染()#框
        盒=文档.createElement('div')#盒
        if 框 is not None:#开着
            盒.appendChild(框)#放入
        return 盒#节点

    def 画删除(自身,窗口,工作区列,属性):
        '删除只去掉登记。列表里真的没有了才关掉'
        文档=窗口.document#文档
        目标=自身.删除目标#目标
        if 自身.已提交删除 is not None:#等消失
            还在=False#还在吗
            for 项 in 工作区列:#找
                if 项.get('workspaceId')==自身.已提交删除:#还在
                    还在=True#在
                    break#停
            if not 还在:#已经没了
                自身.正在删除=False#结束
                自身.已提交删除=None#清
                自身.删除目标=None#关
                目标=None#不再画
        def 关掉():
            '进行中不关'
            if 自身.正在删除:#进行中
                return#不关
            自身.删除目标=None#清
            自身.删除错误=None#清
            自身.渲染()#重画
        def 确认():
            '删除登记'
            if 自身.正在删除 or 目标 is None:#不能
                return#停
            自身.正在删除=True#进行中
            自身.已提交删除=None#还没提交完
            自身.删除错误=None#清
            自身.渲染()#重画
            try:#删除
                取同步结果(属性['deleteWorkspace'](目标['workspaceId']))#删除
                自身.已提交删除=目标['workspaceId']#等列表
            except Exception as 原因:#失败
                自身.正在删除=False#结束
                自身.删除错误=原因.args[0] if isinstance(原因,BaseException) and len(原因.args)>0 else str(原因)#说明
            自身.渲染()#重画
        体=文档.createElement('div')#正文
        if 自身.正在删除:#进行中
            状=文档.createElement('div')#状态
            状.className='deleteStatus'#类
            标(状)#模块
            状.setAttribute('role','status')#状态
            状.textContent=中文['delete.pending']#正在删除
            体.appendChild(状)#放入
        if 自身.删除错误 is not None:#失败
            警=文档.createElement('div')#错误
            警.className='renameError'#类
            标(警)#模块
            警.setAttribute('role','alert')#提示
            警.textContent=自身.删除错误#说明
            体.appendChild(警)#放入
        取消钮=按钮({'window':窗口,'variant':'outline','disabled':自身.正在删除,'onClick':关掉,'children':取消})#取消
        确认钮=按钮({
            'window':窗口,'variant':'outline','className':'deleteAction','disabled':自身.正在删除,
            'onClick':确认,'children':中文['delete.workspace'],
        })#删除
        说明=None if 目标 is None else 填入(中文['delete.desc'],{'name':目标.get('title') or ''})#说明
        框属性={
            'window':窗口,'open':目标 is not None,'onClose':关掉,'closeLabel':关闭,
            'title':中文['delete.workspace'],'footer':[取消钮,确认钮],'children':体,
        }#框
        if 说明 is not None:#有说明
            框属性['description']=说明#说明
        框=模态(框属性).渲染()#框
        盒=文档.createElement('div')#盒
        if 框 is not None:#开着
            盒.appendChild(框)#放入
        return 盒#节点

def 工作区浏览区组件(属性):
    '侧栏这一份浏览区只留一个实例'
    if not hasattr(工作区浏览区组件,'实例'):#第一次
        工作区浏览区组件.实例=工作区浏览区(属性)#创建
    else:#再来
        工作区浏览区组件.实例.属性=属性#更新
    return 工作区浏览区组件.实例.渲染()#节点
