'归档动作：菜单项、行悬停按钮，及停止在途工作后归档的确认对话框'

from nicegui import ui as 界面
from ...异常 import 页面失败文案

__all__=['归档会话菜单项','归档会话行按钮','会话归档确认对话框','活动行文案']#仅中文公开名

class 归档会话菜单项:#菜单 order 400
    '归档，或恢复已归档行'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        '菜单行'
        属性=自身.属性#props
        if 'sessionId' not in 属性 or 'useArchived' not in 属性 or 't' not in 属性 or 'useMenuOpenState' not in 属性:
            return#缺席位
        def 是否归档(集):
            '该会话是否已归档'
            return 属性['sessionId'] in 集
        已归档=属性['useArchived'](是否归档)#归档态
        def 取归档快捷(行表):
            '找出归档快捷键'
            for 行 in 行表:
                if 行['id']=='session.archive':
                    return 行
            return None
        if not 已归档:
            if 'useShortcuts' not in 属性:#无快捷钩
                return
            属性['useShortcuts'](取归档快捷)#快捷
        动作键='unarchiveSession' if 已归档 else 'archiveSession'#归档或恢复
        if 动作键 not in 属性:#无动作
            return
        翻译=属性['t']#文案
        def 选定():
            '关菜单后归档/恢复'
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            属性[动作键](属性['sessionId'])#动作
        界面.button(翻译('menu.unarchiveSession' if 已归档 else 'menu.archiveSession'), on_click=选定)

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

class 归档会话行按钮:#悬停 order 100
    '归档，或恢复已归档行'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        '行按钮'
        属性=自身.属性#props
        if 'sessionId' not in 属性 or 'useArchived' not in 属性 or 't' not in 属性:
            return#缺席位
        def 是否归档(集):
            '该会话是否已归档'
            return 属性['sessionId'] in 集
        已归档=属性['useArchived'](是否归档)#归档态
        动作键='unarchiveSession' if 已归档 else 'archiveSession'#归档或恢复
        if 动作键 not in 属性:#无动作
            return
        翻译=属性['t']#文案
        def 点击():
            '归档/恢复'
            属性[动作键](属性['sessionId'])#动作
        文=翻译('menu.unarchiveSession' if 已归档 else 'menu.archiveSession')
        界面.button(文, on_click=点击).tooltip(翻译('actions.unarchive' if 已归档 else 'actions.archive'))

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

def 活动行文案(条目,翻译):
    '一族活动行：数量与条目标签（无标签用 id）；未知族走通用行'
    项表=条目['items'] if 'items' in 条目 and 条目['items'] is not None else []#项
    数=len(项表)#数
    名=翻译('archive.confirm.listSeparator').join([(项['label'] if 'label' in 项 and 项['label'] is not None else 项['id']) for 项 in 项表])#名串
    复='one' if 数==1 else 'other'#单复
    种=条目['kind']#族
    if 种=='turn':#轮次
        return 翻译('archive.confirm.turn')#轮
    if 种=='subagent':#子智能体
        return 翻译(f'archive.confirm.subagents.{复}',{'n':数,'names':名})#行
    if 种=='job':#任务
        return 翻译(f'archive.confirm.jobs.{复}',{'n':数,'names':名})#行
    if 种=='schedule':#日程
        return 翻译(f'archive.confirm.schedules.{复}',{'n':数,'names':名})#行
    return 翻译(f'archive.confirm.other.{复}',{'kind':种,'n':数})#通用

class 归档确认表单:#单次请求对话框
    '在飞与错误态随请求消亡'

    def __init__(自身,请求,停止并归档,结算,翻译):
        '记下请求与回调'
        自身.请求=请求#请求
        自身.停止并归档=停止并归档#注入
        自身.结算=结算#结算
        自身.翻译=翻译#文案
        自身.归档中=False#在飞
        自身.错误=None#错误文

    def 关闭(自身):
        '归档中不可关'
        if 自身.归档中:#在飞
            return#止
        自身.结算()#结算

    def 确认(自身):
        '停工作并归档'
        自身.归档中=True#在飞
        自身.错误=None
        应答=自身.停止并归档(自身.请求['sessionId'])#跑
        if hasattr(应答,'等待'):#异步
            try:#等
                应答.等待()#等
                自身.归档中=False#完
                自身.结算()#结算
            except Exception as 原因:#失败
                自身.归档中=False#完
                自身.错误=页面失败文案(原因)
            return#止
        自身.归档中=False#同步完
        自身.结算()#结算

    def 渲染(自身):
        '确认对话框结构'
        翻译=自身.翻译#文案
        请求=自身.请求#请求
        with 界面.dialog() as 对话框:
            with 界面.card():
                界面.label(翻译('archive.confirm.title'))
                界面.label(翻译('archive.confirm.desc',{'title':请求['displayTitle']}))
                for 条 in 请求['activity']:
                    界面.label(活动行文案(条,翻译))
                if 自身.归档中:
                    界面.label(翻译('archive.confirm.pending'))
                if isinstance(自身.错误,str) and 自身.错误!='':
                    界面.label(自身.错误)
                取消=界面.button(翻译('cancel'), on_click=自身.关闭)
                确认=界面.button(翻译('archive.confirm.action'), on_click=自身.确认)
                界面.button(翻译('close'), on_click=自身.关闭)
                if 自身.归档中:
                    取消.disable()
                    确认.disable()
        对话框.open()

class 会话归档确认对话框:#shell.overlay 席
    '无待确认时 None；有则按会话键一份对话框'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身._表单=None#当前表单
        自身._表单键=None#会话键
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        '打开的确认对话框'
        属性=自身.属性#props
        if 'useArchiveRequest' not in 属性:#缺钩
            return#空
        def 原样(待):
            '原样返回归档请求'
            return 待
        请求=属性['useArchiveRequest'](原样)#待确认
        if 请求 is None:#无
            自身._表单=None
            自身._表单键=None
            return#空
        键=请求['sessionId']#会话
        if 自身._表单 is None or 自身._表单键!=键:#新请求
            自身._表单=归档确认表单(请求,属性['stopAndArchiveSession'],属性['settleSessionArchive'],属性['t'])#建
            自身._表单键=键
        with 界面.column().classes('session-archive'):
            自身._表单.渲染()

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
