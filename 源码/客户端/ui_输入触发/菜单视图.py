from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标右chevron14
from .异常 import 页面失败文案

__all__=['菜单视图','选项标识','样式表']#仅中文公开名

样式表='''
.menu{position:absolute;bottom:calc(100% + 4px);left:0;right:0;z-index:100;box-sizing:border-box;max-height:400px;overflow:hidden;padding:4px;display:flex;flex-direction:column;border:0;background:var(--dsw-specific-menu);box-shadow:var(--dsw-elevation-prominent)}
.viewport{display:flex;flex-direction:column;min-height:0;overflow-y:auto}
.item{display:flex;align-items:center;gap:6px;width:100%;min-height:34px;padding:6px 8px;border:none;border-radius:var(--dsw-radius-md);background:transparent;cursor:pointer;font-size:13px;line-height:20px;color:var(--dsw-alias-label-primary);text-align:left}
.item.active{background:var(--dsw-alias-interactive-bg-hover)}
.itemName{flex:none;max-width:40%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.itemAlias{flex:none;max-width:20%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
.itemDescription{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right;color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px}
.itemIcon{display:inline-flex;flex:none;width:14px;height:14px;color:var(--dsw-alias-menu-icon)}
.groupTitle{padding:6px 8px;font-size:11px;line-height:15px;color:var(--dsw-alias-label-tertiary)}
.sectionTitle{flex:none;min-height:23px;padding:5px 8px 2px;color:var(--dsw-alias-label-tertiary);font-size:11px;font-weight:500;line-height:16px}
.loading{display:flex;flex-direction:column;min-height:34px}
.skeletonRow{display:flex;align-items:center;box-sizing:border-box;min-height:34px;padding:6px 8px}
.skeletonBar{height:18px;border-radius:var(--dsw-radius-xs);background:var(--dsw-alias-bg-skeleton)}
.crumbs{flex:none;display:flex;align-items:center;flex-wrap:wrap;gap:2px;padding:3px 3px 5px;margin-bottom:2px;border-bottom:0.5px solid var(--dsw-alias-border-l1)}
.crumb{flex:0 1 auto;max-width:40%;overflow:hidden;padding:2px 5px;border:none;border-radius:var(--dsw-radius-sm);background:transparent;color:var(--dsw-alias-label-tertiary);font-size:11px;line-height:16px}
.crumbCurrent{color:var(--dsw-alias-label-primary)}
.crumbSeparator{flex:none;display:inline-flex;color:var(--dsw-alias-menu-icon)}
.trailing{flex:none;display:inline-flex;align-items:center;gap:3px;margin-left:auto}
.drillHintText,.drillHint{color:var(--dsw-alias-label-caption);font-size:10px;line-height:16px}
.drillHint{padding:0 4px;border-radius:var(--dsw-radius-xs);background:var(--dsw-alias-interactive-bg-hover)}
.drill{flex:none;display:inline-grid;place-items:center;width:18px;height:18px;border-radius:var(--dsw-radius-xs);color:var(--dsw-alias-menu-icon);cursor:pointer}
.srOnly{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
'''#样式表结束
界面.add_css(样式表,shared=True)

def 选项标识(来源,下标):#DOM id
    'aria-activedescendant 目标'
    return 'dsh-slash-option-'+来源+'-'+str(下标)#拼 id

def 缺省翻译(键,_插值=None):#无文案函数
    '原样返回键。未知源名就显示源名本身，不另写一句产品文案'
    return 键#键

菜单键=('menu','headers','onPick','onCrumb','onHover','onDismiss')#叠层注入面

def 菜单键齐(属性):
    '六个注入键都在且非空才画'
    if not isinstance(属性,dict):#不是合成 props
        return False#不齐
    for 键 in 菜单键:#逐键
        if 键 not in 属性 or 属性[键] is None:#缺键
            return False#不齐
    return True#齐

def 腾出根(自身):
    '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句。'
    旧=getattr(自身,'根',None)#旧根
    if 旧 is None:#还没有
        return None#无失败
    try:#清空
        旧.clear()#清子节点
    except Exception as 错误:#根已从页面拆掉
        自身.根=None#丢掉
        return 页面失败文案(错误)#页面上的失败句
    return None#清空成功

def 标出失败(文案):
    '失败句非空时写在当前页面上'
    if isinstance(文案,str) and 文案!='':#有句
        界面.label(文案)#留下

