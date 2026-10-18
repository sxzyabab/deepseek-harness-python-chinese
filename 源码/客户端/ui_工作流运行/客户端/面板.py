'持久工作流运行：运行和阶段按状态展开或收起'
import importlib.resources as 包资源
from ...存储 import 浅相等
from ...ui_基础界面组件.icons import 描边图标,常规描边
from ...ui_基础界面组件.状态点 import 状态点

__all__=['工作流运行面板']

样式文本=包资源.files(__package__).joinpath('面板.module.css').read_text(encoding='utf-8')

状态词={
    'running':'运行中',#运行中
    'completed':'已完成',#已完成
    'failed':'失败',#失败
    'cancelled':'已取消',#已取消
    'interrupted':'已中断',#已中断
}
右箭头路径='M6 12L9.29289 8.70711C9.68342 8.31658 9.68342 7.68342 9.29289 7.29289L6 4'#收起时的右箭头
上箭头路径='M12 10L8.70711 6.70711C8.31658 6.31658 7.68342 6.31658 7.29289 6.70711L4 10'#展开时的上箭头

def 清空(节点):
    '卸掉全部子节点'
    while 节点.firstChild is not None:#还有子节点
        节点.firstChild.remove()#从前往后卸

def 建文(文档,文,类名):
    '一段文字'
    节点=文档.createElement('span')#文字节点
    节点.className=类名#样式类
    节点.textContent=文#文案
    return 节点

def 点状态(状态):
    '取消和中断都是警告'
    if 状态=='running':#运行
        return 'ongoing'
    if 状态=='completed':#完成
        return 'done'
    if 状态=='failed':#失败
        return 'error'
    if 状态=='cancelled' or 状态=='interrupted':#取消或中断
        return 'warning'
    return 状态#闭合集合之外原样留下

def 是异常(状态):
    '失败、取消、中断要撑开披露'
    return 状态=='failed' or 状态=='cancelled' or 状态=='interrupted'

def 状态计数(状态,数量):
    '带数量的状态短语'
    return f'{状态词[状态]} {数量}'

def 成员数量(数量):
    '成员数。中文里一条和多条是同一句'
    return f'{数量} 个成员'

def 初始披露(事实):
    '干净默认收起，其余默认展开'
    return {
        'mode':事实['mode'],#模式
        'activityCount':事实['activityCount'],#成员数
        'open':事实['mode']!='clean',#干净才收起
        'pendingCleanCollapse':False,#还没有推迟
    }

def 推进披露(当前,事实,焦点还在):
    '事实没变时，待收且焦点已离开才收起'
    同样=当前['mode']==事实['mode'] and 当前['activityCount']==事实['activityCount']#事实没变
    if 同样:#沿用原来的开合
        if (not 当前['pendingCleanCollapse']) or 焦点还在:#没有待收，或焦点还在里面
            return 当前
        return {
            'mode':当前['mode'],
            'activityCount':当前['activityCount'],
            'open':False,#到点收起
            'pendingCleanCollapse':False,
        }
    if 事实['mode']=='clean':#变成干净
        推迟=当前['open'] and 焦点还在#焦点还在内容里就先别收
        return {
            'mode':事实['mode'],
            'activityCount':事实['activityCount'],
            'open':推迟,
            'pendingCleanCollapse':推迟,
        }
    if 当前['mode']=='clean' or (事实['mode']=='abnormal' and 当前['mode']!='abnormal'):#从干净进入，或新出现异常
        return {
            'mode':事实['mode'],
            'activityCount':事实['activityCount'],
            'open':True,#撑开
            'pendingCleanCollapse':False,
        }
    return {
        'mode':事实['mode'],
        'activityCount':事实['activityCount'],
        'open':当前['open'],#开合保持人手的选择
        'pendingCleanCollapse':False,
    }

def 收起待定(状态):
    '没有待定就原样返回'
    if not 状态['pendingCleanCollapse']:#没有推迟的收起
        return 状态
    return {
        'mode':状态['mode'],
        'activityCount':状态['activityCount'],
        'open':False,#收起
        'pendingCleanCollapse':False,
    }

def 焦点在内(元素):
    '没有元素，或文档焦点不在它里面，则为假'
    if 元素 is None:#还没挂上，或已经卸下
        return False
    return 元素.contains(元素.ownerDocument.activeElement)

def 已有阶段(阶段表,键):
    '挂载中的阶段回调都从这份表来'
    if 键 not in 阶段表:#表里没有这一阶段
        raise Exception(f'Missing disclosure state for phase {键}')
    return 阶段表[键]

