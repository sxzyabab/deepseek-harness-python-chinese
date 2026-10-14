from nicegui import ui as 界面
from .异常 import 去掉敏感,页面失败文案,目标错误
from .样式挂载 import 挂到根,读样式

样式表=挂到根(读样式('目标条.module.css'),'目标条根')
样式表=样式表+'''
.目标条根 button.q-btn{
  min-height:28px;
  min-width:28px;
  padding:0;
  background:transparent !important;
  box-shadow:none !important;
}
'''
界面.add_css(样式表,shared=True)

__all__=['目标条','目标坞','阶段标签键']

def 腾出根(自身,隐藏=None):
    '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句。'
    旧=getattr(自身,'根',None)
    if 旧 is None:
        return None
    try:
        旧.clear()
        if 隐藏 is True:
            旧.set_visibility(False)
        elif 隐藏 is False:
            旧.set_visibility(True)
    except Exception as 错误:
        自身.根=None
        return 页面失败文案(错误)
    return None

def 标出失败(文案):
    '失败句非空时写在当前页面上'
    if isinstance(文案,str) and 文案!='':
        界面.label(文案)

阶段标签键={
    'active':'phase.active',
    'paused':'phase.paused',
    'blocked':'phase.blocked',
}

def 缺省翻译(键,_插值=None):
    '原样返回键'
    return 键

def 键齐(属性):
    '投影和四个变更动词都在才画'
    if not isinstance(属性,dict):
        return False
    for 键 in ('useProjection','onEdit','onPause','onResume','onClear'):
        if 键 not in 属性:
            return False
    return True

