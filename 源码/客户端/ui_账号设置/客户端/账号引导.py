'模型凭据引导里的账号登录'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 挂上,清空子
from .登录对话框 import 登录对话框

__all__=['账号引导']

class 账号引导:
    '未登录时显示登录框。登录成功就完成引导'
    def __init__(自身,属性):
        '挂上时声明引导占有登录框'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.对话框=None
        自身.已声明=False
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '绘制中再来一次只记一笔'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画出(自身):
        '已登录或还没有视图时不画框'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        else:
            清空子(自身.根)
        if 自身.已声明 is not True:
            设=属性.get('setOnboarding')
            if 设 is not None:
                设(True)
            自身.已声明=True
        def 全量(快照):
            '整份账号'
            return 快照
        钩=属性.get('useAccount')
        账号=钩(全量) if 钩 is not None else {}
        if isinstance(账号,dict) is False:
            账号={}
        视图=账号.get('view') if isinstance(账号.get('view'),dict) else None
        if isinstance(视图,dict) and 视图.get('status')=='credential-stored':
            完成=属性.get('complete')
            if 完成 is not None:
                完成()
            自身.订上()
            return
        if 视图 is None:
            自身.订上()
            return
        def 取色(快照):
            '当前色板'
            活动=快照.get('active') if isinstance(快照,dict) else None
            if isinstance(活动,dict):
                return 活动.get('colorScheme')
            return 'light'
        色板钩=属性.get('useTheme')
        色板=色板钩(取色) if 色板钩 is not None else 'light'
        if 色板 not in ('light','dark'):
            色板='light'
        def 关闭():
            '关掉并完成引导'
            显示=属性.get('showLogin')
            if 显示 is not None:
                显示(False)
            完成=属性.get('complete')
            if 完成 is not None:
                完成()
        def 改密钥():
            '改去填密钥'
            显示=属性.get('showLogin')
            if 显示 is not None:
                显示(False)
            用=属性.get('useApiKey')
            if 用 is not None:
                用()
        框属性={
            'window':窗口,
            'account':账号,
            'colorScheme':色板,
            'start':属性.get('start'),
            'cancel':属性.get('cancel'),
            'close':关闭,
            'useApiKey':改密钥,
        }
        if 自身.对话框 is None:
            自身.对话框=登录对话框(框属性)
        else:
            自身.对话框.更新(框属性)
            自身.对话框.渲染()
        挂上(自身.根,自身.对话框)
        自身.订上()

    def 订上(自身):
        '账号或主题变化时重画'
        if 自身.已订:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()
        for 名 in ('useAccount','useTheme'):
            钩=自身.属性.get(名)
            订=getattr(钩,'_subscribe',None) if 钩 is not None else None
            if callable(订):
                自身.退订.append(订(变更))
        自身.已订=True

    def 拆除(自身):
        '卸下时放开登录框的占有'
        设=自身.属性.get('setOnboarding')
        if 自身.已声明 and 设 is not None:
            设(False)
        自身.已声明=False
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False
        if 自身.对话框 is not None:
            自身.对话框.拆除()