def 阻止待定头焦点(事件):
    '点在披露头上时不要把焦点送进标题'
    头=事件.currentTarget.querySelector('[data-disclosure-row]')#这一层的披露头
    if 头 is None:#头应该先于内容画出来
        raise Exception('Missing disclosure header')
    if 头.contains(事件.target):#点在头上
        事件.preventDefault()#不转移焦点

class 状态披露:
    '受控披露头。展开时把子节点放在头下面，收起时卸下'
    def __init__(自身,文档,窗口):
        '建出头和子节点位。颜色用共享行的变量'
        自身.文档=文档#文档
        自身.窗口=窗口#窗口
        自身.根=文档.createElement('div')#头和内容上下排
        自身.根.style.display='flex'#列
        自身.根.style.flexDirection='column'#内容在头下面
        自身.根.style.width='100%'#撑满
        自身.根.style.minWidth='0'#允许收缩
        自身.行=文档.createElement('div')#可点的头
        自身.行.setAttribute('data-disclosure-row','')#供待收起时认出头
        自身.行.setAttribute('data-expandable','true')#整行可展开
        自身.行.setAttribute('role','button')#按钮
        自身.行.tabIndex=0#可聚焦
        自身.行.style.cursor='pointer'#可点
        自身.行.style.color='var(--dsw-alias-label-tertiary)'#三级文字
        自身.行.addEventListener('click',自身.点击)#点按
        自身.行.addEventListener('keydown',自身.按键)#回车和空格
        自身.行.addEventListener('mouseenter',自身.进入)#悬停变深
        自身.行.addEventListener('mouseleave',自身.离开)#离开恢复
        自身.前导=文档.createElement('span')#箭头
        自身.内容=文档.createElement('span')#标题和折叠侧
        自身.内容.className='headerContent'#占满剩余
        自身.内容.style.minWidth='0'#允许收缩
        自身.布局=文档.createElement('span')#标题与摘要同一行
        自身.布局.className='headerContentLayout'#间距在样式里
        自身.布局.style.display='flex'#横排
        自身.布局.style.alignItems='center'#居中
        自身.布局.style.minWidth='0'#允许收缩
        自身.布局.style.width='100%'#撑满内容区
        自身.标题节点=文档.createElement('span')#标题
        自身.折叠位=文档.createElement('span')#折叠侧不自己占盒子
        自身.折叠位.style.display='contents'#子项参加上面的横排
        自身.布局.appendChild(自身.标题节点)#标题在前
        自身.布局.appendChild(自身.折叠位)#摘要在后
        自身.内容.appendChild(自身.布局)
        自身.行.appendChild(自身.前导)#箭头在前
        自身.行.appendChild(自身.内容)#文字在后
        自身.根.appendChild(自身.行)
        自身.子位=文档.createElement('div')#展开后的内容
        自身.子位.style.minWidth='0'#允许收缩
        自身.根.appendChild(自身.子位)
        自身.切换=None#由外面的头接上

    def 更新(自身,标题,打开,行类,前导类,标题类,折叠):
        '改标题、箭头和折叠侧。开合由调用方决定'
        自身.行.className=行类#运行头或阶段头
        自身.前导.className=前导类#箭头盒子
        自身.标题节点.className=标题类#标题
        自身.标题节点.textContent=标题#看得见的标题
        自身.行.setAttribute('aria-expanded','true' if 打开 else 'false')#是否展开
        if 打开:#展开才带这个属性
            自身.根.setAttribute('data-open','true')
        else:#收起时拿掉
            自身.根.removeAttribute('data-open')
        清空(自身.前导)#换箭头
        if 打开:#展开换成上箭头
            路径=上箭头路径
        else:#收起用右箭头
            路径=右箭头路径
        自身.前导.appendChild(描边图标({'window':自身.窗口},'0 0 16 16',[路径],14,常规描边))
        清空(自身.折叠位)#换折叠侧
        for 节点 in 折叠:#分隔、数量、状态
            自身.折叠位.appendChild(节点)

    def 放子(自身,子,打开):
        '展开时挂上子节点，收起时卸下，好让失焦检查看到它已经不在'
        if 打开:#展开
            if 子.parentNode is not 自身.子位:#还没挂在这一位
                自身.子位.appendChild(子)
        elif 子.parentNode is not None:#收起就卸下
            子.remove()

    def 点击(自身,事件):
        '整行点击都交给外面的切换'
        if 自身.切换 is not None:#已接上
            自身.切换()

    def 按键(自身,事件):
        '回车和空格展开或收起。方向键不动'
        if 事件.key!='Enter' and 事件.key!=' ':#只认这两个
            return
        事件.preventDefault()#空格不滚动页面
        if 自身.切换 is not None:#已接上
            自身.切换()

    def 进入(自身,事件):
        '悬停时文字改成二级色'
        自身.行.style.color='var(--dsw-alias-label-secondary)'

    def 离开(自身,事件):
        '离开后回到三级色'
        自身.行.style.color='var(--dsw-alias-label-tertiary)'

