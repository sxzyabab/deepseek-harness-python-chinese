'工作区行和会话行。悬停换图标由样式做，标题超出时在悬停期间滚动'
from ....模块.客户端.通告 import 取握手窗口
import os
from datetime import datetime
from ....ui_对话.异常 import 注入模块样式文件,标样式模块
from ....ui_基础界面组件.提示泡 import 提示泡
from ....ui_基础界面组件.悬停卡 import 悬停卡
from ....ui_基础界面组件.状态点 import 状态点
from ....ui_基础界面组件.菜单 import 菜单
from ....ui_基础界面组件.相对时间 import 相对时间
from ....ui_基础界面组件.icons import 图标
from .....工具.工作区路径 import 缩写家目录路径
from ..会话动作.派生 import 换上
from ..文案 import 中文,填入,复制

__all__=['项目行','检索结果行','会话行','会话状态列','行半','项目行组件','检索结果行组件','会话行组件']

样式模块='rows'#行样式模块
最小露出=8#小于这个溢出不滚动
每毫秒像素=0.03#滚动速度

def 确保样式(文档):
    '行样式只插一次'
    注入模块样式文件(文档,'工作区行样式',os.path.join(os.path.dirname(__file__),'行.module.css'),样式模块)

def 画图标(窗口,名,尺寸=None,类名=None):
    '按图标表画'
    属性={'window':窗口}#窗口
    if 尺寸 is not None:#边长
        属性['size']=尺寸#边长
    if 类名:#类
        属性['className']=类名#类
    return 图标(名,属性)#图标

def 拼类(*段):
    '丢掉空的类名'
    留下=[]#类
    for 项 in 段:#逐段
        if 项 is None or 项 is False or 项=='':#空
            continue#跳过
        留下.append(str(项))#留下
    return ' '.join(留下)#拼

def 标(节点):
    '挂上样式模块'
    if 节点 is not None:#有
        标样式模块(节点,样式模块)#模块
    return 节点#节点

def 展示标题(节点):
    '空白行显示新会话，空标题显示未命名'
    if 节点.get('blank'):#空白
        return 中文['session.new']#新会话
    if 节点.get('title'):#有标题
        return 节点['title']#标题
    return 中文['session.untitled']#未命名

def 时间标签(更新于,现在):
    '刚刚，或几分钟、小时、天'
    桶=相对时间(更新于,现在)#桶
    if 桶['unit']=='now':#刚刚
        return 中文['time.now']#刚刚
    表={'minutes':中文['time.minutes'],'hours':中文['time.hours'],'days':中文['time.days'],'months':中文['time.months'],'years':中文['time.years']}#模板
    return 填入(表[桶['unit']],{'n':桶['n']})#填数

def 悬停时间(更新于,现在):
    '悬停卡上的相对时间，刚刚不加“前”'
    内=时间标签(更新于,现在)#内文
    桶=相对时间(更新于,现在)#桶
    if 桶['unit']=='now':#刚刚
        return 内#不加前
    return 填入(中文['time.ago'],{'t':内})#几分钟前

