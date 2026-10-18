from ....ui_基础界面组件.icons import 图标
from .上下文体 import 不透明体
from .用披露 import 注入聊天样式,画披露行

__all__=['系统提示行','系统提示节点视图']

样式模块='context-injection'


class 系统提示行:
    '完整系统提示。展开后用同一套不透明上下文正文'
    def __init__(自身,属性=None):
        '记下提示文本'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '更新过的提示用另一条标题'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'上下文注入行.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        键='message.systemPromptUpdate' if 属性.get('update') is True else 'message.systemPrompt'

        def 切换():
            '翻转后再画'
            自身.打开=not 自身.打开
            自身.渲染()

        体=文档.createElement('div')
        体.className='body'
        from ....ui_对话.异常 import 标样式模块
        标样式模块(体,样式模块)
        体.setAttribute('data-system-prompt-body','')
        文=不透明体(文档,窗口,[{'type':'text','text':属性.get('text') or ''}],None,翻译)
        if 文 is not None:
            体.appendChild(文)
        自身.根=画披露行(文档,{
            'window':窗口,
            'className':'root',
            '样式模块':样式模块,
            'icon':图标('browse-16',{'window':窗口}),
            'chevronClassName':'chevron',
            'title':翻译(键),
            'open':自身.打开,
            'expandable':True,
            'expandOnRowClick':True,
            'onToggle':切换,
            'children':体,
        })
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根


class 系统提示节点视图:
    '系统提示键的聊天渲染器'
    def __init__(自身,属性=None):
        '从节点取出文本'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.行=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '交给系统提示行'
        属性=自身.属性
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        if 自身.行 is None:
            自身.行=系统提示行({
                'window':属性['window'],
                'text':数据.get('text') or '',
                'update':数据.get('update') is True,
                't':属性.get('t'),
                'parent':属性.get('parent'),
            })
        else:
            自身.行.更新({
                'window':属性['window'],
                'text':数据.get('text') or '',
                'update':数据.get('update') is True,
                't':属性.get('t'),
                'parent':属性.get('parent'),
            })
            自身.行.渲染()
        自身.根=自身.行.根
        return 自身.根
