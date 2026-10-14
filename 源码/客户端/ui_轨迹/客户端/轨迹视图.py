from nicegui import ui as 界面
from .布局 import 派生轨迹布局,追加轨迹流式布局
from .约定 import 空轨迹快照
from .轨迹表实现 import 轨迹表
from .轨迹时间线 import 轨迹时间线
from .轨迹工具栏 import 轨迹工具栏
from ..异常 import 页面失败文案

__all__=['轨迹视图']

def 缺省翻译(键,*_位置参数,**_关键字参数):
    '没有文案函数时原样返回键'
    return 键

class 轨迹视图:
    'conversation.view 的轨迹页。只读轨迹目标，不画进聊天列'
    def __init__(自身,会话标识=None,注入=None,快照=None,翻译=None):
        '槽位只传一份 props。键齐才在末尾画。表和时间线由这里画，构造时不画'
        自身.查询=''
        自身.等宽=False#与时长偏好对偶的等宽操作偏好
        自身.实测=False
        自身.实际时间=False
        自身.折轮=set()
        自身.折助手=set()
        自身._已订=False
        自身.表=轨迹表()
        自身.线=轨迹时间线()
        if isinstance(会话标识,dict) and 注入 is None:
            属性=会话标识
            自身.属性=属性
            自身.会话标识=属性['sessionId'] if 'sessionId' in 属性 else None
            自身.注入=属性
            译=属性['t'] if 't' in 属性 else None
            自身.翻译=译 if callable(译) else 缺省翻译
            自身.快照=空轨迹快照
            键齐=callable(属性.get('useTrajectory'))
        else:
            自身.属性={}
            自身.会话标识=会话标识
            自身.注入=注入 if 注入 is not None else {}
            自身.快照=快照 if isinstance(快照,dict) else 空轨迹快照
            自身.翻译=翻译 if 翻译 is not None else 缺省翻译
            键齐=快照 is not None
        if 键齐:
            自身._订轨迹()
            自身.渲染()

    def _订轨迹(自身):
        '轨迹目标变化后重画。画面已拆掉则不再画'
        if 自身._已订 is True:
            return
        用=自身.属性.get('useTrajectory') if isinstance(自身.属性,dict) else None
        订=getattr(用,'_subscribe',None) if 用 is not None else None
        if callable(订) is not True:
            return
        def 重画():
            '目标变化后重画这一页'
            壳=getattr(自身,'_壳',None)
            if 壳 is None:
                return
            槽=getattr(壳,'parent_slot',None)
            if 槽 is not None and getattr(槽,'parent',None) is None:
                return
            try:
                自身.渲染()
            except Exception as 错误:
                界面.label(页面失败文案(错误))
        订(重画)
        自身._已订=True

    def _读轨迹(自身):
        '只读 useTrajectory。不从会话快照的聊天视图里取'
        用=自身.属性.get('useTrajectory') if isinstance(自身.属性,dict) else None
        if callable(用):
            读到=用(lambda 值:值)
            if isinstance(读到,dict):
                return 读到
            return 空轨迹快照
        if isinstance(自身.快照,dict):
            return 自身.快照
        return 空轨迹快照

    def _渲轨迹图(自身,属主):
        '图片交给 conversation.trajectory.images。槽位组件自己画，这里不再画一遍'
        渲染槽=自身.属性.get('renderSlot') if isinstance(自身.属性,dict) else None
        if not callable(渲染槽):
            return None
        图属主=dict(属主) if isinstance(属主,dict) else {}
        加载=自身.注入.get('loadImage') if isinstance(自身.注入,dict) else None
        if 加载 is not None:
            图属主['loadImage']=加载
        return 渲染槽('conversation.trajectory.images',图属主)

    def 轮次(自身):
        '从轨迹目标派生轮次布局。定稿不含流式，再接上 partial'
        快照=自身._读轨迹()
        定稿=派生轨迹布局({
            'nodes':快照['eventNodes'] if 'eventNodes' in 快照 else None,
            'eventLocations':快照['eventLocations'] if 'eventLocations' in 快照 else None,
            'partial':None,
            'runningCalls':快照['runningCalls'] if 'runningCalls' in 快照 else None,
            'requests':快照['requests'] if 'requests' in 快照 else None,
            'callSchemas':快照['callSchemas'] if 'callSchemas' in 快照 else None,
        })
        最后=0
        for 轮 in 定稿:
            组列表=轮['groups'] if 'groups' in 轮 and 轮['groups'] is not None else []
            for 组 in 组列表:
                格列表=组['cells'] if 'cells' in 组 and 组['cells'] is not None else []
                for 格 in 格列表:
                    下标=格['index'] if 'index' in 格 else 0
                    最后=max(最后,下标)
        流式=快照['partial'] if 'partial' in 快照 else None
        return 追加轨迹流式布局(定稿,流式,最后)

    def 表属性(自身,属性=None):
        '组装轨迹表 props；传入的映射覆盖基线'
        合成={
            'turns':自身.轮次(),
            'onLoadOlder':自身.注入['loadOlder'] if 'loadOlder' in 自身.注入 else None,
            'renderImages':自身._渲轨迹图,
        }
        if 属性 is not None:
            合成.update(属性)
        return 合成

    def 表视图(自身,属性=None):
        '可调用的表视图，与时间线的调用形对称'
        return 自身.表(自身.表属性(属性))

    def _读实测(自身):
        '时长钩子给出的布尔。钩子失败直接抛出'
        用=自身.属性['useDuration'] if isinstance(自身.属性,dict) and 'useDuration' in 自身.属性 else None
        if not callable(用):
            return
        值=用(lambda 当前:当前)
        if isinstance(值,bool):
            自身.实测=值

    def 改实测(自身,值):
        '写入时长偏好并重画'
        自身.实测=值 is True
        写=自身.注入['setActualDuration'] if isinstance(自身.注入,dict) and 'setActualDuration' in 自身.注入 else None
        if callable(写):
            写(自身.实测)
        自身.重画()

    def 改实际时间(自身,值):
        '保留或压缩空闲间隔'
        自身.实际时间=值 is True
        自身.重画()

    def 切换全部轮次(自身):
        '折叠或展开每一轮'
        标识=[]
        for 轮 in 自身.轮次():
            if isinstance(轮,dict) and 'turn' in 轮:
                标识.append(轮['turn'])
        if len(标识)>0 and all(项 in 自身.折轮 for 项 in 标识):
            自身.折轮=set()
        else:
            自身.折轮=set(标识)
        自身.重画()

    def 切换全部调用(自身):
        '折叠或展开调用组'
        if len(自身.折助手)>0:
            自身.折助手=set()
        else:
            自身.折助手={'*'}
        自身.重画()

    def 改查询(自身,值):
        '工具栏已经取出输入值'
        if hasattr(值,'value'):
            值=值.value
        自身.查询=值 if isinstance(值,str) else ''
        自身.重画()

    def 渲染(自身):
        '画出轨迹视图。壳只建一次，之后只重画内容。失败句留在这一页'
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('trajectory-view')
        try:
            自身.重画()
        except Exception as 错误:
            文=页面失败文案(错误)
            壳=getattr(自身,'_壳',None)
            if 壳 is None:
                界面.label(文)
                return
            try:
                壳.clear()
            except Exception as 清失败:
                界面.label(页面失败文案(清失败))
                return
            with 壳:
                界面.label(文)

    def 重画(自身):
        '工具栏、时间线和账本'
        壳=getattr(自身,'_壳',None)
        if 壳 is None:
            return
        壳.clear()
        自身._读实测()
        轮次=自身.轮次()
        全轮折=len(轮次)>0 and all(isinstance(轮,dict) and 轮.get('turn') in 自身.折轮 for 轮 in 轮次)
        with 壳:
            轨迹工具栏({
                't':自身.翻译,
                'actualDuration':自身.实测,
                'onActualDurationChange':自身.改实测,
                'actualTime':自身.实际时间,
                'onActualTimeChange':自身.改实际时间,
                'allTurnsCollapsed':全轮折,
                'onToggleAllTurns':自身.切换全部轮次,
                'allAssistantsCollapsed':len(自身.折助手)>0,
                'onToggleAllAssistants':自身.切换全部调用,
                'searchQuery':自身.查询,
                'onSearchQueryChange':自身.改查询,
            }).渲染()
            线属性=自身.表属性({'collapsedTurns':自身.折轮,'collapsedAssistants':自身.折助手})
            线属性['onLoadEarlier']=线属性['onLoadOlder'] if 'onLoadOlder' in 线属性 else None
            自身.线.更新(线属性)
            自身.线.渲染()
            自身.表.更新(自身.表属性({
                'collapsedTurns':自身.折轮,
                'collapsedAssistants':自身.折助手,
                'onToggleTurn':lambda 轮:自身._翻转(自身.折轮,轮),
                'searchQuery':自身.查询,
            }))
            自身.表.渲染()

    def _翻转(自身,集合,键):
        '集合里已有该键则去掉，否则放入，然后重画'
        if 键 in 集合:
            集合.remove(键)
        else:
            集合.add(键)
        自身.重画()

    def 处理动作(自身,动作,载荷=None):
        '搜索、加载更早、写入实测时长；其余委托表'
        if 动作=='set-query':
            自身.查询=载荷 if 载荷 is not None else ''
            return
        if 动作=='load-older':
            加载=自身.注入['loadOlder'] if 'loadOlder' in 自身.注入 else None
            if 加载 is not None:
                return 加载()
            return False
        if 动作=='set-actual-duration':
            写入=自身.注入['setActualDuration'] if 'setActualDuration' in 自身.注入 else None
            if 写入 is not None:
                写入(载荷)
            return
        return 自身.表.处理动作(动作,载荷)
