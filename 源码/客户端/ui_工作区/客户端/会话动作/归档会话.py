"""归档动作：菜单项、行悬停按钮，及停止在途工作后归档的确认对话框。"""

__all__=['归档会话菜单项','归档会话行按钮','会话归档确认对话框','活动行文案']#仅中文公开名

class 归档会话菜单项:#菜单 order 400
    """归档，或恢复已归档行。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """菜单行。"""
        属性=自身.属性#props
        已归档=属性['useArchived'](lambda 集:属性['sessionId'] in 集)#归档态
        快捷=None if 已归档 else 属性['useShortcuts'](lambda 行表:next((行 for 行 in 行表 if 行['id']=='session.archive'),None))#快捷
        翻译=属性['t']#文案
        def 选定():
            """关菜单后归档/恢复。"""
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            (属性['unarchiveSession'] if 已归档 else 属性['archiveSession'])(属性['sessionId'])#动作
        return {#菜单项
            'type':'MenuItemButton',#种类
            'shortcut':快捷,#快捷
            'icon':'IconUnarchiveOutlineRegular' if 已归档 else 'IconArchiveOutlineRegular',#图标
            'iconSize':14,#尺寸
            'label':翻译('menu.unarchiveSession' if 已归档 else 'menu.archiveSession'),#文案
            'onSelect':选定,#选定
        }#项结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 归档会话行按钮:#悬停 order 100
    """归档，或恢复已归档行。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """行按钮。"""
        属性=自身.属性#props
        已归档=属性['useArchived'](lambda 集:属性['sessionId'] in 集)#归档态
        翻译=属性['t']#文案
        def 点击():
            """归档/恢复。"""
            (属性['unarchiveSession'] if 已归档 else 属性['archiveSession'])(属性['sessionId'])#动作
        return {#按钮
            'type':'button','className':'iconButton',#钮
            'props':{#属性
                'aria-label':翻译('menu.unarchiveSession' if 已归档 else 'menu.archiveSession'),#aria
                'title':翻译('actions.unarchive' if 已归档 else 'actions.archive'),#tooltip
            },#属性结束
            'icon':'IconUnarchiveOutlineRegular' if 已归档 else 'IconArchiveOutlineRegular',#图标
            'iconSize':14,#尺寸
            'onClick':点击,#点击
        }#按钮结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

def 活动行文案(条目,翻译):
    """一族活动行：数量与条目标签（无标签用 id）；未知族走通用行。"""
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
    """在飞与错误态随请求消亡。"""

    def __init__(自身,请求,停止并归档,结算,翻译):
        """记下请求与回调。"""
        自身.请求=请求#请求
        自身.停止并归档=停止并归档#注入
        自身.结算=结算#结算
        自身.翻译=翻译#文案
        自身.归档中=False#在飞
        自身.错误=None#错误文

    def 关闭(自身):
        """归档中不可关。"""
        if 自身.归档中:#在飞
            return#止
        自身.结算()#结算

    def 确认(自身):
        """停工作并归档。"""
        自身.归档中=True#在飞
        自身.错误=None#清错
        应答=自身.停止并归档(自身.请求['sessionId'])#跑
        if hasattr(应答,'等待'):#异步
            try:#等
                应答.等待()#等
                自身.归档中=False#完
                自身.结算()#结算
            except Exception as 原因:#失败
                自身.归档中=False#完
                自身.错误=原因.message if hasattr(原因,'message') else str(原因)#错文
            return#止
        自身.归档中=False#同步完
        自身.结算()#结算

    def 渲染(自身):
        """确认对话框结构。"""
        翻译=自身.翻译#文案
        请求=自身.请求#请求
        活动子=[{'type':'li','key':f"{条['kind']}-{下标}",'children':[活动行文案(条,翻译)]} for 下标,条 in enumerate(请求['activity'])]#活动行
        子=[{'type':'ul','className':'archiveActivity','props':{'aria-label':翻译('archive.confirm.activity')},'children':活动子}]#体
        if 自身.归档中:#进行中
            子.append({'type':'div','className':'deleteStatus','props':{'role':'status'},'children':[翻译('archive.confirm.pending')]})#状态
        if 自身.错误 is not None:#有错
            子.append({'type':'div','className':'renameError','props':{'role':'alert'},'children':[自身.错误]})#错
        return {#Modal
            'type':'Modal','open':True,'onClose':自身.关闭,#模态
            'closeLabel':翻译('close'),#关
            'title':翻译('archive.confirm.title'),#题
            'description':翻译('archive.confirm.desc',{'title':请求['displayTitle']}),#述
            'footer':[#脚
                {'type':'Button','variant':'outline','disabled':自身.归档中,'onClick':自身.关闭,'children':[翻译('cancel')]},#取消
                {'type':'Button','variant':'outline','className':'deleteAction','disabled':自身.归档中,'onClick':自身.确认,'children':[翻译('archive.confirm.action')]},#确认
            ],#脚结束
            'children':子,#体
        }#Modal 结束

class 会话归档确认对话框:#shell.overlay 席
    """无待确认时 None；有则按会话键一份对话框。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身._表单=None#当前表单
        自身._表单键=None#会话键

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """打开的对话框，或 None。"""
        属性=自身.属性#props
        请求=属性['useArchiveRequest'](lambda 待:待)#待确认
        if 请求 is None:#无
            自身._表单=None#清
            自身._表单键=None#清
            return None#空
        键=请求['sessionId']#会话
        if 自身._表单 is None or 自身._表单键!=键:#新请求
            自身._表单=归档确认表单(请求,属性['stopAndArchiveSession'],属性['settleSessionArchive'],属性['t'])#建
            自身._表单键=键#记下
        return 自身._表单.渲染()#渲染

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
