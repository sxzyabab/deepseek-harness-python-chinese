from ...模块.客户端.通告 import 取握手窗口
import os
from ....基础设施.通用工具 import 当前毫秒
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.状态点 import 状态点

__all__=['子智能体报头谱系','子智能体名录动作']

样式模块='subagent-header-lineage'
视口边距=16
图形命名空间='http://www.w3.org/2000/svg'
下箭头路径='M4 6L7.29289 9.29289C7.68342 9.68342 8.31658 9.68342 8.70711 9.29289L12 6'
右箭头路径='M6 12L9.29289 8.70711C9.68342 8.31658 9.68342 7.68342 9.29289 7.29289L6 4'
刷新路径=(
    'M14.5001 8C14.5 9.28552 14.1188 10.5422 13.4045 11.611C12.6903 12.6799 11.6752 13.5129 10.4875 14.0049C9.29982 14.4968 7.99295 14.6255 6.73212 14.3747C5.4713 14.124 4.31314 13.505 3.4041 12.596C2.49514 11.687 1.87614 10.5288 1.62537 9.26798C1.37459 8.00716 1.50331 6.70028 1.99525 5.51261C2.48719 4.32494 3.32025 3.30981 4.3891 2.59557C5.45795 1.88134 6.71458 1.50008 8.0001 1.5C9.9001 1.5 11.7001 2.3 13.0001 3.6L14.5001 5.1',
    'M14.4999 1.5V5.1H10.8999',
)

def 确保样式(文档):
    '报头谱系样式只插一次'
    注入模块样式文件(
        文档,
        '子智能体报头谱系样式',
        os.path.join(os.path.dirname(__file__),'子智能体报头谱系.module.css'),
        样式模块,
    )

def 设或删(节点,名,值):
    '有值才写属性，没有就去掉'
    if 值 is None:
        节点.removeAttribute(名)
        return
    节点.setAttribute(名,值)

def 画线框图标(文档,路径列表,类名,尺寸):
    '上游 Regular 线框图标。类名留在 svg 上'
    图=文档.createElementNS(图形命名空间,'svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 16 16')
    图.setAttribute('fill','none')
    图.setAttribute('stroke-width','1')
    图.setAttribute('aria-hidden','true')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
        标样式模块(图,样式模块)
    for 路径 in 路径列表:
        划=文档.createElementNS(图形命名空间,'path')
        划.setAttribute('d',路径)
        划.setAttribute('stroke','currentColor')
        图.appendChild(划)
    return 图

def 拆时长(毫秒):
    '拆成秒、分、时、天和合计'
    总秒=int(max(0,毫秒)/1000)
    总分=int(总秒/60)
    总时=int(总分/60)
    return {
        'seconds':总秒%60,
        'minutes':总分%60,
        'hours':总时%24,
        'days':int(总时/24),
        'totalMinutes':总分,
        'totalHours':总时,
    }

def 格式化时长(毫秒):
    '随尺度降低视觉精度'
    部分=拆时长(毫秒)
    秒=部分['seconds']
    分=部分['minutes']
    时=部分['hours']
    天=部分['days']
    总分=部分['totalMinutes']
    总时=部分['totalHours']
    if 天>=365:
        年=int(天/365)
        月=int((天%365)/30)
        if 月==0:
            return '约'+str(年)+'年'
        return '约'+str(年)+'年'+str(月)+'个月'
    if 天>=30:
        月=int(天/30)
        余天=天%30
        if 余天==0:
            return '约'+str(月)+'个月'
        return '约'+str(月)+'个月'+str(余天)+'天'
    if 天>0:
        if 时==0:
            return str(天)+'天'
        return str(天)+'天'+str(时)+'小时'
    if 总时>0:
        return str(总时)+'小时'+str(分).zfill(2)+'分'+str(秒).zfill(2)+'秒'
    if 总分>0:
        return str(总分)+'分'+str(秒).zfill(2)+'秒'
    return str(秒)+'秒'

def 已知叶子(目录):
    '子目录已就绪且没有条目，才是已知叶子'
    if not isinstance(目录,dict):
        return False
    return 目录.get('state')=='ready' and len(目录.get('entries') or [])==0

def 树项(根):
    '菜单里可聚焦的树项'
    if 根 is None:
        return []
    return list(根.querySelectorAll('[role="treeitem"]:not([aria-disabled="true"])'))

def 菜单位置(触发,窗口):
    '菜单放在触发器下方，不越过视口'
    矩形=触发.getBoundingClientRect()
    视口宽=窗口.innerWidth
    宽=336
    if 视口宽-视口边距*2<宽:
        宽=视口宽-视口边距*2
    左=矩形.left
    if 左<视口边距:
        左=视口边距
    右边=视口宽-宽-视口边距
    if 左>右边:
        左=右边
    return {'top':矩形.bottom+5,'left':左}

class 切换图标:
    '切换器上的双箭头'
    def __init__(自身,文档):
        '记下文档'
        自身.文档=文档
        自身.根=None

    def 渲染(自身):
        '画出 16 像素的双折线'
        图=自身.文档.createElementNS(图形命名空间,'svg')
        图.setAttribute('width','16')
        图.setAttribute('height','16')
        图.setAttribute('viewBox','0 0 20 20')
        图.setAttribute('fill','none')
        图.setAttribute('aria-hidden','true')
        for 路径 in (
            'M5.99951 12.7L8.95546 14.9478C9.40011 15.2859 9.62244 15.455 9.87526 15.488C9.95774 15.4988 10.0413 15.4988 10.1238 15.488C10.3766 15.455 10.5989 15.2859 11.0436 14.9478L13.9995 12.7',
            'M13.9995 7.7417L11.0436 5.49387C10.5989 5.15574 10.3766 4.98668 10.1238 4.95362C10.0413 4.94283 9.95775 4.94283 9.87527 4.95362C9.62245 4.98668 9.40012 5.15574 8.95547 5.49387L5.99952 7.7417',
        ):
            划=自身.文档.createElementNS(图形命名空间,'path')
            划.setAttribute('d',路径)
            划.setAttribute('stroke','currentColor')
            划.setAttribute('stroke-width','1.5')
            图.appendChild(划)
        自身.根=图
        return 图