def 会话状态列(节点):
    '待处理优先，然后是进行中，再是完成，最后是空闲'
    子数=节点.get('runningSubagentCount') or 0#子代
    子状态=None#子代状态
    if 子数!=0:#有子代在跑
        键='status.subagentsRunning.one' if 子数==1 else 'status.subagentsRunning.other'#单复数
        子状态={'state':'ongoing','label':填入(中文[键],{'n':子数})}#状态
    待处理=None#待处理
    种类=节点.get('pendingInteraction')#种类
    if 种类=='approval':#审批
        待处理={'state':'warning','label':中文['status.waitingApproval'],'trailingLabel':中文['status.compact.approval']}#审批
    elif 种类=='plan-review':#计划
        待处理={'state':'warning','label':中文['status.planReview'],'trailingLabel':中文['status.compact.planReview']}#计划
    elif 种类=='question':#提问
        待处理={'state':'warning','label':中文['status.waitingAnswer'],'trailingLabel':中文['status.compact.answer']}#提问
    elif 种类 is not None:#不认识
        raise RuntimeError('unknown pending interaction: '+str(种类))#封闭
    if 待处理 is not None:#有待处理
        if 子状态 is None:#没有子代
            return [待处理]#只这一条
        return [待处理,子状态]#两条
    if 节点.get('running'):#在跑
        主={'state':'ongoing','label':中文['status.running']}#进行中
        if 子状态 is None:#没有子代
            return [主]#一条
        return [主,子状态]#两条
    if 子状态 is not None:#只有子代
        return [子状态]#子代
    if 节点.get('completed'):#完成未读
        return [{'state':'done','label':中文['status.completed']}]#已完成
    return [{'state':'idle','label':中文['status.idle']}]#空闲

def 行半(事件):
    '指针在行的上半还是下半'
    矩形=事件.currentTarget.getBoundingClientRect()#矩形
    if 事件.clientY<矩形.top+矩形.height/2:#上半
        return 'before'#上面
    return 'after'#下面

def 放标题(标题,左,范围):
    '滚动并标出左右是否还要淡出'
    if hasattr(标题,'scrollTo'):#能滚
        标题.scrollTo({'left':左,'behavior':'instant'})#滚
    else:#没有
        标题.scrollLeft=左#直接
    if 左>0:#离开起点
        标题.dataset.scrolled=''#左淡
    elif hasattr(标题.dataset,'scrolled'):#回到起点
        del 标题.dataset.scrolled#去掉
    if 左<范围:#右边还有
        标题.dataset.clipped=''#右淡
    elif hasattr(标题.dataset,'clipped'):#到头了
        del 标题.dataset.clipped#去掉

def 标题回位(标题):
    '回到起点并去掉淡出'
    if hasattr(标题,'scrollTo'):#能滚
        标题.scrollTo({'left':0,'behavior':'instant'})#回
    else:#没有
        标题.scrollLeft=0#直接
    if hasattr(标题.dataset,'scrolled'):#有
        del 标题.dataset.scrolled#去掉
    if hasattr(标题.dataset,'clipped'):#有
        del 标题.dataset.clipped#去掉

def 挂槽(父,产出):
    '槽位节点挂进去'
    if 产出 is None:#空
        return#不挂
    if isinstance(产出,dict):#包装
        if 'items' in 产出:#列表
            挂槽(父,产出['items'])#多项
            return#完
        for 键 in ('content','body'):#单节点
            if hasattr(产出.get(键),'tagName'):#节点
                父.appendChild(产出[键])#挂
                return#完
        return#没有
    if isinstance(产出,(list,tuple)):#多项
        for 项 in 产出:#逐项
            挂槽(父,项)#挂
        return#完
    if hasattr(产出,'tagName'):#节点
        父.appendChild(产出)#挂

class 状态点组:
    '主状态点，其余状态只给读屏'
    def __init__(自身,属性):
        '记下状态'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '第一态画点，每条状态一个隐藏标签'
        属性=自身.属性#属性
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        根=文档.createElement('span')#组
        状态列=属性['statuses']#状态
        点=状态点({'window':窗口,'state':状态列[0]['state']})#点
        点节点=点.渲染()#画
        if 点节点 is not None:#有
            根.appendChild(点节点)#放入
        for 状态 in 状态列:#每条
            隐=文档.createElement('span')#读屏
            隐.className='visuallyHidden'#上游类名
            标(隐)#模块
            隐.textContent=状态['label']#标签
            根.appendChild(隐)#放入
        return 换上(自身,根)#节点