class 运行头:
    '一次运行的披露头，下面是阶段列表'
    def __init__(自身,文档,窗口,面板):
        '建出头和阶段列表。列表先不挂上'
        自身.文档=文档#文档
        自身.窗口=窗口#窗口
        自身.面板=面板#整块面板
        自身.披露=状态披露(文档,窗口)#头
        自身.披露.切换=自身.切换#点头
        自身.列表=文档.createElement('div')#阶段或空文案
        自身.列表.className='phaseList'#阶段列表
        自身.列表.addEventListener('focusout',自身.内容失焦)#子项失焦会冒泡

    def 更新(自身,名称,数量,状态,打开):
        '改标题、成员数和运行状态，再按开合挂上或卸下阶段列表'
        文档=自身.文档#文档
        分隔=文档.createElement('span')#圆点分隔
        分隔.className='separator'#分隔点
        分隔.setAttribute('aria-hidden','true')#不进无障碍名称以外的读法，属性仍隐藏
        尾=文档.createElement('span')#右侧状态
        尾.className='statusTail'#状态尾
        尾.setAttribute('data-status',状态)#运行状态
        尾.appendChild(状态点({'window':自身.窗口,'state':点状态(状态)}).渲染())#状态点
        文=文档.createElement('span')#状态词
        文.textContent=状态词[状态]#运行中、已完成、失败、已取消、已中断
        尾.appendChild(文)
        自身.披露.更新(名称,打开,'runHeader','runLeading','runTitle',[
            分隔,#分隔点
            建文(文档,成员数量(数量),'runSummary'),#成员数
            尾,#状态
        ])
        自身.披露.放子(自身.列表,打开)#收起时卸下阶段

    def 切换(自身):
        '翻开或收起整次运行'
        自身.面板.切换运行()

    def 内容失焦(自身,事件):
        '焦点离开阶段列表就完成推迟的收起'
        自身.面板.运行失焦(事件)