class 加载行:
    '目录还在加载时的一行说明'
    def __init__(自身,文档):
        '记下文档'
        自身.文档=文档
        自身.根=None

    def 渲染(自身):
        '正在加载子智能体'
        根=模块节点(自身.文档,'div',样式模块,'notice')
        根.textContent='正在加载子智能体…'
        自身.根=根
        return 根

class 名录行:
    '一层目录。只展开被点开的行，运行中每秒改时长'
    def __init__(自身,文档,窗口,容器):
        '记下层容器。时长先按当前时刻'
        自身.文档=文档
        自身.窗口=窗口
        自身.容器=容器
        自身.现在=当前毫秒()
        自身.钟=None
        自身.指纹=None
        自身.时长刷新=[]
        自身.子表={}

    def 停钟(自身):
        '停掉这一层的秒表'
        if 自身.钟 is not None:
            自身.窗口.clearInterval(自身.钟)
            自身.钟=None

    def 拆除(自身):
        '停表并拆掉下级'
        自身.停钟()
        for 子 in 自身.子表.values():
            子.拆除()
        自身.子表={}
        自身.时长刷新=[]

    def 令牌合计(自身,用量):
        '未缓存输入、输出、读缓存、写缓存四段相加'
        if not isinstance(用量,dict):
            return None
        return 用量['uncachedInputTokens']+用量['outputTokens']+用量['cacheReadTokens']+用量['cacheWriteTokens']

    def 同步钟(自身,在跑):
        '有运行中的行才每秒跳动'
        if 在跑 and 自身.钟 is None:
            def 滴答():
                '更新当前时刻并改时长文字'
                自身.现在=当前毫秒()
                自身.刷新时长()
            自身.钟=自身.窗口.setInterval(滴答,1000)
        elif not 在跑:
            自身.停钟()

    def 刷新时长(自身):
        '只改时长文字和行的无障碍名'
        for 项 in 自身.时长刷新:
            项()

    def 同步(自身,参数):
        '结构没变就只刷新时长，变了就重画这一层'
        目录=参数['catalog']
        行印=[]
        for 条目 in 目录.get('entries') or []:
            摘要=参数['summaries'].get(条目['id']) if isinstance(参数['summaries'],dict) else None
            标题=None
            格式=None
            用量=None
            时序=None
            if isinstance(摘要,dict):
                标题=摘要.get('title')
                格式=摘要.get('formatStatus')
                投影值=摘要.get('projectionValues')
                if isinstance(投影值,dict):
                    用量=投影值.get('tokenUsage')
                    时序=投影值.get('subagentTiming')
            子目录=参数['catalogs'].get(条目['id']) if isinstance(参数['catalogs'],dict) else None
            子态=子目录.get('state') if isinstance(子目录,dict) else None
            子数=len(子目录.get('entries') or []) if isinstance(子目录,dict) else None
            活动窗=时序.get('active') if isinstance(时序,dict) else None
            行印.append((
                条目.get('id'),条目.get('mode'),条目.get('label'),条目.get('activity'),
                标题,格式,子态,子数,自身.令牌合计(用量),
                None if not isinstance(时序,dict) else 时序.get('settledMs'),
                None if not isinstance(时序,dict) else 时序.get('lastTurnCompleted'),
                None if not isinstance(活动窗,dict) else 活动窗.get('since'),
                None if not isinstance(活动窗,dict) else 活动窗.get('through'),
            ))
        错误=目录.get('error')
        if isinstance(错误,dict):
            错误文=错误.get('message')
        elif 错误 is None:
            错误文=None
        else:
            错误文=str(错误)
        指纹=(
            参数['parentSessionId'],
            参数.get('currentSessionId'),
            参数['level'],
            目录.get('state'),
            错误文,
            tuple(行印),
            tuple(sorted(参数['expanded'])),
        )
        在跑=False
        for 条目 in 目录.get('entries') or []:
            if 条目.get('activity')=='running':
                在跑=True
                break
        自身.同步钟(在跑)
        if 指纹==自身.指纹:
            自身.现在=当前毫秒()
            自身.刷新时长()
            return
        自身.指纹=指纹
        自身.时长刷新=[]
        for 子 in 自身.子表.values():
            子.拆除()
        自身.子表={}
        while 自身.容器.firstChild is not None:
            自身.容器.firstChild.remove()
        自身.画出(参数)

    def 画出(自身,参数):
        '按这一层的条目画出树行'
        文档=自身.文档
        目录=参数['catalog']
        目录表=参数['catalogs']
        摘要表=参数['summaries']
        已展开=参数['expanded']
        父会话标识=参数['parentSessionId']
        当前标识=参数.get('currentSessionId')
        层级=参数['level']
        空载=目录.get('state')=='loading' and len(目录.get('entries') or [])==0
        留出披露=False
        for 条目 in 目录.get('entries') or []:
            子目录=目录表.get(条目['id']) if isinstance(目录表,dict) else None
            摘要=摘要表.get(条目['id']) if isinstance(摘要表,dict) else None
            格式=摘要.get('formatStatus') if isinstance(摘要,dict) else None
            子态=子目录.get('state') if isinstance(子目录,dict) else None
            if 条目.get('mode')!='external' and not 已知叶子(子目录) and 格式!='migration-required' and 子态!='migration-required':
                留出披露=True
                break
        if 空载:
            自身.容器.appendChild(加载行(文档).渲染())
        if 目录.get('state')=='error':
            错=模块节点(文档,'div',样式模块,'error')
            字=文档.createElement('span')
            错误=目录.get('error')
            错误文=None
            if isinstance(错误,dict) and isinstance(错误.get('message'),str) and 错误.get('message')!='':
                错误文=错误['message']
            elif 错误 is not None and isinstance(getattr(错误,'message',None),str) and 错误.message!='':
                错误文=错误.message
            if 错误文 is None:
                错误文='无法加载子智能体'
            字.textContent=错误文
            钮=模块节点(文档,'button',样式模块,'refresh')
            钮.setAttribute('type','button')
            钮.appendChild(画线框图标(文档,刷新路径,None,14))
            钮.appendChild(文档.createTextNode('重试'))
            def 点重试(事件,钉父=父会话标识):
                '再拉这一层的投影'
                参数['refreshProjection'](钉父)
            钮.addEventListener('click',点重试)
            错.appendChild(字)
            错.appendChild(钮)
            自身.容器.appendChild(错)
        for 条目 in 目录.get('entries') or []:
            自身.追加行(参数,条目,留出披露,当前标识,层级)

    def 追加行(自身,参数,条目,留出披露,当前标识,层级):
        '一行子会话，展开时再挂下一层'
        文档=自身.文档
        目录表=参数['catalogs']
        摘要表=参数['summaries']
        已展开=参数['expanded']
        父会话标识=参数['parentSessionId']
        外部=条目.get('mode')=='external'
        子目录=目录表.get(条目['id']) if isinstance(目录表,dict) else None
        是当前=条目.get('id')==当前标识
        已知=外部 or 已知叶子(子目录)
        摘要=摘要表.get(条目['id']) if isinstance(摘要表,dict) else None
        格式=摘要.get('formatStatus') if isinstance(摘要,dict) else None
        子态=子目录.get('state') if isinstance(子目录,dict) else None
        要打开=格式=='migration-required' or 子态=='migration-required'
        可展开=(not 已知) and (not 要打开)
        展开中=可展开 and 条目['id'] in 已展开
        子加载=子目录 is None or (isinstance(子目录,dict) and 子目录.get('state')=='loading' and len(子目录.get('entries') or [])==0)
        标签=条目['label'] if 条目.get('label') is not None else 条目['id']
        if 外部:
            模式='外部任务'
        elif 条目.get('mode')=='unknown':
            模式='模式未知'
        elif 条目.get('mode')=='one-shot':
            模式='一次性'
        else:
            模式='可继续'
        时序=None
        标题=None
        if isinstance(摘要,dict):
            标题=摘要.get('title')
            投影值=摘要.get('projectionValues')
            if isinstance(投影值,dict):
                时序=投影值.get('subagentTiming')
        已完成=(not 外部) and 条目.get('activity')=='inactive' and isinstance(时序,dict) and 时序.get('lastTurnCompleted') is True
        if 外部:
            活动=None
        elif 条目.get('activity')=='running':
            活动='正在运行'
        elif 已完成:
            活动='已完成'
        else:
            活动='当前未运行'
        次要段=[]
        if 标题 is not None:
            次要段.append(标题)
        if 要打开:
            次要段.append('需要迁移')
        else:
            次要段.append(模式)
        if 活动 is not None:
            次要段.append(活动)
        次要=' · '.join(次要段)
        用量=None
        if isinstance(摘要,dict):
            投影值=摘要.get('projectionValues')
            if isinstance(投影值,dict):
                用量=投影值.get('tokenUsage')
        合计=自身.令牌合计(用量)
        if 合计 is None:
            令牌文=None
        else:
            def 缩放(下一):
                '不到 100 保留一位小数。整数不带小数点'
                if 下一>=100:
                    return str(int(下一+0.5))
                数值=int(下一*10+0.5)/10
                if 数值==int(数值):
                    return str(int(数值))
                return str(数值)
            if 合计<1000:
                紧凑值=str(合计)
            elif 合计<1000000:
                紧凑值=缩放(合计/1000)+'K'
            else:
                紧凑值=缩放(合计/1000000)+'M'
            令牌文=紧凑值+' tok'
        def 活动毫秒(现在):
            '这一行到当前时刻的活跃毫秒'
            if not isinstance(摘要,dict):
                return None
            投影值=摘要.get('projectionValues')
            时=投影值.get('subagentTiming') if isinstance(投影值,dict) else None
            if not isinstance(时,dict):
                return None
            if 时.get('active') is None:
                return 时.get('settledMs')
            if 条目.get('activity')=='running':
                结束=现在
            else:
                结束=时['active']['through']
            return 时['settledMs']+max(0,结束-时['active']['since'])
        节点=模块节点(文档,'div',样式模块,'node')
        行=模块节点(文档,'div',样式模块,'row')
        行.setAttribute('role','treeitem')
        if 外部:
            行.setAttribute('tabindex','-1')
            行.setAttribute('aria-disabled','true')
        else:
            行.setAttribute('tabindex','0')
        行.setAttribute('aria-level',str(层级))
        if 是当前:
            行.setAttribute('aria-current','true')
        if 可展开:
            行.setAttribute('aria-expanded','true' if 展开中 else 'false')
        if not 可展开:
            if 留出披露:
                行.appendChild(模块节点(文档,'span',样式模块,'disclosureSpace'))
        else:
            披露类='disclosure disclosureOpen' if 展开中 else 'disclosure'
            披露=模块节点(文档,'button',样式模块,披露类)
            披露.setAttribute('type','button')
            披露.setAttribute('tabindex','-1')
            if 展开中:
                披露.setAttribute('aria-label','收起 '+str(标签)+' 的下级子智能体')
            else:
                披露.setAttribute('aria-label','展开 '+str(标签)+' 的下级子智能体')
            披露.appendChild(画线框图标(文档,(右箭头路径,),None,14))
            def 点披露(事件,钉子=条目['id']):
                '展开或收起这一枝'
                事件.preventDefault()
                事件.stopPropagation()
                参数['toggleBranch'](钉子)
            披露.addEventListener('click',点披露)
            行.appendChild(披露)
        点区=模块节点(文档,'div',样式模块,'clickarea')
        活动位=模块节点(文档,'span',样式模块,'rowActivitySlot')
        if 条目.get('activity')=='running':
            点态='ongoing'
        elif 已完成:
            点态='done'
        else:
            点态='idle'
        活动位.appendChild(状态点({'window':自身.窗口,'state':点态}).渲染())
        内容=模块节点(文档,'span',样式模块,'content')
        名类='label currentLabel' if 是当前 else 'label'
        名=模块节点(文档,'span',样式模块,名类)
        名.textContent=str(标签)
        副=模块节点(文档,'span',样式模块,'summary')
        副.textContent=次要
        内容.appendChild(名)
        内容.appendChild(副)
        点区.appendChild(活动位)
        点区.appendChild(内容)
        时长位=None
        度量=None
        def 写时长():
            '按当前时刻重写紧凑时长、悬停全文和行名'
            毫秒=活动毫秒(自身.现在)
            精确=None
            紧凑=None
            if 毫秒 is not None:
                紧凑=格式化时长(毫秒)
                部分=拆时长(毫秒)
                if 部分['days']==0:
                    精确=紧凑
                else:
                    精确=str(部分['days'])+'天'+str(部分['hours']).zfill(2)+'小时'+str(部分['minutes']).zfill(2)+'分'+str(部分['seconds']).zfill(2)+'秒'
            段=[]
            if 令牌文 is not None:
                段.append(令牌文)
            if 精确 is not None:
                段.append(精确)
            度量文=' · '.join(段)
            名段=[str(标签)]
            if 次要!='':
                名段.append(次要)
            if 度量文!='':
                名段.append(度量文)
            行.setAttribute('aria-label',' '.join(名段))
            if 时长位 is not None and 紧凑 is not None:
                时长位.textContent=紧凑
                时长位.setAttribute('title','总活跃耗时：'+精确)
        if 令牌文 is not None or 活动毫秒(自身.现在) is not None:
            度量=模块节点(文档,'span',样式模块,'metrics')
            if 令牌文 is not None:
                令牌位=模块节点(文档,'span',样式模块,'metricToken')
                令牌位.textContent=令牌文
                度量.appendChild(令牌位)
            if 活动毫秒(自身.现在) is not None:
                时长位=模块节点(文档,'span',样式模块,'metricDuration')
                度量.appendChild(时长位)
            点区.appendChild(度量)
        写时长()
        自身.时长刷新.append(写时长)
        if (not 是当前) and (not 外部):
            侧钮=模块节点(文档,'button',样式模块,'sidebarButton')
            侧钮.setAttribute('type','button')
            侧钮.setAttribute('aria-label','在侧边栏打开 '+str(标签))
            侧钮.appendChild(画线框图标(文档,(右箭头路径,),None,14))
            def 点侧栏(事件,钉条目=条目):
                '在侧栏新窗格打开，并关掉目录'
                事件.preventDefault()
                事件.stopPropagation()
                参数['openChildAside']({
                    'parentSessionId':父会话标识,
                    'childSessionId':钉条目['id'],
                    'mode':钉条目['mode'],
                })
                参数['closeCatalog']()
            def 侧栏按键(事件):
                '不把按键冒泡成行的打开'
                事件.stopPropagation()
            侧钮.addEventListener('click',点侧栏)
            侧钮.addEventListener('keydown',侧栏按键)
            泡=提示泡({
                'window':自身.窗口,
                'label':'在侧边栏打开',
                'side':'bottom',
                'children':侧钮,
            }).渲染()
            点区.appendChild(泡)
        行.appendChild(点区)
        def 打开本行():
            '外部行不能打开。其余打开子会话并关掉目录'
            if 外部:
                return
            参数['openChild']({
                'parentSessionId':父会话标识,
                'childSessionId':条目['id'],
                'mode':条目['mode'],
            })
            参数['closeCatalog']()
        def 行按键(事件):
            '回车或空格打开。左右方向键展开或收起'
            if 事件.key=='Enter' or 事件.key==' ':
                事件.preventDefault()
                事件.stopPropagation()
                打开本行()
            elif (事件.key=='ArrowRight' and 可展开 and not 展开中) or (事件.key=='ArrowLeft' and 展开中):
                事件.preventDefault()
                事件.stopPropagation()
                参数['toggleBranch'](条目['id'])
        def 点行(事件=None):
            '点这一行就打开'
            打开本行()
        行.addEventListener('click',点行)
        行.addEventListener('keydown',行按键)
        节点.appendChild(行)
        if 展开中:
            组=模块节点(文档,'div',样式模块,'children')
            组.setAttribute('role','group')
            if 子加载:
                组.setAttribute('aria-busy','true')
            if 子目录 is None:
                组.appendChild(加载行(文档).渲染())
            else:
                下级=名录行(文档,自身.窗口,组)
                自身.子表[条目['id']]=下级
                下级.同步({
                    'parentSessionId':条目['id'],
                    'currentSessionId':当前标识,
                    'catalog':子目录,
                    'catalogs':目录表,
                    'summaries':摘要表,
                    'expanded':已展开,
                    'level':层级+1,
                    'openChild':参数['openChild'],
                    'openChildAside':参数['openChildAside'],
                    'refreshProjection':参数['refreshProjection'],
                    'toggleBranch':参数['toggleBranch'],
                    'closeCatalog':参数['closeCatalog'],
                })
            节点.appendChild(组)
        自身.容器.appendChild(节点)

