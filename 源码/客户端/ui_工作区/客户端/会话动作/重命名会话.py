'重命名动作：菜单项拉起请求，shell.overlay 对话框应答'

from nicegui import ui as 界面
from ...异常 import 页面失败文案

__all__=['重命名会话菜单项','会话重命名对话框']#仅中文公开名

class 重命名表单:#单次请求对话框
    """草稿在挂载时由请求播种；在飞与错误随请求消亡。
    会话无客户端重名规则（Host 规范化）；与工作区重命名不同，未改标题不挡确认
    """

    def __init__(自身,请求,重命名会话,结算,翻译):
        '记下请求与回调'
        自身.请求=请求#目标
        自身.重命名会话=重命名会话#注入
        自身.结算=结算#结算
        自身.翻译=翻译#文案
        自身.草稿=请求['currentTitle']#草稿
        自身.重命名中=False#在飞
        自身.错误=None#错文
        自身.拼写中=False#IME

    def 关闭(自身):
        '重命名中不可关'
        if 自身.重命名中:#在飞
            return#止
        自身.结算()#结算

    def 确认(自身):
        '提交修剪后标题'
        修剪=自身.草稿.strip()#修剪
        if 自身.重命名中 or 修剪=='':#挡
            return#止
        自身.重命名中=True#在飞
        自身.错误=None
        应答=自身.重命名会话(自身.请求['sessionId'],修剪)#跑
        if hasattr(应答,'等待'):#异步
            try:#等
                应答.等待()#等
                自身.重命名中=False#完
                自身.结算()#结算
            except Exception as 原因:#失败
                自身.重命名中=False#完
                自身.错误=页面失败文案(原因)
            return#止
        自身.重命名中=False#同步完
        自身.结算()#结算

    def 改草稿(自身,值):
        '输入变更清错'
        自身.草稿=值#草稿
        自身.错误=None

    def 键下(自身,键名):
        'Enter 提交；拼写中的 Enter 不提交'
        if 键名=='Enter' and not 自身.拼写中:#提交
            自身.确认()#确认

    def 渲染(自身):
        '重命名对话框'
        翻译=自身.翻译#文案
        挡=自身.重命名中 or 自身.草稿.strip()==''#挡确认
        def 改文(事件):
            '写入草稿'
            自身.改草稿(事件.value)
        def 开始拼写():
            '输入法组合开始'
            自身.拼写中=True
        def 结束拼写():
            '输入法组合结束'
            自身.拼写中=False
        def 按键(事件):
            '回车提交'
            参数=事件.args if hasattr(事件,'args') else None
            键名=''
            if isinstance(参数,dict) and 'key' in 参数 and isinstance(参数['key'],str):
                键名=参数['key']
            if 键名!='':
                自身.键下(键名)
        with 界面.dialog() as 对话框:
            with 界面.card():
                界面.label(翻译('rename.session.title'))
                框=界面.input(value=自身.草稿, placeholder=翻译('field.sessionName'), on_change=改文).props('autofocus')
                框.on('compositionstart',开始拼写)
                框.on('compositionend',结束拼写)
                框.on('keydown',按键)
                if 自身.重命名中:
                    框.disable()
                if isinstance(自身.错误,str) and 自身.错误!='':
                    界面.label(自身.错误)
                取消=界面.button(翻译('cancel'), on_click=自身.关闭)
                确认=界面.button(翻译('rename'), on_click=自身.确认)
                界面.button(翻译('close'), on_click=自身.关闭)
                if 自身.重命名中:
                    取消.disable()
                if 挡:
                    确认.disable()
        对话框.open()

class 重命名会话菜单项:#菜单 order 200
    '请求重命名对话框，以行当前标题播种'

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
        if 'useShortcuts' not in 属性 or 't' not in 属性 or 'useMenuOpenState' not in 属性 or 'requestSessionRename' not in 属性:
            return#缺席位
        def 取重命名(行表):
            '找出重命名快捷键'
            for 行 in 行表:
                if 行['id']=='session.rename':
                    return 行
            return None
        属性['useShortcuts'](取重命名)#快捷
        翻译=属性['t']#文案
        def 选定():
            '关菜单后请求'
            设开=属性['useMenuOpenState']()[1]#setter
            设开(False)#关
            属性['requestSessionRename'](属性['sessionId'],属性['displayTitle'])#请求
        界面.button(翻译('rename'), on_click=选定)

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

class 会话重命名对话框:#shell.overlay 席
    '无请求时 None；有则按会话键一份对话框'

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身._表单=None#当前
        自身._表单键=None#会话键
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 渲染(自身):
        '打开的对话框'
        属性=自身.属性#props
        if 'useRenameRequest' not in 属性:#缺钩
            return#空
        def 原样(待):
            '原样返回重命名请求'
            return 待
        请求=属性['useRenameRequest'](原样)#待改名
        if 请求 is None:#无
            自身._表单=None
            自身._表单键=None
            return#空
        键=请求['sessionId']#会话
        if 自身._表单 is None or 自身._表单键!=键:#新请求
            自身._表单=重命名表单(请求,属性['renameSession'],属性['settleSessionRename'],属性['t'])#建
            自身._表单键=键
        with 界面.column().classes('session-rename'):
            自身._表单.渲染()

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