class 成员行:
    '一名成员。能打开时是按钮，否则是普通行；焦点还在时先留着按钮'
    def __init__(自身,文档,窗口):
        '先不建节点，等第一次更新'
        自身.文档=文档#文档
        自身.窗口=窗口#窗口
        自身.根=None#行节点
        自身.是按钮=False#当前是不是按钮
        自身.已聚焦=False#焦点是否还在这行
        自身.成员=None#成员数据
        自身.模式=None#可打开时的模式
        自身.打开会话=None#打开回调
        自身.父标识=None#父会话
        自身.序号=None#成员序号
        自身.点槽=None#状态点的位置
        自身.名节点=None#名称
        自身.状态节点=None#状态词

    def 更新(自身,成员,模式,打开会话,父标识):
        '模式或焦点变了就换标签，否则只改文案'
        自身.成员=成员#最新成员
        自身.模式=模式#没有则不能打开
        自身.打开会话=打开会话#打开回调
        自身.父标识=父标识#父会话
        自身.序号=成员['seq']#序号
        应按钮=模式 is not None or 自身.已聚焦#能打开，或焦点还在
        if 自身.根 is None or 应按钮!=自身.是按钮:#标签种类变了
            自身.重建(应按钮)
            return
        自身.填()#只改文字和属性

    def 重建(自身,是按钮):
        '按钮和普通行互相替换，父节点里的位置保持不变'
        文档=自身.文档#文档
        if 是按钮:#可聚焦
            根=文档.createElement('button')
            根.type='button'#按钮
            根.addEventListener('focus',自身.聚焦)#得到焦点
            根.addEventListener('blur',自身.失焦)#失去焦点
            根.addEventListener('click',自身.点击)#打开
        else:#不可聚焦
            根=文档.createElement('div')
        自身.是按钮=是按钮#记下种类
        点槽=文档.createElement('span')#状态点槽
        点槽.className='dotSlot'#点的位置
        名盒=文档.createElement('span')#名称外框，焦点环画在这里
        名盒.className='memberLabelWrap'#外框
        名盒.setAttribute('data-member-label-wrap','')#名称外框
        名=文档.createElement('span')#名称
        名.className='memberLabel'#名称
        名.setAttribute('data-member-label','')#名称
        名盒.appendChild(名)
        状态文=文档.createElement('span')#状态
        状态文.className='memberStatus'#状态
        状态文.setAttribute('data-member-status-text','')#状态文字
        根.appendChild(点槽)#点
        根.appendChild(名盒)#名称
        根.appendChild(状态文)#状态
        自身.点槽=点槽#留下
        自身.名节点=名#留下
        自身.状态节点=状态文#留下
        旧=自身.根#替换前的节点
        if 旧 is not None and 旧.parentNode is not None:#还挂在父节点上
            旧.parentNode.replaceChild(根,旧)#原位替换
        自身.根=根#换成新的
        自身.填()#写入当前成员

    def 填(自身):
        '写名称、状态点和能否打开'
        成员=自身.成员#成员
        模式=自身.模式#模式
        if 成员['label']=='':#空名称
            名称='空成员名'
        else:#用成员自己的名称
            名称=成员['label']
        自身.名节点.textContent=名称#名称
        自身.状态节点.textContent=状态词[成员['status']]#状态词
        根=自身.根#行
        根.setAttribute('data-member-status',成员['status'])#成员状态
        清空(自身.点槽)#换点
        点=状态点({'window':自身.窗口,'state':点状态(成员['status'])})#状态点
        自身.点槽.appendChild(点.渲染())
        if not 自身.是按钮:#普通行没有打开语义
            根.className='memberRow'
            return
        if 模式 is not None:#现在能打开
            根.className='memberButton'#可点
            根.setAttribute('aria-label',f'打开 {名称}')#打开某成员
            根.removeAttribute('aria-disabled')#可点
            根.removeAttribute('tabindex')#回到按钮默认顺序
            return
        根.className='memberRow'#看起来像普通行
        根.setAttribute('aria-label',名称)#只剩名称
        根.setAttribute('aria-disabled','true')#不能打开
        根.tabIndex=-1#离开焦点顺序

    def 聚焦(自身,事件):
        '记下焦点，避免这一拍就被换成不能聚焦的行'
        自身.已聚焦=True#焦点在
        自身.填()#按能打开与否改属性

    def 失焦(自身,事件):
        '先改标记。不能打开时等焦点事件冒泡完再换成普通行'
        自身.已聚焦=False#焦点离开
        if 自身.模式 is not None:#还能打开，标签不用换
            自身.填()
            return
        自身.窗口.setTimeout(自身.换成行,0)#等外层收起逻辑先跑完

    def 换成行(自身):
        '焦点已经离开，且不能打开，就换成普通行'
        if 自身.已聚焦 or 自身.模式 is not None:#中途又聚焦或又能打开
            return
        if 自身.是按钮:#还是按钮
            自身.重建(False)

    def 点击(自身,事件):
        '能打开时把父会话、子会话和模式交给工作区'
        if 自身.模式 is None:#不能打开
            return
        自身.打开会话({
            'parentSessionId':自身.父标识,#父会话
            'childSessionId':自身.成员['childId'],#子会话
            'mode':自身.模式,#子身份上的模式
        })