class 项目行:
    '工作区头。未分组没有悬停卡，也没有菜单'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.菜单开=False#菜单
        自身.根=None#节点

    def 渲染(自身):
        '文件夹、标题、新建和菜单'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        组=属性['group']#组
        标签=中文['group.ungrouped'] if 组.get('workspaceId') is None else 组.get('label') or ''#标签
        活动=属性.get('containsCurrentDescendant') or (组.get('expanded') and 组.get('containsCurrent'))#高亮
        行=文档.createElement('div')#行
        行.className=拼类('projectRow','menuOpen' if 自身.菜单开 else None)#类
        标(行)#模块
        行.setAttribute('data-row-key','workspace:'+str(组.get('key')))#键
        行.setAttribute('role','treeitem')#树项
        行.setAttribute('aria-expanded','true' if 组.get('expanded') else 'false')#展开
        def 点行(事件):
            '展开或收起'
            属性['onToggle']()#切换
        行.addEventListener('click',点行)#点击
        拖=属性.get('drag')#拖
        if 拖 is not None:#可拖
            行.draggable=True#可拖
            def 拖开始(事件):
                '开始拖工作区'
                事件.dataTransfer.effectAllowed='move'#移动
                事件.dataTransfer.setData('text/plain',组.get('key') or '')#键
                拖['start']()#开始
            def 拖结束(事件):
                '结束'
                拖['end']()#结束
            行.addEventListener('dragstart',拖开始)#开始
            行.addEventListener('dragend',拖结束)#结束
        夹=文档.createElement('span')#文件夹槽
        夹.className=拼类('slot','folder','folderActive' if 活动 else None)#类
        标(夹)#模块
        夹图=画图标(窗口,'folder-open-16' if 组.get('expanded') else 'folder-close-16')#文件夹
        if 夹图 is not None:#有
            夹.appendChild(夹图)#放入
        行.appendChild(夹)#放入
        箭槽=文档.createElement('span')#箭头槽
        箭槽.className=拼类('slot','chevron')#类
        标(箭槽)#模块
        箭=画图标(窗口,'triangle-right-14',None,拼类('arrow','arrowOpen' if 组.get('expanded') else None))#箭头
        if 箭 is not None:#有
            标(箭)#模块
            箭槽.appendChild(箭)#放入
        行.appendChild(箭槽)#放入
        字盒=文档.createElement('span')#文字
        字盒.className='projectText'#类
        标(字盒)#模块
        题=文档.createElement('span')#标题
        题.className='title'#类
        标(题)#模块
        题.textContent=标签#标题
        字盒.appendChild(题)#放入
        行.appendChild(字盒)#放入
        动作=文档.createElement('span')#动作
        动作.className='rowActions'#类
        标(动作)#模块
        菜单动作=属性.get('actions')#重命名和删除
        if 菜单动作 is not None:#真实工作区
            def 关菜单():
                '关掉'
                自身.菜单开=False#关
                自身.渲染()#重画
            def 选菜单(标识):
                '只认重命名和删除'
                自身.菜单开=False#关
                if 标识=='rename':#重命名
                    菜单动作['rename']()#重命名
                elif 标识=='delete':#删除
                    菜单动作['delete']()#删除
                自身.渲染()#重画
            锚=文档.createElement('button')#省略
            锚.type='button'#按钮
            锚.className='iconButton'#类
            标(锚)#模块
            锚.setAttribute('aria-label',填入(中文['actions.workspace.aria'],{'name':标签}))#无障碍
            def 点锚(事件):
                '不触发行的展开'
                事件.stopPropagation()#停
                自身.菜单开=not 自身.菜单开#切换
                自身.渲染()#重画
            锚.addEventListener('click',点锚)#点击
            省略=画图标(窗口,'ellipsis-16')#省略
            if 省略 is not None:#有
                锚.appendChild(省略)#放入
            菜单节点=菜单({
                'window':窗口,
                'open':自身.菜单开,
                'onClose':关菜单,
                'items':[
                    {'id':'rename','label':中文['rename'],'icon':画图标(窗口,'edit-16')},
                    {'id':'delete','label':中文['delete.workspace'],'icon':画图标(窗口,'trash-16'),'danger':True},
                ],
                'onSelect':选菜单,
                'portal':True,
                'closeOnPointerLeave':True,
                'anchor':锚,
            }).渲染()#菜单
            if 菜单节点 is not None:#有
                动作.appendChild(菜单节点)#放入
        快捷=属性.get('newShortcut')#新建快捷键
        新建=文档.createElement('button')#新建
        新建.type='button'#按钮
        新建.className='iconButton'#类
        标(新建)#模块
        if isinstance(快捷,dict) and 快捷.get('aria'):#无障碍
            新建.setAttribute('aria-keyshortcuts',str(快捷['aria']))#快捷键
        新建.setAttribute('aria-label',填入(中文['actions.newSession.aria'],{'name':标签}))#无障碍
        def 点新建(事件):
            '不触发展开'
            事件.stopPropagation()#停
            属性['onCreate']()#新建
        新建.addEventListener('click',点新建)#点击
        聊=画图标(窗口,'new-chat-16')#新建
        if 聊 is not None:#有
            新建.appendChild(聊)#放入
        泡=提示泡({
            'window':窗口,
            'label':中文['actions.newSession'],
            'shortcutKeys':快捷.get('keys') if isinstance(快捷,dict) else None,
            'side':'bottom',
            'align':'end',
            'delayMs':500,
            'portal':True,
            'children':新建,
        }).渲染()#提示
        if 泡 is not None:#有
            动作.appendChild(泡)#放入
        行.appendChild(动作)#放入
        if 组.get('createdAt') is None:#未分组
            return 换上(自身,行)#没有卡
        目录=组.get('cwd')#目录
        家=属性.get('home')#家目录
        展示目录=目录 if 目录 is None else 缩写家目录路径(目录,家)#缩写
        时刻=datetime.fromtimestamp(组['createdAt']/1000)#本地时间
        日期=填入(中文['date.ymd'],{'y':时刻.year,'m':时刻.month,'d':时刻.day})#日期
        钟=str(时刻.hour).zfill(2)+':'+str(时刻.minute).zfill(2)#时刻
        卡体=文档.createElement('div')#卡
        卡体.className='hoverContent'#类
        标(卡体)#模块
        卡题=文档.createElement('div')#标题
        卡题.className='hoverTitle'#类
        标(卡题)#模块
        卡题.textContent=组.get('label') or ''#标题
        卡路径=文档.createElement('div')#路径
        卡路径.className='hoverPath'#类
        标(卡路径)#模块
        卡路径.textContent='' if 展示目录 is None else str(展示目录)#路径
        卡时=文档.createElement('div')#时间
        卡时.className='hoverTime'#类
        标(卡时)#模块
        卡时.textContent=填入(中文['hover.created'],{'time':日期+' '+钟})#创建于
        卡体.appendChild(卡题)#放入
        卡体.appendChild(卡路径)#放入
        卡体.appendChild(卡时)#放入
        卡=悬停卡({
            'window':窗口,
            'anchor':行,
            'content':卡体,
            'openDelayMs':800,
            'grouped':True,
            'disabled':自身.菜单开,
            'copyText':组.get('cwd'),
            'copyLabel':复制,
            'copiedLabel':中文['hover.copied'],
        }).渲染()#卡
        return 换上(自身,卡)#节点

