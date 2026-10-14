from nicegui import ui as 界面
from .异常 import 页面失败文案
from .计划芯片 import 腾出根,标出失败

__all__=['计划卡','计划审阅打开']#仅中文公开名

def 恒等翻译(键,参数=None):
    '无文案表时返回键'
    return 键#键

class 计划卡:
    '已完成回合的已提交计划卡列表'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        if 'turn' in 自身.属性 and 'usePlans' in 自身.属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '按 usePlans 投影本回合已提交计划。打开时只传调用标识'
        属性=自身.属性#props
        回合=属性['turn'] if 'turn' in 属性 else None#回合
        用计划=属性['usePlans'] if 'usePlans' in 属性 else None#键控钩子
        打开计划=属性['openPlan'] if 'openPlan' in 属性 else None#打开
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        清除失败=腾出根(自身)
        if 用计划 is None or 回合 is None:#缺
            标出失败(清除失败)
            return
        号=回合['turn'] if isinstance(回合,dict) and 'turn' in 回合 else 回合
        try:
            计划表=用计划(str(号))
        except Exception as 错误:
            if getattr(自身,'根',None) is None:
                自身.根=界面.column().classes('plan-cards')
            with 自身.根:
                标出失败(清除失败)
                标出失败(页面失败文案(错误))
            return
        if not isinstance(计划表,(list,tuple)) or len(计划表)==0:#无
            标出失败(清除失败)
            return
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('plan-cards')
        with 自身.根:
            标出失败(清除失败)
            for 项 in 计划表:#逐
                计划=项 if isinstance(项,dict) else {}
                标题=计划['title'] if 'title' in 计划 and 计划['title'] is not None else ''
                标识=计划['callId'] if 'callId' in 计划 else None
                def 点开(调用=标识):
                    '打开该计划'
                    if 打开计划 is not None and 调用 is not None:
                        打开计划(调用)
                with 界面.card().classes('plan-card'):
                    if 标题!='':
                        界面.label(标题)
                    界面.label(翻译('preview.document'))
                    界面.button(翻译('preview.action'), on_click=点开).tooltip(翻译('preview.openNamed',{'title':标题}))

    def __call__(自身,属性=None):
        '有新属性则刷新后再渲染'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()

class 计划审阅打开:
    '待审计划自动打开与手动打开器'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已自动=False#是否已自动开
        if 'review' in 自身.属性 and 'openReview' in 自身.属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '自动打开一次，并返回手动打开按钮视图'
        属性=自身.属性#props
        审阅=属性['review'] if 'review' in 属性 else {}#审阅
        请求键=属性['requestKey'] if 'requestKey' in 属性 else ''#键
        打开审阅=属性['openReview'] if 'openReview' in 属性 else None#打开
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用存储=属性['useStore'] if 'useStore' in 属性 else None#store
        动作=属性['actions'] if 'actions' in 属性 else None#动作
        身份=('call:'+str(审阅['callId'])) if 'callId' in 审阅 and 审阅['callId'] is not None else ('review:'+请求键)
        已开=False
        if 用存储 is not None:
            def 读已开(态):
                '是否已标记打开'
                已开表=态['opened'] if isinstance(态,dict) and 'opened' in 态 else {}
                return (已开表[身份] if 身份 in 已开表 else None) is True
            已开=用存储(读已开) is True
        已挂=False
        用侧栏=属性['useSidebarMounted'] if 'useSidebarMounted' in 属性 else None
        if 用侧栏 is not None:
            def 有会话(会话):
                '侧栏已经挂上某个会话'
                return 会话 is not None
            已挂=用侧栏(有会话) is True
        if 已挂 is True and 已开 is not True and 自身.已自动 is not True and 打开审阅 is not None:
            try:
                打开审阅(审阅,请求键)
            except Exception as 错误:
                界面.label(页面失败文案(错误))
            else:
                if 动作 is not None and 'markOpened' in 动作:
                    动作['markOpened'](身份)
                自身.已自动=True
        清除失败=腾出根(自身)
        if getattr(自身,'根',None) is None:
            自身.根=界面.row().classes('plan-review-open')
        def 点开():
            '手动打开审阅'
            if 打开审阅 is None:
                return
            try:
                打开审阅(审阅,请求键)
            except Exception as 错误:
                界面.label(页面失败文案(错误))
        with 自身.根:
            标出失败(清除失败)
            界面.button(翻译('preview.full'), on_click=点开).tooltip(翻译('preview.open'))

    def __call__(自身,属性=None):
        '有新属性则刷新后再渲染'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