class 阶段节:
    '一个阶段的披露头和成员列表'
    def __init__(自身,文档,窗口,面板):
        '建出阶段盒子。成员列表挂在披露头下面'
        自身.文档=文档#文档
        自身.窗口=窗口#窗口
        自身.面板=面板#整块面板
        自身.键=None#阶段键
        自身.待收=False#是否正在推迟收起
        自身.行表=[]#成员行
        自身.根=文档.createElement('div')#这一阶段
        自身.根.className='phase'#阶段
        自身.根.addEventListener('mousedown',自身.按下,True)#捕获，先于焦点
        自身.披露=状态披露(文档,窗口)#头
        自身.披露.切换=自身.切换#点头
        自身.成员位=文档.createElement('div')#成员
        自身.成员位.className='members'#成员列表
        自身.成员位.addEventListener('focusout',自身.内容失焦)#成员失焦会冒泡
        自身.根.appendChild(自身.披露.根)#头在盒子里

    def 更新(自身,阶段,披露,可导航):
        '改标题、数量、状态摘要和成员行'
        阶段名=阶段['phase']#阶段身份
        if 阶段名 is None:#没有这个字段
            标题='未分阶段'
        elif 阶段名=='':#空字符串
            标题='空阶段名'
        else:#用阶段自己的名字
            标题=阶段名
        成员表=阶段['members']#成员
        计数={}#状态到数量
        for 成员 in 成员表:#逐个计数
            状态=成员['status']#状态
            if 状态 in 计数:#已有
                计数[状态]=计数[状态]+1
            else:#第一次
                计数[状态]=1
        活跃=[]#还要单独点出的状态
        for 状态 in ('running','failed','cancelled','interrupted'):#这个顺序
            if 计数.get(状态,0)>0:#有这种
                活跃.append(状态)
        if len(活跃)==0:#没有进行中的异常
            摘要=状态计数('completed',计数.get('completed',0))#只写已完成
        else:#把要显示的拼起来
            if 'interrupted' in 活跃 and 计数.get('completed',0)>0:#中断时把已完成也带上
                可见=['completed']#已完成放前面
                可见.extend(活跃)
            else:#就这些
                可见=活跃
            片段=[]#短语
            for 状态 in 可见:#按顺序
                片段.append(状态计数(状态,计数[状态]))
            摘要=' · '.join(片段)#中间点分开
        文档=自身.文档#文档
        分隔=文档.createElement('span')#圆点
        分隔.className='separator'#分隔点
        分隔.setAttribute('aria-hidden','true')#装饰
        数量=建文(文档,成员数量(len(成员表)),'phaseCount')#成员数
        数量.setAttribute('data-phase-count','')#阶段数量
        状态文=建文(文档,摘要,'phaseStatus')#状态摘要
        状态文.setAttribute('data-phase-status-text','')#阶段状态
        打开=披露['open']#是否展开
        自身.待收=披露['pendingCleanCollapse']#推迟收起
        自身.披露.更新(标题,打开,'phaseHeader','phaseLeading','phaseTitle',[分隔,数量,状态文])
        自身.披露.放子(自身.成员位,打开)#收起时卸下成员
        自身.对齐成员(成员表,可导航)#成员行

    def 对齐成员(自身,成员表,可导航):
        '按序号留下原行，顺序跟成员表'
        旧={}#序号到现有行
        for 行 in 自身.行表:#现有
            旧[行.序号]=行
        新=[]#这一轮的顺序
        打开会话=自身.面板.属性['openSession']#打开
        父标识=自身.面板.属性['sessionId']#父会话
        for 成员 in 成员表:#按投影顺序
            序号=成员['seq']#序号
            if 成员['childId'] in 可导航:#这一名可以打开
                模式=可导航[成员['childId']]
            else:#不能打开
                模式=None
            if 序号 in 旧:#原行还在
                行=旧.pop(序号)
            else:#新成员
                行=成员行(自身.文档,自身.窗口)
            行.更新(成员,模式,打开会话,父标识)#改内容
            自身.成员位.appendChild(行.根)#按顺序挂上，已有的会被挪过来
            新.append(行)
        for 行 in 旧.values():#这一轮没有的
            if 行.根 is not None and 行.根.parentNode is not None:#还挂着
                行.根.remove()
        自身.行表=新#留下

    def 切换(自身):
        '翻开或收起这一阶段'
        自身.面板.切换阶段(自身.键)

    def 内容失焦(自身,事件):
        '焦点离开成员区就完成推迟的收起'
        自身.面板.阶段失焦(自身.键,事件)

    def 按下(自身,事件):
        '推迟收起时，点头不要把焦点从成员上抢走'
        if 自身.待收:#正在等焦点离开
            阻止待定头焦点(事件)