class 菜单视图:#候选菜单叠层组件
    '打开时渲染分组；关闭不画。候选来自已登记的源，这里不生成命令、技能或子会话'
    def __init__(自身,属性):#构造
        '记下 props。槽位渲染器只调用构造'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成
        自身.已订=False#菜单与页眉只订一次
        自身.存活=True#实例是否仍挂载
        自身.绘制中=False#避免订阅回调重入
        自身.待重画=False#绘制期间又来了一次
        if 菜单键齐(自身.属性):#键齐
            自身.渲染()#构造末尾才画

    def 更新(自身,属性):#刷新
        '刷新 props'
        自身.属性=属性#最新

    def 订菜单(自身):
        '菜单或页眉变了就重画'
        if 自身.已订 is True:#已订
            return#一次
        自身.已订=True#记下
        def 重画():
            '存储变了再画'
            if 自身.存活 is not True:#已卸
                return#停
            if 自身.绘制中 is True:#正在画
                自身.待重画=True#画完再来
                return#停
            自身.渲染()#重画
        for 名 in ('menu','headers'):#两个仓
            源=自身.属性[名] if 名 in 自身.属性 else None#仓
            订=getattr(源,'subscribe',None) if 源 is not None else None#订阅
            if callable(订):#有方法
                订(重画)#订上

    def 渲染(自身):#结构化视图
        '画出面包屑、分组、骨架、行与下钻。关闭时清掉菜单，不留占位句'
        if not 菜单键齐(自身.属性):#键未齐
            return#不画
        if 自身.绘制中 is True:#重入
            自身.待重画=True#记下
            return#让外层收尾
        自身.绘制中=True#占住
        try:#整段绘制
            自身._画出()#画
        finally:#放行
            自身.绘制中=False#结束
            if 自身.待重画 is True:#绘制期间又变了
                自身.待重画=False#消费
                自身.渲染()#再画

    def _画出(自身):#一次绘制
        '打开时画菜单；关闭时清空根'
        菜单=自身.属性['menu']#菜单仓
        翻译=自身.属性['t'] if 't' in 自身.属性 else 缺省翻译#翻译
        点选=自身.属性['onPick'] if 'onPick' in 自身.属性 else None#点选
        点屑=自身.属性['onCrumb'] if 'onCrumb' in 自身.属性 else None#面包屑
        悬停=自身.属性['onHover'] if 'onHover' in 自身.属性 else None#悬停
        态=菜单.getSnapshot()#快照
        if 'open' not in 态 or 态['open'] is not True:#关闭
            腾出根(自身)#清掉上次打开的菜单
            自身.订菜单()#关上也要能再打开
            return#不画
        页眉=None#面包屑表
        if 'headers' in 自身.属性 and 自身.属性['headers'] is not None:#有页眉仓
            页眉=自身.属性['headers'].getSnapshot()#快照
        高亮=态['highlight'] if 'highlight' in 态 else None#高亮
        组列表=态['groups'] if 'groups' in 态 else []#组
        清除失败=腾出根(自身)#清掉上一帧
        if getattr(自身,'根',None) is None:#还没有根
            自身.根=界面.column().classes('menu')#菜单根
        with 自身.根:#画在同一根上
            标出失败(清除失败)#清空失败留在页面上
            持有=自身.属性['pageFailure'] if 'pageFailure' in 自身.属性 else None
            失败文=getattr(持有,'页面失败',None) if 持有 is not None else None
            if isinstance(失败文,str) and 失败文!='':
                界面.label(失败文)
            if isinstance(页眉,dict) and len(页眉)>0:#有屑才画导航
                for 组 in 组列表:#按组找屑
                    源名=组['source']#源
                    if 源名 not in 页眉:#该源没发页眉
                        continue
                    轨=页眉[源名]#屑列
                    with 界面.row().classes('crumbs'):
                        界面.label(翻译('crumbs.aria')).classes('srOnly')
                        for 序号,屑 in enumerate(轨):#逐级
                            if 序号>0:#分隔
                                with 界面.element('span').classes('crumbSeparator'):
                                    图标右chevron14()
                            当前='current' in 屑 and 屑['current'] is True#当前级
                            def 点这一级(_事件=None,来源=源名,下标=序号,已当前=当前):
                                '回到这一级'
                                if 点屑 is not None and 已当前 is not True:
                                    点屑(来源,下标)
                            文=屑['label'] if 'label' in 屑 else ''#标签
                            钮=界面.button(文, on_click=点这一级).props('flat no-caps').classes('crumb')
                            if 当前:#已在这一级
                                钮.classes(add='crumbCurrent')
                                钮.disable()
            with 界面.column().classes('viewport'):
                界面.label(翻译('suggestions.aria')).classes('srOnly')
                for 组 in 组列表:#各组
                    项列表=组['items'] if 'items' in 组 else []#项
                    if 组['status']=='ready' and len(项列表)==0:#空就绪
                        continue
                    有分节=any('section' in 项 for 项 in 项列表)#行自带分节
                    藏标题='showGroupTitle' in 组 and 组['showGroupTitle'] is False#源关掉组标题
                    if 藏标题 is not True and 有分节 is not True:#组标题
                        界面.label(翻译(组['source'])).classes('groupTitle')
                    if 组['status']=='pending' and len(项列表)==0:#尚无旧行才出骨架
                        with 界面.column().classes('loading'):
                            界面.label(翻译('loading')).classes('srOnly')
                            with 界面.row().classes('skeletonRow'):
                                界面.element('div').classes('skeletonBar').style('width:32%')
                            with 界面.row().classes('skeletonRow'):
                                界面.element('div').classes('skeletonBar').style('width:48%')
                        continue
                    上一有=False#上一行是否带分节
                    上一=None#上一行分节
                    for 号,项 in enumerate(项列表):#行
                        有节='section' in 项#分节键
                        节=项['section'] if 有节 else None#分节文案
                        if 有节 and (上一有 is not True or 节!=上一) and 节 is not None:#新分节
                            界面.label(str(节)).classes('sectionTitle')
                        上一有=有节#记下
                        上一=节#记下
                        活=isinstance(高亮,dict) and 高亮.get('source')==组['source'] and 高亮.get('index')==号#高亮行
                        名=项['name'] if 'name' in 项 and 项['name'] is not None else ''#命令名
                        有标签='label' in 项 and 项['label'] is not None#本地化标题
                        展示=项['label'] if 有标签 else 名#行标题
                        def 点该项(_事件=None,来源=组['source'],下标=号):
                            '落定这一行'
                            if 点选 is not None:
                                点选(来源,下标)
                        def 移入(来源=组['source'],下标=号):
                            '指针移动高亮'
                            if 悬停 is not None:
                                悬停(来源,下标)
                        def 钻入(来源=组['source'],下标=号):
                            '下钻这一行'
                            if 点选 is not None:
                                点选(来源,下标,'drill')
                        钮=界面.button(on_click=点该项).props('flat no-caps').classes('item')
                        with 钮:
                            if 'icon' in 项 and 项['icon'] is not None:#行图标
                                图标值=项['icon']#图标
                                if isinstance(图标值,str):#名字
                                    字形={'folder':'folder','file':'description','session':'forum'}#内建
                                    界面.icon(字形[图标值] if 图标值 in 字形 else 'insert_drive_file').classes('itemIcon')
                                elif hasattr(图标值,'渲染') and getattr(图标值,'根',None) is None:#父级还没画过
                                    图标值.渲染()#放进这一行
                            界面.label(展示).classes('itemName')
                            if 有标签 and 展示.lower()!=名.lower():#标题不是命令名
                                界面.label(名).classes('itemAlias')
                            if 'description' in 项 and 项['description'] is not None:#说明
                                界面.label(str(项['description'])).classes('itemDescription')
                            if 'drill' in 项 and 项['drill'] is True:#可下钻
                                with 界面.row().classes('trailing'):
                                    界面.label(翻译('drill.hint')).classes('drillHintText')
                                    界面.label(翻译('drill.key')).classes('drillHint')
                                    钻=界面.element('span').classes('drill')
                                    钻.on('mousedown', lambda _事件,回调=钻入:回调())
                                    钻.tooltip(翻译('drill.aria'))
                                    with 钻:
                                        图标右chevron14()
                        if 活:#当前高亮
                            钮.classes(add='active')
                        if 活 is not True and 悬停 is not None:#静止指针不抢键盘高亮
                            钮.on('mousemove', lambda _事件,回调=移入:回调())
        自身.订菜单()#画完再订，避免构造期重入

    def __call__(自身,属性=None):#组件调用
        '对齐 React 组件调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
