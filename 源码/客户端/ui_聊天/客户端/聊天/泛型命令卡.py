from ....ui_基础界面组件.icons import 图标
from .用披露 import 注入聊天样式,画披露行,真属性,挂节点

__all__=['泛型命令卡']

样式模块='generic-command'


def 命令态(结局):
    '未结算是 running，出错是 error，其余是 ok'
    if 结局 is None:
        return 'running'
    if isinstance(结局,dict) and 结局.get('kind')=='error':
        return 'error'
    return 'ok'


class 泛型命令卡:
    '命令摘要。多行结果才展开正文'
    def __init__(自身,属性=None):
        '记下命令节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.展开=False
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出披露行。单行结果不再展开'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'泛型命令卡.module.css')
        注入聊天样式(文档,'a11y','无障碍.module.css')
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        结局=节点.get('outcome')
        文本=结局.get('text') if isinstance(结局,dict) else None
        if 结局 is None:
            摘要=属性.get('runningSummary')
            if not isinstance(摘要,str):
                摘要=翻译('command.running')
        elif isinstance(文本,str):
            摘要=文本
        elif isinstance(结局,dict) and 结局.get('kind')=='error':
            摘要=翻译('command.failed')
        else:
            摘要=翻译('command.done')
        标题=节点.get('name')
        if not isinstance(标题,str) or 标题=='':
            标题=翻译('command.title')
        态=命令态(结局)
        在跑=态=='running'
        正文=文本 if isinstance(文本,str) and '\n' in 文本 else None
        打开=自身.展开 and 正文 is not None

        def 切换():
            '有多行结果才翻转'
            自身.展开=not 自身.展开
            自身.渲染()

        折叠=文档.createDocumentFragment()
        点=文档.createElement('span')
        点.className='separator'
        点.setAttribute('data-shimmer-decoration','')
        点.setAttribute('aria-hidden','true')
        from ....ui_对话.异常 import 标样式模块
        标样式模块(点,样式模块)
        折叠.appendChild(点)
        摘=文档.createElement('span')
        摘.className='summary'
        标样式模块(摘,样式模块)
        真属性(摘,'data-error',态=='error')
        from ....ui_基础界面组件.文字闪烁 import 文字闪烁
        闪=文字闪烁({'window':窗口,'children':摘要})
        挂节点(摘,闪)
        折叠.appendChild(摘)
        子=None
        if 打开:
            预=文档.createElement('pre')
            预.className='body'
            标样式模块(预,样式模块)
            真属性(预,'data-error',态=='error')
            预.textContent=正文
            子=预
        根=文档.createElement('div')
        根.className='root'
        标样式模块(根,样式模块)
        根.setAttribute('data-variant','others')
        根.setAttribute('data-state',态)
        if 态=='running':
            隐=文档.createElement('span')
            隐.className='visuallyHidden'
            from ....ui_对话.异常 import 标样式模块 as 标
            标(隐,'a11y')
            隐.textContent=翻译('row.running')
            根.appendChild(隐)
        if 态=='error':
            隐=文档.createElement('span')
            隐.className='visuallyHidden'
            标样式模块(隐,'a11y')
            隐.textContent=翻译('row.failed')
            根.appendChild(隐)
        图=图标('api-14',{'window':窗口})
        披露=画披露行(文档,{
            'window':窗口,
            'className':'',
            '样式模块':披露模块占位(),
            'icon':图,
            'title':标题,
            'running':在跑,
            'open':打开,
            'expandable':正文 is not None,
            'expandOnRowClick':True,
            'keepContentWhenOpen':True,
            'onToggle':切换,
            'collapsedContent':折叠,
            'children':子,
            'leadingClassName':'leading',
            'titleClassName':'title',
        })
        根.appendChild(披露)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根


def 披露模块占位():
    '披露根用披露模块，外层 root 已经标了命令卡模块'
    from .用披露 import 披露模块
    return 披露模块
