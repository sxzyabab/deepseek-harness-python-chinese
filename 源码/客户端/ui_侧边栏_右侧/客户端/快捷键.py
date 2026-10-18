'右侧栏自己的快捷键，对着当前挂着的页面解析'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.模态层 import 关栈顶模态
from .文案 import 中文

__all__=['登记右侧侧栏快捷键']


def 登记右侧侧栏快捷键(快捷键,侧栏,翻译,关闭窗口):
    '登记展开、分栏、全屏、关闭和刷新。显示用中文表'
    def 原因(种类,目标):
        '分栏和全屏现在为什么不能做'
        if 种类=='split':
            阻断=侧栏.分栏阻断(目标)
            if 阻断 is None:
                return None
            return 中文['command.'+阻断]
        if 目标['host']=='float':
            return 中文['command.float']
        return None

    拆除表=[]

    def 切换标签():
        '展开或收起'
        return 中文['command.toggle']

    def 切换解析():
        '没有会话就挡住'
        目标=侧栏.命令目标(None)
        if 目标 is None:
            return {'status':'blocked','reason':中文['command.noSession']}

        def 执行():
            '目标还在才切换'
            if 侧栏.目标仍当前(目标):
                侧栏.切换展开()

        return {'status':'handled','run':执行}

    拆除表.append(快捷键.register({
        'id':'sidebar.right.toggle',
        'label':切换标签,
        'aliases':['right sidebar','toggle right panel'],
        'defaults':{
            'desktop:macos':{'code':'KeyB','modifiers':['primary','alt']},
            'desktop:windows':{'code':'KeyB','modifiers':['primary','alt']},
            'desktop:linux':{'code':'KeyB','modifiers':['primary','alt']},
            'web:macos':{'code':'KeyB','modifiers':['primary','shift']},
            'web:windows':{'code':'KeyB','modifiers':['primary','shift']},
        },
        'regions':['page','editable','terminal'],
        'modals':[],
        'resolve':切换解析,
    }))
    for 种类 in ('split','fullscreen'):
        if 种类=='split':
            绑定={'code':'Backslash','modifiers':['primary']}
            命令标识='pane.split'

            def 分栏标签():
                '分栏'
                return 中文['dock.splitPane']

            标签=分栏标签
        else:
            绑定={'code':'Enter','modifiers':['primary','alt']}
            命令标识='pane.fullscreen.toggle'

            def 全屏标签():
                '全屏'
                return 中文['command.fullscreen']

            标签=全屏标签

        def 做解析(输入,种类=种类):
            '先看焦点，再看这一格能不能做'
            元素=输入.get('target') if isinstance(输入,dict) else None
            目标=侧栏.聚焦目标(元素)
            if 目标 is None:
                return {'status':'blocked','reason':中文['command.noFocus']}
            不可=原因(种类,目标)
            if 不可 is not None:
                return {'status':'blocked','reason':不可}

            def 执行():
                '目标换过就停'
                if not 侧栏.目标仍当前(目标):
                    return
                if 种类=='split':
                    侧栏.分栏(目标['paneId'])
                else:
                    侧栏.切换全屏(目标)

            return {'status':'handled','run':执行}

        拆除表.append(快捷键.register({
            'id':命令标识,
            'label':标签,
            'aliases':[种类,'panel'],
            'defaults':{
                'desktop:macos':绑定,
                'desktop:windows':绑定,
                'desktop:linux':绑定,
                'web:macos':绑定,
                'web:windows':绑定,
            },
            'regions':['page','editable','terminal'],
            'modals':[],
            'resolve':做解析,
        }))
    for 种类 in ('close','refresh'):
        桌面={'code':'KeyW' if 种类=='close' else 'KeyR','modifiers':['primary']}
        网页={'code':桌面['code'],'modifiers':['primary','alt']}
        默认={
            'desktop:macos':桌面,
            'desktop:windows':桌面,
            'desktop:linux':桌面,
            'web:windows':网页,
        }
        if 种类=='close':
            默认['web:macos']=网页

            def 关闭标签():
                '关闭'
                return 中文['command.close']

            标签=关闭标签
            模态=['settings','shortcuts','other']
        else:
            def 刷新标签():
                '刷新'
                return 中文['command.refresh']

            标签=刷新标签
            模态=[]

        def 页解析(输入,种类=种类):
            '模态里的关闭先关模态。刷新只跑页面自己的刷新'
            元素=输入.get('target') if isinstance(输入,dict) else None
            来源=输入.get('source') if isinstance(输入,dict) else None
            模态名=输入.get('modal') if isinstance(输入,dict) else None
            if 种类=='close' and 模态名 is not None:
                def 关模态():
                    '关掉最前的模态'
                    关栈顶模态(取握手窗口().document)
                return {'status':'handled','run':关模态}
            目标=侧栏.聚焦目标(元素)
            在侧栏里=False
            if 元素 is not None:
                在侧栏里=元素.closest('[data-sidebar-right-session]') is not None
            if 目标 is None and (来源=='iframe' or 在侧栏里):
                return {'status':'blocked','reason':中文['command.stale']}
            if 种类=='refresh':
                刷新=None
                if 目标 is not None and 目标.get('occurrence') is not None:
                    刷新=目标['occurrence']['commands'].get('refresh')
                if 目标 is None or 刷新 is None:
                    return {'status':'blocked','reason':中文['command.noRefresh']}

                def 执行刷新(刷新=刷新,目标=目标):
                    '还是这一页才刷新'
                    出现=目标.get('occurrence')
                    仍是=出现 is not None and 出现['commands'].get('refresh') is 刷新
                    if 侧栏.目标仍当前(目标) and 仍是:
                        刷新()

                return {'status':'handled','run':执行刷新}
            if 目标 is not None and 侧栏.可关闭目标(目标):
                def 执行关闭(目标=目标):
                    '关掉捕获到的这一页'
                    侧栏.关闭目标(目标)
                return {'status':'handled','run':执行关闭}
            if 快捷键.runtime!='desktop':
                return {'status':'blocked','reason':中文['command.noFocus']}

            def 关窗口(目标=目标):
                '桌面下，焦点不在侧栏或还是这一页，就关窗口'
                if 目标 is None or 侧栏.目标仍当前(目标):
                    关闭窗口()

            return {'status':'handled','run':关窗口}

        拆除表.append(快捷键.register({
            'id':'page.'+种类,
            'label':标签,
            'aliases':[种类,'page'],
            'defaults':默认,
            'regions':['page','editable','terminal'],
            'modals':模态,
            'resolve':页解析,
        }))

    def 拆除():
        '按登记的反序摘掉'
        for 拆 in reversed(拆除表):
            拆()

    return 拆除