class 名录下拉:
    '一个触发器加一棵以根会话为顶的目录树'
    在册={}
    def __init__(自身,属性):
        '接上这一棵的开合。同一身份的上一棵还开着就沿用'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        自身.打开=False
        自身.钉住=False
        自身.已展开=set()
        自身.菜单位置=None
        自身.目录表={}
        自身.根=None
        自身.触发=None
        自身.菜单=None
        自身.菜单身=None
        自身.名录=None
        自身.悬停开=None
        自身.悬停关=None
        自身.已绑=False
        自身.已听文档=False
        自身.已订=False
        自身.退订=[]
        键=自身.状态键()
        旧=名录下拉.在册.get(键)
        if 旧 is not None and 旧 is not 自身:
            自身.打开=旧.打开
            自身.钉住=旧.钉住
            自身.已展开=set(旧.已展开)
            旧.拆除()
        名录下拉.在册[键]=自身
        自身.渲染()

    def 状态键(自身):
        '根会话、变体和当前行一起区分这一棵'
        当前=自身.属性.get('currentSessionId')
        return (自身.属性.get('rootSessionId'),自身.属性.get('variant'),当前)

    def 更新(自身,属性):
        '换 props。根会话变了就重新合上'
        旧键=自身.状态键()
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'window' in 自身.属性:
            自身.窗口=自身.属性['window']
        新键=自身.状态键()
        if 新键!=旧键:
            if 名录下拉.在册.get(旧键) is 自身:
                del 名录下拉.在册[旧键]
            自身.打开=False
            自身.钉住=False
            自身.已展开=set()
            名录下拉.在册[新键]=自身

    def 拆除(自身):
        '卸监听、停悬停，并从页面拿掉'
        自身.取消悬停开()
        自身.取消悬停关()
        自身.卸文档监听()
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False
        if 自身.名录 is not None:
            自身.名录.拆除()
            自身.名录=None
        if 自身.菜单 is not None:
            自身.菜单.remove()
            自身.菜单=None
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        if 名录下拉.在册.get(自身.状态键()) is 自身:
            del 名录下拉.在册[自身.状态键()]

    def 取消悬停开(自身):
        '取消即将打开的悬停'
        if 自身.悬停开 is None:
            return
        自身.窗口.clearTimeout(自身.悬停开)
        自身.悬停开=None

    def 取消悬停关(自身):
        '取消即将关闭的悬停'
        if 自身.悬停关 is None:
            return
        自身.窗口.clearTimeout(自身.悬停关)
        自身.悬停关=None

    def 安排悬停开(自身,事件=None):
        '指针停在触发器上 150 毫秒后打开'
        自身.取消悬停开()
        自身.取消悬停关()
        if 自身.打开:
            return
        def 到时():
            '到点打开'
            自身.悬停开=None
            自身.改开合(True)
        自身.悬停开=自身.窗口.setTimeout(到时,150)

    def 安排悬停关(自身,事件=None):
        '指针离开 120 毫秒后关闭。钉住的菜单不关'
        自身.取消悬停开()
        自身.取消悬停关()
        if 自身.钉住:
            return
        def 到时():
            '到点关闭'
            自身.悬停关=None
            自身.改开合(False)
        自身.悬停关=自身.窗口.setTimeout(到时,120)

    def 改开合(自身,下一,恢复焦点=False):
        '打开时量一次位置。关闭时清空展开'
        自身.取消悬停开()
        自身.取消悬停关()
        if 下一:
            if 自身.触发 is None:
                return
            自身.打开=True
            自身.菜单位置=菜单位置(自身.触发,自身.窗口)
        else:
            自身.钉住=False
            自身.打开=False
            自身.菜单位置=None
            自身.已展开=set()
        自身.渲染()
        if 恢复焦点 and 自身.触发 is not None:
            def 聚焦():
                '焦点回到触发器'
                if 自身.触发 is not None:
                    自身.触发.focus()
            自身.窗口.queueMicrotask(聚焦)

    def 关闭目录(自身):
        '从行里关掉整棵菜单'
        自身.改开合(False)

    def 切换枝(自身,子标识):
        '已展开则连同下级一起收起，否则展开并刷新该会话投影'
        if 子标识 in 自身.已展开:
            关闭=set()
            def 访问(父标识):
                '收起这一枝里已经展开的会话'
                if 父标识 in 关闭 or 父标识 not in 自身.已展开:
                    return
                关闭.add(父标识)
                枝=自身.目录表.get(父标识)
                条目表=枝.get('entries') if isinstance(枝,dict) else []
                for 条目项 in 条目表 or []:
                    访问(条目项['id'])
            访问(子标识)
            自身.已展开=set(标识 for 标识 in 自身.已展开 if 标识 not in 关闭)
            自身.渲染()
            return
        自身.已展开.add(子标识)
        自身.属性['refreshProjection'](子标识)
        自身.渲染()

    def 聚焦于(自身,序号):
        '在可聚焦树项里循环聚焦'
        项=树项(自身.菜单)
        if len(项)==0:
            return
        项[(序号+len(项))%len(项)].focus()

    def 键盘导航(自身,事件):
        '菜单打开时用方向键、行首行尾和退出移动焦点'
        项=树项(自身.菜单)
        序号=-1
        活动=自身.文档.activeElement
        下标=0
        while 下标<len(项):
            if 项[下标] is 活动:
                序号=下标
                break
            下标+=1
        if 事件.key=='Escape':
            事件.preventDefault()
            自身.改开合(False,True)
        elif 事件.key=='Home':
            事件.preventDefault()
            自身.聚焦于(0)
        elif 事件.key=='End':
            事件.preventDefault()
            自身.聚焦于(len(项)-1)
        elif 事件.key=='ArrowDown':
            事件.preventDefault()
            自身.聚焦于(序号+1)
        elif 事件.key=='ArrowUp':
            事件.preventDefault()
            if 序号<0:
                自身.聚焦于(len(项)-1)
            else:
                自身.聚焦于(序号-1)

    def 点触发(自身,事件=None):
        '没有打开标题时钉住菜单。有标题时点击标题并收起菜单'
        if 'openTitle' not in 自身.属性 or 自身.属性['openTitle'] is None:
            自身.取消悬停开()
            自身.取消悬停关()
            自身.钉住=True
            if not 自身.打开:
                自身.改开合(True)
            return
        自身.取消悬停开()
        if 自身.打开:
            自身.改开合(False)
        自身.属性['openTitle']()

    def 触发按键(自身,事件):
        '向下打开并聚焦第一行'
        if 事件.key!='ArrowDown':
            return
        事件.preventDefault()
        if not 自身.打开:
            自身.改开合(True)
        def 聚焦第一():
            '菜单出来后聚焦第一项'
            自身.聚焦于(0)
        自身.窗口.queueMicrotask(聚焦第一)

    def 点外部(自身,事件):
        '点在触发器和菜单外面就关闭'
        目标=事件.target
        if 目标 is None:
            return
        在根=自身.根 is not None and 自身.根.contains(目标)
        在菜单=自身.菜单 is not None and 自身.菜单.contains(目标)
        if not 在根 and not 在菜单:
            自身.改开合(False)

    def 放菜单(自身,事件=None):
        '视口或滚动变了就重算位置'
        if 自身.触发 is None:
            return
        自身.菜单位置=菜单位置(自身.触发,自身.窗口)
        if 自身.菜单 is not None and 自身.菜单位置 is not None:
            自身.菜单.style.top=str(自身.菜单位置['top'])+'px'
            自身.菜单.style.left=str(自身.菜单位置['left'])+'px'

    def 听文档(自身):
        '打开时听外部点击、缩放和滚动'
        if 自身.已听文档:
            return
        自身.文档.addEventListener('pointerdown',自身.点外部)
        自身.窗口.addEventListener('resize',自身.放菜单)
        自身.文档.addEventListener('scroll',自身.放菜单,True)
        自身.已听文档=True

    def 卸文档监听(自身):
        '菜单关上就摘掉文档监听'
        if not 自身.已听文档:
            return
        自身.文档.removeEventListener('pointerdown',自身.点外部)
        自身.窗口.removeEventListener('resize',自身.放菜单)
        自身.文档.removeEventListener('scroll',自身.放菜单,True)
        自身.已听文档=False

    def 编目录(自身,投影,摘要,状态表):
        '把投影快照收成带运行态的目录表'
        结果={}
        if not isinstance(投影,dict):
            return 结果
        for 标识,快照 in 投影.items():
            if not isinstance(快照,dict):
                continue
            值=快照.get('values') if isinstance(快照.get('values'),dict) else {}
            投影目录=值.get('subagentCatalog') if 'subagentCatalog' in 值 else None
            态=快照.get('state')
            if 态=='idle':
                态='loading' if 投影目录 is None else 'ready'
            elif 态=='migration-required' and 投影目录 is not None:
                态='ready'
            条目表=[]
            for 条目 in 投影目录 or []:
                拷=dict(条目)
                状态行=状态表.get(条目['id']) if isinstance(状态表,dict) else None
                if isinstance(状态行,dict) and 'running' in 状态行 and 状态行['running'] is not None:
                    运行中=状态行['running']
                else:
                    行=摘要.get(条目['id']) if isinstance(摘要,dict) else None
                    运行中=行.get('running') if isinstance(行,dict) else None
                拷['activity']='running' if 运行中 is True else 'inactive'
                条目表.append(拷)
            结果[标识]={
                'state':态,
                'error':快照.get('error'),
                'entries':条目表,
            }
        return 结果

    def 渲染(自身):
        '没有子会话证据就不画。打开时把树挂到 body'
        属性=自身.属性
        文档=自身.窗口.document
        自身.文档=文档
        确保样式(文档)
        def 取投影(状态):
            '各会话的投影快照'
            if not isinstance(状态,dict):
                return {}
            表=状态.get('projectionsBySession')
            if isinstance(表,dict):
                return 表
            return {}
        def 取摘要(状态):
            '会话摘要表'
            if not isinstance(状态,dict):
                return {}
            表=状态.get('byId')
            if isinstance(表,dict):
                return 表
            return {}
        def 原样(值):
            '整份状态'
            return 值
        投影=属性['useSessions'](取投影)
        摘要=属性['useSessions'](取摘要)
        状态表=属性['useSessionStatus'](原样)
        自身.目录表=自身.编目录(投影,摘要,状态表)
        根标识=属性['rootSessionId']
        目录=自身.目录表.get(根标识)
        变体=属性.get('variant')
        当前标识=属性.get('currentSessionId')
        当前条目=None
        if 当前标识 is not None and isinstance(投影,dict):
            根投影=投影.get(根标识)
            值=根投影.get('values') if isinstance(根投影,dict) else None
            表=值.get('subagentCatalog') if isinstance(值,dict) else None
            if isinstance(表,list):
                for 条目 in 表:
                    if isinstance(条目,dict) and 条目.get('id')==当前标识:
                        当前条目=条目
                        break
        if 当前条目 is not None:
            切换标题=当前条目['label'] if 当前条目.get('label') is not None else 当前条目['id']
        else:
            切换标题=属性.get('displayTitle')
        直接=目录.get('entries') if isinstance(目录,dict) else []
        直接数=len(直接 or [])
        运行数=0
        for 条目 in 直接 or []:
            if 条目.get('activity')=='running':
                运行数+=1
        if 目录 is not None:
            呈现=目录
        elif 变体=='switcher':
            呈现={'entries':[],'state':'loading','error':None}
        else:
            呈现=None
        可见=呈现 is not None and (
            变体=='switcher' or 呈现.get('state')=='error' or len(呈现.get('entries') or [])>0
        )
        if not 可见:
            自身.取消悬停开()
            自身.取消悬停关()
            自身.钉住=False
            自身.打开=False
            自身.已展开=set()
            自身.卸文档监听()
            if 自身.名录 is not None:
                自身.名录.拆除()
                自身.名录=None
            if 自身.菜单 is not None:
                自身.菜单.remove()
                自身.菜单=None
                自身.菜单身=None
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
                自身.触发=None
                自身.已绑=False
            自身.订阅()
            return None
        根类='root switcherRoot' if 变体=='switcher' else 'root'
        if 自身.根 is None:
            自身.根=模块节点(文档,'div',样式模块,根类)
        else:
            自身.根.className=根类
            标样式模块(自身.根,样式模块)
        if 自身.触发 is None:
            自身.触发=模块节点(文档,'button',样式模块,'trigger')
            自身.触发.setAttribute('type','button')
            自身.根.appendChild(自身.触发)
        祖先切换=变体=='switcher' and 属性.get('openTitle') is not None
        if 变体=='switcher':
            触发类='switcherTrigger ancestorSwitcherTrigger' if 祖先切换 else 'switcherTrigger'
        else:
            触发类='trigger'
        自身.触发.className=触发类
        标样式模块(自身.触发,样式模块)
        自身.触发.setAttribute('aria-haspopup','tree')
        自身.触发.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        if 变体=='switcher':
            自身.触发.setAttribute('aria-label','切换子智能体：'+str(切换标题))
        elif 运行数>0:
            自身.触发.setAttribute('aria-label',str(运行数)+' 个子智能体，正在运行')
        else:
            自身.触发.setAttribute('aria-label',str(直接数)+' 个子智能体')
        while 自身.触发.firstChild is not None:
            自身.触发.firstChild.remove()
        if 变体=='switcher':
            题=模块节点(文档,'span',样式模块,'switcherTitle')
            题.textContent='' if 切换标题 is None else str(切换标题)
            自身.触发.appendChild(题)
            自身.触发.appendChild(切换图标(文档).渲染())
        else:
            if 运行数>0:
                活动位=模块节点(文档,'span',样式模块,'activitySlot')
                活动位.appendChild(状态点({'window':自身.窗口,'state':'ongoing'}).渲染())
                自身.触发.appendChild(活动位)
            计=模块节点(文档,'span',样式模块,'count')
            计.textContent=str(直接数)+' 个子智能体'
            自身.触发.appendChild(计)
            自身.触发.appendChild(画线框图标(
                文档,
                (下箭头路径,),
                'triggerOpen' if 自身.打开 else None,
                14,
            ))
        if not 自身.已绑:
            自身.根.addEventListener('keydown',自身.键盘导航)
            自身.根.addEventListener('mouseleave',自身.安排悬停关)
            自身.触发.addEventListener('mouseenter',自身.安排悬停开)
            自身.触发.addEventListener('click',自身.点触发)
            自身.触发.addEventListener('keydown',自身.触发按键)
            自身.已绑=True
        if 自身.打开:
            if 自身.菜单 is None:
                自身.菜单=模块节点(文档,'div',样式模块,'menu')
                自身.菜单身=模块节点(文档,'div',样式模块,'menuBody')
                自身.菜单身.setAttribute('role','tree')
                自身.菜单身.setAttribute('aria-label','子智能体会话')
                自身.菜单.appendChild(自身.菜单身)
                自身.菜单.addEventListener('mouseenter',自身.取消悬停关)
                自身.菜单.addEventListener('mouseleave',自身.安排悬停关)
                自身.菜单.addEventListener('keydown',自身.键盘导航)
                文档.body.appendChild(自身.菜单)
            if 自身.菜单位置 is not None:
                自身.菜单.style.top=str(自身.菜单位置['top'])+'px'
                自身.菜单.style.left=str(自身.菜单位置['left'])+'px'
            if 自身.名录 is None:
                自身.名录=名录行(文档,自身.窗口,自身.菜单身)
            自身.名录.同步({
                'parentSessionId':根标识,
                'currentSessionId':当前标识,
                'catalog':呈现,
                'catalogs':自身.目录表,
                'summaries':摘要,
                'expanded':自身.已展开,
                'level':1,
                'openChild':属性['openChild'],
                'openChildAside':属性['openChildAside'],
                'refreshProjection':属性['refreshProjection'],
                'toggleBranch':自身.切换枝,
                'closeCatalog':自身.关闭目录,
            })
            自身.听文档()
        else:
            自身.卸文档监听()
            if 自身.名录 is not None:
                自身.名录.拆除()
                自身.名录=None
            if 自身.菜单 is not None:
                自身.菜单.remove()
                自身.菜单=None
                自身.菜单身=None
        if 'parent' in 属性 and 属性['parent'] is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        自身.订阅()
        return 自身.根

    def 订阅(自身):
        '投影或运行态变了就重画。根离开页面就退订'
        if 自身.已订:
            return
        def 变更():
            '投影变了就重画。暂时没有子会话时也继续听'
            自身.渲染()
        for 名 in ('useSessions','useSessionStatus'):
            钩=自身.属性.get(名)
            if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                自身.退订.append(钩._subscribe(变更))
                自身.已订=True

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 子智能体名录动作:
    '根会话标题栏上的下级数量。子会话不画'
    def __init__(自身,属性):
        '记下 props 并画出数量菜单'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.下拉=None
        自身.根=None
        自身.已订=False
        自身.退订=[]
        if 'window' in 自身.属性 or 'useSessions' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '子会话交给谱系槽。根会话画数量下拉'
        属性=自身.属性
        if 'useSessions' not in 属性:
            return None
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        会话标识=属性['sessionId']
        def 是子(状态):
            '来源是子智能体'
            if not isinstance(状态,dict):
                return False
            表=状态.get('byId')
            行=表.get(会话标识) if isinstance(表,dict) else None
            if not isinstance(行,dict):
                return False
            return 行.get('origin')=='subagent'
        if 属性['useSessions'](是子):
            if 自身.下拉 is not None:
                自身.下拉.拆除()
                自身.下拉=None
            自身.根=None
            自身.订阅()
            return None
        份额={
            'window':窗口,
            'rootSessionId':会话标识,
            'variant':'count',
            'useSessions':属性['useSessions'],
            'useSessionStatus':属性['useSessionStatus'],
            'openChild':属性['openChild'],
            'openChildAside':属性['openChildAside'],
            'refreshProjection':属性['refreshProjection'],
        }
        if 'parent' in 属性:
            份额['parent']=属性['parent']
        if 自身.下拉 is None:
            自身.下拉=名录下拉(份额)
        else:
            自身.下拉.更新(份额)
            自身.下拉.渲染()
        自身.根=自身.下拉.根
        自身.订阅()
        return 自身.根

    def 订阅(自身):
        '会话来源变了就重画'
        if 自身.已订:
            return
        钩=自身.属性.get('useSessions')
        if 钩 is None or not hasattr(钩,'_subscribe') or not callable(钩._subscribe):
            return
        def 变更():
            '重画数量菜单'
            自身.渲染()
        自身.退订.append(钩._subscribe(变更))
        自身.已订=True

    def __call__(自身,属性=None):
        '槽位再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 子智能体报头谱系:
    '面包屑上的标题切换，以及没有打开动作时的下级数量'
    def __init__(自身,属性):
        '记下 props 并画出谱系'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.切换=None
        自身.计数=None
        自身.根=None
        if 'window' in 自身.属性 or 'useSessions' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '找不到父会话就不画。根会话的数量在标题动作里'
        属性=自身.属性
        if 'useSessions' not in 属性 or 'useSession' not in 属性:
            return None
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        谱系标识=属性['lineageSessionId']
        def 取地址(会话):
            '当前会话上的子智能体地址'
            if not isinstance(会话,dict):
                return None
            子=会话.get('subagent')
            if not isinstance(子,dict):
                return None
            return 子.get('address')
        地址=属性['useSession'](取地址)
        def 取父(状态):
            '先认地址，再认目录，最后认摘要上的父标识'
            if isinstance(地址,dict) and 地址.get('childSessionId')==谱系标识:
                return 地址.get('parentSessionId')
            if not isinstance(状态,dict):
                return None
            投影表=状态.get('projectionsBySession')
            if isinstance(投影表,dict):
                for 父标识,快照 in 投影表.items():
                    值=快照.get('values') if isinstance(快照,dict) else None
                    表=值.get('subagentCatalog') if isinstance(值,dict) else None
                    if isinstance(表,list):
                        for 条目 in 表:
                            if isinstance(条目,dict) and 条目.get('id')==谱系标识:
                                return 父标识
            摘要表=状态.get('byId')
            摘要=摘要表.get(谱系标识) if isinstance(摘要表,dict) else None
            if isinstance(摘要,dict) and 摘要.get('origin')=='subagent':
                return 摘要.get('parentId')
            return None
        父标识=属性['useSessions'](取父)
        if 父标识 is None:
            if 自身.切换 is not None:
                自身.切换.拆除()
                自身.切换=None
            if 自身.计数 is not None:
                自身.计数.拆除()
                自身.计数=None
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            自身.订阅()
            return None
        if 自身.根 is None:
            自身.根=文档.createElement('span')
            自身.根.style.display='contents'
        共用={
            'window':窗口,
            'useSessions':属性['useSessions'],
            'useSessionStatus':属性['useSessionStatus'],
            'openChild':属性['openChild'],
            'openChildAside':属性['openChildAside'],
            'refreshProjection':属性['refreshProjection'],
        }
        切换份额=dict(共用)
        切换份额['rootSessionId']=父标识
        切换份额['currentSessionId']=谱系标识
        切换份额['variant']='switcher'
        切换份额['displayTitle']=属性['displayTitle']
        if 属性.get('openTitle') is not None:
            切换份额['openTitle']=属性['openTitle']
        if 自身.切换 is None:
            自身.切换=名录下拉(切换份额)
        else:
            自身.切换.更新(切换份额)
            自身.切换.渲染()
        if 属性.get('openTitle') is None:
            计数份额=dict(共用)
            计数份额['rootSessionId']=谱系标识
            计数份额['variant']='count'
            if 自身.计数 is None:
                自身.计数=名录下拉(计数份额)
            else:
                自身.计数.更新(计数份额)
                自身.计数.渲染()
        elif 自身.计数 is not None:
            自身.计数.拆除()
            自身.计数=None
        保留=[]
        if 自身.切换 is not None and 自身.切换.根 is not None:
            保留.append(自身.切换.根)
        if 自身.计数 is not None and 自身.计数.根 is not None:
            保留.append(自身.计数.根)
        子=自身.根.firstChild
        while 子 is not None:
            下一=子.nextSibling
            if 子 not in 保留:
                子.remove()
            子=下一
        for 节点 in 保留:
            if 节点.parentNode is not 自身.根:
                自身.根.appendChild(节点)
        if 'parent' in 属性 and 属性['parent'] is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        自身.订阅()
        return 自身.根

    def 订阅(自身):
        '父会话或地址变了就重画谱系'
        if getattr(自身,'已订',False):
            return
        自身.已订=False
        自身.退订=[]
        def 变更():
            '重画谱系'
            自身.渲染()
        for 名 in ('useSession','useSessions'):
            钩=自身.属性.get(名)
            if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                自身.退订.append(钩._subscribe(变更))
                自身.已订=True

    def __call__(自身,属性=None):
        '槽位再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
