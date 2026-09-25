"""重命名动作：菜单项拉起请求，shell.overlay 对话框应答。
对话框在行菜单外，因行随菜单卸载；浏览区标题双击走同一请求。
"""

__all__=['重命名会话菜单项','会话重命名对话框']#仅中文公开名

class 重命名表单:#单次请求对话框
    """草稿在挂载时由请求播种；在飞与错误随请求消亡。
    会话无客户端重名规则（Host 规范化）；与工作区重命名不同，未改标题不挡确认。
    """

    def __init__(自身,请求,重命名会话,结算,翻译):
        """记下请求与回调。"""
        自身.请求=请求#目标
        自身.重命名会话=重命名会话#注入
        自身.结算=结算#结算
        自身.翻译=翻译#文案
        自身.草稿=请求['currentTitle']#草稿
        自身.重命名中=False#在飞
        自身.错误=None#错文
        自身.拼写中=False#IME

    def 关闭(自身):
        """重命名中不可关。"""
        if 自身.重命名中:#在飞
            return#止
        自身.结算()#结算

    def 确认(自身):
        """提交修剪后标题。"""
        修剪=自身.草稿.strip()#修剪
        if 自身.重命名中 or 修剪=='':#挡
            return#止
        自身.重命名中=True#在飞
        自身.错误=None#清
        应答=自身.重命名会话(自身.请求['sessionId'],修剪)#跑
        if hasattr(应答,'等待'):#异步
            try:#等
                应答.等待()#等
                自身.重命名中=False#完
                自身.结算()#结算
            except Exception as 原因:#失败
                自身.重命名中=False#完
                自身.错误=原因.message if hasattr(原因,'message') else str(原因)#错
            return#止
        自身.重命名中=False#同步完
        自身.结算()#结算

    def 改草稿(自身,值):
        """输入变更清错。"""
        自身.草稿=值#草稿
        自身.错误=None#清错

    def 键下(自身,键名):
        """Enter 提交；拼写中的 Enter 不提交。"""
        if 键名=='Enter' and not 自身.拼写中:#提交
            自身.确认()#确认

    def 渲染(自身):
        """重命名对话框。"""
        翻译=自身.翻译#文案
        挡=自身.重命名中 or 自身.草稿.strip()==''#挡确认
        子=[{#输入
            'type':'input','className':'renameInput',#输入
            'props':{#属性
                'value':自身.草稿,#值
                'aria-label':翻译('field.sessionName'),#aria
                'data-modal-autofocus':True,#自动焦
                'disabled':自身.重命名中,#禁用
            },#属性结束
            'onFocus':'select',#聚焦全选
            'onChange':自身.改草稿,#改
            'onCompositionStart':lambda:setattr(自身,'拼写中',True),#IME 始
            'onCompositionEnd':lambda:setattr(自身,'拼写中',False),#IME 终
            'onKeyDown':自身.键下,#键
        }]#子起
        if 自身.错误 is not None:#有错
            子.append({'type':'div','className':'renameError','props':{'role':'alert'},'children':[自身.错误]})#错
        return {#Modal
            'type':'Modal','open':True,'onClose':自身.关闭,#模态
            'closeLabel':翻译('close'),#关
            'title':翻译('rename.session.title'),#题
            'footer':[#脚
                {'type':'Button','variant':'outline','disabled':自身.重命名中,'onClick':自身.关闭,'children':[翻译('cancel')]},#取消
                {'type':'Button','variant':'primary','disabled':挡,'onClick':自身.确认,'children':[翻译('rename')]},#确认
            ],#脚结束
            'children':子,#体
        }#Modal 结束

class 重命名会话菜单项:#菜单 order 200
    """请求重命名对话框，以行当前标题播种。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """菜单行。"""
        属性=自身.属性#props
        快捷=属性['useShortcuts'](lambda 行表:next((行 for 行 in 行表 if 行['id']=='session.rename'),None))#快捷
        翻译=属性['t']#文案
        def 选定():
            """关菜单后请求。"""
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            属性['requestSessionRename'](属性['sessionId'],属性['displayTitle'])#请求
        return {#菜单项
            'type':'MenuItemButton',#种类
            'shortcut':快捷,#快捷
            'icon':'IconEditOutlineRegular',#图标
            'label':翻译('rename'),#文案
            'onSelect':选定,#选定
        }#项结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 会话重命名对话框:#shell.overlay 席
    """无请求时 None；有则按会话键一份对话框。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身._表单=None#当前
        自身._表单键=None#会话键

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        """打开的对话框，或 None。"""
        属性=自身.属性#props
        请求=属性['useRenameRequest'](lambda 待:待)#待改名
        if 请求 is None:#无
            自身._表单=None#清
            自身._表单键=None#清
            return None#空
        键=请求['sessionId']#会话
        if 自身._表单 is None or 自身._表单键!=键:#新请求
            自身._表单=重命名表单(请求,属性['renameSession'],属性['settleSessionRename'],属性['t'])#建
            自身._表单键=键#记下
        return 自身._表单.渲染()#渲染

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