class 检索结果行:
    '一条搜索结果。归档的行带恢复按钮，点击只说明不能打开'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '标题、工作区和摘录'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        结果=属性['result']#结果
        选中=结果['id']==属性.get('currentId')#选中
        状态列=会话状态列(结果)#状态
        行=文档.createElement('div')#行
        行.className=拼类('searchResultRow','selected' if 选中 else None,'archived' if 结果.get('archived') else None)#类
        标(行)#模块
        行.setAttribute('role','treeitem')#树项
        行.setAttribute('aria-selected','true' if 选中 else 'false')#选中
        if 结果.get('archived'):#归档
            行.setAttribute('aria-description',中文['toast.archivedNotOpenable'])#不能打开
        def 点行(事件):
            '打开'
            属性['onOpen'](结果['id'])#打开
        行.addEventListener('click',点行)#点击
        头=文档.createElement('span')#头
        头.className='searchResultHeading'#类
        标(头)#模块
        槽=文档.createElement('span')#状态槽
        槽.className='slot'#类
        标(槽)#模块
        if not 结果.get('archived') and 状态列[0]['state']!='idle':#要画点
            槽.appendChild(状态点组({'window':窗口,'statuses':状态列}).渲染())#点
        头.appendChild(槽)#放入
        题=文档.createElement('span')#标题
        题.className='searchResultTitle'#类
        标(题)#模块
        题.textContent=结果.get('title') or 中文['session.untitled']#标题
        头.appendChild(题)#放入
        if 结果.get('archived'):#恢复
            动作=文档.createElement('span')#动作
            动作.className='rowActions'#类
            标(动作)#模块
            钮=文档.createElement('button')#恢复
            钮.type='button'#按钮
            钮.className='iconButton'#类
            标(钮)#模块
            钮.setAttribute('aria-label',中文['menu.unarchiveSession'])#无障碍
            def 点恢复(事件):
                '不打开行'
                事件.stopPropagation()#停
                属性['onUnarchive'](结果['id'])#恢复
            钮.addEventListener('click',点恢复)#点击
            图=画图标(窗口,'unarchive-16',14)#图标
            if 图 is not None:#有
                钮.appendChild(图)#放入
            泡=提示泡({'window':窗口,'label':中文['actions.unarchive'],'side':'bottom','align':'end','delayMs':500,'portal':True,'children':钮}).渲染()#提示
            if 泡 is not None:#有
                动作.appendChild(泡)#放入
            头.appendChild(动作)#放入
        行.appendChild(头)#放入
        元=文档.createElement('span')#元
        元.className='searchResultMeta'#类
        标(元)#模块
        区=文档.createElement('span')#工作区
        区.className='searchResultWorkspace'#类
        标(区)#模块
        区.textContent=结果.get('workspace') or 中文['group.ungrouped']#工作区
        元.appendChild(区)#放入
        if 结果.get('snippet') is not None:#有摘录
            摘=文档.createElement('span')#摘录
            摘.className='searchResultSnippet'#类
            标(摘)#模块
            摘.textContent=str(结果.get('snippet'))#摘录
            元.appendChild(摘)#放入
        行.appendChild(元)#放入
        return 换上(自身,行)#节点