class 工作流运行面板:
    '一次工作流运行。调用本类得到根节点，同一节点复用披露状态'
    实例表={}#节点键到实例

    def __new__(类,属性):
        '根还挂在页面上就复用，卸下之后下次按当前事实重新开始'
        键=属性['node']['key']#聊天节点键
        已=类.实例表[键] if 键 in 类.实例表 else None#已有实例
        if 已 is not None and 已.根 is not None and 已.根.parentNode is not None:#还在页面上
            已.更新(属性)#换 props
            return 已.渲染()
        if 已 is not None:#上次的根已经卸下
            已.拆除()
        已=object.__new__(类)#新实例
        类.实例表[键]=已#按键记住
        return 已.建立(属性)

    def 建立(自身,属性):
        '记下 props 并画第一次'
        自身.属性=属性#合成 props
        自身.键=属性['node']['key']#节点键
        自身.根=None#section
        自身.运行头=None#运行头
        自身.阶段节表=[]#阶段
        自身.空节点=None#没有成员时的句子
        自身.披露状态=None#运行和各阶段的开合
        自身.运行内容=None#阶段列表，用来看焦点
        自身.阶段内容={}#阶段键到成员列表
        自身.阶段数据=[]#这一轮的阶段和事实
        自身.运行事实=None#整次运行的事实
        自身.可导航={}#子会话到模式
        自身.名称=''#运行名
        自身.运行状态='running'#运行状态
        自身.已订=False#是否已订阅
        自身.退订=[]#退订函数
        自身.绘制中=False#防止订阅同步重入
        自身.待重画=False#绘制中又来了一次
        自身.窗口=None#窗口
        自身.文档=None#文档
        return 自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性

    def 渲染(自身):
        '重入时记一笔，画完再补一次'
        if 自身.绘制中:#订阅在绘制中同步回调
            自身.待重画=True
            return 自身.根
        自身.绘制中=True#开始
        try:#画出
            结果=自身.画出()
        finally:#无论成败都放开
            自身.绘制中=False
        if 自身.待重画:#绘制中又要画
            自身.待重画=False
            return 自身.渲染()
        return 结果

    def 画出(自身):
        '先按当前开合铺到页面上，再按焦点推进，开合变了再铺一次'
        属性=自身.属性#props
        窗=属性['window']#这一页的窗口
        自身.窗口=窗#留下
        自身.文档=窗.document#文档
        if 自身.文档.getElementById('工作流运行面板样式') is None:#样式按文档只插一次
            样式=自身.文档.createElement('style')#样式节点
            样式.id='工作流运行面板样式'#只认这一份
            样式.textContent=样式文本#面板样式
            自身.文档.head.appendChild(样式)#放进文档
        自身.确保根()#section 和运行头只建一次
        自身.同步订阅()#会话和运行态
        节点=属性['node']#聊天节点
        数据=节点['data']#工作流载荷
        自身.名称=数据['name']#标题就是运行名
        自身.运行状态=数据['status']#运行状态
        阶段数据=[]#阶段和事实
        for 阶段 in 数据['phases']:#有异常优先，其次仍在跑，否则干净
            成员表=阶段['members']#这一阶段的成员
            模式='clean'#先当干净
            for 成员 in 成员表:#先看有没有异常
                if 是异常(成员['status']):#异常优先
                    模式='abnormal'
                    break
            if 模式!='abnormal':#没有异常再看是否还在跑
                for 成员 in 成员表:
                    if 成员['status']=='running':#仍在跑
                        模式='running'
                        break
            阶段数据.append((阶段,{'mode':模式,'activityCount':len(成员表)}))
        自身.阶段数据=阶段数据#留下给铺开
        有异常=是异常(数据['status'])#运行本身异常
        if not 有异常:#再看阶段
            for 阶段,事实 in 阶段数据:
                if 事实['mode']=='abnormal':#有阶段异常
                    有异常=True
                    break
        if 有异常:#异常优先
            运行模式='abnormal'
        elif 数据['status']=='running':#运行还在进行
            运行模式='running'
        else:#再看有没有阶段还在跑
            运行模式='clean'
            for 阶段,事实 in 阶段数据:
                if 事实['mode']=='running':#有阶段还在跑
                    运行模式='running'
                    break
        活动=0#成员总数
        for 阶段,事实 in 阶段数据:#各阶段相加
            活动=活动+事实['activityCount']
        自身.运行事实={'mode':运行模式,'activityCount':活动}#整次运行
        事实行=[]#推进用的键和事实
        for 阶段,事实 in 阶段数据:
            事实行.append((阶段['key'],事实))
        def 原样(值):
            '运行态快照原样返回'
            return 值
        状态表=属性['useSessionStatus'](原样)#浏览器里的运行态
        父标识=属性['sessionId']#父会话
        def 选取(会话):
            '仍在跑、父会话对得上、并且带有子身份的成员'
            结果={}#子会话到模式
            子表=会话['byId']#会话行
            投影表=会话['projectionsBySession']#投影
            for 阶段,事实 in 阶段数据:#逐阶段
                for 成员 in 阶段['members']:#逐成员
                    if 成员['status']!='running':#已经停下的不能打开
                        continue
                    子标识=成员['childId']#子会话
                    if 子标识 not in 子表:#列表里没有
                        continue
                    子=子表[子标识]#会话行
                    if 子['parentId']!=父标识:#不是这一父会话的
                        continue
                    if 子标识 not in 投影表:#还没有投影
                        continue
                    值=投影表[子标识]['values']#投影值
                    if 'subagent' not in 值:#没有子身份
                        continue
                    身份=值['subagent']#子身份
                    if 身份 is None:#空身份
                        continue
                    快照=状态表.get(子['id'])#这一会话的运行态
                    if isinstance(快照,dict):#字典快照
                        跑=快照.get('running')
                    else:#对象快照或没有
                        跑=None if 快照 is None else getattr(快照,'running',None)
                    if 跑 is None:#快照没写就用会话行
                        在跑=子['running']
                    else:#以快照为准
                        在跑=跑
                    if 在跑:#还在跑
                        结果[子标识]=身份['mode']
            return 结果
        自身.可导航=属性['useSessions'](选取,浅相等)#可打开的成员
        if 自身.披露状态 is None:#第一次按事实取初始开合
            阶段状态={}#各阶段
            for 键,事实 in 事实行:
                阶段状态[键]=初始披露(事实)
            自身.披露状态={'run':初始披露(自身.运行事实),'phases':阶段状态}
        轮=0#最多跟一次开合变化
        while 轮<2:#开合变了再读一次焦点
            开=自身.披露状态['run']['open']#铺开前的运行开合
            自身.铺开()#先让卸下的内容离开文档
            变了=自身.推进(事实行)#再按焦点推进
            if not 变了:#已经稳定
                break
            if 自身.披露状态['run']['open']==开:#运行开合没变，阶段变了
                自身.铺开()#把阶段开合铺上
                break
            轮=轮+1#运行开合变了，再走一轮
        else:#两轮都改了运行开合，把最后一次铺上
            自身.铺开()
        if 'parent' in 属性 and 属性['parent'] is not None and 自身.根.parentNode is not 属性['parent']:
            属性['parent'].appendChild(自身.根)#挂到调用方给的父节点
        return 自身.根

    def 确保根(自身):
        'section 和运行头只建一次'
        if 自身.根 is not None:#已经有了
            return
        根=自身.文档.createElement('section')#整块
        根.className='root'#面板根
        根.setAttribute('data-workflow-run','')#工作流运行
        根.addEventListener('mousedown',自身.按下,True)#运行头的待收起
        自身.根=根#留下
        自身.运行头=运行头(自身.文档,自身.窗口,自身)#运行头
        自身.运行内容=自身.运行头.列表#阶段列表
        根.appendChild(自身.运行头.披露.根)#头和它的内容位

    def 铺开(自身):
        '按当前披露状态改头、阶段和成员，不在这里改开合'
        自身.根.setAttribute('data-run-status',自身.运行状态)#运行状态
        运行=自身.披露状态['run']#运行披露
        自身.运行头.更新(自身.名称,自身.运行事实['activityCount'],自身.运行状态,运行['open'])
        列表=自身.运行头.列表#阶段列表
        if len(自身.阶段数据)==0:#还没有成员
            for 段 in 自身.阶段节表:#卸下阶段
                if 段.根.parentNode is not None:
                    段.根.remove()
                if 段.键 in 自身.阶段内容:#不再用这份焦点
                    del 自身.阶段内容[段.键]
            自身.阶段节表=[]#清空
            if 自身.空节点 is None:#句子只建一次
                自身.空节点=建文(自身.文档,'没有启动成员','empty')
            if 自身.空节点.parentNode is not 列表:#挂上
                列表.appendChild(自身.空节点)
            return
        if 自身.空节点 is not None and 自身.空节点.parentNode is not None:#有阶段就拿掉空文案
            自身.空节点.remove()
        旧={}#键到现有阶段
        for 段 in 自身.阶段节表:
            旧[段.键]=段
        新=[]#这一轮的顺序
        for 阶段,事实 in 自身.阶段数据:#按投影顺序
            键=阶段['key']#阶段键
            if 键 in 自身.披露状态['phases']:#已有开合
                披露=自身.披露状态['phases'][键]
            else:#刚出现，按事实取初始
                披露=初始披露(事实)
            if 键 in 旧:#原阶段还在
                段=旧.pop(键)
            else:#新阶段
                段=阶段节(自身.文档,自身.窗口,自身)
                段.键=键
            段.更新(阶段,披露,自身.可导航)#改这一阶段
            列表.appendChild(段.根)#按顺序挂上
            自身.阶段内容[键]=段.成员位#焦点看成员列表
            新.append(段)
        for 段 in 旧.values():#这一轮没有的阶段
            if 段.根.parentNode is not None:
                段.根.remove()
            if 段.键 in 自身.阶段内容:
                del 自身.阶段内容[段.键]
        自身.阶段节表=新#留下

    def 推进(自身,事实行):
        '焦点离开后收起干净的披露。新一轮活动会重新撑开'
        当前=自身.披露状态#推进前
        阶段状态={}#新的阶段表
        阶段变了=len(当前['phases'])!=len(事实行)#阶段个数变了
        阶段开了轮=False#有干净阶段进入新一轮
        for 键,事实 in 事实行:#逐阶段
            if 键 in 当前['phases']:#原来有
                先前=当前['phases'][键]
            else:#新阶段
                先前=None
            if 先前 is None:#按事实初始
                下一=初始披露(事实)
            else:#沿用并推进
                下一=推进披露(先前,事实,焦点在内(自身.阶段内容.get(键)))
            阶段状态[键]=下一#写下
            if 下一 is not 先前:#开合或事实变了
                阶段变了=True
            if 先前 is not None and 先前['mode']=='clean':#原来是干净的
                if 事实['mode']!='clean' or 事实['activityCount']!=先前['activityCount']:#进入新一轮
                    阶段开了轮=True
        推进运行=推进披露(当前['run'],自身.运行事实,焦点在内(自身.运行内容))#运行本身
        if 阶段开了轮 and 自身.运行事实['mode']!='clean' and not 推进运行['open']:#阶段新一轮把收起的运行重新打开
            运行={
                'mode':推进运行['mode'],
                'activityCount':推进运行['activityCount'],
                'open':True,#撑开
                'pendingCleanCollapse':False,
            }
        else:#沿用推进结果
            运行=推进运行
        if 运行 is 当前['run'] and not 阶段变了:#没有变化
            return False
        自身.披露状态={'run':运行,'phases':阶段状态}#换上
        return True

    def 切换运行(自身):
        '人手翻开或收起整次运行，并取消推迟收起'
        运行=自身.披露状态['run']#当前
        自身.披露状态['run']={
            'mode':运行['mode'],
            'activityCount':运行['activityCount'],
            'open':not 运行['open'],#翻开合
            'pendingCleanCollapse':False,#不再推迟
        }
        自身.渲染()

    def 切换阶段(自身,键):
        '人手翻开或收起一个阶段，并取消推迟收起'
        阶段表=dict(自身.披露状态['phases'])#拷贝
        阶段=已有阶段(阶段表,键)#必须已经有
        阶段表[键]={
            'mode':阶段['mode'],
            'activityCount':阶段['activityCount'],
            'open':not 阶段['open'],#翻开合
            'pendingCleanCollapse':False,#不再推迟
        }
        新=dict(自身.披露状态)#换阶段表
        新['phases']=阶段表
        自身.披露状态=新
        自身.渲染()

    def 运行失焦(自身,事件):
        '焦点还在阶段列表里就不动'
        if 事件.currentTarget.contains(事件.relatedTarget):#仍在列表里
            return
        运行=收起待定(自身.披露状态['run'])#完成推迟
        if 运行 is 自身.披露状态['run']:#没有待收
            return
        新=dict(自身.披露状态)#换运行披露
        新['run']=运行
        自身.披露状态=新
        自身.渲染()

    def 阶段失焦(自身,键,事件):
        '焦点还在这一阶段的成员里就不动'
        if 事件.currentTarget.contains(事件.relatedTarget):#仍在成员里
            return
        阶段=已有阶段(自身.披露状态['phases'],键)#这一阶段
        下一=收起待定(阶段)#完成推迟
        if 下一 is 阶段:#没有待收
            return
        阶段表=dict(自身.披露状态['phases'])#拷贝
        阶段表[键]=下一#换上
        新=dict(自身.披露状态)
        新['phases']=阶段表
        自身.披露状态=新
        自身.渲染()

    def 按下(自身,事件):
        '推迟收起时，点运行头不要把焦点从内容上抢走'
        if 自身.披露状态 is not None and 自身.披露状态['run']['pendingCleanCollapse']:
            阻止待定头焦点(事件)

    def 同步订阅(自身):
        '会话列表或运行态变了就重画'
        if 自身.已订:#已经订过
            return
        def 变更():
            '快照变了就重画'
            自身.渲染()
        for 名 in ('useSessions','useSessionStatus'):#两个钩子
            自身.退订.append(自身.属性[名]._subscribe(变更))
        自身.已订=True#记下

    def 拆除(自身):
        '退订，并从实例表拿掉。页面卸下根之后下次会重新开始'
        for 退 in 自身.退订:#逐个退订
            退()
        自身.退订=[]#清空
        自身.已订=False#可以再订
        if 自身.键 in 工作流运行面板.实例表 and 工作流运行面板.实例表[自身.键] is 自身:
            del 工作流运行面板.实例表[自身.键]
