import re
from ....ui_基础界面组件.icons import 图标
from ....ui_基础界面组件.文字闪烁 import 文字闪烁
from ....ui_对话.异常 import 标样式模块
from .用披露 import 取钩,注入聊天样式,画披露行,真属性,挂节点

__all__=['推理行']

样式模块='reasoning-row'
段落分隔=re.compile(r'\r?\n(?:[\t ]*\r?\n)+')


def 首行(文本):
    '第一个换行之前'
    位=文本.find('\n')
    if 位<0:
        return 文本
    return 文本[:位]


def 最近完成段首行(文本):
    '流式时只展示已经写完第一行的段落'
    摘要=''
    起点=0
    for 匹配 in 段落分隔.finditer(文本):
        段尾=匹配.start()+匹配.group(0).find('\n')
        换行=文本.find('\n',起点)
        if 换行!=-1 and 换行<=段尾:
            候选=文本[起点:换行].strip()
            if 候选!='':
                摘要=候选
        起点=匹配.end()
    换行=文本.find('\n',起点)
    if 换行!=-1:
        候选=文本[起点:换行].strip()
        if 候选!='':
            摘要=候选
    return 摘要


class 推理行:
    '助手推理。收起时给一行预览，展开后走推理正文槽'
    def __init__(自身,属性=None):
        '记下推理文本'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '预览去掉成对星号。流式时用最近完成的段首'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'推理行.module.css')
        注入聊天样式(文档,'a11y','无障碍.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        文本=属性.get('text') if isinstance(属性.get('text'),str) else ''
        在跑=属性.get('running') is True
        披露=属性.get('useDisclosure')
        席=披露() if callable(披露) else None
        if 席 is None:
            from .用披露 import 用披露
            席=用披露()
            自身.席=席
        elif getattr(自身,'席',None) is not 席:
            自身.席=席
        展开=自身.席.是否展开()
        摘要文=最近完成段首行(文本) if 在跑 else 首行(文本)
        摘要=摘要文.replace('**','')
        呈现=取钩(属性,'usePresentation')
        if 呈现 is None and callable(属性.get('usePresentation')):
            呈现=属性['usePresentation']
        预览=False
        if callable(呈现):
            def 选预览(策略):
                '收起且有摘要时，流式或策略允许才预览'
                if not isinstance(策略,dict):
                    return False
                return (not 展开) and 摘要!='' and (在跑 or 策略.get('settledReasoningPreview') is True)
            预览=呈现(选预览) is True
        elif (not 展开) and 摘要!='' and 在跑:
            预览=True

        def 切换():
            '翻转披露'
            自身.席.切换()
            自身.渲染()

        折叠=文档.createDocumentFragment()
        点=文档.createElement('span')
        点.className='separator'
        标样式模块(点,样式模块)
        点.setAttribute('data-shimmer-decoration','')
        点.setAttribute('aria-hidden','true')
        摘=文档.createElement('span')
        摘.className='summary'
        标样式模块(摘,样式模块)
        真属性(摘,'data-streaming',在跑)
        文=文档.createElement('span')
        文.className='summaryText'
        标样式模块(文,样式模块)
        挂节点(文,文字闪烁({'window':窗口,'children':摘要}))
        摘.appendChild(文)
        折叠.appendChild(点)
        折叠.appendChild(摘)
        子=None
        if 展开:
            体=文档.createElement('div')
            体.className='thinkBody'
            标样式模块(体,样式模块)
            槽=属性.get('renderSlot')
            if callable(槽):
                挂节点(体,槽('conversation.chat.reasoning.body',{'text':文本,'running':在跑,'window':窗口}))
            子=体
        根=文档.createElement('div')
        根.className='root'
        标样式模块(根,样式模块)
        根.setAttribute('data-variant','think')
        根.setAttribute('data-state','running' if 在跑 else 'ok')
        真属性(根,'data-expanded',展开)
        真属性(根,'data-preview',预览)
        if 在跑:
            隐=文档.createElement('span')
            隐.className='visuallyHidden'
            标样式模块(隐,'a11y')
            隐.setAttribute('role','status')
            隐.textContent=翻译('row.running')
            根.appendChild(隐)
        根.appendChild(画披露行(文档,{
            'window':窗口,
            '样式模块':样式模块,
            'rowClassName':'row',
            'leadingClassName':'leading',
            'titleClassName':'title',
            'icon':图标('think-14',{'window':窗口}),
            'title':翻译('message.think'),
            'running':在跑,
            'open':展开,
            'expandable':True,
            'expandOnRowClick':True,
            'onToggle':切换,
            'collapsedContent':折叠,
            'children':子,
        }))
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