class 会话行:
    '32 像素的会话行。空白行不显示时间和动作'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.菜单开=False#菜单
        自身.帧=0#滚动帧
        自身.标题节点=None#标题
        自身.根=None#节点

    def 进入标题(自身):
        '超出才滚动。减少动效时直接到尽头'
        标题=自身.标题节点#标题
        if 标题 is None:#没有
            return#停
        范围=标题.scrollWidth-标题.clientWidth#溢出
        if 范围<=最小露出:#太小
            return#不动
        窗口=标题.ownerDocument.defaultView#窗口
        if 窗口.matchMedia('(prefers-reduced-motion: reduce)').matches:#减少动效
            放标题(标题,范围,范围)#直接到头
            return#停
        窗口.cancelAnimationFrame(自身.帧)#停旧的
        先前=[None]#上一帧时间
        位置=[0]#当前位置
        def 步(现在):
            '按固定速度往尽头滚'
            增量=0 if 先前[0] is None else (现在-先前[0])*每毫秒像素#这一帧
            先前[0]=现在#记下
            位置[0]=位置[0]+增量#前进
            放标题(标题,min(位置[0],范围),范围)#放
            if 位置[0]<范围:#还没到
                自身.帧=窗口.requestAnimationFrame(步)#下一帧
        自身.帧=窗口.requestAnimationFrame(步)#开始

    def 离开标题(自身):
        '立刻回到起点'
        标题=自身.标题节点#标题
        if 标题 is None:#没有
            return#停
        窗口=标题.ownerDocument.defaultView#窗口
        窗口.cancelAnimationFrame(自身.帧)#停
        标题回位(标题)#回位

    def 渲染(自身):
        '状态、标题、时间和菜单'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        节点=属性['node']#会话
        标题文=展示标题(节点)#标题
        选中=节点['id']==属性.get('currentId')#选中
        状态列=会话状态列(节点)#状态
        主态=状态列[0]#主状态
        显示状态=主态['state']!='idle'#非空闲
        拖=属性.get('drag')#拖
        可拖=拖 is not None and not 节点.get('blank') and not 节点.get('archived')#可拖
        标记=None if 拖 is None else 拖.get('marker')#插入线
        行=文档.createElement('div')#行
        行.className=拼类(
            'sessionRow',
            'selected' if 选中 else None,
            'menuOpen' if 自身.菜单开 else None,
            'archived' if 节点.get('archived') else None,
            'dropBefore' if 标记=='before' else None,
            'dropAfter' if 标记=='after' else None,
        )#类
        标(行)#模块
        行.setAttribute('data-row-key','session:'+str(节点['id']))#键
        行.setAttribute('role','treeitem')#树项
        行.setAttribute('aria-selected','true' if 选中 else 'false')#选中
        if 节点.get('archived'):#归档
            行.setAttribute('aria-description',中文['toast.archivedNotOpenable'])#不能打开
        def 点行(事件):
            '打开'
            属性['onOpen'](节点['id'])#打开
        行.addEventListener('click',点行)#点击
        def 指针进入(事件):
            '悬停时滚动标题'
            自身.进入标题()#滚动
        def 指针离开(事件):
            '离开时标题回位'
            自身.离开标题()#回位
        行.addEventListener('pointerenter',指针进入)#进入滚动
        行.addEventListener('pointerleave',指针离开)#离开回位
        if 可拖:#可拖
            行.draggable=True#可拖
            def 拖开始(事件):
                '开始拖会话'
                事件.dataTransfer.effectAllowed='move'#移动
                事件.dataTransfer.setData('text/plain',节点['id'])#号
                拖['start']()#开始
            行.addEventListener('dragstart',拖开始)#开始
            def 拖结束(事件):
                '结束拖会话'
                拖['end']()#结束
            行.addEventListener('dragend',拖结束)#结束
        if 拖 is not None:#可作落点
            def 经过(事件):
                '报告指针在上半还是下半'
                if not 拖.get('active'):#不是兼容拖
                    return#不接
                事件.preventDefault()#允许放
                事件.dataTransfer.dropEffect='move'#移动
                拖['hover'](行半(事件))#半
            def 放下(事件):
                '放下'
                if not 拖.get('active'):#不兼容
                    return#不接
                事件.preventDefault()#接住
                拖['drop'](行半(事件))#放
            行.addEventListener('dragover',经过)#经过
            行.addEventListener('drop',放下)#放下
        槽=文档.createElement('span')#前槽
        槽.className='slot'#类
        标(槽)#模块
        if not 节点.get('archived') and not 节点.get('blank'):#要标记
            if 显示状态:#状态点
                槽.appendChild(状态点组({'window':窗口,'statuses':状态列}).渲染())#点
            else:#空闲才放前导槽
                挂槽(槽,属性['renderSlot']('sidebar.session.row.leading',{'sessionId':节点['id']}))#前导
        行.appendChild(槽)#放入
        题=文档.createElement('span')#标题
        题.className='title'#类
        标(题)#模块
        题.textContent=标题文#标题
        自身.标题节点=题#留给滚动
        if not 节点.get('blank'):#可改名
            def 双击(事件):
                '双击标题打开改名'
                事件.stopPropagation()#停
                属性['onRenameRequest'](节点['id'],节点.get('title') or '')#请求
            题.addEventListener('dblclick',双击)#双击
        行.appendChild(题)#放入
        if not 节点.get('blank'):#有时间和动作
            时=文档.createElement('span')#时间
            时.className='time'#类
            标(时)#模块
            if 主态.get('trailingLabel') is not None:#紧凑状态
                时.setAttribute('aria-hidden','true')#读屏用点
                时.textContent=主态['trailingLabel']#紧凑
            else:#相对时间
                时.textContent=时间标签(节点['updatedAt'],属性['now'])#时间
            行.appendChild(时)#放入
        if 节点.get('pinned') and not 节点.get('archived'):#置顶标记
            钉=文档.createElement('span')#标记
            钉.className='pinIndicator'#类
            标(钉)#模块
            钉.setAttribute('role','img')#图
            钉.setAttribute('aria-label',中文['row.pinned'])#已置顶
            钉.setAttribute('title',中文['row.pinned'])#已置顶
            钉图=画图标(窗口,'pin-fill-16',14)#图钉
            if 钉图 is not None:#有
                钉.appendChild(钉图)#放入
            行.appendChild(钉)#放入
        if not 节点.get('blank'):#动作
            动作=文档.createElement('span')#动作
            动作.className='rowActions'#类
            标(动作)#模块
            def 点动作(事件):
                '不打开行'
                事件.stopPropagation()#停
            动作.addEventListener('click',点动作)#停
            def 关菜单():
                '关掉菜单'
                自身.菜单开=False#关
                自身.渲染()#重画
            锚=文档.createElement('button')#省略
            锚.type='button'#按钮
            锚.className='iconButton'#类
            标(锚)#模块
            锚.setAttribute('aria-label',填入(中文['actions.session.aria'],{'name':标题文}))#无障碍
            def 点锚(事件):
                '切换菜单'
                自身.菜单开=not 自身.菜单开#切换
                自身.渲染()#重画
            锚.addEventListener('click',点锚)#点击
            省略=画图标(窗口,'ellipsis-16')#省略
            if 省略 is not None:#有
                锚.appendChild(省略)#放入
            菜单节点=菜单({
                'window':窗口,
                'open':自身.菜单开,
                'onClose':关菜单,
                'portal':True,
                'closeOnPointerLeave':True,
                'anchor':锚,
            }).渲染()#菜单
            if 菜单节点 is not None:#有
                列=菜单节点.querySelector('[role="menu"]')#列表
                def 设开(开):
                    '菜单项要求打开或关掉'
                    自身.设菜单(开)#写入
                子=属性['renderSlot'](
                    'sidebar.workspaces.session.menu.item',
                    {'sessionId':节点['id'],'displayTitle':节点.get('title') or ''},
                    {'hookContext':(自身.菜单开,设开)},
                )#菜单项
                if 列 is not None:#菜单收下了列表
                    挂槽(列,子)#放进行里
                else:#没有列表就跟在菜单后
                    盒=文档.createElement('div')#盒
                    挂槽(盒,子)#放入
                    菜单节点.appendChild(盒)#挂上
                动作.appendChild(菜单节点)#放入
            行动作=文档.createElement('span')#行按钮
            挂槽(行动作,属性['renderSlot']('sidebar.workspaces.session.row.action',{'sessionId':节点['id'],'displayTitle':节点.get('title') or ''}))#按钮
            动作.appendChild(行动作)#放入
            行.appendChild(动作)#放入
        if 属性.get('onReveal') is not None:#要滚进视口
            行.scrollIntoView({'block':'nearest'})#滚
            属性['onReveal']()#确认
        卡体=文档.createElement('div')#悬停体
        卡体.className='hoverContent'#类
        标(卡体)#模块
        卡题=文档.createElement('div')#标题
        卡题.className='hoverTitle'#类
        标(卡题)#模块
        卡题.textContent=标题文#标题
        卡体.appendChild(卡题)#放入
        if not 节点.get('blank'):#有时间
            卡时=文档.createElement('div')#时间
            卡时.className='hoverTime'#类
            标(卡时)#模块
            卡时.textContent=悬停时间(节点['updatedAt'],属性['now'])#时间
            卡体.appendChild(卡时)#放入
        悬停槽=文档.createElement('div')#悬停槽
        挂槽(悬停槽,属性['renderSlot']('sidebar.session.row.hover',{'sessionId':节点['id']}))#槽
        卡体.appendChild(悬停槽)#放入
        for 状态 in 会话状态列(节点):#状态
            if 节点.get('archived') and 状态['state'] in ('done','idle'):#归档不重复空闲
                continue#跳过
            行状=文档.createElement('div')#一行
            行状.className='hoverStatus'#类
            标(行状)#模块
            点=状态点({'window':窗口,'state':状态['state']}).渲染()#点
            if 点 is not None:#有
                行状.appendChild(点)#放入
            字=文档.createElement('span')#字
            字.textContent=状态['label']#标签
            行状.appendChild(字)#放入
            卡体.appendChild(行状)#放入
        if 节点.get('archived'):#已归档
            归档行=文档.createElement('div')#行
            归档行.className=拼类('hoverStatus','hoverArchived')#类
            标(归档行)#模块
            档图=画图标(窗口,'archive-16',14)#归档
            if 档图 is not None:#有
                归档行.appendChild(档图)#放入
            档字=文档.createElement('span')#字
            档字.textContent=中文['row.archived']#已归档
            归档行.appendChild(档字)#放入
            卡体.appendChild(归档行)#放入
        复制文=None if 节点.get('blank') or 节点.get('title') in (None,'') else 节点.get('title')#可复制标题
        卡=悬停卡({
            'window':窗口,
            'anchor':行,
            'content':卡体,
            'openDelayMs':800,
            'grouped':True,
            'disabled':自身.菜单开 or (拖 is not None and 拖.get('active') is True),
            'copyText':复制文,
            'copyLabel':复制,
            'copiedLabel':中文['hover.copied'],
        }).渲染()#卡
        return 换上(自身,卡)#节点

    def 设菜单(自身,开):
        '菜单项关掉菜单时调用'
        自身.菜单开=开 is True#写入
        自身.渲染()#重画