class 目标条:
    '进行中、暂停、受阻目标的条，以及编辑、暂停、恢复、清除'
    def __init__(自身,属性):
        '只记 props。目标坞负责画，构造不画。'
        自身.属性=属性
        自身.编辑中=False
        自身.草稿=''
        自身.进行中=False
        自身.动作错误=None
        自身.已清目标标识=None
        自身.存活=True

    def 更新(自身,属性):
        '目标身份变化时重置本地编辑态'
        旧目标=自身.属性['goal'] if 'goal' in 自身.属性 else None
        旧标识=旧目标['id'] if isinstance(旧目标,dict) and 'id' in 旧目标 else None
        自身.属性=属性
        新目标=属性['goal'] if 'goal' in 属性 else None
        新标识=新目标['id'] if isinstance(新目标,dict) and 'id' in 新目标 else None
        if 旧标识!=新标识:
            自身.编辑中=False
            自身.动作错误=None
            自身.已清目标标识=None

    def 卸载(自身):
        '标死'
        自身.存活=False

    def 执行动作(自身,动作):
        '同一时刻只跑一个变更'
        if 自身.进行中:
            return None
        if not callable(动作):
            return None
        自身.进行中=True
        自身.动作错误=None
        try:
            结果=动作()
        except Exception as 原因:
            if not 自身.存活:
                raise
            自身.进行中=False
            自身.动作错误=页面失败文案(原因)
            return None
        if not 自身.存活:
            return None
        自身.进行中=False
        if 结果 is None or not isinstance(结果,dict) or 结果.get('ok') is not True:
            错误=结果['error'] if isinstance(结果,dict) and 'error' in 结果 and 结果['error'] is not None else {}
            消息=错误['message'] if isinstance(错误,dict) and 'message' in 错误 else None
            码=错误['code'] if isinstance(错误,dict) and 'code' in 错误 else None
            文=去掉敏感(f"{消息} ({码})")
            if 文=='':
                自身.动作错误=页面失败文案(目标错误('目标变更失败'))
            else:
                自身.动作错误=文
        return 结果

    def 保存编辑(自身):
        '空草稿不提交'
        修剪=自身.草稿.strip()
        if 修剪=='':
            return
        编辑=自身.属性['onEdit'] if 'onEdit' in 自身.属性 else None
        def 提交编辑():
            '调用 onEdit'
            return 编辑(修剪)
        结果=自身.执行动作(提交编辑)
        if isinstance(结果,dict) and 结果.get('ok') is True:
            自身.编辑中=False

    def 清除(自身,已清标识):
        '成功后记下本地已清 id'
        清除动词=自身.属性['onClear'] if 'onClear' in 自身.属性 else None
        结果=自身.执行动作(清除动词)
        if isinstance(结果,dict) and 结果.get('ok') is True:
            自身.已清目标标识=已清标识

    def 开始编辑(自身):
        '草稿取当前目标陈述'
        目标=自身.属性['goal'] if 'goal' in 自身.属性 else None
        if isinstance(目标,dict) and 'objective' in 目标 and 目标['objective'] is not None:
            自身.草稿=目标['objective']
        else:
            自身.草稿=''
        自身.编辑中=True

    def 取消编辑(自身):
        '退出编辑'
        自身.编辑中=False

    def 视图(自身):
        '加载、缺席、已结束、已清都不画'
        目标=自身.属性['goal'] if 'goal' in 自身.属性 else None
        if not isinstance(目标,dict):
            return None
        if 目标.get('phase')=='complete':
            return None
        if 'id' in 目标 and 目标['id']==自身.已清目标标识:
            return None
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else 缺省翻译
        if 自身.编辑中:
            return {
                'mode':'edit',
                'draft':自身.草稿,
                'pending':自身.进行中,
                'error':自身.动作错误,
                'objectiveAria':翻译('objective.aria'),
                'saveLabel':翻译('action.save'),
                'cancelLabel':翻译('action.cancel'),
                'saveDisabled':自身.进行中 or 自身.草稿.strip()=='',
            }
        阶段=目标['phase'] if 'phase' in 目标 else None
        激活=自身.属性['activation'] if 'activation' in 自身.属性 else None
        if 阶段=='active':
            if 激活=='disarmed':
                标签键='phase.active.disarmed'
            else:
                标签键='phase.active'
            显示暂停=激活=='armed'
            显示恢复=激活=='disarmed'
        elif 阶段=='paused':
            标签键='phase.paused'
            显示暂停=False
            显示恢复=True
        elif 阶段=='blocked':
            标签键='phase.blocked'
            显示暂停=False
            显示恢复=False
        else:
            return None
        悬停=None
        受阻理由=目标['blockedReason'] if 'blockedReason' in 目标 else None
        if 阶段=='blocked' and isinstance(受阻理由,dict) and 'message' in 受阻理由:
            悬停=去掉敏感(受阻理由['message'])
            if 悬停=='':
                悬停=None
        return {
            'mode':'bar',
            'phase':阶段,
            'label':翻译(标签键),
            'objective':目标['objective'] if 'objective' in 目标 else None,
            'title':悬停,
            'pending':自身.进行中,
            'error':自身.动作错误,
            'showPause':显示暂停,
            'showResume':显示恢复,
            'pauseLabel':翻译('action.pause'),
            'resumeLabel':翻译('action.resume'),
            'editLabel':翻译('action.edit'),
            'clearLabel':翻译('action.clear'),
            'goalId':目标['id'] if 'id' in 目标 else None,
        }

    def 暂停(自身):
        '跑 onPause'
        动词=自身.属性['onPause'] if 'onPause' in 自身.属性 else None
        自身.执行动作(动词)

    def 恢复(自身):
        '跑 onResume'
        动词=自身.属性['onResume'] if 'onResume' in 自身.属性 else None
        自身.执行动作(动词)

    def 图标钮(自身,图标名,无障碍,点击,禁用):
        '图标按钮。父级只画一次'
        钮=界面.button(icon=图标名,on_click=点击).props(
            'flat round dense no-caps aria-label="'+无障碍.replace('"','')+'"'
        ).classes('iconBtn')
        钮.tooltip(无障碍)
        if 禁用 is True:
            钮.disable()
        return 钮

    def 渲染(自身):
        '编辑条，或阶段条与暂停、恢复、编辑、清除'
        视=自身.视图()
        if 视 is None:
            清除失败=腾出根(自身,隐藏=True)
            标出失败(清除失败)
            return
        清除失败=腾出根(自身,隐藏=False)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('目标条根')
        with 自身.根:
            标出失败(清除失败)
            with 界面.element('div').classes('dock'):
                if 视['mode']=='edit':
                    with 界面.element('div').classes('bar editBar'):
                        def 改草稿(事件):
                            '同步陈述草稿'
                            自身.草稿=事件.value
                        输入=界面.textarea(value=视['draft'],on_change=改草稿).props('autogrow borderless')
                        输入.classes('objective')
                        输入.tooltip(视['objectiveAria'])
                        错误=视['error']
                        if isinstance(错误,str) and 错误!='':
                            界面.label(错误).classes('error')
                        with 界面.element('div').classes('actions'):
                            def 点保存():
                                '提交陈述'
                                自身.保存编辑()
                                自身.渲染()
                            def 点取消():
                                '退出编辑'
                                自身.取消编辑()
                                自身.渲染()
                            自身.图标钮('check',视['saveLabel'],点保存,视['saveDisabled'])
                            自身.图标钮('close',视['cancelLabel'],点取消,视['pending'])
                    return
                条=界面.element('div').classes('bar')
                if isinstance(视['title'],str) and 视['title']!='':
                    条.tooltip(视['title'])
                with 条:
                    界面.icon('flag',size='14px').classes('goalGlyph')
                    界面.label(视['label']).classes('label')
                    陈述=视['objective']
                    if isinstance(陈述,str) and 陈述!='':
                        界面.label(陈述).classes('objective')
                    错误=视['error']
                    if isinstance(错误,str) and 错误!='':
                        界面.label(错误).classes('error')
                    with 界面.element('div').classes('actions'):
                        if 视['showPause'] is True:
                            def 点暂停():
                                '暂停目标'
                                自身.暂停()
                                自身.渲染()
                            自身.图标钮('pause',视['pauseLabel'],点暂停,视['pending'])
                        if 视['showResume'] is True:
                            def 点恢复():
                                '恢复目标'
                                自身.恢复()
                                自身.渲染()
                            自身.图标钮('play_arrow',视['resumeLabel'],点恢复,视['pending'])
                        def 点编辑():
                            '进入编辑'
                            自身.开始编辑()
                            自身.渲染()
                        def 点清除():
                            '清除目标'
                            自身.清除(视['goalId'])
                            自身.渲染()
                        自身.图标钮('edit',视['editLabel'],点编辑,视['pending'])
                        自身.图标钮('delete',视['clearLabel'],点清除,视['pending'])

    def __call__(自身,属性=None):
        '对齐组件调用。槽位走目标坞，不从这里再画一遍。'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 目标坞:
    '读 goal 投影，并叠上进程内激活。缺席或已结束不画。'
    def __init__(自身,属性):
        '记下 props。键齐了才在构造末尾画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身._已订=False
        自身._绘制中=False
        自身._待重画=False
        自身.条=目标条(自身.条属性())
        if 键齐(自身.属性):
            自身.渲染()

    def 条属性(自身):
        '从投影取 goal，激活只在 id 与修订对齐时带上'
        用投影=自身.属性['useProjection'] if 'useProjection' in 自身.属性 else None
        if callable(用投影):
            投影=用投影('goal')
        else:
            投影=None
        if isinstance(投影,dict) and 'goal' in 投影:
            目标=投影['goal']
        else:
            目标=None
        激活=None
        用激活=自身.属性['useGoalActivation'] if 'useGoalActivation' in 自身.属性 else None
        if callable(用激活) and isinstance(目标,dict):
            标识=目标['id'] if 'id' in 目标 else None
            修订=目标['revision'] if 'revision' in 目标 else None
            def 选取(下一,期望标识=标识,期望修订=修订):
                '同一目标和修订才返回激活'
                if not isinstance(下一,dict):
                    return None
                if 下一.get('id')!=期望标识:
                    return None
                if 下一.get('revision')!=期望修订:
                    return None
                if 'activation' not in 下一:
                    return None
                return 下一['activation']
            激活=用激活(选取)
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else 缺省翻译
        面={
            'goal':目标,
            'onEdit':自身.属性['onEdit'] if 'onEdit' in 自身.属性 else None,
            'onPause':自身.属性['onPause'] if 'onPause' in 自身.属性 else None,
            'onResume':自身.属性['onResume'] if 'onResume' in 自身.属性 else None,
            'onClear':自身.属性['onClear'] if 'onClear' in 自身.属性 else None,
            't':翻译,
        }
        if 激活 is not None:
            面['activation']=激活
        return 面

    def 确保订阅(自身):
        '投影或激活变化时重画。订阅期间的通知延后。'
        if 自身._已订:
            return
        自身._已订=True
        def 变(*_参数):
            '快照变了就重画'
            if 自身._绘制中:
                自身._待重画=True
                return
            自身.渲染()
        for 名 in ('useProjection','useGoalActivation'):
            用=自身.属性[名] if 名 in 自身.属性 else None
            订=getattr(用,'_subscribe',None)
            if callable(订):
                订(变)

    def 更新(自身,属性):
        '刷新并同步内嵌条'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.条.更新(自身.条属性())

    def 卸载(自身):
        '拆内嵌条'
        自身.条.卸载()

    def 渲染(自身):
        '把投影和激活交给内嵌条。条只在这里画一次。'
        自身._绘制中=True
        try:
            自身.确保订阅()
            自身.条.更新(自身.条属性())
            结果=自身.条.渲染()
        finally:
            自身._绘制中=False
        if 自身._待重画:
            自身._待重画=False
            return 自身.渲染()
        return 结果

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