def 项目行组件(属性):
    '按组键留一份'
    键=属性['group'].get('key')#键
    表=项目行组件.表 if hasattr(项目行组件,'表') else {}#表
    项目行组件.表=表#留下
    实例=表.get(键)#已有
    if 实例 is None:#没有
        实例=项目行(属性)#创建
        表[键]=实例#记下
    else:#更新
        实例.属性=属性#更新
    return 实例.渲染()#节点

def 检索结果行组件(属性):
    '按会话号留一份'
    键=属性['result']['id']#号
    表=检索结果行组件.表 if hasattr(检索结果行组件,'表') else {}#表
    检索结果行组件.表=表#留下
    实例=表.get(键)#已有
    if 实例 is None:#没有
        实例=检索结果行(属性)#创建
        表[键]=实例#记下
    else:#更新
        实例.属性=属性#更新
    return 实例.渲染()#节点

def 会话行组件(属性):
    '按会话号留一份，菜单开关才不会被重画清掉'
    键=属性['node']['id']#号
    表=会话行组件.表 if hasattr(会话行组件,'表') else {}#表
    会话行组件.表=表#留下
    实例=表.get(键)#已有
    if 实例 is None:#没有
        实例=会话行(属性)#创建
        表[键]=实例#记下
    else:#更新
        实例.属性=属性#更新
    return 实例.渲染()#节点
